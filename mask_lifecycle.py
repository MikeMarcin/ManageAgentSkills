"""Complete installation tasks: frozen plan, one review, prepare, publish, verify."""
from __future__ import annotations

from pathlib import Path

import mask_consent as consent
import mask_core as c
import mask_fs as fs
import mask_pinned as pinned
import mask_resolve as r
import mask_setup as setup
import mask_store as store
import mask_progress as progress


def review(args, output, planned, rows):
    """Consent covers the entire task before any consumer effect, including registration."""
    significant = [setup.disclosure(row) for row in rows if 'fingerprint' in row]
    replacements = {}
    for entry in planned.get('workflow_readiness', []):
        for skill in entry['skills']:
            for role in skill['roles']:
                if role.get('observed_sha256') and (role['state'] == 'modified' or
                        any(write['root'] == entry['root'] and write['relative'] == role['path'] and write.get('repair')
                            for write in planned['intent'].get('native_roles', []))):
                    path = str(Path(entry['root']) / role['path'])
                    replacements[path] = dict(kind='file.backup_replace', path=path, before_sha256=role['observed_sha256'], status='planned')
    significant.extend(replacements.values())
    planned['plan_hash'] = c.digest(dict(plan=planned['plan_hash'], command=getattr(args, 'public_command', args.command),
                                       setup=[row.get('fingerprint', row) for row in rows], review=significant))
    fs.public_plan(planned, output)
    output['would_change'] |= planned.get('commit_would_change', False)
    if rows:
        output['data']['setup'] = dict(actions=rows)
    expected = getattr(args, 'expect_plan_hash', None)
    fs.ensure_applicable(planned, expected)
    proposal = dict(kind='task', reason='task.review', scope=planned['intent']['selected'],
                    actions=list(planned['actions']) + significant, plan_hash=planned['plan_hash'],
                    question='Apply these changes?', granted_by=None)
    output['data']['review'] = proposal
    output['would_change'] |= bool(significant)
    if output['dry_run']:
        return
    blocked = [row for row in rows if row['state'] == 'blocked']
    missing_inputs = [item for entry in planned.get('workflow_readiness', []) for skill in entry['skills']
                      for item in skill['inputs'] if item['state'] in ('missing', 'invalid')]
    if blocked or missing_inputs:
        c.fail('workflow.incomplete', 'Required consumer inputs or setup are unavailable; no consumer changes were applied.', 4,
               setup=blocked, inputs=missing_inputs)
    how = 'approve-plan' if expected == planned['plan_hash'] else None
    if significant and how is None:
        if not consent.interactive(args):
            c.fail('confirmation.required', 'Review this task with --dry-run, then apply it with --approve-plan HASH.', 4)
        import mask_present as present
        if not consent.ask(proposal, present.render_confirmation(proposal, output),
                           details=present.task_review(proposal, output, details=True)):
            c.fail('confirmation.declined', 'Declined; no consumer changes were applied.', 4)
        how = 'prompt'
    proposal['granted_by'] = how or 'command'
    for row in rows:
        if 'fingerprint' in row:
            row.update(state='granted', granted_by=how or 'command')


def execute(args, output, home, config, roots, before, candidate, prepare, *, details=None):
    """The caller supplies frozen resolution; rechecks never resolve a newer candidate."""
    progress.phase('Checking selected installations')
    planned = candidate()
    rows = setup.proposals(planned, repair=True)
    preparation = dict(output['data'])
    try:
        review(args, output, planned, rows)
    finally:
        for key, value in preparation.items():
            output['data'].setdefault(key, value)
        output['data'].update(details or {})
    if output['dry_run']:
        return
    # The lifecycle lock excludes other tasks; consumer edits can still happen
    # during a terminal review. Recheck before preparing artifacts in that case.
    consumers = [(root, c.consumer_scope(planned['intent']['after_state'], root)) for root in roots]
    if pinned.snapshot(home, consumers) != before:
        c.fail('plan.stale', 'Consumer state changed during review; no consumer changes were applied.', 4)
    if output['data']['review']['granted_by'] == 'prompt':
        fresh = candidate()
        fresh_rows = setup.proposals(fresh, repair=True)
        preview = dict(output, dry_run=True, data={}, actions=[], warnings=[])
        review(args, preview, fresh, fresh_rows)
        if fresh['plan_hash'] != planned['plan_hash']:
            c.fail('plan.stale', 'The task changed during review; no consumer changes were applied.', 4)
    progress.phase('Preparing locked skill content')
    prepare()
    with c.writer_lock(home):
        if c.kind(home / 'pending.json') != 'missing':
            c.fail('recovery.required', 'Recover the pending operation first.', 8)
        if pinned.snapshot(home, consumers) != before:
            c.fail('plan.stale', 'Consumer state changed during preparation; no consumer changes were applied.', 4)
        fresh = candidate()
        fresh_rows = setup.proposals(fresh, repair=True)
        preview = dict(output, dry_run=True, data={}, actions=[], warnings=[])
        review(args, preview, fresh, fresh_rows)
        if fresh['plan_hash'] != planned['plan_hash']:
            c.fail('plan.stale', 'The task changed during preparation; no consumer changes were applied.', 4)
        progress.phase('Applying skill links and version locks')
        fs.execute(planned, home, output)
        operation = 'ensure'  # After activation, every task uses the pinned readiness service.
        def replan(staged=None):
            state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
            return fs.plan(config, state, roots, home=home, operation=operation,
                           staged_roles=staged, repair_roles=True, retire_files=False)
        if rows:
            try:
                setup.execute(output, home, replan, [row for row in rows if row['state'] == 'granted'])
            except (Exception, KeyboardInterrupt):
                # This is the pre-setup snapshot, not a diagnosis of already published roles.
                output['data']['workflow_readiness_observation'] = 'before_setup'
                raise
        progress.phase('Verifying final readiness')
        final = replan()
        output['data']['workflow_readiness'] = final.get('workflow_readiness', [])
    import mask_ensure
    mask_ensure.final_status(output, ran=any(row['state'] == 'published' for row in rows))


def restore(args, output, home, *, registering=False):
    """Register/repair keep existing locked versions and resolve only missing bindings."""
    import mask
    import mask_task
    import mask_selection
    config = c.config(c.read_json(home / 'config.json'))
    state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
    if c.kind(home / 'pending.json') != 'missing':
        c.fail('recovery.required', 'Recover the pending operation first.', 8)
    if registering:
        root, scope, _, _ = mask_task.consumer(args, state, home, creating=True)
        consumers = [(root, scope)]
    else:
        consumers = [(root, c.consumer_scope(state, root)) for root in mask.selected_roots(args, state)]
    roots = [root for root, _ in consumers]
    before = pinned.snapshot(home, consumers)
    declarations, locks, views = {}, {}, {}
    for root, scope in consumers:
        key = str(root)
        declaration = c.read_json(c.declaration_path(root, scope, home), 'manifest', default={})
        declaration = r.selection(declaration) if declaration else mask_task.fresh_declaration(config)
        declarations[key] = declaration
        previous = r.read_model(r.lock_path(root, scope, home), 'lock', missing=True)[0]
        # Acquiring exact objects is preparation only, never a version upgrade.
        if previous:
            old = r.lock(previous)
            for row in old['packages']:
                if c.kind(store.location(home, row['payload_digest'], row['id'])[0]) == 'directory':
                    continue
                entry = r.approved(declaration, config)[row['source']]
                if not store.exact_cached(home, row, entry):
                    if output['dry_run'] or getattr(args, 'offline', False) or getattr(args, 'expect_plan_hash', None):
                        c.fail('lock.resolution_required', 'The locked content is unavailable locally; run register or repair online before previewing.', 4)
                    import mask_sources
                    effects = {}
                    output['data'].setdefault('acquisitions', []).append(dict(root=key, effects=effects))
                    mask_sources.acquire_exact(home, row['source'], entry, row['commit'], config['git_timeout_seconds'], effects,
                                               root if scope == 'project' else None)
        # A complete valid lock can be used from verified store artifacts without a Git cache.
        try:
            locks[key] = r.lock(previous, declaration) if previous else None
        except c.MaskError as error:
            if error.code != 'lock.stale':
                raise
            locks[key] = None
        if locks[key] is None:
            old_rows = {r.coordinate(row): row for row in r.lock(previous)['packages']} if previous else {}
            rows = []
            for binding in declaration['skills']:
                prior = old_rows.get(r.coordinate(binding))
                if prior:
                    rows.append(prior)
                else:
                    entry = r.approved(declaration, config)[binding['source']]
                    rows.append(mask_task.resolve_row(home, declaration, binding, entry, config, args, output, views,
                                                      root if scope == 'project' else None))
            locks[key] = r.lock(dict(schema_version=1, resolver='mask-lock-v1', selection_digest=r.selection_digest(declaration), packages=rows), declaration)
    register = [str(root) for root in roots if str(root) not in c.consumer_records(state)] if registering else []
    user_root = next((root for root, scope in consumers if scope == 'user'), None)
    def candidate():
        return fs.plan(config, state, roots, home=home, operation='ensure', proposals=declarations,
                       lock_proposals=locks, register=register, user_root=user_root, payload_views=views,
                       repair_roles=True, retire_files=False)
    acquisitions = output['data'].get('acquisitions', [])
    def prepare():
        effects = output['data']['preparation'] = []
        for root, _ in consumers:
            observation = dict(root=str(root), effects={})
            effects.append(observation)
            store.ensure(home, declarations[str(root)], locks[str(root)], config, offline=True,
                         coordinates=mask_selection.applicable_coordinates(declarations[str(root)]), effects=observation['effects'])
    execute(args, output, home, config, roots, before, candidate, prepare,
            details=dict(acquisitions=acquisitions, registered=bool(register), host_load='not_verified'))
