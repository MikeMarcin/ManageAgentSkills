"""Machine-local readiness authority and selected-consumer orchestration."""
from __future__ import annotations

import copy
from pathlib import Path

import mask_core as c
import mask_fs as fs


EVENTS = {'manual', 'startup', 'post-checkout', 'post-merge', 'post-rewrite', 'post-commit'}


def validate_policy(value):
    c.fields(value, ('schema_version', 'approvals'), family='integration')
    if not isinstance(value['approvals'], dict):
        c.fail('integration.invalid', 'Approvals must be a map.')
    for root, entry in value['approvals'].items():
        if not isinstance(root, str) or not Path(root).is_absolute():
            c.fail('integration.invalid', 'Approval roots must be absolute.')
        c.fields(entry, ('identity',), ('common_dir', 'common_identity', 'linked_worktrees', 'inactive_branches', 'tracked'), family='integration')
        for flag in ('linked_worktrees', 'inactive_branches'):
            if flag in entry and type(entry[flag]) is not bool:
                c.fail('integration.invalid', 'Approval flags must be booleans.')
        if 'tracked' in entry:
            c.fields(entry['tracked'], ('head', 'manifest_digest'), family='integration')
            if any(not isinstance(value, str) for value in entry['tracked'].values()):
                c.fail('integration.invalid', 'Invalid tracked-declaration evidence.')
        for field in ('identity', 'common_identity'):
            if field in entry:
                identity = entry[field]
                c.fields(identity, ('device', 'inode'), family='integration')
                if any(type(n) is not int or n < 0 for n in identity.values()):
                    c.fail('integration.invalid', 'Invalid approval identity.')
        if ('common_dir' in entry) != ('common_identity' in entry) or ('common_dir' in entry and (not isinstance(entry['common_dir'], str) or not Path(entry['common_dir']).is_absolute())):
            c.fail('integration.invalid', 'Invalid linked-worktree approval.')
    return value


def policy(home):
    return validate_policy(c.read_json(home / 'integration.json', default=dict(schema_version=1, approvals={})))


def common_directory(root):
    name = c.git(root, 'rev-parse', '--git-common-dir', optional=True)
    return (root / name).resolve() if name else None


def authorized(root, approval):
    entry = approval['approvals'].get(str(root))
    if entry is not None:
        return c.identity(root) == entry['identity']
    # Common-directory authority is only for worktree roots, never nested paths.
    top = c.git(root, 'rev-parse', '--show-toplevel', optional=True)
    if top is None or Path(top).resolve() != root:
        return False
    common = common_directory(root)
    for key, entry in approval['approvals'].items():
        original = Path(key)
        if entry.get('linked_worktrees') and entry.get('common_dir') == str(common) and original.is_dir() and c.identity(original) == entry['identity'] and common.is_dir() and c.identity(common) == entry['common_identity'] and common_directory(original) == common:
            return True
    return False


def integration(args, output, home):
    approval = policy(home)
    root = c.project_root(getattr(args, 'project', None))
    if args.command == 'integration.inspect':
        state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
        record = state['projects'].get(str(root))
        output['data'] = dict(root=str(root), approved=authorized(root, approval), host_load='not_verified',
                              registration_identity=c.digest(record['root_identity']) if record else None,
                              coverage=dict(git=False, startup=False))
        return
    proposal = copy.deepcopy(approval)
    if args.command == 'integration.approve':
        entry = dict(identity=c.identity(root), linked_worktrees=getattr(args, 'linked_worktrees', False),
                     inactive_branches=getattr(args, 'inactive_branches', False))
        common = common_directory(root)
        if common is not None:
            entry.update(common_dir=str(common), common_identity=c.identity(common))
        if getattr(args, 'linked_worktrees', False):
            common = common_directory(root)
            top = c.git(root, 'rev-parse', '--show-toplevel', optional=True)
            if common is None or top is None or Path(top).resolve() != root:
                c.fail('integration.invalid', 'Linked-worktree approval requires a Git worktree root.', 4)
            entry.update(common_dir=str(common), common_identity=c.identity(common))
        previous = approval['approvals'].get(str(root), {})
        if previous.get('identity') == entry['identity'] and 'tracked' in previous:
            entry['tracked'] = previous['tracked']
        proposal['approvals'][str(root)] = entry
    else:
        proposal['approvals'].pop(str(root), None)
    plan_hash = c.digest(dict(before=approval, after=proposal))
    if getattr(args, 'expect_plan_hash', plan_hash) != plan_hash:
        c.fail('plan.stale', 'Integration approval changed; inspect a new preview.', 4)
    output['data'] = dict(root=str(root), plan_hash=plan_hash, approval=proposal['approvals'].get(str(root)))
    output['would_change'] = proposal != approval
    if proposal != approval:
        output['actions'] = [dict(kind=args.command, status='planned', path=str(home / 'integration.json'))]
        if not output['dry_run']:
            before = c.read_text(home / 'integration.json', 'integration', missing=True)
            if policy(home) != approval:
                c.fail('plan.stale', 'Integration policy changed.', 4)
            c.atomic_text(home / 'integration.json', c.text_json(proposal), before)
            output.update(changed=True, transaction='committed')


def ensure(args, output, home):
    event = getattr(args, 'event', 'manual')
    if event not in EVENTS:
        c.fail('invocation.invalid', 'Unsupported readiness event.', 2)
    output['data'] = dict(readiness='blocked', host_load='not_verified', event=event)
    if c.kind(home / 'pending.json') != 'missing':
        c.fail('recovery.required', 'Inspect and recover the pending operation first.', 8)
    selection = getattr(args, 'project', None)
    try:
        root = c.project_root(selection)
    except c.MaskError as error:
        if selection is not None or error.code != 'manifest.missing':
            raise
        # Missing declarations may be a verified inactive branch at the boundary.
        root = c.project_root(initializing=True)
    approval = policy(home)
    if not authorized(root, approval):
        output['data']['readiness'] = 'approval_required'
        c.fail('integration.approval_required', 'Approve this physical project before automatic readiness.', 4, root=str(root))
    config = c.config(c.read_json(home / 'config.json'))
    state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
    observation = workspace_observation(root)
    if observation['index'] and any(line.split('\t', 1)[0].split()[-1] != '0' for line in observation['index'].splitlines()):
        c.fail('readiness.blocked', 'The declaration has unresolved index conflicts.', 4)
    inactive = []
    proposed_approval = copy.deepcopy(approval)
    entry = proposed_approval['approvals'].get(str(root))
    if observation['manifest'] is None:
        if not inactive_branch(root, state['projects'].get(str(root)), entry, observation):
            c.fail('manifest.missing', 'Missing declaration is not a proven opted-in inactive branch.', 4)
        inactive = [str(root)]
    elif entry is not None and observation['head'] is not None:
        tracked = c.git(root, 'show', observation['head'] + ':./.mask.json', optional=True)
        if tracked is not None and tracked == observation['manifest'].strip() and not observation['unsafe']:
            manifest_digest = c.digest(c.manifest(c.parse_json(observation['manifest'], 'manifest')))
            if entry.get('tracked', {}).get('manifest_digest') != manifest_digest:
                entry['tracked'] = dict(head=observation['head'], manifest_digest=manifest_digest)
    register = [str(root)] if str(root) not in state['projects'] else []
    planned = fs.plan(config, state, [root], register=register, home=home,
                      operation='ensure.deactivate' if inactive else 'ensure', source_status=False, inactive=inactive)
    policy_before = c.read_text(home / 'integration.json', 'integration')
    policy_after = c.text_json(proposed_approval) if proposed_approval != approval else policy_before
    planned['intent']['controls'] = dict(workspaces=[observation], policy_before=policy_before, policy_after=policy_after)
    planned['plan_hash'] = c.digest(dict(plan=planned['plan_hash'], controls=planned['intent']['controls']))
    if policy_after != policy_before:
        planned['actions'].append(dict(kind='integration.record', status='planned', path=str(home / 'integration.json')))
        planned['would_change'] = True
    fs.public_plan(planned, output)
    output['data'].update(readiness='blocked', host_load='not_verified', event=event, network='none')
    fs.ensure_applicable(planned)
    if getattr(args, 'check', False):
        if planned['would_change']:
            output['data']['readiness'] = 'drifted'
            c.fail('readiness.drift', 'Approved deployment requires reconciliation.', 7)
    elif not output['dry_run']:
        # Recheck mutable inputs under the same writer lock, with no second payload scan.
        if policy(home) != approval or not authorized(root, approval):
            c.fail('plan.stale', 'Readiness authority changed before execution.', 4)
        fs.execute(planned, home, output)
    output['data']['readiness'] = 'would_reconcile' if output['dry_run'] and planned['would_change'] else 'inactive_on_branch' if inactive else 'ready_legacy_unpinned'


def dispatch(args, output, home):
    if args.command == 'ensure':
        return ensure(args, output, home)
    if args.command == 'workspace.forget':
        return forget(args, output, home)
    return integration(args, output, home)


def workspace_observation(root):
    head = c.git(root, 'rev-parse', '--verify', 'HEAD', optional=True)
    git_dir = c.git(root, 'rev-parse', '--absolute-git-dir', optional=True)
    unsafe = False
    index = None
    if git_dir:
        directory = Path(git_dir)
        unsafe = (c.git(root, 'config', '--bool', 'core.sparseCheckout', optional=True) == 'true'
                  or bool(c.git(root, 'ls-files', '--unmerged'))
                  or any(c.kind(directory / name) != 'missing' for name in ('MERGE_HEAD', 'rebase-merge', 'rebase-apply', 'CHERRY_PICK_HEAD', 'REVERT_HEAD')))
        index = c.git(root, 'ls-files', '--stage', '--', '.mask.json')
    return dict(root=str(root), identity=c.identity(root), head=head, git_dir=git_dir,
                git_identity=c.identity(Path(git_dir)) if git_dir else None,
                index=index, unsafe=unsafe, manifest=c.read_text(root / '.mask.json', 'manifest', missing=True))


def inactive_branch(root, record, entry, observation):
    if not record or not entry or not entry.get('inactive_branches') or not entry.get('tracked'):
        return False
    c.registered_root(root, record)
    tracked = entry['tracked']
    if observation['unsafe'] or not observation['head'] or observation['index'] or tracked['manifest_digest'] != record['last_manifest_digest']:
        return False
    if c.git(root, 'cat-file', '-e', observation['head'] + ':./.mask.json', optional=True) is not None:
        return False
    text = c.git(root, 'show', tracked['head'] + ':./.mask.json', optional=True)
    return text is not None and c.digest(c.manifest(c.parse_json(text, 'manifest'))) == tracked['manifest_digest']


def validate_controls(pending, home):
    if pending['operation'] not in ('ensure', 'ensure.deactivate') or pending['manifests'] or 'git' in pending or 'launcher' in pending:
        c.fail('recovery.conflict', 'Invalid readiness journal operation.', 8)
    controls = pending['controls']
    c.fields(controls, ('workspaces', 'policy_before', 'policy_after'), family='recovery')
    if not isinstance(controls['workspaces'], list):
        c.fail('recovery.conflict', 'Invalid readiness observations.', 8)
    roots = []
    for observation in controls['workspaces']:
        c.fields(observation, ('root', 'identity', 'head', 'git_dir', 'git_identity', 'index', 'unsafe', 'manifest'), family='recovery')
        roots.append(observation['root'])
        if observation['root'] not in pending['selected']:
            c.fail('recovery.conflict', 'Unselected readiness root.', 8)
        if observation['manifest'] is not None:
            c.manifest(c.parse_json(observation['manifest'], 'manifest'))
    if sorted(roots) != sorted(pending['selected']):
        c.fail('recovery.conflict', 'Readiness control coverage differs from selection.', 8)
    before, after = [validate_policy(c.parse_json(controls['policy_' + side], 'integration')) for side in ('before', 'after')]
    # Readiness may record tracked evidence, but cannot grant or revoke authority.
    for value in (before, after):
        for root in roots:
            if root in value['approvals']:
                value['approvals'][root].pop('tracked', None)
    if before != after:
        c.fail('recovery.conflict', 'Readiness journal changes authority.', 8)


def check_controls(pending, home):
    controls = pending['controls']
    if c.read_text(home / 'integration.json', 'integration') not in (controls['policy_before'], controls['policy_after']):
        c.fail('recovery.conflict', 'Readiness authority changed after preparation.', 8)
    for expected in controls['workspaces']:
        root = Path(expected['root'])
        if not root.is_dir() or root.resolve() != root or workspace_observation(root) != expected:
            c.fail('recovery.conflict', 'Readiness worktree or declaration changed after preparation.', 8, root=str(root))


def restore_controls(pending, home, side):
    check_controls(pending, home)
    controls = pending['controls']
    if controls['policy_before'] != controls['policy_after']:
        c.atomic_text(home / 'integration.json', controls['policy_' + side], c.read_text(home / 'integration.json', 'integration'))


def forget(args, output, home):
    root = Path(args.path).expanduser().absolute()
    state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
    record = state['projects'].get(str(root))
    if record is None or args.expect_identity != c.digest(record['root_identity']):
        c.fail('project.identity_changed', 'Expected registration identity does not match.', 4)
    config = c.config(c.read_json(home / 'config.json'))
    missing = c.kind(root) == 'missing'
    if missing:
        entry = policy(home)['approvals'].get(str(root), {})
        common = Path(entry.get('common_dir', ''))
        if not common.is_absolute() or not common.is_dir() or c.identity(common) != entry.get('common_identity'):
            c.fail('project.unavailable', 'Cannot verify removal from the original Git repository.', 4)
        worktrees = c.git(common, 'worktree', 'list', '--porcelain')
        if any(line == 'worktree ' + str(root) for line in worktrees.splitlines()):
            c.fail('project.unavailable', 'Git still records this worktree; missing storage is not removal.', 4)
    planned = fs.plan(config, state, [root], unregister=[str(root)], keep_links=missing,
                      operation='project.unregister', home=home, source_status=False)
    fs.public_plan(planned, output)
    fs.ensure_applicable(planned)
    if not output['dry_run']:
        fs.execute(planned, home, output)
