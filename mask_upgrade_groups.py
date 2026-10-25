"""Repository groups for ``upgrade --all``: resolve once per repository, then propagate (MASK-0146).

Registered project roots are one repository when they share a Git common directory (linked
worktrees) or the normalized fetch URL of ``origin`` (separate clones). One canonical checkout per
group is upgraded; the other members adopt its exact result instead of resolving again, and with
``--commit`` receive its commit by fast-forward or a cherry-picked commit. This module only
observes Git and decides; ``mask_update`` plans the activation and ``mask_upgrade_commit`` commits.
"""
from __future__ import annotations

import os
from pathlib import Path
import re

import mask_core as c
import mask_upgrade_commit as commits

URL = re.compile(r'^([a-z][a-z0-9+.-]*)://(?:[^@/]*@)?(\[[^\]]+\]|[^/:]*)(?::\d*)?(/.*)?$', re.IGNORECASE)
SCP = re.compile(r'^(?:[^@/]+@)?([^:/]+):(.*)$')


def normalize_url(url, root):
    """One spelling per repository: host/path for network forms, an absolute path for local ones."""
    text = url.strip()
    match = URL.match(text)
    if match and match.group(1).lower() != 'file':
        host, path = match.group(2).casefold(), match.group(3) or ''
    else:
        scp = None if match or re.match(r'^[A-Za-z]:[\\/]', text) else SCP.match(text)
        if scp and '/' not in scp.group(1):
            host, path = scp.group(1).casefold(), scp.group(2)
        else:
            local = match.group(3) if match else text
            if match and re.match(r'^/[A-Za-z]:', local or ''):
                local = local[1:]
            location = Path(local) if Path(local).is_absolute() else root / local
            try:
                location = location.resolve()
            except OSError:
                pass
            path = os.path.normcase(str(location)).replace('\\', '/').rstrip('/')
            return 'file:' + (path[:-4] if path.endswith('.git') else path)
    path = path.strip('/')
    if path.endswith('.git'):
        path = path[:-4]
    return host + '/' + path


def describe(root, scope, timeout):
    """Observe one consumer's repository identity, branch and project controls without writing."""
    row = dict(root=str(root), scope=scope, git=False, common_dir=None, origin=None, branch=None, head=None,
               default_branch=None, upstream=None, controls=None, head_controls=None, operation=False)
    if scope != 'project':
        return row

    def git(*args):
        return c.git(root, *args, timeout=timeout, optional=True)
    top = git('rev-parse', '--show-toplevel')
    try:
        if not top or Path(top).resolve() != Path(root).resolve():
            return row
    except OSError:
        return row
    common = git('rev-parse', '--path-format=absolute', '--git-common-dir')
    if not common:
        return row
    row['git'] = True
    row['common_dir'] = os.path.normcase(str(Path(common).resolve())).replace('\\', '/')
    origin = git('config', '--get', 'remote.origin.url')
    row['origin'] = normalize_url(origin, Path(root)) if origin else None
    row['head'] = git('rev-parse', '--verify', '-q', 'HEAD^{commit}')
    branch = git('symbolic-ref', '-q', 'HEAD')
    row['branch'] = branch[len('refs/heads/'):] if branch and branch.startswith('refs/heads/') else None
    if row['branch']:
        row['upstream'] = git('rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{upstream}')
    default = git('symbolic-ref', '-q', 'refs/remotes/origin/HEAD')
    row['default_branch'] = default[len('refs/remotes/origin/'):] if default and default.startswith('refs/remotes/origin/') else None
    row['controls'] = {path: c.digest(value) if value is not None else None for path, value in commits.controls(Path(root)).items()}
    if row['head']:
        row['head_controls'] = {}
        for path in commits.PATHS:
            blob = c.git(root, 'show', row['head'] + ':' + path, timeout=timeout, optional=True, binary=True)
            row['head_controls'][path] = c.digest(blob) if blob is not None else None
    for name in commits.OPERATIONS:
        path = git('rev-parse', '--git-path', name)
        if path and c.kind(Path(root) / path) != 'missing':
            row['operation'] = True
    return row


def partition(rows):
    """Union worktrees (common directory) and clones (origin URL); singletons are independent."""
    parent = list(range(len(rows)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index
    for key in ('common_dir', 'origin'):
        seen = {}
        for index, row in enumerate(rows):
            if not row['git'] or not row[key]:
                continue
            if row[key] in seen:
                parent[find(index)] = find(seen[row[key]])
            else:
                seen[row[key]] = index
    groups = {}
    for index, row in enumerate(rows):
        if row['git']:
            groups.setdefault(find(index), []).append(row)
    return [sorted(members, key=lambda row: row['root']) for members in groups.values() if len(members) > 1]


def identity(members):
    origins = sorted({row['origin'] for row in members if row['origin']})
    return origins[0] if origins else 'gitdir:' + sorted({row['common_dir'] for row in members})[0]


def on_default(row):
    default = row['default_branch']
    if not row['branch']:
        return False
    if default:
        return row['branch'] == default or row['upstream'] == 'origin/' + default
    return row['branch'] in ('main', 'master')


def clean(row):
    return row['head_controls'] is not None and row['controls'] == row['head_controls']


def choose(members, invoking, commit, dev_links):
    """The canonical member and why, or None and the reason no single choice is sound."""
    candidates = [row for row in members if row['root'] not in dev_links and not row['operation'] and
                  (not commit or row['branch'] and row['head'])]
    if not candidates:
        return None, 'no_candidate'
    for row in candidates:
        if invoking is not None and row['root'] == invoking:
            return row, 'invoking_checkout'
    if len(candidates) == 1:
        return candidates[0], 'only_candidate'
    preferred = [row for row in candidates if on_default(row)]
    if not preferred:
        return None, 'ambiguous'
    ranked = sorted(preferred, key=lambda row: (not clean(row), row['root']))
    return ranked[0], 'default_branch' if len(preferred) == 1 else 'default_branch_first_path'


def plan(consumers, records, invoking, commit, timeout):
    """Return the disclosed groups and annotate each grouped consumer item with its role."""
    rows = [describe(item['root'], item['scope'], timeout) for item in consumers]
    by_root = {item['row']['root']: item for item in consumers}
    dev_links = {key for key, record in records.items() if record.get('mode') == 'dev-link'}
    disclosed = []
    for members in partition(rows):
        canonical, reason = choose(members, invoking, commit, dev_links)
        group = dict(identity=identity(members), canonical=canonical['root'] if canonical else None, reason=reason, members=[])
        for row in members:
            item = by_root[row['root']]
            member = dict(root=row['root'], branch=row['branch'], detached=bool(row['head']) and not row['branch'],
                          head=row['head'], action=None, reason=None)
            if row['root'] in dev_links:
                member.update(action='skipped', reason='dev_link')
            elif canonical is None and reason == 'ambiguous':
                member.update(action='blocked', reason='ambiguous')
                if item['row']['status'] != 'blocked':
                    item['row'].update(status='blocked', error=c.MaskError(
                        'upgrade.group_ambiguous',
                        'Several checkouts of this repository could carry the upgrade and none is on the default branch; '
                        'run mask upgrade --all inside the intended checkout, or use --independent.', 4,
                        details=dict(root=row['root'], identity=group['identity'])).as_dict())
            elif canonical is None:
                member.update(action='independent', reason=reason)
            elif row is canonical:
                member.update(action='canonical', reason=reason)
                item['group'] = dict(role='canonical', git=row)
            else:
                member.update(action='adopt', reason='pending')
                item['group'] = dict(role='member', git=row, canonical=by_root[canonical['root']], canonical_git=canonical, disclosure=member)
            group['members'].append(member)
        disclosed.append(group)
    return disclosed


def adoption(item, start, final, commit):
    """Decide a member's action once the canonical result is known.

    ``start`` and ``final`` are the canonical's control digests before and after. Returns
    ``adopt``, ``current`` or ``independent`` with its reason.
    """
    row = item['group']['git']
    if commit and not clean(row):
        return 'independent', 'controls_modified'
    if row['controls'] == final:
        return 'current', 'already_adopted'
    if row['controls'] != start:
        return 'independent', 'controls_modified' if row['head_controls'] is not None and not clean(row) else 'controls_diverged'
    return 'adopt', 'same_controls'
