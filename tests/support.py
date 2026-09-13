"""Tap-first CLI fixtures (RFC-MASK-0020, MASK-0099).

A machine starts the way a user's does: ``tap add`` on an empty MASK_HOME approves one
local bare repository as a ``file`` tap and creates machine config v3 and state. New
consumers are v2 declarations with locks and links into ``MASK_HOME/store``.
``self.source`` is only the test author's checkout; it reaches MASK solely through
``publish`` and a fetch. Legacy starting states for doctor
migration come from ``tests.legacy_support``.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ENTRY = Path(__file__).resolve().parents[1] / 'mask.py'
TAP = 'agentskills'


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mask-fixture-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.home = self.base / 'machine'
        self.personal = self.base / 'personal home'
        self.personal.mkdir()
        self.source = self.base / 'AgentSkills'
        self.source.mkdir()
        self.git(self.source, 'init', '-b', 'main')
        self.git(self.source, 'config', 'user.name', 'Fixture')
        self.git(self.source, 'config', 'user.email', 'fixture@example.invalid')
        self.add_skill('alpha')
        self.add_skill('beta')
        self.git(self.source, 'add', 'skills')
        self.git(self.source, 'commit', '-m', 'initial skills')
        self.upstream = self.base / 'upstream' / 'AgentSkills.git'
        self.upstream.parent.mkdir()
        self.git(self.base, 'init', '-q', '--bare', '-b', 'main', str(self.upstream))
        self.git(self.source, 'push', '-q', str(self.upstream), 'main')
        self.project = self.base / 'project with ü spaces'
        self.project.mkdir()
        self.git(self.project, 'init', '-b', 'main')

    def git(self, root, *args):
        return subprocess.run(['git', '-C', str(root), *args], capture_output=True, encoding="utf-8", check=True).stdout.strip()

    def add_skill(self, name, description='Fixture skill'):
        root = self.source / 'skills' / name
        root.mkdir(parents=True)
        (root / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: {description}\n---\n\nFixture instructions.\n')
        return root

    def publish(self, message='fixture change', *, force=False):
        """Commit the author's skill edits and push them to the tap upstream; MASK sees them only after a fetch."""
        self.git(self.source, 'add', '-A', 'skills')
        self.git(self.source, 'commit', '-q', '--allow-empty', '-m', message)
        self.git(self.source, 'push', '-q', *(['--force'] if force else []), str(self.upstream), 'HEAD:main')
        return self.git(self.source, 'rev-parse', 'HEAD')

    def environment(self, extra=None):
        # Path.home() reads USERPROFILE on Windows and HOME on POSIX; both name the fixture's personal home.
        environment = dict(os.environ, MASK_HOME=str(self.home), HOME=str(self.personal), USERPROFILE=str(self.personal), PYTHONDONTWRITEBYTECODE='1')
        environment.pop('MASK_USER_HOME', None)
        if extra:
            environment.update(extra)
        return environment

    def call(self, *args, code=0, cwd=None, env=None):
        run = subprocess.run([sys.executable, str(ENTRY), *map(str, args), '--json'], capture_output=True, encoding="utf-8", cwd=cwd or self.project, env=self.environment(env))
        data = json.loads(run.stdout)
        self.assertEqual(run.returncode, code, (run.stdout, run.stderr))
        self.assertEqual(run.stderr, '')
        self.assertEqual(data['ok'], code == 0)
        return data

    def init(self):
        """Bootstrap the machine from one tap: tap add on an empty MASK_HOME creates config v3 and state."""
        return self.call('tap', 'add', TAP, self.upstream)

    def install(self, *ids, root=None, user=False, agents=(), code=0):
        """The public install task for the fixture tap: v2 declaration, lock, registration and store links."""
        scope = ['--user'] if user else ['--project', root or self.project]
        return self.call('install', *ids, *scope, *[item for agent in agents for item in ('--agent', agent)], code=code)

    def binding(self):
        """The v2 declaration source binding of the fixture tap."""
        return {TAP: dict(repository=self.upstream.as_uri(), packages='skills')}

    def declare_pinned(self, skills=('alpha',), root=None, fetch=True):
        """Write a v2 declaration of the fixture tap and lock it from the fetched cache; nothing is registered, hydrated or linked.

        ``fetch`` first fetches the tap when the declaration selects anything; pass ``False`` when the cache is already current.
        """
        root = root or self.project
        declaration = dict(schema_version=2, sources=self.binding() if skills else {}, skills=[dict(source=TAP, id=identifier) for identifier in skills])
        (root / '.mask.json').write_text(json.dumps(declaration) + '\n')
        if fetch and skills:
            self.call('source', 'fetch', TAP)
        return self.call('lock', '--project', root)

    def authoring_init(self):
        """Bootstrap the fixture tap with ``self.source`` as its approved authoring checkout; its origin names the tap identity."""
        self.git(self.source, 'remote', 'add', 'origin', str(self.upstream))
        return self.call('tap', 'add', TAP, self.upstream, '--checkout', self.source)

    def snapshot(self, root=None):
        root = root or self.base
        return {str(p.relative_to(root)): ('link', os.readlink(p)) if p.is_symlink() else ('file', p.read_bytes()) if p.is_file() else ('directory',) for p in root.rglob('*') if '.git' not in p.parts}
