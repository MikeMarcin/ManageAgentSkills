"""Explicit project-control commits after upgrade readiness, outside its journal."""
from __future__ import annotations

from pathlib import Path
import os
import tempfile

import mask_core as c

PATHS = ('.mask.json', '.mask.lock.json')
MESSAGE = 'chore(mask): upgrade skills'
OPERATIONS = ('MERGE_HEAD', 'rebase-merge', 'rebase-apply', 'CHERRY_PICK_HEAD',
              'REVERT_HEAD', 'sequencer', 'BISECT_LOG', 'BISECT_START')


def controls(root):
    return {path: (root / path).read_bytes() if c.kind(root / path) == 'file' else None for path in PATHS}


def result_row(root, scope):
    return dict(root=str(root), scope=scope, status='not_applicable' if scope == 'user' else 'not_attempted',
                paths=[], included_existing_changes=[], message=MESSAGE, before_head=None,
                after_head=None, commit=None, error=None)


def observation(root, timeout):
    """No staging, index refresh, filters, hooks or signing in a preview."""
    def git(*args, **options):
        return c.git(root, *args, timeout=timeout, **options)
    top = git('rev-parse', '--show-toplevel', optional=True)
    head = git('rev-parse', '--verify', 'HEAD^{commit}', optional=True) if top else None
    index_path = Path(git('rev-parse', '--git-path', 'index')) if top else None
    if index_path is not None and not index_path.is_absolute():
        index_path = root / index_path
    blobs = {path: git('show', head + ':' + path, optional=True, binary=True) if head else None for path in PATHS}
    return dict(top=top, head=head, branch=git('symbolic-ref', '-q', 'HEAD', optional=True) if top else None,
                git_dir=git('rev-parse', '--absolute-git-dir') if top else None,
                index=git('ls-files', '--stage', '-z', binary=True).hex() if top else None,
                index_fingerprint=c.digest(index_path.read_bytes()) if index_path is not None and index_path.exists() else None,
                controls={path: c.digest(value) if value is not None else None for path, value in controls(root).items()},
                blobs={path: value.hex() if value is not None else None for path, value in blobs.items()})


def eligibility(root, observed, timeout, *, detached=False):
    """``detached`` admits a detached HEAD: a propagated commit is reported as reachable only from it."""
    reason = None
    if not observed['top'] or Path(observed['top']).resolve() != root:
        reason = 'The selected project must be the Git worktree root.'
    elif not observed['head'] or not observed['branch'] and not detached:
        reason = 'An attached branch with an existing HEAD is required.'
    elif any(c.kind(root / path) != 'file' for path in PATHS):
        reason = 'Both project controls must be regular files.'
    elif c.git(root, 'check-ignore', '--no-index', '--', *PATHS, timeout=timeout, optional=True) is not None:
        reason = 'Ignored project controls cannot be committed.'
    elif c.git(root, 'ls-files', '--unmerged', timeout=timeout):
        reason = 'Resolve unmerged index entries before committing controls.'
    else:
        for name in OPERATIONS:
            path = c.git(root, 'rev-parse', '--git-path', name, timeout=timeout)
            if c.kind(root / path) != 'missing':
                reason = 'Finish the active Git operation before committing controls.'
                break
    return c.MaskError('upgrade.commit_ineligible', reason, 4, details=dict(root=str(root))).as_dict() if reason else None


def plan(root, scope, final, timeout, *, skipped=False):
    row = result_row(root, scope)
    if scope == 'user' or skipped:
        return row, None
    observed = observation(root, timeout)
    row['before_head'] = row['after_head'] = observed['head']
    current = controls(root)
    head = {path: bytes.fromhex(value) if value is not None else None for path, value in observed['blobs'].items()}
    row['paths'] = [path for path in PATHS if final[path] != head[path]]
    row['included_existing_changes'] = [path for path in row['paths'] if current[path] != head[path]]
    row['status'] = 'planned' if row['paths'] else 'not_needed'
    # In particular, a clean detached checkout does not need commit eligibility.
    if row['paths']:
        row['error'] = eligibility(root, observed, timeout)
        observed['eligibility'] = row['error']
        if row['error']:
            row['status'] = 'blocked'
    return row, observed


def plan_member(root, scope, final, canonical, timeout):
    """A grouped member receives the canonical commit; its controls were clean at planning."""
    row = result_row(root, scope)
    observed = observation(root, timeout)
    row.update(before_head=observed['head'], after_head=observed['head'], canonical=str(canonical), propagation=None,
               detached=bool(observed['head']) and not observed['branch'])
    head = {path: bytes.fromhex(value) if value is not None else None for path, value in observed['blobs'].items()}
    row['paths'] = [path for path in PATHS if final[path] != head[path]]
    row['status'] = 'planned' if row['paths'] else 'not_needed'
    if row['paths']:
        observed['detached'] = True
        row['error'] = observed['eligibility'] = eligibility(root, observed, timeout, detached=True)
        if row['error']:
            row['status'] = 'blocked'
    return row, observed


def uncommitted(root, scope, reason):
    """A grouped member that fell back to an independent upgrade is never committed."""
    row = result_row(root, scope)
    row.update(status='uncommitted', reason=reason)
    return row


def fresh_observation(root, observed, timeout):
    fresh = observation(root, timeout)
    if 'eligibility' in observed:
        fresh['eligibility'] = eligibility(root, fresh, timeout, detached=observed.get('detached', False))
    return fresh


def recheck(root, observed, final, timeout):
    current = observation(root, timeout)
    if any(current[key] != observed[key] for key in ('top', 'git_dir', 'branch', 'head', 'index', 'index_fingerprint')) or controls(root) != final:
        c.fail('upgrade.commit_failed', 'Git state or project controls changed before committing; concurrent changes were preserved.', 5,
               root=str(root))
    error = eligibility(root, current, timeout, detached=observed.get('detached', False))
    if error:
        c.fail('upgrade.commit_failed', error['message'], 5, root=str(root))


def sync_index(root, observed, updates, timeout):
    """Hold Git's real index lock while publishing the control-only index update."""
    index = Path(c.git(root, 'rev-parse', '--git-path', 'index', timeout=timeout))
    index = index if index.is_absolute() else root / index
    lock = index.with_name(index.name + '.lock')
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        c.fail('upgrade.commit_failed', 'Another Git writer holds the index lock; its staging was preserved.', 5, root=str(root))
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            before = index.read_bytes() if index.exists() else None
            stream.write(before or b'')
        if (c.digest(before) if before is not None else None) != observed['index_fingerprint']:
            c.fail('upgrade.commit_failed', 'The real index changed before publication; concurrent staging was preserved.', 5, root=str(root))
        c.git(root, 'update-index', '--add', *updates, timeout=timeout, mutating=True, index=lock)
        if (index.read_bytes() if index.exists() else None) != before:
            c.fail('upgrade.commit_failed', 'The real index changed during publication; concurrent staging was preserved.', 5, root=str(root))
        os.replace(lock, index)
    finally:
        lock.with_name(lock.name + '.lock').unlink(missing_ok=True)
        lock.unlink(missing_ok=True)


def execute(row, observed, final, timeout):
    """Use a private index, verify the actual commit, then update only control entries."""
    if row['status'] != 'planned':
        return
    root = Path(row['root'])
    row['status'] = 'failed'
    failure = None
    try:
        recheck(root, observed, final, timeout)
        with tempfile.TemporaryDirectory(prefix='mask-upgrade-index-') as temporary:
            index = Path(temporary) / 'index'
            c.git(root, 'read-tree', observed['head'], timeout=timeout, index=index)
            c.git(root, 'add', '--', *row['paths'], timeout=timeout, index=index, mutating=True)
            tree = c.git(root, 'write-tree', timeout=timeout, index=index)
            entries = c.git(root, 'ls-files', '--stage', '-z', timeout=timeout, index=index, binary=True)
            recheck(root, observed, final, timeout)
            if tree == c.git(root, 'rev-parse', observed['head'] + '^{tree}', timeout=timeout):
                row['status'] = 'not_needed'
                return
            try:
                c.git(root, 'commit', '-m', MESSAGE, '--no-status', timeout=timeout,
                      index=index, mutating=True, commit_hooks=True)
            except c.MaskError as error:
                failure = error
            # A hook or timeout can fail after Git has created a commit.
            after = c.git(root, 'rev-parse', '--verify', 'HEAD^{commit}', timeout=timeout)
            row['after_head'] = after
            if after != observed['head']:
                row['commit'] = after
                actual = c.git(root, 'rev-list', '--parents', '-n', '1', after, timeout=timeout).split()
                actual_tree = c.git(root, 'rev-parse', after + '^{tree}', timeout=timeout)
                actual_message = c.git(root, 'log', '-1', '--format=%B', after, timeout=timeout)
                if actual != [after, observed['head']] or actual_tree != tree or actual_message != MESSAGE:
                    c.fail('upgrade.commit_failed', 'The observed commit has an unexpected parent, contents or message; its effects were preserved.', 5,
                           root=str(root), commit=after)
                if controls(root) != final or c.git(root, 'symbolic-ref', '-q', 'HEAD', optional=True, timeout=timeout) != observed['branch']:
                    c.fail('upgrade.commit_failed', 'Project controls or branch changed during commit; hook effects were preserved.', 5,
                           root=str(root), commit=after)
                if c.git(root, 'ls-files', '--stage', '-z', binary=True, timeout=timeout).hex() != observed['index']:
                    c.fail('upgrade.commit_failed', 'The real index changed during commit; concurrent staging was preserved.', 5,
                           root=str(root), commit=after)
                updates = []
                for entry in entries.split(b'\0'):
                    if not entry:
                        continue
                    metadata, path = entry.split(b'\t', 1)
                    if path in [name.encode('ascii') for name in row['paths']]:
                        mode, oid, stage = metadata.decode('ascii').split()
                        updates.extend(('--cacheinfo', mode + ',' + oid + ',' + path.decode('utf-8')))
                sync_index(root, observed, updates, timeout)
                row['status'] = 'committed'
            elif failure is None:
                c.fail('upgrade.commit_failed', 'Git returned without creating the expected commit.', 5, root=str(root))
            if failure is not None:
                raise failure
    except (c.MaskError, OSError, KeyboardInterrupt) as failure:
        error = failure if isinstance(failure, c.MaskError) else c.MaskError(
            'invocation.interrupted' if isinstance(failure, KeyboardInterrupt) else 'upgrade.commit_failed',
            'Git commit was interrupted; observable effects were preserved.' if isinstance(failure, KeyboardInterrupt) else
            'Git commit bookkeeping failed; observable effects were preserved.', 130 if isinstance(failure, KeyboardInterrupt) else 5)
        row['error'] = error.as_dict()
        # Keep a created commit visible even when a later observation or index update failed.
        try:
            row['after_head'] = c.git(root, 'rev-parse', '--verify', 'HEAD^{commit}', optional=True, timeout=timeout)
            if row['after_head'] and row['after_head'] != row['before_head']:
                row['commit'] = row['after_head']
        except c.MaskError:
            row['status'] = 'unknown'
        if isinstance(failure, KeyboardInterrupt):
            raise


def control_entries(root, commit, paths, timeout):
    """``update-index --cacheinfo`` arguments for the control paths as recorded in ``commit``."""
    updates = []
    for line in c.git(root, 'ls-tree', '-z', commit, '--', *paths, timeout=timeout, binary=True).split(b'\0'):
        if line:
            metadata, path = line.split(b'\t', 1)
            mode, _, oid = metadata.decode('ascii').split()
            updates.extend(('--cacheinfo', mode + ',' + oid + ',' + path.decode('utf-8')))
    return updates


def propagate(row, observed, final, canonical, timeout):
    """Give a grouped member the canonical commit: fast-forward to it, or cherry-pick it.

    The fast-forward moves only the member's checked-out branch (or its detached HEAD) to that very
    commit. Otherwise a commit with the canonical author, message and control blobs is created on the
    member HEAD with a private index, normal hooks and signing. A separate clone first fetches the
    canonical objects by local path without writing FETCH_HEAD or any ref. Nothing is pushed.
    """
    if row['status'] != 'planned':
        return
    root = Path(row['root'])
    source = canonical.get('commit')
    row['canonical_commit'] = source
    if not source or canonical['status'] != 'committed':
        row.update(status='not_attempted', error=c.MaskError('upgrade.canonical_commit_missing', 'The canonical checkout did not commit; nothing was propagated.', 5,
                                                             details=dict(root=str(root), canonical=canonical['root'])).as_dict())
        return
    row['status'] = 'failed'
    failure = None
    try:
        recheck(root, observed, final, timeout)
        if c.git(root, 'cat-file', '-e', source + '^{commit}', timeout=timeout, optional=True) is None:
            c.git(root, 'fetch', '--no-tags', '--no-write-fetch-head', '--quiet', canonical['root'], canonical['branch'],
                  timeout=timeout, mutating=True)
            if c.git(root, 'cat-file', '-e', source + '^{commit}', timeout=timeout, optional=True) is None:
                c.fail('upgrade.commit_failed', 'The canonical commit could not be fetched from the canonical checkout.', 5,
                       root=str(root), commit=source)
        parent = c.git(root, 'rev-parse', source + '^', timeout=timeout)
        updates = control_entries(root, source, row['paths'], timeout)
        if parent == observed['head']:
            row['propagation'] = 'fast_forward'
            recheck(root, observed, final, timeout)
            reference = observed['branch'] or 'HEAD'
            c.git(root, 'update-ref', *([] if observed['branch'] else ['--no-deref']), '-m', 'mask: fast-forward to upgrade commit',
                  reference, source, observed['head'], timeout=timeout, mutating=True)
            row['after_head'] = row['commit'] = source
        else:
            row['propagation'] = 'cherry_pick'
            message = c.git(root, 'log', '-1', '--format=%B', source, timeout=timeout)
            with tempfile.TemporaryDirectory(prefix='mask-upgrade-index-') as temporary:
                index = Path(temporary) / 'index'
                c.git(root, 'read-tree', observed['head'], timeout=timeout, index=index)
                c.git(root, 'update-index', '--add', *updates, timeout=timeout, index=index, mutating=True)
                tree = c.git(root, 'write-tree', timeout=timeout, index=index)
                recheck(root, observed, final, timeout)
                try:
                    c.git(root, 'commit', '-C', source, '--no-status', timeout=timeout, index=index, mutating=True, commit_hooks=True)
                except c.MaskError as error:
                    failure = error
            after = c.git(root, 'rev-parse', '--verify', 'HEAD^{commit}', timeout=timeout)
            row['after_head'] = after
            if after == observed['head']:
                if failure is None:
                    c.fail('upgrade.commit_failed', 'Git returned without creating the expected commit.', 5, root=str(root))
                raise failure
            row['commit'] = after
            actual = c.git(root, 'rev-list', '--parents', '-n', '1', after, timeout=timeout).split()
            if actual != [after, observed['head']] or c.git(root, 'rev-parse', after + '^{tree}', timeout=timeout) != tree or \
                    c.git(root, 'log', '-1', '--format=%B', after, timeout=timeout) != message:
                c.fail('upgrade.commit_failed', 'The observed commit has an unexpected parent, contents or message; its effects were preserved.', 5,
                       root=str(root), commit=after)
        if controls(root) != final or c.git(root, 'symbolic-ref', '-q', 'HEAD', optional=True, timeout=timeout) != observed['branch']:
            c.fail('upgrade.commit_failed', 'Project controls or branch changed during propagation; effects were preserved.', 5,
                   root=str(root), commit=row['commit'])
        if c.git(root, 'ls-files', '--stage', '-z', binary=True, timeout=timeout).hex() != observed['index']:
            c.fail('upgrade.commit_failed', 'The real index changed during propagation; concurrent staging was preserved.', 5,
                   root=str(root), commit=row['commit'])
        sync_index(root, observed, updates, timeout)
        row['status'] = 'committed'
        # No branch names this commit; a later checkout would leave it to the reflog.
        row['detached_only'] = row['detached'] and row['propagation'] == 'cherry_pick'
        if failure is not None:
            raise failure
    except (c.MaskError, OSError, KeyboardInterrupt) as failure:
        error = failure if isinstance(failure, c.MaskError) else c.MaskError(
            'invocation.interrupted' if isinstance(failure, KeyboardInterrupt) else 'upgrade.commit_failed',
            'Git propagation was interrupted; observable effects were preserved.' if isinstance(failure, KeyboardInterrupt) else
            'Git propagation bookkeeping failed; observable effects were preserved.', 130 if isinstance(failure, KeyboardInterrupt) else 5)
        row['error'] = error.as_dict()
        try:
            row['after_head'] = c.git(root, 'rev-parse', '--verify', 'HEAD^{commit}', optional=True, timeout=timeout)
            if row['after_head'] and row['after_head'] != row['before_head']:
                row['commit'] = row['after_head']
        except c.MaskError:
            row['status'] = 'unknown'
        if isinstance(failure, KeyboardInterrupt):
            raise
