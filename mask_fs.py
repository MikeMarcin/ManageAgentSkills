"""Observational reconciliation plans and bounded, owned filesystem effects."""
from __future__ import annotations

import copy
import os
from pathlib import Path

import mask_core as c


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


def plan(config, state, roots, *, proposals=None, register=(), unregister=(), keep_links=False, candidate=None, operation='apply', home=None, user_root=None, register_only=False, source_status=True, inactive=()):
    proposals = proposals or {}
    source = Path(config['source']['root'])
    after = copy.deepcopy(state)
    links, files, actions, blockers, observations, packages = [], [], [], [], [], {}
    revision = candidate['revision'] if candidate else c.git(source, 'rev-parse', 'HEAD', optional=True)
    dirty = (bool(c.git(source, 'status', '--porcelain', '--untracked-files=all', optional=True)) if source.is_dir() else False) if source_status else None
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
                current = c.manifest(c.parse_json(before_text, 'manifest'))
                desired = c.manifest(proposals.get(key, current))
            old_links = record['links'] if record else {}
            expected = {}
            if key not in unregister:
                for identifier in desired['skills']:
                    if identifier not in packages:
                        packages[identifier] = candidate['packages'][identifier] if candidate else c.package(source, identifier)
                    for target in desired.get('targets', config['default_targets']):
                        relative = f'{c.ADAPTERS[target]}/{identifier}'
                        expected[relative] = dict(skill=identifier, target=target, link_text=creation_link_text(source / 'skills' / identifier))
            if register_only:
                expected = old_links
            next_record = copy.deepcopy(record) if record else c.registry_record(root, desired, source)
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
                if old and normalized_link(leaf, old['link_text']) != source / 'skills' / old['skill']:
                    c.fail('state.invalid', 'Ownership value does not name the configured source.', path=str(leaf))
                if actual['type'] == 'symlink':
                    if old is None:
                        c.fail('target.unmanaged_link', 'A symlink has no ownership record; inspect explicit adoption.', 4, path=str(leaf))
                    if actual['link_text'] != old['link_text']:
                        c.fail('target.drift', 'Owned link changed since it was recorded.', 4, path=str(leaf))
                before = actual['link_text'] if actual['type'] == 'symlink' else None
                if wanted:
                    after_raw = old['link_text'] if old else wanted['link_text']
                    next_record['links'][relative] = dict(wanted, link_text=after_raw)
                else:
                    after_raw = None
                if before != after_raw:
                    entry = dict(root=key, relative=relative, skill=(wanted or old)['skill'], target=(wanted or old)['target'], before=before, after=after_raw)
                    links.append(entry)
                    actions.append(dict(kind='link.create' if after_raw else 'link.remove', status='planned', path=str(leaf), skill=entry['skill'], target=entry['target'], source=after_raw))
            observations.append(dict(root=key, scope=scope, identity=c.identity(root), manifest=desired, manifest_path=str(manifest_path), manifest_bytes=c.digest(before_text.encode()) if before_text is not None else None, leaves=leaves))
            if key in unregister:
                c.set_consumer(after, root, None, scope)
            else:
                if key not in inactive:
                    next_record.update(last_manifest=desired, last_manifest_digest=c.digest(desired), last_source_revision=revision)
                c.set_consumer(after, root, next_record, scope)
            if desired != current and key not in inactive:
                files.append(dict(root=key, before=before_text, after=c.text_json(desired)))
                actions.append(dict(kind='manifest.write', status='planned', path=str(manifest_path)))
        except c.MaskError as error:
            blockers.append(error.as_dict())
    if after != state:
        actions.append(dict(kind='state.record', status='planned'))
        after['generation'] = state['generation'] + 1
    source_data = dict(root=str(source), revision=revision, dirty=dirty,
                       fingerprint=c.digest({key: value['fingerprint'] for key, value in sorted(packages.items())}))
    payload = dict(protocol=1, adapters=c.ADAPTERS, operation=operation, config=config, generation=state['generation'],
                   state=state, observations=observations, source=source_data, links=links, manifests=files,
                   register=sorted(register), unregister=sorted(unregister), keep_links=keep_links, register_only=register_only, inactive=sorted(inactive))
    if candidate:
        payload['transition'] = candidate.get('transition')
    return dict(applicable=not blockers, blockers=blockers, plan_hash=c.digest(payload), source=source_data,
                projects=[entry for entry in observations if entry['scope'] == 'project'],
                users=[entry for entry in observations if entry['scope'] == 'user'], actions=actions, would_change=bool(actions),
                intent=dict(operation=operation, selected=[str(root) for root in roots], links=links, manifests=files,
                            before_state=state, after_state=after, config=config))


def public_plan(planned, output):
    output['data'] = {key: value for key, value in planned.items() if key not in ('intent', 'actions', 'would_change')}
    output['actions'] = planned['actions']
    output['would_change'] = planned['would_change']
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
    return sorted(directories)


def make_pending(planned, home):
    import uuid
    intent = copy.deepcopy(planned['intent'])
    version = max(intent['before_state']['schema_version'], intent['after_state']['schema_version'])
    if 'controls' in intent:
        version = 3
    intent.update(schema_version=version, transaction_id=str(uuid.uuid4()), phase='prepared',
                  base_generation=intent['before_state']['generation'],
                  before_state_text=c.read_text(home / 'state.json', 'state', missing=True),
                  after_state_text=c.text_json(intent['after_state']),
                  directories=required_directories(intent))
    return intent


def validate_pending(pending, home):
    c.fields(pending, ('schema_version', 'transaction_id', 'phase', 'operation', 'base_generation', 'selected',
                      'links', 'manifests', 'before_state', 'after_state', 'config', 'before_state_text', 'after_state_text', 'directories'),
             ('git', 'launcher', 'controls'), 'recovery', versions=(1, 2, 3))
    if pending['operation'] not in {'ensure', 'ensure.deactivate', 'apply', 'project.register', 'project.unregister', 'project.set', 'project.require', 'project.unrequire', 'project.set-targets', 'user.register', 'user.unregister', 'user.set', 'user.require', 'user.unrequire', 'user.set-targets', 'update', 'self.update', 'self.install'}:
        c.fail('recovery.conflict', 'Unknown pending operation.', 8)
    if pending['operation'].startswith('ensure') and pending['schema_version'] != 3:
        c.fail('recovery.conflict', 'Readiness requires v3 control observations.', 8)
    for field in ('selected', 'links', 'manifests', 'directories'):
        if not isinstance(pending[field], list):
            c.fail('recovery.conflict', 'Invalid pending collection.', 8)
    if any(not isinstance(item, str) for item in pending['selected'] + pending['directories']) or any(not isinstance(item, dict) for item in pending['links'] + pending['manifests']):
        c.fail('recovery.conflict', 'Invalid pending collection item.', 8)
    if not isinstance(pending['transaction_id'], str) or pending['phase'] not in ('prepared', 'git_started', 'git_advanced'):
        c.fail('recovery.conflict', 'Invalid pending transaction identity or phase.', 8)
    if 'git' in pending:
        from mask_git import validate_git_intent
        validate_git_intent(pending['git'], pending['config'], Path(__file__).resolve().parent)
    before, after = c.state(pending['before_state']), c.state(pending['after_state'])
    if pending['schema_version'] != (3 if 'controls' in pending else max(before['schema_version'], after['schema_version'])):
        c.fail('recovery.conflict', 'Journal version disagrees with its states.', 8)
    if before['schema_version'] != after['schema_version'] and not (pending['operation'] == 'user.register' and before['schema_version'] == 1 and after['schema_version'] == 2):
        c.fail('recovery.conflict', 'Only user registration may upgrade the state schema.', 8)
    before_records, after_records = c.consumer_records(before), c.consumer_records(after)
    if type(pending['base_generation']) is not int or pending['base_generation'] != before['generation'] or after['generation'] not in (before['generation'], before['generation'] + 1):
        c.fail('recovery.conflict', 'Invalid pending generation.', 8)
    current_config = c.read_json(home / 'config.json', default={})
    if pending['config'] is None:
        if pending['operation'] not in ('self.install', 'self.update') or current_config:
            c.fail('recovery.conflict', 'Unexpected missing machine configuration.', 8)
    elif c.config(pending['config']) != c.config(current_config):
        c.fail('recovery.conflict', 'Machine configuration changed since the pending operation.', 8)
    source = Path(pending['config']['source']['root']) if pending['config'] else None
    if not isinstance(pending['selected'], list) or len(set(pending['selected'])) != len(pending['selected']):
        c.fail('recovery.conflict', 'Invalid pending project selection.', 8)
    selected = set(pending['selected'])
    if pending['schema_version'] == 3:
        from mask_ensure import validate_controls
        validate_controls(pending, home)
    if not selected <= before_records.keys() | after_records.keys():
        c.fail('recovery.conflict', 'Pending project is absent from recorded registry.', 8)
    if 'launcher' in pending:
        from mask_install import validate_launcher_intent
        validate_launcher_intent(pending)
    elif before['launchers'] != after['launchers']:
        c.fail('recovery.conflict', 'Link operations cannot change launcher ownership.', 8)
    for root in before_records.keys() | after_records.keys():
        if root in before_records and root in after_records and c.consumer_scope(before, root) != c.consumer_scope(after, root):
            c.fail('recovery.conflict', 'A journal cannot change a consumer scope.', 8)
        if root not in selected and before_records.get(root) != after_records.get(root):
            c.fail('recovery.conflict', 'Pending state changes an unselected project.', 8)
    allowed_directories = {str(Path(pending['launcher']['path']).parent)} if 'launcher' in pending else set()
    for key in selected:
        record = before_records.get(key) or after_records[key]
        # Explicit keep-links may abandon an unavailable root without effects.
        touches = any(entry.get('root') == key for entry in pending['links'] + pending['manifests'])
        if touches or pending['operation'] in ('project.register', 'user.register', 'ensure', 'ensure.deactivate'):
            selected_state = before if key in before_records else after
            c.registered_root(Path(key), record, c.consumer_scope(selected_state, key))
        for adapter in c.ADAPTERS.values():
            allowed_directories.update((str(Path(key) / Path(adapter).parent), str(Path(key) / adapter)))
    if not isinstance(pending['directories'], list) or not set(pending['directories']) <= allowed_directories:
        c.fail('recovery.conflict', 'Unsafe pending directory intent.', 8)
    for entry in pending['links']:
        c.fields(entry, ('root', 'relative', 'skill', 'target', 'before', 'after'), family='recovery')
        c.skill_id(entry['skill'])
        if entry['root'] not in selected or entry['target'] not in c.ADAPTERS or entry['relative'] != f"{c.ADAPTERS[entry['target']]}/{entry['skill']}":
            c.fail('recovery.conflict', 'Unsafe pending link path.', 8)
        leaf = Path(entry['root']) / entry['relative']
        for side in ('before', 'after'):
            raw = entry[side]
            if raw is not None and (not isinstance(raw, str) or normalized_link(leaf, raw) != source / 'skills' / entry['skill']):
                c.fail('recovery.conflict', 'Pending link points outside its configured package.', 8)
        for side, state in (('before', before), ('after', after)):
            record = c.consumer_records(state).get(entry['root'], {}).get('links', {}).get(entry['relative'])
            raw = entry[side]
            if raw is not None and (not record or record['link_text'] != raw):
                c.fail('recovery.conflict', 'Pending link disagrees with ownership state.', 8)
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
        if actual['type'] not in ('missing', 'symlink') or actual['link_text'] not in (entry['before'], entry['after']):
            c.fail('recovery.conflict', 'A pending link was replaced or edited.', 8, path=str(leaf))
    for entry in pending['manifests']:
        path = pending_manifest_path(pending, entry, home)
        if c.read_text(path, 'manifest') not in (entry['before'], entry['after']):
            c.fail('recovery.conflict', 'A pending manifest was edited.', 8, path=str(path))
    actual = c.read_text(home / 'state.json', 'state', missing=True)
    if actual not in (pending['before_state_text'], pending['after_state_text']):
        c.fail('recovery.conflict', 'Registry changed after the pending operation.', 8)


def set_link(entry, side):
    root = Path(entry['root'])
    leaf = root / entry['relative']
    c.parents_safe(root, leaf)
    actual = link_value(leaf)
    wanted = entry[side]
    if actual['type'] not in ('missing', 'symlink') or actual['link_text'] not in (entry['before'], entry['after']):
        c.fail('recovery.conflict', 'Link precondition changed immediately before effect.', 8, path=str(leaf))
    if actual['link_text'] == wanted:
        return
    if actual['type'] == 'symlink':
        leaf.unlink()
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
    if 'launcher' in pending:
        from mask_install import restore_launcher
        restore_launcher(pending, side)
        if inject:
            checkpoint('launcher')
    entries = pending['links'] if side == 'after' else reversed(pending['links'])
    for entry in entries:
        if 'controls' in pending:
            from mask_ensure import check_controls
            check_controls(pending, home)
        set_link(entry, side)
        if inject:
            checkpoint('link')
    for entry in pending['manifests']:
        path = pending_manifest_path(pending, entry, home)
        actual = c.read_text(path, 'manifest')
        if actual not in (entry['before'], entry['after']):
            c.fail('recovery.conflict', 'Manifest changed immediately before replacement.', 8)
        c.atomic_text(path, entry[side], actual)
        if inject:
            checkpoint('manifest')
    if 'controls' in pending:
        from mask_ensure import restore_controls
        restore_controls(pending, home, side)
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


def clear_pending(home, pending):
    path = home / 'pending.json'
    if c.read_json(path, 'recovery') != pending:
        c.fail('recovery.conflict', 'Pending journal changed before cleanup.', 8)
    path.unlink()


def execute(planned, home, output, *, pending=None):
    ensure_applicable(planned)
    if not planned['would_change'] and pending is None:
        return
    pending = pending or make_pending(planned, home)
    validate_pending(pending, home)
    if c.kind(home / 'pending.json') == 'missing':
        c.atomic_text(home / 'pending.json', c.text_json(pending), None)
    checkpoint('intent')
    try:
        restore(pending, home, 'after', inject=True)
        clear_pending(home, pending)
        output.update(changed=planned['would_change'], transaction='committed')
        for action in output['actions']:
            action['status'] = 'applied'
    except (Exception, KeyboardInterrupt) as error:
        if pending.get('git'):
            output.update(changed=True, transaction='partial')
            c.fail('recovery.required', 'Git update may have effects; inspect and complete recovery.', 8)
        try:
            restore(pending, home, 'before')
            clear_pending(home, pending)
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


def recover(home, output, mode):
    raw = c.read_text(home / 'pending.json', 'recovery', missing=True)
    if raw is None:
        output['data'] = dict(pending=None)
        return
    pending = c.parse_json(raw, 'recovery')
    validate_pending(pending, home)
    output['data'] = dict(pending=pending, recovery_mode=mode)
    if mode == 'inspect':
        return
    check_current(pending, home)
    if pending.get('git'):
        from mask_git import recover_git
        recover_git(pending, home, output, mode)
    if mode == 'complete':
        source = Path(pending['config']['source']['root']) if pending['config'] else None
        for key in pending['selected']:
            record = c.consumer_records(pending['after_state']).get(key)
            if record:
                identifiers = {link['skill'] for link in record['links'].values()} if pending['operation'] == 'ensure.deactivate' else record['last_manifest']['skills']
                for identifier in identifiers:
                    c.package(source, identifier)
    output['would_change'] = True
    if output['dry_run']:
        return
    try:
        restore(pending, home, 'after' if mode == 'complete' else 'before')
        clear_pending(home, pending)
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
    declaration = c.consumer_manifest(root, scope, home)
    if identifier not in declaration['skills'] or target not in declaration.get('targets', config['default_targets']):
        c.fail('target.unmanaged_link', 'Adoption requires a declared skill and enabled target.', 4)
    source = Path(config['source']['root'])
    package = c.package(source, identifier)
    expected = source / 'skills' / identifier
    if not Path(expected_source).is_absolute() or Path(expected_source).resolve() != expected:
        c.fail('target.unmanaged_link', 'Expected source does not match the configured package.', 4)
    relative = f'{c.ADAPTERS[target]}/{identifier}'
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
        c.consumer_records(after)[str(root)]['links'][relative] = dict(skill=identifier, target=target, link_text=current['link_text'])
        c.save_state(home, state, after)
        output.update(changed=True, transaction='committed')
