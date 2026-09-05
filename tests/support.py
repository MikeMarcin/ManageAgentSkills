import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ENTRY = Path(__file__).resolve().parents[1] / 'mask.py'


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mask-fixture-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.home = self.base / 'machine'
        self.source = self.base / 'AgentSkills'
        self.source.mkdir()
        self.git(self.source, 'init', '-b', 'main')
        self.git(self.source, 'config', 'user.name', 'Fixture')
        self.git(self.source, 'config', 'user.email', 'fixture@example.invalid')
        self.add_skill('alpha')
        self.add_skill('beta')
        self.git(self.source, 'add', 'skills')
        self.git(self.source, 'commit', '-m', 'initial skills')
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

    def call(self, *args, code=0, cwd=None, env=None):
        environment = dict(os.environ, MASK_HOME=str(self.home), PYTHONDONTWRITEBYTECODE='1')
        if env:
            environment.update(env)
        run = subprocess.run([sys.executable, str(ENTRY), *map(str, args), '--json'], capture_output=True, encoding="utf-8", cwd=cwd or self.project, env=environment)
        data = json.loads(run.stdout)
        self.assertEqual(run.returncode, code, (run.stdout, run.stderr))
        self.assertEqual(run.stderr, '')
        self.assertEqual(data['ok'], code == 0)
        return data

    def init(self):
        return self.call('init', '--source', self.source)

    def declare(self, skills=None, targets=None):
        data = dict(schema_version=1, skills=['alpha'] if skills is None else skills)
        if targets is not None:
            data['targets'] = targets
        (self.project / '.mask.json').write_text(json.dumps(data) + '\n')

    def snapshot(self, root=None):
        root = root or self.base
        return {str(p.relative_to(root)): ('link', os.readlink(p)) if p.is_symlink() else ('file', p.read_bytes()) if p.is_file() else ('directory',) for p in root.rglob('*') if '.git' not in p.parts}
