"""One bounded, authenticated MASK request per stdio process."""
from __future__ import annotations

import io
from pathlib import Path
import re
import struct
import sys
import threading
import time
import uuid

import mask_core as c
import mask_fleet as fleet
import mask_fleet_artifacts as artifacts
import mask_fs as fs
import mask_profiles as profiles
import mask_resolve as resolve
import mask_selection as selection
import mask_sources as sources
import mask_store as store
import mask_workflow as workflow

MAX_FRAME = 8 * 1024 * 1024
MAX_SCOPE_PACKAGES = 128
MAX_TTL = 300
FIELDS = ('schema_version', 'protocol', 'id', 'device', 'controller', 'epoch', 'sequence',
          'expires', 'revision', 'generation', 'action', 'payload')
RESPONSE_FIELDS = ('schema_version', 'protocol', 'id', 'device', 'controller', 'request_digest',
                   'status', 'data', 'error')
OPERATION_FIELDS = ('schema_version', 'id', 'device', 'controller', 'epoch', 'sequence', 'revision',
                    'generation', 'action', 'digest', 'scope', 'status', 'result')
OPERATION_OPTIONAL = ('contribution',)
OPERATION_STATES = {'prepare': {'prepared', 'canceled'}, 'apply': {'applied_verified', 'rolled_back', 'canceled'},
                    'cancel-request': {'cancel_recorded'}}
PAYLOADS = {'capabilities': (), 'inspect': ('scope',), 'prepare': ('scope',),
            'apply': ('scope', 'plan'), 'receipt': ('operation', 'digest'),
            'cancel-request': ('operation', 'digest')}


def invalid(message):
    c.fail('rpc.invalid', message, 4)


def digest(value):
    if not isinstance(value, str) or not resolve.SHA.fullmatch(value):
        invalid('Expected a full SHA-256 digest.')
    return value


def read_exact(stream, size):
    result = bytearray()
    while len(result) < size:
        chunk = stream.read(min(size - len(result), 65536))
        if not chunk:
            invalid('Incomplete RPC frame.')
        result.extend(chunk)
    return result


def read_frame(stream):
    length, = struct.unpack('!I', read_exact(stream, 4))
    if not 1 <= length <= MAX_FRAME:
        invalid('RPC frame length is outside the supported bound.')
    raw = read_exact(stream, length)
    if stream.read(1):
        invalid('Expected exactly one RPC frame.')
    try:
        message = c.parse_json(raw.decode('utf-8'), 'rpc')
        fleet.signed_bytes(message)
    except (UnicodeError, RecursionError):
        invalid('Frame must be bounded UTF-8 JSON.')
    return message


def frame(message):
    raw = fleet.signed_bytes(message)
    if not 1 <= len(raw) <= MAX_FRAME:
        invalid('RPC frame exceeds the supported bound.')
    return struct.pack('!I', len(raw)) + raw


def intent_shape(intent):
    c.fields(intent, FIELDS, family='rpc')
    if intent['protocol'] != fleet.PROTOCOL:
        c.fail('rpc.version_unsupported', 'The device requires mask.rpc.v1.', 4)
    for key in ('id', 'device', 'controller'):
        fleet.identifier(intent[key])
    for key in ('epoch', 'sequence', 'expires'):
        fleet.number(intent[key], minimum=1)
    fleet.number(intent['generation'])
    digest(intent['revision'])
    action = intent['action']
    if not isinstance(action, str) or action not in PAYLOADS:
        invalid('Unsupported RPC action.')
    payload = intent['payload']
    optional = {'prepare': ('acquire', 'artifacts', 'profile'), 'apply': ('profile',), 'inspect': ('rollout',)}.get(action, ())
    c.fields(payload, PAYLOADS[action], optional, family='rpc')
    if action == 'prepare' and payload.get('acquire', 'exact') not in ('cached', 'exact'):
        invalid('Unsupported exact artifact acquisition policy.')
    if 'scope' in payload:
        fleet.token(payload['scope'])
    if 'plan' in payload:
        digest(payload['plan'])
    if 'rollout' in payload and payload['rollout'] is not True:
        invalid('Rollout inspection requires a true marker.')
    if payload.get('profile') is not None:
        from mask_control import validate_profile
        validate_profile(payload['profile'])
    if 'operation' in payload:
        fleet.identifier(payload['operation'])
        digest(payload['digest'])
        if payload['operation'] == intent['id']:
            invalid('A query or cancellation cannot name itself.')
    return intent


def request(controller, device, policy, action, payload, *, revision, generation=0, sequence=None,
            operation=None, expires=None):
    intent = intent_shape(dict(schema_version=1, protocol=fleet.PROTOCOL, id=operation or uuid.uuid4().hex,
                              device=device['id'], controller=controller['id'], epoch=policy['epoch'],
                              sequence=policy['minimum_sequence'] if sequence is None else sequence,
                              expires=int(time.time()) + 120 if expires is None else expires, revision=revision,
                              generation=generation, action=action, payload=payload))
    return dict(intent=intent, signature=fleet.sign(intent, controller, fleet.INTENT))


def request_digest(intent):
    return c.digest(fleet.signed_bytes(intent))


def checked_response(raw, intent, device):
    packet = read_frame(io.BytesIO(raw))
    c.fields(packet, ('response', 'signature'), family='rpc')
    value = packet['response']
    c.fields(value, RESPONSE_FIELDS, family='rpc')
    expected = (fleet.PROTOCOL, intent['id'], device['id'], intent['controller'], request_digest(intent))
    if tuple(value[key] for key in ('protocol', 'id', 'device', 'controller', 'request_digest')) != expected:
        c.fail('rpc.response_mismatch', 'The device response does not bind to this request.', 4)
    fleet.verify(value, packet['signature'], device, fleet.RECEIPT)
    if value['status'] not in ('ok', 'refused') or not isinstance(value['data'], dict):
        invalid('Invalid signed device response.')
    if value['status'] == 'refused':
        c.fields(value['error'], ('code',), family='rpc')
        if not isinstance(value['error']['code'], str) or not re.fullmatch(r'[a-z0-9_.]{1,96}', value['error']['code']):
            invalid('Invalid signed refusal.')
    else:
        if value['error'] is not None:
            invalid('Unexpected error on a successful signed response.')
        check_operation_response(value['data'], intent)
    return value


def check_operation_response(data, intent):
    action = intent['action']
    if action == 'receipt':
        expected_id, expected_digest = intent['payload']['operation'], intent['payload']['digest']
        if data == dict(operation=expected_id, status='unknown'):
            return
    elif action in OPERATION_STATES:
        expected_id, expected_digest = intent['id'], request_digest(intent)
    else:
        return
    c.fields(data, OPERATION_FIELDS, OPERATION_OPTIONAL, family='rpc')
    if (data['id'], data['digest'], data['device'], data['controller']) != (
            expected_id, expected_digest, intent['device'], intent['controller']):
        c.fail('rpc.receipt_mismatch', 'Signed operation data does not bind to the requested receipt.', 4)
    recorded_action = data['action']
    status = data['status']
    if (not isinstance(recorded_action, str) or recorded_action not in OPERATION_STATES or
            not isinstance(status, str) or status not in OPERATION_STATES[recorded_action] | {'accepted'}):
        invalid('Unsupported durable operation state.')
    if action != 'receipt':
        if (recorded_action, data['epoch'], data['sequence'], data['revision'], data['generation']) != (
                action, intent['epoch'], intent['sequence'], intent['revision'], intent['generation']) or status == 'accepted':
            c.fail('rpc.receipt_mismatch', 'Signed operation revision, generation or status differs from the request.', 4)
        if status == 'applied_verified' and (not isinstance(data['result'], dict) or
                                             data['result'].get('plan') != intent['payload']['plan']):
            c.fail('rpc.receipt_mismatch', 'Signed application does not bind to the requested plan.', 4)


def current(intent, device, policy):
    if intent['device'] != device['id']:
        c.fail('fleet.device_mismatch', 'Request names a different enrolled device.', 4)
    if intent['controller'] != policy['controller']['id']:
        c.fail('fleet.controller_unknown', 'Request is from an unknown controller.', 4)
    if policy.get('revoked'):
        c.fail('fleet.controller_revoked', 'Controller authority was revoked.', 4)
    if intent['epoch'] != policy['epoch'] or intent['sequence'] < policy['minimum_sequence']:
        c.fail('fleet.epoch_stale', 'Intent does not meet the enrolled epoch and sequence floor.', 4)
    if intent['action'] not in policy['actions']:
        c.fail('fleet.action_denied', 'This action was not granted by the local owner.', 4)
    if 'scope' in intent['payload'] and intent['payload']['scope'] not in policy['scopes']:
        c.fail('fleet.scope_denied', 'This scope alias was not granted by the local owner.', 4)
    now = int(time.time())
    if not now < intent['expires'] <= now + MAX_TTL:
        c.fail('fleet.intent_expired', 'Intent expiry is stale or outside the allowed window.', 4)


def pending_guard(home):
    if c.kind(home / 'pending.json') != 'missing':
        c.fail('recovery.required', 'Recover the ordinary local MASK journal before retrying fleet effects.', 8)


def state_at(home):
    return c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))


def authorized_scope(home, intent, policy):
    alias = intent['payload']['scope']
    scope = policy['scopes'][alias]
    state = state_at(home)
    root, record = fleet.local_scope(scope, state)
    if record.get('dev_links'):
        c.fail('dev_link.active', 'Fleet cannot act on authoring links.', 4)
    config = c.config(c.read_json(home / 'config.json'))
    declaration, locked = resolve.read_exact_lock(root, scope['scope'], home, config, verify=False)
    subscriptions = record.get('profiles', {})
    layers = profiles.layers(declaration, locked, subscriptions)
    all_rows = [row for layer in layers for row in layer['lock']['packages']]
    old_rows = [link['resolution'] for link in record['links'].values()]
    if 'profile' in intent['payload']:
        if not scope.get('rollout'):
            c.fail('fleet.rollout_denied', 'The device did not grant desired profile changes in this scope.', 4)
        if declaration != record['last_manifest'] or locked != record['last_lock']:
            c.fail('fleet.local_drift', 'Reconcile local declaration and lock edits before fleet rollout.', 4)
        name = contribution_name(intent)
        previous = subscriptions.get(name)
        if previous and previous.get('fleet_controller') != intent['controller']:
            c.fail('fleet.profile_collision', 'A local profile already uses this contribution name.', 4)
        subscriptions = dict(subscriptions)
        desired = intent['payload']['profile']
        if desired is None:
            subscriptions.pop(name, None)
        else:
            subscriptions[name] = dict(desired, fleet_controller=intent['controller'])
        profiles.subscriptions(subscriptions)
        all_rows = desired['lock']['packages'] if desired else []
        old_rows = previous['lock']['packages'] if previous else []
        layers = [dict(origin='profile:' + name, declaration=desired['declaration'], lock=desired['lock'])] if desired else []
    elif intent['payload'].get('rollout'):
        if not scope.get('rollout'):
            c.fail('fleet.rollout_denied', 'The device did not grant desired profile changes in this scope.', 4)
        all_rows, old_rows = [], []
    if len(all_rows) > MAX_SCOPE_PACKAGES:
        c.fail('fleet.scope_limit', 'Scope exceeds the bounded fleet package count.', 4)
    for row in all_rows + old_rows:
        grant = scope['sources'].get(row['source'])
        local = sources.selected(config, row['source'])
        if not grant or grant['repository'] != sources.repository(row['repository']) or grant['repository'] != sources.repository(local['repository']):
            c.fail('fleet.source_denied', 'The exact source is outside the locally authorized fleet policy.', 4)
    return state, config, root, scope, layers, subscriptions


def contribution_name(intent):
    return 'fleet-' + intent['controller']


def state_view(state, root):
    record = c.consumer_records(state)[str(root)]
    bindings = [dict(coordinate=resolve.coordinate(link['resolution']), agent=link['target'],
                     commit=link['resolution']['commit'], payload_digest=link['resolution']['payload_digest'])
                for _, link in sorted(record['links'].items())]
    return dict(generation=state['generation'], scope_type=c.consumer_scope(state, root), bindings=bindings)


def operation_path(home, operation):
    return fleet.path(home, 'operations/' + fleet.identifier(operation))


def operation_record(intent):
    record = dict(schema_version=1, id=intent['id'], device=intent['device'], controller=intent['controller'],
                epoch=intent['epoch'], sequence=intent['sequence'], revision=intent['revision'],
                generation=intent['generation'], action=intent['action'], digest=request_digest(intent),
                scope=intent['payload'].get('scope'), status='accepted', result=None)
    if 'profile' in intent['payload']:
        profile = intent['payload']['profile']
        record['contribution'] = profile['revision'] if profile else None
    return record


def existing_operation(home, intent):
    record = fleet.data(operation_path(home, intent['id']), missing=True)
    if record and record['digest'] != request_digest(intent):
        c.fail('fleet.operation_conflict', 'The operation ID already binds different intent bytes.', 4)
    return record


def sequence_guard(home, intent, *, advance=False):
    path = fleet.path(home, 'high-water')
    previous = fleet.data(path, missing=True)
    value = dict(epoch=intent['epoch'], sequence=intent['sequence'], id=intent['id'], digest=request_digest(intent))
    if 'profile' in intent['payload']:
        path = fleet.path(home, 'scope-sequence-' + c.digest(intent['payload']['scope'].encode()).split(':')[1])
        previous = fleet.data(path, missing=True)
        value = dict(epoch=intent['epoch'], sequence=intent['sequence'], revision=intent['revision'])
    if previous is not None:
        order = (value['epoch'], value['sequence'])
        last = (previous['epoch'], previous['sequence'])
        if order < last or order == last and value != previous:
            c.fail('fleet.sequence_stale', 'Intent is below the durable fleet sequence high-water mark.', 4)
    if advance:
        fleet.put(path, value, previous)


def set_result(home, record, status, result):
    completed = dict(record, status=status, result=result)
    fleet.put(operation_path(home, record['id']), completed, record)
    return completed


def finish_receipt(home, intent, policy):
    """Finalize the exact after side only when ordinary effects are already present."""
    with c.writer_lock(home):
        if fleet.current_authority(home) != policy:
            c.fail('fleet.authority_changed', 'Fleet authority changed before receipt publication.', 4)
        pending = c.read_json(home / 'pending.json', 'recovery', default={})
        marker = pending.get('fleet', {}).get('before', {})
        if not pending:
            return
        target = intent['payload']
        if (marker.get('id'), marker.get('digest'), marker.get('controller'), marker.get('device')) != (
                target['operation'], target['digest'], intent['controller'], intent['device']):
            pending_guard(home)
        if marker.get('scope') not in policy['scopes']:
            c.fail('fleet.scope_denied', 'The recorded operation scope is no longer authorized.', 4)
        fs.check_current(pending, home)
        root, = map(Path, pending['selected'])
        after = c.consumer_records(pending['after_state'])[str(root)]
        retained = {root / rel: dict(type='symlink', link_text=link['link_text']) for rel, link in after['links'].items()}
        removed = {root / link['relative']: dict(type='missing', link_text=None)
                   for link in pending['links'] if link['after'] is None}
        for path in retained.keys() | removed.keys():
            c.parents_safe(root, path)
        if (c.read_text(home / 'state.json', 'state', missing=True) != pending['after_state_text'] or
                any(fs.link_value(path) != expected for path, expected in (retained | removed).items()) or
                any(workflow.current_text(entry) != entry['after'] for entry in pending.get('native_roles', []))):
            pending_guard(home)
        fs.check_final_controls(pending, home, 'after')
        restore_journal(home, pending, 'after')
        fs.clear_pending(home, pending)


def receipt(home, intent, policy=None):
    if policy is not None and c.kind(home / 'pending.json') != 'missing':
        finish_receipt(home, intent, policy)
    pending_guard(home)
    payload = intent['payload']
    target = fleet.data(operation_path(home, payload['operation']), missing=True)
    if target is None:
        return dict(operation=payload['operation'], status='unknown')
    if target['digest'] != payload['digest'] or target['controller'] != intent['controller'] or target['device'] != intent['device']:
        c.fail('fleet.receipt_mismatch', 'The durable receipt does not bind to the requested operation.', 4)
    if policy is not None and target['scope'] not in policy['scopes']:
        c.fail('fleet.scope_denied', 'The recorded operation scope is no longer authorized.', 4)
    pending_guard(home)
    return target


def cancel(home, intent):
    payload = intent['payload']
    target = fleet.data(operation_path(home, payload['operation']), missing=True)
    if not target:
        c.fail('fleet.operation_unknown', 'No accepted operation exists at the supplied ID.', 4)
    if (target['digest'], target['device'], target['controller'], target['epoch']) != (
            payload['digest'], intent['device'], intent['controller'], intent['epoch']):
        c.fail('fleet.receipt_mismatch', 'Cancellation does not bind to the accepted operation.', 4)
    if target['status'] == 'accepted':
        return set_result(home, target, 'canceled', dict(cancellation=intent['id']))
    return target


def plan_scope(home, state, config, root, intent, subscriptions):
    updating_profile = 'profile' in intent['payload']
    planned = fs.plan(config, state, [root], home=home,
                      profile_proposals={str(root): subscriptions} if updating_profile else None)
    fs.ensure_applicable(planned)
    if updating_profile:
        before = c.consumer_records(state)[str(root)]
        after = c.consumer_records(planned['intent']['after_state'])[str(root)]
        name = contribution_name(intent)
        allowed = {resolve.coordinate(row) for record in (before, after)
                   for row in record.get('profiles', {}).get(name, {}).get('lock', {}).get('packages', [])}
        if any(resolve.coordinate(link['resolution']) not in allowed
               for action in planned['intent']['links']
               for link in (before['links'].get(action['relative']), after['links'].get(action['relative'])) if link):
            c.fail('fleet.local_drift', 'Reconcile unrelated local links before changing the fleet profile.', 4)
    return planned


def commit_plan(home, intent, record, planned):
    """Commit a verified projection in the ordinary filesystem journal."""
    fs.ensure_applicable(planned, intent['payload']['plan'])
    pending = fs.make_pending(planned, home)
    root, = pending['selected']
    result = dict(state_view(pending['after_state'], root), plan=planned['plan_hash'],
                  changed=planned['would_change'], host_load='not_verified')
    if 'contribution' in record:
        origin = 'profile:' + contribution_name(intent)
        result['contribution'] = record['contribution']
        result['outcomes'] = [dict(coordinate=row['coordinate'], agent=row['agent'], status=row['status'],
                                   reason=row['reason']) for row in planned['outcomes'] if origin in row['origins']]
        before = c.consumer_records(pending['before_state'])[root].get('profiles', {}).get(origin.removeprefix('profile:'))
        result['changed'] = result['changed'] or (before['revision'] if before else None) != record['contribution']
        result['observed_at'] = int(time.time())
    committed = dict(record, status='applied_verified', result=result)
    pending['fleet'] = dict(before=record, after=committed)
    output = dict(data={}, actions=planned['actions'])
    fs.execute(planned, home, output, pending=pending)
    return committed


def validate_journal(pending):
    entry = pending['fleet']
    c.fields(entry, ('before', 'after'), family='recovery')
    before, after = entry['before'], entry['after']
    c.fields(before, OPERATION_FIELDS, OPERATION_OPTIONAL, family='recovery')
    for key in ('id', 'device', 'controller'):
        fleet.identifier(before[key])
    for key in ('digest', 'revision'):
        digest(before[key])
    fleet.number(before['epoch'], minimum=1)
    fleet.number(before['sequence'], minimum=1)
    fleet.token(before['scope'])
    c.fields(after, before.keys(), family='recovery')
    if any(pending.get(key) for key in ('git', 'controls', 'launcher', 'setup', 'retired_files', 'development', 'manifests', 'files')):
        c.fail('recovery.conflict', 'A fleet apply journal cannot change local controls or run setup.', 8)
    if pending['operation'] != 'apply' or len(pending['selected']) != 1 or before['action'] != 'apply' or before['status'] != 'accepted' or before['result'] is not None or before['generation'] != pending['base_generation']:
        c.fail('recovery.conflict', 'Fleet journal requires one accepted pinned apply.', 8)
    result = after['result']
    rollout = 'contribution' in before
    c.fields(result, ('generation', 'scope_type', 'bindings', 'plan', 'changed', 'host_load') +
             (('contribution', 'outcomes', 'observed_at') if rollout else ()), family='recovery')
    root, = pending['selected']
    old = c.consumer_records(pending['before_state'])[root].get('profiles', {})
    new = c.consumer_records(pending['after_state'])[root].get('profiles', {})
    changed = {name for name in old.keys() | new.keys() if old.get(name) != new.get(name)}
    if rollout:
        name = contribution_name(before)
        desired = new.get(name)
        revision = desired['revision'] if desired else None
        if (changed - {name} or revision != before['contribution'] or revision != result['contribution']
                or any(record and record.get('fleet_controller') != before['controller']
                       for record in (old.get(name), desired))):
            c.fail('recovery.conflict', 'Fleet journal changes another contribution or disagrees with the requested revision.', 8)
        if revision is not None:
            digest(revision)
        fleet.number(result['observed_at'], minimum=1)
        if not isinstance(result['outcomes'], list) or len(result['outcomes']) > MAX_SCOPE_PACKAGES * len(c.ADAPTERS):
            c.fail('recovery.conflict', 'Fleet outcomes exceed the journal bound.', 8)
    elif changed:
        c.fail('recovery.conflict', 'An ordinary fleet apply cannot change profile ownership.', 8)
    digest(result['plan'])
    observed = state_view(pending['after_state'], pending['selected'][0])
    if (after != dict(before, status='applied_verified', result=result) or result['host_load'] != 'not_verified' or
            type(result['changed']) is not bool or any(result[key] != val for key, val in observed.items())):
        c.fail('recovery.conflict', 'Fleet receipt disagrees with the journaled device projection.', 8)


def journal_record(pending, side):
    entry = pending['fleet']
    if side == 'after':
        return entry['after']
    return dict(entry['before'], status='rolled_back', result=None)


def check_journal(home, pending):
    before = pending['fleet']['before']
    current_record = fleet.data(operation_path(home, before['id']))
    if current_record not in (before, journal_record(pending, 'after'), journal_record(pending, 'before')):
        c.fail('recovery.conflict', 'Fleet operation record changed outside its pending journal.', 8)
    return current_record


def restore_journal(home, pending, side):
    current_record = check_journal(home, pending)
    wanted = journal_record(pending, side)
    fleet.put(operation_path(home, wanted['id']), wanted, current_record)


def prepare_artifacts(home, intent, scope_data):
    _, config, root, scope, layers, _ = scope_data
    if intent['payload'].get('acquire', 'exact') == 'exact':
        for row in artifacts.applicable_rows(layers):
            store_root, _ = store.location(home, row['payload_digest'], row['id'])
            entry = sources.selected(config, row['source'])
            if c.kind(store_root) != 'missing' or store.exact_cached(home, row, entry):
                continue
            remaining = intent['expires'] - int(time.time())
            if remaining < 1:
                c.fail('fleet.intent_expired', 'Intent expired before exact acquisition.', 4)
            sources.acquire_exact(home, row['source'], entry, row['commit'],
                                  min(config['git_timeout_seconds'], remaining, 10), {},
                                  consumer=root if scope['scope'] == 'project' else None)
    for layer in layers:
        declaration = layer['declaration']
        store.ensure(home, declaration, layer['lock'], config,
                     coordinates=selection.applicable_coordinates(declaration), offline=True)


def recheck_authority(home, intent, device, policy):
    actual = fleet.current_authority(home)
    current(intent, device, actual)
    if actual != policy or fleet.get_identity(home, 'device') != device:
        c.fail('fleet.authority_changed', 'Fleet authority changed while verifying the request.', 4)


def mutate(home, intent, device, policy):
    action = intent['action']
    with c.writer_lock(home):
        pending_guard(home)
        recheck_authority(home, intent, device, policy)
        previous = existing_operation(home, intent)
        if previous and previous['status'] != 'accepted':
            return previous
        sequence_guard(home, intent)
        if action == 'cancel-request':
            # An unrelated cancellation cannot consume authorization sequence.
            target = receipt(home, intent)
            if (target['status'] == 'unknown' or target['epoch'] != intent['epoch'] or
                    target['action'] not in ('prepare', 'apply') or target['scope'] not in policy['scopes']):
                c.fail('fleet.operation_unknown', 'No authorized operation exists at the supplied ID.', 4)
        else:
            scope_data = authorized_scope(home, intent, policy)
            state, config, root, scope, layers, subscriptions = scope_data
            if state['generation'] != intent['generation']:
                c.fail('fleet.generation_stale', 'Device generation changed since inspection.', 4)
        if action == 'prepare':
            incoming = artifacts.transfers(intent['payload'].get('artifacts', []), scope, layers)
        else:
            sequence_guard(home, intent, advance=True)
        record = previous or operation_record(intent)
        if previous is None:
            if action == 'cancel-request':
                record['scope'] = target['scope']
            fleet.put(operation_path(home, intent['id']), record, None)
        if action == 'cancel-request':
            return set_result(home, record, 'cancel_recorded', cancel(home, intent))
        if action == 'apply':
            return commit_plan(home, intent, record, plan_scope(home, state, config, root, intent, subscriptions))
        for row, payload in incoming:
            store.materialize(home, row, payload)
    # Ordinary lifecycle ownership protects retained artifacts from cleanup, but
    # no deployment writer lock is held while the approved Git transport waits.
    prepare_artifacts(home, intent, scope_data)
    with c.writer_lock(home):
        pending_guard(home)
        recheck_authority(home, intent, device, policy)
        if authorized_scope(home, intent, policy) != scope_data:
            c.fail('fleet.generation_stale', 'Device selection or source authority changed during exact preparation.', 4)
        planned = plan_scope(home, state, config, root, intent, subscriptions)
        result = dict(scope=intent['payload']['scope'], generation=state['generation'],
                      plan=planned['plan_hash'], would_change=planned['would_change'])
        return set_result(home, record, 'prepared', result)


def perform(home, intent, device, policy):
    action = intent['action']
    if action == 'capabilities':
        return dict(device=fleet.public(device), authority=fleet.public_authority(policy), generation=state_at(home)['generation'],
                    adapters=selection.read_policy(home)[0]['enabled_agents'], max_frame=MAX_FRAME,
                    max_transfer=artifacts.MAX_TRANSFER, signing_provider='openssh-sshsig-ed25519')
    if action == 'receipt':
        return receipt(home, intent, policy)
    if action == 'inspect':
        state, _, root, _, _, _ = authorized_scope(home, intent, policy)
        return dict(state_view(state, root), scope=intent['payload']['scope'],
                    recovery_required=c.kind(home / 'pending.json') != 'missing')
    with c.writer_lock(home, name='lifecycle.lock'):
        return mutate(home, intent, device, policy)


def response_value(intent, device, data):
    return dict(schema_version=1, protocol=fleet.PROTOCOL, id=intent['id'], device=device['id'],
                controller=intent['controller'], request_digest=request_digest(intent), status='ok', data=data, error=None)


def reply(home, packet):
    c.fields(packet, ('intent', 'signature'), family='rpc')
    intent = intent_shape(packet['intent'])
    device = fleet.get_identity(home, 'device')
    result = response_value(intent, device, {})
    try:
        policy = fleet.current_authority(home)
        current(intent, device, policy)
        fleet.verify(intent, packet['signature'], policy['controller'], fleet.INTENT)
        if fleet.current_authority(home) != policy:
            c.fail('fleet.authority_changed', 'Fleet authority changed while verifying the request.', 4)
        result['data'] = perform(home, intent, device, policy)
    except c.MaskError as error:
        result.update(status='refused', error=dict(code=error.code))
    except OSError:
        result.update(status='refused', error=dict(code='filesystem.failed'))
    return dict(response=result, signature=fleet.sign(result, device, fleet.RECEIPT))


def read_stdin(stream, timeout=12):
    value, errors = [], []

    def read():
        try:
            value.append(read_frame(stream))
        except (OSError, c.MaskError) as error:
            errors.append(error)

    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    reader.join(timeout)
    if reader.is_alive():
        c.fail('rpc.read_timeout', 'Timed out reading a complete RPC frame.', 4)
    if errors:
        raise errors[0]
    return value[0]


def stdio(home):
    try:
        source = getattr(sys.stdin.buffer, 'raw', sys.stdin.buffer)
        result = frame(reply(home, read_stdin(source)))
        sys.stdout.buffer.write(result)
        sys.stdout.buffer.flush()
    except (c.MaskError, OSError) as error:
        code = error.code if isinstance(error, c.MaskError) else 'rpc.io_failed'
        sys.stderr.write(f'MASK RPC failed ({code}).\n')
        return 4
    return 0
