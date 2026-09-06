"""Owned Git entries and recoverable, narrowly scoped integration edits."""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shlex
import signal
import subprocess
import sys

import mask_core as c
import mask_fs as fs


EVENTS = ('post-checkout', 'post-merge', 'post-rewrite', 'post-commit')


def named_hooks(root):
    result = c.git(root, '-c', 'hook.mask-capability-probe.event=post-checkout',
                   '-c', 'hook.mask-capability-probe.command=true', '-c', 'hook.post-checkout.enabled=true',
                   'hook', 'list', 'post-checkout', optional=True)
    return result is not None and 'mask-capability-probe' in result.splitlines()


def registration(home):
    value = c.read_json(home / 'integrations.json', 'integration', default=dict(schema_version=1, installations={}))
    return validate_registration(value)


def validate_registration(value):
    c.fields(value, ('schema_version', 'installations'), family='integration')
    if not isinstance(value['installations'], dict):
        c.fail('integration.invalid', 'Invalid integration ownership.')
    for root, record in value['installations'].items():
        validate_record(root, record)
    return value


def validate_record(root, record):
    c.fields(record, ('root', 'identity', 'common', 'common_identity', 'mode', 'interpreter', 'program', 'home'), ('scope',), family='integration')
    if record.get('scope', 'project') not in ('project', 'user') or record.get('scope') == 'user' and record['mode'] not in ('claude', 'codex'):
        c.fail('integration.invalid', 'Invalid integration scope.')
    if binding(record) != root or record['mode'] not in ('named', 'directory', 'claude', 'codex'):
        c.fail('integration.invalid', 'Invalid integration binding.')
    for key in ('root', 'common', 'interpreter', 'program', 'home'):
        if not isinstance(record[key], str) or not Path(record[key]).is_absolute() or any(ch in record[key] for ch in '\0\r\n'):
            c.fail('integration.invalid', 'Invalid integration path.')
    for key in ('identity', 'common_identity'):
        c.fields(record[key], ('device', 'inode'), family='integration')
        if any(type(value) is not int for value in record[key].values()):
            c.fail('integration.invalid', 'Invalid integration identity.')


def check_record(record):
    root, common = Path(record['root']), Path(record['common'])
    for path, expected in ((root, record['identity']), (common, record['common_identity'])):
        if not path.is_dir() or path.resolve() != path or c.identity(path) != expected:
            c.fail('integration.drift', 'Integration root identity changed.', 4)
    if record['mode'] in ('claude', 'codex'):
        return
    actual = c.git(root, 'rev-parse', '--git-common-dir')
    if (root / actual).resolve() != common:
        c.fail('integration.drift', 'Integration repository changed.', 4)
    if record['mode'] == 'directory':
        effective = c.git(root, 'rev-parse', '--git-path', 'hooks', inspect_hooks=True)
        if (root / effective).resolve() != common / 'hooks':
            c.fail('integration.hook_manager', 'An existing hook manager controls the effective hook path; use its explicit MASK entry.', 4)
    else:
        for event in EVENTS:
            for name in (event, 'mask-readiness-' + event):
                if c.git(root, 'config', '--bool', '--get', f'hook.{name}.enabled', optional=True, inspect_hooks=True) == 'false':
                    c.fail('integration.disabled', 'Git configuration disables a required readiness hook.', 4, event=event)


def hook_command(record, event):
    return shlex.join([record['interpreter'], str(Path(record['program']) / 'mask_integration.py'),
                       'git-hook', record['home'], event])


def binding(record):
    return record['root'] + ('::' + record['mode'] if record['mode'] in ('claude', 'codex') else '')


def host_file(record):
    relative = '.codex/hooks.json'
    if record['mode'] == 'claude':
        relative = '.claude/settings.json' if record.get('scope') == 'user' else '.claude/settings.local.json'
    return Path(record['root']) / relative


def host_root(home):
    state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
    if state.get('user'):
        root = Path(state['user']['root'])
        c.registered_root(root, state['user'], 'user')
        return root
    return Path.home().resolve()


def host_settings(record):
    path = host_file(record)
    c.parents_safe(Path(record['root']), path)
    raw = c.read_text(path, 'integration', missing=True)
    value = c.parse_json(raw, 'integration') if raw is not None else {}
    if not isinstance(value, dict) or not isinstance(value.get('hooks', {}), dict) or not isinstance(value.get('hooks', {}).get('SessionStart', []), list):
        c.fail('integration.invalid', 'Invalid host SessionStart configuration.', 4)
    return raw, value


def entries(record):
    if record['mode'] in ('claude', 'codex'):
        command = shlex.join([record['interpreter'], str(Path(record['program']) / 'mask_integration.py'),
                              'host-hook', record['home'], record['mode']])
        group = dict(matcher='startup|resume|clear|compact', hooks=[dict(type='command', command=command, timeout=45)])
        return [dict(role='host-hook', name='SessionStart', value=[group])]
    result = []
    for event in EVENTS:
        command = hook_command(record, event)
        if record['mode'] == 'named':
            result.extend([dict(role='git-config', name=f'hook.mask-readiness-{event}.command', value=[command]),
                           dict(role='git-config', name=f'hook.mask-readiness-{event}.event', value=[event])])
        else:
            result.append(dict(role='git-hook', name=event, value=f'#!/bin/sh\n# MASK owned readiness hook v1\nexec {command}\n'))
    return result


def read_entry(record, entry):
    check_record(record)
    if entry['role'] == 'host-hook':
        _, value = host_settings(record)
        return [group for group in value.get('hooks', {}).get('SessionStart', []) if group in entry['value']]
    if entry['role'] == 'git-config':
        raw = c.git(Path(record['root']), 'config', '--local', '--null', '--get-all', entry['name'], optional=True)
        return [] if raw is None else raw.rstrip('\0').split('\0')
    path = Path(record['common']) / 'hooks' / entry['name']
    c.parents_safe(Path(record['common']), path)
    return c.read_text(path, 'integration', missing=True)


def write_entry(record, entry, wanted):
    if entry['role'] == 'host-hook':
        raw, value = host_settings(record)
        groups = value.setdefault('hooks', {}).setdefault('SessionStart', [])
        value['hooks']['SessionStart'] = [group for group in groups if group not in entry['value']] + wanted
        c.atomic_text(host_file(record), c.text_json(value), raw)
        return
    if entry['role'] == 'git-config':
        root = Path(record['root'])
        if wanted:
            c.git(root, 'config', '--local', '--replace-all', entry['name'], wanted[0])
        else:
            c.git(root, 'config', '--local', '--unset-all', entry['name'])
        return
    path = Path(record['common']) / 'hooks' / entry['name']
    current = read_entry(record, entry)
    if wanted is None:
        if current is not None:
            path.unlink()
    else:
        c.atomic_text(path, wanted, current)
        if os.name != 'nt':
            path.chmod(path.stat().st_mode | 0o111)


def coverage(record):
    return dict(git=record is not None, mode=record['mode'] if record else None,
                clone=False, existing_worktree=record is not None, linked_worktree=record is not None,
                startup=False, limitation='Per-repository hooks do not cover future clones. Use approved startup/prelaunch readiness.')


def inspect_coverage(home, root):
    owned = registration(home)['installations']
    result = coverage(owned.get(str(root)))
    result['agents'] = {}
    for name, key in [('git', str(root)), ('claude', str(root) + '::claude'), ('codex', str(root) + '::codex')]:
        record = owned.get(key)
        if record is None:
            continue
        try:
            present = all(read_entry(record, entry) == entry['value'] for entry in entries(record))
            if record['mode'] == 'directory' and os.name != 'nt':
                present = present and all(os.access(Path(record['common']) / 'hooks' / event, os.X_OK) for event in EVENTS)
        except c.MaskError:
            present = False
        if name == 'git':
            result['git'] = present
        else:
            result['agents'][name] = dict(configured=present, host_load='not_verified', trust='host_managed')
    result['startup'] = any(item['configured'] for item in result['agents'].values())
    return result


def dispatch(args, output, home):
    agent = getattr(args, 'agent', None)
    if bool(getattr(args, 'git', False)) == bool(agent) or agent is not None and agent not in ('claude', 'codex'):
        c.fail('invocation.invalid', 'Select exactly one of --git or --agent claude|codex.', 2)
    project = getattr(args, 'project', None)
    if agent is None and project is None:
        c.fail('invocation.invalid', 'Per-repository Git installation requires --project.', 2)
    root = c.project_root(project) if project else host_root(home)
    common = str(root) if agent else c.git(root, 'rev-parse', '--git-common-dir', optional=True)
    if common is None:
        c.fail('integration.invalid', 'Git integration requires a repository.', 4)
    common = (root / common).resolve()
    before = registration(home)
    key = str(root) + ('::' + agent if agent else '')
    previous = before['installations'].get(key)
    enable = args.command == 'integration.enable'
    record = previous or dict(root=str(root), identity=c.identity(root), common=str(common), common_identity=c.identity(common),
                              mode=agent or ('named' if named_hooks(root) else 'directory'), interpreter=str(Path(sys.executable).resolve()),
                              program=str(Path(__file__).resolve().parent), home=str(home))
    if project is None:
        record = dict(record, scope='user')
    check_record(record)
    after = copy.deepcopy(before)
    if enable:
        after['installations'][key] = record
    else:
        after['installations'].pop(key, None)
    changes = []
    for entry in entries(record):
        actual = read_entry(record, entry)
        if previous and entry['role'] == 'git-hook' and actual is not None and os.name != 'nt' and not os.access(common / 'hooks' / entry['name'], os.X_OK):
            c.fail('integration.drift', 'An owned hook is no longer executable.', 4, entry=entry['name'])
        empty = [] if entry['role'] in ('git-config', 'host-hook') else None
        expected = entry['value'] if previous else empty
        if actual != expected:
            c.fail('integration.collision', 'An integration entry is unmanaged or changed; preserve it and inspect.', 4, entry=entry['name'])
        wanted = entry['value'] if enable else empty
        if actual != wanted:
            changes.append(dict(entry, before=actual, after=wanted))
    plan_hash = c.digest(dict(before=before, after=after, changes=changes))
    if getattr(args, 'expect_plan_hash', plan_hash) != plan_hash:
        c.fail('plan.stale', 'Integration inputs changed; preview again.', 4)
    output['data'] = dict(plan_hash=plan_hash, coverage=coverage(record if enable else None) if not agent else
                         dict(agent=agent, startup=enable, gate='warning' if agent == 'claude' else 'documented_stop_unverified',
                              reload='requested' if agent == 'claude' else 'restart_may_be_required', host_load='not_verified', trust='host_managed'),
                         named_hooks=named_hooks(root) if not agent else None)
    output['data']['files'] = sorted({str(host_file(record)) if entry['role'] == 'host-hook' else
                                       str(common / 'config') if entry['role'] == 'git-config' else str(common / 'hooks' / entry['name'])
                                       for entry in changes} | ({str(home / 'integrations.json')} if before != after else set()))
    if agent == 'codex':
        output['data']['worktree_setup_command'] = shlex.join([record['interpreter'], str(Path(record['program']) / 'mask.py'),
                                                             'ensure', '--home', str(home), '--event', 'startup'])
        output['data']['worktree_setup'] = 'Available for an existing Codex local-environment setup script; the script is preserved and not replaced.'
    output['would_change'] = bool(changes) or before != after
    output['actions'] = [dict(kind=args.command, status='planned', role=entry['role'], entry=entry['name']) for entry in changes]
    if not output['dry_run'] and output['would_change']:
        pending = dict(schema_version=3, operation=args.command, record=record, changes=changes,
                       ownership_before=c.read_text(home / 'integrations.json', 'integration', missing=True), ownership_after=c.text_json(after))
        validate_pending(pending, home)
        c.atomic_text(home / 'pending.json', c.text_json(pending), None)
        fs.checkpoint('integration-intent')
        try:
            restore(pending, home, 'after')
            fs.clear_pending(home, pending)
            output.update(changed=True, transaction='committed')
        except (Exception, KeyboardInterrupt):
            output.update(changed=True, transaction='partial')
            c.fail('recovery.required', 'Integration changes may remain; inspect and recover the owned entries.', 8)


def validate_pending(pending, home):
    c.fields(pending, ('schema_version', 'operation', 'record', 'changes', 'ownership_before', 'ownership_after'), family='recovery', versions=(3,))
    if pending['operation'] not in ('integration.enable', 'integration.disable'):
        c.fail('recovery.conflict', 'Unknown integration operation.', 8)
    record = pending['record']
    if not isinstance(record, dict) or not isinstance(record.get('root'), str) or not isinstance(record.get('mode'), str):
        c.fail('recovery.conflict', 'Invalid integration record.', 8)
    validate_record(binding(record), record)
    if record['home'] != str(home) or record['program'] != str(Path(__file__).resolve().parent):
        c.fail('recovery.conflict', 'Integration belongs to another machine/program.', 8)
    check_record(record)
    before = validate_registration(c.parse_json(pending['ownership_before'], 'integration')) if pending['ownership_before'] is not None else dict(schema_version=1, installations={})
    after = validate_registration(c.parse_json(pending['ownership_after'], 'integration'))
    if binding(record) not in before['installations'] and record['interpreter'] != str(Path(sys.executable).resolve()):
        c.fail('recovery.conflict', 'Recover a new integration using its original selected interpreter.', 8)
    expected = copy.deepcopy(before)
    if pending['operation'] == 'integration.enable':
        expected['installations'][binding(record)] = record
    else:
        if expected['installations'].get(binding(record)) != record:
            c.fail('recovery.conflict', 'Removal is not owned.', 8)
        expected['installations'].pop(binding(record))
    if expected != after:
        c.fail('recovery.conflict', 'Integration changes unrelated ownership.', 8)
    allowed = {entry['name']: entry for entry in entries(record)}
    if not isinstance(pending['changes'], list):
        c.fail('recovery.conflict', 'Invalid integration entry selection.', 8)
    seen = set()
    for entry in pending['changes']:
        c.fields(entry, ('name', 'role', 'value', 'before', 'after'), family='recovery')
        if not isinstance(entry['name'], str) or entry['name'] in seen:
            c.fail('recovery.conflict', 'Invalid integration entry identity.', 8)
        seen.add(entry['name'])
        canonical = allowed.get(entry['name'])
        if not canonical or {key: entry.get(key) for key in ('name', 'role', 'value')} != canonical or set(entry) != {'name', 'role', 'value', 'before', 'after'}:
            c.fail('recovery.conflict', 'Unsafe integration entry.', 8)
        empty = [] if entry['role'] in ('git-config', 'host-hook') else None
        expected_values = (empty, entry['value']) if pending['operation'] == 'integration.enable' else (entry['value'], empty)
        if (entry['before'], entry['after']) != expected_values:
            c.fail('recovery.conflict', 'Invalid integration entry transition.', 8)


def restore(pending, home, side):
    validate_pending(pending, home)
    path = home / 'integrations.json'
    actual = c.read_text(path, 'integration', missing=True)
    if actual not in (pending['ownership_before'], pending['ownership_after']):
        c.fail('recovery.conflict', 'Integration ownership changed.', 8)
    for entry in pending['changes']:
        if read_entry(pending['record'], entry) not in (entry['before'], entry['after']):
            c.fail('recovery.conflict', 'An integration entry changed after preparation.', 8)
    for entry in pending['changes']:
        current = read_entry(pending['record'], entry)
        if current not in (entry['before'], entry['after']):
            c.fail('recovery.conflict', 'Integration entry changed immediately before effect.', 8)
        if current != entry[side]:
            write_entry(pending['record'], entry, entry[side])
        elif entry['role'] == 'git-hook' and entry[side] is not None and os.name != 'nt':
            hook_path = Path(pending['record']['common']) / 'hooks' / entry['name']
            hook_path.chmod(hook_path.stat().st_mode | 0o111)
        fs.checkpoint('integration-entry')
    wanted = pending['ownership_' + side]
    if wanted is not None:
        c.atomic_text(path, wanted, actual)
    elif actual is not None:
        if c.read_text(path, 'integration') != actual:
            c.fail('recovery.conflict', 'Integration ownership changed before rollback.', 8)
        path.unlink()


def recover(home, output, mode):
    pending = c.read_json(home / 'pending.json', 'recovery')
    validate_pending(pending, home)
    output['data'] = dict(pending=pending, recovery_mode=mode)
    if mode == 'inspect' or output['dry_run']:
        return
    try:
        restore(pending, home, 'after' if mode == 'complete' else 'before')
        fs.clear_pending(home, pending)
    except (Exception, KeyboardInterrupt):
        output.update(changed=True, transaction='partial')
        raise
    output.update(changed=True, would_change=True, transaction='committed' if mode == 'complete' else 'rolled_back')


def run_readiness(command):
    options = dict(start_new_session=True) if os.name != 'nt' else dict(creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, **options)
    try:
        stdout, stderr = process.communicate(timeout=30)
    except (subprocess.TimeoutExpired, KeyboardInterrupt):
        if os.name == 'nt':
            stopped = subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True, timeout=10)
            if stopped.returncode:
                c.fail('recovery.required', 'Readiness process-tree termination is unconfirmed.', 8)
        else:
            os.killpg(process.pid, signal.SIGKILL)
        process.communicate(timeout=10)
        c.fail('readiness.timeout', 'Readiness deadline exceeded; inspect pending recovery before retrying.', 8)
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def git_hook(home, event):
    if os.environ.get('MASK_INTERNAL_GIT') == '1':
        return 0
    if event not in EVENTS:
        return 2
    command = [sys.executable, str(Path(__file__).resolve().parent / 'mask.py'), 'ensure', '--home', home, '--event', event, '--json']
    try:
        run = run_readiness(command)
        if run.returncode:
            data = c.parse_json(run.stdout)
            code = data.get('error', {}).get('code', 'readiness.blocked')
            print(f'MASK: Git {event} already completed; readiness is blocked ({code}). Inspect mask ensure --check.', file=sys.stderr)
    except (OSError, subprocess.TimeoutExpired, c.MaskError):
        print(f'MASK: Git {event} already completed; readiness could not finish. Inspect mask ensure --check.', file=sys.stderr)
    return 0


def host_hook(home, agent):
    if agent not in ('claude', 'codex'):
        return 2
    command = [sys.executable, str(Path(__file__).resolve().parent / 'mask.py'), 'ensure', '--home', home, '--event', 'startup', '--json']
    try:
        run = run_readiness(command)
        data = c.parse_json(run.stdout)
        ready = run.returncode == 0
        message = 'MASK filesystem readiness is complete; host loading is not verified.' if ready else 'MASK readiness is blocked. Inspect mask ensure --check before continuing.'
    except (OSError, c.MaskError, subprocess.TimeoutExpired):
        ready = False
        message = 'MASK readiness could not finish. Inspect pending recovery before continuing.'
    specific = dict(hookEventName='SessionStart', additionalContext=message)
    output = dict(hookSpecificOutput=specific)
    if agent == 'claude':
        specific['reloadSkills'] = ready
    elif not ready:
        output.update({'continue': False, 'stopReason': message})
    print(json.dumps(output))
    return 0


if __name__ == '__main__':
    # Named Git hooks append event arguments; authority comes from our fixed prefix.
    if len(sys.argv) >= 4 and sys.argv[1] == 'git-hook':
        raise SystemExit(git_hook(sys.argv[2], sys.argv[3]))
    if len(sys.argv) == 4 and sys.argv[1] == 'host-hook':
        raise SystemExit(host_hook(sys.argv[2], sys.argv[3]))
    raise SystemExit(2)
