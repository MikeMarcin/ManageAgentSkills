"""Checkout observation, explicit fetch, exact trees and program fast-forwards; no implicit Git reset or push."""
from __future__ import annotations

import copy
from pathlib import Path
import re

import mask_core as c
import mask_fs as fs
import mask_sources as sources


def status(root, remote='origin', branch='main', timeout=30):
    c.checkout(root)
    head = c.git(root, 'rev-parse', 'HEAD', optional=True, timeout=timeout)
    current_branch = c.git(root, 'symbolic-ref', '--short', 'HEAD', optional=True, timeout=timeout)
    dirty = bool(c.git(root, 'status', '--porcelain', '--untracked-files=all', timeout=timeout))
    candidate = c.git(root, 'rev-parse', '--verify', f'refs/remotes/{remote}/{branch}^{{commit}}', optional=True, timeout=timeout)
    relation = 'unknown'
    if head and candidate:
        if head == candidate:
            relation = 'equal'
        elif c.git(root, 'merge-base', '--is-ancestor', head, candidate, optional=True, timeout=timeout) is not None:
            relation = 'behind'
        elif c.git(root, 'merge-base', '--is-ancestor', candidate, head, optional=True, timeout=timeout) is not None:
            relation = 'ahead'
        else:
            relation = 'diverged'
    return dict(root=str(root), revision=head, branch=current_branch, configured_branch=branch, remote=remote,
                candidate=candidate, dirty=dirty, relation=relation, remote_freshness='last_fetched', unborn=head is None)


def checkout_preconditions(root, remote, branch, expected_name=None, timeout=30, *, clean=True):
    """A checkout on its branch with a known remote; ``expected_name`` is the remote repository basename (``update``)."""
    observed = status(root, remote, branch, timeout)
    if observed['branch'] is None:
        c.fail('source.detached', 'Checkout is detached.', 4)
    if observed['branch'] != branch or observed['revision'] is None:
        c.fail('source.identity_mismatch', 'Checkout is not on the configured branch with a commit.', 4)
    origin = c.git(root, 'remote', 'get-url', remote, optional=True, timeout=timeout)
    if origin is None:
        c.fail('source.remote_unknown', 'Configured remote is missing.', 4)
    name = origin.replace('\\', '/').rstrip('/').removesuffix('.git').rsplit('/', 1)[-1].rsplit(':', 1)[-1]
    if expected_name is not None and name != expected_name:
        c.fail('source.identity_mismatch', 'Configured remote does not name the expected repository.', 4, expected_repository=expected_name)
    if clean and observed['dirty']:
        c.fail('source.dirty', 'Commit or preserve authoring changes before updating.', 4)
    for marker in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply'):
        location = c.git(root, 'rev-parse', '--git-path', marker, timeout=timeout)
        path = Path(location)
        if not path.is_absolute():
            path = root / path
        if path.exists():
            c.fail('source.dirty', 'An in-progress Git operation blocks updating.', 4)
    if c.git(root, 'config', '--bool', '--get', 'core.sparseCheckout', optional=True, timeout=timeout) == 'true':
        c.fail('source.candidate_invalid', 'Sparse checkouts are unsupported.', 4)
    entries = c.git(root, 'ls-files', '--stage', timeout=timeout)
    if any(line.startswith('160000 ') for line in entries.splitlines()):
        c.fail('source.candidate_invalid', 'Submodule checkouts are unsupported.', 4)
    return observed


def fetch(root, remote, branch, timeout, output):
    transport = c.git(root, 'remote', 'get-url', remote, timeout=timeout)
    options = sources.network_options(root, transport)
    before = c.git(root, 'rev-parse', '--verify', f'refs/remotes/{remote}/{branch}', optional=True, timeout=timeout)
    output['data']['fetch_effects'] = dict(attempted=True, fetched=False, remote_refs_changed=False)
    try:
        c.git(root, *options, 'fetch', '--no-tags', '--no-recurse-submodules', remote, f'+refs/heads/{branch}:refs/remotes/{remote}/{branch}', timeout=timeout, mutating=True)
        output['data']['fetch_effects']['fetched'] = True
    finally:
        after = c.git(root, 'rev-parse', '--verify', f'refs/remotes/{remote}/{branch}', optional=True, timeout=timeout)
        output['data']['fetch_effects'].update(remote_refs_changed=before != after, before=before, after=after)


def tree(root, revision, path='', recursive=False, *, max_output=16 * 1024 * 1024,
         exact=None, include_trees=False):
    args = ['ls-tree', '-z']
    if recursive:
        args.append('-r')
    if include_trees:
        args.append('-t')
    args.append(revision + (':' + path if path else ''))
    if exact is not None:
        args = ['--literal-pathspecs', *args, '--', exact]
    # A full object id names one tree for ever; any other revision (HEAD, a ref) is observed afresh.
    ask = c.git_frozen if re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', revision) else c.git
    raw = ask(root, *args, binary=True, max_output=max_output)
    rows = []
    for item in raw.split(b'\0'):
        if not item:
            continue
        try:
            header, name = item.split(b'\t', 1)
            mode, kind, oid = header.decode('ascii').split()
            name = name.decode('utf-8')
        except (ValueError, UnicodeError):
            c.fail('source.candidate_invalid', 'Candidate has unsupported tree names.', 4)
        rows.append((mode, kind, oid, name))
    return rows


def validate_git_intent(entry, program_root):
    """Only ``update`` advances a checkout through a journal, and only this program's own root."""
    c.fields(entry, ('scope', 'root', 'before', 'candidate'), ('consent',), family='recovery')
    if entry['scope'] != 'program' or entry['root'] != str(program_root) or any(not isinstance(entry[key], str) or not re.fullmatch('[0-9a-f]{40,64}', entry[key]) for key in ('before', 'candidate')):
        c.fail('recovery.conflict', 'Invalid pending Git transition.', 8)
    if 'consent' in entry and (not isinstance(entry['consent'], str) or not re.fullmatch('sha256:[0-9a-f]{64}', entry['consent'])):
        c.fail('recovery.conflict', 'Invalid pending Git transition.', 8)


def advance(root, candidate, pending, home, output, timeout):
    before = copy.deepcopy(pending)
    pending['phase'] = 'git_started'
    c.atomic_text(home / 'pending.json', c.text_json(pending), c.text_json(before))
    try:
        c.git(root, 'merge', '--ff-only', '--no-edit', candidate, timeout=timeout, mutating=True)
        if c.git(root, 'rev-parse', 'HEAD', timeout=timeout) != candidate:
            c.fail('git.failed', 'Checkout did not reach the frozen candidate.', 5)
        before = copy.deepcopy(pending)
        pending['phase'] = 'git_advanced'
        c.atomic_text(home / 'pending.json', c.text_json(pending), c.text_json(before))
        fs.checkpoint('git')
    except (Exception, KeyboardInterrupt):
        output.update(changed=True, transaction='partial')
        c.fail('recovery.required', 'Checkout may have changed; pending intent retained without resetting Git.', 8)


def recover_git(pending, home, output, mode):
    """Recover an ``update`` program fast-forward: roll back only an unadvanced checkout, or complete the reviewed candidate."""
    entry = pending['git']
    root = Path(entry['root'])
    timeout = (pending['config'] or {}).get('git_timeout_seconds', 30)
    observed = checkout_preconditions(root, 'origin', 'main', 'ManageAgentSkills', timeout)
    if observed['revision'] not in (entry['before'], entry['candidate']):
        c.fail('recovery.conflict', 'Checkout changed outside the recorded transition.', 8)
    if mode == 'rollback':
        if observed['revision'] != entry['before']:
            output.update(changed=True, transaction='partial')
            c.fail('recovery.conflict', 'The source advanced; rollback never resets Git. Complete recovery against the new revision.', 8)
        return
    from mask_install import program_migration
    migration = program_migration(root, entry['before'], entry['candidate'])
    if migration['requires_consent'] and entry.get('consent') != migration['plan_hash']:
        c.fail('plan.stale', 'The interrupted update no longer matches the change that was approved; recovery stopped without moving the checkout further.', 4)
    if observed['revision'] == entry['before'] and entry['candidate'] != entry['before']:
        if c.git(root, 'merge-base', '--is-ancestor', entry['before'], entry['candidate'], optional=True) is None:
            c.fail('recovery.conflict', 'Recorded candidate is no longer a fast-forward.', 8)
        if not output['dry_run']:
            advance(root, entry['candidate'], pending, home, output, timeout)
