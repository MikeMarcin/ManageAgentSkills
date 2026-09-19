"""Explicit cache retention never trusts suspect objects or changes consumers."""
import json
from pathlib import Path

from tests.support import Fixture, TAP


class CacheRepairTests(Fixture):
    def setUp(self):
        super().setUp()
        self.init()
        self.install(TAP + '/alpha')
        self.cache = Path(self.call('source', 'show', TAP)['data']['binding']['cache'])

    def invalidate_identity(self):
        path = self.cache / 'mask-source.json'
        marker = json.loads(path.read_text())
        marker['identity']['device'] += 1
        path.write_text(json.dumps(marker))

    def test_preview_retains_suspect_cache_and_normal_fetch_rebuilds(self):
        self.invalidate_identity()
        refused = self.call('source', 'fetch', TAP, code=4)
        self.assertEqual(refused['error']['code'], 'source.cache_invalid')
        self.assertEqual(refused['error']['details']['path'], str(self.cache))
        marker = (self.cache / 'mask-source.json').read_bytes()
        (self.cache / 'unrelated-note').write_text('keep this evidence')
        # Retention must not execute Git against the suspect cache or copy its config.
        (self.cache / 'config').write_text('[deliberately-invalid')
        config = (self.home / 'config.json').read_bytes()
        state = (self.home / 'state.json').read_bytes()
        consumer = self.snapshot(self.project)
        before = self.snapshot()
        preview = self.call('source', 'repair-cache', TAP, '--dry-run')
        self.assertEqual(before, self.snapshot())
        backup = Path(preview['data']['cache_retained'])
        result = self.call('source', 'repair-cache', TAP, '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertTrue(result['changed'])
        self.assertFalse(self.cache.exists())
        self.assertEqual((backup / 'mask-source.json').read_bytes(), marker)
        self.assertEqual((backup / 'unrelated-note').read_text(), 'keep this evidence')
        self.assertEqual((backup / 'config').read_text(), '[deliberately-invalid')
        self.assertEqual(self.call('source', 'repair-cache', TAP, '--expect-plan-hash', preview['data']['plan_hash'], code=4)['error']['code'], 'plan.stale')
        self.call('source', 'fetch', TAP)
        self.assertFalse((self.cache / 'unrelated-note').exists())
        self.assertEqual(self.call('source', 'show', TAP)['data']['cached_revision'], self.git(self.source, 'rev-parse', 'HEAD'))
        self.assertEqual(config, (self.home / 'config.json').read_bytes())
        self.assertEqual(state, (self.home / 'state.json').read_bytes())
        self.assertEqual(consumer, self.snapshot(self.project))

    def test_stale_plan_and_retention_collision_preserve_all_bytes(self):
        preview = self.call('source', 'repair-cache', TAP, '--dry-run')
        self.invalidate_identity()
        before = self.snapshot()
        self.assertEqual(self.call('source', 'repair-cache', TAP, '--expect-plan-hash', preview['data']['plan_hash'], code=4)['error']['code'], 'plan.stale')
        self.assertEqual(before, self.snapshot())
        preview = self.call('source', 'repair-cache', TAP, '--dry-run')
        backup = Path(preview['data']['cache_retained'])
        backup.mkdir()
        (backup / 'owner').write_text('preserve')
        before = self.snapshot()
        self.assertEqual(self.call('source', 'repair-cache', TAP, '--expect-plan-hash', preview['data']['plan_hash'], code=4)['error']['code'], 'source.cache_collision')
        self.assertEqual(before, self.snapshot())

    def test_unrecognized_directory_and_symlink_refuse(self):
        held = self.cache.with_name('fixture-held.git')
        self.cache.rename(held)
        self.cache.mkdir()
        (self.cache / 'mine').write_text('unmanaged')
        before = self.snapshot()
        self.assertEqual(self.call('source', 'repair-cache', TAP, '--dry-run', code=4)['error']['code'], 'source.cache_invalid')
        self.assertEqual(before, self.snapshot())
        (self.cache / 'mine').unlink()
        self.cache.rmdir()
        self.cache.symlink_to(held, target_is_directory=True)
        before = self.snapshot()
        self.assertEqual(self.call('source', 'repair-cache', TAP, code=4)['error']['code'], 'source.cache_invalid')
        self.assertEqual(before, self.snapshot())
