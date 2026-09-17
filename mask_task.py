"""Complete task commands over the existing engine (RFC-MASK-0018, contract sections 1-2).

``install`` and ``remove`` build one prospective declaration (and, for pinned
consumers, one lock) through the shared resolver, planner and journal, then
activate that single frozen plan. Missing declarations and registration are
folded into the same operation; unrelated bindings, pins, agents and the other
scope are never rewritten. ``list`` is a read-only view derived from the same
plan the mutating commands would use. Nothing here shells out through a second
orchestration layer, and a direct task command asks for no confirmation because
its scoped engine effects are ordinary authority (contract section 3).
"""
from __future__ import annotations

import copy
import os
from pathlib import Path

import mask_adapters as adapters
import mask_core as c
import mask_fs as fs
import mask_pinned as pinned
import mask_resolve as r
import mask_selection as selection
import mask_sources as sources
import mask_store as store

TASKS = ('install', 'remove', 'list')


def machine(home):
    state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
    raw = c.read_json(home / 'config.json', default={})
    if not raw:
        c.fail('config.missing', 'Add a skill source before managing skills.')
    return state, c.config(raw)


def consumer(args, state, home, *, creating):
    """Selected root, scope, registry key and record. Project is the default scope."""
    if getattr(args, 'user', False):
        record = state.get('user')
        root = Path(record['root']) if record else Path.home().resolve()
        if not root.is_dir():
            c.fail('user.not_found', 'The personal home must be an existing directory.', 4, root=str(root))
        return root, 'user', str(root), record
    requested = getattr(args, 'project', None)
    if requested is not None:
        root = c.project_root(requested)
    else:
        try:
            root = c.project_root()
        except c.MaskError as error:
            if error.code != 'manifest.missing' or not creating:
                raise
            root = c.project_root(initializing=True)
    for known in state['projects']:
        if Path(known).is_dir() and os.path.samefile(root, known):
            root = Path(known)
            break
    return root, 'project', str(root), state['projects'].get(str(root))


def fresh_declaration(config=None):
    """A new consumer is always an empty v2 selection: the machine's default agents, or every agent before a machine exists."""
    if config is None:
        return dict(schema_version=2, sources={}, skills=[])
    return r.selection(dict(schema_version=2, sources={}, default_agents=config['default_targets'], skills=[]))


def parse_request(identifiers):
    """Requested ``ID`` or ``SOURCE/ID`` operands; duplicates are an invocation error."""
    requested = []
    for raw in identifiers:
        if raw.count('/') > 1 or raw.startswith('/') or raw.endswith('/'):
            c.fail('invocation.invalid', 'Use ID or SOURCE/ID.', 2, operand=raw)
        alias, identifier = raw.split('/') if '/' in raw else (None, raw)
        c.skill_id(identifier)
        if alias is not None:
            sources.alias(alias)
        if (alias, identifier) in requested:
            c.fail('invocation.invalid', 'Each skill may be requested once.', 2, operand=raw)
        requested.append((alias, identifier))
    return requested


def choose_source(identifier, proposal, config, home, args, output, consumer=None):
    """A bare ID resolves only when exactly one relevant approved catalog offers it."""
    bound = sorted({row['source'] for row in proposal['skills'] if row['id'] == identifier})
    if len(bound) == 1:
        return bound[0]
    if len(bound) > 1:
        c.fail('skill.ambiguous', 'The skill is selected from several sources; name one.', 4, skill=identifier, choices=[name + '/' + identifier for name in bound])
    matches, unresolved = [], []
    for name in sorted(config['sources']):
        entry = config['sources'][name]
        probe = dict(schema_version=2, sources={name: dict(repository=entry['repository'], packages=entry['packages'])}, skills=[dict(source=name, id=identifier)])
        try:
            resolve_row(home, r.selection(probe), dict(source=name, id=identifier), entry, config, args, output, consumer=consumer)
        except c.MaskError as error:
            if error.code == 'skill.unknown':
                continue
            if error.code == 'lock.resolution_required':
                unresolved.append(name)
                continue
            raise
        matches.append(name)
    if unresolved:
        c.fail('source.unresolved', 'A bare ID cannot be chosen while an approved catalog is unresolved; fetch it or name SOURCE/ID.', 4,
               skill=identifier, unresolved=unresolved, resolved=matches)
    if len(matches) > 1:
        c.fail('skill.ambiguous', 'The skill exists in more than one approved source; name SOURCE/ID.', 4, skill=identifier, choices=[name + '/' + identifier for name in matches])
    if not matches:
        c.fail('skill.unknown', 'No approved source offers this skill.', 4, skill=identifier, sources=sorted(config['sources']))
    return matches[0]


def resolve_row(home, declaration, binding, entry, config, args, output, payload_views=None, consumer=None):
    """Resolve one new binding from the approved cache; a live install may first acquire the approved source."""
    try:
        return r.resolve_binding(home, declaration, binding, entry, payload_views)
    except c.MaskError as error:
        if error.code != 'lock.resolution_required' or getattr(args, 'offline', False) or output['dry_run']:
            raise
    scratch = dict(data={})
    sources.fetch(home, binding['source'], entry, config['git_timeout_seconds'], scratch, consumer=consumer)
    output['data'].setdefault('acquisitions', []).append(dict(source=binding['source'], **scratch['data']))
    return r.resolve_binding(home, declaration, binding, entry, payload_views)


def v2_proposal(args, declaration, config, requested, output, root, scope, home, record):
    """Retain unrelated exact resolutions, sources, conditions and overrides; resolve only new bindings."""
    installing = args.command == 'install'
    if record is not None and record.get('mode') == 'dev-link':
        c.fail('dev_link.active', 'Return to pins explicitly before ordinary task operations.', 4)
    lock_value = r.read_model(r.lock_path(root, scope, home), 'lock', missing=True)[0]
    previous = r.lock(lock_value, declaration) if lock_value is not None else None
    prior_rows = {r.coordinate(row): row for row in previous['packages']} if previous else {}
    proposal = copy.deepcopy(declaration)
    agents = sorted(set(r.agents(args.agent))) if installing and getattr(args, 'agent', None) else None
    changed, unchanged, new = [], [], set()
    for alias, identifier in requested:
        if alias is None and installing:
            alias = choose_source(identifier, proposal, config, home, args, output, root if scope == 'project' else None)
        elif alias is None:
            bound = sorted({row['source'] for row in proposal['skills'] if row['id'] == identifier})
            if len(bound) > 1:
                c.fail('skill.ambiguous', 'The skill is selected from several sources; name one.', 4, skill=identifier, choices=[name + '/' + identifier for name in bound])
            alias = bound[0] if bound else None
        # An unselected bare ID stays bare in the not-selected warning; no source alias is invented for it.
        coordinate = identifier if alias is None else alias + '/' + identifier
        present = next((row for row in proposal['skills'] if r.coordinate(row) == coordinate), None)
        if installing:
            if present is not None:
                unchanged.append(coordinate)
                continue
            entry = sources.selected(config, alias)
            if alias not in proposal['sources']:
                proposal['sources'][alias] = dict(repository=sources.repository(entry['repository']), packages=entry['packages'])
            binding = dict(source=alias, id=identifier)
            if agents:
                binding['agents'] = agents
            proposal['skills'].append(binding)
            new.add(coordinate)
            changed.append(coordinate)
        elif present is None:
            unchanged.append(coordinate)
            output['warnings'].append(dict(code='selection.not_selected', message='Skill is not selected in this scope; nothing to remove.', skill=coordinate))
        else:
            proposal['skills'] = [row for row in proposal['skills'] if r.coordinate(row) != coordinate]
            changed.append(coordinate)
    if changed:  # The declaration and lock are written anyway, so they take the canonical spelling (RFC-MASK-0022).
        for entry in proposal['sources'].values():
            entry['repository'] = sources.repository(entry['repository'])
        prior_rows = {key: dict(row, repository=sources.repository(row['repository'])) for key, row in prior_rows.items()}
    proposal = r.selection(proposal)
    entries = r.approved(proposal, config)
    payload_views = {}
    rows = []
    for binding in proposal['skills']:
        coordinate = r.coordinate(binding)
        if coordinate in prior_rows and coordinate not in new:
            rows.append(prior_rows[coordinate])
        else:
            # A project install lends its origin's scheme to transport selection (RFC-MASK-0022); the personal scope has no checkout.
            rows.append(resolve_row(home, proposal, binding, entries[binding['source']], config, args, output, payload_views, root if scope == 'project' else None))
    lock = r.lock(dict(schema_version=1, resolver='mask-lock-v1', selection_digest=r.selection_digest(proposal), packages=rows), proposal)
    return proposal, lock, changed, unchanged, payload_views, previous


def mutate(args, output, home):
    """install/remove: one proposal, one plan, one journaled activation."""
    installing = args.command == 'install'
    if c.kind(home / 'pending.json') != 'missing':
        c.fail('recovery.required', 'Inspect and recover the pending operation first.', 8)
    state, config = machine(home)
    requested = parse_request(args.ids)
    root, scope, key, record = consumer(args, state, home, creating=installing)
    if not installing and record is None:
        c.fail(scope + '.not_registered', 'Nothing is deployed for this scope, so there is nothing to remove.', 4, root=key)
    path = c.declaration_path(root, scope, home)
    text = c.read_text(path, 'manifest', missing=True)
    created = {}
    if text is None:
        if not installing:
            c.fail('manifest.missing', 'No declaration exists for this scope.', 4, path=str(path))
        fresh = fresh_declaration(config)
        created[path] = c.text_json(fresh)
        created[r.lock_path(root, scope, home)] = c.text_json(dict(schema_version=1, resolver='mask-lock-v1', selection_digest=r.selection_digest(fresh), packages=[]))
    declaration = c.selection_manifest(c.parse_json(text if text is not None else created[path], 'manifest'))
    proposal, lock, changed, unchanged, payload_views, previous = v2_proposal(args, declaration, config, requested, output, root, scope, home, record)
    acquisitions = output['data'].get('acquisitions', [])
    task = dict(root=key, scope=scope, declaration_path=str(path), registered=record is not None, declaration_created=bool(created),
                mode=(record or {}).get('mode', 'pinned'),
                requested=[identifier if alias is None else alias + '/' + identifier for alias, identifier in requested],
                added=changed if installing else [], removed=[] if installing else changed, already=unchanged,
                skills=[r.coordinate(row) for row in proposal['skills']],
                acquisitions=acquisitions, network='fetch' if acquisitions else 'none')
    if getattr(args, 'agent', None):
        task['agents'] = sorted(set(args.agent))
    if created and output['dry_run']:
        # A dry run writes nothing, so the shared planner cannot see the declaration it would create.
        output['data'] = dict(task, plan='not_computed')
        output['would_change'] = True
        output['actions'] = [dict(kind='declaration.create', status='planned', path=str(path))]
        output['actions'] += [dict(kind='link.create', status='planned', skill=skill) for skill in task['added']]
        return
    consumers = [(root, scope)]
    committed = False
    try:
        for control, content in created.items():
            # The shared planner and journal replace existing controls; new files are removed again unless the task commits.
            c.atomic_text(control, content, None)
        before = pinned.snapshot(home, consumers)
        planned = fs.plan(config, state, [root], proposals={key: proposal}, lock_proposals={key: lock},
                          register=[key] if record is None else (), operation=args.command, home=home,
                          user_root=root if scope == 'user' else None, payload_views=payload_views)
        fs.public_plan(planned, output)
        output['data'].update(task)
        if created:
            output['would_change'] = True
        fs.ensure_applicable(planned, getattr(args, 'expect_plan_hash', None))
        if output['dry_run']:
            return
        observation = dict(root=key, effects={})
        output['data']['preparation'] = [observation]
        store.ensure(home, proposal, lock, config, offline=True, coordinates=selection.applicable_coordinates(proposal), effects=observation['effects'])
        kept = {r.coordinate(row) for row in lock['packages']}
        retired = [coordinate for coordinate in selection.applicable_coordinates(declaration) if coordinate not in kept] if previous is not None else []
        if retired:
            # The journal verifies the removed links' old artifacts as well; prepare them offline from the approved cache too.
            removal = dict(root=key, effects={})
            output['data']['preparation'].append(removal)
            store.ensure(home, declaration, previous, config, offline=True, coordinates=retired, effects=removal['effects'])
        with c.writer_lock(home):
            if c.kind(home / 'pending.json') != 'missing':
                c.fail('recovery.required', 'Inspect and recover the pending operation first.', 8)
            if pinned.snapshot(home, consumers) != before:
                c.fail('plan.stale', 'The declaration, lock, registry or workspace changed during preparation; nothing was applied.', 4)
            fs.execute(planned, home, output)
            committed = output['transaction'] == 'committed'
        # Links are committed above; declared roles or inputs still unmet make the task nonzero (setup consent lives on ensure).
        import mask_ensure as readiness
        readiness.final_status(output)
    finally:
        for control, content in created.items():
            if not committed and c.read_text(control, 'manifest', missing=True) == content:
                control.unlink()


def link_state(relative, expected, leaves, registered):
    wanted = expected.get(relative)
    leaf = leaves.get(relative)
    if wanted is None:
        return 'excluded'
    if not registered:
        return 'not deployed'
    if leaf is None:
        return 'unknown'
    if leaf['type'] == 'symlink':
        return 'linked' if leaf['link_text'] == wanted['link_text'] else 'drift'
    if leaf['type'] == 'missing':
        return 'missing'
    return 'collision'


def listing(args, output, home):
    """Selected/deployed skills and per-agent states for one scope, from the shared plan."""
    state, config = machine(home)
    root, scope, key, record = consumer(args, state, home, creating=True)
    path = c.declaration_path(root, scope, home)
    text = c.read_text(path, 'manifest', missing=True)
    data = output['data'] = dict(root=key, scope=scope, declaration_path=str(path), registered=record is not None,
                                 declared=text is not None, agents=sorted(adapters.BY_ID), skills=[], links=dict(expected=0, linked=0),
                                 mode=(record or {}).get('mode'), limitations=['Host loading and workflow setup were not checked by this listing.'])
    if text is None:
        data['mode'] = None
        return
    declaration = c.selection_manifest(c.parse_json(text, 'manifest'))
    data['mode'] = data['mode'] or 'pinned'
    planned = fs.plan(config, state, [root], register=[] if record else [key], home=home, user_root=root if scope == 'user' else None, operation='list')
    for blocker in planned['blockers']:
        output['warnings'].append(dict(code=blocker['code'], message=blocker['message'], details=blocker.get('details')))
    expected = c.consumer_records(planned['intent']['after_state']).get(key, {}).get('links', {}) if not planned['blockers'] else {}
    leaves = {leaf['relative']: leaf for entry in planned['projects'] + planned['users'] if entry['root'] == key for leaf in entry['leaves']}
    lock_value = r.read_model(r.lock_path(root, scope, home), 'lock', missing=True)[0]
    rows = {r.coordinate(row): row for row in (lock_value or {}).get('packages', [])} if isinstance(lock_value, dict) else {}
    data['source'] = dict(mode='pinned', sources=sorted(declaration['sources']))
    bindings = [(r.coordinate(binding), binding['id'], binding['source'], rows.get(r.coordinate(binding))) for binding in declaration['skills']]
    linked = 0
    for coordinate, identifier, alias, row in bindings:
        states = {}
        for agent in data['agents']:
            states[agent] = link_state(adapters.relative(agent, scope, identifier), expected, leaves, record is not None)
            linked += states[agent] == 'linked'
        entry = dict(skill=coordinate, id=identifier, source=alias, states=states)
        if row is not None:
            entry.update(commit=row.get('commit'), version=row.get('selector'))
        data['skills'].append(entry)
    data['links'] = dict(expected=len(expected), linked=linked)
    data['shadowing'] = planned['shadowing']
    output['warnings'].extend(fs.shadow_warnings(planned['shadowing']))


def dispatch(args, output, home):
    if args.command == 'list':
        listing(args, output, home)
        return True
    if args.command in ('install', 'remove'):
        mutate(args, output, home)
        return True
    return False
