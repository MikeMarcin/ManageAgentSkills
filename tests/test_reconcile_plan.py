import os
import json
import subprocess
import unittest
from pathlib import Path
from tests.support import Fixture


class PlannerTests(Fixture):
    def setUp(self):
        super().setUp(); self.init(); self.declare(); self.call('project', 'register', self.project)

    def test_pure_plan_supporting_bytes_and_unmanaged_links(self):
        before = self.snapshot()
        preview = self.call('plan')
        self.assertTrue(preview['data']['applicable']); self.assertTrue(preview['would_change'])
        self.assertFalse(preview['changed']); self.assertEqual(before, self.snapshot())
        path = self.source / 'skills/alpha/ref.txt'; path.write_text('new')
        self.assertNotEqual(preview['data']['plan_hash'], self.call('plan')['data']['plan_hash'])
        target = self.project / '.agents/skills/alpha'; target.parent.mkdir(parents=True); target.symlink_to(self.source / 'skills/alpha', target_is_directory=True)
        plan = self.call('plan'); self.assertFalse(plan['data']['applicable'])
        self.assertEqual(plan['data']['blockers'][0]['code'], 'target.unmanaged_link')
        self.assertTrue(target.is_symlink())

    def test_collision_and_linked_parent(self):
        target = self.project / '.claude/skills/alpha'; target.mkdir(parents=True)
        marker = target / 'mine'; marker.write_text('preserve')
        self.assertEqual(self.call('plan')['data']['blockers'][0]['code'], 'target.collision')
        other = self.base / 'outside'; other.mkdir()
        (self.project / '.agents').symlink_to(other, target_is_directory=True)
        before = self.snapshot()
        self.assertFalse(self.call('plan')['data']['applicable'])
        self.assertEqual(before, self.snapshot())

    def test_all_unavailable_and_poisoned_state(self):
        moved = self.base / 'moved'; self.project.rename(moved)
        plan = self.call('plan', '--all', cwd=self.base)
        self.assertFalse(plan['data']['applicable'])
        self.assertEqual(plan['data']['blockers'][0]['code'], 'project.unavailable')
        path = self.home / 'state.json'; data = json.loads(path.read_text())
        data['projects'][str(self.project)]['links']['../../outside'] = dict(skill='alpha', target='codex', link_text='/wrong')
        path.write_text(json.dumps(data))
        self.assertEqual(self.call('plan', '--all', cwd=self.base, code=3)['error']['code'], 'state.invalid')

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
