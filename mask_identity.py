"""Reviewed device-number recovery without weakening ordinary identity checks."""
from __future__ import annotations

import os
from pathlib import Path

import mask_core as c

FILES = ('state.json', 'integration.json', 'integrations.json', 'selection-policy.json')


def rebound(path, expected):
    """Only a canonical real directory with its original inode is eligible."""
    if c.kind(path) != 'directory' or path.resolve() != path:
        c.fail('project.identity_changed', 'Rebind requires the original canonical directory.', 4, root=str(path))
    actual = c.identity(path)
    if actual['inode'] != expected['inode']:
        c.fail('project.identity_changed', 'Directory inode changed; rebind refuses a replacement.', 4, root=str(path))
    return actual


def transition(before, root, scope):
    """Derive the only allowed registry/authority transition from validated bytes."""
    import mask_ensure as ensure
    import mask_integration as integration
    import mask_selection as selection
    models = {
        'state.json': c.state(c.parse_json(before['state.json'], 'state')),
        'integration.json': ensure.validate_policy(c.parse_json(before['integration.json'], 'integration')) if before['integration.json'] else None,
        'integrations.json': integration.validate_registration(c.parse_json(before['integrations.json'], 'integration')) if before['integrations.json'] else None,
        'selection-policy.json': selection.parse_policy_text(before['selection-policy.json']) if before['selection-policy.json'] else None,
    }
    state = models['state.json']
    record = c.consumer_records(state).get(str(root))
    if record is None or c.consumer_scope(state, root) != scope:
        c.fail(scope + '.not_registered', 'Rebind requires an existing registration.', 4)
    original = record['root_identity']
    current = rebound(root, original)
    record['root_identity'] = current
    policy = models['integration.json']
    entry = policy['approvals'].get(str(root)) if policy else None
    if entry:
        # Preserve flags, fetch grants and tracked evidence; do not add authority.
        entry['identity'] = rebound(root, entry['identity'])
        if 'common_dir' in entry:
            common = Path(entry['common_dir'])
            if ensure.common_directory(root) != common:
                c.fail('integration.drift', 'Approved Git common directory changed.', 4)
            entry['common_identity'] = rebound(common, entry['common_identity'])
    ownership = models['integrations.json']
    for installed in ownership['installations'].values() if ownership else ():
        if installed['root'] != str(root):
            continue
        common = Path(installed['common'])
        if installed['mode'] not in c.ADAPTERS and ensure.common_directory(root) != common:
            c.fail('integration.drift', 'Installed Git common directory changed.', 4)
        installed['identity'] = rebound(root, installed['identity'])
        installed['common_identity'] = rebound(common, installed['common_identity'])
    local = models['selection-policy.json']
    for override in local['overrides'] if local else ():
        if override['root'] == str(root):
            if override['identity'] != original:
                c.fail('selection_policy.invalid', 'Override differs from registered identity.', 4)
            override['identity'] = current
    after = dict(before)
    for name, value in models.items():
        if value is not None and value != c.parse_json(before[name]):
            if name == 'state.json':
                value['generation'] += 1
            after[name] = c.text_json(value)
    return after


def read_controls(home):
    return {name: c.read_text(home / name, 'state' if name == 'state.json' else 'integration', missing=name != 'state.json')
            for name in FILES}


def check_links(root, record):
    """Rebinding never adopts changed links or follows destination parents."""
    for relative, owned in record['links'].items():
        leaf = root / relative
        c.parents_safe(root, leaf)
        observed = c.kind(leaf)
        if observed not in ('missing', 'symlink'):
            c.fail('target.collision', 'Rebind preserves conflicting content.', 4, path=str(leaf))
        if observed == 'symlink':
            if os.readlink(leaf) != owned['link_text']:
                c.fail('target.drift', 'Owned link changed; rebind refuses it.', 4, path=str(leaf))


def validate_pending(pending, home):
    c.fields(pending, ('schema_version', 'operation', 'root', 'scope', 'before', 'after'), family='recovery')
    if pending['operation'] != 'directory.rebind' or pending['scope'] not in ('project', 'user'):
        c.fail('recovery.conflict', 'Invalid directory rebind intent.', 8)
    root = Path(pending['root'])
    if not root.is_absolute() or str(root) != pending['root']:
        c.fail('recovery.conflict', 'Noncanonical rebind root.', 8)
    for side in ('before', 'after'):
        c.fields(pending[side], FILES, family='recovery', versions=())
    if transition(pending['before'], root, pending['scope']) != pending['after']:
        c.fail('recovery.conflict', 'Directory rebind changes unrelated controls.', 8)
    record = c.consumer_records(c.state(c.parse_json(pending['before']['state.json'])))[str(root)]
    check_links(root, record)
    for name, actual in read_controls(home).items():
        if actual not in (pending['before'][name], pending['after'][name]):
            c.fail('recovery.conflict', 'Rebind control changed after preparation.', 8, file=name)


def restore(pending, home, side):
    import mask_fs as fs
    validate_pending(pending, home)
    for name in FILES:
        if pending['before'][name] == pending['after'][name]:
            continue
        validate_pending(pending, home)
        c.atomic_text(home / name, pending[side][name], c.read_text(home / name))
        fs.checkpoint('rebind-control')
    fs.clear_pending(home, pending)


def rebind(args, output, home):
    import mask_consent as consent
    import mask_fs as fs
    import mask_present as present
    if c.kind(home / 'pending.json') != 'missing':
        c.fail('recovery.required', 'Recover the pending operation before rebinding.', 8)
    before = read_controls(home)
    state = c.state(c.parse_json(before['state.json'], 'state'))
    # consumer() normally rejects identity drift; selection alone is needed here.
    scope = 'user' if getattr(args, 'user', False) else 'project'
    if scope == 'user':
        record = state.get('user')
        if not record:
            c.fail('user.not_registered', 'Personal scope is not registered.', 4)
        root = Path(record['root'])
    else:
        root = c.project_root(getattr(args, 'project', None))
    after = transition(before, root, scope)
    record = c.consumer_records(state)[str(root)]
    check_links(root, record)
    pending = dict(schema_version=1, operation='directory.rebind', root=str(root), scope=scope, before=before, after=after)
    plan_hash = c.digest(pending)
    output['data'] = dict(root=str(root), scope=scope, rebind=dict(before=record['root_identity'], after=c.identity(root)), plan_hash=plan_hash,
                          files=[name for name in FILES if before[name] != after[name]])
    output['would_change'] = before != after
    output['actions'] = [dict(kind='directory.rebind', path=str(root), status='planned')] if before != after else []
    if getattr(args, 'expect_plan_hash', plan_hash) != plan_hash:
        c.fail('plan.stale', 'Rebind inputs changed; preview again.', 4)
    if output['dry_run'] or before == after:
        return
    if not getattr(args, 'expect_plan_hash', None):
        if not consent.interactive(args):
            c.fail('confirmation.required', 'Preview mask register --rebind --dry-run --json, then use --approve-plan HASH.', 4)
        proposal = dict(question='Rebind this unchanged directory and its existing approvals?')
        if not consent.ask(proposal, f"Directory: {present.clean(root)}\nOriginal inode matches; device identity will be updated.\n"):
            c.fail('confirmation.declined', 'Rebind declined; controls were preserved.', 4)
    with c.writer_lock(home):
        if c.kind(home / 'pending.json') != 'missing':
            c.fail('recovery.required', 'Recover the pending operation first.', 8)
        if read_controls(home) != before or transition(before, root, scope) != after:
            c.fail('plan.stale', 'Rebind changed during review; nothing applied.', 4)
        validate_pending(pending, home)
        c.atomic_text(home / 'pending.json', c.text_json(pending), None)
        fs.checkpoint('rebind-intent')
        try:
            restore(pending, home, 'after')
        except (Exception, KeyboardInterrupt):
            output.update(changed=True, transaction='partial')
            c.fail('recovery.required', 'Rebind was interrupted; inspect mask recover.', 8)
    output.update(changed=True, transaction='committed')


def recover(home, output, mode):
    pending = c.read_json(home / 'pending.json', 'recovery')
    validate_pending(pending, home)
    output['data'] = dict(pending=pending, recovery_mode=mode)
    if mode == 'inspect' or output['dry_run']:
        return
    restore(pending, home, 'after' if mode == 'complete' else 'before')
    output.update(changed=True, would_change=True, transaction='committed' if mode == 'complete' else 'rolled_back')
