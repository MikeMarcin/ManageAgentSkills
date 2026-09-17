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

NOT_ATTEMPTED = dict(attempted=False, ok=None, before=None, after=None, remote_refs_changed=None, error=None)


def fetch_tap(home, name, entry, timeout, selectors=(), consumer=None):
    """One git fetch: the tap's configured ref plus the objects its selected bindings name.

    Returns the disclosure row and the captured error, if any.
    """
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
                'source.dirty': 'this checkout has uncommitted changes', 'source.detached': 'this checkout is detached',
                'source.identity_mismatch': 'this checkout is not on main from the ManageAgentSkills remote'}


def refresh(args, output, home, root):
    """``update``: fast-forward the MASK program, then fetch every approved tap; no declaration, lock, link or consumer changes."""
    import mask_install
    failure = None
    try:
        mask_install.dispatch(args, output, home, root)
        program = dict(output['data'], status='updated' if output['changed'] else 'behind' if output['would_change'] else 'current')
    except c.MaskError as error:
        if error.code not in PROGRAM_HELD and not error.code.startswith('git.'):
            raise
        program = dict(status='held' if error.code in PROGRAM_HELD else 'failed', reason=PROGRAM_HELD.get(error.code, str(error)), code=error.code)
        failure = None if error.code in PROGRAM_HELD else error
    program_changed, program_would_change = output['changed'], output['would_change']
    raw = c.read_json(home / 'config.json', default={})
    output['data'] = dict(fetches={}, network='none')  # Stays so with no configuration yet, or on a machine that predates taps.
    try:
        if raw:
            fetch_all(args, output, home)
    finally:  # A tap that fails to fetch still discloses what happened to the program.
        output['data']['program'] = program
        if not output['dry_run']:
            output['data']['network'] = 'fetch'
        output.update(changed=program_changed, would_change=program_would_change)
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


def dispatch(args, output, home):
    import mask
    import mask_ensure as readiness
    import mask_selection as selection
    import mask_store as store
    if c.kind(home / 'pending.json') != 'missing':
        c.fail('recovery.required', 'Recover the pending operation before updating.', 8)
    config = c.config(c.read_json(home / 'config.json'))
    state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
    records = c.consumer_records(state)
    scoped = bool(getattr(args, 'project', None) or getattr(args, 'user', False))
    roots = mask.selected_roots(args, state, all_default=True)
    requested = getattr(args, 'skill', None) or []
    consumers, declared = [], set()
    for root in roots:
        scope = c.consumer_scope(state, root)
        c.registered_root(root, records[str(root)], scope)
        declaration = r.selection(c.read_json(c.declaration_path(root, scope, home), 'manifest'))
        bindings = {r.coordinate(binding) for binding in declaration['skills']}
        declared |= bindings
        named = sorted(set(requested) & bindings)
        if not requested or named:
            consumers.append(dict(root=root, scope=scope, declaration=declaration, skills=named,
                                  row=dict(root=str(root), scope=scope, status='unchanged', changes=[], error=None)))
    if len(set(requested)) != len(requested) or set(requested) - declared:
        c.fail('invocation.invalid', '--skill requires unique SOURCE/ID coordinates declared by the selected consumers.', 2)
    if not consumers:
        output['data'] = dict(consumers=[], fetches={}, network='none')
        output['warnings'].append(dict(code='project.empty_registry', message='No registered consumers selected.'))
        return
    observed = [(item['root'], item['scope']) for item in consumers]
    before = pinned.snapshot(home, observed)
    active, taps, selectors = [], set(), {}
    for item in consumers:
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
    fetching = not (output['dry_run'] or getattr(args, 'offline', False) or getattr(args, 'expect_plan_hash', None) is not None)
    fetches = {name: dict(NOT_ATTEMPTED) for name in sorted(taps)}
    disclosure = dict(consumers=rows, fetches=fetches, network='fetch' if fetching and taps else 'none')
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
    locks, payload_views, planned_consumers, blocked = {}, {}, [], []
    for item in active:
        row = item['row']
        failed = [name for name in item['taps'] if name in failures]
        if failed:
            if scoped:
                raise failures[failed[0]]
            row.update(status='blocked', error=failures[failed[0]].as_dict())
            blocked.append(row['root'])
            continue
        previous = r.lock(r.read_model(r.lock_path(item['root'], item['scope'], home), 'lock')[0])
        try:
            proposal = r.resolve_candidate(item['declaration'], config, home, previous, refresh=True, skills=item['skills'],
                                           allow_ref_rebind=getattr(args, 'allow_ref_rebind', False), payload_views=payload_views)
        except c.MaskError as error:
            if error.code != 'lock.resolution_required' or fetching:
                raise
            row.update(status='blocked', error=error.as_dict(), requires_fetch=True)
            blocked.append(row['root'])
            continue
        locks[row['root']] = proposal
        row.update(status='unchanged' if proposal == previous else 'updated', changes=changes(previous, proposal))
        planned_consumers.append(item)
    planned = fs.plan(config, state, [item['root'] for item in planned_consumers], home=home, lock_proposals=locks,
                      operation='upgrade', payload_views=payload_views)
    # The guard binds which roots were left out; fetch effects are not bound, so a dry run and a guarded rerun agree.
    planned['plan_hash'] = c.digest(dict(plan=planned['plan_hash'], blocked=blocked,
                                         skipped=[row['root'] for row in rows if row['status'] == 'skipped']))
    fs.public_plan(planned, output)
    output['data'].update(disclosure)
    output['warnings'][:] = [warning for warning in output['warnings'] if warning['code'] != 'project.empty_registry']
    fs.ensure_applicable(planned, getattr(args, 'expect_plan_hash', None))
    if output['dry_run']:
        return
    effects = output['data']['preparation'] = []
    for item in planned_consumers:
        observation = dict(root=item['row']['root'], effects={})
        effects.append(observation)
        store.ensure(home, item['declaration'], locks[item['row']['root']], config, offline=True,
                     coordinates=selection.applicable_coordinates(item['declaration']), effects=observation['effects'])
    with c.writer_lock(home):
        if pinned.snapshot(home, observed) != before:
            c.fail('plan.stale', 'Consumer controls, registry or configuration changed during the update; nothing was applied.', 4)
        fs.execute(planned, home, output)
    workflow = {}
    try:
        readiness.final_status(output)
    except c.MaskError as error:
        if error.code != 'workflow.incomplete' or not blocked:
            raise
        workflow = error.details  # The applied consumers' workflow verdict joins the blocked roots instead of masking them.
    if blocked:
        c.fail('upgrade.incomplete', 'Some selected consumers were blocked and not upgraded; the others were applied.', 4, blocked=blocked, **workflow)
