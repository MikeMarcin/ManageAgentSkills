"""Explicit repair, backup preservation and independent all-scope outcomes."""
import json
from pathlib import Path
import shutil
import subprocess
import sys

from tests.test_setup import SetupFixture
from tests.public_support import CONSUMER_CONTEXT, ENTRY
from tests.test_workflow_roles import WorkflowFixture, STATIC
from tests.support import Fixture


class Repair(SetupFixture):
    def existing_roles(self):
        originals = {'.claude/agents/rfc-integrator.md': '# custom role\n',
                     '.codex/agents/rfc-integrator.toml': 'name = "rfc-integrator"\nmodel = "custom"\n'}
        for relative, content in originals.items():
            path = self.project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
        return originals

    def test_repair_backs_up_replaces_and_is_idempotent_without_persistent_approval(self):
        originals = self.existing_roles()
        self.machine('integration', 'revoke', '--project', self.project)
        policy_before = (self.home / 'integration.json').read_bytes()
        preview = self.machine('ensure', '--project', self.project, '--repair', '--dry-run')
        self.assertEqual(self.launches(), 0)
        self.assertFalse((self.home / 'backups').exists())
        result = self.machine('ensure', '--project', self.project, '--yolo')
        self.assert_published(result)
        self.assertEqual(self.setup_rows(result)[0]['granted_by'], 'repair')
        self.assertEqual((self.home / 'integration.json').read_bytes(), policy_before)
        backups = result['data']['backups']
        self.assertEqual(len(backups), 2)
        for row in backups:
            relative = Path(row['original']).relative_to(self.project).as_posix()
            self.assertEqual(Path(row['path']).read_text(encoding='utf-8'), originals[relative])
            self.assertEqual(row['state'], 'saved')
            self.assertTrue((Path(row['directory']) / 'manifest.json').is_file())
        again = self.machine('ensure', '--project', self.project, '--repair')
        self.assertTrue(again['ok'], again)
        self.assertFalse(again['changed'])
        self.assertEqual(self.launches(), 1)

    def test_all_includes_personal_scope_and_continues_after_a_broken_project(self):
        broken = self.base / 'aaa broken project'
        broken.mkdir()
        self.git(broken, 'init', '-b', 'main')
        self.declare_consumer(broken, [])
        (broken / '.mask.json').write_text('invalid json', encoding='utf-8')
        shutil.copytree(CONSUMER_CONTEXT, self.personal / '.mask')
        self.declare_consumer(self.personal, ['implement-rfc'], user=True)
        result = self.machine('ensure', '--all', '--repair')
        self.assertEqual(result['error']['code'], 'repair.incomplete')
        rows = {row['root']: row for row in result['data']['repair_results']}
        self.assertFalse(rows[str(broken)]['ok'])
        self.assertTrue(rows[str(self.project)]['ok'], result)
        self.assertTrue(rows[str(self.personal)]['ok'], result)
        self.assertEqual(rows[str(self.personal)]['scope'], 'user')
        self.assertEqual(self.launches(), 2)
        text = self.human('ensure', '--all', '--repair').stderr
        self.assertIn('2 of 3 scopes are ready', text)
        self.assertIn(str(broken), text)
        self.assertNotIn('Run this setup?', text)

    def test_script_failure_preserves_original_files_without_replacing_them(self):
        originals = self.existing_roles()
        self.write_script(before='    raise RuntimeError("fixture failure")\n')
        self.commit('failing setup')
        result = self.machine('ensure', '--project', self.project, '--repair')
        self.assertEqual(result['error']['code'], 'setup.failed')
        for relative, content in originals.items():
            self.assertEqual((self.project / relative).read_text(encoding='utf-8'), content)
        self.assertFalse(self.lock.exists())

    def test_role_changed_during_setup_is_not_silently_replaced(self):
        self.existing_roles()
        self.write_script(before="    (args.repo_root / '.claude/agents/rfc-integrator.md').write_text('# concurrent edit\\n')\n")
        self.commit('concurrent edit fixture')
        result = self.machine('ensure', '--project', self.project, '--repair')
        self.assertEqual(result['error']['code'], 'setup.failed')
        self.assertIn('role destination changed', result['error']['message'])
        self.assertEqual((self.project / '.claude/agents/rfc-integrator.md').read_text(), '# concurrent edit\n')
        self.assertFalse(self.lock.exists())

    def test_repair_is_not_an_event_hook_and_check_never_executes(self):
        result = self.machine('ensure', '--all', '--repair', '--event', 'startup')
        self.assertEqual(result['error']['code'], 'invocation.invalid')
        self.machine('ensure', '--project', self.project, '--repair', '--check')
        self.assertEqual(self.launches(), 0)
        self.assertFalse((self.home / 'backups').exists())

    def test_repair_does_not_follow_role_symlinks(self):
        outside = self.base / 'keep.txt'
        outside.write_text('keep me', encoding='utf-8')
        path = self.project / '.codex/agents/rfc-integrator.toml'
        path.parent.mkdir(parents=True)
        path.symlink_to(outside)
        result = self.machine('ensure', '--project', self.project, '--repair')
        self.assertEqual(result['error']['code'], 'workflow.incomplete')
        self.assertTrue(path.is_symlink())
        self.assertEqual(outside.read_text(), 'keep me')

    def test_crash_rollback_restores_unmanaged_bytes_and_retains_backups(self):
        originals = self.existing_roles()
        script = '''
import os, sys
sys.path.insert(0, sys.argv[1])
import mask, mask_fs
def checkpoint(label):
    if label == 'native_role': os._exit(97)
mask_fs.checkpoint = checkpoint
raise SystemExit(__import__('tests.engine_cli', fromlist=['main']).main(sys.argv[2:]))
'''
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), 'ensure', '--project', str(self.project), '--repair', '--json'],
                             capture_output=True, text=True, env=self.environment(), timeout=60)
        self.assertEqual(run.returncode, 97, run.stdout + run.stderr)
        self.assertEqual(self.launches(), 1)
        journal = json.loads((self.home / 'pending.json').read_text())
        self.assertTrue(all(row['repair'] for row in journal['native_roles']))
        result = self.machine('recover', '--rollback')
        self.assertTrue(result['ok'], result)
        self.assertEqual(self.launches(), 1)
        for relative, content in originals.items():
            self.assertEqual((self.project / relative).read_text(encoding='utf-8'), content)
        manifests = list((self.home / 'backups').glob('*/manifest.json'))
        self.assertEqual(len(manifests), 1)
        for row in json.loads(manifests[0].read_text())['files']:
            self.assertTrue(Path(row['backup']).is_file())
        self.assertFalse(self.lock.exists())


class StaticRepair(WorkflowFixture):
    def test_static_role_repair_is_backed_up_without_package_execution(self):
        self.add_package('implement-rfc', STATIC)
        self.consumer(['implement-rfc'])
        path = self.project / '.codex/agents/rfc-integrator.toml'
        path.parent.mkdir(parents=True)
        original = 'name = "rfc-integrator"\nmodel = "custom"\n'
        path.write_text(original, encoding='utf-8')
        result = self.call('ensure', '--project', self.project, '--repair')
        self.assertTrue(result['ok'], result)
        self.assertNotEqual(path.read_text(), original)
        self.assertNotIn('setup', result['data'])
        self.assertEqual(len(result['data']['backups']), 1)
        self.assertEqual(Path(result['data']['backups'][0]['path']).read_text(), original)


class PinnedRepair(Fixture):
    def test_explicit_repair_works_without_persistent_approval_for_pinned_consumer(self):
        self.init()
        self.install('alpha')  # A fresh install on a tap catalog machine is already pinned.
        result = self.call('ensure', '--project', self.project, '--repair')
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['data']['approval'], 'not_approved')
        self.assertEqual(result['data']['readiness'], 'ready_pinned')
