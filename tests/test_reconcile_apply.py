import json
import os
import subprocess
import sys
import unittest
from tests.support import ENTRY
from tests.support import Fixture
from tests.test_manifest_registry import declare_pinned


class ApplyTests(Fixture):
    """Legacy live-checkout starting state until MASK-0100 retires this behavior (v1 planner and engine)."""
    def setUp(self):
        super().setUp(); self.legacy_init(); self.declare(); self.call('project', 'register', self.project)

    def test_convergence_guard_noop_owned_removal(self):
        preview = self.call('plan')
        self.call('apply', '--expect-plan-hash', preview['data']['plan_hash'])
        leaf = self.project / '.agents/skills/alpha'
        self.assertTrue(leaf.is_symlink()); self.assertTrue(leaf.is_dir())
        before = self.snapshot()
        self.assertFalse(self.call('apply')['changed']); self.assertEqual(before, self.snapshot())
        self.call('project', 'unrequire', 'alpha', '--apply')
        self.assertFalse(leaf.exists()); self.assertFalse(leaf.is_symlink())
        self.assertTrue(leaf.parent.is_dir())

    def test_prospective_collision_keeps_manifest_and_other_links(self):
        target = self.project / '.agents/skills/beta'; target.mkdir(parents=True)
        (target / 'mine').write_text('owned by user')
        before = self.snapshot()
        self.call('project', 'require', 'beta', '--apply', code=4)
        self.assertEqual(before, self.snapshot())

    def test_stale_supporting_bytes_and_changed_owned_link(self):
        preview = self.call('plan')
        (self.source / 'skills/alpha/notes').write_text('changed')
        self.call('apply', '--expect-plan-hash', preview['data']['plan_hash'], code=4)
        self.assertFalse((self.project / '.agents').exists())
        self.call('apply')
        leaf = self.project / '.agents/skills/alpha'; leaf.unlink(); leaf.symlink_to(self.source / 'skills/beta', target_is_directory=True)
        before = self.snapshot()
        self.assertEqual(self.call('apply', code=4)['error']['code'], 'target.drift')
        self.assertEqual(before, self.snapshot())

    def test_missing_owned_recreated_and_dangling_removed(self):
        self.call('apply'); leaf = self.project / '.agents/skills/alpha'; leaf.unlink()
        self.call('apply'); self.assertTrue(leaf.is_symlink())
        source = self.source / 'skills/alpha'; source.rename(self.source / 'removed')
        self.call('project', 'unrequire', 'alpha', '--apply')
        self.assertFalse(leaf.is_symlink())

    def test_late_failure_rolls_back_links_but_reports_retained_directories(self):
        code = """
import sys
sys.path.insert(0, sys.argv[1])
import mask, mask_fs
fired = False
def fail(label):
    global fired
    if label == 'link' and not fired:
        fired = True
        raise OSError('injected late failure')
mask_fs.checkpoint = fail
raise SystemExit(mask.main(['apply', '--project', sys.argv[2], '--home', sys.argv[3], '--json']))
"""
        run = subprocess.run([sys.executable, '-B', '-c', code, str(ENTRY.parent), str(self.project), str(self.home)], capture_output=True, text=True)
        data = json.loads(run.stdout)
        self.assertEqual(run.returncode, 5, run.stdout)
        self.assertEqual(data['transaction'], 'rolled_back'); self.assertTrue(data['changed'])
        self.assertFalse((self.project / '.agents/skills/alpha').is_symlink())
        self.assertFalse((self.home / 'pending.json').exists())
        self.assertTrue(data['data']['retained_directories'])

    def test_replaced_parent_refuses(self):
        self.call('apply')
        parent = self.project / '.agents'; moved = self.project / '.agents-retained'
        parent.rename(moved)
        parent.symlink_to(moved, target_is_directory=True)
        before = self.snapshot()
        self.assertEqual(self.call('apply', code=4)['error']['code'], 'target.parent_link')
        self.assertEqual(before, self.snapshot())

    @unittest.skipUnless(os.name == 'nt', 'native Windows symlink error mapping')
    def test_windows_missing_privilege_refusal(self):
        import mask_fs
        from unittest.mock import patch
        from pathlib import Path
        error = OSError('required privilege not held'); error.winerror = 1314
        entry = dict(root=str(self.project), relative='.agents/skills/alpha', before=None, after=str(self.source / 'skills/alpha'))
        with patch.object(Path, 'symlink_to', side_effect=error):
            with self.assertRaises(mask_fs.c.MaskError) as caught:
                mask_fs.set_link(entry, 'after')
        self.assertEqual(caught.exception.code, 'target.symlink_unsupported')


class PinnedApplyTests(Fixture):
    """Tap-first: a registered, not yet applied v2 consumer of the fixture tap."""
    def setUp(self):
        super().setUp(); self.init(); declare_pinned(self); self.call('project', 'register', self.project)

    def test_unregister_preserves_declaration(self):
        self.call('apply'); self.call('project', 'unregister', self.project)
        self.assertTrue((self.project / '.mask.json').is_file())
        self.assertFalse((self.project / '.agents/skills/alpha').is_symlink())

    def test_all_projects_preflight_before_first_effect(self):
        other = self.base / 'second-project'; other.mkdir()
        declare_pinned(self, other, fetch=False)
        self.call('project', 'register', other)
        collision = other / '.claude/skills/alpha'; collision.mkdir(parents=True)
        # Warm the content store first: apply prepares artifacts outside the writer, and this test is about consumer effects.
        for root in (self.project, other):
            self.call('source', 'fetch', '--locked', '--project', root)
        before = self.snapshot()
        self.call('apply', '--all', code=4)
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.project / '.agents').exists())
