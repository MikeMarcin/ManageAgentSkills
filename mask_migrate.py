"""doctor --migrate: convert a live-checkout machine and its consumers to taps through one recoverable journal.

RFC-MASK-0020 AC04; contracts/MIGRATION.md. Detection and the shared declaration mapping live in ``mask_legacy``.

On a v1 or v2 machine the command is unscoped: the machine configuration and every registered legacy (mode-less)
consumer convert in one ``doctor.migrate`` journal, all or nothing. The clone HEAD is acquired into the tap cache
over file transport and materialized into the store before the writer lock; the ordinary planner then retargets the
links and converts the records. Nothing here writes to the clone, and recovery never requires it for rollback.

A registered legacy record whose declaration is already v2 refuses ``migration.declaration_unsupported``: its lock may
name other taps or commits absent from the clone, which an offline, clone-only migration cannot prove.

On a v3 (tap) machine the command converts one scoped straggler, ``--project PATH --alias NAME`` or ``--user --alias
NAME``, with install semantics: see :func:`migrate_straggler`. Its journal has no ``migration`` field and recovery never
reads a checkout.
"""
from __future__ import annotations

import copy
from pathlib import Path
import re
import time
import uuid

import mask_core as c
import mask_fs as fs
import mask_legacy as legacy
import mask_pinned as pinned
import mask_resolve as r
import mask_sources as sources

OPERATION = 'doctor.migrate'
FIELDS = ('config_before', 'config_after', 'source', 'cache')
SOURCE_FIELDS = ('root', 'identity', 'head', 'branch', 'index', 'repository', 'object_format')
# Extensions a machine migration never records; their presence makes the journal something else.
FOREIGN = ('git', 'launcher', 'controls', 'development', 'selection_change', 'setup')
REMEDIATION = ['mask', 'project', 'unregister', '--keep-links']


def refuse(failures, blockers):
    """The first typed blocker is the refusal with its own code and exit code; details carry every reported blocker."""
    first = failures[0]
    raise c.MaskError(first.code, str(first), first.exit_code, details=dict(first.details, blockers=blockers))


def migrated_config(config_before, home, alias, *, transport=None):
    """The v3 configuration a v1 or v2 configuration becomes under ``alias``; reads no Git and writes nothing.

    v1: one tap bound to the checkout. Its transport is the checkout's remote URL, supplied by the caller, or by
    default the checkout path itself. v2: ``source`` and ``legacy_source`` are dropped and every other tap is kept
    unchanged; the legacy binding stays under its alias and another alias renames it (the cache path follows the
    alias). An alias already naming a different tap refuses ``source.alias_conflict``.
    """
    before = c.config(config_before, legacy=True)
    home = Path(home)
    sources.alias(alias)
    if before['schema_version'] == 1:
        root = str(Path(before['source']['root']))
        catalog = {alias: sources.binding(home, alias, transport or root, before['source']['branch'], 'skills', authoring=root)}
    elif before['schema_version'] == 2:
        catalog = copy.deepcopy(before['sources'])
        entry = catalog.pop(before['legacy_source'])
        if alias != before['legacy_source']:
            entry = sources.binding(home, alias, entry['transport'], entry['ref'], entry['packages'], entry['authoring'])
        if alias in catalog and catalog[alias] != entry:
            c.fail('source.alias_conflict', 'The chosen alias already names a different approved tap.', 4, source=alias)
        catalog[alias] = entry
    else:
        c.fail('config.invalid', 'Only a v1 or v2 machine configuration migrates.')
    return c.config(dict(schema_version=3, default_targets=before['default_targets'],
                         git_timeout_seconds=before['git_timeout_seconds'], sources=catalog))


def clone_snapshot(root, repository):
    """The legacy checkout facts a migration binds; read-only."""
    root = Path(root)
    c.parents_safe(Path(root.anchor), root)
    if c.kind(root) != 'directory':
        c.fail('source.missing', 'The legacy checkout is missing.', 3, root=str(root))
    head = c.git(root, 'rev-parse', '--verify', '--quiet', 'HEAD^{commit}', optional=True)
    staged = c.git(root, 'ls-files', '--stage', '-z', binary=True, optional=True)
    return dict(root=str(root), identity=c.identity(root), head=head,
                branch=c.git(root, 'symbolic-ref', '--quiet', '--short', 'HEAD', optional=True),
                index=c.digest(staged) if staged is not None else None, repository=repository,
                object_format=c.git(root, 'rev-parse', '--show-object-format', optional=True) if head else None)


def references_alias(home, state, name):
    """Renaming the legacy tap must not orphan a registered pinned consumer that still names its alias."""
    for key, record in sorted(c.consumer_records(state).items()):
        if not pinned.is_pinned(record):
            continue
        scope = c.consumer_scope(state, key)
        found = name in record['last_manifest'].get('sources', {}) or any(row['source'] == name for row in record['last_lock']['packages'])
        try:
            declaration = c.read_json(c.declaration_path(key, scope, home), 'manifest', default={})
            locked = c.read_json(r.lock_path(Path(key), scope, home), 'lock', default={})
            found = found or name in (declaration.get('sources') or {}) or any(isinstance(row, dict) and row.get('source') == name for row in locked.get('packages') or [])
        except c.MaskError:
            pass  # An unreadable control is still bound by its cached record above.
        if found:
            c.fail('source.alias_conflict', 'A registered pinned consumer still names the legacy alias; keep that alias to migrate.', 4, source=name, root=key)


def locked_selection(declaration, alias, entry, clone_root, source, packages_seen):
    """Lock rows at the clone HEAD: one exact package per declared skill, with its validated payload."""
    import mask_packages as packages
    rows = []
    for binding in declaration['skills']:
        identifier = binding['id']
        if identifier not in packages_seen:
            found = [item for item in sources.discover(clone_root, alias, entry, source['head'], identifier=identifier) if item['id'] == identifier]
            if len(found) != 1:
                c.fail('skill.unknown', 'A declared skill is not exactly one package in the legacy checkout at HEAD.', 4, skill=identifier)
            packages_seen[identifier] = (found[0]['path'], packages.validate(clone_root, source['head'], found[0]['path'], identifier))
        path, payload = packages_seen[identifier]
        rows.append(dict(source=alias, id=identifier, repository=entry['repository'], path=path, commit=source['head'],
                         git_object_format=source['object_format'], selector=dict(ref=declaration['sources'][alias]['ref']),
                         **r.payload_digests(payload)))
    return r.lock(dict(schema_version=1, resolver='mask-lock-v1', selection_digest=r.selection_digest(declaration), packages=rows), declaration)


def acquire_from_clone(home, alias, entry, clone_root, head, timeout, effects):
    """Acquire the clone HEAD into the owned tap cache over file transport, retained as refs/mask/frozen/<head>.

    Identity is checked against the binding repository first. No ref is advertised or selected, and neither
    ``refs/mask/selected`` nor ``mask-refs.json`` is created. The clone is only read.
    """
    if not isinstance(head, str) or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', head):
        c.fail('source.ref_invalid', 'Acquisition from the legacy checkout requires a full commit.', 4)
    root = sources.cache_root(home, alias, entry)
    sources.endpoint(home, entry['transport'], entry['repository'])
    frozen = 'refs/mask/frozen/' + head
    object_format = 'sha256' if len(head) == 64 else 'sha1'
    effects.update(path=str(root), commit=head, source=str(clone_root), transport='file', cache_created=False,
                   acquired=False, retained_objects_possible=False, staging_ref=None, frozen_ref=frozen)
    if c.kind(root) == 'missing':
        c.parents_safe(home, root)
        root.parent.mkdir(parents=True, exist_ok=True)
        root.mkdir()
        effects['cache_created'] = True
        c.git(root, '-c', 'init.templateDir=', 'init', '--bare', '--object-format=' + object_format, mutating=True)
        c.atomic_text(root / 'mask-source.json', c.text_json(dict(schema_version=1, repository=entry['repository'], identity=c.identity(root))), None)
    sources.cached(home, alias, entry)
    if c.git(root, 'rev-parse', '--show-object-format') != object_format:
        c.fail('source.object_format', 'The legacy checkout and the approved cache object formats differ.', 4)
    identity = c.identity(root)
    previous = c.git(root, 'rev-parse', '--verify', '--quiet', frozen, optional=True)
    if previous not in (None, head):
        c.fail('source.cache_invalid', 'An exact cache ref has an unexpected value.', 4)
    if c.git(root, 'rev-parse', '--verify', '--quiet', head + '^{commit}', optional=True) != head:
        baseline, last = sources.cache_bytes(root), 0

        def monitor(force=False):
            nonlocal last
            now = time.monotonic()
            if not force and now - last < 0.05:
                return
            last = now
            size = sources.cache_bytes(root)
            if size > sources.CACHE_BYTES or size - baseline > sources.FETCH_BYTES:
                c.fail('source.fetch_limit', 'Acquisition from the legacy checkout exceeds storage policy; acquired objects are retained.', 4)
        staged = 'refs/mask/acquiring/' + uuid.uuid4().hex
        effects.update(staging_ref=staged, resource_policy=dict(fetch_growth_bytes=sources.FETCH_BYTES, cache_bytes=sources.CACHE_BYTES, storage_poll_seconds=0.05, hard_wire_byte_limit=False))
        monitor(True)
        sources.endpoint(root, entry['transport'], entry['repository'])
        effects['retained_objects_possible'] = True
        c.git(root, '-c', 'protocol.allow=never', '-c', 'protocol.file.allow=always', '-c', 'fetch.unpackLimit=0', '-c', 'gc.auto=0', 'fetch',
              '--no-tags', '--no-recurse-submodules', '--no-write-fetch-head', '--no-auto-maintenance',
              str(clone_root), '+' + head + ':' + staged, timeout=timeout, mutating=True, monitor=monitor)
        monitor(True)
        if c.identity(root) != identity or c.git(root, 'rev-parse', '--verify', '--quiet', staged + '^{commit}', optional=True) != head:
            c.fail('source.cache_invalid', 'Acquisition from the legacy checkout changed cache identity.', 4)
    else:
        staged = None
    if previous is None:
        c.git(root, 'update-ref', frozen, head, '0' * len(head), mutating=True)
    if staged is not None:
        c.git(root, 'update-ref', '-d', staged, head, mutating=True)
        effects['staging_ref'] = None
    effects['acquired'] = True
    return root


def dispatch(args, output, home):
    import mask_selection as selection
    import mask_store as store
    config_text = c.read_text(home / 'config.json')
    config_before = c.config(c.parse_json(config_text), legacy=True)
    if config_before['schema_version'] == 3:
        return migrate_straggler(args, output, home)
    if getattr(args, 'project', None) or getattr(args, 'user', False):
        c.fail('invocation.invalid', 'A live-checkout machine migrates its configuration and every legacy consumer together; omit --project and --user (or pass --all).', 2)
    if c.kind(home / 'pending.json') != 'missing':
        c.fail('recovery.required', 'Recover the pending operation before migrating.', 8)
    state_text = c.read_text(home / 'state.json', 'state', missing=True)
    state = c.state(c.parse_json(state_text, 'state')) if state_text is not None else c.empty_state()
    failures = []
    report, warnings = legacy.inspect(home, config_before, state, failures=failures)
    output['data'] = dict(migration=report)
    output['warnings'].extend(warnings)
    if failures:
        refuse(failures, report['blockers'] + [item for row in report['consumers'] for item in row['blockers']])
    rows = legacy.selected_consumers(home, state)
    consumers = [(root, scope) for root, scope, _ in rows]
    before = pinned.snapshot(home, consumers)
    observed = legacy.clone(config_before)
    alias = legacy.derived_alias(config_before, observed['remote_url'], getattr(args, 'alias', None))
    tap = legacy.proposed_tap(config_before, home, alias, observed)
    entry = {key: value for key, value in tap.items() if key != 'alias'}
    if config_before['schema_version'] == 2 and alias != config_before['legacy_source']:
        references_alias(home, state, config_before['legacy_source'])
    config_after = migrated_config(config_before, home, alias, transport=entry['transport'])
    if config_after['sources'][alias] != entry:
        c.fail('internal.invariant', 'The migrated configuration differs from the proposed tap.', 10)
    clone_root = Path(observed['root'])
    source = clone_snapshot(clone_root, entry['repository'])
    ref = 'refs/heads/' + config_before['source']['branch']
    proposals, locks, views, payloads, seen = {}, {}, {}, {}, {}
    for root, scope, record in rows:
        current = c.read_json(c.declaration_path(root, scope, home), 'manifest')
        if current.get('schema_version') != 1:
            c.fail('migration.declaration_unsupported', 'A legacy consumer already declares a v2 selection; release it with project unregister --keep-links (or workspace forget), then retry.', 4,
                   root=str(root), declaration_version=current.get('schema_version'), remediation=REMEDIATION)
        declaration = legacy.migrated_declaration(current, alias, entry, config_after['default_targets'], ref=ref)
        locked = locked_selection(declaration, alias, entry, clone_root, source, seen)
        proposals[str(root)], locks[str(root)] = declaration, locked
        for row in locked['packages']:
            payload = seen[row['id']][1]
            views[row['payload_digest']] = payload
            payloads[(row['payload_digest'], row['id'])] = (row, payload)
    planned = fs.plan(config_after, state, [root for root, _ in consumers], home=home, proposals=proposals, lock_proposals=locks,
                      operation=OPERATION, allow_migration=True, payload_views=views, legacy_checkout=clone_root)
    intent = planned['intent']
    if 'pinned' not in intent:
        # An empty registry still records the typed machine observations every pinned journal carries.
        intent.update(files=[], pinned=dict(workspaces=[], config_text=config_text, policy_text=c.read_text(home / 'integration.json', missing=True),
                                            selection_policy_text=selection.read_policy(home)[1], home_identity=c.identity(home)))
    config_after_text = c.text_json(config_after)
    intent['files'].append(dict(root=str(home), role='machine_config', before=config_text, after=config_after_text))
    migration = dict(config_before=config_text, config_after=config_after_text, source=source,
                     cache=dict(alias=alias, path=entry['cache'], commit=source['head']) if rows else None)
    intent['migration'] = migration
    planned['actions'].append(dict(kind='config.migrate', status='planned', path=str(home / 'config.json')))
    planned['would_change'] = True
    planned['plan_hash'] = c.digest(dict(plan=planned['plan_hash'], migration=migration))
    fs.public_plan(planned, output)
    output['warnings'][:] = [item for item in output['warnings'] if item['code'] != 'project.empty_registry']
    changes = []
    for root, scope, record in rows:
        key = str(root)
        changes.append(dict(root=key, scope=scope, declaration_before=c.read_json(c.declaration_path(root, scope, home), 'manifest'),
                            declaration_after=proposals[key], lock_after=locks[key],
                            links=[dict(relative=item['relative'], agent=item['target'], before=item['before'], after=item['after']) for item in intent['links'] if item['root'] == key]))
    output['data'].update(network='none', migration=dict(
        report, alias=alias, proposed_tap=tap, config_before=c.parse_json(config_text), config_after=config_after, source=source, changes=changes,
        acquisition=dict(alias=alias, cache=entry['cache'], commit=source['head'], source=str(clone_root), transport='file') if rows else None))
    fs.ensure_applicable(planned, getattr(args, 'expect_plan_hash', None))
    if output['dry_run']:
        return
    effects = output['data']['preparation'] = []
    completed = False
    try:
        if rows:
            acquisition = {}
            effects.append(dict(alias=alias, effects=dict(acquisitions=[acquisition])))
            acquire_from_clone(home, alias, entry, clone_root, source['head'], config_before['git_timeout_seconds'], acquisition)
            for row, payload in payloads.values():
                artifact = {}
                effects.append(dict(skill=r.coordinate(row), effects=dict(artifacts=[artifact])))
                store.materialize(home, row, payload, effects=artifact)
        with c.writer_lock(home):
            if c.kind(home / 'pending.json') != 'missing':
                c.fail('recovery.required', 'Recover the pending operation before migrating.', 8)
            if (pinned.snapshot(home, consumers) != before
                    or c.read_text(home / 'config.json', missing=True) != config_text
                    or c.read_text(home / 'state.json', 'state', missing=True) != state_text
                    or clone_snapshot(clone_root, entry['repository']) != source
                    or not unchanged_links(planned['intent'])):
                c.fail('plan.stale', 'The configuration, a consumer control, an owned link or the legacy checkout changed during preparation; nothing was migrated.', 4)
            pending = fs.make_pending(planned, home)
            pending['schema_version'] = 3
            fs.execute(planned, home, output, pending=pending)
        completed = True
    finally:
        pinned.merge_preparation(output, completed=completed)
        output['data']['network'] = 'none'


def unchanged_links(intent):
    """Under the writer lock, before any journal exists: every link the plan replaces still has its planned before text, or is still absent.

    A link edited during preparation is then plan.stale with nothing written, rather than a retained journal that recovery refuses.
    """
    for entry in intent['links']:
        root = Path(entry['root'])
        leaf = root / entry['relative']
        c.parents_safe(root, leaf)
        actual = fs.link_value(leaf)
        if actual['link_text'] != entry['before'] or entry['before'] is None and actual['type'] != 'missing':
            return False
    return True


def migrate_straggler(args, output, home):
    """M11: on a tap machine, convert one straggler v1 declaration with install semantics (MIGRATION.md "Scope and atomicity").

    ``--project PATH --alias NAME`` or ``--user --alias NAME``. The v1 declaration becomes a v2 declaration bound to the
    approved tap NAME without a ref, as install writes it. Each binding resolves through the ordinary resolver, fetching on
    demand unless ``--offline`` or ``--dry-run``. One ``doctor.migrate`` journal without a ``migration`` field then registers
    the consumer (or converts its registered legacy record) and links from the store. The configuration is unchanged and no
    checkout is read. A scope with nothing to convert is an idempotent no-op.
    """
    import mask_ensure as readiness
    import mask_selection as selection
    import mask_store as store
    import mask_task as task
    project, user, alias = getattr(args, 'project', None), getattr(args, 'user', False), getattr(args, 'alias', None)
    if getattr(args, 'all', False) or alias is None or not (project or user):
        c.fail('invocation.invalid', 'A tap machine migrates one straggler declaration: doctor --migrate --project PATH --alias NAME (or --user --alias NAME).', 2)
    config_text = c.read_text(home / 'config.json')
    config = c.config(c.parse_json(config_text))
    entry = sources.selected(config, alias)
    if c.kind(home / 'pending.json') != 'missing':
        c.fail('recovery.required', 'Recover the pending operation before migrating.', 8)
    state_text = c.read_text(home / 'state.json', 'state', missing=True)
    state = c.state(c.parse_json(state_text, 'state')) if state_text is not None else c.empty_state()
    failures = []
    report, warnings = legacy.inspect(home, config, state, project=project, user=user, failures=failures)
    output['data'] = dict(migration=report)
    output['warnings'].extend(warnings)
    if failures:
        refuse(failures, report['blockers'] + [item for row in report['consumers'] for item in row['blockers']])
    rows = legacy.selected_consumers(home, state, project=project, user=user)
    if not rows:
        return  # Already a tap consumer, or nothing declared: report.required is False and nothing changes.
    root, scope, record = rows[0]
    key, consumers = str(root), [(root, scope)]
    before = pinned.snapshot(home, consumers)
    current = c.read_json(c.declaration_path(root, scope, home), 'manifest')
    declaration = legacy.migrated_declaration(current, alias, entry, config['default_targets'])
    views = {}
    resolved = [task.resolve_row(home, declaration, binding, entry, config, args, output, views) for binding in declaration['skills']]
    acquisitions = output['data'].get('acquisitions', [])
    locked = r.lock(dict(schema_version=1, resolver='mask-lock-v1', selection_digest=r.selection_digest(declaration), packages=resolved), declaration)
    planned = fs.plan(config, state, [root], home=home, proposals={key: declaration}, lock_proposals={key: locked},
                      register=[key] if record is None else (), user_root=root if scope == 'user' else None,
                      operation=OPERATION, allow_migration=True, payload_views=views)
    fs.public_plan(planned, output)
    links = [dict(relative=item['relative'], agent=item['target'], before=item['before'], after=item['after']) for item in planned['intent']['links']]
    output['data'].update(acquisitions=acquisitions, network='fetch' if acquisitions else 'none', migration=dict(
        report, alias=alias, changes=[dict(root=key, scope=scope, registered=record is not None, declaration_before=current,
                                           declaration_after=declaration, lock_after=locked, links=links)]))
    fs.ensure_applicable(planned, getattr(args, 'expect_plan_hash', None))
    if output['dry_run']:
        return
    observation = dict(root=key, effects={})
    output['data']['preparation'] = [observation]
    completed = False
    try:
        store.ensure(home, declaration, locked, config, offline=True, coordinates=selection.applicable_coordinates(declaration), effects=observation['effects'])
        with c.writer_lock(home):
            if c.kind(home / 'pending.json') != 'missing':
                c.fail('recovery.required', 'Recover the pending operation before migrating.', 8)
            if (pinned.snapshot(home, consumers) != before
                    or c.read_text(home / 'config.json', missing=True) != config_text
                    or c.read_text(home / 'state.json', 'state', missing=True) != state_text
                    or not unchanged_links(planned['intent'])):
                c.fail('plan.stale', 'The configuration, registry, consumer declaration or an owned link changed during preparation; nothing was migrated.', 4)
            pending = fs.make_pending(planned, home)
            pending['schema_version'] = 3
            fs.execute(planned, home, output, pending=pending)
        completed = output['transaction'] == 'committed'
    finally:
        pinned.merge_preparation(output, completed=completed)
    # Links are committed above; declared roles or inputs still unmet make the migration nonzero, as install does.
    readiness.final_status(output)


def conflict(message, **details):
    c.fail('recovery.conflict', message, 8, **details)


def journal_alias(value, before, after_value, home):
    """The alias whose recomputed configuration is exactly the recorded after bytes."""
    names = [value['cache']['alias']] if isinstance(value['cache'], dict) else sorted((after_value.get('sources') or {}))
    for name in names:
        try:
            transport = after_value['sources'][name]['transport'] if before['schema_version'] == 1 else None
            if c.text_json(migrated_config(before, home, name, transport=transport)) == value['config_after']:
                return name
        except (c.MaskError, KeyError, TypeError):
            continue
    conflict('Migration config changes exceed the recorded legacy conversion.')


def validate_journal(pending, home):
    """Recompute a doctor.migrate journal from its own records; never reads the clone.

    A journal with a ``migration`` field converts a live-checkout machine; one without it converts a straggler on a tap machine.
    """
    try:
        if 'migration' in pending:
            check_recorded(pending, Path(home))
        else:
            check_straggler(pending, Path(home))
    except c.MaskError as error:
        if error.code == 'recovery.conflict':
            raise
        conflict('The doctor migration journal disagrees with its recorded intent.', cause=error.as_dict())
    except (AttributeError, KeyError, TypeError, ValueError, StopIteration):
        conflict('Invalid doctor migration journal.')


def check_recorded(pending, home):
    value = pending.get('migration')
    c.fields(value, FIELDS, family='recovery')
    files = pending.get('files')
    if (pending['operation'] != OPERATION or pending['schema_version'] != 3 or not isinstance(pending.get('pinned'), dict) or not isinstance(files, list)
            or any(name in pending for name in FOREIGN) or pending['manifests'] != []):
        conflict('A doctor migration requires its typed pinned journal and no other transition.')
    if not isinstance(value['config_before'], str) or not isinstance(value['config_after'], str) or value['config_before'] != pending['pinned'].get('config_text'):
        conflict('Migration before config must preserve its exact observed bytes.')
    before = c.config(c.parse_json(value['config_before']), legacy=True)
    if before['schema_version'] not in (1, 2):
        conflict('Only a live-checkout configuration migrates.')
    after_value = c.parse_json(value['config_after'])
    alias = journal_alias(value, before, after_value, home)
    after = c.config(after_value)
    if not isinstance(pending['config'], dict) or c.text_json(pending['config']) != value['config_after']:
        conflict('Journal intent config differs from the migration after bytes.')
    machine = dict(root=str(home), role='machine_config', before=value['config_before'], after=value['config_after'])
    if not files or files[-1] != machine or sum(1 for item in files if isinstance(item, dict) and item.get('role') == 'machine_config') != 1:
        conflict('Migration config bytes or typed coverage changed.')
    if c.read_text(home / 'config.json', missing=True) not in (value['config_before'], value['config_after']):
        conflict('Machine configuration changed since the pending migration.')
    source, entry = value['source'], after['sources'][alias]
    c.fields(source, SOURCE_FIELDS, family='recovery')
    if source['root'] != entry['authoring'] or source['repository'] != entry['repository']:
        conflict('Migration source observation differs from the migrated tap.')
    before_records, after_records = c.consumer_records(pending['before_state']), c.consumer_records(pending['after_state'])
    legacy_roots = {root for root, record in before_records.items() if legacy.is_legacy(record)}
    if set(pending['selected']) != legacy_roots:
        conflict('A machine migration converts exactly every registered legacy consumer.')
    workspaces = {item['root']: item for item in pending['pinned']['workspaces']}
    ref = 'refs/heads/' + before['source']['branch']
    for root in pending['selected']:
        new = after_records.get(root)
        if not isinstance(new, dict) or new.get('mode') != 'pinned':
            conflict('Migration needs legacy before and pinned after ownership.', root=root)
        expected = legacy.migrated_declaration(c.parse_json(workspaces[root]['manifest'], 'manifest'), alias, entry, after['default_targets'], ref=ref)
        if new['last_manifest'] != expected:
            conflict('Migrated selection differs from the observed legacy declaration.', root=root)
        # A consumer that selects nothing migrates to an empty lock; every row it does lock names the observed HEAD.
        if any(row['commit'] != source['head'] or row['source'] != alias for row in new['last_lock']['packages']):
            conflict('Migrated locks must name the observed checkout HEAD.', root=root)
    if pending['selected']:
        if source['head'] is None or value['cache'] != dict(alias=alias, path=entry['cache'], commit=source['head']):
            conflict('Migration cache acquisition differs from the observed checkout HEAD.')
    elif value['cache'] is not None or files != [machine] or pending['links']:
        conflict('An empty-registry migration converts the configuration only.')


def check_straggler(pending, home):
    """A tap-machine migration: one unregistered or legacy consumer becomes pinned on the unchanged configuration.

    Its after selection must be exactly the mapping of the observed v1 declaration onto the one approved tap it binds, and
    every lock row must name that tap. No clone exists, so ``check_journal`` is never called for such a journal.
    """
    files = pending.get('files')
    if (pending['operation'] != OPERATION or pending['schema_version'] != 3 or not isinstance(pending.get('pinned'), dict)
            or not isinstance(files, list) or any(name in pending for name in FOREIGN) or pending['manifests'] != []):
        conflict('A tap-machine migration requires its typed pinned journal and no other transition.')
    config = c.config(pending['config'])
    if config != c.config(c.read_json(home / 'config.json', default={})):
        conflict('Machine configuration changed since the pending migration.')
    if len(pending['selected']) != 1:
        conflict('A tap-machine migration converts exactly one consumer.')
    root = pending['selected'][0]
    old, new = c.consumer_records(pending['before_state']).get(root), c.consumer_records(pending['after_state']).get(root)
    if not (old is None or legacy.is_legacy(old)) or not isinstance(new, dict) or new.get('mode') != 'pinned':
        conflict('A tap-machine migration needs an unregistered or legacy before record and a pinned after record.', root=root)
    scope = c.consumer_scope(pending['after_state'], root)
    if any(not isinstance(item, dict) or item.get('root') != root or item.get('role') not in (scope + '_declaration', scope + '_lock') for item in files):
        conflict('A tap-machine migration writes only the consumer declaration and lock.', root=root)
    workspace = next(item for item in pending['pinned']['workspaces'] if item['root'] == root)
    names = sorted(new['last_manifest']['sources'])
    if len(names) != 1 or names[0] not in config['sources']:
        conflict('A tap-machine migration binds exactly one approved tap.', root=root)
    alias = names[0]
    expected = legacy.migrated_declaration(c.parse_json(workspace['manifest'], 'manifest'), alias, config['sources'][alias], config['default_targets'])
    if new['last_manifest'] != expected:
        conflict('Migrated selection differs from the observed v1 declaration.', root=root)
    if any(row['source'] != alias for row in new['last_lock']['packages']):
        conflict('Migrated locks must name the migrated tap.', root=root)


def check_journal(pending, home):
    """Before reaching the after side: the clone must still be exactly what the migration observed. Rollback never calls this."""
    migration = pending['migration']
    recorded = migration['source']
    try:
        observed = clone_snapshot(recorded['root'], recorded['repository'])
        before = c.config(c.parse_json(migration['config_before']), legacy=True)
        transport = None
        if before['schema_version'] == 1:
            transport = c.git(Path(recorded['root']), 'remote', 'get-url', before['source']['remote'], optional=True) or recorded['root']
        alias = journal_alias(migration, before, c.parse_json(migration['config_after']), home)
        derived = c.text_json(migrated_config(before, home, alias, transport=transport))
    except c.MaskError as error:
        conflict('The legacy checkout can no longer be observed; roll back, or restore it before completing.', cause=error.as_dict())
    if observed != recorded or derived != migration['config_after']:
        conflict('The legacy checkout changed since the migration was planned; roll back, or restore it before completing.')
