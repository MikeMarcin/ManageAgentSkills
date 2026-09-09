"""Public-journey fixtures for the corrective UX and readiness RFCs.

Unlike ``tests.support.Fixture.call``, nothing here appends ``--json``. Three
helpers are kept separate on purpose: ``raw`` returns the completed process,
``machine`` requests the JSON protocol explicitly, and ``human`` is the plain
terminal invocation whose output is the thing under test. Starting states are
prepared only up to the one-time source prerequisite; no helper registers a
consumer, approves readiness, renders roles or applies a change on behalf of the
command under test.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

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
            (root / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: Fixture skill\n---\n\nFixture only.\n', encoding='utf-8')
        shutil.copytree(STATIC_PACKAGE, self.source / 'skills/implement-rfc')
        self.git(self.source, 'add', 'skills')
        self.git(self.source, 'commit', '-m', 'fixture skills')
        self.project = self.base / 'project with ü spaces'
        self.project.mkdir()
        self.git(self.project, 'init', '-b', 'main')
        self.assertTrue(self.machine('init', '--source', self.source)['ok'])

    def git(self, root, *args):
        return subprocess.run(['git', '-C', str(root), *args], capture_output=True, encoding='utf-8', check=True).stdout.strip()

    def environment(self, extra=None):
        env = dict(os.environ, MASK_HOME=str(self.home), HOME=str(self.personal), PYTHONDONTWRITEBYTECODE='1', GIT_TERMINAL_PROMPT='0')
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

    def linked_consumer_with_stale_roles(self):
        """Already-linked consumer of implement-rfc whose native roles predate the package.

        This is the SRV-shaped starting state: skill links are correct, the workflow
        context exists, ``rfc-integrator`` is absent and ``rfc-worker`` carries older
        bytes. The old role state is deliberately retained, not repaired.
        """
        shutil.copytree(CONSUMER_CONTEXT, self.project / '.mask')
        self.assertTrue(self.machine('project', 'init', '--project', self.project)['ok'])
        self.assertTrue(self.machine('project', 'register', '--project', self.project)['ok'])
        self.assertTrue(self.machine('project', 'require', 'alpha', 'implement-rfc', '--project', self.project, '--apply')['ok'])
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
