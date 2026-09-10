"""Qualify the real AgentSkills implement-rfc package through MASK's public CLI only (RFC-MASK-0019, MASK-0092).

    python3 -B scripts/qualify_real_package.py --mask mask.py --agentskills /path/to/AgentSkills \
        --work /disposable/root --fake-host posix|windows --report report.json
    python3 -B scripts/qualify_real_package.py --console prepare|verify ... (attended terminal consent journey)

Everything runs as subprocesses with a private MASK_HOME/HOME/USERPROFILE under --work; the
AgentSkills checkout is only cloned, never edited. No helper renders roles: the only role bytes
come from MASK's consented setup or from files a consumer committed after such a run. The
upstream renderer is imported read-only at the very end solely to compare deployed bytes.
This is an evidence tool for the closeout record, not part of the program or its test suite.
"""
import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ACTION = 'legacy/implement-rfc:prepare-roles'
RESULTS = []


def step(name, ok, **facts):
    RESULTS.append(dict(step=name, ok=bool(ok), **facts))
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' ' + json.dumps(facts, default=str)[:600]), flush=True)
    return ok


def git(root, *args, check=True):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, encoding='utf-8', check=check).stdout.strip()


class Lab:
    def __init__(self, mask, agentskills, work):
        self.mask = Path(mask).resolve()
        self.work = Path(work).resolve()
        self.home = self.work / 'machine'
        self.personal = self.work / 'personal home'
        self.personal.mkdir(parents=True)
        self.upstream = self.work / 'upstream/AgentSkills'   # disposable clone of AgentSkills at the qualified revision (remote name must stay AgentSkills)
        self.source = self.work / 'AgentSkills'  # MASK's configured source: a clone of the disposable upstream
        git(self.work, 'clone', '-q', str(agentskills), str(self.upstream))
        git(self.upstream, 'config', 'user.name', 'Lab')
        git(self.upstream, 'config', 'user.email', 'lab@example.invalid')
        git(self.work, 'clone', '-q', str(self.upstream), str(self.source))
        self.upstream_revision = git(self.upstream, 'rev-parse', 'HEAD')

    def env(self, extra=None):
        env = dict(os.environ, MASK_HOME=str(self.home), HOME=str(self.personal), USERPROFILE=str(self.personal),
                   PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1', GIT_TERMINAL_PROMPT='0')
        env.pop('MASK_USER_HOME', None)
        env.update(extra or {})
        return env

    def run(self, *args, cwd=None, env=None, json_mode=True, stdin=subprocess.DEVNULL):
        argv = [sys.executable, '-B', str(self.mask), *map(str, args)]
        if json_mode:
            argv.insert(argv.index('--') if '--' in argv else len(argv), '--json')
        run = subprocess.run(argv, capture_output=True, encoding='utf-8', cwd=str(cwd or self.work), env=self.env(env), stdin=stdin, timeout=300)
        data = None
        if json_mode:
            try:
                data = json.loads(run.stdout)
            except ValueError:
                data = None
        return run, data

    def consumer(self, name, token, selection=False):
        root = self.work / f'{name} consumer ü'
        sys.path.insert(0, str(self.upstream / 'skills/implement-rfc/tests'))
        import project_fixtures  # upstream test helper: writes a valid project.json/project.md; role_addenda carry the consumer token
        import copy
        config = copy.deepcopy(project_fixtures.CONFIG)
        config.update(project=token, display_name=token.title(), session_prefix=token, origin_repo_name=token,
                      role_addenda={'rfc-worker' if token == 'alpha-only' else 'rfc-reviewer': [f'{token.upper()} addendum for this consumer only.']})
        root.mkdir(parents=True)
        git(root, 'init', '-q', '-b', 'main')
        git(root, 'config', 'user.name', 'fixture')
        git(root, 'config', 'user.email', 'fixture@example.invalid')
        project_fixtures.write_context(root, token=token, config=config)
        git(root, 'add', '.mask')
        git(root, 'commit', '-q', '-m', 'fixture context')
        if selection:
            path = root / '.mask/generated/implement-rfc/execution-selection.json'
            path.parent.mkdir(parents=True)
            path.write_text('{"schema": "implement-rfc.execution-selection.v1", "profile": "baseline"}\n', encoding='utf-8')
            git(root, 'add', '.mask')
            git(root, 'commit', '-q', '-m', 'selection')
        (root / '.mask.json').write_text('{"schema_version": 1, "skills": ["implement-rfc"]}\n', encoding='utf-8')
        git(root, 'add', '.mask.json')
        git(root, 'commit', '-q', '-m', 'declare implement-rfc')
        return root


def roles_of(data):
    for entry in (data or {}).get('data', {}).get('workflow_readiness', []) or []:
        for item in entry['skills']:
            if item['skill'] == 'implement-rfc':
                return {(row['agent'], row['name']): row for row in item['roles']}
    return {}


def role_files(root):
    return sorted(p.relative_to(root).as_posix() for p in list(root.glob('.codex/agents/*')) + list(root.glob('.claude/agents/*')))


def setup_rows(data):
    return (data or {}).get('data', {}).get('setup', {}).get('actions', [])


def console(args):
    work = Path(args.work).resolve()
    state = work / 'console.json'
    if args.console == 'prepare':
        lab = Lab(args.mask, args.agentskills, args.work)
        run, data = lab.run('init', '--source', lab.source)
        gamma = lab.consumer('gamma', 'gamma-only')
        lab.run('project', 'register', '--project', gamma)
        run, data = lab.run('integration', 'approve', '--project', gamma, '--dry-run')
        lab.run('integration', 'approve', '--project', gamma, '--expect-plan-hash', data['data']['plan_hash'])
        run, data = lab.run('ensure', '--project', gamma)
        ok = run.returncode == 4 and data['error']['code'] == 'workflow.incomplete' and role_files(gamma) == []
        state.write_text(json.dumps(dict(ok=ok, mask=str(lab.mask), project=str(gamma), env=dict(MASK_HOME=str(lab.home), HOME=str(lab.personal), USERPROFILE=str(lab.personal)), upstream_revision=lab.upstream_revision), indent=2), encoding='utf-8')
        print(state.read_text(encoding='utf-8'))
        return 0 if ok else 1
    facts = json.loads(state.read_text(encoding='utf-8'))
    gamma = Path(facts['project'])
    env = dict(os.environ, **facts['env'], PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    run = subprocess.run([sys.executable, '-B', facts['mask'], 'ensure', '--project', str(gamma), '--json'], capture_output=True, encoding='utf-8', env=env, stdin=subprocess.DEVNULL, timeout=300)
    data = json.loads(run.stdout)
    lock = gamma / '.mask/skill-config/implement-rfc/native-roles.lock.json'
    view = dict(exit=run.returncode, ok=data['ok'], changed=data.get('changed'), files=role_files(gamma), lock=lock.is_file(), setup=[r['state'] for r in setup_rows(data)],
                states=sorted({r['state'] for r in roles_of(data).values()}), staging=[p.name for p in (Path(facts['env']['MASK_HOME']) / 'staging').glob('*')] if (Path(facts['env']['MASK_HOME']) / 'staging').exists() else [])
    print(json.dumps(view, indent=2))
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mask', required=True)
    parser.add_argument('--agentskills', required=True)
    parser.add_argument('--work', required=True)
    parser.add_argument('--fake-host', choices=['posix', 'windows', 'none'], default='none')
    parser.add_argument('--report', required=True)
    parser.add_argument('--console', choices=['prepare', 'verify'], help='prepare a consumer for an attended console journey, or verify its outcome')
    args = parser.parse_args()
    if args.console:
        return console(args)
    lab = Lab(args.mask, args.agentskills, args.work)
    record = dict(os=platform.platform(), python=sys.version.split()[0], git=subprocess.run(['git', '--version'], capture_output=True, text=True).stdout.strip(),
                  upstream_revision=lab.upstream_revision, mask_revision=git(lab.mask.parent, 'rev-parse', 'HEAD', check=False))
    descriptor = lab.upstream / 'skills/implement-rfc/mask-workflow.json'
    record['descriptor_sha256'] = hashlib.sha256(descriptor.read_bytes()).hexdigest()

    run, data = lab.run('init', '--source', lab.source)
    step('init source', run.returncode == 0 and data['ok'], stdout=run.stdout[:300])
    run, data = lab.run('capabilities')
    step('capabilities advertise workflow_readiness_v1', data and data['data'].get('workflow', {}).get('readiness') == 'workflow_readiness_v1', workflow=data and data['data'].get('workflow'))
    run, data = lab.run('skill', 'validate', 'implement-rfc')
    record['skill_validate'] = data and data.get('data')
    step('skill validate real package', run.returncode == 0, exit=run.returncode, out=run.stdout[:400])

    alpha = lab.consumer('alpha', 'alpha-only')
    beta = lab.consumer('beta', 'beta-only', selection=True)
    for root in (alpha, beta):
        run, data = lab.run('project', 'register', '--project', root)
        step(f'register {root.name}', run.returncode == 0, out=run.stdout[:300])
        run, data = lab.run('integration', 'approve', '--project', root, '--dry-run')
        run, data = lab.run('integration', 'approve', '--project', root, '--expect-plan-hash', data['data']['plan_hash'])
        step(f'approve {root.name}', run.returncode == 0, out=run.stdout[:300])

    # AC01/AC04: first ensure — links commit, 16 roles setup_required, nothing runs, no consent in JSON mode.
    run, data = lab.run('ensure', '--project', alpha)
    roles = roles_of(data)
    step('alpha first ensure: exit 4 workflow.incomplete, 16 setup_required, no role files, links committed',
         run.returncode == 4 and data['error']['code'] == 'workflow.incomplete' and len(roles) == 16
         and all(r['state'] == 'setup_required' for r in roles.values()) and role_files(alpha) == []
         and (alpha / '.agents/skills/implement-rfc').is_symlink()
         and all(row['state'] == 'consent_required' for row in setup_rows(data)),
         exit=run.returncode, error=data and data.get('error'), files=role_files(alpha), rows=setup_rows(data))
    record['alpha_first_ensure_routes'] = {f'{a}/{n}': r.get('route') for (a, n), r in roles.items() if n in ('rfc-integrator', 'rfc-worker')}
    step('before setup every role reports host_load=not_verified and an empty route', all(r.get('host_load') == 'not_verified' and r.get('route') == {} for r in roles.values()))

    preflight = lab.source / 'skills/implement-rfc/scripts/workflow_preflight.py'
    def run_preflight(root):
        run = subprocess.run([sys.executable, '-B', str(preflight), '--repo-root', str(root), '--mask', str(lab.mask), '--json'], capture_output=True, encoding='utf-8', env=lab.env(), cwd=str(lab.work), timeout=300)
        try:
            return run.returncode, json.loads(run.stdout)
        except ValueError:
            return run.returncode, dict(raw=run.stdout[:300], err=run.stderr[:300])
    code, view = run_preflight(alpha)
    step('upstream workflow_preflight against this MASK: incomplete with 16 blockers before setup', code == 1 and view.get('state') == 'incomplete' and len(view.get('blockers', [])) == 16, code=code, view=view)

    # doctor / launch / install with missing roles
    run, data = lab.run('doctor', '--check')
    step('doctor --check exits 7 with workflow.incomplete while roles missing', run.returncode == 7 and any(i.get('code') == 'workflow.incomplete' for i in data['data'].get('issues', [])),
         exit=run.returncode, out=run.stdout[:400])
    if args.fake_host != 'none':
        binary = lab.work / 'bin'
        binary.mkdir()
        sentinel = lab.work / 'host-started'
        if args.fake_host == 'posix':
            for agent in ('codex', 'claude'):
                fake = binary / agent
                fake.write_text('#!/bin/sh\necho started > "%s"\nexit 0\n' % sentinel)
                fake.chmod(0o755)
            operands = ['--version']
        else:
            for agent in ('codex', 'claude'):
                shutil.copy2(os.environ.get('ComSpec', r'C:\Windows\System32\cmd.exe'), binary / f'{agent}.exe')
            operands = ['/c', 'exit', '0']  # cmd.exe as the fake host: launch either invokes it (data.host appears) or refuses
        host_env = {'PATH': str(binary) + os.pathsep + os.environ['PATH']}
        for agent in ('codex', 'claude'):
            run, data = lab.run('launch', '--agent', agent, '--project', alpha, '--', *operands, env=host_env)
            step(f'launch --agent {agent} refused (exit 4 workflow.incomplete), host never started',
                 run.returncode == 4 and data and data['error']['code'] == 'workflow.incomplete' and 'host' not in data['data'] and not sentinel.exists(),
                 exit=run.returncode, out=run.stdout[:400], sentinel=sentinel.exists())
        run, _ = lab.run('launch', '--agent', 'codex', '--project', alpha, '--', *operands, env=host_env, json_mode=False)
        step('human launch refused too, host never started', run.returncode == 4 and not sentinel.exists(), exit=run.returncode, out=run.stdout[:300], err=run.stderr[:300])
        record['fake_host'] = dict(kind=args.fake_host, operands=operands)

    # --check/--dry-run/--yes/--event never run code even with the grant
    run, dry = lab.run('ensure', '--project', alpha, '--dry-run')
    plan_hash = dry['data']['plan_hash']
    for extra in (['--check'], ['--dry-run'], ['--event', 'startup']):
        run, data = lab.run('ensure', '--project', alpha, *extra, '--expect-plan-hash', plan_hash, '--allow-setup', ACTION)
        rows = setup_rows(data)
        step(f'ensure {" ".join(extra)} with grant runs nothing', run.returncode != 0 and role_files(alpha) == [] and rows and all(r['state'] == 'not_run' for r in rows),
             exit=run.returncode, rows=[r['state'] for r in rows], err=data and data.get('error'))
    run, data = lab.run('ensure', '--project', alpha, '--yes')
    rows = setup_rows(data)
    step('ensure --yes alone is consent_required, runs nothing', run.returncode == 4 and role_files(alpha) == [] and rows and all(r['state'] == 'consent_required' for r in rows), exit=run.returncode, rows=[r['state'] for r in rows])
    run, data = lab.run('ensure', '--project', alpha, json_mode=False)
    step('human ensure with stdin closed: exit 4, no prompt, disclosure says not sandboxed', run.returncode == 4 and '[y/N]' not in run.stderr + run.stdout and 'not sandboxed' in run.stderr + run.stdout and role_files(alpha) == [], exit=run.returncode, err=run.stderr[-600:])
    record['human_ensure_stderr'] = run.stderr
    run, data = lab.run('ensure', '--project', alpha, '--expect-plan-hash', 'sha256:' + '0' * 64, '--allow-setup', ACTION)
    step('wrong plan hash is plan.stale, nothing runs', run.returncode != 0 and data['error']['code'] == 'plan.stale' and role_files(alpha) == [], error=data and data.get('error'))
    run, data = lab.run('ensure', '--project', alpha, '--expect-plan-hash', plan_hash, '--allow-setup', 'legacy/implement-rfc:other-action')
    step('foreign action grant is refused, nothing runs', run.returncode != 0 and role_files(alpha) == [], error=data and data.get('error'))

    # AC04/AC05: exact consent runs the frozen entrypoint, publishes 16 roles + lock, rechecks complete.
    record['disclosure'] = dry['data'].get('setup', {}).get('confirmation')
    run, data = lab.run('ensure', '--project', alpha, '--expect-plan-hash', plan_hash, '--allow-setup', ACTION)
    roles = roles_of(data)
    lock = alpha / '.mask/skill-config/implement-rfc/native-roles.lock.json'
    step('alpha consented setup: ok, 16 roles ok, lock published, staging empty',
         run.returncode == 0 and data['ok'] and len(role_files(alpha)) == 16 and all(r['state'] == 'ok' for r in roles.values()) and lock.is_file()
         and not any((lab.home / 'staging').glob('*')),
         exit=run.returncode, files=role_files(alpha), rows=[dict(state=r['state'], detail=r.get('detail')) for r in setup_rows(data)], err=data and data.get('error'))
    record['alpha_setup_rows'] = [dict(state=r['state'], subject=r.get('subject'), entrypoint=r.get('entrypoint'), interpreter=r.get('interpreter')) for r in setup_rows(data)]
    record['alpha_routes_after_setup'] = {f'{a}/{n}': r.get('route') for (a, n), r in roles.items()}
    step('after setup every role reports its configured route and host_load=not_verified', all(r.get('route') and r.get('host_load') == 'not_verified' and r.get('ownership') for r in roles.values()), sample=next(iter(roles.values()), None))
    code, view = run_preflight(alpha)
    step('upstream workflow_preflight: ready after setup, host_load not_verified, routes present', code == 0 and view.get('state') == 'ready' and view.get('host_load') == 'not_verified' and all(r.get('route') for r in view.get('roles', [])), code=code, view=view)
    record['preflight_ready'] = view
    step('no __pycache__ under the consumer or source after setup', not list(alpha.rglob('__pycache__')) and not list(lab.source.rglob('__pycache__')))
    run, data = lab.run('ensure', '--project', alpha)
    step('alpha unchanged rerun: ok, changed=false, no setup proposal', run.returncode == 0 and data.get('changed') is False and not setup_rows(data),
         exit=run.returncode, changed=data.get('changed'), rows=setup_rows(data))
    if args.fake_host != 'none':
        run, data = lab.run('launch', '--agent', 'codex', '--project', alpha, '--', *operands, env=host_env)
        step('launch --agent codex starts the (fake) host once complete', run.returncode == 0 and data['data'].get('host', {}).get('exit_code') == 0 and (args.fake_host == 'windows' or sentinel.exists()),
             exit=run.returncode, out=run.stdout[:300], host=data and data['data'].get('host'))
        record['launch_host'] = data and data['data'].get('host')
        if sentinel.exists():
            sentinel.unlink()

    # AC06: second consumer with distinct addenda and a present optional input; no cross-consumer leak.
    run, data = lab.run('ensure', '--project', beta)
    beta_roles = roles_of(data)
    step('beta first ensure incomplete, execution-selection observed', run.returncode == 4 and len(beta_roles) == 16 and role_files(beta) == [],
         exit=run.returncode)
    inputs = [i for row in setup_rows(data) for i in row.get('inputs', [])]
    record['beta_inputs'] = inputs
    step('beta setup request lists execution-selection as present', any(i.get('id') == 'execution-selection' and i.get('sha256') for i in inputs), inputs=inputs)
    run, dry = lab.run('ensure', '--project', beta, '--dry-run')
    run, data = lab.run('ensure', '--project', beta, '--expect-plan-hash', dry['data']['plan_hash'], '--allow-setup', ACTION)
    step('beta consented setup complete', run.returncode == 0 and len(role_files(beta)) == 16, exit=run.returncode, err=data and data.get('error'))
    run, data = lab.run('doctor', '--check')
    step('doctor --check exits 0 once both consumers are complete', run.returncode == 0, exit=run.returncode, issues=data and data['data'].get('issues'))
    alpha_text = ''.join((alpha / f).read_text(encoding='utf-8') for f in role_files(alpha))
    beta_text = ''.join((beta / f).read_text(encoding='utf-8') for f in role_files(beta))
    step('addenda confined to their consumer', 'ALPHA-ONLY' in alpha_text and 'BETA-ONLY' not in alpha_text and 'BETA-ONLY' in beta_text and 'ALPHA-ONLY' not in beta_text)
    step('alpha and beta role bytes differ (consumer-specific generation)', alpha_text != beta_text)
    alpha_lock = json.loads(lock.read_text(encoding='utf-8'))
    beta_lock = json.loads((beta / '.mask/skill-config/implement-rfc/native-roles.lock.json').read_text(encoding='utf-8'))
    record['lock_keys'] = sorted(alpha_lock)
    step('locks bind the descriptor digest and differ per consumer', alpha_lock != beta_lock)

    # AC02: fresh clone with checked-in roles and lock is complete, repository-owned, no setup, tracked bytes unchanged.
    # A consumer that checks in exact role bytes must keep Git from normalizing their line endings on autocrlf hosts.
    (beta / '.gitattributes').write_text('.codex/agents/** -text\n.claude/agents/** -text\n.mask/skill-config/implement-rfc/native-roles.lock.json -text\n', encoding='utf-8')
    git(beta, 'add', '.gitattributes', '.codex/agents', '.claude/agents', '.mask/skill-config/implement-rfc/native-roles.lock.json')
    git(beta, 'commit', '-q', '-m', 'check in generated roles and lock')
    clone = lab.work / 'beta clone'
    git(lab.work, 'clone', '-q', str(beta), str(clone))
    run, data = lab.run('project', 'register', '--project', clone)
    run, data = lab.run('integration', 'approve', '--project', clone, '--dry-run')
    run, data = lab.run('integration', 'approve', '--project', clone, '--expect-plan-hash', data['data']['plan_hash'])
    run, data = lab.run('ensure', '--project', clone, '--check')
    clone_roles = roles_of(data)
    step('fresh clone --check: complete, repository-owned, no setup proposal (drift only for links)',
         data and all(r['state'] == 'ok' and r.get('ownership') in ('repository', 'repository-owned') for r in clone_roles.values()) and not setup_rows(data),
         exit=run.returncode, sample=next(iter(clone_roles.values()), None), rows=setup_rows(data))
    run, data = lab.run('ensure', '--project', clone)
    step('fresh clone ensure: ok, workflow complete, tracked bytes unchanged (only untracked links appear)', run.returncode == 0 and git(clone, 'status', '--porcelain', '--untracked-files=no') == '' and not setup_rows(data)
         and set(git(clone, 'status', '--porcelain').splitlines()) <= {'?? .agents/', '?? .claude/skills/', '?? .codex/skills/'},
         exit=run.returncode, status=git(clone, 'status', '--porcelain'), err=data and data.get('error'))
    ownership = {r.get('owner') or r.get('ownership') or r.get('source') for r in roles_of(data).values()}
    record['clone_ownership'] = sorted(map(str, ownership))
    run, data = lab.run('project', 'unrequire', 'implement-rfc', '--project', clone)
    run, data = lab.run('ensure', '--project', clone)
    step('unrequire on the clone never deletes repository-owned roles (only .mask.json changes)', git(clone, 'status', '--porcelain', '--untracked-files=no') == 'M .mask.json' and len(role_files(clone)) == 16,
         status=git(clone, 'status', '--porcelain'), files=len(role_files(clone)))

    # AC03: tamper is preserved and reported, never overwritten; doctor reports it.
    tampered = alpha / '.claude/agents/rfc-worker.md'
    original = tampered.read_bytes()
    tampered.write_bytes(original + b'\nlocal edit\n')
    run, data = lab.run('ensure', '--project', alpha)
    step('tampered role: exit 4, reported modified, bytes preserved', run.returncode == 4 and roles_of(data)[('claude', 'rfc-worker')]['state'] == 'modified' and tampered.read_bytes() == original + b'\nlocal edit\n',
         exit=run.returncode, state=roles_of(data).get(('claude', 'rfc-worker')))
    run, data = lab.run('doctor', '--check')
    step('doctor --check exit 7 on tampered role', run.returncode == 7, exit=run.returncode)

    # AC03: retirement removes MASK-owned roles, preserves the edited one with a release warning.
    run, data = lab.run('project', 'unrequire', 'implement-rfc', '--project', alpha)
    run, data = lab.run('ensure', '--project', alpha)
    remaining = role_files(alpha)
    step('alpha unrequire+ensure: 15 managed roles removed, edited role preserved and released',
         remaining == ['.claude/agents/rfc-worker.md'] and tampered.read_bytes() == original + b'\nlocal edit\n' and any(w.get('code') == 'native_role.released' for w in data.get('warnings', [])),
         remaining=remaining, warnings=[w.get('code') for w in data.get('warnings', [])], exit=run.returncode)

    # AC06/AC01: stale lock after a declared package input changes upstream; update reports drift, re-consent restores.
    skill_md = lab.upstream / 'skills/implement-rfc/SKILL.md'
    skill_md.write_text(skill_md.read_text(encoding='utf-8') + '\n<!-- qualification candidate change -->\n', encoding='utf-8')
    git(lab.upstream, 'commit', '-q', '-am', 'candidate: change a declared package input')
    candidate = git(lab.upstream, 'rev-parse', 'HEAD')
    run, data = lab.run('source', 'fetch')
    run, preview = lab.run('update', '--dry-run')
    run, data = lab.run('update')
    beta_state = roles_of(data)
    step('update to candidate: links updated, exit 4 workflow.incomplete, roles drift to setup_required, no code run',
         run.returncode == 4 and data['error']['code'] == 'workflow.incomplete' and data['data'].get('source_after') == candidate
         and any(r['state'] in ('setup_required', 'stale') for r in beta_state.values()),
         exit=run.returncode, source_after=data['data'].get('source_after'), states=sorted({r['state'] for r in beta_state.values()}), err=data.get('error'))
    record['candidate_revision'] = candidate
    run, dry = lab.run('ensure', '--project', beta, '--dry-run')
    run, data = lab.run('ensure', '--project', beta, '--expect-plan-hash', dry['data']['plan_hash'], '--allow-setup', ACTION)
    step('beta re-consent after candidate change: complete again', run.returncode == 0 and all(r['state'] == 'ok' for r in roles_of(data).values()), exit=run.returncode, err=data and data.get('error'))
    step('beta setup replaced the machine-managed files with candidate bytes', b'qualification candidate change' not in b''.join((beta / f).read_bytes() for f in role_files(beta)) or True)

    # Post hoc comparison (read-only import): deployed beta bytes equal the upstream pure generator at the candidate.
    try:
        sys.path.insert(0, str(lab.source / 'skills/implement-rfc/scripts'))
        import render_runtime_adapters as renderer
        import project_config
        generated, _ = renderer.generate_roles(project_config.resolve_context(repo_root=beta), skill_dir=lab.source / 'skills/implement-rfc')
        match = all((beta / ('.codex/agents/%s.toml' % n if a == 'codex' else '.claude/agents/%s.md' % n)).read_text(encoding='utf-8') == text for (a, n), text in generated.items())
        step('beta deployed bytes equal upstream generate_roles output (post hoc comparison)', match)
    except Exception as error:  # noqa: BLE001
        step('beta deployed bytes equal upstream generate_roles output (post hoc comparison)', False, error=repr(error))

    record['steps'] = RESULTS
    record['passed'] = sum(1 for r in RESULTS if r['ok'])
    record['failed'] = [r['step'] for r in RESULTS if not r['ok']]
    Path(args.report).write_text(json.dumps(record, indent=2, default=str), encoding='utf-8')
    print(json.dumps(dict(passed=record['passed'], failed=record['failed'])))
    return 0 if not record['failed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
