"""Qualify the real AgentSkills implement-rfc package through MASK's public CLI only, on taps (RFC-MASK-0019 MASK-0092; RFC-MASK-0020 MASK-0104).

    python3 -B scripts/qualify_real_package.py --mask /disposable/ManageAgentSkills/mask.py --agentskills /path/to/AgentSkills \
        --work /short/disposable/root --fake-host posix|windows|none --report report.json
    python3 -B scripts/qualify_real_package.py --console prepare|verify ... (attended terminal consent journey)

Every MASK call is a subprocess with its own private MASK_HOME, HOME and USERPROFILE under --work. The
AgentSkills checkout is only cloned, never edited: a disposable bare clone is the tap, and a disposable
authoring clone commits and pushes candidates to it. No helper renders roles: role bytes come only from
MASK's consented setup or from files a consumer committed after such a run; the upstream renderer is
imported read-only at the end to compare deployed bytes. Three independent machines run in order: the
tap lab (bootstrap, consent, roles, fresh clone, removal, push-then-update), a v1 legacy lab built by the
MASK under test's tests/legacy_support.py, and a small owner-shape rehearsal of MASK-0105 (a v1
configuration over a checked-out AgentSkills clone whose origin is a local bare repository, with an empty
registry). Keep --work short on Windows: a tap cache ref path beyond MAX_PATH fails as an untyped git.failed.
This is an evidence tool for the closeout record, not part of the program or its test suite.
"""
import argparse
import copy
import functools
import hashlib
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import traceback
from pathlib import Path

TAP = 'agentskills'
SKILL = 'implement-rfc'
COORDINATE = f'{TAP}/{SKILL}'
ACTION = f'{COORDINATE}:prepare-roles'
LINKS = (f'.agents/skills/{SKILL}', f'.claude/skills/{SKILL}')
RESULTS = []


def step(name, ok, **facts):
    RESULTS.append(dict(step=name, ok=bool(ok), **facts))
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else ' ' + json.dumps(facts, default=str)[:600]), flush=True)
    return ok


def git(root, *args, check=True):
    """Git without optional locks, so observing a checkout never refreshes its index."""
    return subprocess.run(['git', '--no-optional-locks', '-C', str(root), *map(str, args)], capture_output=True, encoding='utf-8', check=check).stdout.strip()


def bare_clone(source, target):
    """A disposable bare copy of ``source`` that shares no object files with it."""
    target.parent.mkdir(parents=True, exist_ok=True)
    git(target.parent, 'clone', '-q', '--bare', '--no-hardlinks', source, target)


def checkout_facts(clone):
    """HEAD, staged entries, raw index bytes and porcelain status of a checkout."""
    def raw(*args):
        return subprocess.run(['git', '--no-optional-locks', '-C', str(clone), *args], capture_output=True, check=True).stdout
    return dict(head=raw('rev-parse', 'HEAD').decode().strip(), staged=hashlib.sha256(raw('ls-files', '--stage', '-z')).hexdigest(),
                index=hashlib.sha256((clone / '.git/index').read_bytes()).hexdigest(), status=raw('status', '--porcelain').decode())


def load(path):
    path = Path(path)
    return json.loads(path.read_text(encoding='utf-8')) if path.is_file() else {}


def body(data):
    return (data or {}).get('data') or {}


def code_of(data):
    return ((data or {}).get('error') or {}).get('code')


def codes(rows):
    return sorted({row.get('code') for row in rows or []})


class Machine:
    """One private MASK_HOME and personal home; every call runs the MASK under test as a subprocess and is logged."""

    def __init__(self, mask, home, personal, cwd):
        self.mask, self.home, self.personal, self.cwd = Path(mask).resolve(), Path(home), Path(personal), Path(cwd)
        self.calls = []

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
        run = subprocess.run(argv, capture_output=True, encoding='utf-8', cwd=str(cwd or self.cwd), env=self.env(env), stdin=stdin, timeout=600)
        data = None
        if json_mode:
            try:
                data = json.loads(run.stdout)
            except ValueError:
                pass
        self.calls.append(dict(argv=argv[3:], exit=run.returncode, error=code_of(data), transaction=(data or {}).get('transaction'), changed=(data or {}).get('changed')))
        return run, data

    def store_links(self, root, relatives=LINKS):
        """Each link leaf and whether it is a link resolving under MASK_HOME/store/v1/."""
        store = (self.home / 'store/v1').resolve()
        return {str(root / relative): (root / relative).is_symlink() and (root / relative).resolve().is_relative_to(store) for relative in relatives}


class Lab(Machine):
    def __init__(self, mask, agentskills, work):
        work = Path(work).resolve()
        super().__init__(mask, work / 'machine', work / 'personal home', work)
        self.work = work
        self.personal.mkdir(parents=True)
        self.upstream = work / 'upstream/AgentSkills.git'  # the tap: a bare disposable clone of AgentSkills at the qualified revision
        self.author = work / 'AgentSkills'  # a disposable authoring clone that commits and pushes candidates to the upstream
        bare_clone(agentskills, self.upstream)
        git(work, 'clone', '-q', self.upstream, self.author)
        git(self.author, 'config', 'user.name', 'Lab')
        git(self.author, 'config', 'user.email', 'lab@example.invalid')
        self.upstream_revision = git(self.upstream, 'rev-parse', 'HEAD')
        sys.path.insert(0, str(self.author / 'skills/implement-rfc/tests'))

    def consumer(self, name, token, selection=False):
        """A Git consumer with committed implement-rfc context; only ``install`` declares the skill."""
        import project_fixtures  # upstream test helper: writes a valid project.json/project.md; role_addenda carry the consumer token
        root = self.work / f'{name} consumer ü'
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
        return root


def roles_of(data):
    for entry in body(data).get('workflow_readiness', []) or []:
        for item in entry['skills']:
            if item['skill'] == SKILL:
                return {(row['agent'], row['name']): row for row in item['roles']}
    return {}


def role_files(root):
    return sorted(p.relative_to(root).as_posix() for p in list(root.glob('.codex/agents/*')) + list(root.glob('.claude/agents/*')))


def setup_rows(data):
    return body(data).get('setup', {}).get('actions', [])


def console(args):
    work = Path(args.work).resolve()
    state = work / 'console.json'
    if args.console == 'prepare':
        lab = Lab(args.mask, args.agentskills, args.work)
        lab.run('tap', 'add', TAP, lab.upstream)
        gamma = lab.consumer('gamma', 'gamma-only')
        lab.run('install', SKILL, '--project', gamma)
        run, data = lab.run('integration', 'approve', '--project', gamma, '--dry-run')
        lab.run('integration', 'approve', '--project', gamma, '--expect-plan-hash', data['data']['plan_hash'])
        run, data = lab.run('ensure', '--project', gamma)
        ok = run.returncode == 4 and code_of(data) == 'workflow.incomplete' and role_files(gamma) == []
        state.write_text(json.dumps(dict(ok=ok, mask=str(lab.mask), project=str(gamma), env=dict(MASK_HOME=str(lab.home), HOME=str(lab.personal), USERPROFILE=str(lab.personal)),
                                         upstream_revision=lab.upstream_revision, calls=lab.calls), indent=2), encoding='utf-8')
        print(state.read_text(encoding='utf-8'))
        return 0 if ok else 1
    facts = json.loads(state.read_text(encoding='utf-8'))
    gamma = Path(facts['project'])
    env = dict(os.environ, **facts['env'], PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1')
    run = subprocess.run([sys.executable, '-B', facts['mask'], 'ensure', '--project', str(gamma), '--json'], capture_output=True, encoding='utf-8', env=env, stdin=subprocess.DEVNULL, timeout=300)
    data = json.loads(run.stdout)
    lock = gamma / '.mask/generated/implement-rfc/native-roles.lock.json'
    view = dict(exit=run.returncode, ok=data['ok'], changed=data.get('changed'), files=role_files(gamma), lock=lock.is_file(), setup=[r['state'] for r in setup_rows(data)],
                states=sorted({r['state'] for r in roles_of(data).values()}), staging=[p.name for p in (Path(facts['env']['MASK_HOME']) / 'staging').glob('*')] if (Path(facts['env']['MASK_HOME']) / 'staging').exists() else [])
    print(json.dumps(view, indent=2))
    return 0


def tap_lab(args, facts):
    """AC01/AC03 and the consent, roles, fresh-clone and removal journey with the real package as a tap."""
    lab = Lab(args.mask, args.agentskills, args.work)
    facts.update(calls=lab.calls, upstream_revision=lab.upstream_revision)
    descriptor = subprocess.run(['git', '-C', str(lab.upstream), 'cat-file', 'blob', 'HEAD:skills/implement-rfc/mask-workflow.json'], capture_output=True, check=True).stdout
    facts['descriptor_sha256'] = hashlib.sha256(descriptor).hexdigest()

    run, data = lab.run('tap', 'add', TAP, lab.upstream)
    config = load(lab.home / 'config.json')
    entry = config.get('sources', {}).get(TAP, {})
    step('tap add agentskills <bare upstream> on an empty MASK_HOME: config v3 with one exact-bytes tap, nothing fetched',
         run.returncode == 0 and config.get('schema_version') == 3 and list(config.get('sources', {})) == [TAP] and entry.get('line_endings', 'exact') == 'exact'
         and entry.get('authoring') is None and not (lab.home / 'sources').exists(), exit=run.returncode, entry=entry, out=run.stdout[:400])
    facts['tap_entry'] = entry
    run, data = lab.run('capabilities')
    step('capabilities: deployment_model taps and workflow_readiness_v1', body(data).get('deployment_model') == 'taps' and body(data).get('workflow', {}).get('readiness') == 'workflow_readiness_v1',
         deployment_model=body(data).get('deployment_model'), workflow=body(data).get('workflow'))

    alpha = lab.consumer('alpha', 'alpha-only')
    beta = lab.consumer('beta', 'beta-only', selection=True)
    facts['install'] = {}
    for root in (alpha, beta):
        run, data = lab.run('install', SKILL, '--project', root)
        lock = [(row['source'], row['id'], row['commit']) for row in load(root / '.mask.lock.json').get('packages', [])]
        links = lab.store_links(root)
        facts['install'][root.name] = dict(exit=run.returncode, error=code_of(data), transaction=(data or {}).get('transaction'), network=body(data).get('network'))
        step(f'install implement-rfc --project {root.name}: v2 declaration, lock at the upstream revision, store links, roles still missing (exit 4 workflow.incomplete)',
             run.returncode == 4 and code_of(data) == 'workflow.incomplete' and data['transaction'] == 'committed' and load(root / '.mask.json').get('schema_version') == 2
             and lock == [(TAP, SKILL, lab.upstream_revision)] and all(links.values()) and role_files(root) == [],
             exit=run.returncode, error=data and data.get('error'), lock=lock, links=links)
    caches = sorted((lab.home / 'sources').iterdir()) if (lab.home / 'sources').is_dir() else []
    modes = {str(root): load(lab.home / 'state.json').get('projects', {}).get(str(root), {}).get('mode') for root in (alpha, beta)}
    step('AC01: the first install fetched on demand into one bare cache under MASK_HOME/sources; no work tree under MASK_HOME; consumers pinned',
         facts['install'][alpha.name]['network'] == 'fetch' and len(caches) == 1 and git(caches[0], 'rev-parse', '--is-bare-repository') == 'true'
         and not list(lab.home.rglob('.git')) and set(modes.values()) == {'pinned'}, install=facts['install'], caches=[str(c) for c in caches], modes=modes)
    for root in (alpha, beta):
        run, data = lab.run('integration', 'approve', '--project', root, '--dry-run')
        run, data = lab.run('integration', 'approve', '--project', root, '--expect-plan-hash', data['data']['plan_hash'])
        step(f'approve {root.name}', run.returncode == 0, out=run.stdout[:300])
    run, data = lab.run('skill', 'validate', COORDINATE)
    facts['skill_validate'] = body(data)
    step('skill validate agentskills/implement-rfc from the tap cache', run.returncode == 0, exit=run.returncode, out=run.stdout[:400])

    # First ensure: links already committed by install, 16 roles setup_required, nothing runs, no consent in JSON mode.
    run, data = lab.run('ensure', '--project', alpha)
    roles = roles_of(data)
    step('alpha first ensure: exit 4 workflow.incomplete, 16 setup_required, no role files, store links in place',
         run.returncode == 4 and code_of(data) == 'workflow.incomplete' and len(roles) == 16
         and all(r['state'] == 'setup_required' for r in roles.values()) and role_files(alpha) == [] and all(lab.store_links(alpha).values())
         and all(row['state'] == 'consent_required' for row in setup_rows(data)),
         exit=run.returncode, error=data and data.get('error'), files=role_files(alpha), rows=setup_rows(data))
    facts['alpha_first_ensure_routes'] = {f'{a}/{n}': r.get('route') for (a, n), r in roles.items() if n in ('rfc-integrator', 'rfc-worker')}
    step('before setup every role reports host_load=not_verified and an empty route', roles and all(r.get('host_load') == 'not_verified' and r.get('route') == {} for r in roles.values()))

    def run_preflight(root):
        preflight = root / LINKS[0] / 'scripts/workflow_preflight.py'  # the deployed store copy, reached through the consumer's link
        run = subprocess.run([sys.executable, '-B', str(preflight), '--repo-root', str(root), '--mask', str(lab.mask), '--json'], capture_output=True, encoding='utf-8', env=lab.env(), cwd=str(lab.work), timeout=300)
        try:
            return run.returncode, json.loads(run.stdout)
        except ValueError:
            return run.returncode, dict(raw=run.stdout[:300], err=run.stderr[:300])
    code, view = run_preflight(alpha)
    step('upstream workflow_preflight against this MASK: incomplete with 16 blockers before setup', code == 1 and view.get('state') == 'incomplete' and len(view.get('blockers', [])) == 16, code=code, view=view)

    run, data = lab.run('doctor', '--check')
    step('doctor --check exits 7 with workflow.incomplete while roles missing', run.returncode == 7 and 'workflow.incomplete' in codes(body(data).get('issues')),
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
                 run.returncode == 4 and code_of(data) == 'workflow.incomplete' and 'host' not in body(data) and not sentinel.exists(),
                 exit=run.returncode, out=run.stdout[:400], sentinel=sentinel.exists())
        run, _ = lab.run('launch', '--agent', 'codex', '--project', alpha, '--', *operands, env=host_env, json_mode=False)
        step('human launch refused too, host never started', run.returncode == 4 and not sentinel.exists(), exit=run.returncode, out=run.stdout[:300], err=run.stderr[:300])
        facts['fake_host'] = dict(kind=args.fake_host, operands=operands)

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
    facts['human_ensure_stderr'] = run.stderr
    run, data = lab.run('ensure', '--project', alpha, '--expect-plan-hash', 'sha256:' + '0' * 64, '--allow-setup', ACTION)
    step('wrong plan hash is plan.stale, nothing runs', run.returncode != 0 and code_of(data) == 'plan.stale' and role_files(alpha) == [], error=data and data.get('error'))
    run, data = lab.run('ensure', '--project', alpha, '--expect-plan-hash', plan_hash, '--allow-setup', f'{COORDINATE}:other-action')
    step('foreign action grant is refused, nothing runs', run.returncode != 0 and role_files(alpha) == [], error=data and data.get('error'))

    # Exact consent runs the frozen entrypoint, publishes 16 roles + lock, rechecks complete.
    facts['disclosure'] = dry['data'].get('setup', {}).get('confirmation')
    run, data = lab.run('ensure', '--project', alpha, '--expect-plan-hash', plan_hash, '--allow-setup', ACTION)
    roles = roles_of(data)
    lock = alpha / '.mask/generated/implement-rfc/native-roles.lock.json'
    step('alpha consented setup: ok, 16 roles ok, lock published, staging empty',
         run.returncode == 0 and data['ok'] and len(role_files(alpha)) == 16 and len(roles) == 16 and all(r['state'] == 'ok' for r in roles.values()) and lock.is_file()
         and not any((lab.home / 'staging').glob('*')),
         exit=run.returncode, files=role_files(alpha), rows=[dict(state=r['state'], detail=r.get('detail')) for r in setup_rows(data)], err=data and data.get('error'))
    facts['alpha_setup_rows'] = [dict(state=r['state'], subject=r.get('subject'), entrypoint=r.get('entrypoint'), interpreter=r.get('interpreter')) for r in setup_rows(data)]
    facts['alpha_routes_after_setup'] = {f'{a}/{n}': r.get('route') for (a, n), r in roles.items()}
    step('after setup every role reports its configured route and host_load=not_verified', roles and all(r.get('route') and r.get('host_load') == 'not_verified' and r.get('ownership') for r in roles.values()), sample=next(iter(roles.values()), None))
    code, view = run_preflight(alpha)
    step('upstream workflow_preflight: ready after setup, host_load not_verified, routes present', code == 0 and view.get('state') == 'ready' and view.get('host_load') == 'not_verified' and all(r.get('route') for r in view.get('roles', [])), code=code, view=view)
    facts['preflight_ready'] = view
    step('no __pycache__ under the consumer, the store or the authoring clone after setup',
         not list(alpha.rglob('__pycache__')) and not list((lab.home / 'store').rglob('__pycache__')) and not list(lab.author.rglob('__pycache__')))
    run, data = lab.run('ensure', '--project', alpha)
    step('alpha unchanged rerun: ok, changed=false, no setup proposal', run.returncode == 0 and data.get('changed') is False and not setup_rows(data),
         exit=run.returncode, changed=data.get('changed'), rows=setup_rows(data))
    if args.fake_host != 'none':
        run, data = lab.run('launch', '--agent', 'codex', '--project', alpha, '--', *operands, env=host_env)
        step('launch --agent codex starts the (fake) host once complete', run.returncode == 0 and body(data).get('host', {}).get('exit_code') == 0 and (args.fake_host == 'windows' or sentinel.exists()),
             exit=run.returncode, out=run.stdout[:300], host=body(data).get('host'))
        facts['launch_host'] = body(data).get('host')
        if sentinel.exists():
            sentinel.unlink()

    # Second consumer with distinct addenda and a present optional input; no cross-consumer leak.
    run, data = lab.run('ensure', '--project', beta)
    step('beta first ensure incomplete, execution-selection observed', run.returncode == 4 and len(roles_of(data)) == 16 and role_files(beta) == [], exit=run.returncode)
    inputs = [i for row in setup_rows(data) for i in row.get('inputs', [])]
    facts['beta_inputs'] = inputs
    step('beta setup request lists execution-selection as present', any(i.get('id') == 'execution-selection' and i.get('sha256') for i in inputs), inputs=inputs)
    run, dry = lab.run('ensure', '--project', beta, '--dry-run')
    run, data = lab.run('ensure', '--project', beta, '--expect-plan-hash', dry['data']['plan_hash'], '--allow-setup', ACTION)
    step('beta consented setup complete', run.returncode == 0 and len(role_files(beta)) == 16, exit=run.returncode, err=data and data.get('error'))
    run, data = lab.run('doctor', '--check')
    step('doctor --check exits 0 once both consumers are complete', run.returncode == 0, exit=run.returncode, issues=body(data).get('issues'))
    alpha_text = ''.join((alpha / f).read_text(encoding='utf-8') for f in role_files(alpha))
    beta_text = ''.join((beta / f).read_text(encoding='utf-8') for f in role_files(beta))
    step('addenda confined to their consumer', 'ALPHA-ONLY' in alpha_text and 'BETA-ONLY' not in alpha_text and 'BETA-ONLY' in beta_text and 'ALPHA-ONLY' not in beta_text)
    step('alpha and beta role bytes differ (consumer-specific generation)', alpha_text != beta_text)
    beta_roles_lock = beta / '.mask/generated/implement-rfc/native-roles.lock.json'
    alpha_lock, beta_lock = load(lock), load(beta_roles_lock)
    facts['lock_keys'] = sorted(alpha_lock)
    step('role locks bind the descriptor digest and differ per consumer', alpha_lock and beta_lock and alpha_lock != beta_lock)

    # Fresh clone with the committed declaration, lock, roles and role lock: complete, repository-owned, no setup, tracked bytes unchanged.
    # A consumer that checks in exact role bytes must keep Git from normalizing their line endings on autocrlf hosts.
    (beta / '.gitattributes').write_text('.codex/agents/** -text\n.claude/agents/** -text\n.mask/generated/implement-rfc/native-roles.lock.json -text\n', encoding='utf-8')
    git(beta, 'add', '.gitattributes', '.mask.json', '.mask.lock.json', '.codex/agents', '.claude/agents', '.mask/generated/implement-rfc/native-roles.lock.json')
    git(beta, 'commit', '-q', '-m', 'check in the declaration, lock, generated roles and role lock')
    clone = lab.work / 'beta clone'
    git(lab.work, 'clone', '-q', beta, clone)
    run, data = lab.run('project', 'register', '--project', clone)
    run, data = lab.run('integration', 'approve', '--project', clone, '--dry-run')
    run, data = lab.run('integration', 'approve', '--project', clone, '--expect-plan-hash', data['data']['plan_hash'])
    run, data = lab.run('ensure', '--project', clone, '--check')
    clone_roles = roles_of(data)
    step('fresh clone --check: complete, repository-owned, no setup proposal (drift only for links)',
         len(clone_roles) == 16 and all(r['state'] == 'ok' and r.get('ownership') in ('repository', 'repository-owned') for r in clone_roles.values()) and not setup_rows(data),
         exit=run.returncode, sample=next(iter(clone_roles.values()), None), rows=setup_rows(data))
    run, data = lab.run('ensure', '--project', clone)
    step('fresh clone ensure: ok, workflow complete, store links, tracked bytes unchanged (only untracked links appear)',
         run.returncode == 0 and git(clone, 'status', '--porcelain', '--untracked-files=no') == '' and not setup_rows(data) and all(lab.store_links(clone).values())
         and set(git(clone, 'status', '--porcelain').splitlines()) <= {'?? .agents/', '?? .claude/skills/', '?? .codex/skills/'},
         exit=run.returncode, status=git(clone, 'status', '--porcelain'), err=data and data.get('error'))
    facts['clone_ownership'] = sorted({str(r.get('ownership')) for r in roles_of(data).values()})
    run, data = lab.run('remove', SKILL, '--project', clone)
    tracked = sorted(line.split()[-1] for line in git(clone, 'status', '--porcelain', '--untracked-files=no').splitlines())
    step('remove implement-rfc on the clone: repository-owned roles kept, only .mask.json and .mask.lock.json change, links removed',
         run.returncode == 0 and tracked == ['.mask.json', '.mask.lock.json'] and len(role_files(clone)) == 16 and not any(os.path.lexists(clone / r) for r in LINKS),
         exit=run.returncode, error=data and data.get('error'), tracked=tracked, files=len(role_files(clone)))

    # Tamper is preserved and reported, never overwritten; doctor reports it.
    tampered = alpha / '.claude/agents/rfc-worker.md'
    original = tampered.read_bytes()
    tampered.write_bytes(original + b'\nlocal edit\n')
    run, data = lab.run('ensure', '--project', alpha)
    step('tampered role: exit 4, reported modified, bytes preserved', run.returncode == 4 and roles_of(data).get(('claude', 'rfc-worker'), {}).get('state') == 'modified' and tampered.read_bytes() == original + b'\nlocal edit\n',
         exit=run.returncode, state=roles_of(data).get(('claude', 'rfc-worker')))
    run, data = lab.run('doctor', '--check')
    step('doctor --check exit 7 on tampered role', run.returncode == 7, exit=run.returncode)

    # Removal retires MASK-owned roles and preserves the edited one with a release warning.
    run, data = lab.run('remove', SKILL, '--project', alpha)
    remaining = role_files(alpha)
    removed = [a for a in (data or {}).get('actions', []) if a.get('kind') == 'native_role.remove']
    step('remove implement-rfc on alpha: 15 unchanged managed roles removed, edited role preserved and released, links removed',
         run.returncode == 0 and len(removed) == 15 and remaining == ['.claude/agents/rfc-worker.md'] and tampered.read_bytes() == original + b'\nlocal edit\n'
         and 'native_role.released' in codes((data or {}).get('warnings')) and not any(os.path.lexists(alpha / r) for r in LINKS),
         exit=run.returncode, error=data and data.get('error'), removed=len(removed), remaining=remaining, warnings=codes((data or {}).get('warnings')))

    # Push-then-update: a committed change to a declared package input reaches MASK only through update's own fetch.
    skill_md = lab.author / 'skills/implement-rfc/SKILL.md'
    skill_md.write_text(skill_md.read_text(encoding='utf-8') + '\n<!-- qualification candidate change -->\n', encoding='utf-8')
    git(lab.author, 'commit', '-q', '-am', 'candidate: change a declared package input')
    candidate = git(lab.author, 'rev-parse', 'HEAD')
    git(lab.author, 'push', '-q', 'origin', 'HEAD:main')
    facts['candidate_revision'] = candidate
    step('candidate committed in the authoring clone and pushed to the disposable bare upstream', candidate != lab.upstream_revision and git(lab.upstream, 'rev-parse', 'refs/heads/main') == candidate)
    cache = Path(load(lab.home / 'config.json')['sources'][TAP]['cache'])
    cached = git(cache, 'for-each-ref', '--format=%(refname) %(objectname)')
    beta_lock_bytes, beta_roles_lock_bytes = (beta / '.mask.lock.json').read_bytes(), beta_roles_lock.read_bytes()
    beta_role_bytes = {f: (beta / f).read_bytes() for f in role_files(beta)}
    run, preview = lab.run('update', '--dry-run')
    fetch = body(preview).get('fetches', {}).get(TAP, {})
    step('update --dry-run after the push: no fetch; cache refs and beta lock unchanged',
         fetch.get('attempted') is False and (preview or {}).get('changed') is False and git(cache, 'for-each-ref', '--format=%(refname) %(objectname)') == cached
         and (beta / '.mask.lock.json').read_bytes() == beta_lock_bytes, exit=run.returncode, fetch=fetch, network=body(preview).get('network'), error=code_of(preview))
    run, data = lab.run('update')
    fetches = body(data).get('fetches', {})
    rows = {row['root']: row for row in body(data).get('consumers', [])}
    changes = [(c['coordinate'], c['before_commit'], c['after_commit']) for c in rows.get(str(beta), {}).get('changes', [])]
    locked = [row['commit'] for row in load(beta / '.mask.lock.json').get('packages', [])]
    facts['update'] = dict(exit=run.returncode, error=(data or {}).get('error'), network=body(data).get('network'), fetches=fetches, transaction=(data or {}).get('transaction'),
                           consumers=[dict(root=r['root'], status=r['status'], changes=r.get('changes')) for r in rows.values()])
    step('plain update (no source fetch): fetches the one tap, beta lock and store links move to the pushed candidate',
         list(fetches) == [TAP] and fetches[TAP].get('attempted') is True and fetches[TAP].get('ok') is True and fetches[TAP].get('after') == candidate and body(data).get('network') == 'fetch'
         and rows.get(str(beta), {}).get('status') == 'updated' and changes == [(COORDINATE, lab.upstream_revision, candidate)] and locked == [candidate]
         and all(lab.store_links(beta).values()) and 'qualification candidate change' in (beta / LINKS[1] / 'SKILL.md').read_text(encoding='utf-8'),
         **facts['update'])
    beta_state = roles_of(data)
    step('update result: exit 4 workflow.incomplete, beta roles drift to setup_required, role files and role lock untouched (no package code ran)',
         run.returncode == 4 and code_of(data) == 'workflow.incomplete' and any(r['state'] in ('setup_required', 'stale') for r in beta_state.values())
         and {f: (beta / f).read_bytes() for f in role_files(beta)} == beta_role_bytes and beta_roles_lock.read_bytes() == beta_roles_lock_bytes,
         exit=run.returncode, states=sorted({r['state'] for r in beta_state.values()}), err=(data or {}).get('error'))
    run, dry = lab.run('ensure', '--project', beta, '--dry-run')
    run, data = lab.run('ensure', '--project', beta, '--expect-plan-hash', dry['data']['plan_hash'], '--allow-setup', ACTION)
    roles = roles_of(data)
    step('beta re-consent after the candidate: complete again, role lock republished for the candidate inputs',
         run.returncode == 0 and len(roles) == 16 and all(r['state'] == 'ok' for r in roles.values()) and beta_roles_lock.read_bytes() != beta_roles_lock_bytes,
         exit=run.returncode, err=data and data.get('error'))

    # Post hoc comparison (read-only import of the deployed candidate package): deployed beta bytes equal the upstream pure generator.
    try:
        package = beta / LINKS[0]
        sys.path.insert(0, str(package / 'scripts'))
        import render_runtime_adapters as renderer
        import project_config
        generated, _ = renderer.generate_roles(project_config.resolve_context(repo_root=beta), skill_dir=package)
        match = len(generated) == 16 and all((beta / ('.codex/agents/%s.toml' % n if a == 'codex' else '.claude/agents/%s.md' % n)).read_text(encoding='utf-8') == text for (a, n), text in generated.items())
        step('beta deployed bytes equal the deployed candidate generate_roles output (post hoc comparison)', match, renderer=renderer.__file__)
    except Exception as error:  # noqa: BLE001
        step('beta deployed bytes equal the deployed candidate generate_roles output (post hoc comparison)', False, error=repr(error))


@functools.cache
def load_legacy_support(mask):
    """The MASK under test's own schema-true legacy builder (tests/legacy_support.py)."""
    spec = importlib.util.spec_from_file_location('mask_legacy_support', Path(mask).resolve().parent / 'tests/legacy_support.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def legacy_lab(args, facts):
    """AC04 on a v1 machine (legacy project, legacy personal scope, unregistered declaration) in its own private homes."""
    legacy = load_legacy_support(args.mask)
    roots = legacy.build_legacy_machine(Path(args.work).resolve() / 'legacy', 1)
    machine = Machine(args.mask, roots.home, roots.personal, roots.base)
    clone = checkout_facts(roots.clone)
    head = clone['head']
    straggler = (roots.straggler / '.mask.json').read_bytes()
    facts.update(calls=machine.calls, base=str(roots.base), head=head)

    run, data = machine.run('doctor', '--check')
    migration = body(data).get('migration', {})
    step('legacy lab: doctor --check exits 7 with migration.required on the v1 machine',
         run.returncode == 7 and migration.get('required') is True and migration.get('machine') == 'legacy_v1' and 'migration.required' in codes(body(data).get('issues')),
         exit=run.returncode, issues=body(data).get('issues'), machine=migration.get('machine'))
    before = legacy.snapshot(roots.base, roots.base)
    run, preview = machine.run('doctor', '--migrate', '--dry-run')
    migration = body(preview).get('migration', {})
    facts['preview'] = dict(exit=run.returncode, proposed_tap=migration.get('proposed_tap'), acquisition=migration.get('acquisition'), config_after=migration.get('config_after'),
                            changes=[row.get('root') for row in migration.get('changes', [])], warnings=codes((preview or {}).get('warnings')), plan_hash=body(preview).get('plan_hash'))
    step('legacy lab: doctor --migrate --dry-run discloses the tap and both consumers and writes nothing (lab byte snapshot, clone facts)',
         run.returncode == 0 and preview['would_change'] is True and preview['changed'] is False and (migration.get('proposed_tap') or {}).get('alias') == TAP
         and sorted(facts['preview']['changes']) == sorted([str(roots.project), str(roots.personal)]) and legacy.snapshot(roots.base, roots.base) == before and checkout_facts(roots.clone) == clone,
         **facts['preview'])
    run, data = machine.run('doctor', '--migrate')
    config = load(roots.home / 'config.json')
    entry = config.get('sources', {}).get(TAP, {})
    locks = {scope: [row['commit'] for row in load(path).get('packages', [])] for scope, path in (('project', roots.project / '.mask.lock.json'), ('user', roots.home / 'user.lock.json'))}
    links = dict(machine.store_links(roots.project, ('.agents/skills/alpha', '.claude/skills/alpha')), **machine.store_links(roots.personal, ('.agents/skills/beta', '.claude/skills/beta')))
    facts['migrate'] = dict(exit=run.returncode, transaction=(data or {}).get('transaction'), warnings=codes((data or {}).get('warnings')), error=(data or {}).get('error'), tap=entry, locks=locks, links=links)
    step('legacy lab: doctor --migrate yields config v3 with the clone as authoring of tap agentskills, v2 declarations, locks at the clone HEAD and store links',
         run.returncode == 0 and data['transaction'] == 'committed' and config.get('schema_version') == 3 and entry.get('authoring') == str(roots.clone) and entry.get('line_endings') == 'exact'
         and load(roots.project / '.mask.json').get('schema_version') == 2 and load(roots.home / 'user.json').get('schema_version') == 2
         and locks == dict(project=[head], user=[head]) and all(links.values()) and (roots.straggler / '.mask.json').read_bytes() == straggler,
         **facts['migrate'])
    run, data = machine.run('doctor', '--check')
    step('legacy lab: doctor --check exits 0 after migration', run.returncode == 0, exit=run.returncode, issues=body(data).get('issues'))
    run, data = machine.run('update')
    fetch = body(data).get('fetches', {}).get(TAP, {})
    statuses = [row['status'] for row in body(data).get('consumers', [])]
    facts['update'] = dict(exit=run.returncode, error=(data or {}).get('error'), changed=(data or {}).get('changed'), fetches=body(data).get('fetches'), statuses=statuses)
    step('legacy lab: update fetches the migrated tap from the clone remote and no-ops for both consumers',
         run.returncode == 0 and fetch.get('attempted') is True and fetch.get('ok') is True and fetch.get('after') == head and statuses == ['unchanged', 'unchanged'] and data['changed'] is False,
         **facts['update'])
    after = checkout_facts(roots.clone)
    step('legacy lab: the clone HEAD, staged index, index file and status are unchanged', after == clone, before=clone, after=after)


def owner_rehearsal(args, facts):
    """A small MASK-0105 rehearsal: v1 config over a checked-out AgentSkills clone with a local bare origin and an empty registry."""
    legacy = load_legacy_support(args.mask)
    roots = legacy.layout(Path(args.work).resolve() / 'owner')
    roots.personal.mkdir(parents=True)
    bare_clone(args.agentskills, roots.upstream)
    git(roots.base, 'clone', '-q', roots.upstream, roots.clone)  # origin is the local bare repository; the working copy follows this host's core.autocrlf
    legacy.write_json(roots.home / 'config.json', legacy.v1_config(roots))
    legacy.write_json(roots.home / 'state.json', legacy.legacy_state())
    machine = Machine(args.mask, roots.home, roots.personal, roots.base)
    clone, upstream = checkout_facts(roots.clone), git(roots.upstream, 'rev-parse', 'HEAD')
    head = clone['head']
    facts.update(calls=machine.calls, base=str(roots.base), head=head, autocrlf=git(roots.clone, 'config', '--get', 'core.autocrlf', check=False),
                 crlf_working_copy=b'\r\n' in (roots.clone / 'skills/implement-rfc/SKILL.md').read_bytes())

    run, data = machine.run('doctor')
    migration = body(data).get('migration', {})
    facts['doctor'] = dict(exit=run.returncode, machine=migration.get('machine'), proposed_tap=migration.get('proposed_tap'), clone=migration.get('clone'), consumers=migration.get('consumers'), blockers=migration.get('blockers'))
    step('owner rehearsal: doctor reports the v1 machine, a clean clone, the proposed agentskills tap and no consumers',
         run.returncode == 0 and migration.get('required') is True and migration.get('machine') == 'legacy_v1' and (migration.get('proposed_tap') or {}).get('alias') == TAP
         and migration.get('consumers') == [] and (migration.get('clone') or {}).get('dirty') is False, **facts['doctor'])
    before = legacy.snapshot(roots.base, roots.base)
    run, preview = machine.run('doctor', '--migrate', '--dry-run')
    facts['preview'] = dict(exit=run.returncode, error=(preview or {}).get('error'), config_after=body(preview).get('migration', {}).get('config_after'), warnings=codes((preview or {}).get('warnings')))
    step('owner rehearsal: doctor --migrate --dry-run writes nothing', run.returncode == 0 and (preview or {}).get('changed') is False and legacy.snapshot(roots.base, roots.base) == before
         and checkout_facts(roots.clone) == clone, **facts['preview'])
    state = (roots.home / 'state.json').read_bytes()
    run, data = machine.run('doctor', '--migrate')
    config = load(roots.home / 'config.json')
    entry = config.get('sources', {}).get(TAP, {})
    facts['migrate'] = dict(exit=run.returncode, error=(data or {}).get('error'), transaction=(data or {}).get('transaction'), warnings=codes((data or {}).get('warnings')), config=config)
    step('owner rehearsal: doctor --migrate converts the configuration only: v3 with tap agentskills, authoring = the clone, exact bytes',
         run.returncode == 0 and config.get('schema_version') == 3 and list(config.get('sources', {})) == [TAP] and entry.get('authoring') == str(roots.clone) and entry.get('line_endings') == 'exact'
         and (roots.home / 'state.json').read_bytes() == state and sorted(path.name for path in roots.home.iterdir()) == ['config.json', 'operation.lock', 'state.json'], **facts['migrate'])
    def personal_verdict(details):
        """The shared readiness verdict of a personal scope without implement-rfc context: both required inputs missing, 16 roles setup_required."""
        rows = (details or {}).get('workflow', [])
        missing = {f'{SKILL} input project-config (.mask/skill-config/{SKILL}/project.json): missing', f'{SKILL} input project-rules (.mask/skill-config/{SKILL}/project.md): missing'}
        return len(rows) == 18 and missing <= set(rows) and sum(row.endswith(': setup_required') for row in rows) == 16

    run, data = machine.run('install', SKILL, '--user')
    links = machine.store_links(roots.personal)
    locked = [row['commit'] for row in load(roots.home / 'user.lock.json').get('packages', [])]
    facts['install'] = dict(exit=run.returncode, error=(data or {}).get('error'), transaction=(data or {}).get('transaction'), network=body(data).get('network'), links=links, locked=locked)
    step('owner rehearsal: install implement-rfc --user fetches the tap, links the personal scope from MASK_HOME/store/v1 and reports exit 4 workflow.incomplete (personal context and role setup missing)',
         run.returncode == 4 and code_of(data) == 'workflow.incomplete' and data['transaction'] == 'committed' and personal_verdict(data['error'].get('details'))
         and body(data).get('network') == 'fetch' and locked == [head] and all(links.values()), **facts['install'])
    run, data = machine.run('list', '--user')
    states = {row['skill']: row.get('states') for row in body(data).get('skills', [])}
    facts['list'] = dict(exit=run.returncode, states=states)
    step('owner rehearsal: list --user shows implement-rfc linked for claude and codex', run.returncode == 0 and states == {COORDINATE: dict(claude='linked', codex='linked')}, **facts['list'])
    run, data = machine.run('update')
    fetch = body(data).get('fetches', {}).get(TAP, {})
    statuses = [row['status'] for row in body(data).get('consumers', [])]
    facts['update'] = dict(exit=run.returncode, error=(data or {}).get('error'), changed=(data or {}).get('changed'), fetches=body(data).get('fetches'), statuses=statuses)
    step('owner rehearsal: update fetches the tap from origin and no-ops (same exit 4 workflow.incomplete verdict)', fetch.get('attempted') is True and fetch.get('ok') is True and fetch.get('after') == head
         and statuses == ['unchanged'] and (data or {}).get('changed') is False and run.returncode == 4 and code_of(data) == 'workflow.incomplete' and personal_verdict(data['error'].get('details')),
         **facts['update'])
    run, data = machine.run('doctor', '--check')
    issues = body(data).get('issues') or []
    facts['doctor_check'] = dict(exit=run.returncode, issues=issues)
    # MASK-0105 expects exit 0 here; without personal implement-rfc context and consented setup the documented verdict is 7.
    step('owner rehearsal: doctor --check exits 7 with only workflow.incomplete (personal context and role setup missing; no migration issue)',
         run.returncode == 7 and codes(issues) == ['workflow.incomplete'] and personal_verdict(issues[0].get('details')), **facts['doctor_check'])
    after = checkout_facts(roots.clone)
    step("owner rehearsal: the clone's HEAD, staged index, index file and status and the bare origin are unchanged", after == clone and git(roots.upstream, 'rev-parse', 'HEAD') == upstream,
         before=clone, after=after)


def host_facts(args):
    mask_root = Path(args.mask).resolve().parent
    facts = dict(os=platform.platform(), os_release=platform.release(), os_version=platform.version(), machine=platform.machine(),
                 python=sys.version.split()[0], python_executable=sys.executable,
                 git=subprocess.run(['git', '--version'], capture_output=True, text=True).stdout.strip(),
                 core_autocrlf=dict(effective=git(mask_root, 'config', '--get', 'core.autocrlf', check=False), origins=git(mask_root, 'config', '--show-origin', '--get-all', 'core.autocrlf', check=False)),
                 mask=dict(entry=str(Path(args.mask).resolve()), revision=git(mask_root, 'rev-parse', 'HEAD', check=False), status=git(mask_root, 'status', '--porcelain', check=False)),
                 agentskills=dict(path=str(Path(args.agentskills).resolve()), revision=git(args.agentskills, 'rev-parse', 'HEAD', check=False)))
    if platform.system() == 'Windows':
        facts['windows_edition'] = platform.win32_edition()
    elif platform.system() == 'Darwin':
        facts['macos'] = platform.mac_ver()[0]
    return facts


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
    script = Path(__file__).resolve()
    record = dict(qualifier=dict(path=str(script), sha256=hashlib.sha256(script.read_bytes()).hexdigest()), host=host_facts(args))
    try:
        for name, section in (('tap_lab', tap_lab), ('legacy_lab', legacy_lab), ('owner_rehearsal', owner_rehearsal)):
            record[name] = {}
            try:
                section(args, record[name])
            except Exception:  # noqa: BLE001 - one section's crash is recorded as a failed step; the independent sections still run
                step(f'{name} ran to completion', False, error=traceback.format_exc()[-3000:])
    finally:
        record['steps'] = RESULTS
        record['passed'] = sum(1 for r in RESULTS if r['ok'])
        record['failed'] = [r['step'] for r in RESULTS if not r['ok']]
        Path(args.report).write_text(json.dumps(record, indent=2, default=str), encoding='utf-8')
    print(json.dumps(dict(passed=record['passed'], failed=record['failed'])))
    return 0 if not record['failed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
