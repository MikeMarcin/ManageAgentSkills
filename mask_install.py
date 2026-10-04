"""Owned portable launchers and independent, compatibility-checked program updates."""
from __future__ import annotations

import ast
import copy
import json
import os
from pathlib import Path
import shlex
import shutil
import sys

import mask_core as c
import mask_fs as fs
import mask_git as g


# The launchers self install writes. Windows has two: mask.cmd for PowerShell and cmd, and an extensionless
# sh launcher because Git Bash runs a #! file by its bare name but never a .cmd. The first one is required.
LAUNCHERS = ('mask.cmd', 'mask') if os.name == 'nt' else ('mask',)


def launcher_text(record, path):
    """The launcher at ``path``: a batch file when its name ends in .cmd, otherwise a POSIX sh script."""
    interpreter, entry = record['interpreter'], str(Path(record['program_root']) / 'mask.py')
    if any(char in interpreter + entry for char in '\r\n\x00'):
        c.fail('config.invalid', 'Unsupported launcher path characters.')
    if Path(path).suffix.lower() == '.cmd':
        interpreter, entry = interpreter.replace('%', '%%'), entry.replace('%', '%%')
        return f'@echo off\r\nrem MASK owned launcher v1\r\nsetlocal DisableDelayedExpansion\r\n"{interpreter}" "{entry}" %*\r\nexit /b %errorlevel%\r\n'
    if os.name == 'nt':  # Git Bash reads C:/forward/slash paths; LF endings come from c.atomic_text.
        interpreter, entry = Path(interpreter).as_posix(), Path(entry).as_posix()
    return f'#!/bin/sh\n# MASK owned launcher v1\nexec {shlex.quote(interpreter)} {shlex.quote(entry)} "$@"\n'


def validate_launcher_intent(pending):
    c.fields(pending['launcher'], ('path',), family='recovery')
    key = pending['launcher']['path']
    before, after = pending['before_state'], pending['after_state']
    record = after['launchers'].get(key) if pending['operation'] == 'self.install' else before['launchers'].get(key) if key not in after['launchers'] else None
    if pending['operation'] not in ('self.install', 'self.uninstall') or pending['selected'] or pending['links'] or pending['manifests'] or before['projects'] != after['projects'] or not record:
        c.fail('recovery.conflict', 'Invalid launcher transaction scope.', 8)
    if record['program_root'] != str(Path(__file__).resolve().parent) or Path(key).name not in LAUNCHERS:
        c.fail('recovery.conflict', 'Launcher does not belong to this program.', 8)
    for side in (before, after):
        for path, item in side['launchers'].items():
            if path != key and before['launchers'].get(path) != after['launchers'].get(path):
                c.fail('recovery.conflict', 'Launcher intent changes unrelated ownership.', 8)
        item = side['launchers'].get(key)
        if item and c.digest(launcher_text(item, key).encode()) != item['content_digest']:
            c.fail('recovery.conflict', 'Launcher record does not describe recognized content.', 8)


def launcher_values(pending):
    key = pending['launcher']['path']
    return [launcher_text(pending[side + '_state']['launchers'][key], key) if key in pending[side + '_state']['launchers'] else None for side in ('before', 'after')]


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


RUNTIME_MODULES = ('mask.py', 'mask_core.py', 'mask_fs.py', 'mask_git.py', 'mask_install.py', 'mask_ensure.py', 'mask_integration.py', 'mask_report.py', 'mask_present.py', 'mask_sources.py', 'mask_packages.py', 'mask_process.py', 'mask_provenance.py', 'mask_resolve.py', 'mask_store.py', 'mask_pinned.py', 'mask_selection.py', 'mask_adapters.py', 'mask_consent.py', 'mask_task.py', 'mask_workflow.py', 'mask_setup.py', 'mask_repair.py', 'mask_update.py', 'mask_cli.py', 'mask_lifecycle.py', 'mask_cleanup.py', 'mask_pin.py', 'mask_progress.py')
# Annotation keywords: changing only these never changes what a document must contain.
ANNOTATIONS = {'$comment', 'description', 'title', 'examples'}
# Schemas that describe MASK's own command output; no saved file is validated against them.
OUTPUT_SCHEMAS = {'result.schema.json'}
# Bounds that an additive change may widen: an upper bound may grow and a lower bound may shrink.
UPPER = {'maxItems', 'maxLength', 'maxProperties', 'maximum', 'exclusiveMaximum'}
LOWER = {'minItems', 'minLength', 'minProperties', 'minimum', 'exclusiveMinimum'}


def protocol_version(root, revision):
    """The program's PROTOCOL_VERSION at one commit; a candidate without a readable one is not a MASK program."""
    entries = {name: (mode, kind, oid) for mode, kind, oid, name in g.tree(root, revision)}
    for name in RUNTIME_MODULES:
        if name not in entries or entries[name][0] not in ('100644', '100755') or entries[name][1] != 'blob':
            c.fail('source.candidate_invalid', f'MASK {revision[:7]} is missing its runtime module {name}.', 4, candidate=revision)
    try:
        source = c.git(root, 'cat-file', 'blob', entries['mask.py'][2], binary=True).decode('utf-8')
        found = [ast.literal_eval(node.value) for node in ast.parse(source).body if isinstance(node, ast.Assign) and len(node.targets) == 1
                 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == 'PROTOCOL_VERSION']
    except (ValueError, SyntaxError, UnicodeError):
        found = []
    if len(found) != 1 or type(found[0]) is not int:
        c.fail('source.candidate_invalid', f'MASK {revision[:7]} has no readable PROTOCOL_VERSION in mask.py.', 4, candidate=revision)
    return found[0]


def schema_blobs(root, revision):
    return {name: oid for mode, kind, oid, name in g.tree(root, revision, 'schemas') if name.endswith('.schema.json') and kind == 'blob'}


def strip_annotations(value):
    if isinstance(value, dict):
        return {key: strip_annotations(item) for key, item in value.items() if key not in ANNOTATIONS}
    if isinstance(value, list):
        return [strip_annotations(item) for item in value]
    return value


def new_rule(key, value, where):
    """Name what a constraint keyword added where there was none now governs, in the reader's terms."""
    names = sorted(value) if isinstance(value, (dict, list)) and all(isinstance(name, str) for name in value) else []
    subjects = ', '.join(where(name) for name in names[:2]) + (f' and {len(names) - 2} more' if len(names) > 2 else '')
    if key == 'properties' and names:
        return f'now constrains {subjects}'
    if key == 'required' and names:
        return f'now requires {subjects}'
    return f'adds a {key} rule to {where()}'


def widening(old, new, path, added, narrowed):
    """Walk an annotation-free schema pair; record each added optional property and each narrowing."""
    def where(key=None):
        return '.'.join(path + ([key] if key else [])) or 'the root'
    if isinstance(old, dict) and isinstance(new, dict):
        required = set(new.get('required', [])) if isinstance(new.get('required'), list) else set()
        for key in sorted(old.keys() | new.keys()):
            if key not in new:
                narrowed.append(f'removes {where(key)}' if key in ('properties', '$defs', 'definitions') else f'drops {key} at {where()}')
            elif key not in old:
                narrowed.append(new_rule(key, new[key], where))
            elif key in ('properties', '$defs', 'definitions') and isinstance(old[key], dict) and isinstance(new[key], dict):
                for name in sorted(old[key].keys() | new[key].keys()):
                    if name not in new[key]:
                        narrowed.append(f'removes {where(name)}')
                    elif name not in old[key]:
                        if key == 'properties' and name in required:
                            narrowed.append(f'requires new {where(name)}')
                        else:
                            added.append(where(name) if key == 'properties' else f'{where(name)} definition')
                    else:
                        widening(old[key][name], new[key][name], path + [name], added, narrowed)
            elif key == 'required' and isinstance(old[key], list) and isinstance(new[key], list):
                extra = [name for name in new[key] if name not in old[key] and name in (old.get('properties') or {})]
                if extra:
                    narrowed.append(f'now requires {where(extra[0])}')
            elif key in ('enum', 'type') and isinstance(old[key], (list, str)) and isinstance(new[key], (list, str)):
                before, after = ({old[key]} if isinstance(old[key], str) else old[key]), ({new[key]} if isinstance(new[key], str) else new[key])
                if not all(item in after for item in before):
                    narrowed.append(f'narrows {key} of {where()}')
            elif key in UPPER | LOWER and type(old[key]) in (int, float) and type(new[key]) in (int, float):
                if (new[key] < old[key]) if key in UPPER else (new[key] > old[key]):
                    narrowed.append(f'tightens {key} of {where()}')
            elif isinstance(old[key], dict) and isinstance(new[key], dict):
                widening(old[key], new[key], path, added, narrowed)
            elif old[key] != new[key]:
                narrowed.append(f'changes {key} at {where()}')
        return
    if old != new:
        narrowed.append(f'changes {where()}')


def schema_change(before, after):
    """Classify one schema file change as comment, additive or breaking, with a few plain words to say why."""
    if after is None:
        return 'breaking', 'removed'
    if before is None:
        return 'additive', 'new schema'
    try:
        old, new = (json.loads(raw.replace(b'\r\n', b'\n').decode('utf-8')) for raw in (before, after))
    except (ValueError, UnicodeError):
        return 'breaking', 'no longer readable JSON'
    old, new = strip_annotations(old), strip_annotations(new)
    if old == new:
        return 'comment', 'wording only'
    added, narrowed = [], []
    widening(old, new, [], added, narrowed)
    if narrowed:
        return 'breaking', narrowed[0] + (f' (+{len(narrowed) - 1} more)' if len(narrowed) > 1 else '')
    if not added:
        return 'breaking', 'changes its rules'
    names = ', '.join(added[:2]) + (f' and {len(added) - 2} more' if len(added) > 2 else '')
    return 'additive', f'adds optional {names}'


def program_migration(root, before, candidate):
    """What moving the program from before to candidate changes in its contracts, and the consent hash binding exactly that."""
    protocol = dict(before=protocol_version(root, before), after=protocol_version(root, candidate))
    old, new = schema_blobs(root, before), schema_blobs(root, candidate)
    schemas = []
    for name in sorted(old.keys() | new.keys()):
        if old.get(name) == new.get(name):
            continue
        raw = [c.git(root, 'cat-file', 'blob', blob, binary=True) if blob else None for blob in (old.get(name), new.get(name))]
        if None not in raw and raw[0].replace(b'\r\n', b'\n') == raw[1].replace(b'\r\n', b'\n'):
            continue
        change, summary = schema_change(*raw)
        schemas.append(dict(file=name, change=change, summary=summary, audience='output' if name in OUTPUT_SCHEMAS else 'files',
                            before_blob=old.get(name), after_blob=new.get(name)))
    count = c.git(root, 'rev-list', '--count', f'{before}..{candidate}', optional=True)
    breaking = protocol['before'] != protocol['after'] or any(row['change'] == 'breaking' for row in schemas)
    migration = dict(before=before, candidate=candidate, commits=int(count) if count and count.isdigit() else None, protocol=protocol,
                     schemas=schemas, breaking=breaking, requires_consent=breaking or any(row['change'] != 'comment' for row in schemas))
    migration['plan_hash'] = c.digest(dict(kind='program.migration', before=before, candidate=candidate, protocol=protocol,
                                           schemas=[(row['file'], row['before_blob'], row['after_blob']) for row in schemas]))
    return migration


def migration_proposal(root, migration):
    import mask_consent as consent
    proposal = consent.request('program.migration', 'this update changes the contracts MASK reads and writes', [str(root)],
                               [dict(kind='program.update', path=str(root), before=migration['before'], after=migration['candidate'])],
                               migration['plan_hash'], f"Update MASK to {migration['candidate'][:7]}?")
    proposal['migration'] = migration
    return proposal


def on_path(path):
    found = shutil.which('mask')
    return bool(found and path.exists() and os.path.samefile(found, path))


def uninstall(output, home, root, state, config):
    """Remove the launchers this program wrote, each through the launcher journal; an edited launcher is somebody's file and stays.

    MASK never deletes directories it did not create file by file, so the program clone, MASK_HOME and the links in
    your projects are reported with the commands that remove them, not removed.
    """
    removable, kept = [], []
    for path, record in sorted(state['launchers'].items()):
        actual = c.read_text(Path(path), 'launcher', missing=True)
        if actual is not None and (actual != launcher_text(record, path) or c.digest(actual.encode()) != record['content_digest']):
            kept.append(dict(path=path, reason='edited since MASK wrote it'))
        else:
            removable.append(path)
    consumers = c.consumer_records(state)
    output['data'] = dict(removed=[], kept=kept, program_root=str(root), home=str(home),
                          linked_consumers=sorted(path for path, record in consumers.items() if record.get('links')))
    output['would_change'] = bool(removable)
    output['actions'] = [dict(kind='launcher.remove', path=path, status='planned') for path in removable]
    if output['dry_run']:
        output['data']['removed'] = removable
        return
    for index, path in enumerate(removable):
        state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
        after = copy.deepcopy(state)
        del after['launchers'][path]
        after['generation'] += 1
        intent = dict(operation='self.uninstall', selected=[], links=[], manifests=[], before_state=state, after_state=after, config=config)
        pending = fs.make_pending(dict(applicable=True, blockers=[], would_change=True, intent=intent), home)
        pending['launcher'] = dict(path=path)
        pending['directories'] = []
        fs.execute(dict(applicable=True, blockers=[], would_change=True, intent=intent), home, output, pending=pending)
        output['actions'][index]['status'] = 'applied'
        output['data']['removed'].append(path)


def install(args, output, home, root, state, config):
    """Write this program's launchers into a bin directory, each through its own launcher journal, as uninstall removes them.

    An unrelated or edited first launcher refuses before anything is written. A later one (the Git Bash ``mask``
    on Windows) that is somebody else's file is kept and reported, and the others are still written.
    """
    directory = Path(args.bin_dir).expanduser().absolute()
    paths = [directory / name for name in LAUNCHERS]
    for path in paths:
        c.parents_safe(Path(path.anchor), path)
    if c.kind(directory) == 'missing' and c.kind(directory.parent) != 'directory':
        c.fail('config.invalid', 'Create the parent of the selected bin directory first.')
    record = dict(program_root=str(root), interpreter=str(Path(sys.executable).resolve()))
    writes, kept = [], []
    for path in paths:
        content = launcher_text(record, path)
        wanted = dict(record, content_digest=c.digest(content.encode()))
        actual = c.read_text(path, 'launcher', missing=True)
        old = state['launchers'].get(str(path))
        if actual is not None and (old is None or actual != launcher_text(old, path) or c.digest(actual.encode()) != old['content_digest']):
            if path == paths[0]:
                c.fail('launcher.collision', 'Existing launcher is unrelated or edited; preserve it.', 4, path=str(path))
            kept.append(dict(path=str(path), reason='an unrelated or edited file is already there'))
            continue
        if actual != content or old != wanted or os.name != 'nt' and not os.access(path, os.X_OK):
            writes.append((path, wanted))
    output['data'] = dict(launcher=str(paths[0]), launchers=[str(path) for path in paths if str(path) not in {row['path'] for row in kept}],
                          kept=kept, interpreter=record['interpreter'], on_path=on_path(paths[0]))
    for row in kept:
        output['warnings'].append(dict(code='launcher.collision', message=f"{row['path']} is unrelated or edited; it was kept and not replaced.", path=row['path']))
    if not writes:
        return
    output['actions'] = [dict(kind='launcher.install', path=str(path), status='planned') for path, _ in writes]
    output['would_change'] = True
    if output['dry_run']:
        return
    for index, (path, wanted) in enumerate(writes):
        current = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
        after = copy.deepcopy(current)
        after['launchers'][str(path)] = wanted
        after['generation'] += 1
        intent = dict(operation='self.install', selected=[], links=[], manifests=[], before_state=current, after_state=after, config=config)
        planned = dict(applicable=True, blockers=[], would_change=True, intent=intent)
        pending = fs.make_pending(planned, home)
        pending['launcher'] = dict(path=str(path))
        pending['directories'] = [str(directory)] if c.kind(directory) == 'missing' else []
        try:
            fs.execute(planned, home, output, pending=pending)
        except (Exception, KeyboardInterrupt):
            for done in output['actions'][:index]:
                done['status'] = 'applied'
            for rest in output['actions'][index + 1:]:
                rest['status'] = 'not_applied'
            raise
    output['data']['on_path'] = on_path(paths[0])


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
        return install(args, output, home, root, state, config)
    if args.command == 'self.uninstall':
        return uninstall(output, home, root, state, config)
    timeout = (config or {}).get('git_timeout_seconds', 30)
    # Uncommitted work is held only where the fast-forward would touch it (blocking); the rest stays in place.
    observed = g.checkout_preconditions(root, 'origin', 'main', 'ManageAgentSkills', timeout, clean=False)
    if not output['dry_run']:
        g.fetch(root, 'origin', 'main', timeout, output)
        observed = g.checkout_preconditions(root, 'origin', 'main', 'ManageAgentSkills', timeout, clean=False)
    if observed['candidate'] is None or observed['relation'] in ('ahead', 'diverged'):
        c.fail('source.' + (observed['relation'] if observed['candidate'] else 'remote_unknown'), 'Program cannot fast-forward from the known remote.', 4)
    changed = observed['revision'] != observed['candidate']
    output['would_change'] = changed
    output['data'].update(program_before=observed['revision'], program_after=observed['revision'], requires_fetch=output['dry_run'], remote_freshness='last_fetched', next_invocation_required=False)
    local = g.local_changes(root, timeout) if changed and observed['dirty'] else []
    blocking = g.blocking_paths(root, observed['candidate'], local, timeout)
    stashing = bool(blocking) and getattr(args, 'stash', False)
    if blocking and not stashing:
        c.fail('source.dirty', 'Local changes touch files this update changes; commit them, or move just them aside with mask update --stash.', 4,
               blocking_paths=blocking, preserved=[path for path in local if path not in blocking])
    if local:
        output['data']['preserved'] = [path for path in local if path not in blocking]
    if stashing:
        output['data']['stash'] = dict(root=str(root), paths=blocking, message=None, commit=None, inspect=None)
    migration = program_migration(root, observed['revision'], observed['candidate']) if changed else None
    if migration and (migration['schemas'] or migration['breaking']):
        output['data']['program_migration'] = migration
    if not changed or output['dry_run']:
        return
    if migration['requires_consent']:
        import mask_consent as consent
        if getattr(args, 'expect_plan_hash', None) not in (None, migration['plan_hash']):
            c.fail('plan.stale', 'The approved hash is not this update; review it again with mask update.', 4, plan_hash=migration['plan_hash'])
        consent.require(args, output, migration_proposal(root, migration))
    current = g.checkout_preconditions(root, 'origin', 'main', 'ManageAgentSkills', timeout, clean=False)
    if current['revision'] != observed['revision']:
        c.fail('plan.stale', 'Program changed before update.', 4)
    now = g.local_changes(root, timeout) if current['dirty'] else []
    if g.blocking_paths(root, observed['candidate'], now, timeout) != blocking:
        c.fail('plan.stale', 'Local changes in the program checkout moved during update; run it again.', 4)
    if now:
        output['data']['preserved'] = [path for path in now if path not in blocking]
    planned['would_change'] = True
    pending = fs.make_pending(planned, home)
    pending['git'] = dict(scope='program', root=str(root), before=observed['revision'], candidate=observed['candidate'])
    if migration['requires_consent']:
        pending['git']['consent'] = migration['plan_hash']  # Recovery completes this approved candidate without asking again.
    if stashing:  # Journaled before Git runs, so an interruption names the stash it may have made.
        pending['git']['stash'] = dict(message=g.stash_message(observed['revision'], observed['candidate']), paths=blocking)
    fs.validate_pending(pending, home)
    c.atomic_text(home / 'pending.json', c.text_json(pending), None)
    if stashing:
        g.stash(root, pending, home, output, timeout)
        output['data']['stash'] = g.stash_report(root, pending['git']['stash'], timeout)
    g.advance(root, observed['candidate'], pending, home, output, timeout)
    fs.execute(planned, home, output, pending=pending)
    output['data'].update(program_after=observed['candidate'], next_invocation_required=True)
