import json
import os
from pathlib import Path
import subprocess
import shutil
import shlex
import sys

from tests.support import Fixture, ENTRY


class HostIntegrationTests(Fixture):
    def setUp(self):
        super().setUp()
        self.init()
        self.declare()

    def hook(self, agent, cwd=None):
        run = subprocess.run([sys.executable, str(ENTRY.parent / 'mask_integration.py'), 'host-hook', str(self.home), agent],
                             cwd=cwd or self.project, input='{}', capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        return json.loads(run.stdout)

    def test_host_specific_ready_and_blocked_protocols(self):
        claude = self.hook('claude')
        self.assertFalse(claude['hookSpecificOutput']['reloadSkills'])
        self.assertNotIn('continue', claude)
        codex = self.hook('codex')
        self.assertFalse(codex['continue'])
        self.assertNotIn('reloadSkills', codex['hookSpecificOutput'])
        self.call('integration', 'approve', '--project', self.project)
        self.assertTrue(self.hook('claude')['hookSpecificOutput']['reloadSkills'])
        self.assertNotIn('continue', self.hook('codex'))

    def test_owned_settings_preserve_unrelated_groups_and_trust(self):
        for agent, relative in [('claude', '.claude/settings.local.json'), ('codex', '.codex/hooks.json')]:
            with self.subTest(agent=agent):
                path = self.project / relative
                path.parent.mkdir(exist_ok=True)
                original = dict(description='mine', hooks=dict(SessionStart=[dict(hooks=[dict(type='command', command='echo unrelated')])]))
                path.write_text(json.dumps(original))
                self.call('integration', 'enable', '--agent', agent, '--project', self.project)
                value = json.loads(path.read_text())
                self.assertEqual(value['description'], 'mine')
                self.assertEqual(value['hooks']['SessionStart'][0], original['hooks']['SessionStart'][0])
                self.assertEqual(len(value['hooks']['SessionStart']), 2)
                self.call('integration', 'disable', '--agent', agent, '--project', self.project)
                self.assertEqual(json.loads(path.read_text()), original)
                self.assertFalse((self.project / '.codex/config.toml').exists())

    def test_startup_preflights_personal_and_project_before_effects(self):
        self.call('integration', 'approve', '--project', self.project)
        personal = self.base / 'personal'
        personal.mkdir()
        self.call('user', 'init')
        self.call('user', 'require', 'beta')
        self.call('user', 'register', '--user-home', personal)
        leaf = personal / '.agents/skills/beta'
        leaf.mkdir(parents=True)
        before = self.snapshot()
        self.call('ensure', '--event', 'startup', code=4)
        self.assertEqual(before, self.snapshot())
        leaf.rmdir()
        self.call('ensure', '--event', 'startup')
        self.assertTrue(leaf.is_symlink())
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())
        before = self.snapshot()
        self.call('ensure', '--event', 'startup', '--check')
        self.assertEqual(before, self.snapshot())

    def test_no_project_session_checks_only_registered_personal_scope(self):
        personal = self.base / 'personal'
        personal.mkdir()
        self.call('user', 'init')
        self.call('user', 'require', 'alpha')
        self.call('user', 'register', '--user-home', personal)
        result = self.call('ensure', '--event', 'startup', cwd=self.base)
        self.assertEqual(result['data']['projects'], [])
        self.assertEqual(len(result['data']['users']), 1)
        self.assertTrue((personal / '.agents/skills/alpha').is_symlink())
        self.assertFalse((self.home / 'integration.json').exists())

    def test_prelaunch_gates_and_preserves_argv_outside_writer_lock(self):
        if os.name == 'nt':
            self.skipTest('POSIX fake executable fixture; native Windows launch is separately required')
        binary = self.base / 'bin'
        binary.mkdir()
        fake = binary / 'codex'
        fake.write_text('#!' + sys.executable + '\nimport sys,json\nfrom pathlib import Path\nsys.path.insert(0,' + repr(str(ENTRY.parent)) + ')\nimport mask_core\nwith mask_core.writer_lock(Path(' + repr(str(self.home)) + ')):\n print(json.dumps(sys.argv[1:]))\n')
        fake.chmod(0o755)
        environment = dict(os.environ, MASK_HOME=str(self.home), PATH=str(binary) + os.pathsep + os.environ['PATH'])
        command = [sys.executable, str(ENTRY), 'launch', '--agent', 'codex', '--project', str(self.project), '--json', '--', 'literal space', '$(not executed)', '--json']
        run = subprocess.run(command, capture_output=True, text=True, env=environment)
        self.assertEqual(run.returncode, 4, run.stdout)
        self.call('integration', 'approve', '--project', self.project)
        run = subprocess.run(command, capture_output=True, text=True, env=environment)
        self.assertEqual(run.returncode, 0, run.stdout)
        result = json.loads(run.stdout)
        self.assertEqual(json.loads(result['data']['host']['stdout']), ['literal space', '$(not executed)', '--json'])
        self.assertEqual(result['data']['host']['exit_code'], 0)

    def test_changed_host_entry_and_parent_are_preserved(self):
        self.call('integration', 'enable', '--agent', 'codex', '--project', self.project)
        path = self.project / '.codex/hooks.json'
        value = json.loads(path.read_text())
        value['hooks']['SessionStart'][0]['hooks'][0]['command'] = 'edited'
        path.write_text(json.dumps(value))
        before = self.snapshot()
        self.call('integration', 'disable', '--agent', 'codex', '--project', self.project, code=4)
        self.assertEqual(before, self.snapshot())

    def test_native_macos_launcher_and_installed_host_prelaunch(self):
        if sys.platform != 'darwin':
            self.skipTest('Native macOS acceptance')
        self.call('integration', 'approve', '--project', self.project)
        binary = self.base / 'launchers'
        binary.mkdir()
        self.call('self', 'install', '--bin-dir', binary)
        launcher = binary / 'mask'
        environment = dict(os.environ, MASK_HOME=str(self.home))
        run = subprocess.run([str(launcher), 'ensure', '--project', str(self.project), '--json'], env=environment, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())
        for agent in ('claude', 'codex'):
            with self.subTest(agent=agent):
                if shutil.which(agent) is None:
                    continue  # Loading is never inferred from an absent host.
                run = subprocess.run([str(launcher), 'launch', '--agent', agent, '--project', str(self.project), '--json', '--', '--version'], env=environment, capture_output=True, text=True)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                result = json.loads(run.stdout)
                self.assertEqual(result['data']['host']['exit_code'], 0)
                self.assertTrue(result['data']['host']['stdout'].strip())

    def test_user_adapter_readies_a_future_approved_clone(self):
        personal = self.base / 'personal'
        personal.mkdir()
        self.call('user', 'init')
        self.call('user', 'register', '--user-home', personal)
        self.call('integration', 'enable', '--agent', 'claude')
        settings = personal / '.claude/settings.json'
        command = json.loads(settings.read_text())['hooks']['SessionStart'][0]['hooks'][0]['command']
        self.assertFalse((personal / '.claude/settings.local.json').exists())
        boundary = self.base / 'clones'
        boundary.mkdir()
        self.git(self.project, 'config', 'user.name', 'Fixture')
        self.git(self.project, 'config', 'user.email', 'fixture@example.invalid')
        self.git(self.project, 'add', '.mask.json')
        self.git(self.project, 'commit', '-m', 'declaration')
        self.call('integration', 'approve', '--repository', str(self.project), '--under', boundary)
        clone = boundary / 'new-clone'
        self.git(self.base, 'clone', str(self.project), str(clone))
        run = subprocess.run(shlex.split(command), cwd=clone, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue(json.loads(run.stdout)['hookSpecificOutput']['reloadSkills'])
        self.assertTrue((clone / '.agents/skills/alpha').is_symlink())
        self.assertTrue(self.call('integration', 'inspect', '--agent', 'claude')['data']['coverage']['startup'])
        self.call('integration', 'disable', '--agent', 'claude')
        self.assertEqual(json.loads(settings.read_text())['hooks']['SessionStart'], [])
