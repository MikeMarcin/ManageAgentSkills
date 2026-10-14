"""The one-line installers against a disposable local program repository.

Each native script is run from downloaded text in the current shell, with only its
documented environment overrides; it never reaches the network and never touches
this checkout or the developer's home.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class InstallerFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mask-installer-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.author = self.base / 'author'
        self.author.mkdir()
        for module in ROOT.glob('mask*.py'):
            shutil.copyfile(module, self.author / module.name)
        shutil.copytree(ROOT / 'schemas', self.author / 'schemas')
        self.git(self.author, 'init', '-q', '-b', 'main')
        self.git(self.author, 'config', 'user.name', 'Fixture')
        self.git(self.author, 'config', 'user.email', 'fixture@example.invalid')
        self.git(self.author, 'add', '.')
        self.git(self.author, 'commit', '-q', '-m', 'program')
        self.remote = self.base / 'remote' / 'ManageAgentSkills.git'
        self.remote.parent.mkdir()
        self.git(self.base, 'init', '-q', '--bare', '-b', 'main', str(self.remote))
        self.git(self.author, 'push', '-q', str(self.remote), 'main')
        self.home = self.base / 'home'
        self.home.mkdir()

    def git(self, root, *args):
        return subprocess.run(['git', '-C', str(root), *args], capture_output=True, encoding='utf-8', check=True).stdout.strip()

    def publish(self):
        with (self.author / 'mask.py').open('a', encoding='utf-8') as handle:
            handle.write('\n# published later\n')
        self.git(self.author, 'commit', '-q', '-a', '-m', 'later')
        self.git(self.author, 'push', '-q', str(self.remote), 'main')


@unittest.skipIf(os.name == 'nt', 'install.sh is the POSIX installer; install.ps1 is the Windows one')
class ShellInstaller(InstallerFixture):
    def install(self, *, default_repository=False, **extra):
        env = dict(os.environ, HOME=str(self.home), MASK_HOME=str(self.base / 'machine'), MASK_REPO=str(self.remote), MASK_PYTHON=sys.executable,
                   PYTHONDONTWRITEBYTECODE='1', GIT_TERMINAL_PROMPT='0')
        for name in ('XDG_DATA_HOME', 'MASK_INSTALL_DIR', 'MASK_BIN_DIR', 'MASK_CLONE_WITH_GH'):
            env.pop(name, None)
        if default_repository:
            env.pop('MASK_REPO')
        env.update(extra)
        script = (ROOT / 'install.sh').read_text(encoding='utf-8')
        return subprocess.run(['sh'], input=script, capture_output=True, encoding='utf-8', env=env, cwd=str(self.base), timeout=120)

    def gh_shim(self):
        binary = self.base / 'shim'
        binary.mkdir()
        log = self.base / 'gh.log'
        shim = binary / 'gh'
        shim.write_text(
            '#!/bin/sh\n'
            '[ "$1" = repo ] && [ "$2" = clone ] || exit 91\n'
            'printf "%s\\n" "$*" > "$MASK_TEST_GH_LOG"\n'
            'exec git clone --quiet "$MASK_TEST_REMOTE" "$4"\n',
            encoding='utf-8', newline='\n')
        shim.chmod(0o755)
        return binary, log

    def test_installs_then_updates_in_place_and_preserves_what_it_does_not_own(self):
        first = self.install()
        self.assertEqual(first.returncode, 0, first.stderr)
        program, launcher = self.home / '.local/share/mask', self.home / '.local/bin/mask'
        self.assertTrue((program / 'mask.py').is_file())
        self.assertIn(str(program / 'mask.py'), launcher.read_text(encoding='utf-8'))
        self.assertIn('is not on your PATH', first.stdout)
        self.assertRegex(first.stdout, r'Installed mask \S+ \([0-9a-f]+\)')
        self.assertIn(f'{launcher} tap agentskills', first.stdout)
        version = subprocess.run([str(launcher), '--version'], capture_output=True, encoding='utf-8', env=dict(os.environ, HOME=str(self.home)))
        self.assertEqual((version.returncode, version.stdout.startswith('mask ')), (0, True), version.stderr)
        # Running it again fast-forwards the same clone to what was published since.
        self.publish()
        again = self.install(PATH=str(launcher.parent) + os.pathsep + os.environ['PATH'])
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn('Updating MASK', again.stdout)
        self.assertRegex(again.stdout, r'Updated mask \S+ \([0-9a-f]+ -> [0-9a-f]+\)')
        self.assertIn('Already up to date: mask ', self.install().stdout)
        self.assertNotIn('is not on your PATH', again.stdout)
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), self.git(self.author, 'rev-parse', 'HEAD'))

    def test_explicit_authenticated_gh_clone(self):
        binary, log = self.gh_shim()
        installed = self.install(
            default_repository=True,
            MASK_CLONE_WITH_GH='1',
            PATH=str(binary) + os.pathsep + os.environ['PATH'],
            MASK_TEST_REMOTE=str(self.remote),
            MASK_TEST_GH_LOG=str(log))
        self.assertEqual(installed.returncode, 0, installed.stderr)
        self.assertTrue((self.home / '.local/share/mask/mask.py').is_file())
        self.assertIn('repo clone MikeMarcin/ManageAgentSkills', log.read_text(encoding='utf-8'))

    def test_public_default_uses_https_git_without_gh(self):
        # Redirect only this exact public URL to the disposable local remote.
        config = self.base / 'fixture-gitconfig'
        config.write_text(f'[url "{self.remote.as_posix()}"]\n\tinsteadOf = https://github.com/MikeMarcin/ManageAgentSkills.git\n')
        installed = self.install(default_repository=True, GIT_CONFIG_GLOBAL=str(config), GIT_CONFIG_SYSTEM=os.devnull)
        self.assertEqual(installed.returncode, 0, installed.stderr)
        program = self.home / '.local/share/mask'
        self.assertEqual(self.git(program, 'remote', 'get-url', 'origin'), 'https://github.com/MikeMarcin/ManageAgentSkills.git')
        self.assertTrue((program / 'mask.py').is_file())

    def test_uninstall_removes_its_own_launcher_and_says_what_is_left(self):
        self.assertEqual(self.install().returncode, 0)
        launcher, env = self.home / '.local/bin/mask', dict(os.environ, HOME=str(self.home), MASK_HOME=str(self.base / 'machine'), PYTHONDONTWRITEBYTECODE='1')
        def mask(*args):
            return subprocess.run([str(launcher) if launcher.exists() else sys.executable, *([] if launcher.exists() else [str(self.home / '.local/share/mask/mask.py')]), *args],
                                  capture_output=True, encoding='utf-8', env=env, cwd=str(self.base))
        preview = mask('self', 'uninstall', '--dry-run')
        self.assertEqual((preview.returncode, launcher.exists()), (0, True), preview.stderr)
        self.assertIn('Would remove 1 launcher', preview.stdout)
        done = mask('self', 'uninstall')
        self.assertEqual((done.returncode, launcher.exists()), (0, False), done.stderr)
        self.assertIn('Removed 1 launcher.', done.stdout)
        self.assertIn('rm -rf', done.stdout)
        self.assertTrue((self.home / '.local/share/mask/mask.py').is_file())  # Folders are never deleted for you.
        self.assertIn('No MASK launcher is recorded', mask('self', 'uninstall').stdout)
        # An edited launcher is somebody's file: kept, and said so.
        self.assertEqual(self.install().returncode, 0)
        launcher.write_text(launcher.read_text(encoding='utf-8') + '# mine\n', encoding='utf-8')
        kept = mask('self', 'uninstall')
        self.assertEqual((kept.returncode, launcher.exists()), (0, True), kept.stderr)
        self.assertIn('edited since MASK wrote it', kept.stdout)

    def test_refuses_without_effect_when_the_target_is_something_else_or_python_is_too_old(self):
        occupied = self.base / 'occupied'
        occupied.mkdir()
        (occupied / 'notes.txt').write_text('mine', encoding='utf-8')
        refused = self.install(MASK_INSTALL_DIR=str(occupied))
        self.assertEqual((refused.returncode, (occupied / 'notes.txt').read_text(encoding='utf-8')), (1, 'mine'))
        self.assertIn('is not a MASK clone', refused.stderr)
        old = self.base / 'old-python'
        old.write_text('#!/bin/sh\nexit 1\n', encoding='utf-8')
        old.chmod(0o755)
        unsupported = self.install(MASK_PYTHON=str(old))
        self.assertEqual(unsupported.returncode, 1)
        self.assertIn('older than Python 3.11', unsupported.stderr)
        self.assertFalse((self.home / '.local').exists())


@unittest.skipUnless(os.name == 'nt', 'install.ps1 is exercised natively on Windows')
class PowerShellInstaller(InstallerFixture):
    def setUp(self):
        super().setUp()
        self.program = self.base / 'program'
        self.binary = self.base / 'bin'
        self.pwsh = shutil.which('pwsh') or shutil.which('powershell')
        if not self.pwsh:
            self.skipTest('PowerShell is unavailable')

    def install(self, *, default_repository=False, **extra):
        env = dict(
            os.environ,
            MASK_HOME=str(self.base / 'machine'),
            MASK_INSTALL_DIR=str(self.program),
            MASK_BIN_DIR=str(self.binary),
            MASK_REPO=str(self.remote),
            MASK_PYTHON=sys.executable,
            PYTHONDONTWRITEBYTECODE='1',
            GIT_TERMINAL_PROMPT='0')
        if default_repository:
            env.pop('MASK_REPO')
        env.pop('MASK_CLONE_WITH_GH', None)
        env.update(extra)
        script = (ROOT / 'install.ps1').read_text(encoding='utf-8')
        return subprocess.run(
            [self.pwsh, '-NoProfile', '-NonInteractive', '-Command',
             '& ([scriptblock]::Create([Console]::In.ReadToEnd()))'],
            input=script, capture_output=True, encoding='utf-8', env=env,
            cwd=str(self.base), timeout=120)

    def gh_shim(self):
        binary = self.base / 'shim'
        binary.mkdir()
        log = self.base / 'gh.log'
        (binary / 'gh.cmd').write_text(
            '@echo off\r\n'
            'if not "%1"=="repo" exit /b 91\r\n'
            'if not "%2"=="clone" exit /b 92\r\n'
            'echo %* > "%MASK_TEST_GH_LOG%"\r\n'
            'git clone --quiet "%MASK_TEST_REMOTE%" "%4"\r\n',
            encoding='utf-8', newline='')
        return binary, log

    def test_installs_then_updates_in_the_current_powershell(self):
        first = self.install()
        self.assertEqual(first.returncode, 0, first.stderr)
        launcher = self.binary / 'mask.cmd'
        self.assertTrue((self.program / 'mask.py').is_file())
        self.assertTrue(launcher.is_file())
        self.assertIn(str(self.program / 'mask.py'), launcher.read_text(encoding='utf-8'))
        self.assertRegex(first.stdout, r'Installed mask \S+ \([0-9a-f]+\)')
        self.assertIn(f'{launcher} tap agentskills', first.stdout)
        version = subprocess.run(
            ['cmd.exe', '/d', '/c', str(launcher), '--version'],
            capture_output=True, encoding='utf-8', env=os.environ)
        self.assertEqual((version.returncode, version.stdout.startswith('mask ')), (0, True), version.stderr)

        self.publish()
        again = self.install(PATH=str(self.binary) + os.pathsep + os.environ['PATH'])
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn('Updating MASK', again.stdout)
        self.assertRegex(again.stdout, r'Updated mask \S+ \([0-9a-f]+ -> [0-9a-f]+\)')
        self.assertEqual(self.git(self.program, 'rev-parse', 'HEAD'), self.git(self.author, 'rev-parse', 'HEAD'))

    def test_explicit_authenticated_gh_clone(self):
        binary, log = self.gh_shim()
        installed = self.install(
            default_repository=True,
            MASK_CLONE_WITH_GH='1',
            PATH=str(binary) + os.pathsep + os.environ['PATH'],
            MASK_TEST_REMOTE=str(self.remote),
            MASK_TEST_GH_LOG=str(log))
        self.assertEqual(installed.returncode, 0, installed.stderr)
        self.assertTrue((self.program / 'mask.py').is_file())
        self.assertIn('repo clone MikeMarcin/ManageAgentSkills', log.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
