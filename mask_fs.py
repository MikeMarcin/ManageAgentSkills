"""Observational reconciliation plans and bounded, owned filesystem effects."""
from __future__ import annotations

import copy
import os
from pathlib import Path

import mask_core as c
import mask_adapters as adapters
import mask_pinned as pinned
import mask_resolve as resolve
import mask_workflow as workflow


def link_value(path):
    observed = c.kind(path)
    return dict(type=observed, link_text=os.readlink(path) if observed == 'symlink' else None)


def normalized_link(path, raw):
    if os.name == 'nt':
        if raw.startswith('\\\\?\\UNC\\'):
            raw = '\\\\' + raw[8:]
        elif raw.startswith('\\\\?\\'):
            raw = raw[4:]
    return Path(os.path.abspath(path.parent / raw))


def creation_link_text(source):
    raw = str(source)
    if os.name == 'nt' and not raw.startswith('\\\\?\\'):
        return '\\\\?\\UNC\\' + raw[2:] if raw.startswith('\\\\') else '\\\\?\\' + raw
    return raw


def plan(config, state, roots, *, proposals=None, register=(), unregister=(), keep_links=False, candidate=None, operation='apply', home=None, user_root=None, register_only=False, source_status=True, inactive=(), lock_proposals=None, allow_migration=False, dev_proposals=None, payload_views=None, selection_policy=None, staged_roles=None, repair_roles=False):
    proposals = proposals or {}
    lock_proposals = lock_proposals or {}
    dev_proposals = dev_proposals or {}
    source = c.legacy_source(config)
    after = copy.deepcopy(state)
    links, files, actions, blockers, observations, packages = [], [], [], [], [], {}
    import mask_selection as selection
    policy_value = selection.policy(selection_policy) if selection_policy is not None else selection.read_policy(home)[0] if home is not None else selection.policy()
    typed_files, uses_pinned = [], selection_policy is not None
    role_files, workflow_reports, released_roles, retired_files = [], [], [], []
    outcomes = []
    revision, dirty = None, None
    for root in sorted(roots, key=str):
        key = str(root)
        record = c.consumer_records(state).get(key)
        scope = 'user' if user_root == root else c.consumer_scope(state, root)
        manifest_path = c.declaration_path(root, scope, home)
        try:
            if record is None and key not in register:
                c.fail(scope + '.not_registered', 'Consumer is not registered.', 4, root=key)
            if key in register:
                c.registration_safe(root, source, home, state, scope)
            if key in unregister and keep_links:
                c.set_consumer(after, root, None, scope)
                actions.extend(dict(kind='link.abandon', status='planned', path=str(root / rel)) for rel in record['links'])
                observations.append(dict(root=key, scope=scope, abandoned=record))
                continue
            if record:
                c.registered_root(root, record, scope)
            elif not root.is_dir():
                c.fail('project.unavailable', 'Project is unavailable.', 4, root=key)
            before_text = c.read_text(manifest_path, 'manifest', missing=key in inactive)
            if key in inactive:
                if before_text is not None or record is None:
                    c.fail('readiness.blocked', 'Inactive transition requires an absent declaration and existing registration.', 4)
                current = record['last_manifest']
                desired = dict(schema_version=1, skills=[])
            else:
                current = c.selection_manifest(c.parse_json(before_text, 'manifest'))
                desired = c.selection_manifest(proposals.get(key, current))
            old_links = record['links'] if record else {}
            selected_pinned = desired['schema_version'] == 2 or pinned.is_pinned(record)
            expected = {}
            if selected_pinned:
                uses_pinned = True
                if record is not None and not pinned.is_pinned(record) and not allow_migration:
                    c.fail('migration.required', 'Convert legacy ownership through explicit pinned migration.', 4)
                if key in inactive:
                    desired, locked = record['last_manifest'], record['last_lock']
                    lock_before = None
                else:
                    lock_value, lock_raw = resolve.read_model(resolve.lock_path(root, scope, home), 'lock', missing=key in lock_proposals)
                    locked = resolve.lock(lock_proposals.get(key, lock_value), desired)
                    lock_before = lock_raw.decode('utf-8') if lock_raw is not None else None
                devs = dev_proposals.get(key, (record or {}).get('dev_links', {}))
                if devs and operation in ('apply', 'update', 'ensure'):
                    c.fail('dev_link.active', 'Explicit dev-link is unpinned; use source dev-link --to-pinned before ordinary reconciliation.', 4)
                if key not in unregister and key not in inactive:
                    expected = pinned.expected_links(home, desired, locked, config, payload_views, root=root, scope=scope, policy_value=policy_value, devs=devs, outcomes=outcomes)
                    for link in expected.values():
                        dev = devs.get(resolve.coordinate(link['resolution']))
                        if dev is not None:
                            pinned.observe_dev(dev, config)
                            link['dev'] = dev
                            link['link_text'] = creation_link_text(pinned.target(link, config, home))
                next_record = dict(root=key, root_identity=c.identity(root), mode='pinned', last_manifest=desired,
                                   last_manifest_digest=resolve.selection_digest(desired), last_source_revision=None,
                                   last_lock=locked, links={})
                if devs:
                    next_record.update(mode='dev-link', dev_links=devs)
                if key not in inactive:
                    for role, before_raw, after_raw in (('declaration', before_text, c.text_json(desired)), ('lock', lock_before, c.text_json(locked))):
                        changed = desired != current if role == 'declaration' else lock_value != locked
                        if changed:
                            if len(after_raw.encode('utf-8')) > resolve.MODEL_BYTES:
                                c.fail('lock.limit' if role == 'lock' else 'selection.limit', 'Serialized pinned control exceeds the 4 MiB model limit.', 4)
                            typed_files.append(dict(root=key, role=scope + '_' + role, before=before_raw, after=after_raw))
                            actions.append(dict(kind=role + '.write', status='planned', path=str(c.declaration_path(root, scope, home) if role == 'declaration' else resolve.lock_path(root, scope, home))))
            else:
                if source is None:
                    c.fail('migration.required', 'A v1 declaration or legacy record has no live checkout on a tap catalog machine; it must be migrated.', 4, root=key)
                revision = candidate['revision'] if candidate else c.git(source, 'rev-parse', 'HEAD', optional=True)
                dirty = (bool(c.git(source, 'status', '--porcelain', '--untracked-files=all', optional=True)) if source.is_dir() else False) if source_status else None
                if key not in unregister:
                    disabled = set(desired.get('targets', config['default_targets'])) - set(policy_value['enabled_agents'])
                    if desired['skills'] and disabled:
                        c.fail('compatibility.unsupported', 'Legacy explicit targets include a locally disabled agent; adjust targets or migrate explicitly.', 4, agents=sorted(disabled))
                    for identifier in desired['skills']:
                        if identifier not in packages:
                            packages[identifier] = candidate['packages'][identifier] if candidate else c.package(source, identifier)
                        for agent in desired.get('targets', config['default_targets']):
                            relative = adapters.relative(agent, scope, identifier)
                            expected[relative] = dict(skill=identifier, target=agent, link_text=creation_link_text(source / 'skills' / identifier))
                next_record = copy.deepcopy(record) if record else c.registry_record(root, desired, source)
            if register_only:
                expected = old_links
            next_record['links'] = {}
            leaves = []
            for relative in sorted(set(old_links) | set(expected)):
                leaf = root / relative
                c.parents_safe(root, leaf)
                actual = link_value(leaf)
                leaves.append(dict(relative=relative, **actual))
                old = old_links.get(relative)
                wanted = expected.get(relative)
                if actual['type'] not in ('missing', 'symlink'):
                    c.fail('target.collision', 'A real or special entry occupies the target.', 4, path=str(leaf), existing_type=actual['type'])
                if old and normalized_link(leaf, old['link_text']) != pinned.target(old, config, home):
                    c.fail('state.invalid', 'Ownership value does not name the configured source.', path=str(leaf))
                if actual['type'] == 'symlink':
                    if old is None:
                        c.fail('target.unmanaged_link', 'A symlink has no ownership record; inspect explicit adoption.', 4, path=str(leaf))
                    if actual['link_text'] != old['link_text']:
                        c.fail('target.drift', 'Owned link changed since it was recorded.', 4, path=str(leaf))
                before = actual['link_text'] if actual['type'] == 'symlink' else None
                if wanted:
                    after_raw = old['link_text'] if old and normalized_link(leaf, old['link_text']) == pinned.target(wanted, config, home) else wanted['link_text']
                    next_record['links'][relative] = dict(wanted, link_text=after_raw)
                else:
                    after_raw = None
                if before != after_raw:
                    entry = dict(root=key, relative=relative, skill=(wanted or old)['skill'], target=(wanted or old)['target'], before=before, after=after_raw)
                    links.append(entry)
                    actions.append(dict(kind='link.create' if after_raw else 'link.remove', status='planned', path=str(leaf), skill=entry['skill'], target=entry['target'], source=after_raw))
            # Declared native roles follow the selected bindings; observation never touches the destinations.
            bindings, targets, coordinates = {}, {}, {}
            for link in next_record['links'].values():
                bindings.setdefault(link['skill'], set()).add(link['target'])
                if link['skill'] not in targets:
                    location = pinned.target(link, config, home)
                    view = (payload_views or {}).get(link['resolution']['payload_digest']) if 'resolution' in link and 'dev' not in link else None
                    frozen = (candidate['packages'].get(link['skill'], {}).get('files') if candidate and 'resolution' not in link else None)
                    targets[link['skill']] = workflow.PackageView(files=frozen) if frozen is not None else workflow.PackageView(root=location) if c.kind(location) == 'directory' else workflow.PackageView(payload=view) if view is not None else None
                    coordinates[link['skill']] = resolve.coordinate(link['resolution']) if 'resolution' in link else legacy_alias(config) + '/' + link['skill']
            roles = workflow.requirements(root, scope, record, bindings, targets, coordinates=coordinates, staged=(staged_roles or {}).get(key), repair=repair_roles)
            from mask_repair import retired_files as plan_retired
            retired = plan_retired(root, roles['reports'], repair_roles)
            retired_files.extend(retired)
            actions.extend(dict(kind='retired_file.remove', status='planned', path=str(root / entry['relative']), skill=entry['skill']) for entry in retired)
            if roles['owned']:
                next_record['native_roles'] = roles['owned']
            else:
                next_record.pop('native_roles', None)
            for entry in roles['writes']:
                role_files.append(entry)
                actions.append(dict(kind='native_role.write' if entry['after'] is not None else 'native_role.remove', status='planned', path=str(root / entry['relative']), skill=entry['skill'], target=entry['agent'], name=entry['name']))
            released_roles.extend(dict(item, root=key) for item in roles['released'])
            workflow_reports.append(dict(root=key, scope=scope, skills=roles['reports'], complete=all(item['complete'] for item in roles['reports'])))
            for outcome in outcomes:
                relative = adapters.relative(outcome['agent'], scope, outcome['skill']) if outcome.get('agent') in adapters.BY_ID else ''
                owned = next_record['links'].get(relative)
                if outcome['root'] == key and outcome['status'] == 'selected' and outcome.get('target_verified', False) and owned is not None and link_value(root / relative) == dict(type='symlink', link_text=owned['link_text']):
                    outcome['status'] = 'deployed'
            observations.append(dict(root=key, scope=scope, identity=c.identity(root), manifest=desired, manifest_path=str(manifest_path), manifest_bytes=c.digest(before_text.encode()) if before_text is not None else None, leaves=leaves))
            if key in unregister:
                c.set_consumer(after, root, None, scope)
            else:
                if key not in inactive and not selected_pinned:
                    next_record.update(last_manifest=desired, last_manifest_digest=c.digest(desired), last_source_revision=revision)
                c.set_consumer(after, root, next_record, scope)
            if desired != current and key not in inactive and not selected_pinned:
                files.append(dict(root=key, before=before_text, after=c.text_json(desired)))
                actions.append(dict(kind='manifest.write', status='planned', path=str(manifest_path)))
        except c.MaskError as error:
            blockers.append(error.as_dict())
    if after != state:
        actions.append(dict(kind='state.record', status='planned'))
        after['generation'] = state['generation'] + 1
    source_data = dict(root=str(source) if source is not None else None, revision=revision, dirty=dirty,
                       fingerprint=c.digest({key: value['fingerprint'] for key, value in sorted(packages.items())}))
    pinned_controls = dict(workspaces=pinned.observe(roots, state, home, user_root=user_root), config_text=c.read_text(home / 'config.json'), policy_text=c.read_text(home / 'integration.json', missing=True), selection_policy_text=selection.read_policy(home)[1], home_identity=c.identity(home)) if uses_pinned else None
    payload = dict(protocol=1, adapters=c.ADAPTERS, operation=operation, config=config, generation=state['generation'],
                   state=state, observations=observations, source=source_data, links=links, manifests=files,
                   register=sorted(register), unregister=sorted(unregister), keep_links=keep_links, register_only=register_only, inactive=sorted(inactive))
    if uses_pinned:
        payload.update(files=typed_files, pinned=pinned_controls)
    if role_files:
        # Only planned role effects bind the hash; an observation that merely differs in detail must not stale a reviewed plan.
        payload['native_roles'] = role_files
    if retired_files:
        payload['retired_files'] = retired_files
    development = pinned.development_observations(state, after, [str(root) for root in roots], config) if uses_pinned else []
    if development:
        payload['development'] = development
    if candidate:
        payload['transition'] = candidate.get('transition')
    payload['selection_policy'] = policy_value
    shadowing = scope_shadowing(after, config, home, {str(root) for root in roots})
    result = dict(outcomes=outcomes, shadowing=shadowing, applicable=not blockers, blockers=blockers, plan_hash=c.digest(payload), source=source_data,
                projects=[entry for entry in observations if entry['scope'] == 'project'],
                users=[entry for entry in observations if entry['scope'] == 'user'], actions=actions, would_change=bool(actions),
                intent=dict(operation=operation, selected=[str(root) for root in roots], links=links, manifests=files,
                            before_state=state, after_state=after, config=config))
    if uses_pinned:
        result['intent'].update(files=typed_files, pinned=pinned_controls)
    if workflow_reports:
        result.update(workflow_readiness=workflow_reports, released_roles=released_roles)
    if role_files:
        result['intent']['native_roles'] = role_files
    if retired_files:
        result['intent']['retired_files'] = retired_files
    if development or operation == 'source.dev-link':
        result['intent']['development'] = development
    return result


def legacy_alias(config):
    """The source-qualified alias of the shared legacy checkout (``mask_task`` uses the same rule)."""
    return config['legacy_source'] if config['schema_version'] == 2 else 'legacy'


def scope_shadowing(state, config, home, selected):
    """Report owned/proposed discovery-name overlap without predicting host precedence."""
    user = state.get('user')
    if user is None:
        return []
    edges = {}
    for key, record in c.consumer_records(state).items():
        root = Path(key)
        scope = c.consumer_scope(state, root)
        try:
            c.registered_root(root, record, scope)
            for relative, link in record['links'].items():
                leaf = root / relative
                c.parents_safe(root, leaf)
                target = pinned.target(link, config, home)
                observed = (link_value(leaf) == dict(type='symlink', link_text=link['link_text'])
                            and normalized_link(leaf, link['link_text']) == target and c.kind(target) == 'directory')
                if not observed and key not in selected:
                    continue
                row = link.get('resolution')
                edge = dict(root=key, scope=scope, agent=link['target'], name=link['skill'], path=str(leaf),
                            coordinate=resolve.coordinate(row) if row else None,
                            payload_digest=row['payload_digest'] if row else None,
                            status='observed' if observed else 'planned')
                edges.setdefault((link['target'], link['skill']), []).append((str(target), edge))
        except c.MaskError:
            # An unavailable unrelated consumer is not evidence of an actual overlap.
            continue
    result = []
    for (agent, name), rows in sorted(edges.items()):
        users = [row for row in rows if row[1]['scope'] == 'user']
        projects = [row for row in rows if row[1]['scope'] == 'project']
        for personal_target, personal in users:
            for project_target, project in projects:
                if personal['root'] in selected or project['root'] in selected:
                    # An overlap whose scopes resolve to one directory stays observable, but precedence
                    # cannot change which bytes a host would load, so it raises no warning.
                    result.append(dict(agent=agent, name=name, user=personal, project=project,
                                       same_target=personal_target == project_target,
                                       host_precedence='not_assumed', host_load='not_verified'))
    return result


def released_message(reason):
    """A deleted managed role is gone, so it must not be reported as preserved."""
    if reason.startswith('deleted'):
        return 'A managed native role file was deleted outside MASK; it is no longer managed.'
    return 'A managed native role file changed outside MASK; it is preserved and no longer managed.'


def shadow_warnings(rows):
    return [dict(code='target.scope_shadowing', message='User and project discovery names overlap; host precedence is not assumed.', **row)
            for row in rows if not row['same_target']]


def public_plan(planned, output):
    output['data'] = {key: value for key, value in planned.items() if key not in ('intent', 'actions', 'would_change', 'released_roles')}
    output['actions'] = planned['actions']
    output['would_change'] = planned['would_change']
    output['warnings'].extend(shadow_warnings(planned.get('shadowing', [])))
    for item in planned.get('released_roles', []):
        output['warnings'].append(dict(code='native_role.released', message=released_message(item['reason']), **item))
    for row in planned.get('outcomes', []):
        if row['status'] == 'overridden':
            output['warnings'].append(dict(code='compatibility.local_override', message=row['reason'], coordinate=row['coordinate'], root=row['root'], agent=row['agent']))
    if planned['source']['dirty']:
        output['warnings'].append(dict(code='source.dirty', message='Local authoring changes are included in the source fingerprint.'))
    if not planned['projects'] and not planned.get('users') and not planned['blockers']:
        output['warnings'].append(dict(code='project.empty_registry', message='No registered projects selected.'))


def ensure_applicable(planned, expected=None):
    if expected is not None and expected != planned['plan_hash']:
        c.fail('plan.stale', 'Plan inputs changed; inspect and preview again.', 4)
    if planned['blockers']:
        first = planned['blockers'][0]
        raise c.MaskError(first['code'], first['message'], 4, details=first['details'])


def checkpoint(label):
    """Internal failure-injection boundary used by local tests."""


def required_directories(intent):
    directories = set()
    for entry in intent['links']:
        if entry['after'] is not None:
            root = Path(entry['root'])
            leaf = root / entry['relative']
            for parent in (leaf.parent.parent, leaf.parent):
                if c.kind(parent) == 'missing':
                    directories.add(str(parent))
    directories.update(workflow.role_directories(intent))
    return sorted(directories)


def make_pending(planned, home):
    import uuid
    intent = copy.deepcopy(planned['intent'])
    version = max(intent['before_state']['schema_version'], intent['after_state']['schema_version'])
    if any(key in intent for key in ('controls', 'selection_change', 'native_roles', 'retired_files')):
        version = 3
    intent.update(schema_version=version, transaction_id=str(uuid.uuid4()), phase='prepared',
                  base_generation=intent['before_state']['generation'],
                  before_state_text=c.read_text(home / 'state.json', 'state', missing=True),
                  after_state_text=c.text_json(intent['after_state']),
                  directories=required_directories(intent))
    return intent


def validate_pending(pending, home):
    import mask_selection as selection
    c.fields(pending, ('schema_version', 'transaction_id', 'phase', 'operation', 'base_generation', 'selected',
                      'links', 'manifests', 'before_state', 'after_state', 'config', 'before_state_text', 'after_state_text', 'directories'),
             ('git', 'launcher', 'controls', 'files', 'pinned', 'migration', 'development', 'selection_change', 'native_roles', 'setup', 'retired_files'), 'recovery', versions=(1, 2, 3))
    if pending['operation'] not in {'selection-policy.set', 'selection-policy.clear', 'compatibility.override', 'compatibility.clear', 'project.set-agents', 'user.set-agents', 'source.dev-link', 'migrate', 'ensure', 'ensure.deactivate', 'apply', 'project.register', 'project.unregister', 'project.set', 'project.require', 'project.unrequire', 'project.set-targets', 'user.register', 'user.unregister', 'user.set', 'user.require', 'user.unrequire', 'user.set-targets', 'update', 'self.update', 'self.install', 'install', 'remove'}:
        c.fail('recovery.conflict', 'Unknown pending operation.', 8)
    if pending['operation'].startswith('ensure') and pending['schema_version'] != 3:
        c.fail('recovery.conflict', 'Readiness requires v3 control observations.', 8)
    if 'files' in pending and not isinstance(pending['files'], list):
        c.fail('recovery.conflict', 'Typed pending files must be a list.', 8)
    for field in ('selected', 'links', 'manifests', 'directories'):
        if not isinstance(pending[field], list):
            c.fail('recovery.conflict', 'Invalid pending collection.', 8)
    if any(not isinstance(item, str) for item in pending['selected'] + pending['directories']) or any(not isinstance(item, dict) for item in pending['links'] + pending['manifests'] + pending.get('files', [])):
        c.fail('recovery.conflict', 'Invalid pending collection item.', 8)
    if not isinstance(pending['transaction_id'], str) or pending['phase'] not in ('prepared', 'git_started', 'git_advanced'):
        c.fail('recovery.conflict', 'Invalid pending transaction identity or phase.', 8)
    if 'git' in pending:
        from mask_git import validate_git_intent
        validate_git_intent(pending['git'], pending['config'], Path(__file__).resolve().parent)
    before, after = c.state(pending['before_state']), c.state(pending['after_state'])
    if pending['schema_version'] != (3 if any(key in pending for key in ('controls', 'selection_change', 'native_roles', 'retired_files')) else max(before['schema_version'], after['schema_version'])):
        c.fail('recovery.conflict', 'Journal version disagrees with its states.', 8)
    if before['schema_version'] != after['schema_version'] and not (pending['operation'] in ('user.register', 'install') and before['schema_version'] == 1 and after['schema_version'] == 2 and before.get('user') is None and after.get('user') is not None) and not (before['schema_version'] < 3 and after['schema_version'] == 3 and 'pinned' in pending):
        c.fail('recovery.conflict', 'Only user registration may upgrade the state schema.', 8)
    before_records, after_records = c.consumer_records(before), c.consumer_records(after)
    if type(pending['base_generation']) is not int or pending['base_generation'] != before['generation'] or after['generation'] not in (before['generation'], before['generation'] + 1):
        c.fail('recovery.conflict', 'Invalid pending generation.', 8)
    current_config = c.read_json(home / 'config.json', default={})
    if pending['config'] is None:
        if pending['operation'] not in ('self.install', 'self.update') or current_config:
            c.fail('recovery.conflict', 'Unexpected missing machine configuration.', 8)
    elif 'migration' not in pending and c.config(pending['config']) != c.config(current_config):
        c.fail('recovery.conflict', 'Machine configuration changed since the pending operation.', 8)
    if not isinstance(pending['selected'], list) or len(set(pending['selected'])) != len(pending['selected']):
        c.fail('recovery.conflict', 'Invalid pending project selection.', 8)
    selected = set(pending['selected'])
    if 'migration' in pending or pending['operation'] == 'migrate':
        pinned.validate_migration(pending, home)
    if 'pinned' not in pending:
        for root in selected:
            old, new = before_records.get(root), after_records.get(root)
            if not (pinned.is_pinned(old) or pinned.is_pinned(new)):
                continue
            # Keep-links unregister only abandons ownership; it has no root effects.
            abandoned = (pinned.is_pinned(old) and new is None
                         and pending['operation'] == c.consumer_scope(before, root) + '.unregister'
                         and not any(entry.get('root') == root for entry in pending['links'] + pending['manifests'] + pending.get('files', []))
                         and not any(name in pending for name in ('git', 'launcher', 'controls')))
            if not abandoned:
                c.fail('recovery.conflict', 'Selected pinned ownership requires pinned journal observations.', 8)
    needs_development = any(record.get('dev_links') for state in (before, after) for root, record in c.consumer_records(state).items() if root in selected) and 'pinned' in pending
    if 'development' in pending or pending['operation'] == 'source.dev-link' or needs_development:
        pinned.validate_development(pending, home)
    needs_selection_change = pending['operation'] in {'selection-policy.set', 'selection-policy.clear', 'compatibility.override', 'compatibility.clear', 'project.set-agents', 'user.set-agents'} or pending['operation'] in {'project.set-targets', 'user.set-targets'} and any(pinned.is_pinned(before_records.get(root)) for root in selected)
    if 'selection_change' in pending or needs_selection_change:
        try:
            selection.validate_change(pending, home)
        except c.MaskError as error:
            c.fail('recovery.conflict', 'Invalid selection authority transition.', 8, cause=error.as_dict())
    if 'controls' in pending:
        from mask_ensure import validate_controls
        validate_controls(pending, home)
    if 'pinned' in pending:
        if pending['schema_version'] != 3 or not isinstance(pending.get('files'), list):
            c.fail('recovery.conflict', 'Pinned journals require typed files and version 3.', 8)
        pinned.validate_observations(pending, home)
    elif 'files' in pending or max(before['schema_version'], after['schema_version']) < 3 and pending['schema_version'] == 3 and 'controls' not in pending and 'native_roles' not in pending:
        c.fail('recovery.conflict', 'Unexpected journal extension.', 8)
    if 'native_roles' in pending:
        if not isinstance(pending['native_roles'], list) or not pending['native_roles'] or any(not isinstance(item, dict) for item in pending['native_roles']):
            c.fail('recovery.conflict', 'Typed native role journal entries must be a nonempty list.', 8)
        workflow.validate_pending_roles(pending, before, after)
    if 'setup' in pending:
        from mask_setup import validate_journal
        validate_journal(pending)
    if 'retired_files' in pending:
        from mask_repair import validate_retired
        validate_retired(pending)
    if not selected <= before_records.keys() | after_records.keys():
        c.fail('recovery.conflict', 'Pending project is absent from recorded registry.', 8)
    if 'launcher' in pending:
        from mask_install import validate_launcher_intent
        validate_launcher_intent(pending)
    elif before['launchers'] != after['launchers']:
        c.fail('recovery.conflict', 'Link operations cannot change launcher ownership.', 8)
    for root in before_records.keys() | after_records.keys():
        if root in before_records and root in after_records and pinned.is_pinned(before_records[root]) != pinned.is_pinned(after_records[root]) and 'migration' not in pending:
            c.fail('recovery.conflict', 'Existing consumer mode conversion requires an explicit migration journal.', 8)
        if root in before_records and root in after_records and c.consumer_scope(before, root) != c.consumer_scope(after, root):
            c.fail('recovery.conflict', 'A journal cannot change a consumer scope.', 8)
        if root not in selected and before_records.get(root) != after_records.get(root):
            c.fail('recovery.conflict', 'Pending state changes an unselected project.', 8)
    allowed_directories = {str(Path(pending['launcher']['path']).parent)} if 'launcher' in pending else set()
    for key in selected:
        record = before_records.get(key) or after_records[key]
        # Explicit keep-links may abandon an unavailable root without effects.
        touches = any(entry.get('root') == key for entry in pending['links'] + pending['manifests'] + pending.get('files', []))
        if touches or pending['operation'] in ('project.register', 'user.register', 'ensure', 'ensure.deactivate'):
            selected_state = before if key in before_records else after
            c.registered_root(Path(key), record, c.consumer_scope(selected_state, key))
        selected_state = before if key in before_records else after
        for adapter in adapters.paths(c.consumer_scope(selected_state, key)).values():
            allowed_directories.update((str(Path(key) / Path(adapter).parent), str(Path(key) / adapter)))
        allowed_directories.update(workflow.allowed_directories(key, c.consumer_scope(selected_state, key)))
    if not isinstance(pending['directories'], list) or not set(pending['directories']) <= allowed_directories:
        c.fail('recovery.conflict', 'Unsafe pending directory intent.', 8)
    link_keys = set()
    for entry in pending['links']:
        c.fields(entry, ('root', 'relative', 'skill', 'target', 'before', 'after'), family='recovery')
        c.skill_id(entry['skill'])
        if entry['root'] not in selected or entry['target'] not in c.ADAPTERS or entry['relative'] != adapters.relative(entry['target'], c.consumer_scope(before if entry['root'] in before_records else after, entry['root']), entry['skill']):
            c.fail('recovery.conflict', 'Unsafe pending link path.', 8)
        leaf = Path(entry['root']) / entry['relative']
        key = (entry['root'], entry['relative'])
        if key in link_keys:
            c.fail('recovery.conflict', 'Duplicate pending link transition.', 8)
        link_keys.add(key)
        for side, state in (('before', before), ('after', after)):
            record = c.consumer_records(state).get(entry['root'], {}).get('links', {}).get(entry['relative'])
            raw = entry[side]
            if raw is not None and (not record or not isinstance(raw, str) or record['link_text'] != raw or normalized_link(leaf, raw) != pinned.target(record, pending['config'], home)):
                c.fail('recovery.conflict', 'Pending link disagrees with ownership state.', 8)
            if side == 'after' and raw != (record['link_text'] if record else None):
                c.fail('recovery.conflict', 'Pending link omits its desired ownership target.', 8)
    for root in selected:
        old, new = before_records.get(root), after_records.get(root)
        if not (pinned.is_pinned(old) or pinned.is_pinned(new)) or 'pinned' not in pending:
            continue
        old_links, new_links = (old or {}).get('links', {}), (new or {}).get('links', {})
        for relative in old_links.keys() | new_links.keys():
            if old_links.get(relative, {}).get('link_text') != new_links.get(relative, {}).get('link_text') and (root, relative) not in link_keys:
                c.fail('recovery.conflict', 'Pinned journal omits an owned link transition.', 8)
    for entry in pending['manifests']:
        c.fields(entry, ('root', 'before', 'after'), family='recovery')
        if entry['root'] not in selected:
            c.fail('recovery.conflict', 'Unselected manifest intent.', 8)
        for side in ('before', 'after'):
            if not isinstance(entry[side], str):
                c.fail('recovery.conflict', 'Invalid pending manifest bytes.', 8)
            c.manifest(c.parse_json(entry[side], 'manifest'))
    for side, expected in (('before', before), ('after', after)):
        text = pending[side + '_state_text']
        if text is None and side == 'before' and expected == c.empty_state():
            continue
        if not isinstance(text, str) or c.state(c.parse_json(text, 'state')) != expected:
            c.fail('recovery.conflict', 'Pending state text disagrees with intent.', 8)
    return pending


def pending_manifest_path(pending, entry, home):
    root = entry['root']
    selected_state = pending['before_state'] if root in c.consumer_records(pending['before_state']) else pending['after_state']
    return c.declaration_path(root, c.consumer_scope(selected_state, root), home)


def check_current(pending, home):
    """Preflight every recoverable before/after state before any recovery effect."""
    validate_pending(pending, home)
    if 'migration' in pending:
        pinned.check_migration(pending, home)
    if 'development' in pending:
        pinned.check_development(pending)
    if 'pinned' in pending:
        pinned.check_observations(pending, home)
        pinned.verify_transition(pending, home)
    if 'controls' in pending:
        from mask_ensure import check_controls
        check_controls(pending, home)
    if 'launcher' in pending:
        from mask_install import check_launcher
        check_launcher(pending)
    for entry in pending['links']:
        leaf = Path(entry['root']) / entry['relative']
        c.parents_safe(Path(entry['root']), leaf)
        actual = link_value(leaf)
        if not recoverable_link(actual, entry):
            c.fail('recovery.conflict', 'A pending link was replaced or edited.', 8, path=str(leaf))
    for entry in pending['manifests']:
        path = pending_manifest_path(pending, entry, home)
        if c.read_text(path, 'manifest') not in (entry['before'], entry['after']):
            c.fail('recovery.conflict', 'A pending manifest was edited.', 8, path=str(path))
    for entry in pending.get('files', []):
        if c.read_text(pinned.file_path(entry, home), missing=True) not in (entry['before'], entry['after']):
            c.fail('recovery.conflict', 'A typed pending control was edited.', 8)
    workflow.check_roles(pending)
    from mask_repair import check_retired
    check_retired(pending)
    if 'setup' in pending:
        from mask_setup import check_journal
        check_journal(pending)
    actual = c.read_text(home / 'state.json', 'state', missing=True)
    if actual not in (pending['before_state_text'], pending['after_state_text']):
        c.fail('recovery.conflict', 'Registry changed after the pending operation.', 8)


def recoverable_link(actual, entry):
    # A scheduled replacement may stop after unlink and before symlink creation.
    return (actual['type'] in ('missing', 'symlink')
            and (actual['link_text'] in (entry['before'], entry['after'])
                 or actual['type'] == 'missing' and entry['before'] != entry['after']))


def set_link(entry, side, *, inject=False):
    root = Path(entry['root'])
    leaf = root / entry['relative']
    c.parents_safe(root, leaf)
    actual = link_value(leaf)
    wanted = entry[side]
    if not recoverable_link(actual, entry):
        c.fail('recovery.conflict', 'Link precondition changed immediately before effect.', 8, path=str(leaf))
    if actual['link_text'] == wanted:
        return
    if actual['type'] == 'symlink':
        leaf.unlink()
        if inject:
            checkpoint('link_unlinked')
    if wanted is not None:
        leaf.parent.mkdir(parents=True, exist_ok=True)
        c.parents_safe(root, leaf)
        if c.kind(leaf) != 'missing':
            c.fail('target.collision', 'Target appeared before link creation.', 4, path=str(leaf))
        try:
            leaf.symlink_to(wanted, target_is_directory=True)
        except OSError as error:
            if getattr(error, 'winerror', None) == 1314:
                c.fail('target.symlink_unsupported', 'Native Windows directory symlink privileges are required.', 5)
            raise


def restore(pending, home, side, *, inject=False):
    check_current(pending, home)
    if side == 'after':
        from mask_repair import save_backups
        save_backups(pending, home)
    if 'launcher' in pending:
        from mask_install import restore_launcher
        restore_launcher(pending, side)
        if inject:
            checkpoint('launcher')
    entries = pending['links'] if side == 'after' else reversed(pending['links'])
    for entry in entries:
        if 'development' in pending:
            pinned.check_development(pending)
        if 'pinned' in pending:
            pinned.check_observations(pending, home)
            pinned.verify_transition(pending, home, entry)
        if 'controls' in pending:
            from mask_ensure import check_controls
            check_controls(pending, home)
        set_link(entry, side, inject=inject)
        if inject:
            checkpoint('link')
    if 'migration' in pending:
        pinned.check_migration(pending, home)
    for entry in pending['manifests']:
        path = pending_manifest_path(pending, entry, home)
        actual = c.read_text(path, 'manifest')
        if actual not in (entry['before'], entry['after']):
            c.fail('recovery.conflict', 'Manifest changed immediately before replacement.', 8)
        c.atomic_text(path, entry[side], actual)
        if inject:
            checkpoint('manifest')
    for entry in pending.get('files', []):
        pinned.check_observations(pending, home)
        path = pinned.file_path(entry, home)
        actual = c.read_text(path, missing=True)
        if actual not in (entry['before'], entry['after']):
            c.fail('recovery.conflict', 'Typed control changed before replacement.', 8)
        wanted = entry[side]
        if wanted is None:
            if actual is not None:
                path.unlink()
        else:
            c.atomic_text(path, wanted, actual)
        if inject:
            checkpoint('selection_policy' if entry['role'] == 'selection_policy' else 'config' if entry['role'] == 'machine_config' else 'lock' if entry['role'].endswith('_lock') else 'manifest')
    for entry in (pending.get('native_roles', []) if side == 'after' else reversed(pending.get('native_roles', []))):
        workflow.set_role(entry, side)
        if inject:
            checkpoint('native_role')
    if 'setup' in pending:
        from mask_setup import restore_journal
        restore_journal(pending, side)
        if inject:
            checkpoint('native_role_lock')
    from mask_repair import restore_retired
    restore_retired(pending, side)
    if inject and pending.get('retired_files'):
        checkpoint('retired_file')
    if side == 'after' and 'pinned' in pending:
        for root, record in c.consumer_records(pending['after_state']).items():
            if root not in pending['selected'] or not pinned.is_pinned(record):
                continue
            for relative, link in record['links'].items():
                leaf = Path(root) / relative
                c.parents_safe(Path(root), leaf)
                if link_value(leaf) != dict(type='symlink', link_text=link['link_text']):
                    c.fail('recovery.conflict', 'Pinned after ownership is not present on disk.', 8, path=str(leaf))
    if 'controls' in pending:
        from mask_ensure import restore_controls
        restore_controls(pending, home, side)
    if 'migration' in pending:
        pinned.check_migration(pending, home)
    check_final_controls(pending, home, side)
    text = pending[side + '_state_text']
    path = home / 'state.json'
    if text is not None:
        actual = c.read_text(path, 'state', missing=True)
        if actual not in (pending['before_state_text'], pending['after_state_text']):
            c.fail('recovery.conflict', 'Registry changed immediately before replacement.', 8)
        c.atomic_text(path, text, actual)
    elif c.kind(path) != 'missing':
        # Only remove the newly created regular registry with exact after bytes.
        if c.read_text(path, 'state') != pending['after_state_text']:
            c.fail('recovery.conflict', 'Registry changed before rollback.', 8)
        path.unlink()
    if inject:
        checkpoint('state')


def check_final_controls(pending, home, side):
    if 'pinned' not in pending:
        return
    pinned.check_observations(pending, home)
    for entry in pending.get('files', []):
        if c.read_text(pinned.file_path(entry, home), missing=True) != entry[side]:
            c.fail('recovery.conflict', 'Final typed control bytes differ from the selected transaction side.', 8)


def clear_pending(home, pending, side='after'):
    check_final_controls(pending, home, side)
    if 'migration' in pending:
        pinned.check_migration(pending, home)
    path = home / 'pending.json'
    if c.read_json(path, 'recovery') != pending:
        c.fail('recovery.conflict', 'Pending journal changed before cleanup.', 8)
    path.unlink()
    if 'setup' in pending:
        from mask_setup import discard_stage
        discard_stage(home, pending)


def execute(planned, home, output, *, pending=None):
    ensure_applicable(planned)
    if not planned['would_change'] and pending is None:
        return
    pending = pending or make_pending(planned, home)
    validate_pending(pending, home)
    from mask_repair import backup_records
    backups = backup_records(pending, home)
    if backups:
        output['data'].setdefault('backups', []).extend(backups)
    if c.kind(home / 'pending.json') == 'missing':
        c.atomic_text(home / 'pending.json', c.text_json(pending), None)
    checkpoint('intent')
    try:
        restore(pending, home, 'after', inject=True)
        clear_pending(home, pending)
        output.update(changed=planned['would_change'], transaction='committed')
        for action in output['actions']:
            action['status'] = 'applied'
        for entry in output['data'].get('workflow_readiness', []):
            for report in entry['skills']:
                for row in report['roles']:
                    if row.get('action') in ('create', 'update'):
                        row.update(state='ok', ownership='package-managed', observed_sha256=row['expected_sha256'], deployed=True)
                removed = {(item['root'], item['relative']) for item in pending.get('retired_files', [])}
                for row in report.get('retired_files', []):
                    if (entry['root'], row['path']) in removed:
                        row.update(state='removed')
        for outcome in output['data'].get('outcomes', []):
            if outcome['status'] not in ('selected', 'overridden'):
                continue
            record = c.consumer_records(pending['after_state']).get(outcome['root'], {})
            relative = adapters.relative(outcome['agent'], outcome['scope'], outcome['skill'])
            owned = record.get('links', {}).get(relative)
            if owned is not None and link_value(Path(outcome['root']) / relative) == dict(type='symlink', link_text=owned['link_text']):
                outcome['deployed'] = True
                outcome['target_verified'] = True
                if outcome['status'] == 'selected':
                    outcome['status'] = 'deployed'
    except (Exception, KeyboardInterrupt) as error:
        if pending.get('git'):
            output.update(changed=True, transaction='partial')
            c.fail('recovery.required', 'Git update may have effects; inspect and complete recovery.', 8)
        try:
            restore(pending, home, 'before')
            clear_pending(home, pending, 'before')
            residual = [path for path in pending['directories'] if c.kind(Path(path)) != 'missing']
            output.update(changed=bool(residual), transaction='rolled_back')
            output['data']['retained_directories'] = residual
            for action in output['actions']:
                action['status'] = 'rolled_back'
        except (Exception, KeyboardInterrupt):
            output.update(changed=True, transaction='partial')
            c.fail('recovery.required', 'Partial operation retained its journal; inspect recovery.', 8)
        if isinstance(error, (c.MaskError, KeyboardInterrupt)):
            raise error
        c.fail('filesystem.failed', 'Filesystem operation failed; core effects were rolled back.', 5)
    finally:
        from mask_repair import backup_status
        backup_status(backups)


def recover(home, output, mode):
    raw = c.read_text(home / 'pending.json', 'recovery', missing=True)
    if raw is None:
        output['data'] = dict(pending=None)
        return
    pending = c.parse_json(raw, 'recovery')
    validate_pending(pending, home)
    output['data'] = dict(pending=pending, recovery_mode=mode)
    if 'setup' in pending:
        # Package script side effects are never inspected or undone; only MASK's own staged/published files are.
        output['data']['setup'] = dict(phase=pending['setup']['phase'], skill=pending['setup']['skill'], script_effects='unknown')
    if mode == 'inspect':
        return
    check_current(pending, home)
    if mode == 'complete' and pending.get('setup', {}).get('phase') == 'launched':
        c.fail('setup.unverified', 'Package setup was launched but never validated; MASK does not rerun package code from a journal.', 8)
    if pending.get('git'):
        from mask_git import recover_git
        recover_git(pending, home, output, mode)
    if mode == 'complete':
        source = c.legacy_source(pending['config'])
        for key in pending['selected']:
            record = c.consumer_records(pending['after_state']).get(key)
            if record and not pinned.is_pinned(record):
                identifiers = {link['skill'] for link in record['links'].values()} if pending['operation'] == 'ensure.deactivate' else record['last_manifest']['skills']
                for identifier in identifiers:
                    c.package(source, identifier)
    output['would_change'] = True
    if output['dry_run']:
        return
    try:
        restore(pending, home, 'after' if mode == 'complete' else 'before')
        clear_pending(home, pending, 'after' if mode == 'complete' else 'before')
    except (Exception, KeyboardInterrupt):
        output.update(changed=True, transaction='partial')
        raise
    residual = [path for path in pending['directories'] if c.kind(Path(path)) != 'missing']
    output.update(changed=True, transaction='committed' if mode == 'complete' else 'rolled_back')
    output['data']['retained_directories'] = residual


def adopt(config, state, root, identifier, target, expected_source, output, home, guard=None):
    c.skill_id(identifier)
    if target not in c.ADAPTERS:
        c.fail('config.invalid', 'Unknown agent target.')
    scope = c.consumer_scope(state, root)
    record = c.consumer_records(state).get(str(root))
    if record is None:
        c.fail('project.not_registered', 'Adoption requires registration.', 4)
    c.registered_root(root, record, scope)
    if record.get('mode') == 'dev-link':
        c.fail('dev_link.active', 'Return to pins explicitly before adopting additional links.', 4)
    if pinned.is_pinned(record):
        declaration, locked = resolve.read_exact_lock(root, scope, home, config, verify=False)
        if declaration != record['last_manifest'] or locked != record['last_lock']:
            c.fail('target.adoption_stale', 'Reconcile changed pinned selection/lock through apply before adopting its links.', 4)
        expected_links = pinned.expected_links(home, declaration, locked, config, root=root, scope=scope)
        wanted = expected_links.get(adapters.relative(target, scope, identifier))
        if wanted is None:
            c.fail('target.unmanaged_link', 'Adoption requires a selected pinned skill and target.', 4)
        import mask_store as store
        expected = store.verify(home, wanted['resolution'])
        package = wanted['resolution']
    else:
        if c.legacy_source(config) is None:
            c.fail('migration.required', 'A legacy consumer has no live checkout on a tap catalog machine; migrate it before adopting links.', 4, root=str(root))
        declaration = c.consumer_manifest(root, scope, home)
        if identifier not in declaration['skills'] or target not in declaration.get('targets', config['default_targets']):
            c.fail('target.unmanaged_link', 'Adoption requires a declared skill and enabled target.', 4)
        source = Path(config['source']['root'])
        package = c.package(source, identifier)
        expected = source / 'skills' / identifier
        wanted = dict(skill=identifier, target=target)
    if not Path(expected_source).is_absolute() or Path(expected_source).resolve() != expected:
        c.fail('target.unmanaged_link', 'Expected source does not match the configured package.', 4)
    relative = adapters.relative(target, scope, identifier)
    leaf = root / relative
    c.parents_safe(root, leaf)
    current = link_value(leaf)
    if current['type'] != 'symlink' or normalized_link(leaf, current['link_text']) != expected:
        c.fail('target.unmanaged_link', 'Only an exact directory symlink can be adopted.', 4)
    owned = record['links'].get(relative)
    if owned and owned['link_text'] != current['link_text']:
        c.fail('target.drift', 'Adoption cannot repair mismatched ownership.', 4)
    plan_hash = c.digest(dict(config=config, state=state, scope=scope, manifest_path=str(c.declaration_path(root, scope, home)), manifest=declaration, identity=c.identity(root), package=package, leaf=current))
    output['data'] = dict(root=str(root), scope=scope, plan_hash=plan_hash, path=str(leaf), link_text=current['link_text'])
    if guard and guard != plan_hash:
        c.fail('plan.stale', 'Adoption inputs changed since preview.', 4)
    if owned:
        return
    output['would_change'] = True
    output['actions'] = [dict(kind='link.adopt', status='planned', path=str(leaf))]
    if not output['dry_run']:
        c.parents_safe(root, leaf)
        if link_value(leaf) != current:
            c.fail('target.drift', 'Link changed before adoption.', 4)
        after = copy.deepcopy(state)
        c.consumer_records(after)[str(root)]['links'][relative] = dict(wanted, link_text=current['link_text'])
        c.save_state(home, state, after)
        output.update(changed=True, transaction='committed')
