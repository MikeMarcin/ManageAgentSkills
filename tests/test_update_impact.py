"""Public exact diffs and the executable update impact candidate."""
import json

from tests.public_support import PublicFixture
from tests.support import TAP


class UpdateImpactTests(PublicFixture):
    def call(self, *args, code=0):
        if args[0] in ('install', 'upgrade'):
            args = (*args, '--no-update')
        run = self.raw(*args, '--json')
        self.assertEqual(run.returncode, code, run.stdout + run.stderr)
        self.assertEqual(run.stderr, '')
        return json.loads(run.stdout)

    def contents(self):
        return {str(path): path.read_bytes() for path in
                [self.home / 'config.json', self.home / 'state.json', self.home / 'user.json',
                 self.home / 'user.lock.json', self.project / '.mask.json', self.project / '.mask.lock.json']}

    def test_supporting_binary_and_metadata_diff_binds_same_approval(self):
        self.call('install', TAP + '/alpha')
        self.call('install', TAP + '/alpha', '--user')
        self.call('pin', 'alpha', '--user')
        package = self.source / 'skills/alpha'
        old = self.git(self.source, 'rev-parse', 'HEAD')
        (package / 'asset.bin').write_bytes(b'\x00\x01\xff')
        (package / 'support.txt').write_text('new support\n', encoding='utf-8')
        (package / 'mask-skill.json').write_text('{"schema_version":1,"requirements":["example"]}\n', encoding='utf-8')
        new = self.publish()
        self.call('tap', 'fetch', TAP)
        before = self.contents()
        result = self.call('update', 'report', '--all')['data']
        self.assertEqual(self.contents(), before)
        self.assertEqual(result['plan_hash'], self.call('upgrade', '--all', '--dry-run')['data']['plan_hash'])
        comparison = result['impact']['comparisons'][0]
        self.assertEqual((comparison['before_commit'], comparison['after_commit']), (old, new))
        files = {row['path']: row for row in comparison['files']}
        self.assertEqual(set(files), {'asset.bin', 'support.txt', 'mask-skill.json'})
        self.assertTrue(files['asset.bin']['binary'])
        self.assertEqual(files['asset.bin']['after']['size'], 3)
        self.assertTrue(files['asset.bin']['after']['sha256'].startswith('sha256:'))
        scopes = {row['scope']: row for row in result['impact']['deployments']}
        self.assertEqual(scopes['user']['status'], 'pinned_unaffected')
        self.assertEqual(scopes['project']['status'], 'affected')
        self.assertTrue(scopes['project']['host_refresh_required'])
        self.assertFalse(scopes['project']['targets_changed'])
        diff = self.call('diff', TAP + '/alpha', '--from', old, '--to', new, '--patch')['data']
        self.assertEqual(diff['files'], comparison['files'])
        self.assertIn('+new support', diff['patch'])
        self.assertNotIn('asset.bin', diff['patch'])
        self.call('upgrade', '--all', '--approve-plan', result['plan_hash'])
        self.assertTrue((self.project / '.agents/skills/alpha/asset.bin').is_file())
        self.assertFalse((self.personal / '.agents/skills/alpha/asset.bin').exists())

    def test_moving_same_payload_ref_stales_approval_without_rewriting_lock(self):
        self.call('install', TAP + '/alpha')
        old = (self.project / '.mask.lock.json').read_bytes()
        first = self.call('update', 'report')['data']
        (self.source / 'skills/beta/extra.txt').write_text('unrelated package', encoding='utf-8')
        self.publish()
        self.call('tap', 'fetch', TAP)
        second = self.call('update', 'report')['data']
        self.assertNotEqual(first['plan_hash'], second['plan_hash'])
        self.assertEqual(second['impact']['deployments'][0]['status'], 'ref_advanced_identical_payload')
        stale = self.call('upgrade', '--approve-plan', first['plan_hash'], code=4)
        self.assertEqual(stale['error']['code'], 'plan.stale')
        self.assertFalse(self.call('upgrade', '--approve-plan', second['plan_hash'])['changed'])
        self.assertEqual((self.project / '.mask.lock.json').read_bytes(), old)

    def test_target_restriction_is_visible_before_activation(self):
        self.call('install', TAP + '/alpha')
        self.call('project', 'set-agents', TAP + '/alpha', '--all')
        package = self.source / 'skills/alpha'
        (package / 'mask-skill.json').write_text('{"schema_version":1,"agents":["codex"]}\n', encoding='utf-8')
        self.publish()
        self.call('tap', 'fetch', TAP)
        result = self.call('update', 'report')['data']['impact']
        self.assertEqual(result['comparisons'][0]['kind'], 'metadata')
        row = result['deployments'][0]
        self.assertEqual(row['before_agents'], ['claude', 'codex'])
        self.assertEqual(row['after_agents'], ['codex'])
        self.assertTrue(row['targets_changed'])
        self.assertTrue((self.project / '.claude/skills/alpha').is_symlink())

    def test_provenance_only_change_and_control_edit_stale_guard(self):
        self.call('install', TAP + '/alpha')
        (self.source / 'skills/alpha/.mask-provenance.json').write_text('{"note":"fixture provenance"}\n', encoding='utf-8')
        self.publish()
        self.call('tap', 'fetch', TAP)
        result = self.call('update', 'report')['data']
        self.assertEqual(result['impact']['comparisons'][0]['kind'], 'provenance')
        self.assertFalse(result['impact']['deployments'][0]['host_refresh_required'])
        declaration = self.project / '.mask.json'
        declaration.write_bytes(declaration.read_bytes() + b'\n')
        refused = self.call('upgrade', '--approve-plan', result['plan_hash'], code=4)
        self.assertEqual(refused['error']['code'], 'plan.stale')
        self.assertFalse((self.project / '.agents/skills/alpha/.mask-provenance.json').exists())
