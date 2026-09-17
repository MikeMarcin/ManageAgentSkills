"""Complete readiness on every public entrypoint (MASK-0090, RFC-MASK-0019 AC01/AC06/AC08).

install/remove/update share ensure's final prerequisite verdict after their link
transaction, doctor observes declared roles without deploying, launch never starts
a host behind an unmet prerequisite, and capabilities advertise the contract. Every
case runs the public CLI as a subprocess against a disposable source; the synthetic
pack fixtures use ``fixture-model-do-not-run`` and never touch a real host profile.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from tests.support import Fixture, ENTRY, TAP

PACK = ENTRY.parent / 'docs/rfcs/assets/mask-corrective-ux-readiness'
STATIC = PACK / 'fixtures/static-package'
GENERATED = PACK / 'fixtures/generated-package'
CONTEXT = PACK / 'fixtures/consumer/.mask'
INTEGRATION = ENTRY.parent / 'mask_integration.py'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def republish(package):
    """Recompute every static asset fingerprint of a package descriptor after editing its files."""
    descriptor = package / 'mask-workflow.json'
    value = json.loads(descriptor.read_text(encoding='utf-8'))
    for role in value['native_roles']:
        if 'asset' in role:
            role['asset']['sha256'] = sha256((package / role['asset']['path']).read_bytes())
    descriptor.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
    return value


class EntrypointFixture(Fixture):
    bootstrap = Fixture.init

    def setUp(self):
        super().setUp()
        self.bootstrap()

    def add_package(self, name, package):
        """Author a package and publish it to the tap upstream; MASK observes it only after a fetch."""
        shutil.copytree(package, self.source / 'skills' / name)
        return Fixture.publish(self, f'add {name}')

    def consumer(self, skills, targets=None):
        """A registered, approved v2 consumer whose lock and store artifacts are prepared but not yet deployed."""
        shutil.copytree(CONTEXT, self.project / '.mask')
        declaration = dict(schema_version=2, sources=self.binding(), skills=[dict(source=TAP, id=identifier) for identifier in skills])
        if targets is not None:
            declaration['default_agents'] = targets
        (self.project / '.mask.json').write_text(json.dumps(declaration) + '\n')
        self.call('source', 'fetch', TAP)
        self.call('lock', '--project', self.project)
        self.call('source', 'fetch', '--locked', '--offline', '--project', self.project)
        self.call('project', 'register', self.project)
        self.call('integration', 'approve', '--project', self.project)

    def human(self, *args, env=None):
        environment = dict(os.environ, MASK_HOME=str(self.home), PYTHONDONTWRITEBYTECODE='1', **(env or {}))
        return subprocess.run([sys.executable, '-B', str(ENTRY), *map(str, args)], capture_output=True, encoding='utf-8', cwd=self.project, env=environment, stdin=subprocess.DEVNULL)

    def roles(self, data, skill='implement-rfc'):
        for entry in data['data'].get('workflow_readiness', []):
            for item in entry['skills']:
                if item['skill'] == skill:
                    return {(row['agent'], row['name']): row for row in item['roles']}
        return {}


class Capabilities(EntrypointFixture):
    def test_capabilities_advertise_the_readiness_contract(self):
        data = self.call('capabilities')['data']
        self.assertEqual(data['workflow']['readiness'], 'workflow_readiness_v1')
        self.assertTrue(data['workflow']['native_roles'])
        self.assertTrue(data['workflow']['staged_setup'])
        self.assertEqual(data['workflow']['host_load'], 'not_verified')
        self.assertEqual(data['workflow']['entrypoints'], ['ensure', 'install', 'remove', 'upgrade', 'doctor', 'launch'])
        run = self.human('capabilities')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('workflow_readiness_v1', run.stdout)


class InstallAndRemove(EntrypointFixture):
    def test_install_commits_links_but_cannot_report_success_with_setup_required_roles(self):
        self.add_package('implement-rfc', GENERATED)
        shutil.copytree(CONTEXT, self.project / '.mask')
        result = self.call('install', 'implement-rfc', code=4)
        self.assertEqual(result['error']['code'], 'workflow.incomplete')
        self.assertEqual(result['transaction'], 'committed')
        self.assertTrue(result['changed'])
        self.assertTrue((self.project / '.agents/skills/implement-rfc').is_symlink())
        self.assertEqual(result['data']['workflow'], {str(self.project): 'incomplete'})
        self.assertIn('implement-rfc codex/rfc-integrator: setup_required', result['error']['details']['workflow'])
        self.assertIn("mask ensure", result['error']['remediation'][0]['message'])
        roles = self.roles(result)
        self.assertEqual(roles[('codex', 'rfc-integrator')]['host_load'], 'not_verified')
        self.assertEqual(roles[('codex', 'rfc-integrator')]['producer'], 'setup')
        self.assertFalse((self.project / '.codex/agents').exists(), 'install never runs setup')
        self.assertFalse(list(self.project.glob('**/__pycache__')))
        again = self.human('install', 'implement-rfc')
        self.assertEqual(again.returncode, 4, again.stdout)
        self.assertIn('.codex/agents/rfc-integrator.toml', again.stderr)
        self.assertIn('setup needed', again.stderr)
        self.assertIn('mask ensure', again.stderr)
        self.assertNotIn('{', again.stdout + again.stderr)
        removed = self.call('remove', 'implement-rfc')
        self.assertEqual(removed['data']['workflow'], {str(self.project): 'not_declared'})
        self.assertFalse((self.project / '.agents/skills/implement-rfc').exists())

    def test_static_roles_deploy_with_install_and_plain_skills_stay_not_declared(self):
        self.add_package('implement-rfc', STATIC)
        shutil.copytree(CONTEXT, self.project / '.mask')
        plain = self.call('install', 'alpha')
        self.assertEqual(plain['data']['workflow'], {str(self.project): 'not_declared'})
        result = self.call('install', 'implement-rfc')
        self.assertEqual(result['data']['workflow'], {str(self.project): 'complete'})
        self.assertEqual((self.project / '.codex/agents/rfc-integrator.toml').read_bytes(), (STATIC / 'runtime/roles/codex/rfc-integrator.toml').read_bytes())
        self.assertEqual(self.roles(result)[('codex', 'rfc-integrator')]['route'], {'model': 'fixture-model-do-not-run'})


class Doctor(EntrypointFixture):
    def test_doctor_observes_declared_roles_without_deploying_and_check_exits_seven(self):
        self.add_package('implement-rfc', STATIC)
        self.consumer(['implement-rfc'])
        self.assertEqual(self.call('ensure')['data']['scope_readiness'][0]['workflow'], 'complete')
        healthy = self.call('doctor')
        self.assertTrue(healthy['data']['healthy'])
        self.assertEqual(healthy['data']['workflow'], {str(self.project): 'complete'})
        self.call('doctor', '--check')
        missing = self.project / '.codex/agents/rfc-integrator.toml'
        missing.unlink()
        edited = self.project / '.claude/agents/rfc-worker.md'
        edited.write_text('---\nname: rfc-worker\nmodel: fixture-model-do-not-run\n---\n\nlocal edit\n', encoding='utf-8')
        before = self.snapshot(self.project)
        result = self.call('doctor')
        self.assertFalse(result['data']['healthy'])
        self.assertEqual(result['data']['workflow'], {str(self.project): 'incomplete'})
        issue = next(item for item in result['data']['issues'] if item['code'] == 'workflow.incomplete')
        self.assertIn('implement-rfc codex/rfc-integrator: missing', issue['details']['workflow'])
        self.assertIn('implement-rfc claude/rfc-worker: modified', issue['details']['workflow'])
        self.assertEqual(self.roles(result)[('codex', 'rfc-integrator')]['host_load'], 'not_verified')
        self.assertEqual(before, self.snapshot(self.project), 'doctor deploys nothing')
        check = self.call('doctor', '--check', code=7)
        self.assertEqual(check['error']['code'], 'state.drift')
        self.assertIn('implement-rfc codex/rfc-integrator: missing', check['error']['details']['workflow'])
        run = self.human('doctor')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('.codex/agents/rfc-integrator.toml', run.stdout)
        self.assertIn('role file(s): missing', run.stdout)
        self.assertIn('.claude/agents/rfc-worker.md', run.stdout)
        self.assertIn('existing files differ', run.stdout)
        run = self.human('doctor', '--check')
        self.assertEqual(run.returncode, 7)
        self.assertIn('rfc-integrator', run.stderr)
        self.assertNotIn('{', run.stdout + run.stderr)
        # Cheap inventory stays observational and labels workflow state unexamined.
        listing = self.call('list')
        self.assertNotIn('workflow_readiness', listing['data'])
        self.assertTrue(any('workflow setup were not checked' in item for item in listing['data']['limitations']))
        self.assertEqual(before, self.snapshot(self.project))


class Launch(EntrypointFixture):
    def test_launch_never_starts_the_host_behind_a_missing_integrator(self):
        if os.name == 'nt':
            self.skipTest('POSIX fake executable fixture; native Windows launch is separately required')
        self.add_package('implement-rfc', GENERATED)
        self.consumer(['implement-rfc'])
        linked = self.call('ensure', code=4)
        self.assertEqual(linked['error']['code'], 'workflow.incomplete')
        self.assertTrue((self.project / '.agents/skills/implement-rfc').is_symlink(), 'links are correct; only the role is missing')
        binary = self.base / 'bin'
        binary.mkdir()
        sentinel = self.base / 'host-started'
        for agent in ('codex', 'claude'):
            fake = binary / agent
            fake.write_text('#!/bin/sh\necho started > ' + repr(str(sentinel)).replace("'", '"') + '\nexit 0\n')
            fake.chmod(0o755)
        environment = dict(os.environ, MASK_HOME=str(self.home), PATH=str(binary) + os.pathsep + os.environ['PATH'], PYTHONDONTWRITEBYTECODE='1')
        for agent in ('codex', 'claude'):
            run = subprocess.run([sys.executable, '-B', str(ENTRY), 'launch', '--agent', agent, '--project', str(self.project), '--json', '--', '--version'], capture_output=True, text=True, env=environment)
            self.assertEqual(run.returncode, 4, run.stdout)
            result = json.loads(run.stdout)
            self.assertEqual(result['error']['code'], 'workflow.incomplete')
            self.assertIn(f'implement-rfc {agent}/rfc-integrator: setup_required', result['error']['details']['workflow'])
            self.assertNotIn('host', result['data'])
            self.assertFalse(sentinel.exists(), 'the host was never invoked')
        human = subprocess.run([sys.executable, '-B', str(ENTRY), 'launch', '--agent', 'codex', '--project', str(self.project), '--', '--version'], capture_output=True, text=True, env=environment)
        self.assertEqual(human.returncode, 4)
        self.assertIn('rfc-integrator', human.stderr)
        self.assertFalse(sentinel.exists())
        # A provider startup hook that cannot stop the host says so; one that can, stops.
        for agent, gate in (('claude', False), ('codex', True)):
            hook = subprocess.run([sys.executable, '-B', str(INTEGRATION), 'host-hook', str(self.home), agent], capture_output=True, text=True, env=environment, cwd=self.project)
            self.assertEqual(hook.returncode, 0, hook.stderr)
            payload = json.loads(hook.stdout)
            context = payload['hookSpecificOutput']['additionalContext']
            self.assertIn('blocked (workflow.incomplete)', context)
            self.assertEqual(payload.get('continue', True), not gate)
            self.assertEqual('warning-only' in context, not gate)
            self.assertIn('mask launch', context) if not gate else None
        self.assertFalse(sentinel.exists())


class TapUpdate(EntrypointFixture):
    """A pinned consumer of the fixture tap (W16 on taps: requirements follow the fetched candidate)."""

    def setUp(self):
        super().setUp()
        # Fingerprinted role assets must reach the tap byte-exact; a publisher disables line-ending normalization.
        (self.source / '.gitattributes').write_text('* -text\n', encoding='utf-8')
        self.git(self.source, 'add', '.gitattributes')
        self.package = self.source / 'skills/implement-rfc'
        shutil.copytree(STATIC, self.package)
        value = json.loads((self.package / 'mask-workflow.json').read_text(encoding='utf-8'))
        value['native_roles'] = [role for role in value['native_roles'] if role['name'] != 'rfc-integrator']
        (self.package / 'mask-workflow.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
        Fixture.publish(self, 'descriptor without the integrator')
        shutil.copytree(CONTEXT, self.project / '.mask')
        installed = self.call('install', 'implement-rfc')
        self.assertEqual(installed['data']['workflow'], {str(self.project): 'complete'})
        self.assertFalse((self.project / '.codex/agents/rfc-integrator.toml').exists())

    def publish(self, message):
        """Refingerprint the edited package and push it to the tap upstream; MASK sees it only after a fetch."""
        republish(self.package)
        return Fixture.publish(self, message)

    def locked(self):
        return json.loads((self.project / '.mask.lock.json').read_text(encoding='utf-8'))['packages'][0]['commit']

    def test_update_adds_renames_and_converts_roles_from_the_candidate(self):
        value = json.loads((self.package / 'mask-workflow.json').read_text(encoding='utf-8'))
        # The candidate adds the integrator with bytes that differ from the retained fixture and renames rfc-scout.
        for agent, suffix in (('codex', 'toml'), ('claude', 'md')):
            integrator = self.package / f'runtime/roles/{agent}/rfc-integrator.{suffix}'
            integrator.write_bytes(integrator.read_bytes().replace(b'Fixture identity only.', b'Candidate identity only.'))
            value['native_roles'].append(dict(agent=agent, name='rfc-integrator', asset=dict(path=f'runtime/roles/{agent}/rfc-integrator.{suffix}', sha256='0' * 64)))
            old = self.package / f'runtime/roles/{agent}/rfc-scout.{suffix}'
            new = self.package / f'runtime/roles/{agent}/rfc-explorer.{suffix}'
            new.write_bytes(old.read_bytes().replace(b'rfc-scout', b'rfc-explorer'))
            old.unlink()
            for role in value['native_roles']:
                if role['name'] == 'rfc-scout' and role['agent'] == agent:
                    role.update(name='rfc-explorer', asset=dict(path=f'runtime/roles/{agent}/rfc-explorer.{suffix}', sha256='0' * 64))
        (self.package / 'mask-workflow.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
        candidate = self.publish('add integrator, rename scout')
        edited = self.project / '.claude/agents/rfc-scout.md'
        edited.write_text('---\nname: rfc-scout\nmodel: fixture-model-do-not-run\n---\n\nlocal edit\n', encoding='utf-8')
        self.call('source', 'fetch')
        preview = self.call('upgrade', '--dry-run')
        kinds = {(action['kind'], action.get('name')) for action in preview['actions'] if action['kind'].startswith('native_role')}
        self.assertIn(('native_role.write', 'rfc-integrator'), kinds)
        self.assertIn(('native_role.write', 'rfc-explorer'), kinds)
        self.assertIn(('native_role.remove', 'rfc-scout'), kinds)
        integrator = self.roles(preview)[('codex', 'rfc-integrator')]
        self.assertEqual(integrator['state'], 'missing')
        self.assertEqual(integrator['route'], {'model': 'fixture-model-do-not-run'})
        self.assertEqual(integrator['host_load'], 'not_verified')
        self.assertFalse((self.project / '.codex/agents/rfc-integrator.toml').exists(), 'a dry run deploys nothing')
        result = self.call('upgrade')
        self.assertEqual(self.locked(), candidate)
        self.assertEqual(result['data']['workflow'], {str(self.project): 'complete'})
        self.assertEqual((self.project / '.codex/agents/rfc-integrator.toml').read_bytes(), (self.package / 'runtime/roles/codex/rfc-integrator.toml').read_bytes())
        self.assertIn(b'Candidate identity only.', (self.project / '.codex/agents/rfc-integrator.toml').read_bytes())
        self.assertTrue((self.project / '.codex/agents/rfc-explorer.toml').is_file())
        self.assertFalse((self.project / '.codex/agents/rfc-scout.toml').exists(), 'an unchanged managed legacy name is retired')
        self.assertEqual(edited.read_text(encoding='utf-8').splitlines()[-1], 'local edit', 'an edited legacy role is preserved')
        self.assertIn('native_role.released', {warning['code'] for warning in result['warnings']})
        self.assertEqual(self.roles(result)[('codex', 'rfc-explorer')]['state'], 'ok')
        # A later candidate turns the integrator into a generated role: the lock advances, links stay, readiness is truthful.
        value = json.loads((self.package / 'mask-workflow.json').read_text(encoding='utf-8'))
        generated = json.loads((GENERATED / 'mask-workflow.json').read_text(encoding='utf-8'))
        value['setup'] = generated['setup']
        for role in value['native_roles']:
            if role['name'] == 'rfc-integrator':
                role.pop('asset')
                role['setup'] = 'prepare-roles'
        (self.package / 'mask-workflow.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
        shutil.copytree(GENERATED / 'scripts', self.package / 'scripts')
        converted = self.publish('generate the integrator')
        outcome = self.call('upgrade', code=4)
        self.assertEqual(outcome['error']['code'], 'workflow.incomplete', outcome['error'])
        self.assertEqual(self.locked(), converted)
        self.assertEqual(outcome['data']['workflow'], {str(self.project): 'incomplete'})
        self.assertIn('implement-rfc codex/rfc-integrator: setup_required', outcome['error']['details']['workflow'])
        self.assertIn('mask ensure', outcome['error']['remediation'][0]['message'])
        self.assertIn(b'Candidate identity only.', (self.project / '.codex/agents/rfc-integrator.toml').read_bytes(), 'the previous managed output is preserved')
        self.assertFalse(list(self.project.glob('**/__pycache__')), 'update never runs setup')
        self.assertEqual(self.call('upgrade', code=4)['error']['code'], 'workflow.incomplete', 'an unchanged rerun cannot report success either')
