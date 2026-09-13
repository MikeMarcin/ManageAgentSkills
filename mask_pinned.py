"""Pinned model and orchestration seams for the ordinary MASK engine."""
from __future__ import annotations

import copy
from pathlib import Path

import mask_core as c
import mask_resolve as r
import mask_adapters as adapters


def is_pinned(record):
    return isinstance(record, dict) and record.get('mode') in ('pinned', 'dev-link')


def validate_record(record):
    c.fields(record, ('root', 'root_identity', 'last_manifest', 'last_manifest_digest', 'last_source_revision', 'links', 'mode', 'last_lock'), ('dev_links', 'native_roles'), family='state')
    if record['last_source_revision'] is not None:
        c.fail('state.invalid', 'Pinned records require exact lock identities, not a shared revision.')
    declaration = r.selection(record['last_manifest'])
    resolved = r.lock(record['last_lock'], declaration)
    if record['last_manifest_digest'] != r.selection_digest(declaration):
        c.fail('state.invalid', 'Pinned cached selection digest differs.')
    rows = {r.coordinate(row): row for row in resolved['packages']}
    devs = record.get('dev_links', {})
    if not isinstance(devs, dict) or bool(devs) != (record['mode'] == 'dev-link'):
        c.fail('state.invalid', 'Development mode requires explicit selected authoring overrides.')
    for key, value in devs.items():
        validate_dev(value)
        if key not in rows or key != value['source'] + '/' + value['id']:
            c.fail('state.invalid', 'Development override is outside the cached selection.')
    if not isinstance(record['links'], dict):
        c.fail('state.invalid', 'Invalid pinned ownership map.')
    for link in record['links'].values():
        c.fields(link, ('skill', 'target', 'link_text', 'resolution'), ('dev',), family='state')
        row = link['resolution']
        if not isinstance(row, dict) or 'source' not in row or 'id' not in row:
            c.fail('state.invalid', 'Pinned link resolution needs a source and ID.')
        c.skill_id(row['source'])
        c.skill_id(row['id'])
        if rows.get(r.coordinate(row)) != row or link['skill'] != row['id']:
            c.fail('state.invalid', 'Pinned link resolution differs from its cached lock.')
        if link.get('dev') != devs.get(r.coordinate(row)):
            c.fail('state.invalid', 'Development link differs from its scope override.')
    return declaration


def target(link, config, home):
    import mask_store as store
    if 'dev' in link:
        validate_dev(link['dev'], config)
        return Path(link['dev']['root']) / link['dev']['path']
    if 'resolution' in link:
        return store.location(home, link['resolution']['payload_digest'], link['skill'])[1]
    if c.legacy_source(config) is None:
        c.fail('migration.required', 'A legacy link record has no live checkout on a tap catalog machine; it must be migrated.', 4, skill=link['skill'])
    return c.legacy_source(config) / 'skills' / link['skill']


def simple_targets(declaration):
    """Display the requested supported agent union; compatibility is evaluated separately."""
    declaration = r.selection(declaration)
    requested = set()
    for binding in declaration['skills']:
        agents = binding.get('agents', declaration['default_agents'])
        requested.update(c.ADAPTERS if agents == 'all' else agents)
    return sorted(requested)


def metadata_supported(home, row, payload=None, *, config=None, verified=None):
    """Read verified passive metadata; absence and publisher assertions remain distinct."""
    import mask_store as store
    from mask_provenance import regular_bytes
    if verified is not None:
        verified[r.coordinate(row)] = False
    if payload is not None:
        store.checked_payload(payload, row)
        if c.kind(store.location(home, row['payload_digest'], row['id'])[0]) != 'missing':
            store.verify(home, row)
            if verified is not None:
                verified[r.coordinate(row)] = True
        raw = next((item.data for item in payload.files if item.path == 'mask-skill.json'), None)
    else:
        artifact, target = store.location(home, row['payload_digest'], row['id'])
        if c.kind(artifact) != 'missing':
            store.verify(home, row)
            if verified is not None:
                verified[r.coordinate(row)] = True
            raw = regular_bytes(target / 'mask-skill.json', r.METADATA_BYTES) if c.kind(target / 'mask-skill.json') != 'missing' else None
        elif row['metadata_digest'] == c.digest(b'null'):
            raw = None
        elif config is not None:
            import mask_sources as sources
            entry = sources.selected(config, row['source'])
            payload = r.verify_resolution(home, row['source'], entry, row)
            raw = next((item.data for item in payload.files if item.path == 'mask-skill.json'), None)
        else:
            c.fail('metadata.unavailable', 'Applicable metadata requires a verified artifact or exact cached payload.', 4)
    value = r.metadata(raw)
    if c.digest(r.canonical(value, 'metadata')) != row['metadata_digest']:
        c.fail('lock.digest_mismatch', 'Verified metadata differs from its locked digest.', 4)
    return value


def effective_selection(home, declaration, resolved, config, *, root, scope, payload_views=None, policy_value=None, devs=None):
    import mask_selection as selection
    policy_value = selection.read_policy(home)[0] if policy_value is None else selection.policy(policy_value)
    facts = selection.device()
    applicable = set(selection.applicable_coordinates(declaration, facts))
    metadata, verified = {}, {}
    for row in resolved['packages']:
        key = r.coordinate(row)
        if key not in applicable:
            continue
        if (devs or {}).get(key) is not None:
            observation, payload = observe_dev(devs[key], config, with_payload=True)
            raw = next((item.data for item in payload.files if item.path == 'mask-skill.json'), None)
            metadata[key] = r.metadata(raw)
            verified[key] = True
        else:
            metadata[key] = metadata_supported(home, row, (payload_views or {}).get(row['payload_digest']), config=config, verified=verified)
    evaluated = selection.evaluate([dict(origin='local', declaration=declaration, lock=resolved)], metadata,
                              facts=facts, enabled_agents=policy_value['enabled_agents'], scope=scope,
                              root=str(root), identity=c.identity(root), overrides=policy_value['overrides'])
    for outcome in evaluated['outcomes']:
        outcome['target_verified'] = verified.get(outcome['coordinate'], False)
    return evaluated


def expected_links(home, declaration, resolved, config, payload_views=None, *, root=None, scope='project', policy_value=None, devs=None, outcomes=None):
    import mask_store as store
    import mask_fs as fs
    r.approved(declaration, config)
    evaluated = effective_selection(home, declaration, resolved, config, root=root or home, scope=scope,
                                    payload_views=payload_views, policy_value=policy_value, devs=devs)
    if outcomes is not None:
        outcomes.extend(evaluated['outcomes'])
    import mask_selection as selection
    selection.require_compatible(evaluated)
    expected = {}
    for deployment in evaluated['deployable']:
        row, agent = deployment['resolution'], deployment['agent']
        relative = adapters.relative(agent, scope, row['id'])
        if relative in expected and expected[relative]['resolution'] != row:
            c.fail('target.collision', 'Different coordinates share one agent invocation path.', 4, path=relative)
        expected[relative] = dict(skill=row['id'], target=agent, resolution=row,
                                 link_text=fs.creation_link_text(store.location(home, row['payload_digest'], row['id'])[1]))
    return expected


def file_path(entry, home):
    role, root = entry['role'], Path(entry['root'])
    if role == 'selection_policy' and root == home:
        return home / 'selection-policy.json'
    if role == 'machine_config' and root == home:
        return home / 'config.json'
    if role == 'project_declaration':
        return root / '.mask.json'
    if role == 'project_lock':
        return root / '.mask.lock.json'
    if role == 'user_declaration':
        return home / 'user.json'
    if role == 'user_lock':
        return home / 'user.lock.json'
    c.fail('recovery.conflict', 'Unknown typed consumer file role.', 8)


def verify_artifacts(state, selected, home):
    import mask_store as store
    seen = set()
    for root, record in c.consumer_records(state).items():
        if root not in selected or not is_pinned(record):
            continue
        for link in record['links'].values():
            if 'dev' in link:
                observe_dev(link['dev'], c.config(c.read_json(home / 'config.json')))
                continue
            row = link['resolution']
            key = (row['payload_digest'], row['id'], row['metadata_digest'], row.get('provenance_digest'))
            if key not in seen:
                store.verify(home, row)
                seen.add(key)


def validate_files(pending, home):
    seen = set()
    for entry in pending.get('files', []):
        c.fields(entry, ('root', 'role', 'before', 'after'), family='recovery')
        if entry['role'] == 'selection_policy':
            change = pending.get('selection_change', {})
            if entry != dict(root=str(home), role='selection_policy', before=change.get('policy_before'), after=change.get('policy_after')):
                c.fail('recovery.conflict', 'Selection policy role differs from its explicit transition.', 8)
            continue
        if entry['role'] == 'machine_config':
            migration = pending.get('migration', {})
            if entry != dict(root=str(home), role='machine_config', before=migration.get('config_before'), after=migration.get('config_after')):
                c.fail('recovery.conflict', 'Machine configuration role differs from explicit migration.', 8)
            continue
        key = (entry['root'], entry['role'])
        if key in seen or entry['root'] not in pending['selected']:
            c.fail('recovery.conflict', 'Duplicate or unselected typed file.', 8)
        seen.add(key)
        state = pending['before_state'] if entry['root'] in c.consumer_records(pending['before_state']) else pending['after_state']
        scope = c.consumer_scope(state, entry['root'])
        if entry['role'] not in (scope + '_declaration', scope + '_lock'):
            c.fail('recovery.conflict', 'Typed role does not match consumer scope.', 8)
        file_path(entry, home)
        for side in ('before', 'after'):
            text = entry[side]
            record = c.consumer_records(pending[side + '_state']).get(entry['root'])
            if side == 'before':
                observed = next(item for item in pending['pinned']['workspaces'] if item['root'] == entry['root'])
                field = 'lock' if entry['role'].endswith('_lock') else 'manifest'
                if text != observed.get(field):
                    c.fail('recovery.conflict', 'Typed before bytes differ from the live workspace observation.', 8)
            if text is None:
                if side == 'after' and record is not None:
                    c.fail('recovery.conflict', 'Active consumer cannot lose a required control.', 8)
                continue
            if not isinstance(text, str):
                c.fail('recovery.conflict', 'Typed control needs exact UTF-8 text or absence.', 8)
            value = r.parse(text, 'lock' if entry['role'].endswith('_lock') else 'manifest')
            parsed = r.lock(value) if entry['role'].endswith('_lock') else c.selection_manifest(value)
            if side == 'before' and entry['role'].endswith('_lock'):
                declaration = c.selection_manifest(r.parse(observed['manifest'], 'manifest'))
                validate_live_lock(parsed, declaration, pending)
            if side == 'after' and record is not None:
                expected = record.get('last_lock') if entry['role'].endswith('_lock') else record['last_manifest']
                if parsed != expected:
                    c.fail('recovery.conflict', 'Typed control bytes disagree with recorded state.', 8)
    for observed in pending['pinned']['workspaces']:
        root = observed['root']
        record = c.consumer_records(pending['after_state']).get(root)
        if not is_pinned(record):
            continue
        if pending['operation'] == 'ensure.deactivate' and observed['manifest'] is None:
            old = c.consumer_records(pending['before_state']).get(root)
            if record['links'] or not is_pinned(old) or any(record[name] != old[name] for name in ('last_manifest', 'last_lock')):
                c.fail('recovery.conflict', 'Inactive pinned ownership must retain its cached controls without active links.', 8)
            continue
        scope = c.consumer_scope(pending['after_state'], root)
        for role, field, expected in (('declaration', 'manifest', record['last_manifest']), ('lock', 'lock', record['last_lock'])):
            transition = next((entry for entry in pending['files'] if entry['root'] == root and entry['role'] == scope + '_' + role), None)
            text = transition['after'] if transition is not None else observed.get(field)
            if not isinstance(text, str):
                c.fail('recovery.conflict', 'Pinned after state requires complete declaration and lock controls.', 8)
            value = r.parse(text, field)
            actual = r.lock(value, record['last_manifest']) if role == 'lock' else c.selection_manifest(value)
            if actual != expected:
                c.fail('recovery.conflict', 'Effective after controls disagree with pinned ownership state.', 8)


def observe(roots, state, home, *, user_root=None):
    import mask_ensure as readiness
    return [readiness.workspace_observation(root, scope='user' if root == user_root else c.consumer_scope(state, root), home=home) for root in roots]


def check_observations(pending, home):
    import mask_ensure as readiness
    observations = pending['pinned']['workspaces']
    if 'home_identity' in pending['pinned'] and c.identity(home) != pending['pinned']['home_identity']:
        c.fail('recovery.conflict', 'Pinned machine home identity changed.', 8)
    policy_before = pending['pinned'].get('selection_policy_text')
    import mask_selection as selection
    try:
        current_policy = selection.read_policy(home)[1]
    except c.MaskError as error:
        c.fail('recovery.conflict', 'Local selection policy is no longer readable.', 8, cause=error.as_dict())
    if current_policy not in (policy_before, pending.get('selection_change', {}).get('policy_after', policy_before)):
        c.fail('recovery.conflict', 'Local selection policy changed.', 8)
    if c.read_text(home / 'config.json', missing=True) not in (pending['pinned']['config_text'], pending.get('migration', {}).get('config_after', pending['pinned']['config_text'])) or c.read_text(home / 'integration.json', missing=True) not in (pending['pinned']['policy_text'], pending.get('controls', {}).get('policy_after', pending['pinned']['policy_text'])):
        c.fail('recovery.conflict', 'Pinned configuration or authority changed.', 8)
    for expected in observations:
        root = Path(expected['root'])
        if not root.is_dir() or root.resolve() != root:
            c.fail('recovery.conflict', 'Pinned consumer root changed.', 8)
        actual = readiness.workspace_observation(root, scope=expected.get('scope', 'project'), home=home)
        for entry in pending.get('files', []):
            if entry['root'] == str(root) and entry['role'] not in ('machine_config', 'selection_policy'):
                field = 'lock' if entry['role'].endswith('_lock') else 'manifest'
                if actual.get(field) not in (entry['before'], entry['after']):
                    c.fail('recovery.conflict', 'Typed consumer control changed.', 8)
                if field in expected:
                    actual[field] = expected[field]
                else:
                    actual.pop(field, None)
        if actual != expected:
            c.fail('recovery.conflict', 'Pinned workspace, index or branch changed.', 8)


def validate_observations(pending, home):
    import mask_ensure as readiness
    value = pending['pinned']
    c.fields(value, ('workspaces', 'config_text', 'policy_text'), ('selection_policy_text', 'home_identity'), family='recovery')
    if not isinstance(value['workspaces'], list) or sorted(item.get('root', '') for item in value['workspaces'] if isinstance(item, dict)) != sorted(pending['selected']):
        c.fail('recovery.conflict', 'Pinned observations must cover selected consumers exactly.', 8)
    expected_config = pending.get('migration', {}).get('config_before', c.text_json(pending['config']))
    if not isinstance(value['config_text'], str) or c.config(c.parse_json(value['config_text'])) != c.config(c.parse_json(expected_config)):
        c.fail('recovery.conflict', 'Pinned config observation differs from intent.', 8)
    if value.get('selection_policy_text') is not None:
        import mask_selection as selection
        selection.policy(c.parse_json(value['selection_policy_text'], 'selection_policy'))
    if value['policy_text'] is not None:
        readiness.validate_policy(c.parse_json(value['policy_text'], 'integration'))
    for item in value['workspaces']:
        c.fields(item, ('root', 'identity', 'head', 'git_dir', 'git_identity', 'index', 'unsafe', 'manifest'), ('scope', 'lock'), 'recovery')
        state = pending['before_state'] if item['root'] in c.consumer_records(pending['before_state']) else pending['after_state']
        if item.get('scope', 'project') != c.consumer_scope(state, item['root']) or item['identity'] != c.consumer_records(state)[item['root']]['root_identity']:
            c.fail('recovery.conflict', 'Pinned observation ownership differs.', 8)
    try:
        for side in ('before', 'after'):
            for root, record in c.consumer_records(pending[side + '_state']).items():
                if root in pending['selected'] and is_pinned(record):
                    r.approved(record['last_manifest'], pending['config'])
        for item in value['workspaces']:
            if item['manifest'] is None:
                if pending['operation'] != 'ensure.deactivate':
                    c.fail('recovery.conflict', 'Only proven inactive readiness can observe an absent declaration.', 8)
                continue
            declaration = c.selection_manifest(r.parse(item['manifest'], 'manifest'))
            if declaration['schema_version'] == 2:
                if item.get('lock') is None:
                    c.fail('recovery.conflict', 'Pinned workspace observation needs its exact lock.', 8)
                validate_live_lock(r.parse(item['lock'], 'lock'), declaration, pending)
                r.approved(declaration, pending['config'])
    except c.MaskError as error:
        c.fail('recovery.conflict', 'Pinned journal controls or source authority are inconsistent.', 8, cause=error.as_dict())
    validate_files(pending, home)


def selected_consumers(args, state, home):
    command = args.command
    if command.startswith('user.') or getattr(args, 'user', False):
        record = state.get('user')
        root = Path(record['root']) if record else Path(getattr(args, 'user_home', Path.home())).expanduser().resolve()
        return [(root, 'user')]
    if getattr(args, 'all', False) or command in ('update', 'inventory', 'skill.where-used') or command == 'doctor' and not getattr(args, 'project', None):
        return [(Path(root), c.consumer_scope(state, root)) for root in c.consumer_records(state)]
    requested = getattr(args, 'project', getattr(args, 'path', None))
    result = []
    try:
        result.append((c.project_root(requested), 'project'))
    except c.MaskError as error:
        if command != 'ensure' or error.code not in ('manifest.missing', 'project.not_found'):
            raise
    if command == 'ensure' and getattr(args, 'event', 'manual') == 'startup' and state.get('user'):
        result.append((Path(state['user']['root']), 'user'))
    if command == 'ensure' and getattr(args, 'event', '').startswith('post-') and requested is None:
        boundary = c.project_root(initializing=True)
        result.extend((Path(root), 'project') for root in state['projects'] if Path(root).is_relative_to(boundary) and (Path(root), 'project') not in result)
    return result


def snapshot(home, consumers):
    import mask_ensure as readiness
    import mask_selection as selection
    controls = {name: c.read_text(home / name, missing=True) for name in ('config.json', 'state.json', 'pending.json', 'integration.json')}
    controls['selection-policy.json'] = selection.read_policy(home)[1]
    return dict(home_identity=c.identity(home), controls=controls,
                workspaces=[readiness.workspace_observation(root, scope=scope, home=home) for root, scope in consumers])


def prepare_dispatch(args, output, home):
    """Prepare outside writer; return a frozen snapshot to recheck after reacquisition."""
    import mask_ensure as readiness
    import mask_store as store
    command = args.command
    if command not in ('apply', 'ensure', 'project.register', 'user.register') or output['dry_run'] or getattr(args, 'check', False):
        return None
    if command.endswith('.register') and not getattr(args, 'apply', False):
        return None
    if c.kind(home / 'pending.json') != 'missing':
        c.fail('recovery.required', 'Recover the pending operation before preparation.', 8)
    state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
    consumers = selected_consumers(args, state, home)
    selected = []
    for root, scope in consumers:
        value = c.read_json(c.declaration_path(root, scope, home), 'manifest', default={})
        if value.get('schema_version') == 2:
            selected.append((root, scope))
    if not selected:
        return None
    before = snapshot(home, consumers)
    config = c.config(c.parse_json(before['controls']['config.json']))
    policy = readiness.policy(home)
    effects = output['data']['preparation'] = []
    for root, scope in selected:
        record = c.consumer_records(state).get(str(root))
        if record is not None and record.get('mode') == 'dev-link':
            c.fail('dev_link.active', 'Return to pins explicitly before ordinary reconciliation.', 4)
        if record is not None and not is_pinned(record):
            c.fail('migration.required', 'Existing legacy ownership requires explicit migration.', 4)
        if command == 'apply' and record is None:
            c.fail(scope + '.not_registered', 'Register this consumer explicitly before apply.', 4)
        # Same rule as readiness itself: events need approval, while manual readiness reaches its one-time consent.
        # An unapproved root still has no locked-fetch grant, so preparation can only use the local cache.
        if command == 'ensure' and scope == 'project' and not readiness.authorized(root, policy) and not getattr(args, 'repair', False) and getattr(args, 'event', 'manual') != 'manual':
            c.fail('integration.approval_required', 'Approve the physical project before readiness.', 4)
        declaration, resolved = r.read_exact_lock(root, scope, home, config, verify=False)
        simple_targets(declaration)
        allowed = policy['approvals'].get(str(root), {}).get('allow_locked_fetch', []) if command == 'ensure' and scope == 'project' and not getattr(args, 'offline', False) else []
        if command == 'ensure' and getattr(args, 'repair', False) and not getattr(args, 'offline', False):
            allowed = {row['source'] for row in resolved['packages']}
        import mask_selection as selection
        applicable = set(selection.applicable_coordinates(declaration))
        for row in resolved['packages']:
            if r.coordinate(row) not in applicable:
                continue
            item = dict(root=str(root), scope=scope, skill=r.coordinate(row), effects={})
            effects.append(item)
            store.ensure(home, declaration, resolved, config, offline=row['source'] not in allowed, coordinates=[r.coordinate(row)], effects=item['effects'])
        evaluated = effective_selection(home, declaration, resolved, config, root=root, scope=scope)
        selection.require_compatible(evaluated)
    return dict(before=before, consumers=consumers, effects=effects)


def recheck_preparation(preparation, home):
    if preparation is not None and snapshot(home, preparation['consumers']) != preparation['before']:
        c.fail('plan.stale', 'Consumer, generation, root, branch or authority changed during unlocked preparation.', 4)


def verify_transition(pending, home, entry=None):
    """Deduplicate a complete preflight, or verify only one link's old/new bytes."""
    import mask_store as store
    seen = set()
    try:
        for side in ('before', 'after'):
            records = c.consumer_records(pending[side + '_state'])
            roots = [entry['root']] if entry is not None else pending['selected']
            for root in roots:
                record = records.get(root)
                if not is_pinned(record):
                    continue
                links = [record['links'].get(entry['relative'])] if entry is not None else record['links'].values()
                for link in links:
                    if link is None or 'dev' in link:
                        continue
                    row = link['resolution']
                    key = (row['payload_digest'], row['id'], row['metadata_digest'], row.get('provenance_digest'))
                    if key not in seen:
                        store.verify(home, row)
                        seen.add(key)
    except c.MaskError as error:
        c.fail('recovery.conflict', 'A retained old/new artifact failed integrity verification; pending effects remain recoverable after explicit repair.', 8, cause=error.as_dict())


def merge_preparation(output, *, completed):
    """Retained preparation effects survive every consumer failure boundary."""
    effects = output.get('data', {}).get('preparation', [])
    changed = False
    network = False
    for observation in effects:
        item = observation['effects']
        network |= item.get('network_attempted', False)
        changed |= any(row.get('created') or row.get('retained_directories') for row in item.get('artifacts', []))
        changed |= any(row.get('cache_created') or row.get('acquired') or row.get('retained_objects_possible') for row in item.get('acquisitions', []))
    if effects:
        output['data']['network'] = 'locked_fetch' if network else output['data'].get('network', 'none')
    if changed:
        output['changed'] = True
        output['would_change'] = True
        if output['transaction'] in ('not_needed', 'not_started'):
            output['transaction'] = 'committed' if completed else 'partial'


def authoring_snapshot(config):
    """Exact clean legacy HEAD observation; reading never fetches or checks out."""
    import mask_sources as sources
    root = Path(config['source']['root'])
    c.parents_safe(Path(root.anchor), root)
    c.checkout(root)
    head = c.git(root, 'rev-parse', '--verify', 'HEAD^{commit}', optional=True)
    if head is None:
        c.fail('migration.unborn', 'Commit the preserved authoring work before pin migration.', 4)
    if c.git(root, 'config', '--bool', '--get', 'core.sparseCheckout', optional=True) == 'true':
        c.fail('source.dirty', 'Sparse authoring checkouts cannot establish a clean migration baseline.', 4)
    flags = c.git(root, 'ls-files', '-v', '-z', binary=True).split(b'\0')
    if any(item and (item[: 1] == b'S' or item[: 1].islower()) for item in flags):
        c.fail('source.dirty', 'Clear skip-worktree/assume-unchanged flags explicitly before migration.', 4)
    if c.git(root, 'status', '--porcelain=v1', '--untracked-files=all'):
        c.fail('source.dirty', 'Migration requires a clean committed authoring checkout; preserve or commit local edits explicitly.', 4)
    branch = c.git(root, 'symbolic-ref', '--short', 'HEAD', optional=True)
    if branch != config['source']['branch']:
        c.fail('source.identity_mismatch', 'Migration requires the configured authoring branch.', 4)
    name = config['legacy_source']
    entry = sources.selected(config, name)
    transport = c.git(root, 'remote', 'get-url', config['source']['remote'], optional=True) or str(root)
    sources.endpoint(root, transport, entry['repository'])
    for marker in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply'):
        path = Path(c.git(root, 'rev-parse', '--path-format=absolute', '--git-path', marker))
        if c.kind(path) != 'missing':
            c.fail('source.dirty', 'An unfinished authoring Git operation blocks migration.', 4)
    return dict(root=str(root), identity=c.identity(root), head=head, branch=branch,
                index = c.digest(c.git(root, 'ls-files', '--stage', '-z', binary=True)),
                repository = entry['repository'], object_format = c.git(root, 'rev-parse', '--show-object-format'))


def migrated_selection(legacy, config):
    import mask_sources as sources
    legacy = c.manifest(legacy)
    name = config['legacy_source']
    entry = sources.selected(config, name)
    return r.selection(dict(schema_version=2, sources={name:dict(repository=entry['repository'], packages=entry['packages'], ref='refs/heads/' + config['source']['branch'])},
                            default_agents = legacy.get('targets', config['default_targets']),
                            skills = [dict(source=name, id=identifier) for identifier in legacy['skills']]))


def validate_migration(pending, home):
    import mask_sources as sources
    value = pending.get('migration')
    c.fields(value, ('config_before', 'config_after', 'source'), family='recovery')
    if pending['operation'] != 'migrate' or 'pinned' not in pending or pending['schema_version'] != 3:
        c.fail('recovery.conflict', 'Migration requires its explicit typed pinned journal.', 8)
    if value['config_before'] != pending['pinned']['config_text']:
        c.fail('recovery.conflict', 'Migration before config must preserve its exact observed bytes.', 8)
    before, after = c.config(c.parse_json(value['config_before'])), c.config(c.parse_json(value['config_after']))
    name = after.get('legacy_source')
    if after != sources.migrated_config(before, home, name) or pending['config'] != after:
        c.fail('recovery.conflict', 'Migration config changes exceed the legacy source binding.', 8)
    config_entries = [entry for entry in pending['files'] if entry.get('role') == 'machine_config']
    expected = [dict(root=str(home), role='machine_config', before=value['config_before'], after=value['config_after'])] if value['config_before'] != value['config_after'] else []
    if config_entries != expected or c.read_text(home / 'config.json') not in (value['config_before'], value['config_after']):
        c.fail('recovery.conflict', 'Migration config bytes or typed coverage changed.', 8)
    c.fields(value['source'], ('root', 'identity', 'head', 'branch', 'index', 'repository', 'object_format'), family='recovery')
    if value['source']['root'] != after['source']['root'] or value['source']['repository'] != after['sources'][name]['repository']:
        c.fail('recovery.conflict', 'Migration source observation differs from approval.', 8)
    for root in pending['selected']:
        old = c.consumer_records(pending['before_state']).get(root)
        new = c.consumer_records(pending['after_state']).get(root)
        if old is None or not is_pinned(new):
            c.fail('recovery.conflict', 'Migration needs registered before and pinned after ownership.', 8)
        if not is_pinned(old):
            observed = next(item for item in pending['pinned']['workspaces'] if item['root'] == root)
            if new['last_manifest'] != migrated_selection(c.parse_json(observed['manifest']), after):
                c.fail('recovery.conflict', 'Migrated selection differs from explicit legacy requirements/targets.', 8)
            if any(row['commit'] != value['source']['head'] for row in new['last_lock']['packages']):
                c.fail('recovery.conflict', 'Migrated locks must name the observed authoring HEAD.', 8)


def check_migration(pending, home):
    try:
        if authoring_snapshot(pending['config']) != pending['migration']['source']:
            c.fail('recovery.conflict', 'Authoring source changed during migration.', 8)
    except c.MaskError as error:
        c.fail('recovery.conflict', 'Migration authoring baseline changed; preserve work and inspect recovery.', 8, cause=error.as_dict())


def transition_dispatch(args, output, home):
    """Resolve/prepare outside the writer, then activate one frozen ordinary plan."""
    import mask
    import mask_fs as fs
    import mask_packages as packages
    import mask_sources as sources
    import mask_store as store
    if c.kind(home / 'pending.json') != 'missing':
        c.fail('recovery.required', 'Recover the pending operation before resolving a transition.', 8)
    state = c.state(c.read_json(home / 'state.json', default=c.empty_state()))
    config_before = c.read_text(home / 'config.json')
    original = c.config(c.parse_json(config_before))
    roots = mask.selected_roots(args, state, all_default=args.command == 'update')
    records = c.consumer_records(state)
    if any(str(root) not in records for root in roots):
        c.fail('migration.registration_required', 'Register selected consumers before changing deployment mode.', 4)
    if args.command == 'update' and any(not is_pinned(records[str(root)]) for root in roots):
        if getattr(args, 'skill', None):
            c.fail('migration.required', 'Per-binding updates require pinned consumers; migrate explicitly first.', 4)
        return False  # The legacy shared-source operation discloses its full impact itself.
    if args.command == 'update' and not roots:
        if getattr(args, 'skill', ()):
            c.fail('invocation.invalid', '--skill requires coordinates present in the selected consumer scopes.', 2)
        return False
    if not roots:
        c.fail('migration.no_selection', 'No registered consumer was selected for migration.', 4)
    migration = args.command == 'migrate'
    if migration and not getattr(args, 'to_pinned', False):
        c.fail('invocation.invalid', 'Migration requires explicit --to-pinned.', 2)
    config = sources.migrated_config(original, home, original.get('legacy_source', 'legacy')) if migration else original
    consumers = [(root, c.consumer_scope(state, root)) for root in roots]
    observed_consumers = consumers
    before = snapshot(home, observed_consumers)
    requested = getattr(args, 'skill', ()) if not migration else ()
    scoped_skills = {}
    if requested:
        available = set()
        for root, scope in consumers:
            declaration = r.selection(c.read_json(c.declaration_path(root, scope, home), 'manifest'))
            bindings = {r.coordinate(binding) for binding in declaration['skills']}
            available.update(bindings)
            scoped_skills[str(root)] = sorted(set(requested) & bindings)
        if len(set(requested)) != len(requested) or set(requested) - available:
            c.fail('invocation.invalid', '--skill requires unique coordinates present in the selected consumer scopes.', 2)
        consumers = [(root, scope) for root, scope in consumers if scoped_skills[str(root)]]
        roots = [root for root, scope in consumers]
    if any(records[str(root)].get('mode') == 'dev-link' for root in roots):
        c.fail('dev_link.active', 'Return to pins explicitly before migration/update.', 4)
    source = authoring_snapshot(config) if migration else None
    proposals, locks, payloads = {}, {}, []
    payload_views = {}
    for root, scope in consumers:
        current = c.selection_manifest(c.read_json(c.declaration_path(root, scope, home), 'manifest'))
        if migration and not is_pinned(records[str(root)]):
            declaration = migrated_selection(current, config)
            rows = []
            for binding in declaration['skills']:
                found = [item for item in sources.discover(Path(source['root']), binding['source'], config['sources'][binding['source']], source['head'], identifier=binding['id']) if item['id'] == binding['id']]
                if len(found) != 1:
                    c.fail('skill.unknown', 'Migration needs one exact raw package at clean HEAD.', 4)
                item = found[0]
                payload = packages.validate(Path(source['root']), source['head'], item['path'], binding['id'])
                row = dict(source=binding['source'], id=binding['id'], repository=item['repository'], path=item['path'], commit=source['head'], git_object_format=source['object_format'], selector=dict(ref=declaration['sources'][binding['source']]['ref']), **r.payload_digests(payload))
                rows.append(row)
                payloads.append((row, payload))
                payload_views[row['payload_digest']] = payload
            proposals[str(root)] = declaration
            locks[str(root)] = r.lock(dict(schema_version=1, resolver='mask-lock-v1', selection_digest=r.selection_digest(declaration), packages=rows), declaration)
        else:
            if migration:
                declaration, previous = r.read_exact_lock(root, scope, home, config, verify=False)
            else:
                declaration = r.selection(current)
                previous = r.lock(r.read_model(r.lock_path(root, scope, home), 'lock')[0])
                r.approved(declaration, config)
            locks[str(root)] = previous if migration else r.resolve_candidate(declaration, config, home, previous, refresh=True, skills=scoped_skills.get(str(root), ()), allow_ref_rebind=getattr(args, 'allow_ref_rebind', False), payload_views=payload_views)
    planned = fs.plan(config, state, roots, home=home, proposals=proposals, lock_proposals=locks, operation=args.command, allow_migration=migration, payload_views=payload_views)
    if migration:
        config_after = config_before if config == original else c.text_json(config)
        planned['intent']['migration'] = dict(config_before=config_before, config_after=config_after, source=source)
        if config_after != config_before:
            planned['intent']['files'].append(dict(root=str(home), role='machine_config', before=config_before, after=config_after))
            planned['actions'].append(dict(kind='config.migrate', status='planned'))
            planned['would_change'] = True
        planned['plan_hash'] = c.digest(dict(plan=planned['plan_hash'], migration=planned['intent']['migration']))
    fs.public_plan(planned, output)
    fs.ensure_applicable(planned, getattr(args, 'expect_plan_hash', None))
    if output['dry_run']:
        return True
    effects = output['data']['preparation'] = []
    for row, payload in payloads:
        observation = dict(skill=r.coordinate(row), effects=dict(artifacts=[{}]))
        effects.append(observation)
        store.materialize(home, row, payload, effects=observation['effects']['artifacts'][0])
    if not migration:
        for root, scope in consumers:
            observation = dict(root=str(root), effects={})
            effects.append(observation)
            import mask_selection as selection
            declaration = c.selection_manifest(c.read_json(c.declaration_path(root, scope, home)))
            store.ensure(home, declaration, locks[str(root)], config, offline=True, coordinates=selection.applicable_coordinates(declaration), effects=observation['effects'])
    with c.writer_lock(home):
        if snapshot(home, observed_consumers) != before or migration and authoring_snapshot(config) != source:
            c.fail('plan.stale', 'Source, consumer controls, generation or identity changed during preparation.', 4)
        fs.execute(planned, home, output)
    if args.command == 'update':
        import mask_ensure as readiness
        readiness.final_status(output)
    return True


def validate_live_lock(value, declaration, pending):
    """Only explicit update can repair a stale, separately approved disk lock."""
    import mask_sources as sources
    if pending['operation'] != 'update':
        return r.lock(value, declaration)
    locked = r.lock(value)
    for row in locked['packages']:
        entry = sources.selected(pending['config'], row['source'])
        if row['repository'] != entry['repository']:
            c.fail('recovery.conflict', 'Before disk lock contains an unapproved source identity.', 8)
    return locked


def validate_dev(value, config=None):
    import mask_sources as sources
    c.fields(value, ('source', 'id', 'root', 'identity', 'path'), family='state')
    c.skill_id(value['source'])
    c.skill_id(value['id'])
    r.path(value['path'])
    c.fields(value['identity'], ('device', 'inode'), family='state')
    if any(type(number) is not int for number in value['identity'].values()) or not isinstance(value['root'], str) or not Path(value['root']).is_absolute() or str(Path(value['root'])) != value['root']:
        c.fail('state.invalid', 'Development source requires canonical physical ownership.')
    if config is not None:
        entry = sources.selected(config, value['source'])
        if entry['authoring'] != value['root']:
            c.fail('source.identity_mismatch', 'Development source is not the approved authoring root.', 4)
    return value


def observe_dev(value, config, *, with_payload=False):
    import mask_provenance as provenance
    import mask_packages as packages
    validate_dev(value, config)
    root, target, observed = provenance.destination(config, value['source'], value['id'])
    if observed['root_identity'] != value['identity'] or observed['path'] != value['path']:
        c.fail('source.identity_mismatch', 'Development source identity or package path changed.', 4)
    # Preserve tracked logical executable modes on Windows; new files default regular.
    modes = {item.path: item.mode for item in packages.validate(root, observed['head'], value['path'], value['id']).files}
    payload = provenance.working_payload(target, value['id'], commit=observed['head'], path=value['path'], modes=modes)
    result = dict(binding=value, observation=observed, payload_digest=payload.digest)
    return (result, payload) if with_payload else result


def development_observations(before, after, selected, config):
    values = {}
    for state in (before, after):
        for root, record in c.consumer_records(state).items():
            if root in selected:
                for value in record.get('dev_links', {}).values():
                    values[c.digest(value)] = value
    return [observe_dev(values[key], config) for key in sorted(values)]


def validate_development(pending, home):
    actual = pending.get('development')
    if not isinstance(actual, list) or len(actual) > 4096 or 'pinned' not in pending:
        c.fail('recovery.conflict', 'Development transitions require bounded pinned observations.', 8)
    wanted = {}
    for state in (pending['before_state'], pending['after_state']):
        for root, record in c.consumer_records(state).items():
            if root in pending['selected']:
                for value in record.get('dev_links', {}).values():
                    validate_dev(value, pending['config'])
                    wanted[c.digest(value)] = value
    seen = {}
    for item in actual:
        c.fields(item, ('binding', 'observation', 'payload_digest'), family='recovery')
        validate_dev(item['binding'], pending['config'])
        seen[c.digest(item['binding'])] = item['binding']
    if seen != wanted or len(seen) != len(actual):
        c.fail('recovery.conflict', 'Development observations must cover exact old/new authoring identities.', 8)
    for root in pending['selected']:
        before = c.consumer_records(pending['before_state']).get(root, {})
        after = c.consumer_records(pending['after_state']).get(root, {})
        if before.get('dev_links', {}) != after.get('dev_links', {}) and pending['operation'] not in ('source.dev-link', 'project.unregister', 'user.unregister'):
            c.fail('recovery.conflict', 'Only explicit development/retirement operations may change live overrides.', 8)


def check_development(pending):
    try:
        for item in pending['development']:
            if observe_dev(item['binding'], pending['config']) != item:
                c.fail('recovery.conflict', 'Development source changed since the frozen operation.', 8)
    except c.MaskError as error:
        c.fail('recovery.conflict', 'Development authoring input changed; inspect pending recovery.', 8, cause=error.as_dict())


def dev_dispatch(args, output, home):
    import mask
    import mask_fs as fs
    import mask_provenance as provenance
    import mask_store as store
    if c.kind(home / 'pending.json') != 'missing':
        c.fail('recovery.required', 'Recover pending effects before development changes.', 8)
    if '/' not in args.id or not any(getattr(args, key, None) for key in ('project', 'user')):
        c.fail('invocation.invalid', 'Development links require SOURCE/ID and an explicit project/user scope.', 2)
    if not getattr(args, 'authoring_root', None) and not getattr(args, 'to_pinned', False):
        c.fail('invocation.invalid', 'Choose --authoring-root or explicit --to-pinned.', 2)
    config = c.config(c.read_json(home / 'config.json'))
    state = c.state(c.read_json(home / 'state.json'))
    root = mask.selected_roots(args, state)[0]
    scope = c.consumer_scope(state, root)
    record = c.consumer_records(state).get(str(root))
    if not is_pinned(record):
        c.fail('migration.required', 'Migrate the selected legacy consumer before adding a scope-local development exception.', 4)
    declaration, locked = r.read_exact_lock(root, scope, home, config, verify=False)
    if args.id not in {r.coordinate(row) for row in locked['packages']}:
        c.fail('skill.unknown', 'Development binding is outside the selected lock.', 4)
    before = snapshot(home, [(root, scope)])
    devs = copy.deepcopy(record.get('dev_links', {}))
    if getattr(args, 'to_pinned', False):
        devs.pop(args.id, None)
    else:
        name, identifier = args.id.split('/', 1)
        authoring, target, observation = provenance.destination(config, name, identifier)
        if Path(args.authoring_root).expanduser().resolve() != authoring:
            c.fail('source.identity_mismatch', 'Explicit development root must match approved authoring identity.', 4)
        devs[args.id] = dict(source=name, id=identifier, root=str(authoring), identity=c.identity(authoring), path=observation['path'])
    planned = fs.plan(config, state, [root], home=home, operation='source.dev-link', dev_proposals={str(root): devs})
    fs.public_plan(planned, output)
    fs.ensure_applicable(planned, getattr(args, 'expect_plan_hash', None))
    output['data'].update(mode='dev-link' if devs else 'pinned', reproducible=not bool(devs), fleet_eligible=not bool(devs), writeback=False)
    if output['dry_run']:
        return
    if not devs:
        effects = output['data']['preparation'] = [dict(root=str(root), effects={})]
        store.ensure(home, declaration, locked, config, offline=True, effects=effects[0]['effects'])
    with c.writer_lock(home):
        if snapshot(home, [(root, scope)]) != before:
            c.fail('plan.stale', 'Consumer controls changed during development preparation.', 4)
        fs.execute(planned, home, output)
