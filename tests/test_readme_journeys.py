"""README recipes replayed verbatim through the public CLI (RFC-MASK-0021 AC06; MASK-0105; case D02).

``ReadmeText`` pins the replayed strings to README.md: it fails when a fenced command block or an Everyday command
changes and this file does not follow. ``ReadmeRecipes`` runs exactly those strings on a fresh machine, with no
``--json``, no plan hash and no preparation. ``shell`` splits each line with POSIX shell quoting and makes only these
substitutions:

- ``python3`` is this test's interpreter.
- The ManageAgentSkills GitHub URL is a local bare remote holding this working tree's runtime, so
  ``ManageAgentSkills/mask.py`` is the entrypoint of the disposable clone the README's ``git clone`` makes. Every
  later command runs that clone, and ``mask update`` updates it, never this repository's checkout.
- The AgentSkills GitHub URL is the fixture's local bare tap upstream.
- ``$HOME`` is the fixture's personal home, and ``mkdir -p`` is ``Path.mkdir`` (native Windows has no such executable).
- ``mask`` and ``"$HOME/.local/bin/mask"`` are the launcher ``self install`` wrote (``mask.cmd`` on Windows).
- The Everyday placeholders ``ID`` and ``TAP/BUNDLE`` are a fixture skill and a fixture bundle.

Prompts are exercised on a POSIX pseudoterminal, which is the macOS lane's terminal boundary; it is not native
Windows qualification.
"""
import json
import os
from pathlib import Path
import re
import select
import shlex
import shutil
import signal
import subprocess
import sys
import time
import unittest

try:
    import pty
except ImportError:  # Windows: prompts are exercised through a recorded native console interaction instead.
    pty = None

from tests.public_support import ENTRY, PublicFixture
from tests.support import TAP

README = ENTRY.parent / 'README.md'
PROGRAM_URL = 'git@github.com:MikeMarcin/ManageAgentSkills.git'
TAP_URL = 'https://github.com/MikeMarcin/AgentSkills.git'
INSTALL_ONCE = (f'git clone {PROGRAM_URL}',
                'mkdir -p "$HOME/.local/bin"',
                'python3 ManageAgentSkills/mask.py self install --bin-dir "$HOME/.local/bin"',
                f'"$HOME/.local/bin/mask" tap agentskills {TAP_URL}')
# The piped installer is proven against a local program repository in tests.test_installer; this module replays the by-hand recipe.
INSTALLER = ('gh api repos/MikeMarcin/ManageAgentSkills/contents/install.sh \\',
             "  -H 'Accept: application/vnd.github.raw+json' | sh")
WINDOWS_INSTALLER = ('$install = gh api repos/MikeMarcin/ManageAgentSkills/contents/install.ps1 -H \'Accept: application/vnd.github.raw+json\'',
                     "if ($LASTEXITCODE -ne 0) { throw 'Could not download the MASK installer.' }",
                     'Invoke-Expression ($install -join "`n")')
IN_YOUR_PROJECT = ('mask install implement-rfc', 'mask list', 'mask upgrade')
MAKE_EVERYTHING_WORK = ('mask upgrade --all',)
EVERYDAY = {
    'Add a skill here': 'mask install ID',
    'Add a personal skill': 'mask install ID --user',
    'Remove a skill here': 'mask uninstall ID',
    "Show this checkout's skills": 'mask list',
    'Show personal skills': 'mask list --user',
    "Inspect this checkout's readiness": 'mask status',
    'Inspect a named bundle': 'mask bundle show TAP/BUNDLE',
    'Install a named bundle here': 'mask bundle install TAP/BUNDLE',
    'Review bundle membership and member versions': 'mask bundle upgrade TAP/BUNDLE --dry-run',
    'Uninstall a bundle contribution here': 'mask bundle uninstall TAP/BUNDLE',
    'Update MASK itself and fetch your taps': 'mask update',
    'Upgrade this checkout': 'mask upgrade',
    'Upgrade and commit changed project controls': 'mask upgrade --commit',
    'Upgrade personal skills': 'mask upgrade --user',
    'Upgrade every registered checkout and personal skills': 'mask upgrade --all',
    'Hold a skill at its installed version': 'mask pin ID',
    'Release a version hold': 'mask unpin ID',
    'Register and prepare this checkout': 'mask register',
    'Restore pinned setup, or review an interrupted setup': 'mask repair',
    'Preview unused storage and backups': 'mask cleanup --dry-run',
}

FENCE = re.compile(r'^```[^\n]*\n(.*?)^```$', re.M | re.S)


def sections(text):
    """README text by ``## `` heading; the text before the first heading is keyed ``''``."""
    parts = re.split(r'^## (.+)$', text, flags=re.M)
    return dict(zip(['', *parts[1::2]], parts[0::2]))


class ReadmeText(unittest.TestCase):
    def test_replayed_text_is_the_readme_text(self):
        found = sections(README.read_text(encoding='utf-8'))
        blocks = {name: [tuple(block.splitlines()) for block in FENCE.findall(body)] for name, body in found.items()}
        self.assertEqual({name: rows for name, rows in blocks.items() if rows},
                         {'Install once': [INSTALLER, WINDOWS_INSTALLER, INSTALL_ONCE], 'In your project': [IN_YOUR_PROJECT], 'Make everything work': [MAKE_EVERYTHING_WORK]})
        table = [[cell.strip() for cell in line.strip('|').split('|')] for line in found['Everyday commands'].splitlines() if line.startswith('|')]
        self.assertEqual(table, [['Task', 'Command'], ['---', '---'], *([task, f'`{command}`'] for task, command in EVERYDAY.items())])


class ReadmeRecipes(PublicFixture):
    """README "Install once" on a fresh machine, then each later recipe exactly as written."""

    def bootstrap(self):
        """Nothing: setUp replays "Install once", whose ``tap add`` is the first command that creates machine config."""

    def setUp(self):
        super().setUp()
        self.program_author, self.program_remote = self.program_repository()
        self.program = self.base / 'ManageAgentSkills'
        self.launcher = self.personal / '.local/bin' / ('mask.cmd' if os.name == 'nt' else 'mask')
        self.assertFalse((self.home / 'config.json').exists())
        for line in INSTALL_ONCE:
            run = self.shell(line, cwd=self.base)  # "From the directory that will hold the clone".
            self.assertEqual(run.returncode, 0, f'{line}\n{run.stdout}{run.stderr}')
            self.assertFalse(self.parses_as_result_envelope(run.stdout))
        self.assertIn(str(self.program / 'mask.py'), self.launcher.read_text(encoding='utf-8'))

    def program_repository(self):
        """A local bare ``ManageAgentSkills.git`` holding this working tree's runtime, and the author clone that publishes to it."""
        author = self.base / 'program author'
        author.mkdir()
        for module in ENTRY.parent.glob('mask*.py'):
            shutil.copyfile(module, author / module.name)
        shutil.copytree(ENTRY.parent / 'schemas', author / 'schemas')
        self.git(author, 'init', '-b', 'main')
        self.git(author, 'config', 'user.name', 'Fixture')
        self.git(author, 'config', 'user.email', 'fixture@example.invalid')
        self.git(author, 'add', '.')
        self.git(author, 'commit', '-q', '-m', 'program')
        remote = self.base / 'program remote' / 'ManageAgentSkills.git'  # update requires this repository name.
        remote.parent.mkdir()
        self.git(self.base, 'init', '-q', '--bare', '-b', 'main', str(remote))
        self.git(author, 'push', '-q', str(remote), 'main')
        return author, remote

    def argv(self, line, **placeholders):
        """The README line split as POSIX sh would, with only the substitutions the module docstring names."""
        command, *words = shlex.split(line)
        self.assertIn(command, ('git', 'mkdir', 'python3', 'mask', '$HOME/.local/bin/mask'), line)
        program = {'python3': sys.executable, 'mask': str(self.launcher), '$HOME/.local/bin/mask': str(self.launcher)}.get(command, command)
        urls = {PROGRAM_URL: str(self.program_remote), TAP_URL: str(self.upstream)}
        return [program, *(urls.get(word, placeholders.get(word, word)).replace('$HOME', str(self.personal)) for word in words)]

    def shell(self, line, cwd=None, **placeholders):
        """Run one README line from the project (or ``cwd``) with stdin closed, as a pipeline would."""
        argv = self.argv(line, **placeholders)
        self.assertNotIn('--json', argv)
        cwd = cwd or self.project
        if argv[:2] == ['mkdir', '-p']:
            for directory in argv[2:]:
                (cwd / directory).mkdir(parents=True, exist_ok=True)
            return subprocess.CompletedProcess(argv, 0, '', '')
        return subprocess.run(argv, capture_output=True, encoding='utf-8', cwd=str(cwd), env=self.environment(),
                              stdin=subprocess.DEVNULL, timeout=60)

    def terminal(self, line, *, answer):
        master, slave = pty.openpty()
        process = subprocess.Popen(self.argv(line), stdin=slave, stdout=slave, stderr=slave, cwd=str(self.project),
                                   env=self.environment(), close_fds=True)
        os.close(slave)
        transcript = b''
        answered = False
        deadline = time.monotonic() + 60
        try:
            while time.monotonic() < deadline:
                ready, _, _ = select.select([master], [], [], 0.2)
                if ready:
                    try:
                        chunk = os.read(master, 4096)
                    except OSError:
                        break
                    if not chunk:
                        break
                    transcript += chunk
                if not answered and b'[y/N]' in transcript:
                    answered = True
                    os.write(master, answer)
                if process.poll() is not None and not ready:
                    break
            process.wait(timeout=10)
        finally:
            if process.poll() is None:
                process.send_signal(signal.SIGKILL)
                process.wait()
            os.close(master)
        self.assertTrue(answered, transcript.decode('utf-8', 'replace'))
        return process.returncode, transcript.decode('utf-8', 'replace')

    def links(self, root):
        return sorted(path.relative_to(root).as_posix() for path in root.glob('.*/skills/*') if path.is_symlink())

    @staticmethod
    def unlink(link):
        os.rmdir(link) if os.name == 'nt' else link.unlink()  # A Windows directory symlink is removed as a directory.

    @staticmethod
    def locked(path):
        return json.loads(path.read_text(encoding='utf-8'))['packages'][0]['commit']

    def test_install_once_then_in_your_project(self):
        from tests.public_support import CONSUMER_CONTEXT
        shutil.copytree(CONSUMER_CONTEXT, self.project / '.mask')
        for command in IN_YOUR_PROJECT + MAKE_EVERYTHING_WORK:
            run = self.shell(command)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(self.links(self.project), ['.agents/skills/implement-rfc', '.claude/skills/implement-rfc'])
        self.assertTrue((self.project / '.codex/agents/rfc-integrator.toml').is_file())
        self.assertTrue((self.project / '.mask.lock.json').is_file())

    def test_missing_input_preserves_fresh_checkout(self):
        installed = self.shell(IN_YOUR_PROJECT[0])
        self.assertEqual(installed.returncode, 4, installed.stdout + installed.stderr)
        self.assertIn('workflow.incomplete', installed.stderr)
        self.assertFalse((self.project / '.mask.json').exists())
        self.assertEqual(self.links(self.project), [])

    def test_ordinary_repair_needs_no_confirmation(self):
        self.assertEqual(self.shell(EVERYDAY['Add a skill here'], ID='alpha').returncode, 0)
        self.unlink(self.project / '.claude/skills/alpha')
        repaired = self.shell(EVERYDAY['Restore pinned setup, or review an interrupted setup'])
        self.assertEqual(repaired.returncode, 0, repaired.stderr)
        self.assertNotIn('[y/N]', repaired.stdout + repaired.stderr)
        self.assertEqual(self.links(self.project), ['.agents/skills/alpha', '.claude/skills/alpha'])

    def test_everyday_commands(self):
        replayed = set()

        def run(task, **placeholders):
            replayed.add(task)
            result = self.shell(EVERYDAY[task], **placeholders)
            self.assertEqual(result.returncode, 0, f'{EVERYDAY[task]}\n{result.stdout}{result.stderr}')
            self.assertFalse(self.parses_as_result_envelope(result.stdout))
            return result

        def push_upstream(text):
            path = self.source / 'skills/alpha/SKILL.md'
            path.write_text(path.read_text(encoding='utf-8') + text + '\n', encoding='utf-8', newline='\n')
            return self.publish(text)

        alpha = ['.agents/skills/alpha', '.claude/skills/alpha']
        run('Add a skill here', ID='alpha')
        run('Add a personal skill', ID='alpha')
        run('Add a skill here', ID='beta')
        self.assertEqual(self.links(self.project), sorted(alpha + ['.agents/skills/beta', '.claude/skills/beta']))
        self.assertEqual(self.links(self.personal), alpha)
        self.assertIn('beta', run("Show this checkout's skills").stdout)
        self.assertIn('alpha', run('Show personal skills').stdout)
        self.assertIn(f'- {TAP}/beta', run('Remove a skill here', ID='beta').stdout)
        self.assertEqual(self.links(self.project), alpha)
        run('Restore pinned setup, or review an interrupted setup')

        for root in (self.project, self.personal):
            self.unlink(root / '.claude/skills/alpha')
        self.assertEqual(self.shell('mask repair --all').returncode, 0)
        self.assertEqual((self.links(self.project), self.links(self.personal)), (alpha, alpha))

        # The README names the tap's rfc bundle; the fixture tap publishes one over alpha and beta.
        index = dict(schema_version=1, packages={name: 'skills/' + name for name in ('alpha', 'beta', 'implement-rfc')},
                     bundles={'rfc': dict(description='Fixture bundle', skills=[dict(source=TAP, id='alpha'), dict(source=TAP, id='beta')])})
        (self.source / 'mask-source.json').write_text(json.dumps(index, indent=2) + '\n', encoding='utf-8', newline='\n')
        self.git(self.source, 'add', 'mask-source.json')
        self.publish('rfc bundle')
        self.assertEqual(self.shell(f'mask tap fetch {TAP}').returncode, 0)
        bundle = {'TAP/BUNDLE': f'{TAP}/rfc'}
        self.assertIn(f'{TAP}/beta', run('Inspect a named bundle', **bundle).stdout)
        run('Install a named bundle here', **bundle)
        self.assertEqual(self.links(self.project), sorted(alpha + ['.agents/skills/beta', '.claude/skills/beta']))
        run('Review bundle membership and member versions', **bundle)
        run('Uninstall a bundle contribution here', **bundle)
        self.assertEqual(self.links(self.project), alpha, 'alpha was installed by hand, so it stays')

        # Each update scope moves only its own lock to the fetched upstream commit.
        project_lock, user_lock = self.project / '.mask.lock.json', self.home / 'user.lock.json'
        installed = self.locked(user_lock)
        first = push_upstream('First upstream change.')
        run('Upgrade this checkout')
        self.assertEqual((self.locked(project_lock), self.locked(user_lock)), (first, installed))
        run('Upgrade personal skills')
        self.assertEqual(self.locked(user_lock), first)
        self.git(self.project, 'config', 'user.name', 'Fixture')
        self.git(self.project, 'config', 'user.email', 'fixture@example.invalid')
        self.git(self.project, 'commit', '-q', '--allow-empty', '-m', 'start')  # --commit needs a branch with a commit.
        committed = push_upstream('Committed upstream change.')
        run('Upgrade and commit changed project controls')
        self.assertEqual(self.locked(project_lock), committed)
        self.assertEqual(self.git(self.project, 'status', '--porcelain', '--', '.mask.json', '.mask.lock.json'), '')
        second = push_upstream('Second upstream change.')
        self.assertIn(f'tap {TAP}: fetched new commits', run('Upgrade every registered checkout and personal skills').stdout)
        self.assertEqual((self.locked(project_lock), self.locked(user_lock)), (second, second))
        self.assertIn('Second upstream change.', (self.personal / '.claude/skills/alpha/SKILL.md').read_text(encoding='utf-8'))

        # "Update MASK itself and fetch your taps" fast-forwards the disposable program clone to a published compatible change.
        with (self.program_author / 'mask.py').open('a', encoding='utf-8') as handle:
            handle.write('\n# compatible fixture update\n')
        self.git(self.program_author, 'commit', '-q', '-a', '-m', 'compatible fixture update')
        self.git(self.program_author, 'push', '-q', str(self.program_remote), 'main')
        # The same command fetches the taps, as brew update does, and moves no consumer: upgrade does that.
        third = push_upstream('Third upstream change.')
        refreshed = run('Update MASK itself and fetch your taps').stdout
        self.assertEqual(self.git(self.program, 'rev-parse', 'HEAD'), self.git(self.program_author, 'rev-parse', 'HEAD'))
        self.assertIn('MASK updated: ', refreshed)
        self.assertIn(f'tap {TAP}: fetched new commits', refreshed)
        self.assertIn("Run 'mask upgrade'", refreshed)
        self.assertEqual((self.locked(project_lock), self.locked(user_lock)), (second, second))
        self.assertEqual(self.shell('mask upgrade --all --offline').returncode, 0)
        self.assertEqual((self.locked(project_lock), self.locked(user_lock)), (third, third))

        run('Register and prepare this checkout')
        run('Hold a skill at its installed version', ID='alpha')
        run('Release a version hold', ID='alpha')
        run("Inspect this checkout's readiness")
        run('Preview unused storage and backups')
        self.assertEqual(replayed, set(EVERYDAY))


if __name__ == '__main__':
    unittest.main()
