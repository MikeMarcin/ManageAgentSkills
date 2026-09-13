import json
import os
import shlex
import subprocess
import sys

import mask_core as c
import mask_integration as integration
from tests.support import Fixture, ENTRY, TAP


class GitIntegrationTests(Fixture):
    def setUp(self):
        super().setUp()
        self.init()
        self.call('source', 'fetch', TAP)
        self.controls = {}
        self.declare_pinned()
        self.git(self.project, 'config', 'user.name', 'Fixture')
        self.git(self.project, 'config', 'user.email', 'fixture@example.invalid')
        self.git(self.project, 'add', '.mask.json', '.mask.lock.json')
        self.git(self.project, 'commit', '-m', 'declaration')
        self.call('integration', 'approve', '--project', self.project, '--linked-worktrees')

    def declare_pinned(self, skills=('alpha',), root=None):
        """Write a v2 declaration of the fixture tap and its matching lock into ``root``; nothing is deployed.

        ``lock`` refuses to rewrite an active consumer's lock, so each selection is resolved once in an unregistered
        scratch consumer from the fetched cache, its artifacts are hydrated, and both control files are copied. A Git
        event then observes the changed selection exactly as committed.
        """
        root = root or self.project
        key = tuple(skills)
        if key not in self.controls:
            scratch = self.base / 'pinned controls'
            scratch.mkdir(exist_ok=True)
            (scratch / '.mask.lock.json').unlink(missing_ok=True)
            (scratch / '.mask.json').write_text(json.dumps(dict(schema_version=2, sources=self.binding(), skills=[dict(source=TAP, id=identifier) for identifier in skills])) + '\n')
            self.call('lock', '--project', scratch)
            self.call('source', 'fetch', '--locked', '--offline', '--project', scratch)
            self.controls[key] = {name: (scratch / name).read_bytes() for name in ('.mask.json', '.mask.lock.json')}
        for name, data in self.controls[key].items():
            (root / name).write_bytes(data)

    def enable(self, *options, code=0):
        return self.call('integration', 'enable', '--git', '--project', self.project, *options, code=code)

    def test_owned_enable_disable_preserves_other_hooks(self):
        hook = self.project / '.git/hooks/pre-commit'
        hook.write_text('#!/bin/sh\nexit 0\n')
        preview = self.enable('--dry-run')
        self.assertFalse((self.project / '.git/hooks/post-commit').exists())
        self.enable('--expect-plan-hash', preview['data']['plan_hash'])
        self.assertFalse(self.enable()['changed'])
        self.git(self.project, 'commit', '--allow-empty', '-m', 'ensure')
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())
        self.call('integration', 'disable', '--git', '--project', self.project)
        self.assertEqual(hook.read_text(), '#!/bin/sh\nexit 0\n')
        self.assertFalse((self.project / '.git/hooks/post-commit').exists())

    def test_switch_worktree_and_merge_events(self):
        self.enable()
        self.git(self.project, 'switch', '-c', 'other')
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())
        self.declare_pinned(['beta'])
        self.git(self.project, 'commit', '-am', 'beta')
        self.assertTrue((self.project / '.agents/skills/beta').is_symlink())
        self.git(self.project, 'switch', 'main')
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())
        self.git(self.project, 'merge', 'other')
        self.assertTrue((self.project / '.agents/skills/beta').is_symlink())
        linked = self.base / 'linked'
        self.git(self.project, 'worktree', 'add', '-b', 'linked', str(linked))
        self.assertTrue((linked / '.agents/skills/beta').is_symlink())

    def test_git_event_reconciles_registered_nested_consumers_without_crawling(self):
        nested = self.project / 'nested'
        nested.mkdir()
        self.declare_pinned(root=nested)
        # The declaration moves into the nested consumer together with its lock.
        (self.project / '.mask.json').unlink()
        (self.project / '.mask.lock.json').unlink()
        self.git(self.project, 'add', '-A')
        self.git(self.project, 'commit', '-m', 'nested declaration')
        self.call('project', 'register', nested)
        self.call('integration', 'approve', '--project', nested)
        unrelated = self.project / 'not-registered'
        unrelated.mkdir()
        self.declare_pinned(root=unrelated)
        inner = self.project / 'inner-repository'
        inner.mkdir()
        self.git(inner, 'init', '-b', 'main')
        self.declare_pinned(root=inner)
        self.call('project', 'register', inner)
        self.call('integration', 'approve', '--project', inner)
        self.enable()
        self.declare_pinned(['beta'], root=nested)
        self.git(self.project, 'commit', '-am', 'change nested selection')
        self.assertTrue((nested / '.agents/skills/beta').is_symlink())
        self.assertFalse((unrelated / '.agents').exists())
        self.assertFalse((inner / '.agents/skills/alpha').is_symlink())

    def test_manual_merge_completion_and_postoperation_warning(self):
        self.enable()
        self.git(self.project, 'switch', '-c', 'other')
        self.declare_pinned(['beta'])
        self.git(self.project, 'commit', '-am', 'beta')
        self.git(self.project, 'switch', 'main')
        self.declare_pinned([])
        self.git(self.project, 'commit', '-am', 'empty')
        run = subprocess.run(['git', '-C', str(self.project), 'merge', 'other'], capture_output=True)
        self.assertNotEqual(run.returncode, 0)
        self.declare_pinned(['alpha', 'beta'])
        self.git(self.project, 'add', '.mask.json', '.mask.lock.json')
        self.git(self.project, 'commit', '-m', 'resolve')
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())
        self.assertTrue((self.project / '.agents/skills/beta').is_symlink())
        self.call('integration', 'revoke', '--project', self.project)
        run = subprocess.run(['git', '-C', str(self.project), 'commit', '--allow-empty', '-m', 'unapproved'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0)
        self.assertIn('already completed', run.stderr)
        self.assertIn('approval_required', run.stderr)

    def test_clone_coverage_is_explicit_and_no_hook_manager_takeover(self):
        clone = self.base / 'clone'
        self.git(self.base, 'clone', str(self.project), str(clone))
        result = self.enable()
        self.assertFalse(result['data']['coverage']['clone'])
        self.assertFalse((clone / '.agents/skills/alpha').is_symlink())
        self.call('integration', 'disable', '--git', '--project', self.project)
        manager = self.base / 'hook-manager'
        manager.mkdir()
        self.git(self.project, 'config', 'core.hooksPath', str(manager))
        if not integration.named_hooks(self.project):
            self.enable(code=4)
        self.assertEqual(self.git(self.project, 'config', '--get', 'core.hooksPath'), str(manager))

    def test_collisions_and_changed_owned_entries_refuse(self):
        if integration.named_hooks(self.project):
            self.skipTest('Directory collision fixture for legacy Git')
        hook = self.project / '.git/hooks/post-commit'
        hook.write_text('mine')
        self.enable(code=4)
        self.assertEqual(hook.read_text(), 'mine')
        hook.unlink()
        self.enable()
        hook.write_text('edited')
        self.call('integration', 'disable', '--git', '--project', self.project, code=4)
        self.assertEqual(hook.read_text(), 'edited')

    def test_interrupted_install_is_recoverable(self):
        script = """
import sys,os
sys.path.insert(0,sys.argv[1])
import mask,mask_fs
mask_fs.checkpoint=lambda label: os._exit(99) if label=='integration-entry' else None
mask.main(['integration','enable','--git','--project',sys.argv[3],'--home',sys.argv[2],'--json'])
"""
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), str(self.home), str(self.project)], capture_output=True)
        self.assertEqual(run.returncode, 99, run.stdout)
        self.call('recover', '--inspect')
        path = self.home / 'pending.json'
        original = path.read_bytes()
        pending = json.loads(original)
        pending['record']['interpreter'] = str(self.base / 'unapproved-interpreter')
        path.write_text(json.dumps(pending))
        before = self.snapshot()
        self.call('recover', '--complete', code=8)
        self.assertEqual(before, self.snapshot())
        path.write_bytes(original)
        self.call('recover', '--complete')
        self.assertFalse(self.enable()['changed'])

    def test_internal_git_suppresses_directory_and_configured_hooks(self):
        marker = self.base / 'marker'
        hook = self.project / '.git/hooks/post-commit'
        command = shlex.join(['touch', marker.as_posix()])
        hook.write_text('#!/bin/sh\n' + command + '\n', newline='\n')
        hook.chmod(0o755)
        self.git(self.project, 'config', 'hook.marker.event', 'post-commit')
        self.git(self.project, 'config', 'hook.marker.command', command)
        c.git(self.project, 'commit', '--allow-empty', '-m', 'internal', mutating=True)
        self.assertFalse(marker.exists())
        self.git(self.project, 'commit', '--allow-empty', '-m', 'external')
        self.assertTrue(marker.exists())
        marker.unlink()
        hook.unlink()
        if integration.named_hooks(self.project):
            self.git(self.project, 'commit', '--allow-empty', '-m', 'configured')
            self.assertTrue(marker.exists())
        run = subprocess.run([sys.executable, str(ENTRY.parent / 'mask_integration.py'), 'git-hook', str(self.home), 'post-checkout', 'old-revision', 'new-revision', '1'], env=dict(os.environ, MASK_INTERNAL_GIT='1'), capture_output=True)
        self.assertEqual(run.returncode, 0)
        self.assertEqual(run.stdout, b'')
