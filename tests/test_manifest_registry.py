import json

import mask_core as c
from tests.support import TAP, Fixture


class ManifestRegistryTests(Fixture):
    def test_preinit_nested_discovery_and_explicit_root(self):
        self.call('project', 'init')
        child = self.project / 'nested'; child.mkdir()
        self.assertEqual(self.call('project', 'show', cwd=child)['data']['root'], str(self.project))
        self.call('project', 'show', '--project', child, code=3)
        self.assertFalse(self.home.joinpath('config.json').exists())

    def test_alias_registration_and_unavailable_entries(self):
        self.init(); self.declare_pinned()
        self.call('project', 'register', self.project)
        alias = self.base / 'alias'; alias.symlink_to(self.project, target_is_directory=True)
        before = self.snapshot()
        self.assertFalse(self.call('project', 'register', alias)['changed'])
        self.assertEqual(before, self.snapshot())
        moved = self.base / 'moved'; self.project.rename(moved)
        rows = self.call('project', 'list', cwd=self.base)['data']['projects']
        self.assertEqual(len(rows), 1); self.assertFalse(rows[0]['available'])
        self.call('project', 'unregister', self.project, '--keep-links', cwd=self.base)
        self.assertTrue((moved / '.mask.json').exists())

    def test_worktrees_are_independent(self):
        self.init(); self.declare_pinned(skills=())
        self.git(self.project, 'config', 'user.name', 'Fixture'); self.git(self.project, 'config', 'user.email', 'fixture@example.invalid')
        self.git(self.project, 'add', '.mask.json', '.mask.lock.json'); self.git(self.project, 'commit', '-m', 'declaration')
        other = self.base / 'worktree'
        self.git(self.project, 'worktree', 'add', '-b', 'lane', str(other))
        self.call('project', 'register', self.project); self.call('project', 'register', other)
        self.assertEqual(len(self.call('project', 'list')['data']['projects']), 2)

    def test_show_observes_deployment_without_writing(self):
        self.init(); self.declare_pinned(); self.call('project', 'register', self.project)
        before = self.snapshot()
        data = self.call('project', 'show')['data']
        self.assertTrue(data['source']['fingerprint'].startswith('sha256:'))
        self.assertEqual(len(data['expected_links']), 2)
        self.assertTrue(all(entry['type'] == 'missing' for entry in data['actual_links']))
        self.assertEqual(before, self.snapshot())


class SelectionMembershipTests(Fixture):
    """v2 membership changes through install and remove; the retired v1 require/unrequire/set string mutations refuse."""
    def setUp(self):
        super().setUp(); self.init()

    def selected(self):
        return [row['id'] for row in c.read_json(self.project / '.mask.json')['skills']]

    def test_install_remove_membership_and_exact_set_noop(self):
        self.install('alpha'); self.install('beta')
        self.assertEqual(self.selected(), ['alpha', 'beta'])
        before = self.snapshot()
        repeated = self.install('alpha', 'beta')
        self.assertFalse(repeated['changed'])
        self.assertEqual(sorted(repeated['data']['already']), [TAP + '/alpha', TAP + '/beta'])
        self.assertEqual(before, self.snapshot())
        removed = self.call('remove', 'alpha', 'missing', '--project', self.project)
        self.assertEqual(removed['data']['removed'], [TAP + '/alpha'])
        self.assertIn('selection.not_selected', [warning['code'] for warning in removed['warnings']])
        self.assertEqual(self.selected(), ['beta'])
        self.assertFalse((self.project / '.agents/skills/alpha').is_symlink())
        self.assertTrue((self.project / '.agents/skills/beta').is_symlink())
        self.call('remove', 'beta', '--project', self.project)
        self.assertEqual(self.selected(), [])
        self.assertFalse((self.project / '.agents/skills/beta').is_symlink())

    def test_preview_guard_and_no_partial_apply(self):
        self.declare_pinned(skills=())
        self.call('source', 'fetch', TAP)
        before = self.snapshot()
        preview = self.call('install', 'alpha', '--project', self.project, '--dry-run')
        self.assertTrue(preview['would_change'])
        self.assertEqual(before, self.snapshot())
        stale = self.call('install', 'alpha', '--project', self.project, '--expect-plan-hash', 'sha256:' + '0' * 64, code=4)
        self.assertEqual(stale['error']['code'], 'plan.stale')
        # Neither the declaration, the lock, the registry nor a link changed.
        self.assertEqual(before, self.snapshot())
        self.call('install', 'alpha', '--project', self.project, '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertEqual(self.selected(), ['alpha'])
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())

    def test_retired_string_mutations_refuse_without_writing(self):
        self.declare_pinned()
        mutations = (('project', 'require', 'beta'), ('project', 'unrequire', 'alpha'), ('project', 'set', '--clear'))
        for args in mutations:
            with self.subTest(declaration=2, args=args):
                before = self.snapshot()
                self.assertEqual(self.call(*args, code=4)['error']['code'], 'selection.command_unsupported')
                self.assertEqual(before, self.snapshot())
        (self.project / '.mask.json').write_text(json.dumps(dict(schema_version=1, skills=['alpha'])) + '\n')
        (self.project / '.mask.lock.json').unlink()
        for args in mutations:
            with self.subTest(declaration=1, args=args):
                before = self.snapshot()
                self.assertEqual(self.call(*args, code=4)['error']['code'], 'migration.required')
                self.assertEqual(before, self.snapshot())
