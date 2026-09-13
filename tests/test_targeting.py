import json
from unittest.mock import patch

import mask
import mask_core as c
import mask_selection as selection
from tests.support import TAP, Fixture

ALPHA = TAP + '/alpha'


def remove_tree(path):
    import shutil
    for leaf in path.rglob("*"):
        if leaf.is_file() and not leaf.is_symlink():
            leaf.chmod(0o600)
    shutil.rmtree(path)


class TargetingTests(Fixture):
    def setUp(self):
        super().setUp()
        self.init()
        self.install('alpha')
        self.call('project', 'set-targets', '--inherit', '--apply')

    def test_independent_agents_inheritance_noop_and_declaration_only(self):
        personal = self.base / 'personal'
        personal.mkdir()
        (self.home / 'user.json').write_bytes((self.project / '.mask.json').read_bytes())
        (self.home / 'user.lock.json').write_bytes((self.project / '.mask.lock.json').read_bytes())
        self.call('user', 'register', '--user-home', personal, '--apply')
        original_lock = c.read_json(self.project / '.mask.lock.json')['packages']
        self.call('project', 'set-agents', ALPHA, 'codex')
        self.assertTrue((self.project / '.claude/skills/alpha').is_symlink())
        self.call('apply')
        self.assertFalse((self.project / '.claude/skills/alpha').exists())
        self.assertTrue((personal / '.claude/skills/alpha').is_symlink())
        self.call('user', 'set-agents', ALPHA, 'claude', '--apply')
        self.assertFalse((personal / '.agents/skills/alpha').exists())
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())
        self.assertEqual(original_lock, c.read_json(self.project / '.mask.lock.json')['packages'])
        before = self.snapshot()
        self.assertFalse(self.call('project', 'set-agents', ALPHA, 'codex', '--apply')['changed'])
        self.assertEqual(before, self.snapshot())
        self.call('project', 'set-agents', ALPHA, '--inherit', '--apply')
        self.assertNotIn('agents', c.read_json(self.project / '.mask.json')['skills'][0])
        self.assertTrue((self.project / '.claude/skills/alpha').is_symlink())

    def test_registered_boundary_collision_preview_and_stale_policy(self):
        other = self.base / 'unregistered'
        other.mkdir()
        (other / '.mask.json').write_bytes((self.project / '.mask.json').read_bytes())
        (other / '.mask.lock.json').write_bytes((self.project / '.mask.lock.json').read_bytes())
        self.assertEqual(self.call('project', 'set-agents', ALPHA, 'codex', '--project', other, code=4)['error']['code'], 'project.not_registered')
        self.call('project', 'set-agents', ALPHA, 'codex', '--apply')
        leaf = self.project / '.claude/skills/alpha'
        leaf.mkdir()
        (leaf / 'mine').write_text('preserve')
        before = self.snapshot()
        self.call('project', 'set-agents', ALPHA, '--all', '--apply', code=4)
        self.assertEqual(before, self.snapshot())
        (leaf / 'mine').unlink()
        leaf.rmdir()
        preview = self.call('project', 'set-agents', ALPHA, '--all', '--apply', '--dry-run')
        self.call('selection-policy', 'set', '--agent', 'codex')
        self.call('project', 'set-agents', ALPHA, '--all', '--apply', '--expect-plan-hash', preview['data']['plan_hash'], code=4)
        self.assertEqual(c.read_json(self.project / '.mask.json')['skills'][0]['agents'], ['codex'])

    def test_false_when_skips_cold_package_and_preserves_lock(self):
        declaration = c.read_json(self.project / '.mask.json')
        declaration['skills'][0]['when'] = {'platforms': ['windows' if selection.device()['platform'] != 'windows' else 'linux']}
        (self.project / '.mask.json').write_text(json.dumps(declaration))
        self.call('source', 'fetch', TAP)
        self.call('update', '--project', self.project)
        remove_tree(self.home / 'store')
        remove_tree(self.home / 'sources')
        before = self.snapshot()
        lock = (self.project / '.mask.lock.json').read_bytes()
        result = self.call('apply', '--dry-run')
        self.assertEqual(before, self.snapshot())
        self.assertEqual(result['data']['outcomes'][0]['status'], 'not_applicable')
        self.call('apply')
        self.assertFalse((self.home / 'store').exists())
        self.assertFalse((self.home / 'sources').exists())
        self.assertEqual(lock, (self.project / '.mask.lock.json').read_bytes())

    def test_global_enabled_policy_and_physical_cas(self):
        other = self.base / 'other'
        other.mkdir()
        for name in ('.mask.json', '.mask.lock.json'):
            (other / name).write_bytes((self.project / name).read_bytes())
        self.call('project', 'register', '--project', other, '--apply')
        before = self.snapshot()
        preview = self.call('selection-policy', 'set', '--agent', 'codex', '--dry-run')
        self.assertEqual(before, self.snapshot())
        self.assertEqual(set(preview['data']['affected_scopes']), {str(other), str(self.project)})
        self.call('selection-policy', 'set', '--agent', 'codex', '--expect-plan-hash', preview['data']['plan_hash'])
        for root in (other, self.project):
            self.assertFalse((root / '.claude/skills/alpha').exists())
        self.assertFalse(self.call('selection-policy', 'set', '--agent', 'codex')['changed'])
        self.call('selection-policy', 'clear')
        self.assertFalse((self.home / 'selection-policy.json').exists())
        parser, leaves = mask.make_parser()
        args = parser.parse_args(['selection-policy', 'set', '--agent', 'codex', '--home', str(self.home)])
        output = mask.result('selection-policy.set')
        import mask_store as store
        original = store.ensure
        def changed(*args, **kwargs):
            value = original(*args, **kwargs)
            (self.home / 'selection-policy.json').write_text(c.text_json(selection.policy()))
            return value
        with patch.object(store, 'ensure', side_effect=changed), self.assertRaises(c.MaskError) as caught:
            mask.dispatch(args, output, leaves)
        self.assertEqual(caught.exception.code, 'plan.stale')
        self.assertTrue((self.project / '.claude/skills/alpha').is_symlink())


    def test_dangling_and_corrupt_artifacts_are_never_reported_deployed(self):
        remove_tree(self.home / 'store')
        before = self.snapshot()
        result = self.call('plan')
        self.assertEqual(before, self.snapshot())
        self.assertEqual({row['status'] for row in result['data']['outcomes']}, {'selected'})
        self.assertTrue(all(not row['target_verified'] for row in result['data']['outcomes']))
        self.call('source', 'fetch', TAP)
        self.call('apply')
        leaf = (self.project / '.agents/skills/alpha').resolve() / 'SKILL.md'
        leaf.chmod(0o600)
        leaf.write_text('corrupt')
        before = self.snapshot()
        result = self.call('plan')
        self.assertEqual(before, self.snapshot())
        self.assertTrue(result['data']['blockers'])
        self.assertFalse(any(row['status'] == 'deployed' for row in result['data']['outcomes']))


class PolicyRegistryTests(Fixture):
    """Selection policy on an empty registry and beside registered pinned consumers' explicit agents (ported from the v1 set-targets case)."""

    def test_empty_registry_policy_and_required_agents_remain_explicit(self):
        self.init()
        self.call('selection-policy', 'set', '--agent', 'codex')
        self.assertEqual(c.read_json(self.home / 'selection-policy.json')['enabled_agents'], ['codex'])
        self.call('selection-policy', 'clear')
        self.assertFalse((self.home / 'selection-policy.json').exists())
        # The project requires codex through a per-binding agent list; the personal scope requires claude through default_agents.
        self.install(ALPHA, agents=['codex'])
        self.install(TAP + '/beta', user=True)
        self.call('user', 'set-targets', 'claude', '--apply')
        self.call('selection-policy', 'set', '--agent', 'claude', '--agent', 'codex')
        for enabled, coordinate, required in (('claude', ALPHA, 'codex'), ('codex', TAP + '/beta', 'claude')):
            with self.subTest(enabled=enabled):
                before = self.snapshot()
                refused = self.call('selection-policy', 'set', '--agent', enabled, code=4)['error']
                self.assertEqual(refused['code'], 'compatibility.unsupported')
                self.assertEqual([(row['coordinate'], row['agent'], row['reason']) for row in refused['details']['outcomes']],
                                 [(coordinate, required, 'agent_disabled_by_policy')])
                self.assertEqual(before, self.snapshot())
        self.assertEqual(c.read_json(self.project / '.mask.json')['skills'][0]['agents'], ['codex'])
        self.assertEqual(c.read_json(self.home / 'user.json')['default_agents'], ['claude'])
        self.assertFalse((self.home / 'selection-policy.json').exists(), 'enabling every agent is the default policy, so nothing was written')
