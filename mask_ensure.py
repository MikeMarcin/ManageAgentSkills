"""Machine-local readiness authority and selected-consumer orchestration."""
from __future__ import annotations

import copy
import re
from pathlib import Path
from urllib.parse import urlsplit

import mask_core as c
import mask_fs as fs


EVENTS = {'manual', 'startup', 'post-checkout', 'post-merge', 'post-rewrite', 'post-commit'}


def validate_policy(value):
    c.fields(value, ('schema_version', 'approvals'), ('repositories',), family='integration')
    if not isinstance(value.get('repositories', []), list):
        c.fail('integration.invalid', 'Repository approvals must be a list.')
    seen = set()
    for entry in value.get('repositories', []):
        c.fields(entry, ('repository', 'under', 'identity'), family='integration')
        repository_identity(entry['repository'])
        if not isinstance(entry['under'], str) or not Path(entry['under']).is_absolute():
            c.fail('integration.invalid', 'Clone boundaries must be absolute.')
        c.fields(entry['identity'], ('device', 'inode'), family='integration')
        if any(type(number) is not int for number in entry['identity'].values()):
            c.fail('integration.invalid', 'Invalid clone-boundary identity.')
        key = (entry['repository'], entry['under'])
        if key in seen:
            c.fail('integration.invalid', 'Duplicate repository approval.')
        seen.add(key)
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


def repository_identity(value):
    if not isinstance(value, str) or not value or value.startswith('-') or any(ord(ch) < 32 for ch in value):
        c.fail('integration.invalid', 'Invalid repository identity.')
    if Path(value).is_absolute():
        return value
    if re.fullmatch(r'[A-Za-z0-9._-]+@[A-Za-z0-9.-]+:[A-Za-z0-9._/-]+', value):
        return value
    try:
        parsed = urlsplit(value)
    except ValueError:
        c.fail('integration.invalid', 'Invalid repository identity.')
    if parsed.scheme not in ('https', 'ssh') or not parsed.hostname or parsed.password is not None or parsed.query or parsed.fragment or (parsed.scheme == 'https' and parsed.username is not None):
        c.fail('integration.invalid', 'Use an absolute local repository or credential-free HTTPS/SSH identity.')
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
    for entry in approval.get('repositories', []):
        boundary = Path(entry['under'])
        if root.is_relative_to(boundary) and boundary.is_dir() and boundary.resolve() == boundary and c.identity(boundary) == entry['identity']:
            remote = c.git(root, 'remote', 'get-url', 'origin', optional=True)
            if remote is not None and repository_identity(remote) == entry['repository']:
                return True
    return False


def integration(args, output, home):
    approval = policy(home)
    if args.command == 'integration.inspect':
        import mask_integration as integrations
        state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
        if getattr(args, 'agent', None) not in (None, 'claude', 'codex'):
            c.fail('invocation.invalid', 'Choose a supported agent.', 2)
        root = integrations.host_root(home) if getattr(args, 'agent', None) and not getattr(args, 'project', None) else c.project_root(getattr(args, 'project', None))
        record = state['projects'].get(str(root))
        output['data'] = dict(root=str(root), approved=authorized(root, approval), host_load='not_verified',
                              registration_identity=c.digest(record['root_identity']) if record else None,
                              coverage=integrations.inspect_coverage(home, root))
        return
    repository, under, project = getattr(args, 'repository', None), getattr(args, 'under', None), getattr(args, 'project', None)
    if bool(repository) == bool(project) or bool(repository) != bool(under) or repository and (getattr(args, 'linked_worktrees', False) or getattr(args, 'inactive_branches', False)):
        c.fail('invocation.invalid', 'Choose --project PATH or --repository ID --under ROOT; branch flags require --project.', 2)
    proposal = copy.deepcopy(approval)
    root = None
    selected_approval = None
    if repository:
        repository_identity(repository)
        boundary = Path(under).expanduser().resolve()
        if args.command == 'integration.approve' and not boundary.is_dir():
            c.fail('integration.invalid', 'The approved clone boundary must exist.', 4)
        values = [item for item in proposal.get('repositories', []) if (item['repository'], item['under']) != (repository, str(boundary))]
        if args.command == 'integration.approve':
            entry = dict(repository=repository, under=str(boundary), identity=c.identity(boundary))
            values.append(entry)
            selected_approval = entry
        proposal['repositories'] = sorted(values, key=lambda item: (item['repository'], item['under']))
    else:
        root = c.project_root(project) if args.command == 'integration.approve' else Path(project).expanduser().resolve()
    if root is not None and args.command == 'integration.approve':
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
        selected_approval = entry
    elif root is not None:
        proposal['approvals'].pop(str(root), None)
        if root.is_dir() and authorized(root, proposal):
            c.fail('integration.inherited_authority', 'Revoke the linked-worktree or repository-boundary approval that grants this root authority.', 4)
    plan_hash = c.digest(dict(before=approval, after=proposal))
    if getattr(args, 'expect_plan_hash', plan_hash) != plan_hash:
        c.fail('plan.stale', 'Integration approval changed; inspect a new preview.', 4)
    output['data'] = dict(root=str(root) if root is not None else None, plan_hash=plan_hash, approval=selected_approval)
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
    config = c.config(c.read_json(home / 'config.json'))
    state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
    selection = getattr(args, 'project', None)
    try:
        root = c.project_root(selection)
    except c.MaskError as error:
        if selection is None and error.code == 'project.not_found' and event == 'startup' and state.get('user'):
            root = None
        elif selection is None and error.code == 'manifest.missing':
            root = c.project_root(initializing=True)
        else:
            raise
    approval = policy(home)
    if root is not None and not authorized(root, approval):
        output['data']['readiness'] = 'approval_required'
        c.fail('integration.approval_required', 'Approve this physical project before automatic readiness.', 4, root=str(root))
    observation = workspace_observation(root) if root is not None else None
    if observation and observation['index'] and any(line.split('\t', 1)[0].split()[-1] != '0' for line in observation['index'].splitlines()):
        c.fail('readiness.blocked', 'The declaration has unresolved index conflicts.', 4)
    inactive = []
    proposed_approval = copy.deepcopy(approval)
    entry = proposed_approval['approvals'].get(str(root))
    if observation and observation['manifest'] is None:
        if not inactive_branch(root, state['projects'].get(str(root)), entry, observation):
            c.fail('manifest.missing', 'Missing declaration is not a proven opted-in inactive branch.', 4)
        inactive = [str(root)]
    elif observation and entry is not None and observation['head'] is not None:
        tracked = c.git(root, 'show', observation['head'] + ':./.mask.json', optional=True)
        if tracked is not None and tracked == observation['manifest'].strip() and not observation['unsafe']:
            manifest_digest = c.digest(c.manifest(c.parse_json(observation['manifest'], 'manifest')))
            if entry.get('tracked', {}).get('manifest_digest') != manifest_digest:
                entry['tracked'] = dict(head=observation['head'], manifest_digest=manifest_digest)
    roots = [root] if root is not None else []
    observations = [observation] if observation else []
    user_root = Path(state['user']['root']) if event == 'startup' and state.get('user') else None
    if user_root is not None:
        roots.append(user_root)
        observations.append(workspace_observation(user_root, scope='user', home=home))
    register = [str(root)] if root is not None and str(root) not in state['projects'] else []
    planned = fs.plan(config, state, roots, register=register, home=home, user_root=user_root,
                      operation='ensure.deactivate' if inactive else 'ensure', source_status=False, inactive=inactive)
    policy_before = c.read_text(home / 'integration.json', 'integration', missing=True)
    policy_after = c.text_json(proposed_approval) if proposed_approval != approval else policy_before
    planned['intent']['controls'] = dict(workspaces=observations, policy_before=policy_before, policy_after=policy_after)
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
        if policy(home) != approval or root is not None and not authorized(root, approval):
            c.fail('plan.stale', 'Readiness authority changed before execution.', 4)
        fs.execute(planned, home, output)
    output['data']['readiness'] = 'would_reconcile' if output['dry_run'] and planned['would_change'] else 'inactive_on_branch' if inactive else 'ready_legacy_unpinned'


def dispatch(args, output, home):
    if args.command == 'ensure':
        return ensure(args, output, home)
    if args.command == 'workspace.forget':
        return forget(args, output, home)
    return integration(args, output, home)


def workspace_observation(root, *, scope='project', home=None):
    head = c.git(root, 'rev-parse', '--verify', 'HEAD', optional=True) if scope == 'project' else None
    git_dir = c.git(root, 'rev-parse', '--absolute-git-dir', optional=True) if scope == 'project' else None
    unsafe = False
    index = None
    if git_dir:
        directory = Path(git_dir)
        unsafe = (c.git(root, 'config', '--bool', 'core.sparseCheckout', optional=True) == 'true'
                  or bool(c.git(root, 'ls-files', '--unmerged'))
                  or any(c.kind(directory / name) != 'missing' for name in ('MERGE_HEAD', 'rebase-merge', 'rebase-apply', 'CHERRY_PICK_HEAD', 'REVERT_HEAD')))
        index = c.git(root, 'ls-files', '--stage', '--', '.mask.json')
    result = dict(root=str(root), identity=c.identity(root), head=head, git_dir=git_dir,
                git_identity=c.identity(Path(git_dir)) if git_dir else None,
                index=index, unsafe=unsafe, manifest=c.read_text(c.declaration_path(root, scope, home), 'manifest', missing=True))
    if scope == 'user':
        result['scope'] = 'user'
    return result


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
        c.fields(observation, ('root', 'identity', 'head', 'git_dir', 'git_identity', 'index', 'unsafe', 'manifest'), ('scope',), family='recovery')
        roots.append(observation['root'])
        if observation['root'] not in pending['selected']:
            c.fail('recovery.conflict', 'Unselected readiness root.', 8)
        selected_state = pending['before_state'] if observation['root'] in c.consumer_records(pending['before_state']) else pending['after_state']
        if observation.get('scope', 'project') != c.consumer_scope(selected_state, observation['root']):
            c.fail('recovery.conflict', 'Readiness scope differs from ownership.', 8)
        if observation['manifest'] is not None:
            c.manifest(c.parse_json(observation['manifest'], 'manifest'))
    if sorted(roots) != sorted(pending['selected']):
        c.fail('recovery.conflict', 'Readiness control coverage differs from selection.', 8)
    before, after = [validate_policy(c.parse_json(controls['policy_' + side], 'integration')) if controls['policy_' + side] is not None else dict(schema_version=1, approvals={}) for side in ('before', 'after')]
    # Readiness may record tracked evidence, but cannot grant or revoke authority.
    for value in (before, after):
        for root in roots:
            if root in value['approvals']:
                value['approvals'][root].pop('tracked', None)
    if before != after:
        c.fail('recovery.conflict', 'Readiness journal changes authority.', 8)


def check_controls(pending, home):
    controls = pending['controls']
    if c.read_text(home / 'integration.json', 'integration', missing=True) not in (controls['policy_before'], controls['policy_after']):
        c.fail('recovery.conflict', 'Readiness authority changed after preparation.', 8)
    for expected in controls['workspaces']:
        root = Path(expected['root'])
        if not root.is_dir() or root.resolve() != root or workspace_observation(root, scope=expected.get('scope', 'project'), home=home) != expected:
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
