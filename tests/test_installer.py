"""The one-line installer (install.sh) against a disposable local program repository.

The script is run as a user would pipe it, from stdin, with only its documented environment overrides; it never
reaches the network and never touches this checkout or the developer's home.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipIf(os.name == 'nt', 'install.sh is the POSIX installer; install.ps1 is the Windows one')
class ShellInstaller(unittest.TestCase):
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

    def install(self, **extra):
        env = dict(os.environ, HOME=str(self.home), MASK_HOME=str(self.base / 'machine'), MASK_REPO=str(self.remote), MASK_PYTHON=sys.executable,
                   PYTHONDONTWRITEBYTECODE='1', GIT_TERMINAL_PROMPT='0')
        for name in ('XDG_DATA_HOME', 'MASK_INSTALL_DIR', 'MASK_BIN_DIR'):
            env.pop(name, None)
        env.update(extra)
        with (ROOT / 'install.sh').open(encoding='utf-8') as script:  # As piped: `curl ... | sh`.
            return subprocess.run(['sh'], stdin=script, capture_output=True, encoding='utf-8', env=env, cwd=str(self.base), timeout=120)

    def test_installs_then_updates_in_place_and_preserves_what_it_does_not_own(self):
        first = self.install()
        self.assertEqual(first.returncode, 0, first.stderr)
        program, launcher = self.home / '.local/share/mask', self.home / '.local/bin/mask'
        self.assertTrue((program / 'mask.py').is_file())
        self.assertIn(str(program / 'mask.py'), launcher.read_text(encoding='utf-8'))
        self.assertIn('is not on your PATH', first.stdout)
        self.assertIn(f'{launcher} tap add agentskills', first.stdout)
        version = subprocess.run([str(launcher), '--version'], capture_output=True, encoding='utf-8', env=dict(os.environ, HOME=str(self.home)))
        self.assertEqual((version.returncode, version.stdout.startswith('mask ')), (0, True), version.stderr)
        # Running it again fast-forwards the same clone to what was published since.
        with (self.author / 'mask.py').open('a', encoding='utf-8') as handle:
            handle.write('\n# published later\n')
        self.git(self.author, 'commit', '-q', '-a', '-m', 'later')
        self.git(self.author, 'push', '-q', str(self.remote), 'main')
        again = self.install(PATH=str(launcher.parent) + os.pathsep + os.environ['PATH'])
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn('Updating MASK', again.stdout)
        self.assertNotIn('is not on your PATH', again.stdout)
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), self.git(self.author, 'rev-parse', 'HEAD'))

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


if __name__ == '__main__':
    unittest.main()
