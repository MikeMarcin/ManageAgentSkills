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


def paths(raw):
    """NUL-separated repository-relative paths from a ``-z`` Git listing."""
    try:
        return [item.decode('utf-8') for item in raw.split(b'\0') if item]
    except UnicodeError:
        c.fail('source.candidate_invalid', 'Checkout has unsupported path names.', 4)


def local_changes(root, timeout=30):
    """Every modified, staged or untracked path, sorted and repository-relative. Ignored files are not changes."""
    raw = c.git(root, 'status', '--porcelain=v1', '-z', '--untracked-files=all', '--no-renames', binary=True, timeout=timeout)
    return sorted({item[3:] for item in paths(raw)})


def parents(path):
    parts = path.split('/')
    return {'/'.join(parts[:index]) for index in range(1, len(parts))}


def blocking_paths(root, candidate, local, timeout=30):
    """The local changes a fast-forward from HEAD to ``candidate`` would touch.

    A path blocks when the update changes it, or when one side has a file where the other has a directory.
    Everything else stays in the working tree through Git's own ``merge --ff-only``.
    """
    if not local:
        return []
    folded = c.git(root, 'config', '--bool', '--get', 'core.ignorecase', optional=True, timeout=timeout) == 'true'
    key = str.casefold if folded else str
    incoming = {key(path) for path in paths(c.git(root, 'diff', '--name-only', '--no-renames', '-z', 'HEAD', candidate, binary=True, timeout=timeout))}
    folders = set().union(*(parents(path) for path in incoming))
    return sorted(path for path in local if key(path) in incoming or key(path) in folders or parents(key(path)) & incoming)


def stash_message(before, candidate):
    from datetime import datetime, timezone
    return f"mask update {before[:7]}..{candidate[:7]} {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}"


def find_stash(root, message, timeout=30):
    """The stash entry whose message is exactly ``message``, for a journal interrupted before it recorded the commit."""
    listing = c.git(root, 'stash', 'list', '--format=%H%x00%gs', optional=True, timeout=timeout) or ''
    for line in listing.splitlines():
        commit, _, subject = line.partition('\0')
        if subject.split(': ', 1)[-1] == message:
            return commit
    return None


def stash_report(root, entry, timeout=30):
    """Where ``update --stash`` put the blocking changes, and the command that shows them. MASK never pops or applies it."""
    commit = entry.get('commit') or find_stash(root, entry['message'], timeout)
    return dict(root=str(root), paths=entry['paths'], message=entry['message'], commit=commit,
                inspect=f'git stash show -p {commit}' if commit else None)


def stash(root, pending, home, output, timeout):
    """Move only the journaled blocking paths into one new stash entry and record its commit in the pending intent."""
    entry = pending['git']['stash']
    previous = c.git(root, 'rev-parse', '--verify', '--quiet', 'refs/stash', optional=True, timeout=timeout)
    try:
        c.git(root, '--literal-pathspecs', 'stash', 'push', '--include-untracked', '-m', entry['message'], '--', *entry['paths'],
              timeout=timeout, mutating=True)
        created = c.git(root, 'rev-parse', '--verify', '--quiet', 'refs/stash', optional=True, timeout=timeout)
        if created is None or created == previous:
            c.fail('git.failed', 'Git did not record a stash.', 5)
        before = copy.deepcopy(pending)
        entry['commit'] = created
        c.atomic_text(home / 'pending.json', c.text_json(pending), c.text_json(before))
        fs.checkpoint('stash')
        if blocking_paths(root, pending['git']['candidate'], local_changes(root, timeout), timeout):
            c.fail('git.failed', 'The stash left changes that the update would overwrite.', 5)
    except (Exception, KeyboardInterrupt):
        output.update(changed=True, transaction='partial')
        output['data']['stash'] = stash_report(root, entry, timeout)
        c.fail('recovery.required', 'The blocking changes may have been stashed; pending intent retained without resetting Git.', 8)


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
    c.fields(entry, ('scope', 'root', 'before', 'candidate'), ('consent', 'stash'), family='recovery')
    if entry['scope'] != 'program' or entry['root'] != str(program_root) or any(not isinstance(entry[key], str) or not re.fullmatch('[0-9a-f]{40,64}', entry[key]) for key in ('before', 'candidate')):
        c.fail('recovery.conflict', 'Invalid pending Git transition.', 8)
    if 'consent' in entry and (not isinstance(entry['consent'], str) or not re.fullmatch('sha256:[0-9a-f]{64}', entry['consent'])):
        c.fail('recovery.conflict', 'Invalid pending Git transition.', 8)
    if 'stash' in entry:  # update --stash: the blocking paths it moves aside, and the stash commit once Git made it.
        c.fields(entry['stash'], ('message', 'paths'), ('commit',), family='recovery')
        stashed = entry['stash']
        if (not isinstance(stashed['message'], str) or not stashed['message'].startswith('mask update ') or any(char in stashed['message'] for char in '\r\n\0')
                or not isinstance(stashed['paths'], list) or not stashed['paths'] or any(not isinstance(path, str) or not path for path in stashed['paths'])
                or 'commit' in stashed and (not isinstance(stashed['commit'], str) or not re.fullmatch('[0-9a-f]{40,64}', stashed['commit']))):
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
    observed = checkout_preconditions(root, 'origin', 'main', 'ManageAgentSkills', timeout, clean=False)
    if observed['revision'] not in (entry['before'], entry['candidate']):
        c.fail('recovery.conflict', 'Checkout changed outside the recorded transition.', 8)
    if 'stash' in entry:
        output['data']['stash'] = stash_report(root, entry['stash'], timeout)
    if mode == 'rollback':  # Rollback never moves the checkout, so no local change can be lost by it.
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
        # The same tolerance as update: changes the fast-forward does not touch stay in the working tree.
        blocking = blocking_paths(root, entry['candidate'], local_changes(root, timeout), timeout) if observed['dirty'] else []
        if blocking:
            c.fail('source.dirty', 'Local changes touch files this update changes; commit or stash them, then complete recovery.', 4, blocking_paths=blocking)
        if not output['dry_run']:
            advance(root, entry['candidate'], pending, home, output, timeout)
