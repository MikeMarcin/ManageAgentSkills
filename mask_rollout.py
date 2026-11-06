"""Controller planning, delivery and observation for approved skill rollouts."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
from pathlib import Path
import tempfile
from types import SimpleNamespace
import time

import mask_control as control
import mask_core as c
import mask_fleet as fleet
import mask_fleet_artifacts as artifacts
import mask_profiles as profiles
import mask_resolve as resolve
import mask_rpc as rpc
import mask_sources as sources
import mask_store as store
import mask_transport as transport

TERMINAL = {'applied_verified', 'not_applicable', 'canceled', 'superseded'}
CONVERGED = {'applied_verified', 'not_applicable'}
DISCONNECTED = {'fleet.transport_unknown', 'fleet.response_unverified'}


def choose_devices(args, home):
    names = getattr(args, 'device', [])
    if bool(names) == bool(getattr(args, 'all_devices', False)):
        c.fail('invocation.invalid', 'Select --all-devices or one or more --device NAME values.', 2)
    if len(set(names)) != len(names):
        c.fail('invocation.invalid', 'Device names must be unique.', 2)
    peers = [transport.peer_at(home, name) for name in sorted(names)] if names else transport.peers(home)
    if not peers or len(peers) > control.MAX_DEVICES:
        c.fail('fleet.device_limit', 'Select between one and 64 enrolled active devices.', 4)
    return peers


def binding_digest(peer):
    return c.digest(transport.view(peer))


def frozen_target(peer, args, signer):
    alias = getattr(args, 'project_alias', None)
    scope_type = getattr(args, 'scope', None)
    if not (scope_type == 'user' and alias is None or scope_type in (None, 'project') and alias):
        c.fail('invocation.invalid', 'Use --scope user or --project-alias ALIAS.', 2)
    granted = peer['authority']['scopes']
    if alias:
        fleet.token(alias)
        scope_type = 'project'
    else:
        users = [name for name, scope in granted.items() if scope['scope'] == 'user']
        alias = 'user' if 'user' in users or len(users) != 1 else users[0]
    target = dict(name=peer['name'], device=peer['device']['id'], device_epoch=peer['authority']['epoch'],
                  scope=alias, scope_type=scope_type, profile=None, identity=peer['device'], binding=binding_digest(peer))
    scope = granted.get(alias)
    if fleet.public(signer) != peer['authority']['controller']:
        target['blocked'] = 'fleet.controller_changed'
    elif scope is None or scope['scope'] != scope_type:
        target['blocked'] = 'fleet.scope_unmapped'
    elif not scope.get('rollout') or not {'inspect', 'prepare', 'apply', 'receipt'} <= set(peer['authority']['actions']):
        target['blocked'] = 'fleet.rollout_denied'
    return target


def resolve_input(home, config, name, *, ref=None, path=None):
    if name.startswith('https://'):
        inspected = dict(dry_run=True, data={})
        sources.inspect(SimpleNamespace(url=name, ref=ref, path=path), inspected, home)
        data = inspected['data']
        if data['resolution_required']:
            c.fail('lock.resolution_required', 'Fetch the already approved tap explicitly before planning a fleet rollout.', 4)
        found = data['skills']
        selected_ref = data['ref']
    else:
        if ref is not None or path is not None:
            c.fail('invocation.invalid', '--ref and --path apply to a GitHub URL.', 2)
        source_name, sep, identifier = name.partition('/')
        if sep:
            resolve.qualified(name, 'fleet')
            selected = {source_name: sources.selected(config, source_name)}
        else:
            c.skill_id(source_name)
            identifier, selected = source_name, config['sources']
        found, selected_ref = [], None
        for alias, entry in sorted(selected.items()):
            cache = sources.cached(home, alias, entry)
            refs = sources.cached_refs(cache, entry) if cache else None
            if not refs:
                c.fail('lock.resolution_required', 'Fetch configured taps before resolving a bare skill name.', 4, source=alias)
            commit = c.peeled_commit(cache, sources.resolve_ref(refs, entry['ref']))
            if commit is None:
                c.fail('lock.resolution_required', 'The selected tap revision is unavailable in the cache.', 4, source=alias)
            found.extend(row for row in sources.discover(cache, alias, entry, commit, identifier=identifier)
                         if row['id'] == identifier)
    if len(found) != 1:
        c.fail('fleet.selection_required', 'Select exactly one skill from the already approved taps.', 4,
               choices=[{key: row[key] for key in ('coordinate', 'repository', 'path', 'commit')} for row in found[:32]])
    row, = found
    entry = sources.selected(config, row['source'])
    selector = selected_ref or entry['ref']
    cache = sources.cached(home, row['source'], entry)
    if resolve.OID.fullmatch(selector):
        chosen = {'commit': row['commit']}
    else:
        chosen = resolve.machine_selector(cache, dict(entry, ref=selector))
    return exact_row(cache, row, chosen)


def exact_row(cache, row, chosen):
    result = {key: row[key] for key in ('source', 'id', 'repository', 'path', 'commit')}
    result['repository'] = sources.repository(result['repository'])
    result.update(selector=chosen, git_object_format=c.git(cache, 'rev-parse', '--show-object-format'))
    result.update(resolve.payload_digests(resolve.frozen_payload(cache, result)))
    return result


def update_row(home, config, coordinate, chosen):
    name, identifier = coordinate.split('/', 1)
    entry = sources.selected(config, name)
    declaration = dict(schema_version=2, sources={name: dict(repository=entry['repository'], packages=entry['packages'])},
                       skills=[dict(source=name, id=identifier, version=chosen)])
    return resolve.resolve_binding(home, declaration, declaration['skills'][0], entry)


def contribution(previous, coordinate, action, row, config):
    declaration = previous['declaration'] if previous else dict(schema_version=2, sources={}, default_agents='all', skills=[])
    packages = {resolve.coordinate(item): item for item in previous['lock']['packages']} if previous else {}
    bindings = {resolve.coordinate(item): item for item in declaration['skills']}
    old = bindings.get(coordinate)
    if action == 'update' and old is None:
        return previous, 'fleet.skill_not_selected'
    if action == 'update' and (old.get('pinned') or 'commit' in packages[coordinate]['selector']):
        return previous, None
    if action == 'update' and packages[coordinate]['selector'] != row['selector']:
        return previous, 'fleet.selector_changed'
    if action == 'install' and old is not None and packages[coordinate] != row:
        return previous, 'fleet.skill_already_selected'
    if action == 'remove':
        bindings.pop(coordinate, None)
        packages.pop(coordinate, None)
    else:
        source_name = row['source']
        packages[coordinate] = row
        if old is None:
            bindings[coordinate] = dict(source=source_name, id=row['id'], version=row['selector'])
    if not bindings:
        return None, None
    required = {item['source'] for item in bindings.values()}
    entries = {name: item for name, item in declaration['sources'].items() if name in required}
    for name in required - entries.keys():
        entry = sources.selected(config, name)
        entries[name] = dict(repository=sources.repository(entry['repository']), packages=entry['packages'])
    result, lock = profiles.pair(dict(declaration, sources=entries, skills=list(bindings.values())), packages.values())
    return control.desired_profile(result, lock), None


def validate_sources(target, peer, allow_forward):
    profile = target['profile']
    if not profile:
        return
    if len(fleet.signed_bytes(profile)) > fleet.RECORD_BYTES // 2:
        target['blocked'] = 'fleet.profile_limit'
        return
    grants = peer['authority']['scopes'][target['scope']]['sources']
    for row in profile['lock']['packages']:
        grant = grants.get(row['source'])
        if grant is None or grant['repository'] != row['repository']:
            target['blocked'] = 'fleet.source_denied'
            return
        if allow_forward and not grant['forward']:
            target['blocked'] = 'fleet.artifact_forward_denied'
            return


def peer_for(home, target, signer):
    peer = transport.peer_at(home, target['name'])
    if (peer['device']['id'] != target['device'] or peer['authority']['epoch'] != target['device_epoch']
            or peer['authority']['controller'] != fleet.public(signer) or binding_digest(peer) != target.get('binding')):
        c.fail('fleet.binding_changed', 'Enrolled identity, scope or transport changed after plan approval.', 4)
    return peer


def outcome_path(home, entry, target):
    return fleet.path(home, 'deliveries/' + entry['operation'] + '-' + target['device'])


def base_result(target):
    return dict(name=target['name'], device_id=target['device'], scope=target['scope'], scope_type=target['scope_type'],
                status='queued_offline', host_load='not_verified', bindings=[], outcomes=[])


def proof_result(record, entry, target):
    proof = record.get('proof')
    if not proof:
        return None
    original = record['apply']['intent']
    wanted = target['profile']['revision'] if target['profile'] else None
    if (original['device'], original['epoch'], original['sequence'], original['revision'], original['payload']['scope']) != (
            target['device'], target['device_epoch'], entry['sequence'], control.intent_digest(entry), target['scope']):
        c.fail('fleet.receipt_mismatch', 'Recorded apply request does not match the approved desired revision.', 4)
    if original['payload'].get('profile') != target['profile']:
        c.fail('fleet.receipt_mismatch', 'Recorded apply request does not match the approved exact profile.', 4)
    query = proof['intent']
    if query != original and (query['action'] != 'receipt' or query['payload'] != dict(
            operation=original['id'], digest=rpc.request_digest(original))):
        c.fail('fleet.receipt_mismatch', 'Receipt query does not name the approved apply request.', 4)
    response = rpc.checked_response(rpc.frame(proof['packet']), query, target['identity'])
    data = response['data']
    if response['status'] != 'ok' or data.get('status') != 'applied_verified':
        return None
    result = data['result']
    if (data['revision'], data['sequence'], data['epoch'], data['scope'], data.get('contribution'), result.get('contribution'),
            result.get('scope_type'), result.get('plan')) != (
            original['revision'], entry['sequence'], target['device_epoch'], target['scope'], wanted, wanted,
            target['scope_type'], original['payload']['plan']):
        c.fail('fleet.receipt_mismatch', 'Signed outcome does not match the exact approved revision, scope or plan.', 4)
    for row in result['outcomes']:
        if row['status'] not in ('selected', 'overridden'):
            continue
        package = next((item for item in target['profile']['lock']['packages']
                        if resolve.coordinate(item) == row['coordinate']), None)
        if package is None or not any((edge['coordinate'], edge['agent'], edge['payload_digest']) ==
                                      (row['coordinate'], row['agent'], package['payload_digest']) for edge in result['bindings']):
            c.fail('fleet.receipt_mismatch', 'Signed filesystem projection lacks a requested exact binding.', 4)
    skipped = bool(result['outcomes']) and not any(row['status'] in ('selected', 'overridden') for row in result['outcomes'])
    return dict(base_result(target), status='not_applicable' if skipped else 'applied_verified',
                bindings=result['bindings'], outcomes=result['outcomes'], changed=result['changed'],
                observed_at=result['observed_at'], generation=result['generation'], intent_digest=data['revision'],
                receipt_operation=data['id'], receipt_digest=c.digest(proof['packet']))


def response(home, signer, target, entry, action, payload, *, timeout, generation=0, packet=None):
    peer = peer_for(home, target, signer)
    if packet is None:
        expiry = int(time.time()) + 120
        if action in ('prepare', 'apply'):
            expiry = min(expiry, entry['expires'])
        packet = rpc.request(signer, peer['device'], peer['authority'], action, payload, generation=generation,
                             revision=control.intent_digest(entry), sequence=entry['sequence'], expires=expiry)
    envelope = transport.exchange(peer, packet, timeout=timeout, signed=True)
    observed = envelope['response']
    if observed['status'] != 'ok':
        code = observed['error']['code']
        c.fail(code, 'The device refused the signed rollout request.', 4)
    return observed['data'], dict(intent=packet['intent'], packet=envelope)


def forward_packages(home, target):
    profile = target['profile']
    if not profile:
        return []
    config = c.config(c.read_json(home / 'config.json'))
    result = []
    total = 0
    for row in profile['lock']['packages']:
        payload = store.cached_payload(home, row, config)
        if payload is None:
            try:
                payload = store.verify(home, row, as_payload=True)
            except c.MaskError as error:
                if error.code not in ('artifact.unavailable', 'artifact.missing'):
                    raise
                entry = sources.selected(config, row['source'])
                sources.acquire_exact(home, row['source'], entry, row['commit'], config['git_timeout_seconds'], {})
                payload = store.cached_payload(home, row, config)
                if payload is None:
                    c.fail('artifact.unavailable', 'The approved exact forwarding payload is unavailable.', 4)
        total += payload.total_bytes
        if total > artifacts.MAX_TRANSFER or len(result) >= artifacts.MAX_PACKAGES:
            c.fail('fleet.artifact_limit', 'The selected packages exceed the aggregate forwarding bound.', 4)
        result.append(artifacts.packet(home, row, payload=payload))
    return result


def save_proof(path, record, proof, entry, target):
    candidate = dict(record, proof=proof)
    result = proof_result(candidate, entry, target)
    if result:
        fleet.put(path, candidate, record)
    return result


def deliver(home, signer, history, entry, target, *, timeout=15, observe_only=False):
    base = base_result(target)
    path = outcome_path(home, entry, target)
    if 'blocked' in target:
        return dict(base, status='blocked', reason=target['blocked'])
    suffix = target['device'] + '-' + target['scope']
    try:
        # A device lane serializes retries without holding the ordinary MASK writer lock.
        with c.writer_lock(home, name='fleet-delivery-' + suffix + '.lock'):
            record = fleet.data(path, missing=True)
            if record:
                verified = proof_result(record, entry, target)
                if verified:
                    return verified
                original = record['apply']['intent']
                query = dict(operation=original['id'], digest=rpc.request_digest(original))
                _, proof = response(home, signer, target, entry, 'receipt', query, timeout=timeout)
                verified = save_proof(path, record, proof, entry, target)
                if verified:
                    return verified
            latest = history.effective().get(control.target_key(target))
            if latest and latest[0] != entry:
                status = 'canceled' if latest[0]['action'] == 'cancel' and latest[0]['input']['operation'] == entry['operation'] else 'superseded'
                return dict(base, status=status, superseding_operation=latest[0]['operation'])
            if observe_only:
                return dict(base, status='unknown' if record else 'queued_offline')
            if entry['expires'] <= int(time.time()):
                return dict(base, status='blocked', reason='fleet.intent_expired')
            peer = peer_for(home, target, signer)
            if entry['sequence'] < peer['authority']['minimum_sequence']:
                c.fail('fleet.sequence_stale', 'Desired revision predates the enrolled sequence floor.', 4)
            observed, _ = response(home, signer, target, entry, 'inspect',
                                   dict(scope=target['scope'], rollout=True), timeout=timeout)
            if observed['recovery_required']:
                return dict(base, status='recovery_required', reason='recovery.required')
            payload = dict(scope=target['scope'], profile=target['profile'])
            preparation = dict(payload)
            if entry['input'].get('forward'):
                preparation['artifacts'] = forward_packages(home, target)
            prepared, _ = response(home, signer, target, entry, 'prepare', preparation,
                                   generation=observed['generation'], timeout=timeout)
            if prepared['status'] != 'prepared':
                c.fail('fleet.prepare_refused', 'The device did not return a prepared exact plan.', 4)
            payload['plan'] = prepared['result']['plan']
            if control.remote_head(history.root, history.control) != history.head:
                c.fail('fleet.control_conflict', 'Desired head changed during preparation. Run fleet sync for its latest state.', 4)
            packet = rpc.request(signer, target['identity'], peer['authority'], 'apply', payload,
                                 generation=observed['generation'], revision=control.intent_digest(entry),
                                 sequence=entry['sequence'], expires=min(entry['expires'], int(time.time()) + 120))
            candidate = dict(apply=packet, proof=None)
            fleet.put(path, candidate, record)
            _, proof = response(home, signer, target, entry, 'apply', payload, timeout=timeout, packet=packet)
            result = save_proof(path, candidate, proof, entry, target)
            return result or dict(base, status='unknown', reason='fleet.receipt_unavailable')
    except c.MaskError as error:
        if error.code in DISCONNECTED:
            return dict(base, status='unknown' if fleet.data(path, missing=True) else 'queued_offline', reason=error.code)
        return dict(base, status='recovery_required' if error.code == 'recovery.required' else 'blocked', reason=error.code)
    except OSError:
        return dict(base, status='unknown', reason='filesystem.failed')


def set_report(output, entry, rows):
    complete = all(row['status'] in CONVERGED for row in rows)
    installed = entry['action'] in ('install', 'update') and all(
        row['status'] == 'applied_verified' and any(item['coordinate'] == entry['input']['coordinate']
                                                  for item in row['bindings'])
        and all(item['status'] in ('selected', 'overridden') or item['reason'] in ('agent_disabled_by_policy', 'advertised_agents')
                for item in row['outcomes'] if item['coordinate'] == entry['input']['coordinate'])
        for row in rows)
    output['data'].update(operation_id=entry['operation'], action=entry['action'], desired_revision=control.intent_digest(entry),
                          sequence=entry['sequence'], input=entry['input'], selected_devices=len(rows), device_results=rows,
                          complete=complete, installed_everywhere=installed, host_load='not_verified')


def fanout(home, signer, history, pairs, *, timeout):
    with ThreadPoolExecutor(max_workers=min(4, max(1, len(pairs)))) as executor:
        return list(executor.map(lambda pair: deliver(home, signer, history, *pair, timeout=timeout), pairs))


def require_complete(output):
    if not output['data']['complete']:
        c.fail('fleet.incomplete', 'Some devices have not verified the requested exact rollout.', 9)


def rollout(home, signer, history, args, output, stack):
    action = args.command.rsplit('.', 1)[-1]
    config = c.config(c.read_json(home / 'config.json'))
    peers = choose_devices(args, home)
    targets = [frozen_target(peer, args, signer) for peer in peers]
    effective = history.effective()
    previous_profiles = {key: target['profile'] for key, (_, target) in effective.items()}
    copy = None
    source_effect = upstream = None
    if action == 'install':
        mode = getattr(args, 'mode', None) or history.control.get('import_mode')
        if mode not in ('tap', 'copy'):
            c.fail('fleet.mode_required', 'Choose --mode tap or --mode copy, or configure a reviewed default.', 4)
        row = resolve_input(home, config, args.input, ref=getattr(args, 'ref', None), path=getattr(args, 'path', None))
        if mode == 'copy':
            import mask_fleet_copy as copy
            upstream = row
            scratch = Path(stack.enter_context(tempfile.TemporaryDirectory(prefix='mask-fleet-copy-')))
            row, source_effect, endpoint, observed = copy.prepare(home, config, upstream, getattr(args, 'into', None), scratch)
        elif hasattr(args, 'into'):
            c.fail('invocation.invalid', '--into names the curated destination in copy mode.', 2)
        coordinate = resolve.coordinate(row)
    else:
        mode = None
        coordinate = args.input
        resolve.qualified(coordinate, 'fleet')
        row = None
        if action == 'update':
            selectors = set()
            for target in targets:
                previous = previous_profiles.get(control.target_key(target))
                if not previous or 'blocked' in target:
                    continue
                held = {resolve.coordinate(binding) for binding in previous['declaration']['skills'] if binding.get('pinned')}
                selectors.update(row['selector']['ref'] for row in previous['lock']['packages']
                                 if resolve.coordinate(row) == coordinate and coordinate not in held and 'ref' in row['selector'])
            if len(selectors) > 1:
                c.fail('fleet.selector_ambiguous', 'Selected devices track different refs for this skill. Select them separately.', 4,
                       choices=sorted(selectors))
            if selectors:
                row = update_row(home, config, coordinate, {'ref': selectors.pop()})
    forward = getattr(args, 'forward', False)
    details = dict(input=args.input, coordinate=coordinate, mode=mode, forward=forward, resolution=row)
    if upstream is not None:
        details['upstream'] = upstream
    for peer, target in zip(peers, targets):
        if 'blocked' in target:
            continue
        previous = previous_profiles.get(control.target_key(target))
        target['profile'], blocker = contribution(previous, coordinate, action, row, config)
        if blocker:
            target['blocked'] = blocker
        else:
            validate_sources(target, peer, forward)
    proposal = dict(head=history.head, epoch=history.control['epoch'], action=action,
                    targets=sorted(targets, key=control.target_key), input=details, source_effect=source_effect)
    plan_hash = c.digest(proposal)
    operation = plan_hash.split(':')[1][:32]
    output['data'].update(plan_hash=plan_hash, operation_id=operation, action=action, input=details,
                          targets=proposal['targets'],
                          source_publication=dict(source_effect, status='planned') if source_effect else None,
                          control_publication='planned')
    output['would_change'] = any('blocked' not in target for target in targets)
    if output['dry_run']:
        return
    if getattr(args, 'approve_plan', None) != plan_hash:
        c.fail('confirmation.required', 'Preview the exact fleet intent and pass its --approve-plan hash.', 4)
    if not output['would_change']:
        output['data'].update(device_results=[dict(base_result(target), status='blocked', reason=target['blocked'])
                                              for target in targets], complete=False, installed_everywhere=False,
                              control_publication='not_attempted')
        require_complete(output)
    if copy is not None:
        output['data']['source_publication']['status'] = 'attempted'
        phase = copy.publish(config, scratch, row, source_effect, endpoint, observed)
        output['data']['source_publication']['status'] = phase
        output.update(changed=phase == 'published', transaction='committed' if phase == 'published' else 'not_started')
    entry = control.event(history.control, signer, history.events, action, operation, targets, details, source_effect)
    output['data'].update(control_commit=control.publish(history, entry, signer), control_publication='published')
    output.update(changed=True, transaction='committed')
    control.remember(home, history)
    rows = fanout(home, signer, history, [(entry, target) for target in entry['targets']], timeout=timeout_option(args))
    set_report(output, entry, rows)
    require_complete(output)


def timeout_option(args):
    timeout = getattr(args, 'timeout', 15)
    if not 1 <= timeout <= 180:
        c.fail('invocation.invalid', 'Choose an SSH timeout from 1 through 180 seconds.', 2)
    return timeout


def sync(home, signer, history, args, output):
    peers = choose_devices(SimpleNamespace(device=getattr(args, 'device', []), all_devices=getattr(args, 'all', False)), home)
    selected = {peer['device']['id'] for peer in peers}
    pairs = [(entry, target) for entry, target in history.effective().values()
             if target['device'] in selected and entry['action'] != 'cancel']
    pairs.sort(key=lambda pair: (pair[1]['name'], pair[1]['scope']))
    control.remember(home, history)
    rows = fanout(home, signer, history, pairs, timeout=timeout_option(args))
    complete = all(row['status'] in CONVERGED for row in rows)
    output['data'].update(device_results=rows, complete=complete, selected_devices=len(selected),
                          installed_everywhere=False, host_load='not_verified',
                          operation_ids=sorted({entry['operation'] for entry, _ in pairs}))
    output['changed'] = any(row.get('changed') for row in rows)
    if output['changed']:
        output['transaction'] = 'committed'
    require_complete(output)


def operation_status(home, signer, history, args, output):
    operation = fleet.identifier(args.operation)
    entry = history.operation(operation)
    if entry is None or entry['action'] == 'cancel':
        c.fail('fleet.operation_unknown', 'The signed history does not contain that rollout operation.', 4)
    rows = []
    latest = history.effective()
    for target in entry['targets']:
        row = base_result(target)
        replacement = latest.get(control.target_key(target))
        record = fleet.data(outcome_path(home, entry, target), missing=True)
        if record and (verified := proof_result(record, entry, target)):
            row = verified
        elif 'blocked' in target:
            row.update(status='blocked', reason=target['blocked'])
        elif replacement and replacement[0] != entry:
            superseding = replacement[0]
            canceled = superseding['action'] == 'cancel' and superseding['input']['operation'] == operation
            row.update(status='canceled' if canceled else 'superseded', superseding_operation=superseding['operation'])
        elif record:
            row['status'] = 'unknown'
        rows.append(row)
    set_report(output, entry, rows)


def dispatch(args, output, home):
    signer = fleet.get_identity(home, 'controller')
    settings = control.settings(home, missing=True)
    if settings is None:
        c.fail('fleet.control_required', 'Configure an explicitly approved private Git control repository first.', 4)
    command = args.command
    if command != 'fleet.operation.show':
        timeout_option(args)
    with ExitStack() as stack:
        history = stack.enter_context(control.snapshot(home, settings, signer))
        if command == 'fleet.sync':
            return sync(home, signer, history, args, output)
        if command == 'fleet.operation.show':
            return operation_status(home, signer, history, args, output)
        return rollout(home, signer, history, args, output, stack)
