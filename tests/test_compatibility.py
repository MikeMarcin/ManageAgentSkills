import copy
import json
import os
import subprocess
import sys
import unittest
from unittest.mock import patch

import mask_core as c
import mask_fs as fs
import mask_resolve as r
import mask_selection as selection
from tests.support import ENTRY, TAP, Fixture

ALPHA = TAP + '/alpha'


class CompatibilityTests(Fixture):
    # Development links need an approved authoring checkout on the tap; every other test starts from init().
    AUTHORING = {'test_live_dev_metadata_is_used_and_duplicate_destinations_refuse'}

    def setUp(self):
        super().setUp()
        self.authoring_init() if self._testMethodName in self.AUTHORING else self.init()
        self.declaration = dict(schema_version=2, sources=self.binding(), skills=[dict(source=TAP, id='alpha')])
        (self.project / '.mask.json').write_text(json.dumps(self.declaration))

    def prepare(self, metadata=None, apply=False):
        if metadata is not None:
            (self.source / 'skills/alpha/mask-skill.json').write_text(json.dumps(metadata))
            self.publish('publisher metadata')
        self.call('source', 'fetch', TAP)
        self.call('lock')
        if apply:
            self.call('project', 'register', '--apply')

    def test_cold_specific_implicit_exclusion_explicit_block_and_requirements(self):
        self.prepare(dict(schema_version=1, agents=['codex'], requirements=['tool installed separately']))
        before = self.snapshot()
        preview = self.call('project', 'register', '--apply', '--dry-run')
        self.assertEqual(before, self.snapshot())
        outcomes = {item['agent']: item for item in preview['data']['outcomes']}
        self.assertEqual(outcomes['claude']['status'], 'excluded_by_metadata')
        self.assertEqual(outcomes['codex']['compatibility'], 'specific_asserted')
        self.assertFalse(outcomes['codex']['tested'])
        self.assertEqual(outcomes['codex']['requirements'], ['tool installed separately'])
        self.call('project', 'register', '--apply', '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertFalse((self.project / '.claude/skills/alpha').exists())
        before = self.snapshot()
        blocked = self.call('project', 'set-agents', ALPHA, 'claude', '--apply', code=4)
        self.assertEqual(blocked['error']['code'], 'compatibility.unsupported')
        self.assertEqual(before, self.snapshot())

    def test_absent_generic_specific_assertions_and_architecture_are_pure(self):
        self.prepare()
        declaration = r.selection(self.declaration)
        lock = c.read_json(self.project / '.mask.lock.json')
        contribution = dict(origin='local', declaration=declaration, lock=lock)
        facts = dict(platform='linux', architecture='x86_64')
        def evaluate(metadata, contributions=None):
            with patch('shutil.which', side_effect=AssertionError('must not detect executables')):
                return selection.evaluate(contributions or [contribution], {ALPHA: metadata}, facts=facts,
                                          enabled_agents=['claude', 'codex'], scope='project', root=self.project, identity=c.identity(self.project))
        for metadata, expected in [(None, 'unspecified'), (dict(schema_version=1, agents='generic'), 'generic_asserted'), (dict(schema_version=1, platforms=['linux']), 'specific_asserted')]:
            result = evaluate(metadata)
            self.assertEqual({row['compatibility'] for row in result['outcomes']}, {expected})
            self.assertTrue(all(not row['tested'] for row in result['outcomes']))
        self.assertTrue(evaluate(dict(schema_version=1, architectures=['arm64']))['blocked'])
        declaration['skills'][0]['when'] = dict(architectures=['arm64'])
        lock['selection_digest'] = r.selection_digest(declaration)
        result = evaluate(None)
        self.assertEqual(result['outcomes'][0]['status'], 'not_applicable')

    def test_override_is_reasoned_physical_scope_local_and_cannot_enable(self):
        self.prepare(dict(schema_version=1, agents=['codex']), apply=True)
        other = self.base / 'other'
        other.mkdir()
        for name in ('.mask.json', '.mask.lock.json'):
            (other / name).write_bytes((self.project / name).read_bytes())
        self.call('project', 'register', '--project', other, '--apply')
        preview = self.call('compatibility', 'override', ALPHA, '--project', self.project, '--agent', 'claude', '--reason', 'Reviewed local use', '--dry-run')
        self.assertEqual(preview['data']['affected_scopes'], [str(self.project)])
        result = self.call('compatibility', 'override', ALPHA, '--project', self.project, '--agent', 'claude', '--reason', 'Reviewed local use', '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertTrue((self.project / '.claude/skills/alpha').is_symlink())
        self.assertFalse((other / '.claude/skills/alpha').exists())
        self.assertIn('overridden', {row['status'] for row in result['data']['outcomes']})
        self.call('compatibility', 'override', ALPHA, '--project', other, '--agent', 'claude', '--reason', 'Second scope')
        policy_bytes = (self.home / 'selection-policy.json').read_bytes()
        self.assertFalse(self.call('compatibility', 'override', ALPHA, '--project', self.project, '--agent', 'claude', '--reason', 'Reviewed local use')['changed'])
        self.assertEqual(policy_bytes, (self.home / 'selection-policy.json').read_bytes())
        self.call('compatibility', 'override', ALPHA, '--project', self.project, '--agent', 'unknown', '--reason', 'cannot grant adapter', code=4)
        self.assertEqual(policy_bytes, (self.home / 'selection-policy.json').read_bytes())
        self.call('selection-policy', 'set', '--agent', 'codex')
        self.assertFalse((self.project / '.claude/skills/alpha').exists())
        self.call('project', 'set-agents', ALPHA, 'claude', '--apply', code=4)
        self.call('selection-policy', 'clear')
        self.assertTrue((self.project / '.claude/skills/alpha').is_symlink())
        self.call('compatibility', 'clear', ALPHA, '--project', self.project)
        self.assertFalse((self.project / '.claude/skills/alpha').exists())
        self.assertTrue((other / '.claude/skills/alpha').is_symlink())
        remaining = c.read_json(self.home / 'selection-policy.json')['overrides']
        self.assertEqual([row['root'] for row in remaining], [str(other)])

    def test_policy_journal_exact_bytes_and_typed_coverage(self):
        self.prepare(apply=True)
        script = "import os,sys;sys.path.insert(0,sys.argv[1]);import mask,mask_fs;mask_fs.checkpoint=lambda label: os._exit(99) if label=='selection_policy' else None;mask.main(sys.argv[2:])"
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), 'selection-policy', 'set', '--agent', 'codex', '--home', str(self.home), '--json'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 99, run.stdout + run.stderr)
        journal = c.read_json(self.home / 'pending.json')
        for transform in ('extension', 'files', 'before'):
            bad = copy.deepcopy(journal)
            if transform == 'extension':
                bad.pop('selection_change')
            elif transform == 'files':
                bad['files'] = []
            else:
                bad['selection_change']['policy_before'] = c.text_json(selection.policy())
            (self.home / 'pending.json').write_bytes(c.text_json(bad).encode('utf-8'))
            self.call('recover', '--rollback', code=8)
        (self.home / 'pending.json').write_bytes(c.text_json(journal).encode('utf-8'))
        self.call('recover', '--rollback')
        self.assertFalse((self.home / 'selection-policy.json').exists())
        self.assertTrue((self.project / '.claude/skills/alpha').is_symlink())

    def test_live_dev_metadata_is_used_and_duplicate_destinations_refuse(self):
        self.prepare(apply=True)
        (self.source / 'skills/alpha/mask-skill.json').write_text(json.dumps(dict(schema_version=1, agents=['codex'])))
        self.call('source', 'dev-link', ALPHA, '--project', self.project, '--authoring-root', self.source)
        self.assertFalse((self.project / '.claude/skills/alpha').exists())
        self.assertEqual(self.call('project', 'show')['data']['mode'], 'dev-link')
        self.assertEqual(self.call('apply', code=4)['error']['code'], 'dev_link.active')
        self.call('source', 'dev-link', ALPHA, '--project', self.project, '--to-pinned')
        self.assertTrue((self.project / '.claude/skills/alpha').is_symlink())
        self.call('tap', 'add', 'second', str(self.upstream))
        self.call('source', 'fetch', 'second')
        declaration = c.read_json(self.project / '.mask.json')
        declaration['sources']['second'] = dict(declaration['sources'][TAP])
        declaration['skills'].append(dict(source='second', id='alpha'))
        (self.project / '.mask.json').write_text(json.dumps(declaration))
        self.call('upgrade', '--project', self.project, code=4)
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())


    def test_recovery_rederives_links_from_effective_after_policy(self):
        self.prepare(dict(schema_version=1, agents=['codex']), apply=True)
        script = "import os,sys;sys.path.insert(0,sys.argv[1]);import mask,mask_fs;mask_fs.checkpoint=lambda label: os._exit(99) if label=='intent' else None;mask.main(sys.argv[2:])"
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), 'compatibility', 'override', ALPHA, '--project', str(self.project), '--agent', 'claude', '--reason', 'Reviewed', '--home', str(self.home), '--json'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 99, run.stdout + run.stderr)
        journal = c.read_json(self.home / 'pending.json')
        bad = copy.deepcopy(journal)
        unauthorized = c.text_json(selection.policy())
        bad['selection_change']['policy_after'] = unauthorized
        next(row for row in bad['files'] if row['role'] == 'selection_policy')['after'] = unauthorized
        (self.home / 'pending.json').write_bytes(c.text_json(bad).encode('utf-8'))
        before = self.snapshot()
        self.call('recover', '--complete', code=8)
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.project / '.claude/skills/alpha').exists())
        (self.home / 'pending.json').write_bytes(c.text_json(journal).encode('utf-8'))
        self.call('recover', '--complete')
        self.assertTrue((self.project / '.claude/skills/alpha').is_symlink())

    def test_final_policy_edits_retain_partial_recovery(self):
        import mask
        self.prepare(apply=True)
        for boundary in ('selection_policy', 'state'):
            with self.subTest(boundary=boundary):
                parser, leaves = mask.make_parser()
                args = parser.parse_args(['selection-policy', 'set', '--agent', 'codex', '--home', str(self.home)])
                output = mask.result('selection-policy.set')
                altered = c.text_json(dict(schema_version=1, enabled_agents=['claude'], overrides=[]))
                def edit(label):
                    if label == boundary:
                        (self.home / 'selection-policy.json').write_text(altered)
                with patch.object(fs, 'checkpoint', side_effect=edit), self.assertRaises(c.MaskError) as caught:
                    mask.dispatch(args, output, leaves)
                self.assertEqual(caught.exception.exit_code, 8)
                self.assertEqual(output['transaction'], 'partial')
                self.assertTrue(output['changed'])
                self.assertEqual((self.home / 'selection-policy.json').read_text(), altered)
                journal = c.read_json(self.home / 'pending.json')
                (self.home / 'selection-policy.json').write_bytes(journal['selection_change']['policy_after'].encode('utf-8'))
                self.call('recover', '--rollback')
                self.assertFalse((self.home / 'selection-policy.json').exists())
                self.assertTrue((self.project / '.claude/skills/alpha').is_symlink())


class PolicyModelTests(unittest.TestCase):
    def test_closed_policy_authority_and_device_conditions(self):
        for value in [dict(schema_version=1, enabled_agents=['unknown'], overrides=[]),
                      dict(schema_version=1, enabled_agents=['codex', 'codex'], overrides=[]),
                      dict(schema_version=1, enabled_agents=['codex'], overrides=[], trust=True)]:
            with self.subTest(value=value), self.assertRaises(c.MaskError):
                selection.policy(value)
        root = str(ENTRY.parent.resolve())
        override = dict(root=root, identity=c.identity(ENTRY.parent), coordinate='vendor/alpha', reason='Reviewed', agents=['codex'])
        valid = dict(schema_version=1, enabled_agents=['codex'], overrides=[override])
        self.assertEqual(selection.policy(valid), valid)
        wide = copy.deepcopy(valid)
        wide['overrides'][0]['identity'] = dict(device=2 ** 64 - 1, inode=2 ** 64 - 1)
        self.assertEqual(selection.policy(wide), wide)
        for field, value in [('root', root + '/../escape'), ('reason', ''), ('agents', ['unknown']), ('identity', dict(device=1.0, inode=2))]:
            bad = copy.deepcopy(valid)
            bad['overrides'][0][field] = value
            with self.subTest(field=field), self.assertRaises(c.MaskError):
                selection.policy(bad)
        with patch.object(selection, 'POLICY_BYTES', 8), self.assertRaises(c.MaskError):
            selection.parse_policy_text(c.text_json(valid))
        self.assertFalse(selection.applies(dict(when=dict(platforms=['linux'], architectures=['arm64'])), dict(platform='linux', architecture='x86_64')))
