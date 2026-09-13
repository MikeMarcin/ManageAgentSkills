import json
from pathlib import Path
from tests.support import TAP, Fixture


def declare_pinned(fixture, root=None, skills=('alpha',), fetch=True):
    """Write a v2 declaration of the fixture tap and lock it from the fetched cache, without registering or deploying it.

    The tap-first counterpart of declare() before project register; a candidate for tests.support.
    """
    root = root or fixture.project
    declaration = dict(schema_version=2, sources=fixture.binding() if skills else {}, skills=[dict(source=TAP, id=identifier) for identifier in skills])
    (root / '.mask.json').write_text(json.dumps(declaration) + '\n')
    if fetch and skills:
        fixture.call('source', 'fetch', TAP)
    return fixture.call('lock', '--project', root)


class ManifestRegistryTests(Fixture):
    def test_preinit_nested_discovery_and_explicit_root(self):
        self.call('project', 'init')
        child = self.project / 'nested'; child.mkdir()
        self.assertEqual(self.call('project', 'show', cwd=child)['data']['root'], str(self.project))
        self.call('project', 'show', '--project', child, code=3)
        self.assertFalse(self.home.joinpath('config.json').exists())

    def test_alias_registration_and_unavailable_entries(self):
        self.init(); declare_pinned(self)
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
        self.init(); declare_pinned(self, skills=())
        self.git(self.project, 'config', 'user.name', 'Fixture'); self.git(self.project, 'config', 'user.email', 'fixture@example.invalid')
        self.git(self.project, 'add', '.mask.json', '.mask.lock.json'); self.git(self.project, 'commit', '-m', 'declaration')
        other = self.base / 'worktree'
        self.git(self.project, 'worktree', 'add', '-b', 'lane', str(other))
        self.call('project', 'register', self.project); self.call('project', 'register', other)
        self.assertEqual(len(self.call('project', 'list')['data']['projects']), 2)

    def test_show_observes_deployment_without_writing(self):
        self.init(); declare_pinned(self); self.call('project', 'register', self.project)
        before = self.snapshot()
        data = self.call('project', 'show')['data']
        self.assertTrue(data['source']['fingerprint'].startswith('sha256:'))
        self.assertEqual(len(data['expected_links']), 2)
        self.assertTrue(all(entry['type'] == 'missing' for entry in data['actual_links']))
        self.assertEqual(before, self.snapshot())


class LegacyManifestRegistryTests(Fixture):
    """Legacy live-checkout starting state until MASK-0100 retires this behavior (v1 project require/unrequire/set)."""
    def test_incremental_exact_set_clear_targets_noop(self):
        self.legacy_init(); self.call('project', 'init')
        self.call('project', 'require', 'alpha'); self.call('project', 'require', 'beta')
        before = self.snapshot()
        self.assertFalse(self.call('project', 'require', 'beta')['changed'])
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.call('project', 'show')['data']['manifest']['skills'], ['alpha', 'beta'])
        self.call('project', 'unrequire', 'alpha', 'missing')
        self.assertEqual(self.call('project', 'show')['data']['manifest']['skills'], ['beta'])
        self.call('project', 'set', '--skill', 'alpha')
        self.call('project', 'set-targets', 'codex')
        self.assertEqual(self.call('project', 'show')['data']['effective_targets'], ['codex'])
        self.call('project', 'set-targets', '--inherit')
        self.call('project', 'set', '--clear')
        self.assertEqual(self.call('project', 'show')['data']['manifest']['skills'], [])

    def test_preview_guard_and_no_partial_apply(self):
        self.legacy_init(); self.declare()
        # legacy_init writes bytes without running MASK; the retired init --source also left MASK_HOME/operation.lock,
        # which the first locked command creates. A locked public no-op restores that starting state before observing.
        self.assertFalse(self.call('config', 'set', '--git-timeout', '30')['changed'])
        before = self.snapshot()
        preview = self.call('project', 'require', 'beta', '--dry-run')
        self.assertEqual(before, self.snapshot())
        self.call('project', 'require', 'beta', '--apply', code=4)
        self.call('project', 'require', 'beta', '--expect-plan-hash', 'bad', code=4)
        self.assertEqual(before, self.snapshot())
        self.call('project', 'require', 'beta', '--expect-plan-hash', preview['data']['plan_hash'])
