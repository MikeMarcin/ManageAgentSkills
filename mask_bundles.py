"""Explicit flat bundle contributions over the shared selection and task lifecycle."""
from __future__ import annotations

import copy

import mask_core as c
import mask_fs as fs
import mask_lifecycle as lifecycle
import mask_pinned as pinned
import mask_resolve as r
import mask_selection as selection
import mask_sources as sources
import mask_store as store
import mask_task as task


def catalog(home, config, name, args, output, consumer=None):
    entry = sources.selected(config, name)
    root = sources.cached(home, name, entry)
    if root is None:
        if args.command in ('bundle.list', 'bundle.show') or output['dry_run'] or getattr(args, 'offline', False) or getattr(args, 'expect_plan_hash', None):
            c.fail('bundle.catalog_required', 'Fetch the approved bundle source before browsing or previewing.', 4, source=name)
        scratch = dict(data={})
        sources.fetch(home, name, entry, config['git_timeout_seconds'], scratch, consumer=consumer)
        output['data'].setdefault('acquisitions', []).append(dict(source=name, **scratch['data']))
        root = r.cached(home, name, entry)
    chosen = r.machine_selector(root, entry)
    commit = chosen.get('commit') or (sources.cached_refs(root, entry) or {}).get(chosen['ref'])
    if commit is None or c.peeled_commit(root, commit) != commit:
        c.fail('bundle.catalog_required', 'Bundle source revision is unavailable; explicitly fetch it.', 4, source=name)
    record = sources.exact_entry(root, commit, 'mask-source.json')
    index = sources.source_index(root, {'mask-source.json': record} if record else {})
    return entry, commit, (index or {}).get('bundles', {})


def definition(home, config, key, args, output, consumer=None):
    name, bundle = r.qualified(key).split('/')
    entry, commit, available = catalog(home, config, name, args, output, consumer)
    if bundle not in available:
        c.fail('bundle.unknown', 'The approved source has no bundle with this name.', 4, bundle=key)
    value = available[bundle]
    return dict(coordinate=key, repository=sources.repository(entry['repository']), commit=commit,
                definition_digest=c.digest(r.canonical(value, 'bundle')),
                description=value.get('description', ''), bindings=r.bundle_bindings(value['skills']))


def browse(args, output, home):
    _, config = task.machine(home)
    if args.command == 'bundle.show':
        output['data'] = dict(bundle=definition(home, config, args.bundle, args, output), network='none')
        return
    rows, unavailable = [], []
    names = [args.source] if getattr(args, 'source', None) else sorted(config['sources'])
    for name in names:
        try:
            _, _, bundles = catalog(home, config, name, args, output)
            for bundle in bundles:
                rows.append(definition(home, config, name + '/' + bundle, args, output))
        except c.MaskError as error:
            if error.code != 'bundle.catalog_required' or getattr(args, 'source', None):
                raise
            unavailable.append(dict(source=name, error=error.as_dict()))
    output['data'] = dict(bundles=sorted(rows, key=lambda row: row['coordinate']), unavailable=unavailable, network='none')


def semantics(binding):
    return {field: value for field, value in binding.items() if field != 'introduced_by'}


def origins(ledger, coordinate):
    return (['manual'] if coordinate in ledger['manual'] else []) + [key for key, receipt in ledger['bundles'].items()
            if any(r.coordinate(row) == coordinate for row in receipt['bindings'])]


def conflict(coordinate, dimension, before, after, competing):
    c.fail('bundle.conflict', 'Bundle binding conflicts with an existing local contribution.', 4,
           skill=coordinate, dimension=dimension, before=before, after=after, origins=competing)


def retire_members(current, ledger, key, old, incoming):
    """Release only exclusive unchanged/unheld members; retain other local intent."""
    preserved, removed = [], []
    for coordinate, binding in old.items():
        if coordinate in incoming or coordinate not in current:
            continue
        competing = origins(ledger, coordinate)
        existing = current[coordinate]
        if coordinate not in ledger['manual'] and competing == [key] and semantics(existing) == semantics(binding) and not existing.get('pinned'):
            del current[coordinate]
            removed.append(coordinate)
        else:
            reason = 'manual_or_overlap' if coordinate in ledger['manual'] or competing != [key] else 'held_or_modified'
            preserved.append(dict(skill=coordinate, reason=reason, origins=competing))
            if competing == [key] and coordinate not in ledger['manual']:
                ledger['manual'].append(coordinate)
    return preserved, sorted(removed)


def withdraw(declaration, key):
    """Remove the frozen local receipt, without reading a current source definition."""
    proposal = copy.deepcopy(declaration)
    ledger = proposal['bundle_state']
    old = {r.coordinate(row): row for row in ledger['bundles'][key]['bindings']}
    current = {r.coordinate(row): row for row in proposal['skills']}
    preserved, removed = retire_members(current, ledger, key, old, {})
    del ledger['bundles'][key]
    for binding in current.values():
        if 'introduced_by' in binding:
            binding['introduced_by'] = [origin for origin in binding['introduced_by'] if origin != 'bundle:' + key]
            if not binding['introduced_by']:
                del binding['introduced_by']
    proposal['skills'] = list(current.values())
    return r.selection(proposal), set(), preserved, removed


def expand(declaration, previous, descriptor, config, *, replacing):
    """Merge only the selected local contribution; preserve manual intent and exact rows."""
    proposal = copy.deepcopy(declaration)
    ledger = proposal.setdefault('bundle_state', dict(manual=[r.coordinate(row) for row in declaration['skills']], bundles={}))
    key = descriptor['coordinate']
    prior = ledger['bundles'].get(key)
    if prior and not sources.same(prior['repository'], descriptor['repository']):
        conflict(key, 'repository', prior['repository'], descriptor['repository'], [key])
    if prior and not replacing:
        if prior['definition_digest'] != descriptor['definition_digest']:
            c.fail('bundle.upgrade_required', 'The bundle definition changed; preview bundle upgrade explicitly.', 4, bundle=key,
                   before=prior['definition_digest'], after=descriptor['definition_digest'])
        return proposal, set(), [], []
    old = {r.coordinate(row): row for row in prior['bindings']} if prior else {}
    current = {r.coordinate(row): row for row in proposal['skills']}
    incoming = {r.coordinate(row): row for row in descriptor['bindings']}
    rows = {r.coordinate(row): row for row in previous['packages']} if previous else {}
    refresh, preserved = set(), []
    for coordinate, binding in incoming.items():
        sources.selected(config, binding['source'])  # Report every trust prerequisite before consumer changes.
        existing = current.get(coordinate)
        if existing is None:
            current[coordinate] = copy.deepcopy(binding)
            continue
        competing = origins(ledger, coordinate)
        exclusively_owned = coordinate not in ledger['manual'] and competing == [key] and coordinate in old and semantics(existing) == semantics(old[coordinate]) and not existing.get('pinned')
        if exclusively_owned:
            current[coordinate] = copy.deepcopy(binding)
            if r.declared_selector(declaration, existing) != r.declared_selector(declaration, binding):
                refresh.add(coordinate)
            continue
        desired_version = binding.get('version')
        locked_version = rows.get(coordinate, {}).get('selector')
        if desired_version is not None and desired_version != (r.declared_selector(declaration, existing) or locked_version):
            conflict(coordinate, 'version', locked_version, desired_version, competing + [key])
        if binding.get('when') != existing.get('when'):
            conflict(coordinate, 'when', existing.get('when'), binding.get('when'), competing + [key])
        manual_target = coordinate in ledger['manual'] or coordinate in old and semantics(existing) != semantics(old[coordinate])
        if 'agents' in binding and not manual_target and binding['agents'] != existing.get('agents', declaration['default_agents']):
            conflict(coordinate, 'agents', existing.get('agents', declaration['default_agents']), binding['agents'], competing + [key])
        if manual_target and 'agents' in binding and binding['agents'] != existing.get('agents', declaration['default_agents']):
            preserved.append(dict(skill=coordinate, reason='manual_targets', agents=existing.get('agents', declaration['default_agents']), suggestion=binding['agents']))
    retained, removed = retire_members(current, ledger, key, old, incoming)
    preserved.extend(retained)
    ledger['bundles'][key] = {field: copy.deepcopy(descriptor[field]) for field in ('repository', 'commit', 'definition_digest', 'bindings')}
    needed_sources = {row['source'] for row in current.values()} | {bundle.split('/')[0] for bundle in ledger['bundles']}
    for name in needed_sources:
        entry = sources.selected(config, name)
        proposal['sources'].setdefault(name, dict(repository=sources.repository(entry['repository']), packages=entry['packages']))
    for coordinate, binding in current.items():
        attributed = origins(ledger, coordinate)
        annotations = set(binding.get('introduced_by', []))
        annotations.update('bundle:' + origin for origin in attributed if origin != 'manual')
        if annotations:
            binding['introduced_by'] = sorted(annotations)
    proposal['skills'] = list(current.values())
    return r.selection(proposal), refresh, preserved, sorted(removed)


def mutate(args, output, home):
    if c.kind(home / 'pending.json') != 'missing':
        c.fail('recovery.required', 'Inspect and recover the pending operation first.', 8)
    state, config = task.machine(home)
    r.qualified(args.bundle)
    uninstalling = args.command == 'bundle.uninstall'
    root, scope, key, record = task.consumer(args, state, home, creating=True)
    if record and record.get('mode') == 'dev-link':
        c.fail('dev_link.active', 'Return to pins before changing a bundle contribution.', 4)
    declaration_path = c.declaration_path(root, scope, home)
    raw = c.read_text(declaration_path, 'manifest', missing=True)
    declaration = r.selection(c.parse_json(raw, 'manifest') if raw is not None else task.fresh_declaration(config))
    receipt = declaration.get('bundle_state', {}).get('bundles', {}).get(args.bundle)
    if uninstalling and receipt is None:
        # No registration, source approval/fetch, lock rewrite or setup for an absent contribution.
        plan_hash = c.digest(dict(command=args.command, root=key, scope=scope, declaration=declaration, record=record))
        if getattr(args, 'expect_plan_hash', None) not in (None, plan_hash):
            c.fail('plan.stale', 'The bundle contribution changed since the preview.', 4, bundle=args.bundle)
        output['data'].update(root=key, scope=scope, bundle=dict(coordinate=args.bundle),
                              before=declaration, after=declaration, added=[], removed=[], preserved=[],
                              already=True, plan_hash=plan_hash, network='none')
        return
    lock_value = r.read_model(r.lock_path(root, scope, home), 'lock', missing=True)[0]
    previous = r.lock(lock_value, declaration) if lock_value is not None else None
    if uninstalling and previous is None:
        c.fail('lock.resolution_required', 'Restore the missing exact lock with repair before uninstalling this contribution.', 4, bundle=args.bundle)
    descriptor = dict(coordinate=args.bundle, **copy.deepcopy(receipt)) if uninstalling else definition(home, config, args.bundle, args, output, root if scope == 'project' else None)
    replacing = args.command == 'bundle.upgrade' or getattr(args, 'replace', False)
    if args.command == 'bundle.upgrade' and receipt is None:
        c.fail('bundle.not_installed', 'Install this bundle before upgrading its local contribution.', 4, bundle=args.bundle)
    proposal, refresh, preserved, removed = withdraw(declaration, args.bundle) if uninstalling else expand(declaration, previous, descriptor, config, replacing=replacing)
    entries = r.approved(proposal, config)
    prior_rows = {r.coordinate(row): row for row in previous['packages']} if previous else {}
    views, rows = {}, []
    for binding in proposal['skills']:
        coordinate = r.coordinate(binding)
        if coordinate in prior_rows and coordinate not in refresh:
            rows.append(prior_rows[coordinate])
        else:
            rows.append(task.resolve_row(home, proposal, binding, entries[binding['source']], config, args, output, views, root if scope == 'project' else None))
    locked = r.lock(dict(schema_version=1, resolver='mask-lock-v1', selection_digest=r.selection_digest(proposal), packages=rows), proposal)
    before = pinned.snapshot(home, [(root, scope)])
    selected_before = {r.coordinate(row): row for row in declaration['skills']}
    selected_after = {r.coordinate(row): row for row in proposal['skills']}
    changes = dict(coordinate=args.bundle, commit=descriptor['commit'], definition_digest=descriptor['definition_digest'],
                   added=sorted(selected_after.keys() - selected_before.keys()), removed=removed, preserved=preserved,
                   changed=[dict(skill=coordinate, before=semantics(selected_before[coordinate]), after=semantics(selected_after[coordinate]))
                            for coordinate in sorted(selected_before.keys() & selected_after.keys())
                            if semantics(selected_before[coordinate]) != semantics(selected_after[coordinate])])
    def candidate():
        if not uninstalling:
            observed = definition(home, config, args.bundle, args, output, root if scope == 'project' else None)
            if observed != descriptor:
                c.fail('plan.stale', 'The bundle source revision or definition changed during this task.', 4, bundle=args.bundle)
        plan = fs.plan(config, state, [root], proposals={key: proposal}, lock_proposals={key: locked},
                       register=[key] if record is None else (), operation='remove' if uninstalling else 'install', home=home,
                       user_root=root if scope == 'user' else None, payload_views=views, repair_roles=True, retire_files=False)
        plan['plan_hash'] = c.digest(dict(plan=plan['plan_hash'], bundle=descriptor, replacing=replacing, uninstalling=uninstalling))
        plan['bundle_changes'] = changes
        for blocker in plan['blockers']:
            if blocker['code'] in ('target.collision', 'selection.conflict'):
                blocker.setdefault('details', {})['contribution_origins'] = {
                    r.coordinate(binding): origins(proposal['bundle_state'], r.coordinate(binding))
                    for binding in proposal['skills']}
        return plan
    def prepare():
        effects = output['data']['preparation'] = []
        for selection_value, lock, coordinates in [(proposal, locked, selection.applicable_coordinates(proposal)),
                (declaration, previous, sorted(set(removed) & set(selection.applicable_coordinates(declaration))))]:
            if not coordinates or lock is None:
                continue
            row = dict(root=key, effects={})
            effects.append(row)
            store.ensure(home, selection_value, lock, config, offline=True, coordinates=coordinates, effects=row['effects'])
    lifecycle.execute(args, output, home, config, [root], before, candidate, prepare,
            details=dict(root=key, scope=scope, bundle=descriptor, replacing=replacing,
                         expansion=proposal['bundle_state']['bundles'].get(args.bundle),
                         added=changes['added'],
                         removed=removed, preserved=preserved, before=declaration, after=proposal,
                         locked=locked, network='fetch' if output['data'].get('acquisitions') else 'none'))


def dispatch(args, output, home):
    if args.command in ('bundle.list', 'bundle.show'):
        browse(args, output, home)
    else:
        mutate(args, output, home)
