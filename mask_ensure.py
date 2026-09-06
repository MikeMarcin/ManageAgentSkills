"""Machine-local readiness authority and selected-consumer orchestration."""
from __future__ import annotations

import copy
from pathlib import Path

import mask_core as c
import mask_fs as fs


EVENTS = {'manual', 'startup', 'post-checkout', 'post-merge', 'post-rewrite', 'post-commit'}


def policy(home):
    value = c.read_json(home / 'integration.json', default=dict(schema_version=1, approvals={}))
    c.fields(value, ('schema_version', 'approvals'), family='integration')
    if not isinstance(value['approvals'], dict):
        c.fail('integration.invalid', 'Approvals must be a map.')
    for root, entry in value['approvals'].items():
        if not isinstance(root, str) or not Path(root).is_absolute():
            c.fail('integration.invalid', 'Approval roots must be absolute.')
        c.fields(entry, ('identity',), ('common_dir', 'common_identity'), family='integration')
        for field in ('identity', 'common_identity'):
            if field in entry:
                identity = entry[field]
                c.fields(identity, ('device', 'inode'), family='integration')
                if any(type(n) is not int or n < 0 for n in identity.values()):
                    c.fail('integration.invalid', 'Invalid approval identity.')
        if ('common_dir' in entry) != ('common_identity' in entry) or ('common_dir' in entry and (not isinstance(entry['common_dir'], str) or not Path(entry['common_dir']).is_absolute())):
            c.fail('integration.invalid', 'Invalid linked-worktree approval.')
    return value


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
        if entry.get('common_dir') == str(common) and original.is_dir() and c.identity(original) == entry['identity'] and common.is_dir() and c.identity(common) == entry['common_identity'] and common_directory(original) == common:
            return True
    return False


def integration(args, output, home):
    approval = policy(home)
    root = c.project_root(getattr(args, 'project', None))
    if args.command == 'integration.inspect':
        output['data'] = dict(root=str(root), approved=authorized(root, approval), host_load='not_verified',
                              coverage=dict(git=False, startup=False))
        return
    proposal = copy.deepcopy(approval)
    if args.command == 'integration.approve':
        entry = dict(identity=c.identity(root))
        if getattr(args, 'linked_worktrees', False):
            common = common_directory(root)
            top = c.git(root, 'rev-parse', '--show-toplevel', optional=True)
            if common is None or top is None or Path(top).resolve() != root:
                c.fail('integration.invalid', 'Linked-worktree approval requires a Git worktree root.', 4)
            entry.update(common_dir=str(common), common_identity=c.identity(common))
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
    root = c.project_root(getattr(args, 'project', None))
    approval = policy(home)
    if not authorized(root, approval):
        output['data']['readiness'] = 'approval_required'
        c.fail('integration.approval_required', 'Approve this physical project before automatic readiness.', 4, root=str(root))
    config = c.config(c.read_json(home / 'config.json'))
    state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
    register = [str(root)] if str(root) not in state['projects'] else []
    planned = fs.plan(config, state, [root], register=register, home=home,
                      operation='project.register' if register else 'apply', source_status=False)
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
        for observation in planned['projects']:
            if c.digest(c.read_text(Path(observation['manifest_path']), 'manifest').encode()) != observation['manifest_bytes']:
                c.fail('plan.stale', 'Declaration changed before execution.', 4)
        fs.execute(planned, home, output)
    output['data']['readiness'] = 'would_reconcile' if output['dry_run'] and planned['would_change'] else 'ready_legacy_unpinned'


def dispatch(args, output, home):
    if args.command == 'ensure':
        return ensure(args, output, home)
    return integration(args, output, home)
