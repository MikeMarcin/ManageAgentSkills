import copy
import json
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import mask
import mask_core as c
import mask_fs as fs
import mask_pinned as pinned
import mask_store as store
from tests.support import Fixture, ENTRY


class MigrationTests(Fixture):
    """Legacy live-checkout starting state until MASK-0100/0102 retires this behavior (migrate --to-pinned)."""
    def setUp(self):
        super().setUp()
        self.legacy_init()
        self.declare()
        self.call('project', 'register', '--apply')

    def crash(self, label):
        script = "import os,sys;sys.path.insert(0,sys.argv[1]);import mask,mask_fs;mask_fs.checkpoint=lambda label: os._exit(99) if label==sys.argv[2] else None;mask.main(sys.argv[3:])"
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), label, 'migrate', '--to-pinned', '--project', str(self.project), '--home', str(self.home), '--json'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 99, run.stdout + run.stderr)

    def test_project_migration_preview_targets_and_unselected_preservation(self):
        other = self.base / 'other'
        other.mkdir()
        (other / '.mask.json').write_text(json.dumps(dict(schema_version=1, skills=['beta'])))
        self.call('project', 'register', '--project', other, '--apply')
        original = c.read_json(self.home / 'state.json')['projects'][str(other)]
        before = self.snapshot()
        preview = self.call('migrate', '--to-pinned', '--dry-run')
        self.assertEqual(before, self.snapshot())
        self.call('migrate', '--to-pinned', '--expect-plan-hash', preview['data']['plan_hash'])
        state = c.state(c.read_json(self.home / 'state.json'))
        self.assertEqual(state['schema_version'], 3)
        self.assertEqual(state['projects'][str(other)], original)
        record = state['projects'][str(self.project)]
        self.assertEqual(record['last_manifest']['default_agents'], ['claude', 'codex'])
        leaf = self.project / '.agents/skills/alpha'
        self.assertIn('/store/v1/', fs.normalized_link(leaf, os.readlink(leaf)).as_posix())
        self.assertFalse(self.call('apply')['changed'])

    def test_exact_rollback_at_typed_effects_and_completion(self):
        baseline = {name: (self.home / name).read_bytes() for name in ('config.json', 'state.json')}
        declaration = (self.project / '.mask.json').read_bytes()
        old = os.readlink(self.project / '.agents/skills/alpha')
        for label in ('intent', 'link_unlinked', 'manifest', 'lock', 'config', 'state'):
            with self.subTest(label=label):
                self.crash(label)
                self.call('recover', '--rollback')
                self.assertEqual(baseline, {name: (self.home / name).read_bytes() for name in baseline})
                self.assertEqual(declaration, (self.project / '.mask.json').read_bytes())
                self.assertFalse((self.project / '.mask.lock.json').exists())
                self.assertEqual(old, os.readlink(self.project / '.agents/skills/alpha'))
        self.crash('config')
        self.call('recover', '--complete')
        self.assertFalse(self.call('apply')['changed'])

    def test_user_and_mixed_all_migration(self):
        user = self.base / 'personal'
        user.mkdir()
        self.call('user', 'init')
        self.call('user', 'require', 'beta')
        self.call('user', 'register', '--user-home', user, '--apply')
        project_before = c.read_json(self.home / 'state.json')['projects']
        self.call('migrate', '--to-pinned', '--user')
        self.assertEqual(c.read_json(self.home / 'state.json')['projects'], project_before)
        self.assertEqual(c.read_json(self.home / 'user.json')['schema_version'], 2)
        self.call('migrate', '--to-pinned', '--all')
        self.assertTrue(all(pinned.is_pinned(record) for record in c.consumer_records(c.read_json(self.home / 'state.json')).values()))

    def test_dirty_unborn_pending_and_preparation_cas_refuse(self):
        (self.source / 'skills/alpha/dirty').write_text('preserve')
        before = self.snapshot()
        self.call('migrate', '--to-pinned', code=4)
        self.assertEqual(before, self.snapshot())
        (self.source / 'skills/alpha/dirty').unlink()
        original = store.materialize
        def changed(*args, **kwargs):
            result = original(*args, **kwargs)
            (self.project / '.mask.json').write_text(json.dumps(dict(schema_version=1, skills=['beta'])))
            return result
        parser, leaves = mask.make_parser()
        args = parser.parse_args(['migrate', '--to-pinned', '--project', str(self.project), '--home', str(self.home)])
        output = mask.result('migrate')
        with patch.object(store, 'materialize', side_effect=changed), self.assertRaises(c.MaskError) as error:
            mask.dispatch(args, output, leaves)
        self.assertEqual(error.exception.code, 'plan.stale')
        self.assertEqual(c.read_json(self.home / 'config.json')['schema_version'], 1)
        self.assertTrue(output['changed'])
        self.declare()
        self.crash('intent')
        self.assertEqual(self.call('migrate', '--to-pinned', code=8)['error']['code'], 'recovery.required')
        self.call('recover', '--rollback')
        self.git(self.source, 'checkout', '--orphan', 'unborn')
        self.call('migrate', '--to-pinned', code=4)

    def test_cold_generic_metadata_and_hidden_checkout_flags(self):
        (self.source / 'skills/alpha/mask-skill.json').write_text(json.dumps(dict(schema_version=1, agents='generic', platforms='generic')))
        self.git(self.source, 'add', '.')
        self.git(self.source, 'commit', '-m', 'generic metadata')
        for flag, clear in (('--assume-unchanged', '--no-assume-unchanged'), ('--skip-worktree', '--no-skip-worktree')):
            self.git(self.source, 'update-index', flag, 'skills/alpha/SKILL.md')
            self.assertEqual(self.call('migrate', '--to-pinned', '--dry-run', code=4)['error']['code'], 'source.dirty')
            self.git(self.source, 'update-index', clear, 'skills/alpha/SKILL.md')
        self.git(self.source, 'config', 'core.sparseCheckout', 'true')
        self.call('migrate', '--to-pinned', code=4)
        self.git(self.source, 'config', 'core.sparseCheckout', 'false')
        before = self.snapshot()
        preview = self.call('migrate', '--to-pinned', '--dry-run')
        self.assertEqual(before, self.snapshot())
        self.call('migrate', '--to-pinned', '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertFalse(self.call('apply')['changed'])

    def test_recovery_rejects_changed_config_and_source(self):
        self.crash('config')
        journal = c.read_json(self.home / 'pending.json')
        tampered = copy.deepcopy(journal)
        altered = json.dumps(json.loads(tampered['migration']['config_before']), separators=(',', ':'))
        tampered['migration']['config_before'] = altered
        next(item for item in tampered['files'] if item['role'] == 'machine_config')['before'] = altered
        (self.home / 'pending.json').write_bytes(c.text_json(tampered).encode('utf-8'))
        before = self.snapshot()
        self.call('recover', '--rollback', code=8)
        self.assertEqual(before, self.snapshot())
        (self.home / 'pending.json').write_bytes(c.text_json(journal).encode('utf-8'))
        config = (self.home / 'config.json').read_bytes()
        (self.home / 'config.json').write_bytes(config + b' ')
        self.call('recover', '--rollback', code=8)
        (self.home / 'config.json').write_bytes(config)
        dirty = self.source / 'skills/alpha/concurrent'
        dirty.write_text('preserve')
        self.call('recover', '--complete', code=8)
        self.assertEqual(dirty.read_text(), 'preserve')
        dirty.unlink()
        self.call('recover', '--rollback')

    def test_after_link_authoring_change_retains_partial_journal(self):
        parser, leaves = mask.make_parser()
        args = parser.parse_args(['migrate', '--to-pinned', '--project', str(self.project), '--home', str(self.home)])
        output = mask.result('migrate')
        target = self.source / 'skills/alpha/SKILL.md'
        original = target.read_bytes()
        def change(label):
            if label == 'link':
                target.write_bytes(original + b'preserve concurrent authoring edit\n')
        with patch.object(fs, 'checkpoint', side_effect=change), self.assertRaises(c.MaskError) as error:
            mask.dispatch(args, output, leaves)
        self.assertEqual(error.exception.code, 'recovery.required')
        self.assertEqual(output['transaction'], 'partial')
        self.assertTrue((self.home / 'pending.json').exists())
        self.assertNotEqual(target.read_bytes(), original)
        self.assertEqual(c.read_json(self.home / 'config.json')['schema_version'], 1)
        target.write_bytes(original)
        self.call('recover', '--rollback')
        self.crash('intent')
        real_set_link = fs.set_link
        def change_recovered_link(entry, side, **kwargs):
            real_set_link(entry, side, **kwargs)
            target.write_bytes(original + b'preserve recovery-time source edit\n')
        args = parser.parse_args(['recover', '--complete', '--home', str(self.home)])
        output = mask.result('recover')
        with patch.object(fs, 'set_link', side_effect=change_recovered_link), self.assertRaises(c.MaskError):
            mask.dispatch(args, output, leaves)
        self.assertEqual(output['transaction'], 'partial')
        self.assertTrue((self.home / 'pending.json').exists())
        self.assertNotEqual(target.read_bytes(), original)
        target.write_bytes(original)
        self.call('recover', '--rollback')

    def test_migration_preview_refuses_unreadable_generated_lock(self):
        import mask_resolve as resolve
        parser, leaves = mask.make_parser()
        args = parser.parse_args(['migrate', '--to-pinned', '--dry-run', '--project', str(self.project), '--home', str(self.home)])
        before = self.snapshot()
        with patch.object(resolve, 'MODEL_BYTES', 500), self.assertRaises(c.MaskError) as error:
            mask.dispatch(args, mask.result('migrate', True), leaves)
        self.assertEqual(error.exception.code, 'lock.limit')
        self.assertEqual(before, self.snapshot())
