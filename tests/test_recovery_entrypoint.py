"""Public repair/recovery on interrupted setup; no live homes or package reruns."""
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import unittest

from tests.public_support import PublicFixture, ENTRY
from tests import test_cli_v2 as lifecycle
from tests.test_setup import SetupFixture


class RecoveryEntrypoint(PublicFixture):
    bootstrap = lifecycle.CliV2.bootstrap
    raw = lifecycle.CliV2.raw
    setUp = lifecycle.SetupV2.setUp
    write_script = SetupFixture.write_script

    def interrupt_install(self, checkpoint='native_role'):
        preview = self.machine('install', 'implement-rfc', '--dry-run')
        script = '''
import os, sys
sys.path.insert(0, sys.argv[1])
import mask, mask_fs
mask_fs.checkpoint = lambda label: os._exit(99) if label == sys.argv[2] else None
raise SystemExit(mask.main(sys.argv[3:]))
'''
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), checkpoint,
                              'install', 'implement-rfc', '--no-update', '--approve-plan', preview['data']['plan_hash'], '--json'],
                             cwd=self.project, env=self.environment(), capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 99, run.stderr)
        return json.loads((self.home / 'pending.json').read_text())

    def commit_work(self):
        (self.project / 'work.txt').write_text('Unrelated work\n')
        self.git(self.project, 'add', 'work.txt', '.mask.json', '.mask.lock.json')
        self.git(self.project, 'commit', '-m', 'Commit work and existing skill controls')

    def launches(self):
        return len(self.sentinel.read_text().splitlines()) if self.sentinel.exists() else 0

    def test_bare_recover_is_read_only_and_guides_repair(self):
        self.assertTrue(self.machine('recover')['ok'])
        self.interrupt_install()
        journal = (self.home / 'pending.json').read_bytes()
        text = self.human('recover')
        self.assertEqual(text.returncode, 0, text.stderr)
        self.assertIn('Interrupted setup: implement-rfc', text.stdout)
        self.assertIn('Next: mask repair', text.stdout)
        self.assertEqual(journal, (self.home / 'pending.json').read_bytes())
        self.assertEqual(self.launches(), 1)
        blocked = self.machine('update')
        self.assertEqual(blocked['error']['code'], 'recovery.required', blocked)
        self.assertIn("'mask repair'", blocked['error']['remediation'][0]['message'])
        self.assertEqual(self.machine('recover', '--complete', '--rollback')['error']['code'], 'invocation.invalid')

    def test_reviewed_repair_completes_after_commit_and_preserves_bytecode(self):
        pending = self.interrupt_install()
        self.commit_work()
        row = pending['after_state']['projects'][str(self.project)]['last_lock']['packages'][0]
        artifact = self.home / 'store/v1' / row['payload_digest'].removeprefix('sha256:') / 'payload/implement-rfc'
        cache = artifact / 'scripts/__pycache__/incidental.pyc'
        cache.parent.mkdir()
        cache.write_bytes(b'not executed by recovery')
        before = (self.home / 'pending.json').read_bytes()
        preview = self.machine('repair', '--dry-run')
        self.assertTrue(preview['ok'], preview)
        self.assertEqual(preview['data']['recovery']['mode'], 'complete')
        self.assertEqual(before, (self.home / 'pending.json').read_bytes())
        self.assertTrue(cache.exists())
        refused = self.machine('repair')
        self.assertEqual(refused['error']['code'], 'confirmation.required', refused)
        self.assertTrue(cache.exists(), 'inspection must not delete cache before review')
        stale = self.machine('repair', '--approve-plan', 'sha256:' + '0' * 64)
        self.assertEqual(stale['error']['code'], 'plan.stale')
        result = self.machine('repair', '--approve-plan', preview['data']['plan_hash'])
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['transaction'], 'committed')
        self.assertFalse((self.home / 'pending.json').exists())
        self.assertEqual(cache.read_bytes(), b'not executed by recovery')
        self.assertEqual(self.launches(), 1)
        self.assertTrue(self.lock.is_file())
        self.assertTrue(self.machine('recover')['ok'])

    def test_changed_inputs_roles_controls_and_unknown_artifact_files_still_refuse(self):
        pending = self.interrupt_install()
        self.commit_work()
        row = pending['after_state']['projects'][str(self.project)]['last_lock']['packages'][0]
        artifact = self.home / 'store/v1' / row['payload_digest'].removeprefix('sha256:') / 'payload/implement-rfc'
        changes = [self.project / '.mask/skill-config/implement-rfc/project.md',
                   self.project / pending['native_roles'][0]['relative'],
                   self.project / '.mask.lock.json', artifact / 'scripts/helper.py',
                   artifact / 'scripts/__pycache__/unknown.txt']
        journal = (self.home / 'pending.json').read_bytes()
        for path in changes:
            with self.subTest(path=path):
                before = path.read_bytes() if path.exists() else None
                mode = stat.S_IMODE(path.stat().st_mode) if before is not None else 0o644
                path.parent.mkdir(parents=True, exist_ok=True)
                if before is not None:
                    path.chmod(mode | stat.S_IWUSR)
                path.write_bytes(b'Edited; preserve me\n')
                path.chmod(mode)
                result = self.machine('repair', '--dry-run')
                self.assertFalse(result['ok'], result)
                self.assertEqual(path.read_bytes(), b'Edited; preserve me\n')
                self.assertEqual(journal, (self.home / 'pending.json').read_bytes())
                if before is None:
                    path.unlink()
                else:
                    path.chmod(mode | stat.S_IWUSR)
                    path.write_bytes(before)
                    path.chmod(mode)
        self.assertEqual(self.launches(), 1)

    def test_non_setup_journal_keeps_head_guard(self):
        self.interrupt_install('intent')
        (self.project / 'unrelated').write_text('work')
        self.git(self.project, 'add', 'unrelated')
        self.git(self.project, 'commit', '-m', 'Changed head')
        result = self.machine('recover', '--complete', '--dry-run')
        self.assertEqual(result['error']['code'], 'recovery.conflict', result)
        self.assertEqual(self.launches(), 0)

    def test_linked_role_and_linked_bytecode_are_preserved_and_refused(self):
        pending = self.interrupt_install()
        self.commit_work()
        row = pending['after_state']['projects'][str(self.project)]['last_lock']['packages'][0]
        artifact = self.home / 'store/v1' / row['payload_digest'].removeprefix('sha256:') / 'payload/implement-rfc'
        outsider = self.base / 'outside.txt'
        outsider.write_text('Preserve outside data\n')
        destinations = [self.project / pending['native_roles'][0]['relative'],
                        artifact / 'scripts/__pycache__/linked.pyc']
        journal = (self.home / 'pending.json').read_bytes()
        for path in destinations:
            with self.subTest(path=path):
                before = path.read_bytes() if path.exists() else None
                if before is not None:
                    path.unlink()
                path.parent.mkdir(parents=True, exist_ok=True)
                path.symlink_to(outsider)
                result = self.machine('repair', '--dry-run')
                self.assertFalse(result['ok'], result)
                self.assertTrue(path.is_symlink())
                self.assertEqual(outsider.read_text(), 'Preserve outside data\n')
                self.assertEqual(journal, (self.home / 'pending.json').read_bytes())
                path.unlink()
                if before is not None:
                    path.write_bytes(before)
        self.assertEqual(self.launches(), 1)

    def test_unvalidated_setup_repair_rolls_back_without_rerun(self):
        self.interrupt_install('setup.exited')
        preview = self.machine('repair', '--dry-run')
        self.assertTrue(preview['ok'], preview)
        self.assertEqual(preview['data']['recovery']['mode'], 'rollback')
        result = self.machine('repair', '--approve-plan', preview['data']['plan_hash'])
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['transaction'], 'rolled_back')
        self.assertFalse((self.home / 'pending.json').exists())
        self.assertEqual(self.launches(), 1)
        self.assertFalse(self.lock.exists())

    @unittest.skipUnless(os.name == 'posix', 'POSIX terminal consent journey')
    def test_terminal_repair_decline_then_completion(self):
        self.interrupt_install()
        code, text = self.terminal('repair', answer=b'n\n')
        self.assertEqual(code, 4, text)
        self.assertTrue((self.home / 'pending.json').exists())
        code, text = self.terminal('repair', answer=b'y\n')
        self.assertEqual(code, 0, text)
        self.assertIn('Completed interrupted setup', text)
        self.assertFalse((self.home / 'pending.json').exists())
        self.assertEqual(self.launches(), 1)
