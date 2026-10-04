"""Unchanged package locks survive self-hosted bookkeeping commits (MASK-0125)."""
import json
import os

from tests.public_support import PublicFixture
from tests.support import TAP
from tests import test_cli_v2 as public_cli


class StablePackageLocks(PublicFixture):
    raw = public_cli.CliV2.raw  # Never update the real program checkout.

    def packages(self, root):
        return json.loads((root / '.mask.lock.json').read_text(encoding='utf-8'))['packages']

    def commit_controls(self):
        self.git(self.source, 'add', '.mask.json', '.mask.lock.json')
        self.git(self.source, 'commit', '-m', 'record consumer locks')
        self.git(self.source, 'push', '-q', str(self.upstream), 'HEAD:main')

    def test_self_hosted_lock_commits_converge_and_only_changed_skill_advances(self):
        self.assertTrue(self.machine('install', 'alpha', 'beta', '--project', self.source)['ok'])
        self.commit_controls()
        before = (self.source / '.mask.lock.json').read_bytes()
        first = self.packages(self.source)
        run = self.machine('upgrade', '--all')
        self.assertTrue(run['ok'], run)
        self.assertFalse(run['changed'])
        self.assertEqual((self.source / '.mask.lock.json').read_bytes(), before)
        self.assertEqual(run['data']['consumers'][0]['changes'], [])
        self.assertTrue(run['data']['fetches'][TAP]['remote_refs_changed'])

        (self.source / 'skills/alpha/support.txt').write_text('new supporting content')
        candidate = self.publish()
        run = self.machine('upgrade', '--all')
        self.assertTrue(run['ok'], run)
        self.assertEqual([row['coordinate'] for row in run['data']['consumers'][0]['changes']], [TAP + '/alpha'])
        self.assertEqual(self.packages(self.source)[0]['commit'], candidate)
        self.assertEqual(self.packages(self.source)[1], first[1])
        self.commit_controls()
        before = (self.source / '.mask.lock.json').read_bytes()
        self.assertFalse(self.machine('upgrade', '--all')['changed'])
        self.assertEqual((self.source / '.mask.lock.json').read_bytes(), before)
        self.assertEqual(self.git(self.source, 'status', '--porcelain', '--', '.mask.lock.json'), '')

        # Content stability must not short-circuit ordinary readiness repair.
        link = self.source / '.agents/skills/alpha'
        target = os.readlink(link)
        link.unlink()
        repaired = self.machine('upgrade', '--all', '--offline')
        self.assertTrue(repaired['ok'], repaired)
        self.assertTrue(repaired['changed'])
        self.assertEqual(os.readlink(link), target)
        self.assertEqual((self.source / '.mask.lock.json').read_bytes(), before)
        self.assertEqual(repaired['data']['consumers'][0]['changes'], [])
        self.assertTrue(self.machine('status', '--all')['ok'])

    def test_shared_digest_different_commits_work_with_warm_and_cold_previews(self):
        (self.source / 'skills/alpha/mask-skill.json').write_text('{"schema_version":1,"requirements":[]}')
        self.publish('package metadata')
        self.assertTrue(self.machine('install', 'alpha', '--project', self.source)['ok'])
        self.publish('unrelated empty commit')
        self.assertTrue(self.machine('tap', 'fetch')['ok'])
        self.assertTrue(self.machine('install', 'alpha')['ok'])
        roots = (self.source, self.project)
        rows = [self.packages(root)[0] for root in roots]
        self.assertNotEqual(rows[0]['commit'], rows[1]['commit'])
        self.assertEqual(rows[0]['payload_digest'], rows[1]['payload_digest'])
        before = {root: (root / '.mask.lock.json').read_bytes() for root in roots}
        self.publish('another unrelated commit')
        self.assertTrue(self.machine('tap', 'fetch')['ok'])
        for cold in (False, True):
            with self.subTest(cold=cold):
                if cold:
                    (self.home / 'store').rename(self.base / 'retained-fixture-store')
                preview = self.machine('upgrade', '--all', '--dry-run')
                self.assertTrue(preview['ok'], preview)
                self.assertTrue(all(row['changes'] == [] for row in preview['data']['consumers']))
                self.assertEqual((self.home / 'store').exists(), not cold)
                run = self.machine('upgrade', '--all', '--approve-plan', preview['data']['plan_hash'])
                self.assertTrue(run['ok'], run)
                for root in roots:
                    self.assertEqual((root / '.mask.lock.json').read_bytes(), before[root])
                    self.assertTrue((root / '.agents/skills/alpha/SKILL.md').is_file())
                self.assertTrue(self.machine('status', '--all')['ok'])
