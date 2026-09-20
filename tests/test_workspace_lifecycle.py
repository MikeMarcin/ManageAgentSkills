import json
import subprocess
import sys

from tests.support import Fixture, ENTRY, TAP


class WorkspaceLifecycleTests(Fixture):
    def setUp(self):
        super().setUp()
        self.init()
        self.call('source', 'fetch', TAP)
        self.controls = {}
        self.git(self.project, 'config', 'user.name', 'Fixture')
        self.git(self.project, 'config', 'user.email', 'fixture@example.invalid')
        (self.project / 'README').write_text('initial')
        self.git(self.project, 'add', 'README')
        self.git(self.project, 'commit', '-m', 'without declaration')
        self.git(self.project, 'branch', 'inactive')
        self.declare_pinned()
        self.git(self.project, 'add', '.mask.json', '.mask.lock.json')
        self.git(self.project, 'commit', '-m', 'declare')
        self.call('integration', 'approve', '--project', self.project, '--inactive-branches')
        self.call('ensure')

    def pinned_controls(self, skills):
        """Declaration and lock bytes of one v2 selection of the fixture tap, resolved once with hydrated artifacts.

        ``lock`` refuses to rewrite an active consumer's lock, so the selection is resolved in an unregistered scratch
        consumer from the fetched cache; a branch then carries both controls exactly as committed.
        """
        key = tuple(skills)
        if key not in self.controls:
            scratch = self.base / 'pinned controls'
            scratch.mkdir(exist_ok=True)
            (scratch / '.mask.lock.json').unlink(missing_ok=True)
            (scratch / '.mask.json').write_text(json.dumps(dict(schema_version=2, sources=self.binding(), skills=[dict(source=TAP, id=identifier) for identifier in skills])) + '\n')
            self.call('lock', '--project', scratch)
            self.call('source', 'fetch', '--locked', '--offline', '--project', scratch)
            self.controls[key] = {name: (scratch / name).read_bytes() for name in ('.mask.json', '.mask.lock.json')}
        return self.controls[key]

    def declare_pinned(self, skills=('alpha',)):
        for name, data in self.pinned_controls(skills).items():
            (self.project / name).write_bytes(data)

    def crash(self, label):
        script = """
import os,sys
sys.path.insert(0,sys.argv[1])
import mask,mask_fs
mask_fs.checkpoint=lambda label: os._exit(99) if label==sys.argv[4] else None
__import__('tests.engine_cli', fromlist=['main']).main(['ensure','--home',sys.argv[2],'--project',sys.argv[3],'--json'])
"""
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), str(self.home), str(self.project), label], capture_output=True)
        self.assertEqual(run.returncode, 99, run.stdout)

    def test_inactive_branch_removes_only_owned_and_restores(self):
        unrelated = self.project / '.agents/skills/mine'
        unrelated.mkdir()
        self.git(self.project, 'switch', 'inactive')
        self.assertEqual(self.call('ensure')['data']['readiness'], 'inactive_on_branch')
        self.assertFalse((self.project / '.mask.json').exists())
        self.assertFalse((self.project / '.agents/skills/alpha').is_symlink())
        self.assertTrue(unrelated.is_dir())
        before = self.snapshot()
        self.assertFalse(self.call('ensure')['changed'])
        self.assertEqual(before, self.snapshot())
        self.git(self.project, 'switch', 'main')
        self.call('ensure')
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())

    def test_deletion_sparse_and_no_optin_preserve_links(self):
        (self.project / '.mask.json').unlink()
        (self.project / '.mask.lock.json').unlink()
        before = self.snapshot()
        self.call('ensure', code=4)
        self.assertEqual(before, self.snapshot())
        self.git(self.project, 'restore', '.mask.json', '.mask.lock.json')
        self.git(self.project, 'switch', 'inactive')
        self.git(self.project, 'config', 'core.sparseCheckout', 'true')
        self.call('ensure', code=4)
        self.git(self.project, 'config', 'core.sparseCheckout', 'false')
        self.call('integration', 'approve', '--project', self.project)
        self.call('ensure', code=4)
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())

    def test_crash_refuses_changed_branch_or_control_file(self):
        self.git(self.project, 'switch', 'inactive')
        self.crash('link')
        pending = json.loads((self.home / 'pending.json').read_text())
        self.assertEqual(pending['schema_version'], 3)
        self.git(self.project, 'switch', 'main')
        before = self.snapshot()
        self.call('recover', '--complete', code=8)
        self.assertEqual(before, self.snapshot())
        self.git(self.project, 'switch', 'inactive')
        self.call('recover', '--rollback')
        self.git(self.project, 'switch', 'main')
        self.declare_pinned(['beta'])
        self.pinned_controls([])  # Resolve before the crash: exact artifact preparation refuses while a journal is pending.
        self.crash('intent')
        self.declare_pinned([])
        self.call('recover', '--complete', code=8)
        self.declare_pinned(['beta'])
        self.call('recover', '--complete')

    def test_inactive_cleanup_recovery_does_not_require_removed_packages(self):
        self.git(self.project, 'switch', 'inactive')
        # The package leaves the tap: the author renames it away, publishes, and MASK fetches the new tap head.
        # The fetch precedes the crash because a named fetch refuses while a journal is pending.
        (self.source / 'skills/alpha').rename(self.source / 'skills/removed-alpha')
        self.publish('remove alpha')
        self.call('source', 'fetch', TAP)
        self.crash('link')
        self.call('recover', '--complete')
        self.assertFalse((self.project / '.agents/skills/alpha').is_symlink())
        self.assertFalse((self.project / '.claude/skills/alpha').is_symlink())
        self.assertEqual(self.call('ensure')['data']['readiness'], 'inactive_on_branch')

    def test_recovery_checks_authority_and_root_identity(self):
        self.git(self.project, 'switch', 'inactive')
        self.crash('intent')
        # Simulate an external control edit while the journal is pending.
        path = self.home / 'integration.json'
        original = path.read_bytes()
        path.write_text(json.dumps(dict(schema_version=1, approvals={})))
        self.call('recover', '--complete', code=8)
        path.write_bytes(original)
        self.call('recover', '--complete')

    def test_unrelated_commit_is_noop_and_conflicted_declaration_blocks(self):
        before = self.snapshot()
        self.git(self.project, 'commit', '--allow-empty', '-m', 'unrelated')
        self.assertFalse(self.call('ensure')['changed'])
        self.assertEqual(before, self.snapshot())
        self.git(self.project, 'switch', '-c', 'other')
        self.declare_pinned(['beta'])
        self.git(self.project, 'commit', '-am', 'other declaration')
        self.git(self.project, 'switch', 'main')
        self.declare_pinned([])
        self.git(self.project, 'commit', '-am', 'main declaration')
        run = subprocess.run(['git', '-C', str(self.project), 'merge', 'other'], capture_output=True)
        self.assertNotEqual(run.returncode, 0)
        self.declare_pinned(['alpha'])  # Valid bytes do not resolve the conflicted index.
        before = self.snapshot()
        self.call('ensure', code=4)
        self.assertEqual(before, self.snapshot())

    def test_unavailable_worktree_is_not_automatically_forgotten(self):
        linked = self.base / 'linked ü'
        self.git(self.project, 'worktree', 'add', '-b', 'linked', str(linked))
        self.call('integration', 'approve', '--project', linked)
        self.call('ensure', '--project', linked)
        identity = self.call('integration', 'inspect', '--project', linked)['data']['registration_identity']
        moved = self.base / 'missing-mount'
        linked.rename(moved)
        self.call('workspace', 'forget', linked, '--expect-identity', identity, code=4)
        moved.rename(linked)
        # Remove the fixture through Git, after explicitly unregistering links.
        self.call('project', 'unregister', linked)
        self.call('project', 'register', linked)
        self.git(self.project, 'worktree', 'remove', str(linked))
        self.call('workspace', 'forget', linked, '--expect-identity', 'wrong', code=4)
        self.call('workspace', 'forget', linked, '--expect-identity', identity)
        state = json.loads((self.home / 'state.json').read_text())
        self.assertNotIn(str(linked), state['projects'])
