import json
import os
from pathlib import Path
import subprocess
import sys
from tests.support import Fixture, ENTRY


class UpdateTests(Fixture):
    def setUp(self):
        super().setUp()
        self.remote = self.base / 'AgentSkills.git'
        self.git(self.base, 'init', '--bare', str(self.remote))
        self.git(self.source, 'remote', 'add', 'origin', str(self.remote))
        self.git(self.source, 'push', '-u', 'origin', 'main')
        self.author = self.base / 'author'
        self.git(self.base, 'clone', '--branch', 'main', str(self.remote), str(self.author))
        self.git(self.author, 'config', 'user.name', 'Fixture'); self.git(self.author, 'config', 'user.email', 'fixture@example.invalid')
        self.init(); self.declare(); self.call('project', 'register', self.project, '--apply')

    def upstream(self, text='Updated instructions.'):
        path = self.author / 'skills/alpha/SKILL.md'
        path.write_text(path.read_text() + '\n' + text + '\n')
        self.git(self.author, 'add', 'skills'); self.git(self.author, 'commit', '-m', 'upstream change'); self.git(self.author, 'push', 'origin', 'main')
        return self.git(self.author, 'rev-parse', 'HEAD')

    def test_fetch_preview_guard_update_noop(self):
        old = self.git(self.source, 'rev-parse', 'HEAD'); candidate = self.upstream()
        before = self.snapshot()
        preview = self.call('update', '--dry-run')
        self.assertEqual(before, self.snapshot()); self.assertEqual(self.git(self.source, 'rev-parse', 'HEAD'), old)
        self.assertTrue(preview['data']['requires_fetch'])
        fetched = self.call('source', 'fetch')
        self.assertFalse(fetched['changed']); self.assertTrue(fetched['data']['fetch_effects']['remote_refs_changed'])
        preview = self.call('update', '--dry-run')
        done = self.call('update', '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertEqual(self.git(self.source, 'rev-parse', 'HEAD'), candidate)
        self.assertTrue(done['changed']); self.assertEqual(done['data']['source_after'], candidate)
        self.assertFalse(self.call('update')['changed'])

    def test_missing_skill_and_link_candidate_refuse(self):
        self.git(self.author, 'rm', '-r', 'skills/alpha'); self.git(self.author, 'commit', '-m', 'remove requested'); self.git(self.author, 'push', 'origin', 'main')
        old = self.git(self.source, 'rev-parse', 'HEAD')
        self.assertEqual(self.call('update', code=4)['error']['code'], 'source.candidate_invalid')
        self.assertEqual(old, self.git(self.source, 'rev-parse', 'HEAD'))
        self.assertTrue((self.project / '.agents/skills/alpha').is_dir())

    def test_dirty_ahead_detached_and_unavailable_refuse(self):
        (self.source / 'untracked').write_text('authoring')
        self.assertEqual(self.call('update', code=4)['error']['code'], 'source.dirty')
        (self.source / 'untracked').unlink()
        self.git(self.source, 'commit', '--allow-empty', '-m', 'local only')
        self.assertEqual(self.call('update', code=4)['error']['code'], 'source.ahead')
        self.git(self.source, 'checkout', '--detach')
        self.assertEqual(self.call('update', code=4)['error']['code'], 'source.detached')

    def test_remote_movement_stales_guard(self):
        self.upstream(); self.call('source', 'fetch')
        preview = self.call('update', '--dry-run'); old = self.git(self.source, 'rev-parse', 'HEAD')
        self.upstream('Another revision')
        self.assertEqual(self.call('update', '--expect-plan-hash', preview['data']['plan_hash'], code=4)['error']['code'], 'plan.stale')
        self.assertEqual(old, self.git(self.source, 'rev-parse', 'HEAD'))

    def test_post_advance_crash_recovers_without_git_rollback(self):
        candidate = self.upstream()
        script = """
import sys,os
sys.path.insert(0,sys.argv[1])
import mask,mask_fs
mask_fs.checkpoint = lambda label: os._exit(99) if label == 'git' else None
raise SystemExit(mask.main(['update','--home',sys.argv[2],'--json']))
"""
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), str(self.home)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 99, (run.stdout, run.stderr))
        self.assertEqual(self.git(self.source, 'rev-parse', 'HEAD'), candidate)
        self.call('recover', '--rollback', code=8)
        self.call('recover', '--complete')
        self.assertEqual(self.git(self.source, 'rev-parse', 'HEAD'), candidate)
        self.assertFalse(self.call('apply')['changed'])
