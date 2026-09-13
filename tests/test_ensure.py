import json
import subprocess
import sys
from unittest.mock import patch

import mask_core as c
from tests.support import Fixture, ENTRY, TAP


class EnsureTests(Fixture):
    def setUp(self):
        super().setUp()
        self.init()
        self.call('source', 'fetch', TAP)
        self.declare_hydrated()

    def declare_hydrated(self, skills=('alpha',), root=None):
        """The shared v2 declaration and lock of the fixture tap plus its hydrated store artifacts; nothing is registered or linked.

        Hydration is part of the starting state, so a refused readiness call cannot pass off unlocked artifact
        preparation as a consumer effect. setUp has already fetched the tap.
        """
        locked = self.declare_pinned(skills, root, fetch=False)
        self.call('source', 'fetch', '--locked', '--offline', '--project', root or self.project)
        return locked

    def approve(self, *options):
        return self.call('integration', 'approve', '--project', self.project, *options)

    def test_authority_registration_check_and_noop(self):
        before = self.snapshot()
        refused = self.call('ensure', code=4)  # Manual JSON invocation: a typed proposal, never a prompt (MASK-0085).
        self.assertEqual(refused['error']['code'], 'confirmation.required')
        self.assertEqual(refused['data']['confirmation']['reason'], 'integration.approval_required')
        self.assertEqual(self.call('ensure', '--event', 'startup', code=4)['error']['code'], 'integration.approval_required')
        self.assertEqual(before, self.snapshot())
        preview = self.approve('--dry-run')
        self.assertEqual(before, self.snapshot())
        self.approve('--expect-plan-hash', preview['data']['plan_hash'])
        before = self.snapshot()
        self.call('ensure', '--check', code=7)
        self.assertEqual(before, self.snapshot())
        result = self.call('ensure', '--offline')
        self.assertTrue(result['changed'])
        self.assertEqual(result['data']['readiness'], 'ready_pinned')
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())
        before = self.snapshot()
        self.assertFalse(self.call('ensure')['changed'])
        self.call('ensure', '--check')
        self.assertEqual(before, self.snapshot())
        self.call('integration', 'revoke', '--project', self.project)
        before = self.snapshot()
        self.call('ensure', '--event', 'startup', code=4)
        noop = self.call('ensure')  # Already usable: no-op needs no consent, but automatic readiness is reported as not approved.
        self.assertFalse(noop['changed'])
        self.assertEqual(noop['data']['approval'], 'not_approved')
        self.assertEqual(before, self.snapshot())
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
        self.assertEqual(self.call('ensure', cwd=nested, code=4)['error']['code'], 'manifest.missing')
        self.assertEqual(self.call('ensure', '--event', 'post-commit', cwd=nested, code=4)['error']['code'], 'integration.approval_required')
        ordinary = self.base / 'ordinary'
        ordinary.mkdir()
        self.declare_hydrated(['beta'], root=ordinary)
        self.call('integration', 'approve', '--project', ordinary)
        self.call('ensure', '--project', ordinary)
        self.assertTrue((ordinary / '.agents/skills/beta').is_symlink())

    def test_linked_worktrees_and_root_replacement(self):
        self.git(self.project, 'config', 'user.name', 'Fixture')
        self.git(self.project, 'config', 'user.email', 'fixture@example.invalid')
        self.git(self.project, 'add', '.mask.json', '.mask.lock.json')
        self.git(self.project, 'commit', '-m', 'declaration')
        self.approve('--linked-worktrees')
        linked = self.base / 'linked'
        self.git(self.project, 'worktree', 'add', '-b', 'linked', str(linked))
        self.call('ensure', cwd=linked)
        self.assertTrue((linked / '.agents/skills/alpha').is_symlink())
        moved = self.base / 'original'
        self.project.rename(moved)
        self.project.mkdir()
        self.declare_hydrated()
        self.call('ensure', '--project', self.project, code=4)

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

    def test_repository_clone_boundary_identity_and_revocation(self):
        self.git(self.project, 'config', 'user.name', 'Fixture')
        self.git(self.project, 'config', 'user.email', 'fixture@example.invalid')
        self.git(self.project, 'add', '.mask.json', '.mask.lock.json')
        self.git(self.project, 'commit', '-m', 'declaration')
        boundary = self.base / 'clones'
        boundary.mkdir()
        self.call('integration', 'approve', '--repository', str(self.project), '--under', boundary)
        clone = boundary / 'approved'
        self.git(self.base, 'clone', str(self.project), str(clone))
        self.call('ensure', '--project', clone)
        self.assertTrue((clone / '.agents/skills/alpha').is_symlink())
        self.call('integration', 'revoke', '--project', clone, code=4)
        outside = self.base / 'outside'
        self.git(self.base, 'clone', str(self.project), str(outside))
        self.assertEqual(self.call('ensure', '--project', outside, code=4)['error']['code'], 'confirmation.required')
        self.assertEqual(self.call('ensure', '--project', outside, '--event', 'post-checkout', code=4)['error']['code'], 'integration.approval_required')
        self.git(clone, 'remote', 'set-url', 'origin', str(self.source))
        self.assertEqual(self.call('ensure', '--project', clone)['data']['approval'], 'not_approved')
        self.git(clone, 'remote', 'set-url', 'origin', str(self.project))
        self.call('integration', 'revoke', '--repository', str(self.project), '--under', boundary)
        self.assertEqual(self.call('ensure', '--project', clone, '--event', 'startup', code=4)['error']['code'], 'integration.approval_required')

    def test_replaced_clone_boundary_and_credential_identity_refuse(self):
        boundary = self.base / 'clones'
        boundary.mkdir()
        self.call('integration', 'approve', '--repository', str(self.source), '--under', boundary)
        boundary.rename(self.base / 'old-boundary')
        boundary.mkdir()
        clone = boundary / 'new'
        self.git(self.base, 'clone', str(self.source), str(clone))
        self.declare_hydrated(root=clone)
        self.call('ensure', '--project', clone, code=4)
        result = self.call('integration', 'approve', '--repository', 'https://user:secret@example.invalid/org/repo', '--under', boundary, code=3)
        self.assertNotIn('secret', json.dumps(result))
        self.call('integration', 'approve', '--repository', str(self.source), '--project', self.project, '--under', boundary, code=2)

    def register_user(self):
        # The public install task registers and deploys the personal consumer at the redirected personal home.
        return self.install('alpha', user=True)

    def test_explicit_scope_selects_the_personal_consumer_or_every_consumer(self):
        self.assertEqual(self.call('ensure', '--user', code=4)['error']['code'], 'user.not_registered')
        personal = self.personal
        self.register_user()
        # --user reconciles the personal consumer alone, from inside an unrelated project directory.
        result = self.call('ensure', '--user')
        self.assertEqual([row['root'] for row in result['data']['scope_readiness']], [str(personal)])
        self.assertTrue((personal / '.agents/skills/alpha').is_symlink())
        self.assertFalse((self.project / '.agents/skills/alpha').exists())
        # --all covers every registered consumer, and each project still needs its own authority.
        self.call('project', 'register', self.project)
        refused = self.call('ensure', '--all', code=4)
        self.assertEqual(refused['error']['code'], 'confirmation.required')
        self.assertEqual(refused['data']['confirmation']['reason'], 'integration.approval_required')
        preview = self.approve('--dry-run')
        self.approve('--expect-plan-hash', preview['data']['plan_hash'])
        result = self.call('ensure', '--all')
        self.assertEqual(sorted(row['root'] for row in result['data']['scope_readiness']), sorted([str(personal), str(self.project)]))
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())
        self.assertFalse(self.call('ensure', '--all')['changed'])
        # An explicit selection is exclusive and never falls back to the working directory.
        for conflict in (('--all', '--user'), ('--all', '--project', str(self.project)), ('--user', '--project', str(self.project))):
            self.assertEqual(self.call('ensure', *conflict, code=2)['error']['code'], 'invocation.invalid')

    def test_readiness_reads_only_the_selected_packages(self):
        # The tap offers alpha and beta; readiness for this alpha consumer verifies, resolves and materializes alpha alone,
        # and never runs git status (the retired live-checkout scan).
        import mask
        import mask_resolve as r
        import mask_store as store
        self.approve()
        parser, leaves = mask.make_parser()
        args = parser.parse_args(['ensure', '--offline', '--project', str(self.project), '--home', str(self.home)])
        output = mask.result('ensure')
        with patch.object(store, 'verify_tree', wraps=store.verify_tree) as trees, patch.object(store, 'materialize', wraps=store.materialize) as materialized, \
                patch.object(r, 'verify_resolution', wraps=r.verify_resolution) as resolutions, patch.object(c, 'git', wraps=c.git) as git:
            mask.dispatch(args, output, leaves)
        self.assertEqual(output['data']['readiness'], 'ready_pinned')
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())
        packages = [value['id'] for mock in (trees, materialized, resolutions) for call in mock.call_args_list
                    for value in (*call.args, *call.kwargs.values()) if isinstance(value, dict) and 'payload_digest' in value]
        self.assertIn('alpha', packages)
        self.assertEqual(set(packages), {'alpha'})
        self.assertFalse(any(len(call.args) > 1 and call.args[1] == 'status' for call in git.call_args_list))
