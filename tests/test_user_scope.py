import json
import os
from pathlib import Path
import subprocess
import sys

from tests.support import ENTRY, Fixture
from tests.test_git_update import UpdateTests


class UserScopeTests(Fixture):
    """Legacy live-checkout starting state until MASK-0100/0102 retires this behavior (v1 personal-scope engine)."""
    def setUp(self):
        super().setUp()
        self.legacy_init()
        self.personal = self.base / 'personal ü home'
        self.personal.mkdir()

    def register_user(self, *skills, apply=False):
        self.call('user', 'init')
        if skills:
            self.call('user', 'require', *skills)
        args = ['user', 'register', '--user-home', self.personal]
        if apply:
            args.append('--apply')
        preview = self.call(*args, '--dry-run')
        return self.call(*args, '--expect-plan-hash', preview['data']['plan_hash'])

    def crash(self, label, *command):
        script = """
import sys, os
sys.path.insert(0, sys.argv[1])
import mask, mask_fs
mask_fs.checkpoint = lambda label: os._exit(99) if label == sys.argv[2] else None
mask.main(sys.argv[3:])
"""
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), label,
                              *map(str, command), '--home', str(self.home), '--json'],
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 99, (run.stdout, run.stderr))

    def test_membership_targets_and_home_are_independent(self):
        self.declare(['beta'])
        self.call('project', 'register', self.project, '--apply')
        project_manifest = (self.project / '.mask.json').read_bytes()
        self.register_user('alpha')
        self.assertFalse((self.personal / '.mask.json').exists())
        self.assertFalse((self.personal / '.agents').exists())
        # Path.home() reads USERPROFILE on Windows and HOME on POSIX; move both to prove the registered home wins.
        different = str(self.base / 'different')
        shown = self.call('user', 'show', cwd=self.base, env={'HOME': different, 'USERPROFILE': different})['data']
        self.assertEqual(shown['root'], str(self.personal))
        self.assertEqual(shown['manifest_path'], str(self.home / 'user.json'))
        self.assertEqual(shown['scope'], 'user')
        self.call('apply', '--user', cwd=self.base)
        for adapter in ('.agents', '.claude'):
            self.assertEqual((self.personal / adapter / 'skills/alpha').resolve(), self.source / 'skills/alpha')
        self.call('user', 'require', 'beta', '--apply')
        self.call('user', 'unrequire', 'alpha', '--apply')
        self.call('user', 'set-targets', 'codex', '--apply')
        self.assertFalse((self.personal / '.claude/skills/beta').exists())
        self.call('user', 'set-targets', '--inherit', '--apply')
        self.call('user', 'set', '--clear', '--apply')
        self.assertFalse((self.personal / '.agents/skills/beta').exists())
        self.assertEqual((self.project / '.mask.json').read_bytes(), project_manifest)
        self.assertTrue((self.project / '.agents/skills/beta').is_symlink())
        before = self.snapshot()
        self.assertFalse(self.call('user', 'set', '--clear', '--apply')['changed'])
        self.assertFalse(self.call('apply', '--user')['changed'])
        self.assertEqual(before, self.snapshot())

    def test_scope_selection_and_parser(self):
        self.declare(['beta'])
        self.call('project', 'register', self.project)
        self.register_user('alpha')
        self.call('apply')
        self.assertFalse((self.personal / '.agents').exists())
        plan = self.call('plan', '--all')['data']
        self.assertEqual(len(plan['projects']), 1)
        self.assertEqual(len(plan['users']), 1)
        self.call('apply', '--all')
        self.assertTrue(self.call('doctor', '--all', '--check')['data']['healthy'])
        self.assertEqual(len(self.call('project', 'list')['data']['projects']), 1)
        for args in [('apply', '--user', '--all'), ('plan', '--user', '--project', self.project),
                     ('doctor', '--user', '--all'), ('user', 'set'), ('user', 'set-targets'),
                     ('link', 'adopt', '--skill', 'alpha', '--target', 'codex', '--expect-source', self.source)]:
            self.call(*args, code=2)
        caps = self.call('capabilities')['data']
        # A bumped write schema must stay readable; asserting only a literal let state v3 drift unnoticed.
        for name, version in caps['schemas'].items():
            if name in caps['readable_versions']:
                self.assertIn(version, caps['readable_versions'][name], name)
        self.assertEqual(caps['readable_versions']['state'], [1, 2, 3])
        self.assertIn('user.require', {item['name'] for item in caps['commands']})

    def test_collision_preflights_both_scopes_and_manifest_edit(self):
        self.declare(['beta'])
        self.call('project', 'register', self.project)
        self.register_user('alpha')
        leaf = self.personal / '.agents/skills/alpha'
        leaf.mkdir(parents=True)
        (leaf / 'mine').write_text('preserve')
        before = self.snapshot()
        self.assertEqual(self.call('apply', '--all', code=4)['error']['code'], 'target.collision')
        self.call('user', 'require', 'beta', '--apply', code=4)
        self.assertEqual(before, self.snapshot())

    def test_linked_parent_and_cross_scope_overlap_refuse(self):
        target = self.base / 'external'
        target.mkdir()
        (self.personal / '.agents').symlink_to(target, target_is_directory=True)
        self.call('user', 'init')
        before = self.snapshot()
        self.assertEqual(self.call('user', 'register', '--user-home', self.personal, code=4)['error']['code'], 'target.parent_link')
        self.assertEqual(before, self.snapshot())
        (self.personal / '.agents').unlink()
        self.register_user('alpha')
        self.call('project', 'init', '--project', self.personal)
        self.assertEqual(self.call('project', 'register', self.personal, code=4)['error']['code'], 'target.overlap')
        nested = self.personal / '.agents/skills/nested'
        nested.mkdir(parents=True)
        self.call('project', 'init', '--project', nested)
        self.assertEqual(self.call('project', 'register', nested, code=4)['error']['code'], 'target.overlap')
        self.call('user', 'register', '--user-home', self.project, code=4)

    def test_stale_preview_and_observational_reads(self):
        self.register_user('alpha')
        before = self.snapshot()
        preview = self.call('plan', '--user')
        self.call('user', 'show')
        self.call('doctor', '--user')
        self.call('apply', '--user', '--dry-run')
        self.assertEqual(before, self.snapshot())
        (self.source / 'skills/alpha/reference.txt').write_text('new supporting bytes')
        before = self.snapshot()
        self.assertEqual(self.call('apply', '--user', '--expect-plan-hash', preview['data']['plan_hash'], code=4)['error']['code'], 'plan.stale')
        self.assertEqual(before, self.snapshot())

    def test_v1_no_rewrite_upgrade_and_exact_rollback(self):
        original = (self.home / 'state.json').read_bytes()
        self.call('user', 'init')
        self.call('user', 'show')
        self.assertEqual(original, (self.home / 'state.json').read_bytes())
        self.crash('state', 'user', 'register', '--user-home', self.personal)
        pending = self.call('recover', '--inspect')['data']['pending']
        self.assertEqual(pending['schema_version'], 2)
        self.assertEqual(pending['before_state']['schema_version'], 1)
        self.call('recover', '--rollback')
        self.assertEqual(original, (self.home / 'state.json').read_bytes())
        self.assertTrue((self.home / 'user.json').is_file())
        self.crash('intent', 'user', 'register', '--user-home', self.personal)
        self.call('recover', '--complete')
        self.assertEqual(json.loads((self.home / 'state.json').read_text())['schema_version'], 2)

    def test_mixed_scope_crash_and_user_manifest_recovery(self):
        self.declare(['beta'])
        self.call('project', 'register', self.project)
        self.register_user('alpha')
        self.crash('link', 'apply', '--all')
        self.call('recover', '--complete')
        self.assertTrue(self.call('doctor', '--all', '--check')['data']['healthy'])
        original = (self.home / 'user.json').read_bytes()
        self.crash('manifest', 'user', 'require', 'beta', '--apply')
        self.call('recover', '--rollback')
        self.assertEqual(original, (self.home / 'user.json').read_bytes())
        self.assertFalse((self.personal / '.agents/skills/beta').exists())
        self.assertTrue((self.project / '.agents/skills/beta').is_symlink())

    def test_recovery_preserves_user_manifest_and_replaced_link(self):
        self.register_user('alpha', apply=True)
        self.crash('manifest', 'user', 'require', 'beta', '--apply')
        (self.home / 'user.json').write_text('{"schema_version":1,"skills":[]}\n')
        before = self.snapshot()
        self.call('recover', '--rollback', code=8)
        self.assertEqual(before, self.snapshot())

    def test_adopt_unregister_keep_links_and_unavailable_home(self):
        self.register_user('alpha')
        leaf = self.personal / '.agents/skills/alpha'
        leaf.parent.mkdir(parents=True)
        leaf.symlink_to(self.source / 'skills/alpha', target_is_directory=True)
        args = ('link', 'adopt', '--user', '--skill', 'alpha', '--target', 'codex', '--expect-source', self.source / 'skills/alpha')
        preview = self.call(*args, '--dry-run')
        self.call(*args, '--expect-plan-hash', preview['data']['plan_hash'])
        self.call('apply', '--user')
        self.call('user', 'unregister')
        self.assertFalse(leaf.is_symlink())
        self.assertEqual(self.call('user', 'show')['data']['manifest']['skills'], ['alpha'])
        self.register_user('alpha', apply=True)
        moved = self.base / 'moved-home'
        self.personal.rename(moved)
        self.call('apply', '--user', code=4)
        self.call('user', 'unregister', '--keep-links')
        self.assertTrue((moved / '.agents/skills/alpha').is_symlink())
        self.assertEqual(self.call('plan', '--user', code=4)['error']['code'], 'user.not_registered')


class UserUpdateTests(UpdateTests):
    """Run existing update scenarios with a second, independently declared consumer.

    Legacy live-checkout starting state until MASK-0101 retires this behavior (shared-checkout update).
    """
    def setUp(self):
        super().setUp()
        self.personal = self.base / 'personal'
        self.personal.mkdir()
        self.call('user', 'init')
        self.call('user', 'require', 'beta')
        self.call('user', 'register', '--user-home', self.personal, '--apply')

    def test_user_only_candidate_is_validated(self):
        self.git(self.author, 'rm', '-r', 'skills/beta')
        self.git(self.author, 'commit', '-m', 'remove personal requirement')
        self.git(self.author, 'push', 'origin', 'main')
        previous = self.git(self.source, 'rev-parse', 'HEAD')
        self.assertEqual(self.call('update', code=4)['error']['code'], 'source.candidate_invalid')
        self.assertEqual(self.git(self.source, 'rev-parse', 'HEAD'), previous)
        self.assertTrue((self.personal / '.agents/skills/beta').is_dir())

    def test_unavailable_user_blocks_before_fetch(self):
        self.personal.rename(self.base / 'moved-personal')
        self.push_upstream()
        before = self.snapshot()
        self.call('update', code=4)
        self.assertEqual(before, self.snapshot())
