"""Approved staged setup for generated native roles (RFC-MASK-0019 AC04/AC05).

A package may declare that a native role is produced by a Python setup action
instead of shipping its bytes. MASK offers such an action only when a selected
generated role has no coherent checked-in lock, only under exact consent
(``package.setup`` through ``mask_consent``; never ``--yes``, never a check, dry
run, event or redirected invocation), and runs it through one fixed interface:
the selected MASK interpreter, the entrypoint frozen in a task-private copy of
the selected package, ``--repo-root``/``--output-root``/``--request-file`` as
separate arguments, an inert JSON request, an owned process tree with bounded
wall time and output. The script only stages ``STAGE/AGENT/NAME.ext`` files; MASK
validates the complete output set, computes the portable lock and publishes
through the ordinary typed journal in ``mask_fs``, which derives every host
destination. This is ordinary user process execution, not a security sandbox,
and MASK never reruns package code from a journal: an interrupted launch is
reported and discarded, not replayed.
"""
from __future__ import annotations

import os
from pathlib import Path
import platform
import re
import shutil
import sys
import uuid

import mask_core as c
import mask_adapters as adapters
import mask_consent as consent
import mask_fs as fs
import mask_workflow as workflow

REQUEST_SCHEMA = 'mask.setup-request.v1'
LOCK_SCHEMA = 'mask.native-role-lock.v1'
STAGING = 'staging'
STREAM_BYTES = 64 * 1024
EXCERPT_CHARS = 4096
SNAPSHOT_FILES = 4096
SNAPSHOT_BYTES = 32 * 1024 * 1024
PHASES = ('launched', 'staged')
UUID_RE = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
UNKNOWN_EFFECTS = 'the script ran; nothing was published and script side effects outside the stage are unknown'
# Everything a consent hash binds for one action: a change in any of these is a stale proposal.
FROZEN = ('root', 'scope', 'skill', 'coordinate', 'action', 'entrypoint', 'timeout_seconds', 'native_roles', 'inputs',
          'parameters', 'package_sha256', 'descriptor_sha256', 'role_inputs_sha256', 'interpreter')


def interpreter():
    if not sys.executable:
        c.fail('setup.failed', 'The running interpreter has no executable path; setup cannot be frozen.', 5)
    return dict(executable=sys.executable, version=platform.python_version())


def package_files(root):
    """Regular files of a package directory, bounded; links and special entries are refused, never followed."""
    root = Path(root)
    files, total = [], 0
    def walk(directory):
        nonlocal total
        for entry in sorted(directory.iterdir()):
            observed = c.kind(entry)
            if entry.name == '__pycache__' or entry.suffix in ('.pyc', '.pyo'):
                continue  # Bytecode never enters the frozen snapshot; only the reviewed source runs.
            if observed == 'directory':
                walk(entry)
            elif observed == 'file':
                total += entry.stat().st_size
                files.append(entry)
                if len(files) > SNAPSHOT_FILES or total > SNAPSHOT_BYTES:
                    c.fail('workflow.invalid', 'The package exceeds the setup snapshot bounds.', 4, path=str(root))
            else:
                c.fail('workflow.invalid', 'Package contains a link or special entry; setup cannot freeze it.', 4, path=str(entry))
    if c.kind(root) != 'directory':
        c.fail('workflow.invalid', 'Package content is not a local directory.', 4, path=str(root))
    walk(root)
    return [(path.relative_to(root).as_posix(), path) for path in files]


def snapshot(root, destination=None):
    """Digest of the exact package bytes; with ``destination`` also copies them into the task-private snapshot."""
    digests = {}
    for relative, path in package_files(root):
        data = path.read_bytes()
        digests[relative] = c.digest(data)
        if destination is not None:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    return c.digest(digests)


def describe(entry, report, desc, action_id, roles, package_sha256):
    """The frozen identity of one action for one consumer, plus the disclosure a human or automation reviews."""
    action = desc['setup'][action_id]
    inputs_by_id = {row['id']: row for row in report['inputs']}
    row = dict(root=entry['root'], scope=entry['scope'], skill=report['skill'], coordinate=report['package']['coordinate'], action=action_id,
               subject=f"{report['package']['coordinate']}:{action_id}", entrypoint=action['entrypoint'], path=str(Path(report['package']['root']) / action['entrypoint']),
               timeout_seconds=action['timeout_seconds'], native_roles=[dict(agent=agent, name=name) for agent, name in sorted(roles)],
               inputs=[dict(id=name, path=inputs_by_id[name]['path'], sha256=inputs_by_id[name]['sha256']) for name in action['inputs']],
               parameters=action['parameters'], package_sha256=package_sha256, descriptor_sha256=desc['digest'], role_inputs_sha256=workflow.role_inputs(desc),
               interpreter=interpreter(), state='proposed', granted_by=None)
    row['fingerprint'] = c.digest({key: row[key] for key in FROZEN})
    return row


def proposals(planned, *, repair=False):
    """Setup actions that would complete the planned readiness: one row per (consumer, skill, action)."""
    rows = []
    for entry in planned.get('workflow_readiness', []):
        for report in entry['skills']:
            wanted = {}
            for role in report['roles'] if report['workflow'] == 'declared' else []:
                if role['state'] in (('setup_required', 'modified') if repair else ('setup_required',)) and role['producer'] == 'setup':
                    wanted.setdefault(role['setup'], []).append((role['agent'], role['name']))
            if not wanted:
                continue
            blocked = [row['id'] for row in report['inputs'] if row['state'] in ('missing', 'invalid')]
            if report['package']['root'] is None or blocked:
                rows.append(dict(root=entry['root'], skill=report['skill'], coordinate=report['package']['coordinate'], state='blocked',
                                 detail=f"consumer inputs are missing or invalid: {', '.join(blocked)}" if blocked else 'package content is not a local directory'))
                continue
            package_root = Path(report['package']['root'])
            desc = workflow.descriptor(workflow.PackageView(root=package_root), report['skill'])
            package_sha256 = snapshot(package_root)
            for action_id, roles in sorted(wanted.items()):
                row = describe(entry, report, desc, action_id, roles, package_sha256)
                occupied = [role['path'] for role in report['roles']
                            if (role['agent'], role['name']) in roles and role.get('observed_sha256')
                            and role.get('ownership') != 'package-managed']
                if occupied and not repair:
                    # Consent to run a generator cannot authorize replacing repository files.
                    # Refuse before prompting instead of running an action that loops back here.
                    row.update(state='blocked', paths=occupied,
                               detail='existing role files are not managed by MASK; restore a matching native-role lock or review these files before setup')
                rows.append(row)
    return rows


def disclosure(row):
    """What consent shows: skill, source and content fingerprint, the exact interpreter and script, and the targets."""
    return dict(kind='setup.run', status='planned', skill=row['skill'], coordinate=row['coordinate'], action=row['action'], root=row['root'],
                fingerprint=row['package_sha256'].removeprefix('sha256:')[:12], interpreter=row['interpreter']['executable'], path=row['path'],
                native_roles=[f"{role['agent']}/{role['name']}" for role in row['native_roles']])


def authorize(args, output, planned, rows):
    """Record the setup proposal on the result and settle its authority without running anything."""
    data = output['data']['setup'] = dict(actions=rows)
    live = [row for row in rows if row['state'] == 'proposed']
    if not live:
        return
    proposal = consent.request('package.setup', 'setup.required', sorted({row['root'] for row in live}), [disclosure(row) for row in live],
                               planned['plan_hash'], 'Run this setup?', subjects=[row['subject'] for row in live])
    data['confirmation'] = proposal
    if output['dry_run'] or getattr(args, 'check', False) or getattr(args, 'event', 'manual') != 'manual':
        for row in live:
            row.update(state='not_run', detail='check, dry-run and event invocations never run package code')
        return
    if 'package.setup' in (getattr(args, 'declined', None) or ()):
        for row in live:
            row.update(state='declined', detail='setup was declined; nothing ran and the roles stay incomplete')
        return
    how = 'repair' if getattr(args, 'repair', False) else consent.granted_by(args, proposal)
    if how is None and consent.interactive(args):
        raise consent.ConsentRequired(proposal)
    proposal['granted_by'] = how
    for row in live:
        row.update(state='granted' if how else 'consent_required', granted_by=how)


def request_text(row):
    return c.text_json(dict(schema=REQUEST_SCHEMA, action=row['action'], native_roles=row['native_roles'], inputs=row['inputs'], parameters=row['parameters'], paths=workflow.paths(row['skill'])))


def excerpt(data):
    text = data.decode('utf-8', errors='replace')
    return text if len(text) <= EXCERPT_CHARS else text[:EXCERPT_CHARS] + '...'


def run_action(work, snapshot_root, root, row):
    """Run one frozen action against the stage and return its validated outputs."""
    work.mkdir()
    out = work / 'output'
    out.mkdir()
    request = work / 'request.json'
    request.write_text(request_text(row), encoding='utf-8')
    entrypoint = snapshot_root / row['entrypoint']
    if c.kind(entrypoint) != 'file':
        c.fail('workflow.invalid', 'The setup entrypoint is not a regular file in the frozen package.', 4, path=row['entrypoint'])
    command = [sys.executable, '-B', str(entrypoint), '--repo-root', str(root), '--output-root', str(out), '--request-file', str(request)]
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONPYCACHEPREFIX=str(work / 'pycache'))
    try:
        code, stdout, stderr = c.contained_run(command, environment, timeout=row['timeout_seconds'], max_output=STREAM_BYTES, max_error=STREAM_BYTES,
                                               family='setup', name='Package setup', cwd=str(work))
    except c.MaskError as error:
        if error.code.startswith('setup.'):
            row.update(state='failed', reason=error.code.split('.', 1)[1], detail='the owned process tree was stopped; script side effects outside the stage are unknown')
            c.fail('setup.failed', str(error), 5, action=row['subject'], reason=row['reason'])
        raise
    row.update(stdout=excerpt(stdout), stderr=excerpt(stderr))
    if code:
        row.update(state='failed', reason='exit', exit_status=code, detail='the script exited unsuccessfully; nothing was published')
        c.fail('setup.failed', 'The setup script exited unsuccessfully; nothing was published.', 5, action=row['subject'], reason='exit', exit_status=code)
    return collect_outputs(work, row)


def collect_outputs(work, row):
    """Exactly STAGE/AGENT/NAME.ext per requested role, regular files only; anything else refuses the whole stage."""
    out = work / 'output'
    expected = {}
    for role in row['native_roles']:
        expected.setdefault(role['agent'], {})[Path(adapters.role_relative(role['agent'], row['scope'], role['name'])).name] = role['name']

    def refuse(message, path):
        row.update(state='refused', detail=message)
        c.fail('setup.outputs_invalid', message, 4, action=row['subject'], path=str(path))

    def entries(directory, admitted, directories):
        found = {}
        for entry in os.scandir(directory):
            contained = entry.is_dir(follow_symlinks=False) if directories else entry.is_file(follow_symlinks=False)
            if entry.is_symlink() or not contained or entry.name not in admitted:
                refuse('Unexpected stage entry; only AGENT/NAME.ext regular files for the requested roles are admitted.', entry.path)
            found[entry.name] = Path(entry.path)
        missing = sorted(set(admitted) - set(found))
        if missing:
            refuse('The stage is missing a requested output.', directory / missing[0])
        return found

    for entry in os.scandir(work):
        if entry.is_symlink() or entry.name not in ('request.json', 'output') or (entry.name == 'output') != entry.is_dir(follow_symlinks=False):
            refuse('The stage received an entry outside its output root; only AGENT/NAME.ext regular files under the output root are admitted.', entry.path)
    if c.kind(out) != 'directory':
        refuse('The stage output root was replaced.', out)
    outputs = {}
    for agent, directory in entries(out, expected, True).items():
        for name, path in entries(directory, expected[agent], False).items():
            if path.stat().st_size > workflow.ASSET_BYTES:
                refuse('A staged role exceeds the role size bound.', path)
            data = path.read_bytes()
            try:
                workflow.native(agent, expected[agent][name], data, row['skill'])
            except c.MaskError as error:
                refuse(f'A staged role is not a supported native role: {str(error)}', path)
            outputs[(agent, expected[agent][name])] = data
    return outputs


def vouchable(report):
    """Generated roles whose destination holds the bytes MASK expects once this transaction publishes.

    A transaction stages only the roles that still need setup, so the lock is derived from the whole
    rechecked report rather than from this run's outputs: roles an earlier transaction published stay
    vouched, and a preserved destination is left out instead of being recorded as if it were deployed.
    """
    return [row for row in report['roles']
            if row['producer'] == 'setup' and row['state'] in ('ok', 'missing', 'stale') and row.get('expected_sha256')]


def lock_text(facts, report):
    value = dict(schema_version=1, schema=LOCK_SCHEMA, coordinate=facts['coordinate'], contract_sha256=facts['descriptor_sha256'],
                 role_inputs_sha256=facts['role_inputs_sha256'],
                 parameters_sha256=c.digest({action['action']: action['parameters'] for action in facts['actions']}).removeprefix('sha256:'),
                 inputs={row['id']: row['sha256'] for row in report['inputs']}, input_paths={row['id']: row['path'] for row in report['inputs']},
                 roles=[dict(agent=row['agent'], name=row['name'], sha256=row['expected_sha256']) for row in vouchable(report)])
    return c.text_json(value)


def facts_for(rows):
    first = rows[0]
    return dict(phase='launched', root=first['root'], scope=first['scope'], skill=first['skill'], coordinate=first['coordinate'],
                package_sha256=first['package_sha256'], descriptor_sha256=first['descriptor_sha256'], role_inputs_sha256=first['role_inputs_sha256'],
                interpreter=first['interpreter'], granted_by=first['granted_by'],
                actions=[{key: row[key] for key in ('action', 'entrypoint', 'timeout_seconds', 'native_roles', 'inputs', 'parameters', 'fingerprint')} for row in rows])


def skill_report(planned, root, skill):
    for entry in planned.get('workflow_readiness', []):
        if entry['root'] == root:
            for report in entry['skills']:
                if report['skill'] == skill:
                    return report
    c.fail('plan.stale', 'The selected skill no longer declares a workflow for this consumer.', 4, skill=skill)


def recheck(planned, rows, *, ran=False):
    """The frozen identity must still hold; otherwise nothing (more) runs or publishes.

    Before execution a mismatch is a stale plan. After execution the script's own effects are
    unknown, so the rows say so instead of claiming nothing ran.
    """
    root, skill = rows[0]['root'], rows[0]['skill']
    entry = next((item for item in planned.get('workflow_readiness', []) if item['root'] == root), None)
    if entry is None:
        stale(rows, ran, 'the consumer can no longer be planned (a blocker such as a replaced role directory was observed)')
    report = skill_report(planned, root, skill)
    desc = workflow.descriptor(workflow.PackageView(root=Path(report['package']['root'])), skill) if report['package']['root'] else None
    package_sha256 = snapshot(Path(report['package']['root'])) if report['package']['root'] else None
    for row in rows:
        fresh = describe(entry, report, desc, row['action'], [(role['agent'], role['name']) for role in row['native_roles']], package_sha256) if desc and row['action'] in desc['setup'] else None
        if fresh is None or fresh['fingerprint'] != row['fingerprint']:
            stale(rows, ran, 'the package, descriptor, consumer inputs or interpreter changed')
    return report


def stale(rows, ran, what):
    if ran:
        for item in rows:
            item.update(state='failed', reason='post-run', detail=f'{what} while the script ran; {UNKNOWN_EFFECTS}')
        c.fail('setup.failed', f'Setup inputs changed while the script ran ({what}); nothing was published and script side effects outside the stage are unknown.', 5, action=rows[0]['subject'], reason='post-run')
    for item in rows:
        item.update(state='stale', detail=f'{what} after consent; nothing ran')
    c.fail('plan.stale', 'Setup inputs changed after consent; nothing ran and nothing was published.', 4, action=rows[0]['subject'])


def execute(output, home, replan, rows):
    """Run every granted action per consumer and skill, then publish validated outputs through the typed journal."""
    groups = {}
    for row in rows:
        groups.setdefault((row['root'], row['skill']), []).append(row)
    for _, group in sorted(groups.items()):
        publish(output, home, replan, group)


def publish(output, home, replan, rows):
    root = Path(rows[0]['root'])
    skill = rows[0]['skill']
    base = replan()
    report = recheck(base, rows)
    observed_roles = {(role['agent'], role['name']): role.get('observed_sha256') for role in report['roles']}
    if c.kind(home / 'pending.json') != 'missing':
        c.fail('recovery.required', 'Inspect and recover the pending operation first.', 8)
    transaction = str(uuid.uuid4())
    stage = home / STAGING / transaction
    pending = fs.make_pending(base, home)
    pending.update(transaction_id=transaction, setup=facts_for(rows))
    fs.validate_pending(pending, home)  # Validated before the stage exists, so a refused journal leaves nothing behind.
    launched = c.text_json(pending)
    stage.mkdir(parents=True)
    try:
        c.atomic_text(home / 'pending.json', launched, None)
    except BaseException:
        discard_stage(home, pending)  # No journal was written; the empty stage must not outlive this call.
        raise
    fs.checkpoint('setup.launched')
    ran = False
    try:
        package_root = stage / 'package'
        if snapshot(Path(report['package']['root']), package_root) != rows[0]['package_sha256']:
            c.fail('plan.stale', 'Package bytes changed while freezing the setup snapshot; nothing ran.', 4)
        outputs = {}
        for index, row in enumerate(rows):
            ran = True
            outputs.update(run_action(stage / f'action-{index}', package_root, root, row))
            fs.checkpoint('setup.exited')
        staged = {(skill, agent, name): data for (agent, name), data in outputs.items()}
        after = replan(staged={str(root): staged})
        report = recheck(after, rows, ran=True)
        from mask_repair import check_retired_snapshot
        check_retired_snapshot(base, after)
        if rows[0].get('granted_by') == 'repair':
            for role in report['roles']:
                key = (role['agent'], role['name'])
                if key in outputs and role.get('observed_sha256') != observed_roles.get(key):
                    stale(rows, True, 'a role destination changed during setup')
        lock_relative = workflow.lock_relative(skill)
        lock_path = root / lock_relative
        c.parents_safe(root, lock_path)
        if c.kind(lock_path) not in ('missing', 'file'):
            c.fail('setup.outputs_invalid', 'The consumer lock path is occupied by a link or special entry; it is preserved.', 4, path=str(lock_path))
        lock = dict(relative=lock_relative, before=c.read_text(lock_path, 'workflow', missing=True), after=lock_text(pending['setup'], report))
        after['actions'].append(dict(kind='native_role_lock.write', status='planned', path=str(lock_path), skill=skill))
        after['would_change'] = True
        staged_pending = fs.make_pending(after, home)
        staged_pending.update(transaction_id=transaction, setup=dict(pending['setup'], phase='staged', lock=lock))
        fs.validate_pending(staged_pending, home)
        c.atomic_text(home / 'pending.json', c.text_json(staged_pending), launched)
        output['actions'].extend(after['actions'])
        fs.execute(after, home, output, pending=staged_pending)
        preserved = [f"{role['agent']}/{role['name']}: {role['state']}" for role in report['roles']
                     if (role['agent'], role['name']) in outputs and role['state'] not in ('ok', 'missing', 'stale')]
        for row in rows:
            row.update(state='partial' if preserved else 'published', detail='preserved without publication: ' + ', '.join(preserved) if preserved else 'staged outputs were validated and published; readiness is rechecked below')
    except (Exception, KeyboardInterrupt) as error:
        if isinstance(error, c.MaskError) and error.code == 'recovery.required':
            raise  # An unconfirmed termination or partial publication keeps its journal for recovery.
        if c.read_text(home / 'pending.json', 'recovery', missing=True) == launched:
            # No consumer effect happened in the launched phase; the task-private stage is discarded, script side effects stay unknown.
            (home / 'pending.json').unlink()
            discard_stage(home, pending)
        if isinstance(error, KeyboardInterrupt):
            for row in rows:
                row.update(state='failed', reason='interrupted', detail='the owned process tree was stopped; script side effects outside the stage are unknown')
        elif ran:
            # Any other failure after launch: the rows must not keep claiming the script never ran.
            for row in rows:
                if row['state'] in ('granted', 'proposed'):
                    row.update(state='failed', reason='post-run', detail=UNKNOWN_EFFECTS)
        raise


# --- journal seam (validated by mask_fs before any recovery effect) ---------

def validate_journal(pending):
    facts = pending['setup']
    if not isinstance(pending['transaction_id'], str) or not UUID_RE.fullmatch(pending['transaction_id']):
        c.fail('recovery.conflict', 'Unsafe pending setup transaction id.', 8)
    c.fields(facts, ('phase', 'root', 'scope', 'skill', 'coordinate', 'package_sha256', 'descriptor_sha256', 'role_inputs_sha256', 'interpreter', 'granted_by', 'actions'), ('lock',), family='recovery')
    c.skill_id(facts['skill'])
    if (facts['phase'] not in PHASES or pending['operation'] != 'ensure' or facts['root'] not in pending['selected'] or facts['scope'] not in ('project', 'user')
            or not isinstance(facts['coordinate'], str) or not consent.GRANT_RE.fullmatch(facts['coordinate'] + ':x') or not facts['coordinate'].endswith('/' + facts['skill'])
            or any(not isinstance(facts[key], str) for key in ('package_sha256', 'descriptor_sha256', 'role_inputs_sha256'))
            or not isinstance(facts['interpreter'], dict) or set(facts['interpreter']) != {'executable', 'version'} or any(not isinstance(item, str) for item in facts['interpreter'].values())
            or facts['granted_by'] not in ('prompt', 'allow-setup', 'repair')
            or not isinstance(facts['actions'], list) or not 1 <= len(facts['actions']) <= workflow.LIMITS['setup']):
        c.fail('recovery.conflict', 'Unsafe pending setup facts.', 8)
    for action in facts['actions']:
        c.fields(action, ('action', 'entrypoint', 'timeout_seconds', 'native_roles', 'inputs', 'parameters', 'fingerprint'), family='recovery')
        workflow.identifier(action['action'], 'setup')
        workflow.relative_path(action['entrypoint'], 'recovery')
        if (type(action['timeout_seconds']) is not int or not 1 <= action['timeout_seconds'] <= 120 or not isinstance(action['fingerprint'], str) or not isinstance(action['parameters'], dict)
                or not isinstance(action['native_roles'], list) or not action['native_roles'] or not isinstance(action['inputs'], list)):
            c.fail('recovery.conflict', 'Unsafe pending setup action.', 8)
        for role in action['native_roles']:
            c.fields(role, ('agent', 'name'), family='recovery')
            if role['agent'] not in adapters.BY_ID:
                c.fail('recovery.conflict', 'Unsafe pending setup role.', 8)
            workflow.identifier(role['name'], 'role')
        for row in action['inputs']:
            c.fields(row, ('id', 'path', 'sha256'), family='recovery')
            workflow.relative_path(row['path'], 'recovery')
            if row['sha256'] is not None and (not isinstance(row['sha256'], str) or not workflow.HEX_RE.fullmatch(row['sha256'])):
                c.fail('recovery.conflict', 'Unsafe pending setup input.', 8)
    if facts['phase'] == 'launched':
        if 'lock' in facts or 'native_roles' in pending or pending['before_state'] != pending['after_state']:
            c.fail('recovery.conflict', 'A launched setup journal cannot carry effects.', 8)
        return
    if 'lock' not in facts:
        c.fail('recovery.conflict', 'A staged setup journal needs its lock transition.', 8)
    lock = facts['lock']
    c.fields(lock, ('relative', 'before', 'after'), family='recovery')
    # A journal written before the lock moved out of .mask/skill-config still names the retired path.
    if lock['relative'] not in (workflow.lock_relative(facts['skill']), workflow.legacy_lock_relative(facts['skill'])) or not isinstance(lock['after'], str) or lock['before'] is not None and not isinstance(lock['before'], str):
        c.fail('recovery.conflict', 'Unsafe pending setup lock.', 8)
    try:
        workflow.parse_lock(c.parse_json(lock['after'], 'workflow'))
    except c.MaskError:
        c.fail('recovery.conflict', 'Pending setup lock bytes are not a portable role lock.', 8)


def lock_state(pending):
    facts = pending['setup']
    path = Path(facts['root']) / facts['lock']['relative']
    c.parents_safe(Path(facts['root']), path)
    if c.kind(path) not in ('missing', 'file'):
        c.fail('recovery.conflict', 'The pending native role lock path is not a regular file.', 8, path=str(path))
    actual = c.read_text(path, 'recovery', missing=True)
    if actual not in (facts['lock']['before'], facts['lock']['after']):
        c.fail('recovery.conflict', 'The pending native role lock was edited.', 8, path=str(path))
    return path, actual


def check_journal(pending):
    if pending['setup']['phase'] == 'staged':
        lock_state(pending)


def restore_journal(pending, side):
    facts = pending['setup']
    if facts['phase'] == 'launched':
        if side == 'after':
            c.fail('setup.unverified', 'Package setup was launched but never validated; MASK does not rerun package code from a journal.', 8)
        return
    path, actual = lock_state(pending)
    wanted = facts['lock'][side]
    if actual == wanted:
        return
    if wanted is None:
        path.unlink()
        return
    c.atomic_text(path, wanted, actual)


def discard_stage(home, pending):
    """Remove the task-private stage; consumer directories are never touched here."""
    staging = home / STAGING
    stage = staging / pending['transaction_id']
    if UUID_RE.fullmatch(pending['transaction_id']) and stage.resolve().parent == staging.resolve() and c.kind(stage) == 'directory':
        shutil.rmtree(stage, ignore_errors=True)
        try:
            stage.parent.rmdir()
        except OSError:
            pass  # Other stages are still in use.
