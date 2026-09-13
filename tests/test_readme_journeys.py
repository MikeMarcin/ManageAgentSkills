"""README recipes replayed as written (RFC-MASK-0018 AC07/AC08, MASK-0091; case C21).

Each command below is the README's everyday command, run through the launcher that
``self install`` wrote or through the plain entrypoint, with no ``--json``, no
plan hash and no preparation beyond the one-time source selection. Prompts are
exercised on a POSIX pseudoterminal, which is the macOS lane's terminal boundary;
it is not native Windows qualification.
"""
import os
import select
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
from tests.test_update_task import TapUpdateFixture


class ReadmeRecipes(PublicFixture):
    """The README from "Install once" to "Everyday commands" on a fresh machine."""

    def bootstrap(self):
        """Nothing: README runs ``self install`` before the one-time ``tap add``, which each journey replays itself."""

    def select_source(self):
        """README "Install once": approve the skills upstream as a tap; the first command that creates machine config."""
        self.assertFalse((self.home / 'config.json').exists())
        return self.mask('tap', 'add', TAP, self.upstream)

    def setUp(self):
        super().setUp()
        self.bin = self.personal / '.local/bin'  # README: mkdir -p "$HOME/.local/bin" precedes self install on a fresh home.
        self.bin.mkdir(parents=True)
        installed = self.human('self', 'install', '--bin-dir', self.bin)
        self.assertEqual(installed.returncode, 0, installed.stderr)
        self.launcher = self.bin / ('mask.cmd' if os.name == 'nt' else 'mask')
        self.assertTrue(self.launcher.exists(), installed.stdout)

    def mask(self, *args, cwd=None, stdin=subprocess.DEVNULL):
        """``mask ...`` exactly as the README shows it, through the installed launcher."""
        self.assertNotIn('--json', args)
        return subprocess.run([str(self.launcher), *map(str, args)], capture_output=True, encoding='utf-8',
                              cwd=str(cwd or self.project), env=self.environment(), stdin=stdin, timeout=60)

    def terminal(self, *args, answer, cwd=None):
        master, slave = pty.openpty()
        process = subprocess.Popen([str(self.launcher), *map(str, args)], stdin=slave, stdout=slave, stderr=slave,
                                   cwd=str(cwd or self.project), env=self.environment(), close_fds=True)
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

    def test_install_once_then_in_your_project(self):
        # README: `mask tap add agentskills https://github.com/MikeMarcin/AgentSkills.git`, with the fixture's local bare upstream for the URL.
        selected = self.select_source()
        self.assertEqual(selected.returncode, 0, selected.stderr)
        self.assertFalse(self.parses_as_result_envelope(selected.stdout))
        self.assertTrue((self.home / 'config.json').is_file())

        # The package declares consumer inputs this fresh project does not have yet: the links and
        # static roles are committed, but install cannot report success (MASK-0090); it names them.
        installed = self.mask('install', 'implement-rfc')
        self.assertEqual(installed.returncode, 4, installed.stdout + installed.stderr)
        self.assertIn('workflow.incomplete', installed.stderr)
        self.assertIn('.mask/skill-config/implement-rfc/project.json', installed.stderr)
        self.assertIn('deployment changes were saved', installed.stderr)
        self.assertIn('mask ensure', installed.stderr)
        self.assertEqual(installed.stdout, '')
        self.assertEqual(self.links(self.project), ['.agents/skills/implement-rfc', '.claude/skills/implement-rfc'])
        self.assertTrue((self.project / '.codex/agents/rfc-integrator.toml').is_file())
        self.assertTrue((self.project / '.claude/agents/rfc-integrator.md').is_file())

        listed = self.mask('list')
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertFalse(self.parses_as_result_envelope(listed.stdout))
        self.assertIn('implement-rfc', listed.stdout)
        self.assertIn('linked', listed.stdout)

        # ensure shares the same verdict: it names the inputs and stops; no package code runs and nothing is overwritten.
        ensured = self.mask('ensure')
        self.assertEqual(ensured.returncode, 4, ensured.stdout + ensured.stderr)
        self.assertIn('workflow.incomplete', ensured.stderr)
        self.assertIn('.mask/skill-config/implement-rfc/project.json', ensured.stderr)
        self.assertEqual(ensured.stdout, '')

    @unittest.skipUnless(pty, 'POSIX pseudoterminal required; native Windows console is recorded separately')
    def test_ensure_asks_once_in_the_terminal_and_completes(self):
        self.assertEqual(self.select_source().returncode, 0)
        installed = self.mask('install', 'alpha')
        self.assertEqual(installed.returncode, 0, installed.stderr)
        (self.project / '.claude/skills/alpha').unlink()  # Something to reconcile.
        code, text = self.terminal('ensure', answer=b'y\n')
        self.assertEqual(code, 0, text)
        self.assertIn('[y/N]', text)
        self.assertNotIn('sha256:', text)
        self.assertEqual(self.links(self.project), ['.agents/skills/alpha', '.claude/skills/alpha'])
        # Declining leaves the explicit incomplete result the README promises.
        (self.project / '.claude/skills/alpha').unlink()
        code, text = self.terminal('ensure', answer=b'n\n')
        self.assertEqual(code, 4, text)
        self.assertIn('confirmation.declined', text)
        self.assertEqual(self.links(self.project), ['.agents/skills/alpha'])
        # The same command through a pipe never asks.
        piped = self.mask('ensure')
        self.assertEqual(piped.returncode, 4, piped.stderr)
        self.assertIn('confirmation.required', piped.stderr)

    def test_personal_scope_and_remove(self):
        self.assertEqual(self.select_source().returncode, 0)
        personal = self.mask('install', 'alpha', '--user')
        self.assertEqual(personal.returncode, 0, personal.stderr)
        self.assertEqual(self.links(self.personal), ['.agents/skills/alpha', '.claude/skills/alpha'])
        self.assertFalse((self.project / '.mask.json').exists())

        listed = self.mask('list', '--user')
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertIn('alpha', listed.stdout)

        installed = self.mask('install', 'alpha', 'beta')
        self.assertEqual(installed.returncode, 0, installed.stderr)
        removed = self.mask('remove', 'beta')
        self.assertEqual(removed.returncode, 0, removed.stderr)
        self.assertIn(f'removed: {TAP}/beta', removed.stdout)
        self.assertEqual(self.links(self.project), ['.agents/skills/alpha', '.claude/skills/alpha'])
        self.assertEqual(self.links(self.personal), ['.agents/skills/alpha', '.claude/skills/alpha'])


class ReadmeUpdate(TapUpdateFixture):
    """``mask update`` and ``mask update --dry-run`` as the README describes them, on the fixture tap."""

    def test_update_previews_locally_and_applies_in_one_command(self):
        cache, lock = self.cached(), (self.project / '.mask.lock.json').read_bytes()
        candidate = self.push_upstream()
        preview = self.human('update', '--dry-run')
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertFalse(self.parses_as_result_envelope(preview.stdout))
        self.assertNotIn('sha256:', preview.stdout)
        self.assertEqual((self.cached(), (self.project / '.mask.lock.json').read_bytes()), (cache, lock))  # Preview did not fetch.
        applied = self.human('update')
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertFalse(self.parses_as_result_envelope(applied.stdout))
        self.assertNotIn('sha256:', applied.stdout)
        self.assertEqual(self.locked(), candidate)
        again = self.human('update')
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn('no change needed', again.stdout)
        self.assertEqual(self.locked(), candidate)


if __name__ == '__main__':
    unittest.main()
