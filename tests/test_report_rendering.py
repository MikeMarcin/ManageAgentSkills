"""Public report views, layered inventory and recorded-only fleet observations."""
import json

from tests.test_profiles import ProfileFixture, URI
from tests.support import TAP


class ReportRenderingTests(ProfileFixture):
    def test_saved_report_is_redacted_paginated_and_uses_same_guard(self):
        self.call('install', TAP + '/alpha', '--no-update')
        self.install_user('alpha')
        self.call('pin', 'alpha', '--user')
        (self.source / 'skills/alpha/changes & notes.txt').write_text('Do not display <script>alert(1)</script>\x1b[31m\n', encoding='utf-8')
        self.publish()
        self.call('tap', 'fetch', TAP)
        first = self.call('update', 'report', '--all', '--limit', '1')['data']
        self.assertEqual(first['impact']['total_rows'], 2)
        self.assertEqual(first['impact']['next_offset'], 1)
        receipt = self.base / 'impact.json'
        saved = self.call('update', 'report', '--all', '--offset', '1', '--output', receipt)
        self.assertEqual(saved['data']['plan_hash'], first['plan_hash'])
        raw = receipt.read_text(encoding='utf-8')
        for private in (str(self.project), str(self.home), str(self.personal), str(self.upstream), URI, '<script>', 'alert(1)', '\x1b'):
            self.assertNotIn(private, raw)
        self.assertIn('project-1', raw)
        self.assertIn('user-1', raw)
        view = self.call('report', receipt, '--format', 'html')['data']['view']
        self.assertEqual(view['operation_id'], saved['data']['operation_id'])
        text = self.human('report', receipt)
        self.assertEqual(text.returncode, 0, text.stderr)
        self.assertIn('affected', text.stdout)
        html = self.human('report', receipt, '--format', 'html')
        self.assertEqual(html.returncode, 0, html.stderr)
        self.assertIn('changes &amp; notes.txt', html.stdout)
        for unsafe in ('<script', 'http', 'href=', str(self.project), '\x1b'):
            self.assertNotIn(unsafe, html.stdout)
        target = self.base / 'report.html'
        self.call('report', receipt, '--format', 'html', '--output', target)
        self.assertEqual(target.read_text(encoding='utf-8'), html.stdout)
        self.assertEqual(self.call('report', receipt, '--format', 'html', '--output', target, code=4)['error']['code'], 'report.collision')
        self.assertEqual(self.call('update', 'report', '--all', '--output', receipt, code=4)['error']['code'], 'report.collision')
        self.assertEqual(receipt.read_text(encoding='utf-8'), raw)
        invalid = self.base / 'edited-receipt.json'
        invalid.write_text(raw.replace('project-1', 'other-location'), encoding='utf-8')
        self.assertEqual(self.call('report', invalid, '--format', 'html', code=4)['error']['code'], 'report.invalid')
        self.call('upgrade', '--all', '--no-update', '--approve-plan', first['plan_hash'])
        self.assertTrue((self.project / '.agents/skills/alpha/changes & notes.txt').exists())

    def test_layered_inventory_and_stale_recorded_receipt_stay_observational(self):
        self.install_user('alpha', '--agent', 'codex')
        self.install_user('beta')
        profile = self.export()
        self.call('uninstall', 'beta', '--user')
        self.call('profile', 'subscribe', profile, '--user', '--name', 'shared')
        source_index = self.source / 'mask-source.json'
        source_index.write_text(json.dumps(dict(schema_version=1,
            packages={name: 'skills/' + name for name in ('alpha', 'beta', 'implement-rfc')},
            bundles={'example': dict(skills=[dict(source=TAP, id='alpha')])})), encoding='utf-8')
        self.git(self.source, 'add', 'mask-source.json')
        self.publish()
        self.call('tap', 'fetch', TAP)
        self.call('bundle', 'install', TAP + '/example')
        project_rows = self.call('skill', 'where-used', TAP + '/alpha', '--scope', 'project')['data']['rows']
        self.assertEqual({tuple(row['origins']) for row in project_rows}, {('bundle:' + TAP + '/example',)})
        unrelated = self.personal / '.agents/skills/unmanaged'
        unrelated.mkdir()
        (unrelated / 'notes').write_text('unmanaged', encoding='utf-8')
        state = (self.home / 'state.json').read_bytes()
        before = self.call('skill', 'where-used', TAP + '/alpha', '--scope', 'user', '--agent', 'codex', '--fleet')['data']
        self.assertEqual(before['fleet']['status'], 'unavailable')
        self.assertFalse(before['complete'])
        self.assertEqual(len(before['rows']), 1)
        row = before['rows'][0]
        self.assertEqual(row['origins'], ['local', 'profile:shared'])
        self.assertEqual(row['status'], 'managed_converged')
        self.assertEqual(row['host_load'], 'not_verified')
        self.assertEqual(before['work']['leaves_inspected'], 1)
        self.assertEqual(before['work']['payload_files_read'], 0)
        self.assertEqual(before['work']['payload_bytes_read'], 0)
        self.assertEqual(before['work']['git_scans'], 0)
        self.assertGreater(before['work']['declaration_bytes_read'], 0)
        inventory = self.call('inventory', '--user', '--include-unmanaged')['data']
        self.assertEqual({tuple(row['origins']) for row in inventory['rows'] if row['skill'] == TAP + '/beta'}, {('profile:shared',)})
        self.assertTrue(any(row['name'] == 'unmanaged' and row['status'] == 'unmanaged_present' for row in inventory['rows']))
        snapshot = self.base / 'fleet-observation-fixture.json'
        new, old = 'sha256:' + 'b' * 64, 'sha256:' + 'a' * 64
        observation = dict(device='fixture-host', observed_at='2026-10-01T00:00:00Z', desired_revision=old, scope='user',
                           agent='codex', skill=TAP + '/alpha', repository=URI, payload_digest=row['artifact']['payload_digest'],
                           outcome='installed')
        snapshot.write_text(json.dumps(dict(schema_version=1, desired_revision=new, observations=[observation])), encoding='utf-8')
        data = self.call('skill', 'where-used', TAP + '/alpha', '--scope', 'user', '--agent', 'codex', '--fleet',
                         '--fleet-observations', snapshot)['data']
        self.assertEqual(data['rows'], before['rows'])
        self.assertEqual(data['fleet']['rows'][0]['status'], 'stale_receipt')
        self.assertEqual(data['fleet']['rows'][0]['observed_at'], observation['observed_at'])
        self.assertEqual(data['network'], 'none')
        self.assertFalse(data['complete'])
        self.assertEqual((self.home / 'state.json').read_bytes(), state)
        self.assertEqual((unrelated / 'notes').read_text(encoding='utf-8'), 'unmanaged')
