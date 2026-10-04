"""Public CLI bundle journeys against disposable projects and local bare taps."""
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

from tests.public_support import PublicFixture, ENTRY
from tests.support import TAP


def remove_tree(path):
    """``shutil.rmtree`` that also removes read-only files: Git writes its objects read-only and Windows refuses to unlink them."""
    def writable(function, target, _):
        os.chmod(target, stat.S_IWRITE)
        function(target)
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=writable)
    else:
        shutil.rmtree(path, onerror=writable)


class BundleTests(PublicFixture):
    def setUp(self):
        super().setUp()
        self.index = dict(schema_version=1, packages={name: 'skills/' + name for name in ('alpha', 'beta', 'implement-rfc')}, bundles={
            'first': dict(description='First fixture bundle', skills=[dict(source=TAP, id='alpha')]),
            'both': dict(skills=[dict(source=TAP, id='alpha'), dict(source=TAP, id='beta')])})
        self.publish_index()
        self.call('tap', 'fetch', TAP)

    def call(self, *args, code=0, **kwargs):
        if args[0] in ('install', 'upgrade'):
            args = (*args, '--no-update')  # Fixture taps only; never refresh the real program checkout.
        run = self.raw(*args, '--json', **kwargs)
        self.assertEqual(run.returncode, code, run.stdout + run.stderr)
        self.assertEqual(run.stderr, '', run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result['ok'], code == 0, result)
        return result

    def publish_index(self):
        (self.source / 'mask-source.json').write_text(json.dumps(self.index, indent=2) + '\n', encoding='utf-8', newline='\n')
        self.git(self.source, 'add', 'skills', 'mask-source.json')
        self.git(self.source, 'commit', '-q', '--allow-empty', '-m', 'bundle fixture')
        self.git(self.source, 'push', '-q', str(self.upstream), 'HEAD:main')
        return self.git(self.source, 'rev-parse', 'HEAD')

    def declaration(self):
        return json.loads((self.project / '.mask.json').read_text(encoding='utf-8'))

    def lock(self):
        return json.loads((self.project / '.mask.lock.json').read_text(encoding='utf-8'))

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

    def install_bundle(self, name='first', **kwargs):
        return self.call('bundle', 'install', TAP + '/' + name, '--project', self.project, **kwargs)

    def test_public_browse_preview_additive_repeat_and_exact_lock(self):
        listed = self.call('bundle', 'list')['data']['bundles']
        self.assertEqual([row['coordinate'] for row in listed], [TAP + '/both', TAP + '/first'])
        shown = self.call('bundle', 'show', TAP + '/both')['data']['bundle']
        self.assertEqual(shown['commit'], self.git(self.source, 'rev-parse', 'HEAD'))
        self.assertEqual([row['id'] for row in shown['bindings']], ['alpha', 'beta'])
        self.call('install', TAP + '/beta')
        prior = self.lock()['packages'][0]
        before = self.consumer_bytes()
        preview = self.call('bundle', 'install', TAP + '/first', '--dry-run')
        self.assertEqual(self.consumer_bytes(), before)
        self.call('bundle', 'install', TAP + '/first', '--approve-plan', preview['data']['plan_hash'])
        self.assertEqual(self.selected(), {TAP + '/alpha', TAP + '/beta'})
        self.assertEqual(next(row for row in self.lock()['packages'] if row['id'] == 'beta'), prior)
        receipt = self.declaration()['bundle_state']['bundles'][TAP + '/first']
        self.assertEqual((receipt['commit'], receipt['definition_digest']), (shown['commit'], self.call('bundle', 'show', TAP + '/first')['data']['bundle']['definition_digest']))
        before = self.consumer_bytes()
        self.assertFalse(self.install_bundle()['changed'])
        self.assertEqual(self.consumer_bytes(), before)
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())
        self.assertTrue((self.project / '.claude/skills/alpha').is_symlink())
        self.call('status', '--check')

    def test_manual_targets_and_manual_install_after_bundle_survive_refresh(self):
        self.call('install', TAP + '/alpha', '--agent', 'codex')
        self.index['bundles']['first']['skills'][0]['agents'] = ['claude']
        self.publish_index(); self.call('tap', 'fetch', TAP)
        result = self.install_bundle()
        self.assertEqual(result['data']['preserved'][0]['reason'], 'manual_targets')
        self.assertEqual(self.declaration()['skills'][0]['agents'], ['codex'])
        self.install_bundle('both')
        self.call('install', TAP + '/beta')  # Positive manual selection of an existing bundle member.
        self.index['bundles']['both']['skills'] = []
        self.publish_index(); self.call('tap', 'fetch', TAP)
        result = self.call('bundle', 'upgrade', TAP + '/both')
        self.assertEqual(result['data']['removed'], [])
        self.assertEqual(self.selected(), {TAP + '/alpha', TAP + '/beta'})

    def test_overlap_and_bounded_replace_preserve_other_contributions(self):
        self.install_bundle('both'); self.install_bundle('first')
        self.index['bundles']['both']['skills'] = []
        self.publish_index(); self.call('tap', 'fetch', TAP)
        preview = self.call('bundle', 'upgrade', TAP + '/both', '--dry-run')
        self.assertEqual(preview['data']['removed'], [TAP + '/beta'])
        review = self.human('bundle', 'upgrade', TAP + '/both', '--dry-run')
        self.assertEqual(review.returncode, 0, review.stderr)
        self.assertIn('- ' + TAP + '/beta', review.stdout)
        self.assertIn('preserve ' + TAP + '/alpha', review.stdout)
        self.call('bundle', 'install', TAP + '/both', '--replace', '--approve-plan', preview['data']['plan_hash'], code=4)  # Public command differs.
        self.call('bundle', 'install', TAP + '/both', '--replace')
        self.assertEqual(self.selected(), {TAP + '/alpha'})
        self.assertFalse((self.project / '.agents/skills/beta').exists())
        self.assertIn(TAP + '/first', self.declaration()['bundle_state']['bundles'])

    def test_definition_change_stales_preview_and_requires_explicit_refresh(self):
        preview = self.call('bundle', 'install', TAP + '/first', '--dry-run')
        self.index['bundles']['first']['skills'].append(dict(source=TAP, id='beta'))
        self.publish_index(); self.call('tap', 'fetch', TAP)
        before = self.consumer_bytes()
        refused = self.call('bundle', 'install', TAP + '/first', '--approve-plan', preview['data']['plan_hash'], code=4)
        self.assertEqual(refused['error']['code'], 'plan.stale')
        self.assertEqual(self.consumer_bytes(), before)
        self.install_bundle()
        self.index['bundles']['first']['skills'] = [dict(source=TAP, id='beta')]
        self.publish_index(); self.call('tap', 'fetch', TAP)
        refused = self.install_bundle(code=4)
        self.assertEqual(refused['error']['code'], 'bundle.upgrade_required')
        preview = self.call('bundle', 'upgrade', TAP + '/first', '--dry-run')
        self.assertEqual(preview['data']['removed'], [TAP + '/alpha'])
        self.call('bundle', 'upgrade', TAP + '/first', '--approve-plan', preview['data']['plan_hash'])
        self.assertEqual(self.selected(), {TAP + '/beta'})

    def test_unapproved_source_missing_member_and_flat_validation_refuse_before_consumer_changes(self):
        for member, expected in [(dict(source='unapproved', id='alpha'), 'source.unknown'), (dict(source=TAP, id='missing'), 'skill.unknown')]:
            self.index['bundles']['first']['skills'] = [member]
            self.publish_index(); self.call('tap', 'fetch', TAP)
            before = self.consumer_bytes()
            refused = self.install_bundle(code=4)
            self.assertEqual(refused['error']['code'], expected)
            self.assertEqual(self.consumer_bytes(), before)
        self.index['bundles']['first']['includes'] = ['first']
        self.publish_index()
        self.call('tap', 'fetch', TAP)
        before = self.consumer_bytes()
        refused = self.install_bundle(code=3)
        self.assertEqual(refused['error']['code'], 'source.invalid')
        self.assertEqual(self.consumer_bytes(), before)

    def test_version_and_bundle_target_conflicts_report_origins_and_preserve_bytes(self):
        self.index['bundles']['first']['skills'][0]['agents'] = ['codex']
        self.publish_index(); self.call('tap', 'fetch', TAP)
        self.install_bundle()
        self.index['bundles']['both']['skills'][0]['agents'] = ['claude']
        self.publish_index(); self.call('tap', 'fetch', TAP)
        before = self.consumer_bytes()
        refused = self.install_bundle('both', code=4)
        self.assertEqual(refused['error']['details']['dimension'], 'agents')
        self.assertIn(TAP + '/first', refused['error']['details']['origins'])
        self.assertEqual(self.consumer_bytes(), before)
        self.index['bundles']['both']['skills'][0].pop('agents')
        self.index['bundles']['both']['skills'][0]['version'] = {'commit': self.git(self.source, 'rev-parse', 'HEAD')}
        self.publish_index(); self.call('tap', 'fetch', TAP)
        before = self.consumer_bytes()
        refused = self.install_bundle('both', code=4)
        self.assertEqual(refused['error']['details']['dimension'], 'version')
        self.assertEqual(self.consumer_bytes(), before)

    def test_held_versions_and_local_target_edits_are_preserved_on_refresh_removal(self):
        self.install_bundle('both')
        self.call('pin', TAP + '/alpha')
        self.call('project', 'set-agents', TAP + '/beta', 'codex')
        prior = self.lock()['packages']
        self.index['bundles']['both']['skills'] = []
        self.publish_index(); self.call('tap', 'fetch', TAP)
        result = self.call('bundle', 'upgrade', TAP + '/both')
        self.assertEqual(result['data']['removed'], [])
        self.assertEqual(self.lock()['packages'], prior)
        self.assertEqual(set(self.declaration()['bundle_state']['manual']), {TAP + '/alpha', TAP + '/beta'})

    def test_user_scope_uninstall_and_capabilities(self):
        self.call('bundle', 'install', TAP + '/both', '--user')
        self.assertTrue((self.personal / '.agents/skills/alpha').is_symlink())
        self.assertFalse((self.project / '.mask.json').exists())
        self.call('uninstall', TAP + '/alpha', '--user')
        self.call('bundle', 'install', TAP + '/both', '--user')
        value = json.loads((self.home / 'user.json').read_text(encoding='utf-8'))
        self.assertEqual([row['id'] for row in value['skills']], ['beta'])
        self.call('bundle', 'upgrade', TAP + '/both', '--user')
        self.call('status', '--user', '--check')
        commands = {row['name']: row for row in self.call('capabilities')['data']['commands']}
        self.assertTrue(commands['bundle.install']['plan_guard'])
        self.assertTrue(commands['bundle.uninstall']['plan_guard'])
        self.assertFalse(commands['bundle.uninstall']['network'])
        self.assertNotIn('bundle.apply', commands)
        self.assertNotIn('bundle.remove', commands)
        self.assertNotIn('profile.subscribe', commands)

    def test_install_keeps_frozen_rows_but_upgrade_advances_unheld_member_versions(self):
        self.install_bundle()
        prior = self.lock()['packages'][0]
        receipt = self.declaration()['bundle_state']['bundles'][TAP + '/first']
        with (self.source / 'skills/alpha/SKILL.md').open('a') as stream:
            stream.write('\nNew fixture content.\n')
        head = self.publish_index(); self.call('tap', 'fetch', TAP)
        self.assertFalse(self.install_bundle()['changed'])
        self.assertEqual(self.declaration()['bundle_state']['bundles'][TAP + '/first'], receipt)
        self.call('bundle', 'upgrade', TAP + '/first')
        self.assertNotEqual(self.lock()['packages'][0]['payload_digest'], prior['payload_digest'])
        self.assertEqual(self.lock()['packages'][0]['commit'], head)
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
        preview = self.call('bundle', 'install', TAP + '/workflow', '--dry-run')
        self.assertFalse(self.sentinel.exists())
        self.assertEqual(self.consumer_bytes(), before)
        result = self.install_bundle('workflow', code=4)
        self.assertEqual(result['error']['code'], 'confirmation.required')
        self.assertEqual(self.consumer_bytes(), before)
        result = self.call('bundle', 'install', TAP + '/workflow', '--approve-plan', preview['data']['plan_hash'], code=5)
        self.assertEqual(result['error']['code'], 'setup.failed')
        self.assertTrue(result['changed'])
        self.assertEqual(result['transaction'], 'committed')
        self.assertEqual(len(self.sentinel.read_text().splitlines()), 1)
        self.assertEqual(self.selected(), {TAP + '/alpha', TAP + '/implement-rfc'})
        self.assertFalse(self.call('status')['data']['healthy'])

    def test_bundle_setup_interruption_recovery_never_reruns_scripts(self):
        self.generated_bundle()
        preview = self.call('bundle', 'install', TAP + '/workflow', '--dry-run')
        self.fault('bundle', 'install', TAP + '/workflow', '--approve-plan', preview['data']['plan_hash'], label='setup.exited')
        self.assertEqual(json.loads((self.home / 'pending.json').read_text(encoding='utf-8'))['operation'], 'ensure')
        self.assertEqual(self.call('recover', '--complete', code=8)['error']['code'], 'setup.unverified')
        self.call('recover', '--rollback')
        self.assertEqual(len(self.sentinel.read_text().splitlines()), 1)
        self.assertEqual(self.selected(), {TAP + '/alpha', TAP + '/implement-rfc'})
        self.call('bundle', 'install', TAP + '/workflow', '--dry-run')

    def test_bundle_activation_recovery_uses_frozen_selection_and_receipt(self):
        preview = self.call('bundle', 'install', TAP + '/both', '--dry-run')
        expected = preview['data']['after']
        self.fault('bundle', 'install', TAP + '/both', '--approve-plan', preview['data']['plan_hash'], label='lock')
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
        refused = self.call('bundle', 'install', TAP + '/both', '--offline', code=4)
        self.assertEqual(refused['error']['code'], 'lock.resolution_required')
        self.assertEqual(self.consumer_bytes(), before)
        self.call('tap', 'fetch', 'other')
        refused = self.install_bundle('both', code=4)
        self.assertEqual(refused['error']['code'], 'target.collision')
        self.assertEqual(refused['error']['details']['contribution_origins']['other/alpha'], [TAP + '/both'])
        self.assertEqual(self.consumer_bytes(), before)
        self.index['bundles']['both']['skills'][0]['agents'] = ['nonexistent']
        self.publish_index(); self.call('tap', 'fetch', TAP)
        refused = self.install_bundle('both', code=4)
        self.assertEqual(refused['error']['code'], 'selection.invalid')

    def test_unchanged_definition_new_source_revision_stales_plan_and_human_output(self):
        preview = self.call('bundle', 'install', TAP + '/first', '--dry-run')
        self.publish_index(); self.call('tap', 'fetch', TAP)
        before = self.consumer_bytes()
        refused = self.call('bundle', 'install', TAP + '/first', '--approve-plan', preview['data']['plan_hash'], code=4)
        self.assertEqual(refused['error']['code'], 'plan.stale')
        self.assertEqual(self.consumer_bytes(), before)
        run = self.human('bundle', 'show', TAP + '/first')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('Bundle ' + TAP + '/first', run.stdout)
        self.assertFalse(self.parses_as_result_envelope(run.stdout))
        run = self.human('bundle', 'install', TAP + '/first', '--dry-run')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('Would install', run.stdout)

    def test_refresh_refuses_edited_deployment_before_any_consumer_change(self):
        self.install_bundle()
        leaf = self.project / '.agents/skills/alpha'
        leaf.unlink(); leaf.mkdir()
        (leaf / 'mine.md').write_text('Keep my edited fixture.\n')
        self.index['bundles']['first']['skills'] = []
        self.publish_index(); self.call('tap', 'fetch', TAP)
        before = self.consumer_bytes()
        refused = self.call('bundle', 'upgrade', TAP + '/first', code=4)
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
        preview = self.call('bundle', 'install', 'catalogue/pack', '--dry-run')
        self.assertEqual(preview['data']['bundle']['commit'], head)
        self.assertNotEqual(preview['data']['locked']['packages'][0]['commit'], head)
        self.call('bundle', 'install', 'catalogue/pack', '--approve-plan', preview['data']['plan_hash'])
        self.assertEqual(self.declaration()['bundle_state']['bundles']['catalogue/pack']['commit'], head)
        self.assertIn('catalogue', self.declaration()['sources'])
        refused = self.call('untap', 'catalogue', code=4)
        self.assertEqual(refused['error']['code'], 'source.referenced')

    def test_cold_approved_catalog_browse_offline_refusal_and_live_acquisition(self):
        cold = self.base / 'cold-machine'
        self.call('tap', TAP, self.upstream, '--home', cold)
        listed = self.call('bundle', 'list', '--home', cold)
        self.assertEqual(listed['data']['unavailable'][0]['source'], TAP)
        refused = self.call('bundle', 'install', TAP + '/first', '--home', cold, '--offline', code=4)
        self.assertEqual(refused['error']['code'], 'bundle.catalog_required')
        self.assertFalse((self.project / '.mask.json').exists())
        installed = self.call('bundle', 'install', TAP + '/first', '--home', cold)
        self.assertEqual(installed['data']['network'], 'fetch')
        self.assertEqual(installed['data']['acquisitions'][0]['source'], TAP)
        self.assertEqual(self.selected(), {TAP + '/alpha'})

    def test_exclusive_explicit_version_refresh_changes_only_authorized_lock(self):
        old = self.git(self.source, 'rev-parse', 'HEAD')
        self.index['bundles']['first']['skills'][0]['version'] = {'commit': old}
        self.publish_index(); self.call('tap', 'fetch', TAP)
        self.install_bundle()
        self.call('install', TAP + '/beta')
        beta = next(row for row in self.lock()['packages'] if row['id'] == 'beta')
        with (self.source / 'skills/alpha/SKILL.md').open('a') as stream:
            stream.write('\nNew explicitly selected version.\n')
        changed = self.publish_index()
        self.index['bundles']['first']['skills'][0]['version'] = {'commit': changed}
        self.publish_index(); self.call('tap', 'fetch', TAP)
        preview = self.call('bundle', 'upgrade', TAP + '/first', '--dry-run')
        self.assertEqual(preview['data']['bundle_changes']['changed'][0]['skill'], TAP + '/alpha')
        self.call('bundle', 'upgrade', TAP + '/first', '--approve-plan', preview['data']['plan_hash'])
        rows = {row['id']: row for row in self.lock()['packages']}
        self.assertEqual(rows['alpha']['commit'], changed)
        self.assertEqual(rows['beta'], beta)

    def test_uninstall_preview_exclusive_repeat_and_fresh_reinstall(self):
        before = self.consumer_bytes()
        absent = self.call('bundle', 'uninstall', 'unapproved/absent', '--offline')
        self.assertFalse(absent['changed'])
        self.assertEqual(self.consumer_bytes(), before)
        self.assertFalse((self.project / '.mask.json').exists())
        self.install_bundle('both')
        before = self.consumer_bytes()
        preview = self.call('bundle', 'uninstall', TAP + '/both', '--dry-run')
        self.assertEqual(preview['data']['removed'], [TAP + '/alpha', TAP + '/beta'])
        self.assertIsNone(preview['data']['expansion'])
        self.assertEqual(self.consumer_bytes(), before)
        human = self.human('bundle', 'uninstall', TAP + '/both', '--dry-run')
        self.assertEqual(human.returncode, 0, human.stderr)
        self.assertIn('Would uninstall', human.stdout)
        self.assertIn('- ' + TAP + '/alpha', human.stdout)
        self.call('bundle', 'uninstall', TAP + '/both', '--approve-plan', preview['data']['plan_hash'])
        self.assertEqual(self.selected(), set())
        self.assertEqual(self.lock()['packages'], [])
        self.assertNotIn(TAP + '/both', self.declaration()['bundle_state']['bundles'])
        self.assertFalse((self.project / '.agents/skills/alpha').exists())
        before = self.consumer_bytes()
        self.assertFalse(self.call('bundle', 'uninstall', TAP + '/both')['changed'])
        self.assertEqual(self.consumer_bytes(), before)
        self.install_bundle('both')
        self.assertEqual(self.selected(), {TAP + '/alpha', TAP + '/beta'})
        self.call('status', '--check')
        removed_surface = self.raw('bundle', 'apply', TAP + '/both', '--json')
        self.assertEqual(removed_surface.returncode, 2)

    def test_bundle_uninstall_preserves_manual_overlap_and_unrelated_exact_rows(self):
        self.install_bundle('both'); self.install_bundle('first')
        self.call('install', TAP + '/beta')
        from tests.public_support import CONSUMER_CONTEXT
        shutil.copytree(CONSUMER_CONTEXT, self.project / '.mask', dirs_exist_ok=True)
        self.call('install', TAP + '/implement-rfc')
        prior = self.lock()['packages']
        result = self.call('bundle', 'uninstall', TAP + '/both')
        self.assertEqual(result['data']['removed'], [])
        self.assertEqual(self.lock()['packages'], prior)
        self.assertEqual(self.selected(), {TAP + '/alpha', TAP + '/beta', TAP + '/implement-rfc'})
        self.assertEqual(set(self.declaration()['bundle_state']['bundles']), {TAP + '/first'})
        self.assertNotIn('bundle:' + TAP + '/both', self.declaration()['skills'][0].get('introduced_by', []))
        self.call('bundle', 'uninstall', TAP + '/first')
        self.assertEqual(self.selected(), {TAP + '/beta', TAP + '/implement-rfc'})
        self.assertEqual(self.lock()['packages'], [row for row in prior if row['id'] != 'alpha'])
        self.assertTrue((self.project / '.agents/skills/beta').is_symlink())

    def test_bundle_uninstall_promotes_held_and_local_edit_survivors_for_reinstall(self):
        self.install_bundle('both')
        self.call('pin', TAP + '/alpha')
        self.call('project', 'set-agents', TAP + '/beta', 'codex')
        prior = self.lock()['packages']
        result = self.call('bundle', 'uninstall', TAP + '/both')
        self.assertEqual(result['data']['removed'], [])
        self.assertEqual(set(self.declaration()['bundle_state']['manual']), {TAP + '/alpha', TAP + '/beta'})
        self.assertEqual(self.declaration()['bundle_state']['bundles'], {})
        self.assertEqual(self.lock()['packages'], prior)
        self.install_bundle('both')
        self.assertEqual(self.lock()['packages'], prior)
        self.assertEqual(next(row for row in self.declaration()['skills'] if row['id'] == 'beta')['agents'], ['codex'])
        self.call('bundle', 'uninstall', TAP + '/both')
        self.assertEqual(self.selected(), {TAP + '/alpha', TAP + '/beta'})

    def test_bundle_uninstall_uses_frozen_receipt_without_catalogue_or_network(self):
        self.install_bundle('both')
        self.index['bundles'] = {}
        self.publish_index(); self.call('tap', 'fetch', TAP)
        remove_tree(self.home / 'sources')  # Only disposable cached fixture data.
        remove_tree(self.upstream)  # Even the remote is unavailable.
        result = self.call('bundle', 'uninstall', TAP + '/both', '--offline')
        self.assertEqual(result['data']['network'], 'none')
        self.assertEqual(self.selected(), set())
        self.assertFalse(self.call('bundle', 'uninstall', TAP + '/both', '--offline')['changed'])

    def test_bundle_uninstall_plan_stales_after_manual_promotion_or_receipt_removal(self):
        self.install_bundle('both')
        preview = self.call('bundle', 'uninstall', TAP + '/both', '--dry-run')
        self.call('install', TAP + '/alpha')
        before = self.consumer_bytes()
        result = self.call('bundle', 'uninstall', TAP + '/both', '--approve-plan', preview['data']['plan_hash'], code=4)
        self.assertEqual(result['error']['code'], 'plan.stale')
        self.assertEqual(self.consumer_bytes(), before)
        preview = self.call('bundle', 'uninstall', TAP + '/both', '--dry-run')
        self.call('bundle', 'uninstall', TAP + '/both')
        before = self.consumer_bytes()
        result = self.call('bundle', 'uninstall', TAP + '/both', '--approve-plan', preview['data']['plan_hash'], code=4)
        self.assertEqual(result['error']['code'], 'plan.stale')
        self.assertEqual(self.consumer_bytes(), before)

    def test_bundle_uninstall_frozen_recovery_does_not_rerun_setup(self):
        self.generated_bundle()
        preview = self.call('bundle', 'install', TAP + '/workflow', '--dry-run')
        self.call('bundle', 'install', TAP + '/workflow', '--approve-plan', preview['data']['plan_hash'])
        self.assertEqual(len(self.sentinel.read_text().splitlines()), 1)
        preview = self.call('bundle', 'uninstall', TAP + '/workflow', '--dry-run')
        self.fault('bundle', 'uninstall', TAP + '/workflow', '--approve-plan', preview['data']['plan_hash'], label='lock')
        self.assertEqual(json.loads((self.home / 'pending.json').read_text(encoding='utf-8'))['operation'], 'remove')
        self.index['bundles']['workflow']['skills'] = [dict(source=TAP, id='beta')]
        self.publish_index()
        blocked = self.call('bundle', 'uninstall', TAP + '/workflow', code=8)
        self.assertEqual(blocked['error']['code'], 'recovery.required')
        self.call('recover', '--complete')
        self.assertEqual(self.declaration(), preview['data']['after'])
        self.assertEqual(self.selected(), set())
        self.assertEqual(len(self.sentinel.read_text().splitlines()), 1)
        self.call('status', '--check')

    def test_bundle_uninstall_rollback_restores_receipt_and_links_without_setup(self):
        self.generated_bundle()
        preview = self.call('bundle', 'install', TAP + '/workflow', '--dry-run')
        self.call('bundle', 'install', TAP + '/workflow', '--approve-plan', preview['data']['plan_hash'])
        declaration, locked = self.declaration(), self.lock()
        preview = self.call('bundle', 'uninstall', TAP + '/workflow', '--dry-run')
        self.fault('bundle', 'uninstall', TAP + '/workflow', '--approve-plan', preview['data']['plan_hash'], label='link_unlinked')
        self.call('recover', '--rollback')
        self.assertEqual(self.declaration(), declaration)
        self.assertEqual(self.lock(), locked)
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())
        self.assertTrue((self.project / '.claude/skills/implement-rfc').is_symlink())
        self.assertEqual(len(self.sentinel.read_text().splitlines()), 1)
        self.call('status', '--check')

    def test_bundle_uninstall_refuses_edited_deployment_before_receipt_changes(self):
        self.install_bundle()
        leaf = self.project / '.agents/skills/alpha'
        leaf.unlink(); leaf.mkdir()
        (leaf / 'mine.md').write_text('Preserve fixture edit.')
        before = self.consumer_bytes()
        result = self.call('bundle', 'uninstall', TAP + '/first', code=4)
        self.assertEqual(result['error']['code'], 'target.collision')
        self.assertEqual(self.consumer_bytes(), before)

    def test_bundle_uninstall_refuses_missing_exact_lock_without_resolving_new_versions(self):
        self.install_bundle('both')
        (self.project / '.mask.lock.json').unlink()  # Missing lock in the disposable consumer.
        before = self.consumer_bytes()
        result = self.call('bundle', 'uninstall', TAP + '/both', code=4)
        self.assertEqual(result['error']['code'], 'lock.resolution_required')
        self.assertEqual(self.consumer_bytes(), before)

    def test_personal_bundle_uninstall_preserves_manual_member_and_has_no_aggregate(self):
        self.call('bundle', 'install', TAP + '/both', '--user')
        self.call('install', TAP + '/alpha', '--user')
        result = self.call('bundle', 'uninstall', TAP + '/both', '--user')
        self.assertEqual(result['data']['removed'], [TAP + '/beta'])
        value = json.loads((self.home / 'user.json').read_text(encoding='utf-8'))
        self.assertEqual([row['id'] for row in value['skills']], ['alpha'])
        self.assertEqual(value['bundle_state']['bundles'], {})
        self.assertTrue((self.personal / '.agents/skills/alpha').is_symlink())
        self.assertFalse((self.personal / '.agents/skills/beta').exists())
        self.assertFalse((self.project / '.mask.json').exists())
        self.assertFalse(self.call('bundle', 'uninstall', TAP + '/both', '--user')['changed'])
        self.assertEqual(self.raw('bundle', 'uninstall', TAP + '/both', '--all', '--json').returncode, 2)

    def test_upgrade_combines_definition_and_versions_in_one_diff_and_guard(self):
        self.install_bundle()
        prior = self.lock()['packages'][0]
        self.index['bundles']['first']['skills'].append(dict(source=TAP, id='beta'))
        with (self.source / 'skills/alpha/SKILL.md').open('a') as stream:
            stream.write('Updated alpha package.\n')
        head = self.publish_index(); self.call('tap', 'fetch', TAP)
        before = self.consumer_bytes()
        preview = self.call('bundle', 'upgrade', TAP + '/first', '--dry-run')
        self.assertEqual(preview['data']['added'], [TAP + '/beta'])
        self.assertEqual(preview['data']['versions'][0]['before_commit'], prior['commit'])
        self.assertEqual(self.consumer_bytes(), before)
        human = self.human('bundle', 'upgrade', TAP + '/first', '--dry-run')
        self.assertIn('version ' + TAP + '/alpha', human.stdout)
        self.assertIn('+ ' + TAP + '/beta', human.stdout)
        self.call('bundle', 'upgrade', TAP + '/first', '--approve-plan', preview['data']['plan_hash'])
        self.assertEqual(next(row for row in self.lock()['packages'] if row['id'] == 'alpha')['commit'], head)
        self.assertEqual(self.selected(), {TAP + '/alpha', TAP + '/beta'})
        self.assertFalse(self.call('bundle', 'upgrade', TAP + '/first', '--offline')['changed'])

    def test_upgrade_shared_manual_members_compatible_selectors_holds_and_local_edits(self):
        self.install_bundle('both'); self.install_bundle('first')
        self.call('install', TAP + '/alpha')
        prior = {row['id']: row for row in self.lock()['packages']}
        self.call('project', 'set-agents', TAP + '/beta', 'codex')
        for name in ('alpha', 'beta'):
            with (self.source / f'skills/{name}/SKILL.md').open('a') as stream:
                stream.write('New fixture bytes.\n')
        head = self.publish_index(); self.call('tap', 'fetch', TAP)
        result = self.call('bundle', 'upgrade', TAP + '/both', '--offline')
        current = {row['id']: row for row in self.lock()['packages']}
        self.assertEqual(current['alpha']['commit'], head)  # Compatible manual + overlapping selectors follow the same ref.
        self.assertEqual(current['beta'], prior['beta'])  # Local target edit retains its exact package.
        self.assertIn(TAP + '/alpha', self.declaration()['bundle_state']['manual'])
        self.assertIn(TAP + '/first', self.declaration()['bundle_state']['bundles'])
        self.assertIn('locally_modified_version', [row['reason'] for row in result['data']['preserved']])
        self.call('pin', TAP + '/alpha')
        with (self.source / 'skills/alpha/SKILL.md').open('a') as stream:
            stream.write('New held fixture bytes.\n')
        self.publish_index(); self.call('tap', 'fetch', TAP)
        self.call('bundle', 'upgrade', TAP + '/both', '--offline')
        self.assertEqual(self.lock()['packages'], list(current.values()))

    def test_upgrade_stale_package_preview_and_frozen_recovery(self):
        self.install_bundle()
        with (self.source / 'skills/alpha/SKILL.md').open('a') as stream:
            stream.write('First update.\n')
        self.publish_index(); self.call('tap', 'fetch', TAP)
        preview = self.call('bundle', 'upgrade', TAP + '/first', '--dry-run')
        with (self.source / 'skills/alpha/SKILL.md').open('a') as stream:
            stream.write('Later update.\n')
        self.publish_index(); self.call('tap', 'fetch', TAP)
        before = self.consumer_bytes()
        result = self.call('bundle', 'upgrade', TAP + '/first', '--approve-plan', preview['data']['plan_hash'], code=4)
        self.assertEqual(result['error']['code'], 'plan.stale')
        self.assertEqual(self.consumer_bytes(), before)
        preview = self.call('bundle', 'upgrade', TAP + '/first', '--dry-run')
        self.fault('bundle', 'upgrade', TAP + '/first', '--approve-plan', preview['data']['plan_hash'], label='lock')
        self.assertEqual(json.loads((self.home / 'pending.json').read_text(encoding='utf-8'))['operation'], 'upgrade')
        self.index['bundles']['first']['skills'] = []
        self.publish_index()
        self.call('recover', '--complete')
        self.assertEqual(self.declaration(), preview['data']['after'])
        self.assertEqual(self.lock(), preview['data']['locked'])
        self.call('status', '--check')

    def test_upgrade_all_installed_definitions_projects_personal_holds_and_stale_guard(self):
        second = self.base / 'second-project'; second.mkdir(); self.git(second, 'init', '-b', 'main')
        self.install_bundle()
        self.call('bundle', 'install', TAP + '/first', '--project', second)
        self.call('bundle', 'install', TAP + '/first', '--user')
        self.call('pin', TAP + '/alpha', '--project', second)
        held = json.loads((second / '.mask.lock.json').read_text(encoding='utf-8'))['packages'][0]
        self.call('install', TAP + '/beta')
        self.index['bundles']['first']['skills'].append(dict(source=TAP, id='beta'))
        with (self.source / 'skills/alpha/SKILL.md').open('a') as stream:
            stream.write('Aggregate update.\n')
        self.publish_index(); self.call('tap', 'fetch', TAP)
        before = self.consumer_bytes()
        preview = self.call('upgrade', '--all', '--dry-run')
        self.assertEqual(len(preview['data']['bundle_updates']), 3)
        self.assertEqual(self.consumer_bytes(), before)
        human = self.human('upgrade', '--all', '--dry-run')
        self.assertIn('Bundles in ', human.stdout)
        self.assertIn('+ ' + TAP + '/beta', human.stdout)
        self.publish_index(); self.call('tap', 'fetch', TAP)  # Same definition, new source revision still stales approval.
        before = self.consumer_bytes()
        result = self.call('upgrade', '--all', '--approve-plan', preview['data']['plan_hash'], code=4)
        self.assertEqual(result['error']['code'], 'plan.stale')
        self.assertEqual(self.consumer_bytes(), before)
        preview = self.call('upgrade', '--all', '--dry-run')
        self.call('upgrade', '--all', '--approve-plan', preview['data']['plan_hash'])
        for declaration in (self.declaration(), json.loads((second / '.mask.json').read_text(encoding='utf-8')), json.loads((self.home / 'user.json').read_text(encoding='utf-8'))):
            self.assertEqual({row['id'] for row in declaration['skills']}, {'alpha', 'beta'})
        self.assertEqual(next(row for row in json.loads((second / '.mask.lock.json').read_text(encoding='utf-8'))['packages'] if row['id'] == 'alpha'), held)
        self.call('status', '--all', '--check')

    def test_default_upgrade_adopts_overlapping_definitions_together_and_ids_stay_bounded(self):
        self.install_bundle('both'); self.install_bundle('first')
        old = self.declaration()['bundle_state']['bundles'][TAP + '/first']
        new = self.publish_index()
        for key in ('first', 'both'):
            self.index['bundles'][key]['skills'][0]['version'] = {'commit': new}
        self.publish_index(); self.call('tap', 'fetch', TAP)
        self.call('upgrade', TAP + '/alpha', '--offline')
        self.assertEqual(self.declaration()['bundle_state']['bundles'][TAP + '/first'], old)
        self.call('upgrade', '--offline')
        self.assertEqual(self.declaration()['skills'][0]['version'], {'commit': new})
        self.assertEqual(self.lock()['packages'][0]['commit'], new)
        self.assertIn(TAP + '/both', self.declaration()['bundle_state']['bundles'])

    def test_upgrade_all_reports_conflicting_scope_and_applies_valid_scope_truthfully(self):
        self.index['bundles']['first']['skills'][0]['agents'] = ['codex']
        self.index['bundles']['both']['skills'][0]['agents'] = ['codex']
        self.publish_index(); self.call('tap', 'fetch', TAP)
        self.install_bundle('first')
        second = self.base / 'second-project'; second.mkdir(); self.git(second, 'init', '-b', 'main')
        self.call('bundle', 'install', TAP + '/first', '--project', second)
        self.call('bundle', 'install', TAP + '/both', '--project', second)
        original = (second / '.mask.json').read_bytes(), (second / '.mask.lock.json').read_bytes()
        self.index['bundles']['first']['skills'][0]['agents'] = ['claude']
        self.publish_index(); self.call('tap', 'fetch', TAP)
        preview = self.call('upgrade', '--all', '--dry-run')
        rows = {row['root']: row for row in preview['data']['consumers']}
        self.assertEqual(rows[str(second)]['status'], 'blocked')
        self.assertEqual(rows[str(second)]['error']['code'], 'bundle.conflict')
        result = self.call('upgrade', '--all', '--approve-plan', preview['data']['plan_hash'], code=4)
        self.assertEqual(result['error']['code'], 'upgrade.incomplete')
        self.assertTrue(result['changed'])
        self.assertEqual((second / '.mask.json').read_bytes(), original[0])
        self.assertEqual((second / '.mask.lock.json').read_bytes(), original[1])
        self.assertEqual(self.declaration()['skills'][0]['agents'], ['claude'])

    def test_upgrade_respects_manual_exact_selector_and_reports_competing_origins(self):
        old = self.git(self.source, 'rev-parse', 'HEAD')
        self.index['bundles']['first']['skills'][0]['version'] = {'commit': old}
        self.publish_index(); self.call('tap', 'fetch', TAP)
        self.install_bundle(); self.call('install', TAP + '/alpha')
        with (self.source / 'skills/alpha/SKILL.md').open('a') as stream:
            stream.write('Explicit new constraint.\n')
        new = self.publish_index()
        self.index['bundles']['first']['skills'][0]['version'] = {'commit': new}
        self.publish_index(); self.call('tap', 'fetch', TAP)
        before = self.consumer_bytes()
        result = self.call('bundle', 'upgrade', TAP + '/first', '--offline', code=4)
        self.assertEqual(result['error']['code'], 'bundle.conflict')
        self.assertEqual(result['error']['details']['dimension'], 'version')
        self.assertIn('manual', result['error']['details']['origins'])
        self.assertEqual(self.consumer_bytes(), before)

    def test_bundle_upgrade_moved_tag_requires_explicit_ref_rebind(self):
        self.git(self.source, 'tag', 'release')
        self.git(self.source, 'push', '-q', str(self.upstream), 'refs/tags/release')
        self.index['bundles']['first']['skills'][0]['version'] = {'ref': 'refs/tags/release'}
        self.publish_index(); self.call('tap', 'fetch', TAP)
        self.install_bundle()
        old = self.lock()['packages'][0]
        with (self.source / 'skills/alpha/SKILL.md').open('a') as stream:
            stream.write('Moved tagged package.\n')
        new = self.publish_index()
        self.git(self.source, 'tag', '-f', 'release')
        self.git(self.source, 'push', '-q', '--force', str(self.upstream), 'refs/tags/release')
        self.call('tap', 'fetch', TAP)
        before = self.consumer_bytes()
        result = self.call('bundle', 'upgrade', TAP + '/first', '--offline', code=4)
        self.assertEqual(result['error']['code'], 'lock.ref_rebound')
        self.assertEqual(self.consumer_bytes(), before)
        preview = self.call('bundle', 'upgrade', TAP + '/first', '--allow-ref-rebind', '--dry-run')
        self.call('bundle', 'upgrade', TAP + '/first', '--allow-ref-rebind', '--approve-plan', preview['data']['plan_hash'])
        self.assertEqual(self.lock()['packages'][0]['commit'], new)
        self.assertNotEqual(self.lock()['packages'][0]['payload_digest'], old['payload_digest'])

    def test_aggregate_upgrade_recovery_uses_frozen_membership_and_package_rows(self):
        self.install_bundle()
        self.call('bundle', 'install', TAP + '/first', '--user')
        self.index['bundles']['first']['skills'].append(dict(source=TAP, id='beta'))
        self.publish_index(); self.call('tap', 'fetch', TAP)
        preview = self.call('upgrade', '--all', '--dry-run')
        self.fault('upgrade', '--all', '--offline', '--approve-plan', preview['data']['plan_hash'], label='lock')
        self.index['bundles']['first']['skills'] = []
        self.publish_index()
        self.call('recover', '--complete')
        self.assertEqual(self.selected(), {TAP + '/alpha', TAP + '/beta'})
        self.assertEqual({row['id'] for row in json.loads((self.home / 'user.json').read_text(encoding='utf-8'))['skills']}, {'alpha', 'beta'})
        self.call('status', '--all', '--check')

    def test_upgrade_setup_still_requires_review_and_recovery_never_reruns_scripts(self):
        self.generated_bundle()
        preview = self.call('bundle', 'install', TAP + '/workflow', '--dry-run')
        self.call('bundle', 'install', TAP + '/workflow', '--approve-plan', preview['data']['plan_hash'])
        with (self.package / 'scripts/prepare_fixture_roles.py').open('a') as stream:
            stream.write('\n# New declared setup input revision.\n')
        self.publish_index(); self.call('tap', 'fetch', TAP)
        before = self.consumer_bytes()
        preview = self.call('bundle', 'upgrade', TAP + '/workflow', '--dry-run')
        self.assertTrue(preview['data']['setup']['actions'])
        self.assertEqual(self.consumer_bytes(), before)
        self.assertEqual(self.call('bundle', 'upgrade', TAP + '/workflow', '--offline', code=4)['error']['code'], 'confirmation.required')
        self.fault('bundle', 'upgrade', TAP + '/workflow', '--approve-plan', preview['data']['plan_hash'], label='setup.exited')
        self.assertEqual(len(self.sentinel.read_text().splitlines()), 2)
        self.assertEqual(self.call('recover', '--complete', code=8)['error']['code'], 'setup.unverified')
        self.call('recover', '--rollback')
        self.assertEqual(len(self.sentinel.read_text().splitlines()), 2)
