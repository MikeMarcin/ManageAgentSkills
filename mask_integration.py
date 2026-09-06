"""Owned Git entries and recoverable, narrowly scoped integration edits."""
from __future__ import annotations

import copy
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
    c.fields(value, ('schema_version', 'installations'), family='integration')
    if not isinstance(value['installations'], dict):
        c.fail('integration.invalid', 'Invalid integration ownership.')
    for root, record in value['installations'].items():
        validate_record(root, record)
    return value


def validate_record(root, record):
    c.fields(record, ('root', 'identity', 'common', 'common_identity', 'mode', 'interpreter', 'program', 'home'), family='integration')
    if record['root'] != root or record['mode'] not in ('named', 'directory'):
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
    actual = c.git(root, 'rev-parse', '--git-common-dir')
    if (root / actual).resolve() != common:
        c.fail('integration.drift', 'Integration repository changed.', 4)
    if record['mode'] == 'directory':
        effective = c.git(root, 'rev-parse', '--git-path', 'hooks', inspect_hooks=True)
        if (root / effective).resolve() != common / 'hooks':
            c.fail('integration.hook_manager', 'An existing hook manager controls the effective hook path; use its explicit MASK entry.', 4)


def hook_command(record, event):
    return shlex.join([record['interpreter'], str(Path(record['program']) / 'mask_integration.py'),
                       'git-hook', record['home'], event])


def entries(record):
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
    if entry['role'] == 'git-config':
        raw = c.git(Path(record['root']), 'config', '--local', '--null', '--get-all', entry['name'], optional=True)
        return [] if raw is None else raw.rstrip('\0').split('\0')
    path = Path(record['common']) / 'hooks' / entry['name']
    c.parents_safe(Path(record['common']), path)
    return c.read_text(path, 'integration', missing=True)


def write_entry(record, entry, wanted):
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


def dispatch(args, output, home):
    if not getattr(args, 'git', False):
        c.fail('invocation.invalid', 'Select --git for this integration.', 2)
    root = c.project_root(args.project)
    common = c.git(root, 'rev-parse', '--git-common-dir', optional=True)
    if common is None:
        c.fail('integration.invalid', 'Git integration requires a repository.', 4)
    common = (root / common).resolve()
    before = registration(home)
    previous = before['installations'].get(str(root))
    enable = args.command == 'integration.enable'
    record = previous or dict(root=str(root), identity=c.identity(root), common=str(common), common_identity=c.identity(common),
                              mode='named' if named_hooks(root) else 'directory', interpreter=str(Path(sys.executable).resolve()),
                              program=str(Path(__file__).resolve().parent), home=str(home))
    check_record(record)
    after = copy.deepcopy(before)
    if enable:
        after['installations'][str(root)] = record
    else:
        after['installations'].pop(str(root), None)
    changes = []
    for entry in entries(record):
        actual = read_entry(record, entry)
        empty = [] if entry['role'] == 'git-config' else None
        expected = entry['value'] if previous else empty
        if actual != expected:
            c.fail('integration.collision', 'An integration entry is unmanaged or changed; preserve it and inspect.', 4, entry=entry['name'])
        wanted = entry['value'] if enable else empty
        if actual != wanted:
            changes.append(dict(entry, before=actual, after=wanted))
    plan_hash = c.digest(dict(before=before, after=after, changes=changes))
    if getattr(args, 'expect_plan_hash', plan_hash) != plan_hash:
        c.fail('plan.stale', 'Integration inputs changed; preview again.', 4)
    output['data'] = dict(plan_hash=plan_hash, coverage=coverage(record if enable else None), named_hooks=named_hooks(root))
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
    validate_record(record['root'], record)
    if record['home'] != str(home) or record['program'] != str(Path(__file__).resolve().parent):
        c.fail('recovery.conflict', 'Integration belongs to another machine/program.', 8)
    check_record(record)
    before = c.parse_json(pending['ownership_before'], 'integration') if pending['ownership_before'] is not None else dict(schema_version=1, installations={})
    after = c.parse_json(pending['ownership_after'], 'integration')
    expected = copy.deepcopy(before)
    if pending['operation'] == 'integration.enable':
        expected['installations'][record['root']] = record
    else:
        if expected['installations'].get(record['root']) != record:
            c.fail('recovery.conflict', 'Removal is not owned.', 8)
        expected['installations'].pop(record['root'])
    if expected != after:
        c.fail('recovery.conflict', 'Integration changes unrelated ownership.', 8)
    allowed = {entry['name']: entry for entry in entries(record)}
    if not isinstance(pending['changes'], list) or len({entry['name'] for entry in pending['changes']}) != len(pending['changes']):
        c.fail('recovery.conflict', 'Invalid integration entry selection.', 8)
    for entry in pending['changes']:
        canonical = allowed.get(entry['name'])
        if not canonical or {key: entry.get(key) for key in ('name', 'role', 'value')} != canonical or set(entry) != {'name', 'role', 'value', 'before', 'after'}:
            c.fail('recovery.conflict', 'Unsafe integration entry.', 8)
        empty = [] if entry['role'] == 'git-config' else None
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


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == 'git-hook':
        raise SystemExit(git_hook(sys.argv[2], sys.argv[3]))
    raise SystemExit(2)
