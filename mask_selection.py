"""Pure binding applicability and local, non-portable selection authority."""
from __future__ import annotations

import copy
import platform
from pathlib import Path

import mask_core as c
import mask_resolve as r
import mask_adapters as adapters

POLICY_BYTES = 1024 * 1024


def device():
    system = {'Darwin': 'macos', 'Windows': 'windows', 'Linux': 'linux'}.get(platform.system(), 'unknown')
    architecture = {'AMD64': 'x86_64', 'amd64': 'x86_64', 'aarch64': 'arm64'}.get(platform.machine(), platform.machine())
    return dict(platform=system, architecture=architecture)


def policy(value=None):
    if value is None:
        return dict(schema_version=1, enabled_agents=sorted(c.ADAPTERS), overrides=[])
    # Override identities are local stat numbers: Windows reports 64-bit volume serials and inodes up to 128 bits.
    r.canonical(value, 'selection_policy', integer_limit=2 ** 128 - 1)
    c.fields(value, ('schema_version', 'enabled_agents', 'overrides'), family='selection_policy')
    enabled = r.strings(value['enabled_agents'], 'selection_policy', choices=set(c.ADAPTERS), empty=True)
    overrides = value['overrides']
    if not isinstance(overrides, list) or len(overrides) > 4096:
        c.fail('selection_policy.invalid', 'Compatibility overrides must be a bounded list.', 4)
    seen = set()
    for item in overrides:
        c.fields(item, ('root', 'identity', 'coordinate', 'reason'), ('agents', 'platforms', 'architectures'), family='selection_policy')
        if not isinstance(item['root'], str) or not Path(item['root']).is_absolute() or str(Path(item['root'])) != item['root'] or '..' in Path(item['root']).parts or len(item['root']) > 32768:
            c.fail('selection_policy.invalid', 'Override requires a canonical physical consumer root.', 4)
        c.fields(item['identity'], ('device', 'inode'), family='selection_policy')
        if any(type(number) is not int or number < 0 for number in item['identity'].values()):
            c.fail('selection_policy.invalid', 'Override root identity is invalid.', 4)
        if not isinstance(item['coordinate'], str) or item['coordinate'].count('/') != 1:
            c.fail('selection_policy.invalid', 'Override requires one SOURCE/ID coordinate.', 4)
        for token in item['coordinate'].split('/'):
            c.skill_id(token)
        key = (item['root'], item['coordinate'])
        if key in seen:
            c.fail('selection_policy.invalid', 'Duplicate scope/coordinate override.', 4)
        seen.add(key)
        if not isinstance(item['reason'], str) or not 1 <= len(item['reason']) <= 4096 or not item['reason'].strip() or any(ord(char) < 32 or ord(char) == 127 for char in item['reason']):
            c.fail('selection_policy.invalid', 'Override needs a bounded nonempty reason.', 4)
        if not any(field in item for field in ('agents', 'platforms', 'architectures')):
            c.fail('selection_policy.invalid', 'Override must name a compatibility dimension.', 4)
        for field in ('agents', 'platforms', 'architectures'):
            if field in item:
                choices = set(c.ADAPTERS) if field == 'agents' else r.PLATFORMS if field == 'platforms' else r.ARCHITECTURES
                if r.strings(item[field], 'selection_policy', choices=choices) != item[field]:
                    c.fail('selection_policy.invalid', 'Override dimension sets must use sorted canonical order.', 4)
    return dict(schema_version=1, enabled_agents=enabled, overrides=copy.deepcopy(overrides))


def read_policy(home):
    from mask_provenance import regular_bytes
    path = home / 'selection-policy.json'
    c.parents_safe(home, path)
    try:
        raw = None if c.kind(path) == 'missing' else regular_bytes(path, POLICY_BYTES).decode('utf-8')
    except UnicodeError:
        c.fail('selection_policy.invalid', 'Local selection policy must be UTF-8.', 4)
    except c.MaskError as error:
        c.fail('selection_policy.invalid', 'Local selection policy requires a bounded regular file.', 4, cause=error.as_dict())
    if raw is not None and len(raw.encode('utf-8')) > POLICY_BYTES:
        c.fail('selection_policy.limit', 'Local selection policy exceeds 1 MiB.', 4)
    return policy(c.parse_json(raw, 'selection_policy') if raw is not None else None), raw


def applies(binding, facts):
    condition = binding.get('when', {})
    return all(facts[singular] in condition.get(plural, [facts[singular]]) for plural, singular in (('platforms', 'platform'), ('architectures', 'architecture')))


def applicable_coordinates(declaration, facts=None):
    facts = facts or device()
    return [r.coordinate(binding) for binding in r.selection(declaration)['skills'] if applies(binding, facts)]


def assertion(metadata):
    if metadata is None:
        return 'unspecified'
    dimensions = [metadata.get(field) for field in ('agents', 'platforms', 'architectures')]
    if any(isinstance(value, list) for value in dimensions):
        return 'specific_asserted'
    return 'generic_asserted' if 'generic' in dimensions else 'unspecified'


def evaluate(contributions, metadata, *, facts, enabled_agents, scope, root, identity, overrides=()):
    """No filesystem, Git, executable detection, hydration, or policy mutation."""
    if scope not in ('project', 'user') or not isinstance(metadata, dict):
        c.fail('selection.invalid', 'Effective selection requires a known scope and verified metadata map.', 4)
    if not isinstance(contributions, list) or len(contributions) > 64:
        c.fail('selection.invalid', 'Expected bounded attributed contributions.', 4)
    overrides = policy(dict(schema_version=1, enabled_agents=list(enabled_agents), overrides=list(overrides)))['overrides']
    c.fields(facts, ('platform', 'architecture'), family='selection')
    if not all(isinstance(value, str) for value in facts.values()):
        c.fail('selection.invalid', 'Device facts require plain platform/architecture names.', 4)
    enabled = set(r.strings(list(enabled_agents), 'selection_policy', choices=set(c.ADAPTERS), empty=True))
    outcomes, deployable = [], []
    binding_count = 0
    for contribution in contributions:
        c.fields(contribution, ('origin', 'declaration', 'lock'), family='selection')
        origin = contribution['origin']
        if not isinstance(origin, str) or not 1 <= len(origin) <= 500:
            c.fail('selection.invalid', 'Contribution needs bounded origin attribution.', 4)
        declaration = r.selection(contribution['declaration'])
        binding_count += len(declaration['skills'])
        if binding_count > r.BINDINGS:
            c.fail('selection.limit', 'Effective contributions exceed the binding limit.', 4)
        locked = r.lock(contribution['lock'], declaration)
        rows = {r.coordinate(row): row for row in locked['packages']}
        for binding in declaration['skills']:
            key = r.coordinate(binding)
            common = dict(coordinate=key, skill=binding['id'], scope=scope, root=str(root), origins=[origin], tested=False,
                          resolutions=[dict(origin=origin, resolution=rows[key])])
            if not applies(binding, facts):
                outcomes.append(dict(common, agent=None, status='not_applicable', reason='when_false', compatibility='not_evaluated'))
                continue
            metadata_key = rows[key]['payload_digest'] if rows[key]['payload_digest'] in metadata else key
            if metadata_key not in metadata:
                c.fail('metadata.unavailable', 'Applicable binding needs verified metadata or explicit absence.', 4, skill=key)
            advertised = metadata[metadata_key]
            if advertised is not None:
                advertised = r.metadata(r.canonical(advertised, 'metadata'))
            common.update(compatibility=assertion(advertised), requirements=(advertised or {}).get('requirements', []))
            advertised = advertised or {}
            requested = binding.get('agents', declaration['default_agents'])
            explicit = requested != 'all'
            agents = requested if explicit else sorted(c.ADAPTERS)
            override = next((item for item in overrides if item['root'] == str(root) and item['identity'] == identity and item['coordinate'] == key), None)
            for agent in agents:
                row = dict(common, agent=agent, status='selected', reason='compatible')
                if agent not in enabled:
                    row.update(status='blocked' if explicit else 'not_applicable', reason='agent_disabled_by_policy')
                    outcomes.append(row)
                    continue
                mismatches = []
                for dimension, chosen in (('agents', agent), ('platforms', facts['platform']), ('architectures', facts['architecture'])):
                    allowed = advertised.get(dimension)
                    if isinstance(allowed, list) and chosen not in allowed:
                        mismatches.append((dimension, chosen))
                unapproved = [(dimension, chosen) for dimension, chosen in mismatches if override is None or chosen not in override.get(dimension, [])]
                if unapproved:
                    implicit_agent_only = not explicit and all(dimension == 'agents' for dimension, chosen in unapproved)
                    row.update(status='excluded_by_metadata' if implicit_agent_only else 'blocked', reason='advertised_' + '_and_'.join(dimension for dimension, chosen in unapproved))
                elif mismatches:
                    row.update(status='overridden', reason=override['reason'], warning='compatibility.local_override')
                if row['status'] in ('selected', 'overridden'):
                    deployable.append(dict(coordinate=key, agent=agent, resolution=rows[key], origins=[origin],
                                           resolutions=[dict(origin=origin, resolution=rows[key])]))
                outcomes.append(row)
    return merge_edges(outcomes, deployable, scope)


def require_compatible(evaluated):
    if evaluated['conflicts']:
        code = 'target.collision' if any(row['kind'] == 'invocation_name' for row in evaluated['conflicts']) else 'selection.conflict'
        c.fail(code, 'Effective contributions require conflicting artifact authority or invocation names.', 4,
               conflicts=evaluated['conflicts'], outcomes=evaluated['outcomes'])
    if evaluated['blocked']:
        c.fail('compatibility.unsupported', 'Explicit agent or device compatibility blocks activation.', 4, outcomes=evaluated['outcomes'])


def merge_edges(outcomes, deployments, scope):
    """Union positive edges; retain exact source facts and refuse competing authority."""
    def attribution(rows):
        unique = {r.canonical(item): item for row in rows for item in row['resolutions']}
        return [unique[key] for key in sorted(unique)]

    by_coordinate = {}
    for row in deployments:
        by_coordinate.setdefault(row['coordinate'], []).append(row)
    conflicts, refused = [], set()
    representatives = {}
    for coordinate, rows in sorted(by_coordinate.items()):
        claims = {tuple(row['resolution'].get(field) for field in ('repository', 'payload_digest', 'metadata_digest', 'provenance_digest')) for row in rows}
        if len(claims) > 1:
            conflicts.append(dict(kind='artifact_authority', coordinate=coordinate, resolutions=attribution(rows)))
            refused.update((coordinate, row['agent']) for row in rows)
        else:
            # Equal artifact/authority has one destination. Preserve every exact
            # resolution and select a canonical representative, never arrival order.
            representatives[coordinate] = min((row['resolution'] for row in rows), key=r.canonical)
    by_edge = {}
    for row in deployments:
        key = (row['coordinate'], row['agent'])
        if key not in refused:
            by_edge.setdefault(key, []).append(row)
    merged = []
    for (coordinate, agent), rows in sorted(by_edge.items()):
        merged.append(dict(coordinate=coordinate, agent=agent, resolution=representatives[coordinate],
                           origins=sorted({origin for row in rows for origin in row['origins']}), resolutions=attribution(rows)))
    by_name = {}
    for row in merged:
        by_name.setdefault((row['agent'], row['resolution']['id']), []).append(row)
    for (agent, name), rows in sorted(by_name.items()):
        if len({row['coordinate'] for row in rows}) > 1:
            conflicts.append(dict(kind='invocation_name', agent=agent, name=name,
                                  relative=adapters.relative(agent, scope, name), candidates=rows))
            refused.update((row['coordinate'], agent) for row in rows)
    for row in outcomes:
        if (row['coordinate'], row['agent']) in refused and row['status'] in ('selected', 'overridden'):
            row.update(status='blocked', reason='selection_conflict')
    grouped = {}
    for row in outcomes:
        key = r.canonical({field: value for field, value in row.items() if field not in ('origins', 'resolutions')})
        grouped.setdefault(key, []).append(row)
    outcomes = [dict(rows[0], origins=sorted({origin for row in rows for origin in row['origins']}), resolutions=attribution(rows))
                for key, rows in sorted(grouped.items())]
    return dict(outcomes=outcomes, deployable=[row for row in merged if (row['coordinate'], row['agent']) not in refused],
                conflicts=conflicts, blocked=bool(conflicts) or any(item['status'] == 'blocked' for item in outcomes))


def parse_policy_text(raw):
    if raw is not None and (not isinstance(raw, str) or len(raw.encode('utf-8')) > POLICY_BYTES):
        c.fail('selection_policy.limit', 'Policy text exceeds its bound.', 4)
    return policy(c.parse_json(raw, 'selection_policy') if raw is not None else None)


def validate_change(pending, home):
    change = pending.get('selection_change')
    c.fields(change, ('policy_before', 'policy_after', 'apply'), ('coordinate',), family='recovery')
    allowed = {'selection-policy.set', 'selection-policy.clear', 'compatibility.override', 'compatibility.clear', 'project.set-agents', 'user.set-agents', 'project.set-targets', 'user.set-targets'}
    if pending['operation'] not in allowed or type(change['apply']) is not bool or 'pinned' not in pending or pending['schema_version'] != 3:
        c.fail('recovery.conflict', 'Selection authority requires its explicit typed transition.', 8)
    if change['policy_before'] != pending['pinned'].get('selection_policy_text'):
        c.fail('recovery.conflict', 'Selection policy before bytes differ from observation.', 8)
    before = parse_policy_text(change['policy_before'])
    after = parse_policy_text(change['policy_after'])
    entries = [entry for entry in pending['files'] if entry.get('role') == 'selection_policy']
    expected = [dict(root=str(home), role='selection_policy', before=change['policy_before'], after=change['policy_after'])] if change['policy_before'] != change['policy_after'] else []
    if entries != expected:
        c.fail('recovery.conflict', 'Typed policy effects do not cover their exact before/after bytes.', 8)
    records = c.consumer_records(pending['before_state'])
    if pending['operation'].startswith('selection-policy.'):
        if before['overrides'] != after['overrides'] or set(pending['selected']) != set(records) or not change['apply']:
            c.fail('recovery.conflict', 'Enabled-agent changes must preserve overrides and include all registered consumers.', 8)
    elif pending['operation'].startswith('compatibility.'):
        if len(pending['selected']) != 1 or before['enabled_agents'] != after['enabled_agents'] or not change['apply']:
            c.fail('recovery.conflict', 'Compatibility authority is restricted to one unchanged enabled-agent policy.', 8)
        root = pending['selected'][0]
        key = change.get('coordinate')
        record = records[root]
        if key not in {r.coordinate(binding) for binding in r.selection(record['last_manifest'])['skills']}:
            c.fail('recovery.conflict', 'Override coordinate is outside registered selection.', 8)
        unchanged = lambda rows: [row for row in rows if (row['root'], row['coordinate']) != (root, key)]
        if unchanged(before['overrides']) != unchanged(after['overrides']):
            c.fail('recovery.conflict', 'Compatibility mutation changes unrelated policy rows.', 8)
        for row in after['overrides']:
            if (row['root'], row['coordinate']) == (root, key) and row['identity'] != record['root_identity']:
                c.fail('recovery.conflict', 'Override must use registered physical scope identity.', 8)
    else:
        if change['policy_before'] != change['policy_after'] or len(pending['selected']) != 1:
            c.fail('recovery.conflict', 'A selection setter cannot change local authority.', 8)
        root = pending['selected'][0]
        observed = next(item for item in pending['pinned']['workspaces'] if item['root'] == root)
        old = r.selection(c.parse_json(observed['manifest']))
        new_record = c.consumer_records(pending['after_state'])[root]
        new = r.selection(new_record['last_manifest'])
        permitted = copy.deepcopy(old)
        if pending['operation'].endswith('set-targets'):
            permitted['default_agents'] = new['default_agents']
        else:
            key = change.get('coordinate')
            old_binding = next((row for row in permitted['skills'] if r.coordinate(row) == key), None)
            new_binding = next((row for row in new['skills'] if r.coordinate(row) == key), None)
            if old_binding is None or new_binding is None:
                c.fail('recovery.conflict', 'Agent setter coordinate is outside the declaration.', 8)
            old_binding.pop('agents', None)
            if 'agents' in new_binding:
                old_binding['agents'] = new_binding['agents']
        if permitted != new:
            c.fail('recovery.conflict', 'Agent setter changes unrelated declaration intent.', 8)
        old_lock = r.lock(c.parse_json(observed['lock']), old)
        if new_record['last_lock']['packages'] != old_lock['packages']:
            c.fail('recovery.conflict', 'Agent setters must preserve exact package resolutions.', 8)
        if not change['apply'] and new_record['links'] != records[root]['links']:
            c.fail('recovery.conflict', 'Declaration-only setter cannot change active link ownership.', 8)

    if change['apply']:
        validate_after_links(pending, home, after)


def validate_after_links(pending, home, after_policy):
    """Saved effects must still be derivable from their exact after authority."""
    import mask_pinned as pinned
    import mask_fs as fs
    config = pending['config']
    records = c.consumer_records(pending['after_state'])
    for key in pending['selected']:
        record = records[key]
        root = Path(key)
        if not pinned.is_pinned(record):
            c.fail('recovery.conflict', 'Legacy live-checkout ownership has no effective selection authority to recover.', 8)
        expected = pinned.expected_links(home, record['last_manifest'], record['last_lock'], config,
                                         root=root, scope=c.consumer_scope(pending['after_state'], root),
                                         policy_value=after_policy, devs=record.get('dev_links', {}))
        for link in expected.values():
            dev = record.get('dev_links', {}).get(r.coordinate(link['resolution']))
            if dev is not None:
                link['dev'] = dev
        if set(expected) != set(record['links']):
            c.fail('recovery.conflict', 'After ownership differs from effective selection authority.', 8)
        for relative, wanted in expected.items():
            actual = record['links'][relative]
            if any(actual.get(field) != wanted.get(field) for field in ('skill', 'target', 'resolution', 'dev')):
                c.fail('recovery.conflict', 'After owned resolution differs from effective selection.', 8)
            if fs.normalized_link(root / relative, actual['link_text']) != pinned.target(wanted, config, home):
                c.fail('recovery.conflict', 'After owned target differs from effective selection.', 8)


def dispatch(args, output, home):
    """Guarded policy/agent mutations using the existing typed transition engine."""
    import mask_fs as fs
    import mask_pinned as pinned
    import mask_store as store
    command = args.command
    setter = command in ('project.set-agents', 'user.set-agents', 'project.set-targets', 'user.set-targets')
    policy_command = command.startswith(('selection-policy.', 'compatibility.'))
    if not setter and not policy_command:
        return False
    state = c.state(c.read_json(home / 'state.json', default=c.empty_state()))
    config = c.config(c.read_json(home / 'config.json'))
    if c.kind(home / 'pending.json') != 'missing':
        c.fail('recovery.required', 'Recover pending effects before changing selection policy.', 8)
    current_policy, policy_before = read_policy(home)
    proposal_policy = copy.deepcopy(current_policy)
    proposals, locks = {}, {}
    coordinate = None
    apply = bool(getattr(args, 'apply', False)) if setter else True
    records = c.consumer_records(state)
    if command.startswith('selection-policy.'):
        roots = [Path(root) for root in sorted(records)]
        if command == 'selection-policy.set':
            proposal_policy['enabled_agents'] = r.strings(getattr(args, 'agent', []), 'selection_policy', choices=set(c.ADAPTERS))
        else:
            proposal_policy['enabled_agents'] = sorted(c.ADAPTERS)
    else:
        scope = 'user' if command.startswith('user.') or getattr(args, 'user', False) else 'project'
        if scope == 'project':
            root = c.project_root(getattr(args, 'project', None))
        else:
            root = Path(state['user']['root']) if state.get('user') else home
        declaration = c.selection_manifest(c.read_json(c.declaration_path(root, scope, home), 'manifest'))
        if setter and declaration['schema_version'] == 1:
            c.migration_required('A v1 declaration must be migrated to a v2 declaration before setting agents or targets.', path=str(c.declaration_path(root, scope, home)))
        record = records.get(str(root))
        if not pinned.is_pinned(record):
            c.fail(scope + '.not_registered', 'Register this v2 consumer explicitly with ' + scope + ' register before setting agents or compatibility policy.', 4)
        c.registered_root(root, record, scope)
        declaration, previous_lock = r.read_exact_lock(root, scope, home, config, verify=False)
        roots = [root]
        if setter:
            proposed = copy.deepcopy(declaration)
            if command.endswith('set-agents'):
                coordinate = args.id
                binding = next((row for row in proposed['skills'] if r.coordinate(row) == coordinate), None)
                if binding is None:
                    c.fail('skill.unknown', 'Agent setter requires one selected SOURCE/ID.', 4)
                if getattr(args, 'inherit', False):
                    binding.pop('agents', None)
                else:
                    binding['agents'] = 'all' if getattr(args, 'all', False) else r.agents(getattr(args, 'agents', []))
            else:
                proposed['default_agents'] = 'all' if getattr(args, 'inherit', False) else r.agents(getattr(args, 'targets', []))
            proposals[str(root)] = r.selection(proposed)
            locks[str(root)] = r.lock(dict(previous_lock, selection_digest=r.selection_digest(proposed)), proposed)
        else:
            coordinate = args.id
            if coordinate not in {r.coordinate(row) for row in declaration['skills']}:
                c.fail('skill.unknown', 'Override requires one selected SOURCE/ID.', 4)
            proposal_policy['overrides'] = [row for row in current_policy['overrides'] if (row['root'], row['coordinate']) != (str(root), coordinate)]
            if command == 'compatibility.override':
                override = dict(root=str(root), identity=c.identity(root), coordinate=coordinate, reason=args.reason)
                if getattr(args, 'agent', None):
                    override['agents'] = r.strings(args.agent, 'selection_policy', choices=set(c.ADAPTERS))
                facts = device()
                if getattr(args, 'platform', False):
                    override['platforms'] = [facts['platform']]
                if getattr(args, 'architecture', False):
                    override['architectures'] = [facts['architecture']]
                old_rows = current_policy['overrides']
                existing = any((row['root'], row['coordinate']) == (str(root), coordinate) for row in old_rows)
                if existing:
                    proposal_policy['overrides'] = [override if (row['root'], row['coordinate']) == (str(root), coordinate) else row for row in old_rows]
                else:
                    proposal_policy['overrides'] = old_rows + [override]
    proposal_policy = policy(proposal_policy)
    policy_after = policy_before if proposal_policy == current_policy else c.text_json(proposal_policy)
    if command == 'selection-policy.clear' and not proposal_policy['overrides']:
        policy_after = None
    parse_policy_text(policy_after)
    consumers = [(root, c.consumer_scope(state, root)) for root in roots]
    before = pinned.snapshot(home, consumers)
    planned = fs.plan(config, state, roots, home=home, proposals=proposals, lock_proposals=locks,
                      operation=command, register_only=not apply, selection_policy=proposal_policy)
    change = dict(policy_before=policy_before, policy_after=policy_after, apply=apply)
    if coordinate is not None:
        change['coordinate'] = coordinate
    planned['intent']['selection_change'] = change
    if policy_after != policy_before:
        planned['intent']['files'].append(dict(root=str(home), role='selection_policy', before=policy_before, after=policy_after))
        planned['actions'].append(dict(kind='selection_policy.write', status='planned', path=str(home / 'selection-policy.json')))
        planned['would_change'] = True
    planned['plan_hash'] = c.digest(dict(plan=planned['plan_hash'], change=change))
    fs.public_plan(planned, output)
    output['data'].update(selection_policy=proposal_policy, affected_scopes=[str(root) for root in roots])
    fs.ensure_applicable(planned, getattr(args, 'expect_plan_hash', None))
    if output['dry_run']:
        return True
    effects = output['data']['preparation'] = []
    if apply:
        for root, scope in consumers:
            record = planned['intent']['after_state']['user'] if scope == 'user' else planned['intent']['after_state']['projects'][str(root)]
            if not pinned.is_pinned(record):
                continue
            coordinates = {r.coordinate(link['resolution']) for link in record['links'].values() if 'dev' not in link}
            observation = dict(root=str(root), effects={})
            effects.append(observation)
            store.ensure(home, record['last_manifest'], record['last_lock'], config, offline=True, coordinates=coordinates, effects=observation['effects'])
    with c.writer_lock(home):
        if pinned.snapshot(home, consumers) != before:
            c.fail('plan.stale', 'Selection controls, policy, state or physical identity changed during preparation.', 4)
        fs.execute(planned, home, output)
    return True
