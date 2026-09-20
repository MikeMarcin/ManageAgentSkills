"""Explicit version holds preserve selectors and change no resolved version."""
import copy

import mask_core as c
import mask_fs as fs
import mask_pinned as pinned
import mask_resolve as r


def dispatch(args, output, home):
    import mask_task
    import mask_lifecycle
    state, config = mask_task.machine(home)
    root, scope, key, record = mask_task.consumer(args, state, home, creating=False)
    if record is None:
        c.fail(scope + '.not_registered', 'Register this checkout before pinning its skills.', 4)
    if record.get('mode') == 'dev-link':
        c.fail('dev_link.active', 'Return development links to locked installations before pinning.', 4)
    declaration = r.selection(c.read_json(c.declaration_path(root, scope, home), 'manifest'))
    lock = r.lock(c.read_json(r.lock_path(root, scope, home), 'lock'), declaration)
    wanted = getattr(args, 'id', None)
    selected = [binding for binding in declaration['skills'] if getattr(args, 'all', False) or
                wanted in (binding['id'], r.coordinate(binding))]
    if wanted and len(selected) != 1:
        c.fail('skill.ambiguous' if selected else 'skill.unknown', 'Choose one installed skill; qualify it as TAP/ID.', 4,
               choices=[r.coordinate(binding) for binding in selected])
    proposal = copy.deepcopy(declaration)
    keys = {r.coordinate(binding) for binding in selected}
    for binding in proposal['skills']:
        if r.coordinate(binding) in keys:
            if args.command == 'pin':
                binding['pinned'] = True
            else:
                binding.pop('pinned', None)
    lock = dict(lock, selection_digest=r.selection_digest(proposal))
    before = pinned.snapshot(home, [(root, scope)])
    def candidate():
        return fs.plan(config, state, [root], home=home, operation='install', proposals={key: proposal},
                       lock_proposals={key: lock}, repair_roles=True, retire_files=False)
    def prepare():
        import mask_store
        import mask_selection
        effects = output['data']['preparation'] = [dict(root=key, effects={})]
        mask_store.ensure(home, proposal, lock, config, offline=True,
                          coordinates=mask_selection.applicable_coordinates(proposal), effects=effects[0]['effects'])
    mask_lifecycle.execute(args, output, home, config, [root], before, candidate, prepare,
                           details=dict(root=key, scope=scope, skills=sorted(keys), pinned=args.command == 'pin'))
