"""Automatic refresh runs only against disposable program clones and local taps."""
import json
import subprocess
import sys

from tests.public_support import PublicFixture, ENTRY
from tests import test_launcher as launcher_fixtures


class RefreshV2(PublicFixture):
    def setUp(self):
        super().setUp()
        self.program_root, self.program_author = launcher_fixtures.LauncherTests.program_checkout(self)

    def command(self, *args):
        wrong_home = self.base / 'wrong-machine-home'
        run = subprocess.run([sys.executable, '-B', str(self.program_root / 'mask.py'), *map(str, args),
                              '--home', str(self.home), '--json'], cwd=self.project,
                             env=self.environment({'MASK_HOME': str(wrong_home)}), capture_output=True, encoding='utf-8', timeout=60)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(run.stderr, '')
        self.assertFalse(wrong_home.exists(), 'explicit --home must also govern automatic refresh')
        return json.loads(run.stdout)

    def advance(self, text):
        """Publish a real package change: an unchanged package keeps its lock across commits (MASK-0125)."""
        path = self.source / 'skills/alpha/SKILL.md'
        path.write_text(path.read_text(encoding='utf-8') + text + '\n', encoding='utf-8', newline='\n')
        return self.publish(text)

    def publish_program(self):
        path = self.program_author / 'mask.py'
        old = path.read_text()
        self.assertIn("VERSION = '0.3.0'", old)
        path.write_text(old.replace("VERSION = '0.3.0'", "VERSION = '0.3.1-fixture'"))
        self.git(self.program_author, 'add', 'mask.py')
        self.git(self.program_author, 'commit', '-m', 'fixture version')
        self.git(self.program_author, 'push', 'origin', 'main')
        return self.git(self.program_author, 'rev-parse', 'HEAD')

    def locked(self):
        return json.loads((self.project / '.mask.lock.json').read_text(encoding='utf-8'))['packages'][0]['commit']

    def test_program_update_reexecutes_before_install(self):
        commit = self.publish_program()
        result = self.command('install', 'alpha')
        self.assertEqual(result['tool_version'], '0.3.1-fixture')
        self.assertEqual(self.git(self.program_root, 'rev-parse', 'HEAD'), commit)
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())
        self.assertTrue((self.home / 'refresh.json').is_file())

    def test_freshness_no_update_offline_and_reviewed_application(self):
        first = self.command('install', 'alpha')
        self.assertIn('refresh', first['data'])
        program_before = self.git(self.program_root, 'rev-parse', 'HEAD')
        self.publish_program()
        newer = self.advance('next package revision')
        fresh = self.command('upgrade')
        self.assertNotIn('refresh', fresh['data'])
        self.assertTrue(fresh['data']['fetches']['agentskills']['attempted'])
        self.assertEqual(self.locked(), newer)
        self.assertEqual(self.git(self.program_root, 'rev-parse', 'HEAD'), program_before)
        (self.home / 'refresh.json').unlink()
        newer = self.advance('another package revision')
        self.command('upgrade', '--no-update')
        self.assertEqual(self.locked(), newer)
        self.assertFalse((self.home / 'refresh.json').exists())
        self.advance('not fetched')
        offline = self.command('upgrade', '--offline')
        self.assertEqual(offline['data']['network'], 'none')
        self.assertEqual(self.locked(), newer)
        preview = self.command('upgrade', '--dry-run')
        self.command('upgrade', '--approve-plan', preview['data']['plan_hash'])
        self.assertEqual(self.locked(), newer)
        self.assertFalse((self.home / 'refresh.json').exists())
        self.assertEqual(self.git(self.program_root, 'rev-parse', 'HEAD'), program_before)
