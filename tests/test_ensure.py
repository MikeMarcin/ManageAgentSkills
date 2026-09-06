import json
import subprocess
import sys
from unittest.mock import patch

import mask_core as c
import mask_fs as fs
from tests.support import Fixture, ENTRY


class EnsureTests(Fixture):
    def setUp(self):
        super().setUp()
        self.init()
        self.declare()

    def approve(self, *options):
        return self.call('integration', 'approve', '--project', self.project, *options)

    def test_authority_registration_check_and_noop(self):
        before = self.snapshot()
        self.assertEqual(self.call('ensure', code=4)['error']['code'], 'integration.approval_required')
        self.assertEqual(before, self.snapshot())
        preview = self.approve('--dry-run')
        self.assertEqual(before, self.snapshot())
        self.approve('--expect-plan-hash', preview['data']['plan_hash'])
        before = self.snapshot()
        self.call('ensure', '--check', code=7)
        self.assertEqual(before, self.snapshot())
        result = self.call('ensure', '--offline')
        self.assertTrue(result['changed'])
        self.assertEqual(result['data']['readiness'], 'ready_legacy_unpinned')
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())
        before = self.snapshot()
        self.assertFalse(self.call('ensure')['changed'])
        self.call('ensure', '--check')
        self.assertEqual(before, self.snapshot())
        self.call('integration', 'revoke', '--project', self.project)
        self.call('ensure', code=4)
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())

    def test_collision_and_replaced_parent_are_preserved(self):
        self.approve()
        leaf = self.project / '.agents/skills/alpha'
        leaf.mkdir(parents=True)
        (leaf / 'mine').write_text('keep')
        before = self.snapshot()
        self.assertEqual(self.call('ensure', code=4)['error']['code'], 'target.collision')
        self.assertEqual(before, self.snapshot())
        (leaf / 'mine').unlink()
        leaf.rmdir()
        leaf.parent.rmdir()
        external = self.base / 'outside'
        external.mkdir()
        leaf.parent.symlink_to(external, target_is_directory=True)
        before = self.snapshot()
        self.call('ensure', code=4)
        self.assertEqual(before, self.snapshot())

    def test_registration_is_not_automatic_approval(self):
        self.call('project', 'register', self.project)
        self.call('ensure', code=4)
        self.call('apply')  # Existing explicit management remains available.

    def test_selection_boundary_and_explicit_nongit_root(self):
        nested = self.project / 'nested'
        nested.mkdir()
        self.git(nested, 'init', '-b', 'main')
        self.approve()
        self.assertEqual(self.call('ensure', cwd=nested, code=3)['error']['code'], 'manifest.missing')
        ordinary = self.base / 'ordinary'
        ordinary.mkdir()
        (ordinary / '.mask.json').write_text(json.dumps(dict(schema_version=1, skills=['beta'])))
        self.call('integration', 'approve', '--project', ordinary)
        self.call('ensure', '--project', ordinary)
        self.assertTrue((ordinary / '.agents/skills/beta').is_symlink())

    def test_linked_worktrees_and_root_replacement(self):
        self.git(self.project, 'config', 'user.name', 'Fixture')
        self.git(self.project, 'config', 'user.email', 'fixture@example.invalid')
        self.git(self.project, 'add', '.mask.json')
        self.git(self.project, 'commit', '-m', 'declaration')
        self.approve('--linked-worktrees')
        linked = self.base / 'linked'
        self.git(self.project, 'worktree', 'add', '-b', 'linked', str(linked))
        self.call('ensure', cwd=linked)
        self.assertTrue((linked / '.agents/skills/alpha').is_symlink())
        moved = self.base / 'original'
        self.project.rename(moved)
        self.project.mkdir()
        self.declare()
        self.call('ensure', '--project', self.project, code=4)

    def test_selected_package_only_and_no_source_status_scan(self):
        self.approve()
        config = c.config(c.read_json(self.home / 'config.json'))
        state = c.state(c.read_json(self.home / 'state.json'))
        with patch.object(c, 'package', wraps=c.package) as packages, patch.object(c, 'git', wraps=c.git) as git:
            planned = fs.plan(config, state, [self.project], register=[str(self.project)], home=self.home, source_status=False)
        self.assertFalse(planned['blockers'])
        self.assertEqual([call.args[1] for call in packages.call_args_list], ['alpha'])
        self.assertFalse(any(call.args[1] == 'status' for call in git.call_args_list))

    def test_pending_and_busy_refuse(self):
        self.approve()
        script = """
import os,sys
sys.path.insert(0,sys.argv[1])
import mask,mask_fs
mask_fs.checkpoint=lambda label: os._exit(99) if label=='intent' else None
mask.main(['ensure','--home',sys.argv[2],'--project',sys.argv[3],'--json'])
"""
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), str(self.home), str(self.project)], capture_output=True)
        self.assertEqual(run.returncode, 99)
        before = self.snapshot()
        self.call('ensure', code=8)
        self.call('ensure', '--check', code=8)
        self.assertEqual(before, self.snapshot())
        self.call('recover', '--rollback')
        with c.writer_lock(self.home):
            self.assertEqual(self.call('ensure', code=6)['error']['code'], 'lock.busy')

    def test_approval_guard_and_event_validation(self):
        preview = self.approve('--dry-run')
        self.approve()
        self.assertEqual(self.call('integration', 'approve', '--project', self.project, '--expect-plan-hash', preview['data']['plan_hash'], code=4)['error']['code'], 'plan.stale')
        self.call('ensure', '--event', 'unknown', code=2)
