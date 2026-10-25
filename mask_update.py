"""``update`` and ``upgrade``, named as brew and apt name them (RFC-MASK-0021 AC03; contracts/CLI.md, Update semantics).

``refresh`` owns ``update``: advance this program, then fetch every approved tap. It touches no consumer.
``dispatch`` owns ``upgrade``: select consumers, fetch each referenced tap once, resolve every remaining
consumer from the cache, disclose per-consumer lock changes and activate one ordinary journaled plan.
``fetch_all`` is ``source fetch`` without a name. Only Git and source family errors are captured per tap;
every other error propagates.
"""
from __future__ import annotations

import mask_core as c
import mask_fs as fs
import mask_pinned as pinned
import mask_resolve as r
import mask_sources as sources
import mask_progress as progress

NOT_ATTEMPTED = dict(attempted=False, ok=None, before=None, after=None, remote_refs_changed=None, error=None)


def fetch_tap(home, name, entry, timeout, selectors=(), consumer=None):
    """One git fetch: the tap's configured ref plus the objects its selected bindings name.

    Returns the disclosure row and the captured error, if any.
    """
    progress.phase(f'Fetching tap {name}')
    scratch = dict(data={})
    row, captured = dict(NOT_ATTEMPTED, attempted=True, ok=False), None
    try:
        existing = sources.cached(home, name, entry)
        chosen, refs, options = sources.negotiate(home, name, entry, timeout, scratch, consumer)
        extra = set()
        for selector in selectors:
            if 'ref' in selector:
                if selector['ref'] in refs:
                    extra.add(refs[selector['ref']])
            elif existing is None or c.git(existing, 'rev-parse', '--verify', selector['commit'] + '^{commit}', optional=True) != selector['commit']:
                extra.add(selector['commit'])
        sources.fetch(home, name, entry, timeout, scratch, advertised=(chosen, refs, options), extra=sorted(extra))
        row['ok'] = True
    except c.MaskError as error:
        if not error.code.startswith(('git.', 'source.')):
            raise
        captured = error
        row['error'] = error.as_dict()
    effects = scratch['data'].get('fetch_effects', {})
    row.update(scratch['data'].get('transports', {}).get(name) or {})  # transport, transport_policy, chosen_by, tried (RFC-MASK-0022)
    row.update(before=effects.get('before'), after=effects.get('after'), remote_refs_changed=effects.get('remote_refs_changed', False))
    return row, captured


def fetch_all(args, output, home):
    """Fetch every approved tap once; no declaration, lock, link or state is written."""
    config = c.config(c.read_json(home / 'config.json'))
    fetches, failed = {}, {}
    output['data'] = dict(fetches=fetches, network='none' if output['dry_run'] or not config['sources'] else 'fetch')
    for name in sorted(config['sources']):
        if output['dry_run']:
            fetches[name] = dict(NOT_ATTEMPTED)
            continue
        fetches[name], error = fetch_tap(home, name, config['sources'][name], config['git_timeout_seconds'])
        if error is not None:
            failed[name] = error
    if failed:
        first = next(iter(failed.values()))
        raise c.MaskError(first.code, str(first), first.exit_code, details=dict(first.details, failed=sorted(failed)))


# A program checkout in one of these states is somebody's deliberate work, not a failed refresh: say so and still fetch the taps.
PROGRAM_HELD = {'source.ahead': 'this checkout is ahead of its remote', 'source.diverged': 'this checkout has diverged from its remote',
                'source.dirty': 'your uncommitted changes touch files this update changes', 'source.detached': 'this checkout is detached',
                'source.identity_mismatch': 'this checkout is not on main from the ManageAgentSkills remote'}


def refresh(args, output, home, root):
    """``update``: fast-forward the MASK program, then fetch every approved tap; no declaration, lock, link or consumer changes.

    A program whose contracts change needs consent (``program.migration``). The taps are fetched before the
    question is asked or refused, and an approved retry in the same invocation reuses that fetch.
    """
    import mask_consent as consent
    import mask_install
    progress.phase('Checking for MASK updates')
    failure, review = None, None
    try:
        mask_install.dispatch(args, output, home, root)
        program = dict(output['data'], status='updated' if output['changed'] else 'behind' if output['would_change'] else 'current')
    except consent.ConsentRequired as error:
        review = error
    except c.MaskError as error:
        if error.code == 'confirmation.required' and (output['data'].get('confirmation') or {}).get('kind') == 'program.migration':
            review = error
        elif error.code not in PROGRAM_HELD and not error.code.startswith('git.'):
            raise
        else:
            program = dict(status='held' if error.code in PROGRAM_HELD else 'failed', reason=PROGRAM_HELD.get(error.code, str(error)), code=error.code)
            if error.code == 'source.dirty' and not error.details.get('blocking_paths'):
                program['reason'] = 'a Git merge, rebase, cherry-pick or revert is in progress in this checkout'
            for key in ('blocking_paths', 'preserved'):  # Which paths are in the way, and which would simply stay.
                if key in error.details:
                    program[key] = error.details[key]
            failure = None if error.code in PROGRAM_HELD else error
    confirmation = output['data'].pop('confirmation', None)
    if review is not None:
        program = dict(output['data'], status='review')
    program_changed, program_would_change = output['changed'], output['would_change']
    raw = c.read_json(home / 'config.json', default={})
    output['data'] = dict(fetches={}, network='none')  # Stays so with no configuration yet, or on a machine that predates taps.
    try:
        if raw and getattr(args, 'tap_fetches', None) is not None:
            output['data']['fetches'] = args.tap_fetches
        elif raw:
            fetch_all(args, output, home)
    finally:  # A tap that fails to fetch still discloses what happened to the program.
        output['data']['program'] = program
        if confirmation is not None:
            output['data']['confirmation'] = confirmation
        if not output['dry_run']:
            output['data']['network'] = 'fetch'
        output.update(changed=program_changed, would_change=program_would_change)
    if review is not None:
        args.tap_fetches = output['data']['fetches']
        raise review
    if failure is not None:
        raise failure


def changes(previous, proposal):
    """Per-coordinate lock differences for the disclosure."""
    before = {r.coordinate(row): row for row in previous['packages']}
    after = {r.coordinate(row): row for row in proposal['packages']}
    result = []
    for key in sorted(before.keys() | after.keys()):
        old, new = before.get(key, {}), after.get(key, {})
        if old != new:
            result.append(dict(coordinate=key, before_commit=old.get('commit'), after_commit=new.get('commit'),
                               before_digest=old.get('payload_digest'), after_digest=new.get('payload_digest'),
                               selector=(new or old)['selector']))
    return result


def missing_selectors(home, name, entry, selectors):
    cache = sources.cached(home, name, entry)
    if cache is None:
        return True
    refs = sources.cached_refs(cache, entry) or {}
    return any('commit' in value and c.peeled_commit(cache, value['commit']) != value['commit'] or
               'ref' in value and value['ref'] not in refs for value in selectors if value)


def invoking(state):
    """The registered project containing the working directory, if any; it is the preferred canonical checkout."""
    import os
    try:
        root = c.project_root(None)
    except c.MaskError:
        return None
    for known in c.consumer_records(state):
        try:
            if os.path.samefile(root, known):
                return known
        except OSError:
            continue
    return None


def dispatch(args, output, home):
    import mask
    import mask_selection as selection
    import mask_store as store
    import mask_upgrade_commit as commits
    commit_requested = getattr(args, 'commit', False)
    if c.kind(home / 'pending.json') != 'missing':
        c.fail('recovery.required', 'Recover the pending operation before updating.', 8)
    config = c.config(c.read_json(home / 'config.json'))
    state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
    records = c.consumer_records(state)
    scoped = not getattr(args, 'all', False)
    roots = mask.selected_roots(args, state)
    requested = getattr(args, 'skill', None) or []
    consumers, declared = [], set()
    for root in roots:
        scope = c.consumer_scope(state, root)
        c.registered_root(root, records[str(root)], scope)
        unsafe = commit_requested and scope == 'project' and any(c.kind(root / path) != 'file' for path in commits.PATHS)
        error = c.MaskError('upgrade.commit_ineligible', 'Both project controls must be regular files.', 4,
                            details=dict(root=str(root))).as_dict() if unsafe else None
        # An unsafe control is never followed, read or rewritten. Its last declared
        # selection identifies a blocked consumer for aggregate/skill disclosure.
        declaration = r.selection(records[str(root)]['last_manifest'] if unsafe else
                                  c.read_json(c.declaration_path(root, scope, home), 'manifest'))
        bindings = {r.coordinate(binding) for binding in declaration['skills']}
        declared |= bindings
        named = sorted(set(requested) & bindings)
        if not requested or named:
            consumers.append(dict(root=root, scope=scope, declaration=declaration, skills=named,
                                  row=dict(root=str(root), scope=scope, status='blocked' if unsafe else 'unchanged', changes=[], error=error)))
    if len(set(requested)) != len(requested) or set(requested) - declared:
        c.fail('invocation.invalid', '--skill requires unique SOURCE/ID coordinates declared by the selected consumers.', 2)
    groups = None
    if not scoped and not getattr(args, 'independent', False):
        # One canonical checkout per repository resolves; its other checkouts adopt that result (MASK-0146).
        import mask_upgrade_groups as grouping
        groups = grouping.plan(consumers, records, invoking(state), commit_requested, config['git_timeout_seconds'])
    if not consumers:
        output['data'] = dict(consumers=[], fetches={}, network='none')
        if commit_requested:
            output['data']['commits'] = []
        output['warnings'].append(dict(code='project.empty_registry', message='No registered consumers selected.'))
        return
    observed = [(item['root'], item['scope']) for item in consumers if item['row']['status'] != 'blocked']
    before = pinned.snapshot(home, observed)
    active, taps, selectors = [], set(), {}
    for item in consumers:
        if item['row']['status'] == 'blocked':
            continue
        if records[str(item['root'])].get('mode') == 'dev-link':
            if scoped:
                c.fail('dev_link.active', 'Return the development link to pins before updating this consumer.', 4, root=str(item['root']))
            item['row']['status'] = 'skipped'
            output['warnings'].append(dict(code='dev_link.active', message='A dev-link consumer was skipped; return it to pins to upgrade it.', root=str(item['root'])))
            continue
        declaration = item['declaration']
        r.approved(declaration, config)
        item['taps'] = sorted({key.split('/', 1)[0] for key in item['skills']} if requested else declaration['sources'])
        taps.update(item['taps'])
        for binding in declaration['skills']:
            chosen = r.declared_selector(declaration, binding)
            if chosen and (not requested or r.coordinate(binding) in item['skills']):
                selectors.setdefault(binding['source'], []).append(chosen)
        active.append(item)
    rows = [item['row'] for item in consumers]
    fetching = not (output['dry_run'] or getattr(args, 'catalog_refreshed', False) or getattr(args, 'offline', False) or getattr(args, 'expect_plan_hash', None) is not None)
    fetches = {name: dict(NOT_ATTEMPTED) for name in sorted(taps)}
    disclosure = dict(consumers=rows, fetches=fetches, network='fetch' if fetching and taps else 'none')
    if groups is not None:
        disclosure['groups'] = groups
    if commit_requested:
        disclosure['commits'] = [commits.result_row(item['root'], item['scope']) for item in consumers]
    output['data'] = dict(disclosure)  # A refusal after the fetch phase still discloses its effects.
    failures = {}
    if fetching and taps:
        # Cache writes are MASK-owned effects, serialized with other writers like source fetch NAME.
        with c.writer_lock(home):
            if c.kind(home / 'pending.json') != 'missing':
                c.fail('recovery.required', 'Recover the pending operation before updating.', 8)
            for name in sorted(taps):
                # One selected project lends its origin's scheme; a bare upgrade over many consumers fetches each tap once without it.
                lender = consumers[0]['root'] if len(consumers) == 1 and consumers[0]['scope'] == 'project' else None
                fetches[name], error = fetch_tap(home, name, config['sources'][name], config['git_timeout_seconds'], selectors.get(name, ()), lender)
                if error is not None:
                    failures[name] = error
    progress.phase('Resolving selected skills')  # The fetch is over; this work must not run under its label.
    import mask_bundles as bundles
    locks, proposals, descriptors, bundle_updates, payload_views, planned_consumers = {}, {}, {}, [], {}, []
    blocked = [item['row']['root'] for item in consumers if item['row']['status'] == 'blocked']
    def resolve(item):
        row = item['row']
        failed = [name for name in item['taps'] if name in failures]
        if failed:
            if scoped:
                raise failures[failed[0]]
            row.update(status='blocked', error=failures[failed[0]].as_dict())
            blocked.append(row['root'])
            return
        previous = r.lock(r.read_model(r.lock_path(item['root'], item['scope'], home), 'lock')[0])
        try:
            declaration = item['declaration']
            definitions = bundles.definitions(home, config, declaration, args, output, item['root'] if item['scope'] == 'project' else None) if not requested else {}
            descriptors[row['root']] = definitions
            preserved, removed = [], []
            if definitions:
                declaration, _, preserved, removed = bundles.upgrade_proposal(declaration, previous, definitions, config)
            chosen = item['skills'] if requested else [r.coordinate(binding) for binding in declaration['skills']]
            protected = {entry['skill'] for entry in preserved if entry['reason'] == 'locally_modified_version'}
            chosen = [coordinate for coordinate in chosen if coordinate not in protected]
            if fetching:
                # New definitions can introduce an approved tap/selector absent from the old declaration.
                for name in sorted({binding['source'] for binding in declaration['skills'] if r.coordinate(binding) in chosen}):
                    selected = [r.declared_selector(declaration, binding) for binding in declaration['skills'] if binding['source'] == name and r.coordinate(binding) in chosen]
                    missing = name not in fetches or missing_selectors(home, name, config['sources'][name], selected)
                    if missing:
                        with c.writer_lock(home):
                            fetches[name], error = fetch_tap(home, name, config['sources'][name], config['git_timeout_seconds'], [value for value in selected if value], item['root'] if item['scope'] == 'project' else None)
                        if error:
                            raise error
            proposal = r.resolve_candidate(declaration, config, home, previous, refresh=bool(chosen), skills=chosen,
                                           allow_ref_rebind=getattr(args, 'allow_ref_rebind', False), payload_views=payload_views)
        except c.MaskError as error:
            bundle_failure = bool(item['declaration'].get('bundle_state', {}).get('bundles')) and error.code.startswith(('bundle.', 'source.', 'skill.', 'lock.resolution_required'))
            if (bundle_failure and scoped) or (not bundle_failure and (error.code != 'lock.resolution_required' or fetching)):
                raise
            row.update(status='blocked', error=error.as_dict(), requires_fetch=error.code in ('lock.resolution_required', 'bundle.catalog_required'))
            blocked.append(row['root'])
            return
        locks[row['root']] = proposal
        item['previous_lock'] = previous
        proposals[row['root']] = declaration
        descriptors[row['root']] = definitions
        row.update(status='unchanged' if proposal == previous and declaration == item['declaration'] else 'updated', changes=changes(previous, proposal))
        if definitions:
            old_keys = {r.coordinate(binding) for binding in item['declaration']['skills']}
            new_keys = {r.coordinate(binding) for binding in declaration['skills']}
            update = dict(root=row['root'], definitions=list(definitions.values()), added=sorted(new_keys - old_keys), removed=removed, preserved=preserved, versions=row['changes'])
            row['bundle_changes'] = update
            bundle_updates.append(update)
        planned_consumers.append(item)

    def final_of(item):
        """The control bytes the activation leaves in a planned project consumer."""
        key = item['row']['root']
        final = commits.controls(item['root'])
        if proposals[key] != item['declaration']:
            final['.mask.json'] = c.text_json(proposals[key]).encode('utf-8')
        if locks[key] != item['previous_lock']:
            final['.mask.lock.json'] = c.text_json(locks[key]).encode('utf-8')
        return final

    def member(item):
        group, key = item['group'], item['row']['root']
        canonical = group['canonical']
        if canonical not in planned_consumers:
            group['disclosure'].update(action='blocked', reason='canonical_blocked')
            item['row'].update(status='blocked', error=c.MaskError(
                'upgrade.canonical_blocked', 'The canonical checkout of this repository was not upgraded; this checkout was left unchanged.', 4,
                details=dict(root=key, canonical=canonical['row']['root'])).as_dict())
            blocked.append(key)
            return
        final = {path: c.digest(value) if value is not None else None for path, value in final_of(canonical).items()}
        action, reason = grouping.adoption(item, group['canonical_git']['controls'], final, commit_requested)
        group['disclosure'].update(action=action, reason=reason)
        if action == 'independent':
            item['fallback'] = reason
            resolve(item)
            return
        previous = r.lock(r.read_model(r.lock_path(item['root'], item['scope'], home), 'lock')[0])
        declaration, proposal = (proposals[canonical['row']['root']], locks[canonical['row']['root']]) if action == 'adopt' else (item['declaration'], previous)
        locks[key], proposals[key], descriptors[key], item['previous_lock'] = proposal, declaration, {}, previous
        item['row'].update(status='unchanged' if proposal == previous and declaration == item['declaration'] else 'updated',
                           changes=changes(previous, proposal), adopted_from=canonical['row']['root'])
        planned_consumers.append(item)

    for item in active:
        if item.get('group', {}).get('role') != 'member':
            resolve(item)
    for item in active:
        if item.get('group', {}).get('role') == 'member':
            member(item)
    commit_rows, commit_observations, final_controls = [], {}, {}
    if commit_requested:
        for item in consumers:
            key, scope = item['row']['root'], item['scope']
            final = commits.controls(item['root']) if scope == 'project' else {}
            if item in planned_consumers and scope == 'project':
                final = final_of(item)
            grouped = item.get('group', {}).get('role') == 'member' and item in planned_consumers
            if grouped and item.get('fallback'):
                row, observed_git = commits.uncommitted(item['root'], scope, item['fallback']), None
            elif grouped:
                row, observed_git = commits.plan_member(item['root'], scope, final, item['group']['canonical']['row']['root'], config['git_timeout_seconds'])
            else:
                row, observed_git = commits.plan(item['root'], scope, final, config['git_timeout_seconds'],
                                                 skipped=item not in planned_consumers)
            if item['row']['status'] == 'blocked' and scope == 'project':
                row.update(status='blocked', error=item['row']['error'])
            commit_rows.append(row)
            if observed_git is not None:
                commit_observations[key] = observed_git
                final_controls[key] = final
            if row['status'] == 'blocked' and item in planned_consumers:
                item['row'].update(status='blocked', error=row['error'])
                blocked.append(key)
        by_root = {row['root']: row for row in commit_rows}
        for item in planned_consumers:
            group = item.get('group', {})
            row = by_root[item['row']['root']]
            if group.get('role') == 'member' and row['status'] == 'planned':
                # A member at the canonical HEAD is fast-forwarded to the canonical commit; any other is cherry-picked.
                canonical_head = by_root[group['canonical']['row']['root']]['before_head']
                row['propagation'] = 'fast_forward' if row['before_head'] == canonical_head else 'cherry_pick'
            if group.get('role') == 'member' and row['status'] == 'planned' and \
                    by_root[group['canonical']['row']['root']]['status'] == 'blocked':
                # Adopting the controls of a canonical checkout that cannot commit would leave an unrecorded copy.
                error = c.MaskError('upgrade.canonical_blocked', 'The canonical checkout of this repository cannot commit; this checkout was left unchanged.', 4,
                                    details=dict(root=row['root'], canonical=group['canonical']['row']['root'])).as_dict()
                row.update(status='blocked', error=error)
                item['row'].update(status='blocked', error=error)
                group['disclosure'].update(action='blocked', reason='canonical_blocked')
                blocked.append(row['root'])
        disclosure['commits'] = commit_rows
        output['data'].update(disclosure)
        planned_consumers = [item for item in planned_consumers if item['row']['status'] != 'blocked']
    selected = [item['root'] for item in planned_consumers]

    def candidate_plan():
        for item in consumers:
            bundles.guard_definitions(home, config, descriptors.get(str(item['root']), {}), args, output, item['root'] if item['scope'] == 'project' else None)
        planned = fs.plan(config, state, selected, home=home, proposals=proposals, lock_proposals=locks,
                          operation='upgrade', payload_views=payload_views, repair_roles=True, retire_files=False)
        planned['plan_hash'] = c.digest(dict(plan=planned['plan_hash'], blocked=[row for row in rows if row['status'] == 'blocked'],
                                             bundles=descriptors, groups=groups,
                                             skipped=[row['root'] for row in rows if row['status'] == 'skipped'],
                                             commit=dict(enabled=commit_requested, rows=commit_rows,
                                                         observations={key: commits.fresh_observation(item['root'], commit_observations[key], config['git_timeout_seconds'])
                                                                       for item in consumers if (key := item['row']['root']) in commit_observations})))
        if commit_requested:
            planned['commit_would_change'] = any(row['status'] == 'planned' for row in commit_rows)
            planned['commits'] = commit_rows
            if scoped:
                planned['blockers'].extend(row['error'] for row in commit_rows if row['status'] == 'blocked')
        planned['bundle_updates'] = bundle_updates
        return planned

    # Only selected consumers participate in the activation; the snapshot still
    # binds all originally observed roots, including a failed tap's consumers.
    before_selected = pinned.snapshot(home, [(item['root'], item['scope']) for item in planned_consumers])
    def prepare():
        if pinned.snapshot(home, observed) != before:
            c.fail('plan.stale', 'Consumer controls changed during update preparation.', 4)
        effects = output['data']['preparation'] = []
        for item in planned_consumers:
            observation = dict(root=item['row']['root'], effects={})
            effects.append(observation)
            declaration = proposals[item['row']['root']]
            store.ensure(home, declaration, locks[item['row']['root']], config, offline=True,
                         coordinates=selection.applicable_coordinates(declaration), effects=observation['effects'])
            retired = set(selection.applicable_coordinates(item['declaration'])) - set(selection.applicable_coordinates(declaration))
            if retired:
                old = r.lock(r.read_model(r.lock_path(item['root'], item['scope'], home), 'lock')[0])
                store.ensure(home, item['declaration'], old, config, offline=True, coordinates=sorted(retired), effects=observation['effects'])
    import mask_lifecycle
    try:
        mask_lifecycle.execute(args, output, home, config, selected, before_selected, candidate_plan, prepare,
                               details=dict(disclosure, host_load='not_verified'))
    except (Exception, KeyboardInterrupt):
        for row in commit_rows:
            if row['status'] == 'planned':
                row['status'] = 'not_attempted'
        raise
    commit_errors = []
    if commit_requested and not output['dry_run']:
        by_root = {row['root']: row for row in commit_rows}
        for row in sorted(commit_rows, key=lambda row: 'canonical' in row):
            if row['status'] == 'planned':
                progress.phase(('Propagating the upgrade commit to ' if 'canonical' in row else 'Committing project controls at ') + row['root'])
                try:
                    if 'canonical' in row:
                        source = dict(by_root[row['canonical']], branch=commit_observations[row['canonical']]['branch'])
                        commits.propagate(row, commit_observations[row['root']], final_controls[row['root']], source, config['git_timeout_seconds'])
                    else:
                        commits.execute(row, commit_observations[row['root']], final_controls[row['root']], config['git_timeout_seconds'])
                except KeyboardInterrupt:
                    for remaining in commit_rows:
                        if remaining['status'] == 'planned':
                            remaining['status'] = 'not_attempted'
                    raise
                finally:
                    if row['commit']:
                        output['changed'] = True
            if row['error']:
                commit_errors.append(row['error'])
        if scoped and commit_errors:
            c.fail('upgrade.commit_failed', 'The upgrade is applied, but its Git commit did not complete cleanly.', 5, errors=commit_errors)
    if blocked and not output['dry_run']:
        c.fail('upgrade.incomplete', 'Some selected consumers were blocked and not upgraded; the others were applied.', 4, blocked=blocked, errors=commit_errors)
    if commit_errors and not output['dry_run']:
        c.fail('upgrade.incomplete', 'Some project commits failed; applied upgrades and successful commits were retained.', 4, errors=commit_errors)
