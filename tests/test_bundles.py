"""Public CLI bundle journeys against disposable projects and local bare taps."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from tests.public_support import PublicFixture, ENTRY
from tests.support import TAP


class BundleTests(PublicFixture):
    def setUp(self):
        super().setUp()
        self.index = dict(schema_version=1, packages={name: 'skills/' + name for name in ('alpha', 'beta', 'implement-rfc')}, bundles={
            'first': dict(description='First fixture bundle', skills=[dict(source=TAP, id='alpha')]),
            'both': dict(skills=[dict(source=TAP, id='alpha'), dict(source=TAP, id='beta')])})
        self.publish_index()
        self.call('tap', 'fetch', TAP)

    def call(self, *args, code=0, **kwargs):
        run = self.raw(*args, '--json', **kwargs)
        self.assertEqual(run.returncode, code, run.stdout + run.stderr)
        self.assertEqual(run.stderr, '', run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result['ok'], code == 0, result)
        return result

    def publish_index(self):
        (self.source / 'mask-source.json').write_text(json.dumps(self.index, indent=2) + '\n', encoding='utf-8')
        self.git(self.source, 'add', 'skills', 'mask-source.json')
        self.git(self.source, 'commit', '-q', '--allow-empty', '-m', 'bundle fixture')
        self.git(self.source, 'push', '-q', str(self.upstream), 'HEAD:main')
        return self.git(self.source, 'rev-parse', 'HEAD')

    def declaration(self):
        return json.loads((self.project / '.mask.json').read_text())

    def lock(self):
        return json.loads((self.project / '.mask.lock.json').read_text())

    def selected(self):
        return {row['source'] + '/' + row['id'] for row in self.declaration()['skills']}

    def consumer_bytes(self):
        result = {}
        for root in (self.project, self.home):
            if not root.exists():
                continue
            for parent, dirs, files in os.walk(root):
                dirs[:] = [name for name in dirs if name not in ('.git', 'sources', 'store')]
                for name in files + [name for name in dirs if (Path(parent) / name).is_symlink()]:
                    path = Path(parent) / name
                    if name.endswith('.lock'):
                        continue
                    result[str(path)] = ('link', os.readlink(path)) if path.is_symlink() else ('file', path.read_bytes())
        return result

    def apply_bundle(self, name='first', **kwargs):
        return self.call('bundle', 'apply', TAP + '/' + name, '--project', self.project, **kwargs)

    def test_public_browse_preview_additive_repeat_and_exact_lock(self):
        listed = self.call('bundle', 'list')['data']['bundles']
        self.assertEqual([row['coordinate'] for row in listed], [TAP + '/both', TAP + '/first'])
        shown = self.call('bundle', 'show', TAP + '/both')['data']['bundle']
        self.assertEqual(shown['commit'], self.git(self.source, 'rev-parse', 'HEAD'))
        self.assertEqual([row['id'] for row in shown['bindings']], ['alpha', 'beta'])
        self.call('install', TAP + '/beta')
        prior = self.lock()['packages'][0]
        before = self.consumer_bytes()
        preview = self.call('bundle', 'apply', TAP + '/first', '--dry-run')
        self.assertEqual(self.consumer_bytes(), before)
        self.call('bundle', 'apply', TAP + '/first', '--approve-plan', preview['data']['plan_hash'])
        self.assertEqual(self.selected(), {TAP + '/alpha', TAP + '/beta'})
        self.assertEqual(next(row for row in self.lock()['packages'] if row['id'] == 'beta'), prior)
        receipt = self.declaration()['bundle_state']['bundles'][TAP + '/first']
        self.assertEqual((receipt['commit'], receipt['definition_digest']), (shown['commit'], self.call('bundle', 'show', TAP + '/first')['data']['bundle']['definition_digest']))
        before = self.consumer_bytes()
        self.assertFalse(self.apply_bundle()['changed'])
        self.assertEqual(self.consumer_bytes(), before)
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())
        self.assertTrue((self.project / '.claude/skills/alpha').is_symlink())
        self.call('status', '--check')

    def test_manual_targets_and_manual_install_after_bundle_survive_refresh(self):
        self.call('install', TAP + '/alpha', '--agent', 'codex')
        self.index['bundles']['first']['skills'][0]['agents'] = ['claude']
        self.publish_index(); self.call('tap', 'fetch', TAP)
        result = self.apply_bundle()
        self.assertEqual(result['data']['preserved'][0]['reason'], 'manual_targets')
        self.assertEqual(self.declaration()['skills'][0]['agents'], ['codex'])
        self.apply_bundle('both')
        self.call('install', TAP + '/beta')  # Positive manual selection of an existing bundle member.
        self.index['bundles']['both']['skills'] = []
        self.publish_index(); self.call('tap', 'fetch', TAP)
        result = self.call('bundle', 'refresh', TAP + '/both')
        self.assertEqual(result['data']['removed'], [])
        self.assertEqual(self.selected(), {TAP + '/alpha', TAP + '/beta'})

    def test_overlap_and_bounded_replace_preserve_other_contributions(self):
        self.apply_bundle('both'); self.apply_bundle('first')
        self.index['bundles']['both']['skills'] = []
        self.publish_index(); self.call('tap', 'fetch', TAP)
        preview = self.call('bundle', 'refresh', TAP + '/both', '--dry-run')
        self.assertEqual(preview['data']['removed'], [TAP + '/beta'])
        review = self.human('bundle', 'refresh', TAP + '/both', '--dry-run')
        self.assertEqual(review.returncode, 0, review.stderr)
        self.assertIn('- ' + TAP + '/beta', review.stdout)
        self.assertIn('preserve ' + TAP + '/alpha', review.stdout)
        self.call('bundle', 'apply', TAP + '/both', '--replace', '--approve-plan', preview['data']['plan_hash'], code=4)  # Public command differs.
        self.call('bundle', 'apply', TAP + '/both', '--replace')
        self.assertEqual(self.selected(), {TAP + '/alpha'})
        self.assertFalse((self.project / '.agents/skills/beta').exists())
        self.assertIn(TAP + '/first', self.declaration()['bundle_state']['bundles'])

    def test_definition_change_stales_preview_and_requires_explicit_refresh(self):
        preview = self.call('bundle', 'apply', TAP + '/first', '--dry-run')
        self.index['bundles']['first']['skills'].append(dict(source=TAP, id='beta'))
        self.publish_index(); self.call('tap', 'fetch', TAP)
        before = self.consumer_bytes()
        refused = self.call('bundle', 'apply', TAP + '/first', '--approve-plan', preview['data']['plan_hash'], code=4)
        self.assertEqual(refused['error']['code'], 'plan.stale')
        self.assertEqual(self.consumer_bytes(), before)
        self.apply_bundle()
        self.index['bundles']['first']['skills'] = [dict(source=TAP, id='beta')]
        self.publish_index(); self.call('tap', 'fetch', TAP)
        refused = self.apply_bundle(code=4)
        self.assertEqual(refused['error']['code'], 'bundle.refresh_required')
        preview = self.call('bundle', 'refresh', TAP + '/first', '--dry-run')
        self.assertEqual(preview['data']['removed'], [TAP + '/alpha'])
        self.call('bundle', 'refresh', TAP + '/first', '--approve-plan', preview['data']['plan_hash'])
        self.assertEqual(self.selected(), {TAP + '/beta'})

    def test_unapproved_source_missing_member_and_flat_validation_refuse_before_consumer_changes(self):
        for member, expected in [(dict(source='unapproved', id='alpha'), 'source.unknown'), (dict(source=TAP, id='missing'), 'skill.unknown')]:
            self.index['bundles']['first']['skills'] = [member]
            self.publish_index(); self.call('tap', 'fetch', TAP)
            before = self.consumer_bytes()
            refused = self.apply_bundle(code=4)
            self.assertEqual(refused['error']['code'], expected)
            self.assertEqual(self.consumer_bytes(), before)
        self.index['bundles']['first']['includes'] = ['first']
        self.publish_index()
        self.call('tap', 'fetch', TAP)
        before = self.consumer_bytes()
        refused = self.apply_bundle(code=3)
        self.assertEqual(refused['error']['code'], 'source.invalid')
        self.assertEqual(self.consumer_bytes(), before)

    def test_version_and_bundle_target_conflicts_report_origins_and_preserve_bytes(self):
        self.index['bundles']['first']['skills'][0]['agents'] = ['codex']
        self.publish_index(); self.call('tap', 'fetch', TAP)
        self.apply_bundle()
        self.index['bundles']['both']['skills'][0]['agents'] = ['claude']
        self.publish_index(); self.call('tap', 'fetch', TAP)
        before = self.consumer_bytes()
        refused = self.apply_bundle('both', code=4)
        self.assertEqual(refused['error']['details']['dimension'], 'agents')
        self.assertIn(TAP + '/first', refused['error']['details']['origins'])
        self.assertEqual(self.consumer_bytes(), before)
        self.index['bundles']['both']['skills'][0].pop('agents')
        self.index['bundles']['both']['skills'][0]['version'] = {'commit': self.git(self.source, 'rev-parse', 'HEAD')}
        self.publish_index(); self.call('tap', 'fetch', TAP)
        before = self.consumer_bytes()
        refused = self.apply_bundle('both', code=4)
        self.assertEqual(refused['error']['details']['dimension'], 'version')
        self.assertEqual(self.consumer_bytes(), before)

    def test_held_versions_and_local_target_edits_are_preserved_on_refresh_removal(self):
        self.apply_bundle('both')
        self.call('pin', TAP + '/alpha')
        self.call('project', 'set-agents', TAP + '/beta', 'codex')
        prior = self.lock()['packages']
        self.index['bundles']['both']['skills'] = []
        self.publish_index(); self.call('tap', 'fetch', TAP)
        result = self.call('bundle', 'refresh', TAP + '/both')
        self.assertEqual(result['data']['removed'], [])
        self.assertEqual(self.lock()['packages'], prior)
        self.assertEqual(set(self.declaration()['bundle_state']['manual']), {TAP + '/alpha', TAP + '/beta'})

    def test_user_scope_uninstall_and_capabilities(self):
        self.call('bundle', 'apply', TAP + '/both', '--user')
        self.assertTrue((self.personal / '.agents/skills/alpha').is_symlink())
        self.assertFalse((self.project / '.mask.json').exists())
        self.call('uninstall', TAP + '/alpha', '--user')
        self.call('bundle', 'apply', TAP + '/both', '--user')
        value = json.loads((self.home / 'user.json').read_text())
        self.assertEqual([row['id'] for row in value['skills']], ['beta'])
        self.call('bundle', 'refresh', TAP + '/both', '--user')
        self.call('status', '--user', '--check')
        commands = {row['name']: row for row in self.call('capabilities')['data']['commands']}
        self.assertTrue(commands['bundle.apply']['plan_guard'])
        self.assertNotIn('bundle.remove', commands)
        self.assertNotIn('profile.subscribe', commands)

    def test_refresh_never_upgrades_package_rows_or_silently_changes_membership(self):
        self.apply_bundle()
        prior = self.lock()['packages'][0]
        receipt = self.declaration()['bundle_state']['bundles'][TAP + '/first']
        with (self.source / 'skills/alpha/SKILL.md').open('a') as stream:
            stream.write('\nNew fixture content.\n')
        head = self.publish_index(); self.call('tap', 'fetch', TAP)
        self.assertFalse(self.apply_bundle()['changed'])
        self.assertEqual(self.declaration()['bundle_state']['bundles'][TAP + '/first'], receipt)
        self.call('bundle', 'refresh', TAP + '/first')
        self.assertEqual(self.lock()['packages'][0], prior)
        self.assertEqual(self.declaration()['bundle_state']['bundles'][TAP + '/first']['commit'], head)

    def generated_bundle(self, before=''):
        from tests.test_setup import GENERATED, SetupFixture
        from tests.public_support import CONSUMER_CONTEXT
        self.package = self.source / 'skills/implement-rfc'
        shutil.rmtree(self.package)  # Only the disposable author fixture.
        shutil.copytree(GENERATED, self.package)
        self.sentinel = self.base / 'setup-launches.txt'
        SetupFixture.write_script(self, before=before)
        shutil.copytree(CONSUMER_CONTEXT, self.project / '.mask')
        self.index['bundles']['workflow'] = dict(skills=[dict(source=TAP, id='alpha'), dict(source=TAP, id='implement-rfc')])
        self.publish_index(); self.call('tap', 'fetch', TAP)

    def fault(self, *args, label):
        script = '''
import os, sys
sys.path.insert(0, sys.argv[1])
import mask, mask_fs
mask_fs.checkpoint = lambda observed: os._exit(99) if observed == sys.argv[2] else None
raise SystemExit(mask.main(sys.argv[3:]))
'''
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), label, *map(str, args), '--json'],
                             capture_output=True, text=True, env=self.environment(), cwd=self.project, timeout=60)
        self.assertEqual(run.returncode, 99, run.stdout + run.stderr)

    def test_bundle_setup_requires_exact_review_and_reports_failure_truthfully(self):
        self.generated_bundle(before='    raise RuntimeError("fixture failure")\n')
        before = self.consumer_bytes()
        preview = self.call('bundle', 'apply', TAP + '/workflow', '--dry-run')
        self.assertFalse(self.sentinel.exists())
        self.assertEqual(self.consumer_bytes(), before)
        result = self.apply_bundle('workflow', code=4)
        self.assertEqual(result['error']['code'], 'confirmation.required')
        self.assertEqual(self.consumer_bytes(), before)
        result = self.call('bundle', 'apply', TAP + '/workflow', '--approve-plan', preview['data']['plan_hash'], code=5)
        self.assertEqual(result['error']['code'], 'setup.failed')
        self.assertTrue(result['changed'])
        self.assertEqual(result['transaction'], 'committed')
        self.assertEqual(len(self.sentinel.read_text().splitlines()), 1)
        self.assertEqual(self.selected(), {TAP + '/alpha', TAP + '/implement-rfc'})
        self.assertFalse(self.call('status')['data']['healthy'])

    def test_bundle_setup_interruption_recovery_never_reruns_scripts(self):
        self.generated_bundle()
        preview = self.call('bundle', 'apply', TAP + '/workflow', '--dry-run')
        self.fault('bundle', 'apply', TAP + '/workflow', '--approve-plan', preview['data']['plan_hash'], label='setup.exited')
        self.assertEqual(json.loads((self.home / 'pending.json').read_text())['operation'], 'ensure')
        self.assertEqual(self.call('recover', '--complete', code=8)['error']['code'], 'setup.unverified')
        self.call('recover', '--rollback')
        self.assertEqual(len(self.sentinel.read_text().splitlines()), 1)
        self.assertEqual(self.selected(), {TAP + '/alpha', TAP + '/implement-rfc'})
        self.call('bundle', 'apply', TAP + '/workflow', '--dry-run')

    def test_bundle_activation_recovery_uses_frozen_selection_and_receipt(self):
        preview = self.call('bundle', 'apply', TAP + '/both', '--dry-run')
        expected = preview['data']['after']
        self.fault('bundle', 'apply', TAP + '/both', '--approve-plan', preview['data']['plan_hash'], label='lock')
        self.index['bundles']['both']['skills'] = []
        self.publish_index()  # Remote can advance; recovery consumes the frozen journal.
        self.call('recover', '--complete')
        self.assertEqual(self.declaration(), expected)
        self.call('status', '--check')

    def test_approved_missing_cache_offline_invalid_targets_and_target_collision(self):
        other = self.base / 'other-tap'
        shutil.copytree(self.source / 'skills/alpha', other / 'skills/alpha')
        self.git(other, 'init', '-b', 'main')
        self.git(other, 'config', 'user.name', 'Fixture')
        self.git(other, 'config', 'user.email', 'fixture@example.invalid')
        self.git(other, 'add', 'skills'); self.git(other, 'commit', '-m', 'other fixture')
        self.call('tap', 'other', other)
        self.index['bundles']['both']['skills'].append(dict(source='other', id='alpha'))
        self.publish_index(); self.call('tap', 'fetch', TAP)
        before = self.consumer_bytes()
        refused = self.call('bundle', 'apply', TAP + '/both', '--offline', code=4)
        self.assertEqual(refused['error']['code'], 'lock.resolution_required')
        self.assertEqual(self.consumer_bytes(), before)
        self.call('tap', 'fetch', 'other')
        refused = self.apply_bundle('both', code=4)
        self.assertEqual(refused['error']['code'], 'target.collision')
        self.assertEqual(refused['error']['details']['contribution_origins']['other/alpha'], [TAP + '/both'])
        self.assertEqual(self.consumer_bytes(), before)
        self.index['bundles']['both']['skills'][0]['agents'] = ['nonexistent']
        self.publish_index(); self.call('tap', 'fetch', TAP)
        refused = self.apply_bundle('both', code=4)
        self.assertEqual(refused['error']['code'], 'selection.invalid')

    def test_unchanged_definition_new_source_revision_stales_plan_and_human_output(self):
        preview = self.call('bundle', 'apply', TAP + '/first', '--dry-run')
        self.publish_index(); self.call('tap', 'fetch', TAP)
        before = self.consumer_bytes()
        refused = self.call('bundle', 'apply', TAP + '/first', '--approve-plan', preview['data']['plan_hash'], code=4)
        self.assertEqual(refused['error']['code'], 'plan.stale')
        self.assertEqual(self.consumer_bytes(), before)
        run = self.human('bundle', 'show', TAP + '/first')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('Bundle ' + TAP + '/first', run.stdout)
        self.assertFalse(self.parses_as_result_envelope(run.stdout))
        run = self.human('bundle', 'apply', TAP + '/first', '--dry-run')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('Would apply', run.stdout)

    def test_refresh_refuses_edited_deployment_before_any_consumer_change(self):
        self.apply_bundle()
        leaf = self.project / '.agents/skills/alpha'
        leaf.unlink(); leaf.mkdir()
        (leaf / 'mine.md').write_text('Keep my edited fixture.\n')
        self.index['bundles']['first']['skills'] = []
        self.publish_index(); self.call('tap', 'fetch', TAP)
        before = self.consumer_bytes()
        refused = self.call('bundle', 'refresh', TAP + '/first', code=4)
        self.assertEqual(refused['error']['code'], 'target.collision')
        self.assertEqual(self.consumer_bytes(), before)

    def test_definition_source_with_no_package_is_revision_bound_and_declared(self):
        catalogue = self.base / 'catalogue'
        catalogue.mkdir()
        self.git(catalogue, 'init', '-b', 'main')
        self.git(catalogue, 'config', 'user.name', 'Fixture')
        self.git(catalogue, 'config', 'user.email', 'fixture@example.invalid')
        index = dict(schema_version=1, packages={}, bundles={'pack': dict(skills=[dict(source=TAP, id='alpha')])})
        (catalogue / 'mask-source.json').write_text(json.dumps(index))
        self.git(catalogue, 'add', 'mask-source.json'); self.git(catalogue, 'commit', '-m', 'catalogue fixture')
        head = self.git(catalogue, 'rev-parse', 'HEAD')
        self.call('tap', 'catalogue', catalogue); self.call('tap', 'fetch', 'catalogue')
        preview = self.call('bundle', 'apply', 'catalogue/pack', '--dry-run')
        self.assertEqual(preview['data']['bundle']['commit'], head)
        self.assertNotEqual(preview['data']['locked']['packages'][0]['commit'], head)
        self.call('bundle', 'apply', 'catalogue/pack', '--approve-plan', preview['data']['plan_hash'])
        self.assertEqual(self.declaration()['bundle_state']['bundles']['catalogue/pack']['commit'], head)
        self.assertIn('catalogue', self.declaration()['sources'])
        refused = self.call('untap', 'catalogue', code=4)
        self.assertEqual(refused['error']['code'], 'source.referenced')
