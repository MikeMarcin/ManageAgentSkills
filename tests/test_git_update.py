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

    def test_guard_binds_the_previewed_candidate_without_fetching(self):
        # RFC-MASK-0018 contract section 4: --expect-plan-hash never fetches a different candidate before applying.
        reviewed = self.upstream(); self.call('source', 'fetch')
        preview = self.call('update', '--dry-run')
        newer = self.upstream('Another revision')
        done = self.call('update', '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertFalse(done['data']['fetch_effects']['attempted'])
        self.assertEqual(reviewed, self.git(self.source, 'rev-parse', 'HEAD'))
        self.call('source', 'fetch')
        self.assertEqual(self.call('update', '--expect-plan-hash', preview['data']['plan_hash'], code=4)['error']['code'], 'plan.stale')
        self.assertEqual(reviewed, self.git(self.source, 'rev-parse', 'HEAD'))
        self.assertEqual(self.call('update')['data']['source_after'], newer)

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

    def test_candidate_directory_case_collision_and_symlink(self):
        blob = self.git(self.source, 'rev-parse', 'HEAD:skills/alpha/SKILL.md')
        for entries in ((('100644', 'Docs/a.txt'), ('100644', 'docs/b.txt')), (('120000', 'linked'),)):
            for mode, name in entries:
                self.git(self.source, 'update-index', '--add', '--cacheinfo', mode + ',' + blob + ',skills/alpha/' + name)
            tree = self.git(self.source, 'write-tree')
            head = self.git(self.source, 'rev-parse', 'HEAD')
            candidate = self.git(self.source, 'commit-tree', tree, '-p', head, '-m', 'invalid candidate')
            self.git(self.source, 'read-tree', 'HEAD')
            self.git(self.source, 'update-ref', 'refs/remotes/origin/main', candidate)
            self.assertEqual(self.call('update', '--dry-run', code=4)['error']['code'], 'source.candidate_invalid')
            self.assertEqual(head, self.git(self.source, 'rev-parse', 'HEAD'))

    def test_hooks_suppressed_and_late_apply_failure_retains_intent(self):
        candidate = self.upstream()
        marker = self.base / 'hook-ran'
        hook = self.source / '.git/hooks/post-merge'
        hook.write_text('#!/bin/sh\necho unsafe > "' + str(marker) + '"\n')
        hook.chmod(0o755)
        script = """
import sys
sys.path.insert(0,sys.argv[1])
import mask,mask_fs
original = mask_fs.restore
def fail(pending, home, side, **kwargs):
    if side == 'after': raise OSError('injected late failure')
    return original(pending,home,side,**kwargs)
mask_fs.restore = fail
raise SystemExit(mask.main(['update','--home',sys.argv[2],'--json']))
"""
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), str(self.home)], capture_output=True, encoding='utf-8')
        self.assertEqual(run.returncode, 8, run.stdout)
        self.assertFalse(marker.exists())
        self.assertEqual(candidate, self.git(self.source, 'rev-parse', 'HEAD'))
        self.assertTrue((self.home / 'pending.json').exists())
        self.call('recover', '--complete')

    def test_diverged_and_unavailable_preflight(self):
        self.upstream()
        self.git(self.source, 'commit', '--allow-empty', '-m', 'local divergence')
        self.assertEqual(self.call('update', code=4)['error']['code'], 'source.diverged')
        # No fetch is attempted for an unavailable registered consumer.
        moved = self.base / 'moved project'
        self.project.rename(moved)
        result = self.call('update', cwd=self.base, code=4)
        self.assertEqual(result['error']['code'], 'project.unavailable')
        self.assertNotIn('fetch_effects', result['data'])

    def test_checkout_failure_retains_journal_without_reset(self):
        self.upstream()
        old = self.git(self.source, 'rev-parse', 'HEAD')
        script = """
import sys
sys.path.insert(0,sys.argv[1])
import mask,mask_core
original = mask_core.git
def fail(root,*args,**kwargs):
    if args and args[0] == 'merge': raise OSError('injected checkout failure')
    return original(root,*args,**kwargs)
mask_core.git = fail
raise SystemExit(mask.main(['update','--home',sys.argv[2],'--json']))
"""
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), str(self.home)], capture_output=True, encoding='utf-8')
        self.assertEqual(run.returncode, 8, run.stdout)
        self.assertEqual(json.loads(run.stdout)['transaction'], 'partial')
        self.assertEqual(old, self.git(self.source, 'rev-parse', 'HEAD'))
        self.call('recover', '--rollback')
