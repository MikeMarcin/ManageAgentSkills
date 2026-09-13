import os
import json
import subprocess
import unittest

import mask_core as c
import mask_resolve as r
import mask_store as store
from tests.support import TAP, Fixture


class PlannerTests(Fixture):
    """Tap-first: a registered, not yet applied v2 consumer of the fixture tap."""
    def setUp(self):
        super().setUp(); self.init(); self.declare_pinned(); self.call('project', 'register', self.project)

    def test_pure_plan_control_change_and_unmanaged_links(self):
        before = self.snapshot()
        preview = self.call('plan')
        self.assertTrue(preview['data']['applicable']); self.assertTrue(preview['would_change'])
        self.assertFalse(preview['changed']); self.assertEqual(before, self.snapshot())
        # Upstream bytes reach a plan only through the lock: a fetched new commit leaves the plan unchanged.
        (self.source / 'skills/alpha/ref.txt').write_text('new')
        self.publish('upstream change')
        self.call('source', 'fetch', TAP)
        self.assertEqual(preview['data']['plan_hash'], self.call('plan')['data']['plan_hash'])
        # A changed control changes the plan: alpha for codex only, with its coherent lock.
        declaration = c.read_json(self.project / '.mask.json')
        declaration['skills'][0]['agents'] = ['codex']
        lock = c.read_json(self.project / '.mask.lock.json')
        (self.project / '.mask.json').write_text(json.dumps(declaration) + '\n')
        (self.project / '.mask.lock.json').write_text(c.text_json(dict(lock, selection_digest=r.selection_digest(declaration))))
        self.assertNotEqual(preview['data']['plan_hash'], self.call('plan')['data']['plan_hash'])
        # Even a link to the exact locked store payload is unmanaged without an ownership record.
        self.call('source', 'fetch', '--locked', '--offline')
        target = self.project / '.agents/skills/alpha'; target.parent.mkdir(parents=True)
        target.symlink_to(store.location(self.home, lock['packages'][0]['payload_digest'], 'alpha')[1], target_is_directory=True)
        plan = self.call('plan'); self.assertFalse(plan['data']['applicable'])
        self.assertEqual(plan['data']['blockers'][0]['code'], 'target.unmanaged_link')
        self.assertTrue(target.is_symlink())

    def test_all_unavailable_and_poisoned_state(self):
        moved = self.base / 'moved'; self.project.rename(moved)
        plan = self.call('plan', '--all', cwd=self.base)
        self.assertFalse(plan['data']['applicable'])
        self.assertEqual(plan['data']['blockers'][0]['code'], 'project.unavailable')
        path = self.home / 'state.json'; data = json.loads(path.read_text(encoding='utf-8'))
        (record,) = data['projects'].values()
        # A resolution-valid pinned link record under an escaping path.
        record['links']['../../outside'] = dict(skill='alpha', target='codex', link_text='/wrong', resolution=record['last_lock']['packages'][0])
        path.write_text(json.dumps(data), encoding='utf-8')
        self.assertEqual(self.call('plan', '--all', cwd=self.base, code=3)['error']['code'], 'state.invalid')

    def test_collision_and_linked_parent(self):
        target = self.project / '.claude/skills/alpha'; target.mkdir(parents=True)
        marker = target / 'mine'; marker.write_text('preserve')
        self.assertEqual(self.call('plan')['data']['blockers'][0]['code'], 'target.collision')
        other = self.base / 'outside'; other.mkdir()
        (self.project / '.agents').symlink_to(other, target_is_directory=True)
        before = self.snapshot()
        self.assertFalse(self.call('plan')['data']['applicable'])
        self.assertEqual(before, self.snapshot())

    def test_case_aliases_on_case_insensitive_filesystem(self):
        alias = self.project.with_name(self.project.name.upper())
        if not alias.exists():
            self.skipTest('filesystem is case-sensitive')
        self.assertFalse(self.call('project', 'register', alias)['changed'])
        self.assertEqual(len(self.call('project', 'list')['data']['projects']), 1)
        self.assertTrue(self.call('plan', '--project', alias)['data']['applicable'])

    @unittest.skipUnless(os.name == 'nt', 'native Windows junction case')
    def test_windows_junction_parent_refuses(self):
        outside = self.base / 'outside'; outside.mkdir()
        junction = self.project / '.agents'
        subprocess.run(['cmd', '/c', 'mklink', '/J', str(junction), str(outside)], check=True, capture_output=True)
        self.assertEqual(self.call('plan')['data']['blockers'][0]['code'], 'target.parent_link')
        self.assertEqual(list(outside.iterdir()), [])
