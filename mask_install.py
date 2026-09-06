"""Owned portable launchers and independent, compatibility-checked program updates."""
from __future__ import annotations

import ast
import copy
import os
from pathlib import Path
import shlex
import shutil
import sys

import mask_core as c
import mask_fs as fs
import mask_git as g


def launcher_text(record):
    interpreter, entry = record['interpreter'], str(Path(record['program_root']) / 'mask.py')
    if any(char in interpreter + entry for char in '\r\n\x00'):
        c.fail('config.invalid', 'Unsupported launcher path characters.')
    if os.name == 'nt':
        interpreter, entry = interpreter.replace('%', '%%'), entry.replace('%', '%%')
        return f'@echo off\r\nrem MASK owned launcher v1\r\nsetlocal DisableDelayedExpansion\r\n"{interpreter}" "{entry}" %*\r\nexit /b %errorlevel%\r\n'
    return f'#!/bin/sh\n# MASK owned launcher v1\nexec {shlex.quote(interpreter)} {shlex.quote(entry)} "$@"\n'


def validate_launcher_intent(pending):
    c.fields(pending['launcher'], ('path',), family='recovery')
    key = pending['launcher']['path']
    before, after = pending['before_state'], pending['after_state']
    record = after['launchers'].get(key)
    if pending['operation'] != 'self.install' or pending['selected'] or pending['links'] or pending['manifests'] or before['projects'] != after['projects'] or not record:
        c.fail('recovery.conflict', 'Invalid launcher transaction scope.', 8)
    if record['program_root'] != str(Path(__file__).resolve().parent) or Path(key).name != ('mask.cmd' if os.name == 'nt' else 'mask'):
        c.fail('recovery.conflict', 'Launcher does not belong to this program.', 8)
    for side in (before, after):
        for path, item in side['launchers'].items():
            if path != key and before['launchers'].get(path) != after['launchers'].get(path):
                c.fail('recovery.conflict', 'Launcher intent changes unrelated ownership.', 8)
        item = side['launchers'].get(key)
        if item and c.digest(launcher_text(item).encode()) != item['content_digest']:
            c.fail('recovery.conflict', 'Launcher record does not describe recognized content.', 8)


def launcher_values(pending):
    key = pending['launcher']['path']
    return [launcher_text(pending[side + '_state']['launchers'][key]) if key in pending[side + '_state']['launchers'] else None for side in ('before', 'after')]


def check_launcher(pending):
    path = Path(pending['launcher']['path'])
    actual = c.read_text(path, 'launcher', missing=True)
    if actual not in launcher_values(pending):
        c.fail('recovery.conflict', 'Launcher contents changed.', 8, path=str(path))
    return actual


def restore_launcher(pending, side):
    actual = check_launcher(pending)
    wanted = launcher_values(pending)[side == 'after']
    path = Path(pending['launcher']['path'])
    if wanted is None:
        if actual is not None:
            path.unlink()
    else:
        c.atomic_text(path, wanted, actual)
        if os.name != 'nt':
            path.chmod(path.stat().st_mode | 0o111)


def validate_program(root, candidate):
    entries = {name: (mode, kind, oid) for mode, kind, oid, name in g.tree(root, candidate)}
    for name in ('mask.py', 'mask_core.py', 'mask_fs.py', 'mask_git.py', 'mask_install.py', 'mask_ensure.py', 'mask_integration.py', 'mask_report.py', 'mask_sources.py'):
        if name not in entries or entries[name][0] not in ('100644', '100755') or entries[name][1] != 'blob':
            c.fail('source.candidate_invalid', 'Program candidate is missing a regular runtime module.', 4)
    try:
        source = c.git(root, 'cat-file', 'blob', entries['mask.py'][2], binary=True).decode('utf-8')
        assignments = {node.targets[0].id: ast.literal_eval(node.value) for node in ast.parse(source).body if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'PROTOCOL_VERSION'}
        if assignments.get('PROTOCOL_VERSION') != 1:
            raise ValueError('protocol')
        # Preserve exact contracts apart from Git's LF/CRLF checkout conversion.
        candidate_schemas = {name: (mode, oid) for mode, kind, oid, name in g.tree(root, candidate, 'schemas')}
        for path in sorted((root / 'schemas').glob('*.schema.json')):
            mode, oid = candidate_schemas.get(path.name, ('', ''))
            if mode not in ('100644', '100755') or c.git(root, 'cat-file', 'blob', oid, binary=True).replace(b'\r\n', b'\n') != path.read_bytes().replace(b'\r\n', b'\n'):
                raise ValueError('schema')
    except (ValueError, SyntaxError, UnicodeError, c.MaskError):
        c.fail('source.candidate_invalid', 'Program protocol or schema migration requires explicit review.', 4)


def on_path(path):
    found = shutil.which('mask')
    return bool(found and path.exists() and os.path.samefile(found, path))


def dispatch(args, output, home, root):
    state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
    config_raw = c.read_json(home / 'config.json', default={})
    config = c.config(config_raw) if config_raw else None
    if args.command == 'self.status':
        output['data'] = dict(program_root=str(root), interpreter=sys.executable, launchers=state['launchers'], path_command=shutil.which('mask'))
        return
    intent = dict(operation=args.command, selected=[], links=[], manifests=[], before_state=state, after_state=copy.deepcopy(state), config=config)
    planned = dict(applicable=True, blockers=[], would_change=False, intent=intent)
    if args.command == 'self.install':
        directory = Path(args.bin_dir).expanduser().absolute()
        path = directory / ('mask.cmd' if os.name == 'nt' else 'mask')
        c.parents_safe(Path(path.anchor), path)
        if c.kind(directory) == 'missing' and c.kind(directory.parent) != 'directory':
            c.fail('config.invalid', 'Create the parent of the selected bin directory first.')
        record = dict(program_root=str(root), interpreter=str(Path(sys.executable).resolve()))
        content = launcher_text(record)
        record['content_digest'] = c.digest(content.encode())
        actual = c.read_text(path, 'launcher', missing=True)
        old = state['launchers'].get(str(path))
        if actual is not None and (old is None or actual != launcher_text(old) or c.digest(actual.encode()) != old['content_digest']):
            c.fail('launcher.collision', 'Existing launcher is unrelated or edited; preserve it.', 4, path=str(path))
        intent['after_state']['launchers'][str(path)] = record
        planned['would_change'] = actual != content or state != intent['after_state'] or os.name != 'nt' and not os.access(path, os.X_OK)
        output['data'] = dict(launcher=str(path), interpreter=record['interpreter'], on_path=on_path(path))
        if not planned['would_change']:
            return
        intent['after_state']['generation'] += 1
        output['actions'] = [dict(kind='launcher.install', path=str(path), status='planned')]
        output['would_change'] = True
        if output['dry_run']:
            return
        pending = fs.make_pending(planned, home)
        pending['launcher'] = dict(path=str(path))
        pending['directories'] = [str(directory)] if c.kind(directory) == 'missing' else []
        fs.execute(planned, home, output, pending=pending)
        output['data']['on_path'] = on_path(path)
        return
    timeout = (config or {}).get('git_timeout_seconds', 30)
    observed = g.checkout_preconditions(root, 'origin', 'main', 'ManageAgentSkills', timeout)
    if not output['dry_run']:
        g.fetch(root, 'origin', 'main', timeout, output)
        observed = g.checkout_preconditions(root, 'origin', 'main', 'ManageAgentSkills', timeout)
    if observed['candidate'] is None or observed['relation'] in ('ahead', 'diverged'):
        c.fail('source.' + (observed['relation'] if observed['candidate'] else 'remote_unknown'), 'Program cannot fast-forward from the known remote.', 4)
    validate_program(root, observed['candidate'])
    changed = observed['revision'] != observed['candidate']
    output['would_change'] = changed
    output['data'].update(program_before=observed['revision'], program_after=observed['revision'], requires_fetch=output['dry_run'], remote_freshness='last_fetched', next_invocation_required=False)
    if not changed or output['dry_run']:
        return
    current = g.checkout_preconditions(root, 'origin', 'main', 'ManageAgentSkills', timeout)
    if current['revision'] != observed['revision']:
        c.fail('plan.stale', 'Program changed before update.', 4)
    planned['would_change'] = True
    pending = fs.make_pending(planned, home)
    pending['git'] = dict(scope='program', root=str(root), before=observed['revision'], candidate=observed['candidate'])
    fs.validate_pending(pending, home)
    c.atomic_text(home / 'pending.json', c.text_json(pending), None)
    g.advance(root, observed['candidate'], pending, home, output, timeout)
    fs.execute(planned, home, output, pending=pending)
    output['data'].update(program_after=observed['candidate'], next_invocation_required=True)
