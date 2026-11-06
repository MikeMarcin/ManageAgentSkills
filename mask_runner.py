"""Local pull convergence for a device with explicit desired and receipt repositories."""
from __future__ import annotations

import time
import uuid

import mask_control as control
import mask_core as c
import mask_fleet as fleet
import mask_fleet_receipts as receipts
import mask_rollout as rollout
import mask_rpc as rpc


def prerequisites(home):
    device = fleet.get_identity(home, 'device')
    policy = fleet.current_authority(home)
    if policy.get('revoked'):
        c.fail('fleet.controller_revoked', 'Controller authority was revoked locally.', 4)
    settings = control.settings(home, missing=True)
    if settings is None or 'receipts' not in settings:
        c.fail('fleet.runner_control_required', 'Configure a read-only desired repository and separate writable receipt repository.', 4)
    return device, policy, settings


def local_intent(device, policy, event, action, payload, *, generation=0):
    expiry = int(time.time()) + 120
    if action in ('prepare', 'apply'):
        expiry = min(event['expires'], expiry)
    intent = rpc.intent_shape(dict(schema_version=1, protocol=fleet.PROTOCOL, id=uuid.uuid4().hex,
                                   device=device['id'], controller=policy['controller']['id'], epoch=policy['epoch'],
                                   sequence=event['sequence'], expires=expiry, revision=control.intent_digest(event),
                                   generation=generation, action=action, payload=payload))
    rpc.current(intent, device, policy)
    return intent


def apply_latest(home, device, policy, settings, history, entry, target):
    base = rollout.base_result(target)
    pathname = fleet.path(home, 'runner-deliveries/' + entry['operation'])
    try:
        if target.get('identity') != fleet.public(device) or target['device_epoch'] != policy['epoch']:
            c.fail('fleet.authority_changed', 'Desired target does not match the current device identity or grant.', 4)
        before = fleet.data(pathname, missing=True)
        if before:
            verified = rollout.proof_result(before, entry, target)
            if verified:
                receipt = receipts.publish(settings, entry, target, before)
                return dict(verified, receipt_commit=receipt)
            attempt = before['apply']['intent']
            query = local_intent(device, policy, entry, 'receipt',
                                 dict(operation=attempt['id'], digest=rpc.request_digest(attempt)))
            observed = rpc.perform(home, query, device, policy)
            if observed['status'] == 'applied_verified':
                return finish(home, device, settings, entry, target, pathname, before, attempt, observed, proof_intent=query)
        if entry['expires'] <= int(time.time()):
            c.fail('fleet.intent_expired', 'The approved revision expired before new local application.', 4)
        if policy != fleet.current_authority(home):
            c.fail('fleet.authority_changed', 'Desired target no longer matches the current local grant.', 4)
        scope = policy['scopes'].get(target['scope'])
        if scope is None or scope['scope'] != target['scope_type'] or not scope.get('rollout'):
            c.fail('fleet.scope_denied', 'The desired scope is not currently authorized.', 4)
        payload = dict(scope=target['scope'], profile=target['profile'])
        generation = rpc.state_at(home)['generation']
        intent = local_intent(device, policy, entry, 'prepare', payload, generation=generation)
        prepared = rpc.perform(home, intent, device, policy)
        if prepared['status'] != 'prepared' or control.remote_head(history.root, settings) != history.head:
            c.fail('fleet.control_conflict', 'The approved control head changed before local apply.', 4)
        payload['plan'] = prepared['result']['plan']
        intent = local_intent(device, policy, entry, 'apply', payload, generation=generation)
        record = dict(apply=dict(intent=intent), proof=None)
        fleet.put(pathname, record, before)
        applied = rpc.perform(home, intent, device, policy)
        return finish(home, device, settings, entry, target, pathname, record, intent, applied)
    except c.MaskError as error:
        known = fleet.data(pathname, missing=True)
        applied = rollout.proof_result(known, entry, target) if known else None
        if applied is not None:
            return dict(applied, status='unknown', reason=error.code, local_status=applied['status'])
        return dict(base, status='recovery_required' if error.code == 'recovery.required' else 'blocked', reason=error.code)


def finish(home, device, settings, entry, target, pathname, record, intent, applied, *, proof_intent=None):
    query = proof_intent or intent
    value = rpc.response_value(query, device, applied)
    envelope = dict(response=value, signature=fleet.sign(value, device, fleet.RECEIPT))
    complete = dict(record, proof=dict(intent=query, packet=envelope))
    result = rollout.proof_result(complete, entry, target)
    if result is None:
        c.fail('fleet.receipt_unavailable', 'The local application has no verified signed outcome.', 4)
    fleet.put(pathname, complete, record)
    return dict(result, newly_observed=True, receipt_commit=receipts.publish(settings, entry, target, complete))


def converge(home, output):
    device, policy, settings = prerequisites(home)
    with c.writer_lock(home, name='fleet-pull.lock'):
        with control.snapshot(home, settings, policy['controller']) as history:
            control.remember(home, history)
            pairs = [(event, target) for event, target in history.effective().values()
                     if target['device'] == device['id'] and event['action'] != 'cancel']
            pairs.sort(key=lambda pair: pair[0]['sequence'])
            rows = [apply_latest(home, device, policy, settings, history, event, target) for event, target in pairs]
    output['data'].update(device_results=rows, complete=all(row['status'] in rollout.CONVERGED for row in rows),
                          selected_devices=int(bool(pairs)), installed_everywhere=False, host_load='not_verified',
                          operation_ids=[entry['operation'] for entry, _ in pairs])
    output['changed'] = any(row.get('newly_observed') or row.get('local_status') for row in rows)
    if output['changed']:
        output['transaction'] = 'committed'
    rollout.require_complete(output)


def record_path(home):
    return fleet.path(home, 'runner')


def runner_argv(home):
    from pathlib import Path
    import sys
    return [str(Path(sys.executable).resolve()), '-B', str(Path(__file__).resolve().with_name('mask.py')),
            '--home', str(home), 'fleet', 'runner', 'tick', '--json']


def read_record(home):
    record = fleet.data(record_path(home), missing=True)
    if record is None:
        return None
    c.fields(record, ('schema_version', 'platform', 'user', 'name', 'path', 'interval', 'argv', 'enabled', 'control'),
             ('start_boundary',), family='fleet')
    if type(record['enabled']) is not bool or not 60 <= fleet.number(record['interval']) <= 3600:
        c.fail('fleet.runner_invalid', 'Invalid saved runner ownership or interval.', 4)
    if 'start_boundary' in record and (record['platform'] != 'windows' or not isinstance(record['start_boundary'], str)):
        c.fail('fleet.runner_invalid', 'Invalid saved Windows task start boundary.', 4)
    return record


def scheduler_command(args, output, home):
    import mask_fleet_schedule as scheduler

    action = args.command.rsplit('.', 1)[-1]
    previous = read_record(home)
    saved_boundary = None
    if previous:
        device = fleet.get_identity(home, 'device')
        expected = scheduler.schedule_record(home, device, previous['interval'], previous['argv'])
        saved_binding = scheduler_binding(previous)
        saved_boundary = saved_binding.pop('start_boundary', None)
        if expected != saved_binding:
            c.fail('fleet.scheduler_scope', 'The saved scheduler entry does not belong to this MASK home and native user.', 4)
    if action == 'status':
        output['data']['runner'] = dict(enabled=False, status='disabled')
        if previous:
            present, active = scheduler.observe(scheduler_binding(previous))
            output['data']['runner'] = dict(enabled=previous['enabled'], status='active' if active else 'inactive',
                                            scheduler_present=present, interval=previous['interval'],
                                            name=previous['name'], next=fleet.data(fleet.path(home, 'runner-clock'), missing=True))
        return
    if action == 'disable' and (previous is None or not previous['enabled']):
        if previous is None or not scheduler.observe(scheduler_binding(previous))[0]:
            output['data']['runner'] = dict(enabled=False, status='disabled')
            return
    if action == 'enable':
        interval = getattr(args, 'interval', 300)
        if not 60 <= interval <= 3600:
            c.fail('invocation.invalid', 'Choose a runner interval from 60 through 3600 seconds.', 2)
        device, _, settings = prerequisites(home)
        binding = scheduler.schedule_record(home, device, interval, runner_argv(home))
        if saved_boundary is not None:
            binding['start_boundary'] = saved_boundary
        candidate = dict(binding, enabled=True, control=c.digest(settings))
        if previous and previous['enabled'] and previous != candidate:
            c.fail('fleet.runner_active', 'Disable the existing runner before changing its schedule.', 4)
    else:
        candidate = dict(previous, enabled=False)
        binding = scheduler_binding(previous)
    present, active = scheduler.observe(binding)
    if present and previous is None:
        c.fail('fleet.scheduler_collision', 'A scheduler entry exists without this MASK home owning it.', 4)
    output['data']['runner'] = dict(enabled=candidate['enabled'], name=binding['name'], interval=binding['interval'],
                                    status='planned', scheduler=scheduler_binding(candidate))
    # Include current native existence, so an explicit preview cannot authorize
    # deleting or replacing an entry created after that preview.
    old_facts = dict(record=previous, present=present, active=active)
    plan_hash = c.digest(dict(before=old_facts, after=candidate))
    output['data']['plan_hash'] = plan_hash
    output['would_change'] = previous != candidate or (not active if action == 'enable' else present)
    if output['dry_run'] or not output['would_change']:
        return
    if getattr(args, 'approve_plan', None) != plan_hash:
        c.fail('confirmation.required', 'Preview the exact current-user scheduler change before approval.', 4)
    with c.writer_lock(home, name='fleet-scheduler.lock'):
        if read_record(home) != previous or scheduler.observe(binding) != (present, active):
            c.fail('plan.stale', 'Runner ownership changed after preview.', 4)
        # Persist ownership before installation; disable the tick gate before
        # removal. An interruption can safely retry the reviewed operation.
        if action == 'enable' and binding['platform'] == 'windows' and not present:
            # Approval fixes the schedule policy. Bind its actual installation
            # time durably before registering the native definition.
            binding = dict(binding, start_boundary=scheduler.windows_start_boundary())
            candidate['start_boundary'] = binding['start_boundary']
            output['data']['runner']['scheduler'] = binding
        fleet.put(record_path(home), candidate, previous)
        output.update(changed=True, transaction='committed')
        if action == 'enable':
            scheduler.install(binding)
        else:
            with c.writer_lock(home, name='fleet-pull.lock'):
                scheduler.remove(binding)
    output['data']['runner']['status'] = 'active' if action == 'enable' else 'disabled'


def scheduler_binding(record):
    return {key: value for key, value in record.items() if key not in ('enabled', 'control')}


def next_tick(now, interval, failures, jitter):
    return now + min(3600, interval * 2 ** min(failures, 6) + jitter)


def tick(home, output):
    import secrets

    record = read_record(home)
    if record is None or not record['enabled']:
        output['data']['runner'] = dict(enabled=False, status='disabled')
        return
    if c.digest(control.settings(home)) != record['control'] or record['argv'] != runner_argv(home):
        c.fail('fleet.runner_changed', 'Review and re-enable the runner after its approved inputs change.', 4)
    now = int(time.time())
    pathname = fleet.path(home, 'runner-clock')
    before = fleet.data(pathname, missing=True)
    if before and now < before['next_at']:
        output['data']['runner'] = dict(enabled=True, status='waiting', **before)
        return
    failed = True
    try:
        converge(home, output)
        failed = False
    finally:
        interval = record['interval']
        failures = min(6, (before or {}).get('failures', 0) + 1) if failed else 0
        after = dict(failures=failures, next_at=next_tick(int(time.time()), interval, failures, secrets.randbelow(max(1, interval // 8))))
        with c.writer_lock(home, name='fleet-scheduler.lock'):
            if read_record(home) == record and fleet.data(pathname, missing=True) == before:
                fleet.put(pathname, after, before)
        output['data']['runner'] = dict(enabled=True, status='backoff' if failed else 'checked', **after)


def dispatch(args, output, home):
    if args.command == 'fleet.sync':
        if any(getattr(args, name, False) for name in ('all', 'device', 'timeout')):
            c.fail('invocation.invalid', '--local uses this device and cannot select controller SSH targets.', 2)
        return converge(home, output)
    if args.command == 'fleet.runner.tick':
        return tick(home, output)
    return scheduler_command(args, output, home)
