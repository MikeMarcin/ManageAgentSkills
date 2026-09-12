"""Public deployment contract tests using disposable packages and consumers."""
import json
import subprocess
import sys

from tests.test_setup import SetupFixture
from tests.public_support import ENTRY


class DeploymentContracts(SetupFixture):
    def descriptor(self, **changes):
        path = self.package / 'mask-workflow.json'
        value = json.loads(path.read_text())
        value.update(changes)
        path.write_text(json.dumps(value, indent=2) + '\n')
        self.commit('deployment contract fixture')

    def repair(self, *args):
        return self.machine('ensure', '--project', self.project, '--repair', *args)

    def legacy(self):
        path = self.project / '.mask/skill-config/implement-rfc/native-roles.lock.json'
        path.write_bytes(self.lock.read_bytes())
        return path

    def test_paths_are_published_in_capabilities_and_request(self):
        paths = self.machine('capabilities')['data']['workflow']['paths']
        self.assertEqual(paths['native_role_lock'].format(skill='implement-rfc'), self.lock.relative_to(self.project).as_posix())
        self.write_script(before="    assert request['paths']['native_role_lock'] == '.mask/generated/implement-rfc/native-roles.lock.json'\n    assert request['paths']['retired_native_role_locks'] == ['.mask/skill-config/implement-rfc/native-roles.lock.json']\n")
        self.commit('request path assertion')
        self.assertTrue(self.repair()['ok'])

    def test_noop_input_edit_can_vouch_for_exact_prior_lock(self):
        self.assertTrue(self.repair()['ok'])
        old = self.lock.read_bytes()
        lock = json.loads(old)
        helper = self.package / 'scripts/helper.py'
        helper.write_text(helper.read_text() + '\n# No output changes.\n')
        self.descriptor(compatible_locks=[{key: lock[key] for key in ('contract_sha256', 'role_inputs_sha256')}])
        result = self.machine('ensure', '--project', self.project)
        self.assertTrue(result['ok'], result)
        self.assertEqual(self.launches(), 1)
        self.assertEqual(self.lock.read_bytes(), old)
        role = self.project / '.codex/agents/rfc-integrator.toml'
        role.write_text(role.read_text() + '# changed output\n')
        self.assertFalse(self.machine('ensure', '--project', self.project)['ok'])
        self.assertEqual(self.launches(), 1)

    def test_compatibility_keeps_consumer_inputs_and_hash_pair_enforced(self):
        self.assertTrue(self.repair()['ok'])
        lock = json.loads(self.lock.read_text())
        pair = {key: lock[key] for key in ('contract_sha256', 'role_inputs_sha256')}
        self.descriptor(compatible_locks=[pair])
        config = self.project / '.mask/skill-config/implement-rfc/project.json'
        original = config.read_bytes()
        config.write_bytes(original + b'\n')
        self.assertFalse(self.machine('ensure', '--project', self.project)['ok'])
        config.write_bytes(original)
        pair['contract_sha256'] = '0' * 64
        self.descriptor(compatible_locks=[pair])
        self.assertFalse(self.machine('ensure', '--project', self.project)['ok'])
        self.assertEqual(self.launches(), 1)

    def test_retired_lock_cleanup_is_explicit_backed_up_and_idempotent(self):
        self.assertTrue(self.repair()['ok'])
        legacy = self.legacy()
        original = legacy.read_bytes()
        for args in [(), ('--check',), ('--repair', '--dry-run'), ('--repair', '--check')]:
            result = self.machine('ensure', '--project', self.project, *args)
            self.assertEqual(legacy.read_bytes(), original)
            self.assertFalse((self.home / 'backups').exists())
        result = self.repair()
        self.assertTrue(result['ok'], result)
        self.assertFalse(legacy.exists())
        self.assertEqual(len(result['data']['backups']), 1)
        backup = result['data']['backups'][0]
        from pathlib import Path
        self.assertEqual(Path(backup['path']).read_bytes(), original)
        self.assertEqual(backup['state'], 'saved')
        self.assertFalse(self.repair()['changed'])
        self.assertEqual(self.launches(), 1)

    def test_active_fallback_is_preserved_without_execution(self):
        self.assertTrue(self.repair()['ok'])
        legacy = self.legacy()
        self.lock.unlink()
        result = self.repair()
        self.assertTrue(result['ok'], result)
        self.assertTrue(legacy.exists())
        self.assertEqual(self.launches(), 1)
        report = result['data']['workflow_readiness'][0]['skills'][0]
        self.assertEqual(report['retired_files'][0]['state'], 'in_use')

    def test_stale_fallback_is_cleaned_after_successful_setup(self):
        self.assertTrue(self.repair()['ok'])
        legacy = self.legacy()
        self.lock.unlink()
        helper = self.package / 'scripts/helper.py'
        helper.write_text(helper.read_text() + '\n# changed package inputs\n')
        self.commit('stale fixture')
        result = self.repair()
        self.assertTrue(result['ok'], result)
        self.assertTrue(self.lock.exists())
        self.assertFalse(legacy.exists())
        self.assertEqual(self.launches(), 2)

    def test_descriptor_retired_files_and_unsafe_entries(self):
        relative = '.mask/skill-config/implement-rfc/obsolete.json'
        self.descriptor(retired_paths=[relative])
        self.assertTrue(self.repair()['ok'])
        path = self.project / relative
        path.write_text('repository-owned old config\r\n', newline='')
        self.assertTrue(self.machine('ensure', '--project', self.project)['ok'])
        self.assertTrue(path.exists())
        result = self.repair()
        self.assertTrue(result['ok'], result)
        self.assertFalse(path.exists())
        from pathlib import Path
        self.assertEqual(Path(result['data']['backups'][0]['path']).read_bytes(), b'repository-owned old config\r\n')
        outside = self.base / 'outside'
        outside.write_text('keep')
        path.symlink_to(outside)
        result = self.repair()
        self.assertTrue(path.is_symlink())
        self.assertEqual(outside.read_text(), 'keep')
        self.assertIn('unsafe', [row['state'] for row in result['data']['workflow_readiness'][0]['skills'][0]['retired_files']])

    def test_invalid_retirement_and_compatibility_declarations_fail_closed(self):
        for changes in [dict(retired_paths=['../outside']), dict(retired_paths=['.mask/skill-config/other/old.json']),
                        dict(retired_paths=['.mask/skill-config/implement-rfc/project.json']),
                        dict(retired_paths=['.mask/generated/implement-rfc/native-roles.lock.json']),
                        dict(compatible_locks=[dict(contract_sha256='0' * 64, role_inputs_sha256='bogus')])]:
            self.descriptor(retired_paths=[], compatible_locks=[])
            self.descriptor(**changes)
            result = self.repair()
            self.assertFalse(result['ok'], changes)
            self.assertEqual(self.launches(), 0)

    def test_cleanup_crash_can_roll_back_or_complete_without_setup(self):
        self.assertTrue(self.repair()['ok'])
        legacy = self.legacy()
        original = legacy.read_bytes()
        script = '''
import os, sys
sys.path.insert(0, sys.argv[1])
import mask, mask_fs
def checkpoint(label):
    if label == 'retired_file': os._exit(97)
mask_fs.checkpoint = checkpoint
raise SystemExit(mask.main(sys.argv[2:]))
'''
        for disposition in ('--rollback', '--complete'):
            run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), 'ensure', '--project', str(self.project), '--repair', '--json'],
                                 capture_output=True, text=True, env=self.environment(), timeout=60)
            self.assertEqual(run.returncode, 97, run.stdout + run.stderr)
            self.assertFalse(legacy.exists())
            result = self.machine('recover', disposition)
            self.assertTrue(result['ok'], result)
            self.assertEqual(legacy.exists(), disposition == '--rollback')
            if legacy.exists():
                self.assertEqual(legacy.read_bytes(), original)
        self.assertEqual(self.launches(), 1)

    def test_retired_file_changed_by_setup_is_preserved(self):
        self.assertTrue(self.repair()['ok'])
        legacy = self.legacy()
        self.lock.unlink()
        self.write_script(before="    (args.repo_root / '.mask/skill-config/implement-rfc/native-roles.lock.json').write_text('concurrent edit\\n')\n")
        self.commit('setup changes retired file')
        result = self.repair()
        self.assertFalse(result['ok'], result)
        self.assertEqual(legacy.read_text(), 'concurrent edit\n')
        self.assertEqual(self.launches(), 2)

    def test_cleanup_recovery_refuses_external_edit_and_unsafe_journal_path(self):
        self.assertTrue(self.repair()['ok'])
        legacy = self.legacy()
        original = legacy.read_bytes()
        script = '''
import os, sys
sys.path.insert(0, sys.argv[1])
import mask, mask_fs
mask_fs.checkpoint = lambda label: os._exit(97) if label == 'retired_file' else None
raise SystemExit(mask.main(sys.argv[2:]))
'''
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), 'ensure', '--project', str(self.project), '--repair', '--json'],
                             capture_output=True, text=True, env=self.environment(), timeout=60)
        self.assertEqual(run.returncode, 97)
        legacy.write_text('external edit')
        self.assertEqual(self.machine('recover', '--rollback')['error']['code'], 'recovery.conflict')
        self.assertEqual(legacy.read_text(), 'external edit')
        legacy.write_bytes(original)
        pending = self.home / 'pending.json'
        journal = pending.read_bytes()
        changed = json.loads(journal)
        changed['retired_files'][0]['relative'] = '../outside'
        pending.write_text(json.dumps(changed))
        self.assertEqual(self.machine('recover', '--complete')['error']['code'], 'recovery.conflict')
        pending.write_bytes(journal)
        self.assertTrue(self.machine('recover', '--rollback')['ok'])
