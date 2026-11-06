"""Reviewed fleet catalog changes using the existing signed maintenance transport."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
import time

import mask_core as c
import mask_fleet as fleet
import mask_fleet_maintenance as maintenance
import mask_rollout as rollout
import mask_rpc as rpc
import mask_sources as sources
import mask_transport as transport


def validate_change(change):
    c.fields(change, ('kind', 'name'), ('repository', 'ref', 'packages'), 'rpc', versions=())
    sources.alias(change['name'])
    if change['kind'] == 'add' and set(change) == {'kind', 'name', 'repository', 'ref', 'packages'}:
        if fleet.tap_repository(change['repository']) != change['repository']:
            rpc.invalid('A tap change requires a canonical repository identity.')
        sources.selector(change['ref'])
        sources.package_path(change['packages'])
    elif change['kind'] != 'remove' or set(change) != {'kind', 'name'}:
        rpc.invalid('Expected an exact tap addition or removal.')


def validate_payload(action, payload):
    if action == 'tap-apply':
        rpc.digest(payload['observed'])
    if payload['change'] is not None or action == 'tap-apply':
        validate_change(payload['change'])


def summary(entry):
    if entry is None:
        return None
    return {key: entry[key] for key in ('repository', 'ref', 'packages', 'fleet_owner') if key in entry}


def validate_summary(side):
    if side is not None:
        c.fields(side, ('repository', 'ref', 'packages'), ('fleet_owner',), 'fleet', versions=())
        sources.spelling(side['repository'])
        sources.selector(side['ref'])
        sources.package_path(side['packages'])
        if 'fleet_owner' in side:
            fleet.identifier(side['fleet_owner'])


def validate_receipt(value):
    c.fields(value, ('operation', 'plan', 'name', 'status', 'before', 'after', 'changed'),
             family='fleet', versions=())
    rpc.digest(value['operation'])
    rpc.digest(value['plan'])
    sources.alias(value['name'])
    validate_summary(value['before'])
    validate_summary(value['after'])
    if value['status'] != 'applied_verified' or value['changed'] is not (value['before'] != value['after']):
        fleet.invalid('Invalid fleet tap result.')
    return value


def catalog_at(home):
    raw = c.read_text(home / 'config.json', missing=True)
    return raw, c.config(c.parse_json(raw)) if raw is not None else c.empty_config()


def candidate(home, config, change, owner, *, policy=None):
    name = change['name']
    before = config['sources'].get(name)
    owned = before is not None and before.get('fleet_owner') == owner
    if change['kind'] == 'add':
        repository = change['repository']
        if policy is not None and not fleet.tap_granted(policy, repository):
            c.fail('fleet.tap_repository_denied', 'The repository is outside the local tap management grant.', 4)
        proposed = sources.binding(home, name, repository, change['ref'], change['packages'])
        if before is not None and not sources.same_binding(before, proposed):
            c.fail('source.alias_conflict', 'The alias already has a different approved binding.', 4)
        if before is not None and not owned and (policy is not None or 'fleet_owner' in before):
            c.fail('fleet.tap_not_owned', 'The alias belongs to a different owner.', 4)
        after = before if before is not None else dict(proposed, fleet_owner=owner)
    elif before is None:
        after = None
    elif not owned:
        if policy is not None:
            c.fail('fleet.tap_not_owned', 'The alias belongs to a different owner.', 4)
        after = before
    else:
        if policy is not None:
            if not fleet.tap_granted(policy, fleet.tap_repository(before['repository'])):
                c.fail('fleet.tap_repository_denied', 'The repository is outside the local tap management grant.', 4)
            if any(name in scope['sources'] for scope in policy['scopes'].values()):
                c.fail('source.referenced', 'A static fleet scope still references the tap.', 4)
        state = rpc.state_at(home)
        if sources.references(home, config, state, name) or any(
                name in record['last_manifest']['sources'] for record in c.consumer_records(state).values()):
            c.fail('source.referenced', 'A registered consumer still references the tap.', 4)
        after = None
    observation = dict(before=summary(before), after=summary(after),
                       observed=c.digest(dict(change=change, before=before, after=after, marker=config.get('fleet_tap'))))
    return observation, after


def result_path(home, operation):
    return maintenance.durable_path(home, 'tap-results', operation)


def save_result(home, receipt):
    path = result_path(home, receipt['operation'])
    previous = fleet.data(path, missing=True)
    if previous is not None and previous != receipt:
        c.fail('state.drift', 'The committed tap result differs from its durable receipt.', 4)
    if previous is None:
        fleet.put(path, receipt, None)


def commit_catalog(home, raw, config, name, after, observation, operation, plan):
    # Keep a committed result with the catalog replacement itself. If receipt
    # publication fails, the next retry or mutation can recover it from there.
    marker = config.get('fleet_tap')
    if marker is not None:
        save_result(home, marker)
    before, final = observation['before'], observation['after']
    receipt = dict(operation=operation, plan=plan, name=name, status='applied_verified',
                   before=before, after=final, changed=before != final)
    catalog = dict(config['sources'])
    if after is None:
        catalog.pop(name, None)
    else:
        catalog[name] = after
    proposal = c.config(dict(config, sources=catalog, fleet_tap=receipt))
    c.atomic_text(home / 'config.json', c.text_json(proposal), raw)
    save_result(home, receipt)
    return receipt


def recover_result(home, config, operation):
    marker = config.get('fleet_tap')
    if marker is not None and marker['operation'] == operation:
        save_result(home, marker)
        return marker
    saved = fleet.data(result_path(home, operation), missing=True)
    if saved is not None and validate_receipt(saved)['operation'] != operation:
        c.fail('state.drift', 'The saved tap result does not bind the catalog operation.', 4)
    return saved


def perform(home, intent, device, policy):
    change = intent['payload']['change']
    owner = policy['controller']['id']
    if intent['action'] == 'tap-inspect':
        config = catalog_at(home)[1]
        if change is None:
            taps = fleet.managed_taps(policy, config['sources'])
            return dict(taps={name: summary(config['sources'][name]) for name in taps})
        rpc.pending_guard(home)
        return candidate(home, config, change, owner, policy=policy)[0]
    operation = c.digest(maintenance.observation_facts(intent))
    with c.writer_lock(home, name='lifecycle.lock'), c.writer_lock(home):
        rpc.recheck_authority(home, intent, device, policy)
        rpc.pending_guard(home)
        raw, config = catalog_at(home)
        receipt = recover_result(home, config, operation)
        if receipt is not None:
            return receipt
        observation, after = candidate(home, config, change, owner, policy=policy)
        if observation['observed'] != intent['payload']['observed']:
            c.fail('plan.stale', 'Device tap catalog changed after the reviewed observation.', 4)
        return commit_catalog(home, raw, config, change['name'], after, observation, operation, intent['revision'])


def inspect(peer, signer, change, timeout):
    row = maintenance.target(peer)
    if not set(fleet.TAP_ACTIONS) <= set(peer['authority']['actions']):
        return dict(row, **maintenance.failure_row('fleet.tap_management_denied'))
    row = maintenance.inspect_target(peer, signer, 'tap-inspect', dict(change=change), timeout, row,
                                     capability='tap_management')
    if row['status'] != 'observed':
        return row
    observation = row['observation']
    try:
        if change is None:
            c.fields(observation, ('taps',), family='fleet', versions=())
            taps = observation['taps']
            if not isinstance(taps, dict) or len(taps) > 256:
                fleet.invalid('Expected a bounded managed tap catalog.')
            for name, entry in taps.items():
                sources.alias(name)
                validate_summary(entry)
                if entry is None or entry.get('fleet_owner') != signer['id']:
                    fleet.invalid('Expected controller-owned tap observations.')
        else:
            c.fields(observation, ('before', 'after', 'observed'), family='fleet', versions=())
            validate_summary(observation['before'])
            validate_summary(observation['after'])
            row.update(status='planned', request=dict(change=change, observed=rpc.digest(observation['observed'])))
    except c.MaskError:
        row.pop('observation')
        row.update(maintenance.failure_row('fleet.response_unverified'))
    return row


def inspect_all(peers, signer, change, timeout):
    with ThreadPoolExecutor(max_workers=min(8, len(peers))) as executor:
        return list(executor.map(lambda peer: inspect(peer, signer, change, timeout), peers))


def controller_observation(home, config, change, owner, devices):
    if change['kind'] == 'remove' and devices:
        return dict(status='not_applicable', reason='fleet.tap_subset_retains_controller')
    try:
        observation, _ = candidate(home, config, change, owner)
        return dict(observation, status='planned')
    except c.MaskError as error:
        return maintenance.failure_row(error)


def apply_controller(home, signer, change, reviewed, digest, eligible):
    if reviewed['status'] != 'planned':
        return reviewed
    operation = c.digest(dict(role='controller', plan=digest))
    try:
        with c.writer_lock(home, name='lifecycle.lock'), c.writer_lock(home):
            raw, config = catalog_at(home)
            prior = recover_result(home, config, operation)
            if prior is not None:
                return dict(status='applied_verified', receipt=prior)
            if not eligible:
                return dict(status='not_attempted', reason='fleet.tap_device_results_incomplete')
            rpc.pending_guard(home)
            marker = config.get('fleet_tap')
            # The controller can also be an enrolled device backed by this same catalog.
            if marker and marker['plan'] == digest and summary(config['sources'].get(change['name'])) == reviewed['after']:
                return dict(status='applied_verified', receipt=marker)
            observation, after = candidate(home, config, change, signer['id'])
            if dict(observation, status='planned') != reviewed:
                c.fail('plan.stale', 'Controller tap catalog changed after the reviewed observation.', 4)
            if observation['before'] == observation['after']:
                return dict(status='applied_verified', changed=False)
            receipt = commit_catalog(home, raw, config, change['name'], after, observation, operation, digest)
            return dict(status='applied_verified', receipt=receipt)
    except c.MaskError as error:
        return maintenance.failure_row(error, dispatch=True)
    except OSError:
        return dict(status='unknown', reason='filesystem.failed')


def input_change(args):
    name, url = getattr(args, 'name', None), getattr(args, 'url', None)
    if args.command == 'fleet.untap':
        return dict(kind='remove', name=sources.alias(name))
    if name and url:
        return dict(kind='add', name=sources.alias(name), repository=fleet.tap_repository(url),
                    ref=sources.selector(getattr(args, 'ref', 'main')), packages=sources.package_path(getattr(args, 'packages', 'skills')))
    if name or url or any(hasattr(args, option) for option in ('ref', 'packages', 'approve_plan')):
        c.fail('invocation.invalid', 'Use fleet tap to list, or fleet tap NAME URL to add a tap.', 2)
    return None


def dispatch(args, output, home):
    _, config = catalog_at(home)
    change = input_change(args)
    signer = fleet.get_identity(home, 'controller')
    timeout = rollout.timeout_option(args)
    if change is None:
        peers = rollout.choose_devices(args, home) if getattr(args, 'device', []) else transport.peers(home)
        rows = inspect_all(peers, signer, None, timeout) if peers else []
        output['data'].update(device_results=rows, controller_taps={
            name: summary(entry) for name, entry in config['sources'].items() if entry.get('fleet_owner') == signer['id']},
            complete=all(row['status'] == 'observed' for row in rows))
        if not output['data']['complete']:
            c.fail('fleet.incomplete', 'Some selected devices have no verified catalog observation.', 9)
        return

    devices = sorted(getattr(args, 'device', []))
    approval = getattr(args, 'approve_plan', None)
    path = maintenance.durable_path(home, 'tap-plans', rpc.digest(approval)) if approval else None
    lock = c.writer_lock(home, name='fleet-tap.lock') if approval and not output['dry_run'] else nullcontext()
    with lock:
        saved = fleet.data(path, missing=True, limit=maintenance.PLAN_LIMIT) if path else None
        if saved:
            plan = saved['plan']
            if (c.digest(plan) != approval or plan['change'] != change or plan['devices'] != devices or
                    plan['controller_id'] != signer['id'] or saved['expires'] <= int(time.time())):
                c.fail('plan.stale', 'Use a current preview of the same change and device selection.', 4)
        else:
            peers = rollout.choose_devices(args, home, default_all=True)
            plan = dict(change=change, devices=devices, controller_id=signer['id'],
                        controller=controller_observation(home, config, change, signer['id'], devices),
                        targets=inspect_all(peers, signer, change, timeout))
        digest = c.digest(plan)
        output['data'].update(plan=plan, plan_hash=digest, catalog_only=True)
        controller = plan['controller']
        can_send = change['kind'] == 'remove' or controller['status'] == 'planned'
        output['would_change'] = can_send and (
            controller.get('before') != controller.get('after') or any(
                row['status'] == 'planned' and row['observation']['before'] != row['observation']['after']
                for row in plan['targets']))
        if output['dry_run']:
            return
        if approval != digest:
            c.fail('plan.stale' if approval else 'confirmation.required', 'Preview the tap change and pass its --approve-plan hash.', 4)
        if saved is None:
            fleet.put(path, dict(plan=plan, expires=int(time.time()) + maintenance.TTL), None, limit=maintenance.PLAN_LIMIT)
        deliver(home, signer, plan, digest, timeout, can_send, output)


def deliver(home, signer, plan, digest, timeout, can_send, output):
    def send(row):
        if row['status'] != 'planned':
            return row
        if not can_send:
            return dict(row, status='not_attempted', reason='fleet.tap_controller_blocked')
        try:
            result = maintenance.send_update(home, signer, digest, row, 'tap-apply', timeout,
                                             verify_receipt=verify_device_receipt)
            if result.get('reason') == 'filesystem.failed':
                result['status'] = 'unknown'
            return result
        except c.MaskError as error:
            return dict(row, **maintenance.failure_row(error, dispatch=True))
        except OSError:
            return dict(row, status='unknown', reason='filesystem.failed')

    with ThreadPoolExecutor(max_workers=min(8, len(plan['targets']))) as executor:
        rows = list(executor.map(send, plan['targets']))
    complete = all(row['status'] == 'applied_verified' for row in rows)
    eligible = complete if plan['change']['kind'] == 'remove' else any(row['status'] == 'applied_verified' for row in rows)
    controller = apply_controller(home, signer, plan['change'], plan['controller'], digest, eligible)
    complete = complete and controller['status'] in ('applied_verified', 'not_applicable')
    output['data'].update(device_results=rows, controller_result=controller, complete=complete,
                          receipt_semantics='verified_operation')
    output['changed'] = any(row.get('receipt', {}).get('changed') for row in [*rows, controller])
    if output['changed']:
        output['transaction'] = 'committed'
    if not complete:
        c.fail('fleet.incomplete', 'Some reviewed catalog effects have no verified result.', 9)


def verify_device_receipt(receipt, row):
    validate_receipt(receipt)
    reviewed = row['observation']
    if (receipt['name'], receipt['before'], receipt['after']) != (
            row['request']['change']['name'], reviewed['before'], reviewed['after']):
        c.fail('fleet.response_unverified', 'Signed tap result differs from the reviewed catalog effect.', 4)
