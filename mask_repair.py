"""Explicit all-scope repair and durable backups for typed native role replacement.

Repair broadens a manual ensure or upgrade's declared-role authority. It does not
invent consumer inputs, follow unsafe destinations, change persistent approval,
or replay package scripts during recovery. Existing transaction before-bytes
remain the rollback source; backups survive both success and rollback.
"""
from __future__ import annotations

import copy
from pathlib import Path
import re

import mask_core as c
import mask_workflow as workflow

UUID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')


def retired_files(root, reports, repair=False):
    """Observe bounded retired files. Only explicit repair produces deletion intents."""
    writes = []
    active_inputs = [row['path'] for report in reports for row in report['inputs']]
    for report in reports:
        retired = report.pop('retired_paths', [])
        if not retired:
            continue
        report['retired_files'] = []
        for relative in retired:
            row = dict(path=relative, state='absent')
            report['retired_files'].append(row)
            if any(relative == item or relative.startswith(item + '/') or item.startswith(relative + '/') for item in active_inputs):
                row['state'] = 'active_input'
                continue
            path = Path(root) / relative
            try:
                c.parents_safe(Path(root), path)
                kind = c.kind(path)
                if kind == 'missing':
                    continue
                row['state'] = 'unsafe'
                if kind != 'file' or path.stat().st_size > workflow.ASSET_BYTES:
                    continue
                text = path.read_bytes().decode('utf-8')
            except (c.MaskError, UnicodeError):
                continue
            row.update(state='present', sha256=workflow.sha256(text.encode('utf-8')))
            if relative == workflow.legacy_lock_relative(report['skill']) and c.kind(Path(root) / workflow.lock_relative(report['skill'])) == 'missing':
                row['state'] = 'in_use'
            elif repair and report['complete']:
                row['state'] = 'remove_planned'
                writes.append(dict(root=str(root), skill=report['skill'], relative=relative, before=text, after=None))
    return writes


def validate_retired(pending):
    entries = pending['retired_files']
    if pending['operation'] not in ('ensure', 'upgrade') or not isinstance(entries, list) or not entries or len(entries) > 4096:
        c.fail('recovery.conflict', 'Unsafe retired-file repair journal.', 8)
    seen = set()
    for entry in entries:
        c.fields(entry, ('root', 'skill', 'relative', 'before', 'after'), family='recovery')
        c.skill_id(entry['skill'])
        try:
            workflow.retired_path(entry['relative'], entry['skill'])
        except c.MaskError:
            c.fail('recovery.conflict', 'Unsafe retired-file repair path.', 8)
        key = (entry['root'], entry['relative'])
        record = c.consumer_records(pending['after_state']).get(entry['root'], {})
        if (entry['root'] not in pending['selected'] or key in seen or entry['after'] is not None
                or not isinstance(entry['before'], str) or len(entry['before'].encode('utf-8')) > workflow.ASSET_BYTES
                or not any(link['skill'] == entry['skill'] for link in record.get('links', {}).values())):
            c.fail('recovery.conflict', 'Invalid retired-file repair transition.', 8)
        seen.add(key)


def check_retired(pending):
    for entry in pending.get('retired_files', []):
        if workflow.current_text(entry) not in (entry['before'], None):
            c.fail('recovery.conflict', 'A retired file changed after repair planning.', 8, path=entry['relative'])


def check_retired_snapshot(before, after):
    """Setup must not turn concurrent changes into newly authorized cleanup bytes."""
    observed = {(entry['root'], row['path']): row.get('sha256')
                for entry in before.get('workflow_readiness', []) for report in entry['skills']
                for row in report.get('retired_files', [])}
    for entry in after['intent'].get('retired_files', []):
        if observed.get((entry['root'], entry['relative'])) != workflow.sha256(entry['before'].encode('utf-8')):
            c.fail('plan.stale', 'A retired file changed during setup; cleanup was preserved. Setup may already have published roles.', 4, path=entry['relative'])


def restore_retired(pending, side):
    for entry in pending.get('retired_files', []):
        workflow.set_role(entry, side)


def backup_files(pending, home):
    files = [(entry['root'], entry['relative'], entry['before'])
             for entry in pending.get('native_roles', []) if entry.get('repair')]
    files.extend((entry['root'], entry['relative'], entry['before']) for entry in pending.get('retired_files', []))
    setup = pending.get('setup') or {}
    lock = setup.get('lock') or {}
    if setup.get('granted_by') in ('repair', 'approve-plan', 'prompt') and lock.get('before') is not None and lock['before'] != lock['after']:
        files.append((setup['root'], lock['relative'], lock['before']))
    if not files:
        return []
    if not UUID.fullmatch(pending['transaction_id']):
        c.fail('recovery.conflict', 'Unsafe repair backup identity.', 8)
    directory = home / 'backups' / pending['transaction_id']
    result = []
    for root, relative, content in files:
        consumer = c.digest(root).removeprefix('sha256:')[:16]
        path = directory / consumer / relative
        c.parents_safe(home, path)
        result.append(dict(original=str(Path(root) / relative), path=str(path), content=content,
                           sha256=c.digest(content.encode('utf-8'))))
    return result


def backup_records(pending, home):
    return [dict(original=row['original'], path=row['path'], directory=str(home / 'backups' / pending['transaction_id']), sha256=row['sha256'], state='planned')
            for row in backup_files(pending, home)]


def save_backups(pending, home):
    files = backup_files(pending, home)
    if not files:
        return
    manifest = home / 'backups' / pending['transaction_id'] / 'manifest.json'
    entries = [dict(original=row['original'], backup=row['path'], sha256=row['sha256']) for row in files]
    # Journal-derived names only. A preexisting backup must have the exact original
    # bytes; an edited backup is a recovery conflict, never something to overwrite.
    for path, content in [(Path(row['path']), row['content']) for row in files] + [(manifest, c.text_json(dict(files=entries)))]:
        c.parents_safe(home, path)
        if c.kind(path) not in ('missing', 'file'):
            c.fail('recovery.conflict', 'Repair backup path is occupied; nothing was overwritten.', 8, path=str(path))
        actual = c.read_text(path, 'recovery', missing=True)
        if actual is not None:
            if actual != content:
                c.fail('recovery.conflict', 'Repair backup was changed; it is preserved.', 8, path=str(path))
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        c.parents_safe(home, path)
        c.atomic_text(path, content, None)


def backup_status(records):
    for row in records:
        path = Path(row['path'])
        try:
            row['state'] = 'saved' if c.kind(path) == 'file' and c.digest(path.read_bytes()) == row['sha256'] else 'not_saved'
        except OSError:
            row['state'] = 'unknown'


def ensure_all(args, output, home, ensure):
    """Try every registered project and the personal scope; retain each verdict."""
    if getattr(args, 'expect_plan_hash', None):
        c.fail('invocation.invalid', '--all --repair authorizes a fresh repair of each scope; omit --expect-plan-hash or select one scope.', 2)
    state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
    scopes = [('project', root) for root in sorted(state['projects'])]
    if state.get('user'):
        scopes.append(('user', state['user']['root']))
    data = output['data'] = dict(repair=True, repair_results=[], workflow_readiness=[], scope_readiness=[], backups=[], preparation=[], setup=dict(actions=[]))
    stopped = False
    for scope, root in scopes:
        child = dict(output, data={}, actions=[], warnings=[], error=None, changed=False, would_change=False, transaction='not_needed')
        selected = copy.copy(args)
        selected.all = False
        selected.user = scope == 'user'
        selected.project = root if scope == 'project' else None
        interrupted = False
        try:
            if stopped:
                c.fail('recovery.required', 'A prior scope needs transaction recovery; this scope was not attempted.', 8)
            c.registered_root(Path(root), c.consumer_records(state)[root], scope)
            ensure(selected, child, home)
        except c.MaskError as error:
            child['error'] = error.as_dict()
            stopped = c.kind(home / 'pending.json') != 'missing'
        except KeyboardInterrupt:
            child['error'] = c.MaskError('invocation.interrupted', 'Repair interrupted in this scope.', 130).as_dict()
            interrupted = True
        row = dict(root=root, scope=scope, ok=child['error'] is None, changed=child['changed'],
                   readiness=child['data'].get('readiness', 'blocked'), error=child['error'])
        data['repair_results'].append(row)
        for key in ('workflow_readiness', 'scope_readiness', 'backups', 'preparation'):
            data[key].extend(child['data'].get(key) or [])
        data['setup']['actions'].extend((child['data'].get('setup') or {}).get('actions') or [])
        output['actions'].extend(child['actions'])
        output['warnings'].extend(child['warnings'])
        output['changed'] |= child['changed']
        output['would_change'] |= child['would_change'] or bool((child['data'].get('setup') or {}).get('actions'))
        if child['transaction'] == 'partial':
            output['transaction'] = 'partial'
        elif child['changed'] and child['transaction'] != 'not_started' and output['transaction'] != 'partial':
            # A scope that refused with only retained preparation applied no consumer transaction (MASK-0112).
            output['transaction'] = 'committed'
        if interrupted:
            if c.kind(home / 'pending.json') != 'missing':
                output['transaction'] = 'partial'
            raise KeyboardInterrupt
    failed = sum(not row['ok'] for row in data['repair_results'])
    data.update(readiness='repair_incomplete' if failed else 'ready', ready_count=sum(row['ok'] for row in data['repair_results']), failed=failed)
    if failed:
        c.fail('repair.incomplete', f'{len(scopes) - failed} of {len(scopes)} scopes are ready; {failed} still need attention.', 4)
