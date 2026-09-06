"""Pinned model and orchestration seams for the ordinary MASK engine."""
from __future__ import annotations

import copy
from pathlib import Path

import mask_core as c
import mask_resolve as r


def is_pinned(record):
    return isinstance(record, dict) and record.get('mode') == 'pinned'


def validate_record(record):
    c.fields(record, ('root', 'root_identity', 'last_manifest', 'last_manifest_digest', 'last_source_revision', 'links', 'mode', 'last_lock'), family='state')
    if record['mode'] != 'pinned' or record['last_source_revision'] is not None:
        c.fail('state.invalid', 'Pinned records require exact lock identities, not a shared revision.')
    declaration = r.selection(record['last_manifest'])
    resolved = r.lock(record['last_lock'], declaration)
    if record['last_manifest_digest'] != r.selection_digest(declaration):
        c.fail('state.invalid', 'Pinned cached selection digest differs.')
    rows = {r.coordinate(row): row for row in resolved['packages']}
    if not isinstance(record['links'], dict):
        c.fail('state.invalid', 'Invalid pinned ownership map.')
    for link in record['links'].values():
        c.fields(link, ('skill', 'target', 'link_text', 'resolution'), family='state')
        row = link['resolution']
        if not isinstance(row, dict) or 'source' not in row or 'id' not in row:
            c.fail('state.invalid', 'Pinned link resolution needs a source and ID.')
        c.skill_id(row['source'])
        c.skill_id(row['id'])
        if rows.get(r.coordinate(row)) != row or link['skill'] != row['id']:
            c.fail('state.invalid', 'Pinned link resolution differs from its cached lock.')
    return declaration


def target(link, config, home):
    import mask_store as store
    if 'resolution' in link:
        return store.location(home, link['resolution']['payload_digest'], link['skill'])[1]
    return Path(config['source']['root']) / 'skills' / link['skill']


def simple_targets(declaration):
    declaration = r.selection(declaration)
    if any('when' in binding or 'agents' in binding for binding in declaration['skills']):
        c.fail('targeting.unsupported', 'Per-binding agents/conditions require the targeting implementation.', 4)
    names = [binding['id'] for binding in declaration['skills']]
    if len(set(names)) != len(names):
        c.fail('target.collision', 'Selected sources have the same host invocation name.', 4)
    return sorted(c.ADAPTERS) if declaration['default_agents'] == 'all' else declaration['default_agents']


def metadata_supported(home, row):
    import mask_store as store
    from mask_provenance import regular_bytes
    if row['metadata_digest'] == c.digest(b'null'):
        return
    path = store.verify(home, row)
    value = r.metadata(regular_bytes(path / 'mask-skill.json', r.METADATA_BYTES))
    if any(value.get(field) not in (None, 'generic') for field in ('agents', 'platforms', 'architectures')) or value.get('requirements'):
        c.fail('targeting.unsupported', 'Restrictive package compatibility requires the targeting implementation.', 4)


def expected_links(home, declaration, resolved, config):
    import mask_store as store
    import mask_fs as fs
    agents = simple_targets(declaration)
    r.approved(declaration, config)
    expected = {}
    for row in resolved['packages']:
        root, _ = store.location(home, row['payload_digest'], row['id'])
        if c.kind(root) != 'missing':
            store.verify(home, row)
        metadata_supported(home, row)
        for agent in agents:
            relative = c.ADAPTERS[agent] + '/' + row['id']
            expected[relative] = dict(skill=row['id'], target=agent, resolution=row,
                                     link_text=fs.creation_link_text(store.location(home, row['payload_digest'], row['id'])[1]))
    return expected


def file_path(entry, home):
    role, root = entry['role'], Path(entry['root'])
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
            row = link['resolution']
            key = (row['payload_digest'], row['id'], row['metadata_digest'], row.get('provenance_digest'))
            if key not in seen:
                store.verify(home, row)
                seen.add(key)


def validate_files(pending, home):
    seen = set()
    for entry in pending.get('files', []):
        c.fields(entry, ('root', 'role', 'before', 'after'), family='recovery')
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
                r.lock(parsed, declaration)
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
    if c.read_text(home / 'config.json', missing=True) != pending['pinned']['config_text'] or c.read_text(home / 'integration.json', missing=True) not in (pending['pinned']['policy_text'], pending.get('controls', {}).get('policy_after', pending['pinned']['policy_text'])):
        c.fail('recovery.conflict', 'Pinned configuration or authority changed.', 8)
    for expected in observations:
        root = Path(expected['root'])
        if not root.is_dir() or root.resolve() != root:
            c.fail('recovery.conflict', 'Pinned consumer root changed.', 8)
        actual = readiness.workspace_observation(root, scope=expected.get('scope', 'project'), home=home)
        for entry in pending.get('files', []):
            if entry['root'] == str(root):
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
    c.fields(value, ('workspaces', 'config_text', 'policy_text'), family='recovery')
    if not isinstance(value['workspaces'], list) or sorted(item.get('root', '') for item in value['workspaces'] if isinstance(item, dict)) != sorted(pending['selected']):
        c.fail('recovery.conflict', 'Pinned observations must cover selected consumers exactly.', 8)
    if not isinstance(value['config_text'], str) or c.config(c.parse_json(value['config_text'])) != pending['config']:
        c.fail('recovery.conflict', 'Pinned config observation differs from intent.', 8)
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
                r.lock(r.parse(item['lock'], 'lock'), declaration)
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
    return dict(home_identity=c.identity(home), controls={name:c.read_text(home / name, missing=True) for name in ('config.json','state.json','pending.json','integration.json')},
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
        if record is not None and not is_pinned(record):
            c.fail('migration.required', 'Existing legacy ownership requires explicit migration.', 4)
        if command == 'apply' and record is None:
            c.fail(scope + '.not_registered', 'Register this consumer explicitly before apply.', 4)
        if command == 'ensure' and scope == 'project' and not readiness.authorized(root, policy):
            c.fail('integration.approval_required', 'Approve the physical project before readiness.', 4)
        declaration, resolved = r.read_exact_lock(root, scope, home, config, verify=False)
        simple_targets(declaration)
        allowed = policy['approvals'].get(str(root), {}).get('allow_locked_fetch', []) if command == 'ensure' and scope == 'project' and not getattr(args, 'offline', False) else []
        for row in resolved['packages']:
            item = dict(root=str(root), scope=scope, skill=r.coordinate(row), effects={})
            effects.append(item)
            store.ensure(home, declaration, resolved, config, offline=row['source'] not in allowed, coordinates=[r.coordinate(row)], effects=item['effects'])
        for row in resolved['packages']:
            metadata_supported(home, row)
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
                    if link is None:
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
        output['data']['network'] = 'locked_fetch' if network else 'none'
    if changed:
        output['changed'] = True
        output['would_change'] = True
        if output['transaction'] in ('not_needed', 'not_started'):
            output['transaction'] = 'committed' if completed else 'partial'
