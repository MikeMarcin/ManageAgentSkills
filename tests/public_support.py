"""Public-journey fixtures for the corrective UX and readiness RFCs.

Unlike ``tests.support.Fixture.call``, nothing here appends ``--json``. Three
helpers are kept separate on purpose: ``raw`` returns the completed process,
``machine`` requests the JSON protocol explicitly, and ``human`` is the plain
terminal invocation whose output is the thing under test. Starting states are
prepared only up to the one-time source prerequisite, which is ``tap add`` of a
local bare upstream on an empty MASK_HOME (RFC-MASK-0021); no helper registers a
consumer, approves readiness, renders roles or applies a change on behalf of the
command under test.
"""
import json
import os
from pathlib import Path
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

from tests.support import TAP

ENTRY = Path(__file__).resolve().parents[1] / 'mask.py'
PACK = Path(__file__).resolve().parents[1] / 'docs/rfcs/assets/mask-corrective-ux-readiness'
STATIC_PACKAGE = PACK / 'fixtures/static-package'
CONSUMER_CONTEXT = PACK / 'fixtures/consumer/.mask'
MISSING_ROLE = 'rfc-integrator'
STALE_ROLE = 'rfc-worker'


class PublicFixture(unittest.TestCase):
    """A source with three skills, a private MASK_HOME and no registered consumer."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mask-public-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.home = self.base / 'machine'
        self.personal = self.base / 'personal home'
        self.personal.mkdir()
        self.source = self.base / 'AgentSkills'
        (self.source / 'skills').mkdir(parents=True)
        self.git(self.source, 'init', '-b', 'main')
        self.git(self.source, 'config', 'user.name', 'Fixture')
        self.git(self.source, 'config', 'user.email', 'fixture@example.invalid')
        for name in ('alpha', 'beta'):
            root = self.source / 'skills' / name
            root.mkdir()
            # Explicit LF: the working bytes equal the committed bytes on every host, whatever Git line-ending conversion applies.
            (root / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: Fixture skill\n---\n\nFixture only.\n', encoding='utf-8', newline='\n')
        shutil.copytree(STATIC_PACKAGE, self.source / 'skills/implement-rfc')
        self.git(self.source, 'add', 'skills')
        self.git(self.source, 'commit', '-m', 'fixture skills')
        self.upstream = self.base / 'upstream' / 'AgentSkills.git'
        self.upstream.parent.mkdir()
        self.git(self.base, 'init', '-q', '--bare', '-b', 'main', str(self.upstream))
        self.git(self.source, 'push', '-q', str(self.upstream), 'main')
        self.project = self.base / 'project with ü spaces'
        self.project.mkdir()
        self.git(self.project, 'init', '-b', 'main')
        self.bootstrap()

    def bootstrap(self):
        """The one-time source prerequisite: approve the fixture upstream as a tap on an empty MASK_HOME."""
        self.assertTrue(self.machine('tap', 'add', TAP, self.upstream)['ok'])

    def publish(self, message='fixture change', *, force=False):
        """Commit the author's skill edits and push them to the tap upstream; MASK sees them only after a fetch."""
        self.git(self.source, 'add', '-A', 'skills')
        self.git(self.source, 'commit', '-q', '--allow-empty', '-m', message)
        self.git(self.source, 'push', '-q', *(['--force'] if force else []), str(self.upstream), 'HEAD:main')
        return self.git(self.source, 'rev-parse', 'HEAD')

    def git(self, root, *args):
        return subprocess.run(['git', '-C', str(root), *args], capture_output=True, encoding='utf-8', check=True).stdout.strip()

    def environment(self, extra=None):
        # HOME on POSIX and USERPROFILE on Windows are what Path.home() reads; both point at the fixture's personal home
        # so no test can touch the real profile.
        env = dict(os.environ, MASK_HOME=str(self.home), HOME=str(self.personal), USERPROFILE=str(self.personal),
                   PYTHONDONTWRITEBYTECODE='1', GIT_TERMINAL_PROMPT='0')
        env.pop('MASK_USER_HOME', None)
        if extra:
            env.update(extra)
        return env

    def raw(self, *args, cwd=None, env=None, stdin=subprocess.DEVNULL):
        """Run the CLI exactly as given; nothing is appended."""
        return subprocess.run([sys.executable, '-B', str(ENTRY), *map(str, args)], capture_output=True, encoding='utf-8',
                              cwd=str(cwd or self.project), env=self.environment(env), stdin=stdin, timeout=60)

    def machine(self, *args, **kwargs):
        run = self.raw(*args, '--json', **kwargs)
        data = json.loads(run.stdout)
        self.assertEqual(run.stderr, '', run.stderr)
        self.assertEqual(data['ok'], run.returncode == 0, run.stdout)
        return data

    def human(self, *args, **kwargs):
        """The plain terminal invocation. ``--json`` is never injected here."""
        self.assertNotIn('--json', args)
        return self.raw(*args, **kwargs)

    @staticmethod
    def parses_as_result_envelope(text):
        try:
            data = json.loads(text)
        except ValueError:
            return False
        return isinstance(data, dict) and {'ok', 'schema_version', 'data'} <= set(data)

    def terminal(self, *args, answer=None, before_answer=None, interrupt=False, timeout=60):
        """Run the CLI on a POSIX pseudoterminal and answer each ``[y/N]`` prompt in turn.

        ``answer`` is one reply or a list of replies (bytes); ``before_answer`` runs once,
        before the first reply. Returns the exit code and the transcript.
        """
        import pty
        replies = list(answer) if isinstance(answer, list) else [answer]
        master, slave = pty.openpty()
        process = subprocess.Popen([sys.executable, '-B', str(ENTRY), *map(str, args)], stdin=slave, stdout=slave, stderr=slave,
                                   cwd=str(self.project), env=self.environment(), close_fds=True)
        os.close(slave)
        transcript = b''
        answered = 0
        deadline = time.monotonic() + timeout
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
                if answered < len(replies) and transcript.count(b'[y/N]') > answered:
                    if answered == 0 and before_answer is not None:
                        before_answer()
                    if interrupt:
                        process.send_signal(signal.SIGINT)
                    else:
                        os.write(master, replies[answered])
                    answered += 1
                if process.poll() is not None and not ready:
                    break
            process.wait(timeout=10)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            os.close(master)
        self.assertEqual(answered, len(replies), transcript.decode('utf-8', 'replace'))
        return process.returncode, transcript.decode('utf-8', 'replace')

    def linked_consumer_with_stale_roles(self):
        """Already-linked consumer of implement-rfc whose native roles predate the package.

        This is the SRV-shaped starting state: skill links are correct, the workflow
        context exists, ``rfc-integrator`` is absent and ``rfc-worker`` carries older
        bytes. The old role state is deliberately retained, not repaired.
        """
        shutil.copytree(CONSUMER_CONTEXT, self.project / '.mask')
        self.assertTrue(self.machine('install', 'alpha', 'implement-rfc', '--project', self.project)['ok'])
        self.assertTrue(self.machine('integration', 'approve', '--project', self.project)['ok'])
        # Since MASK-0088 the engine deploys declared static roles with the links; the
        # old-host starting state is then restored by hand: the integrator role is absent
        # and the worker role carries older bytes. Nothing below repairs that state.
        for agent, suffix in (('codex', 'toml'), ('claude', 'md')):
            roles = self.project / f'.{agent}/agents'
            roles.mkdir(parents=True, exist_ok=True)
            for path in roles.glob('*'):
                path.unlink()
            (roles / f'{STALE_ROLE}.{suffix}').write_text(f'# older {STALE_ROLE} definition for {agent}\n', encoding='utf-8')
        for agent in ('codex', 'claude'):
            self.assertTrue((self.project / f'.agents/skills/implement-rfc').is_symlink())
            self.assertFalse(any((self.project / f'.{agent}/agents').glob(MISSING_ROLE + '.*')))
        return self.machine('project', 'list')
