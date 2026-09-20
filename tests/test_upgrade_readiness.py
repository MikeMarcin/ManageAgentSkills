"""Registered consumers reach workflow readiness through upgrade itself (MASK-0120)."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

from tests.public_support import CONSUMER_CONTEXT, ENTRY, EngineFixture
from tests.test_setup import SetupFixture, SUBJECT
from tests import test_cli_v2 as public_cli


class UpgradeReadiness(SetupFixture):
    raw = public_cli.CliV2.raw

    def setUp(self):
        # Retained private harness builds a registered, locked but unready consumer.
        # Every behavior under test below uses the shipped command surface.
        super().setUp()
        self.entrypoint = ENTRY

    def declare_consumer(self, *args, **kwargs):
        old = self.entrypoint
        self.entrypoint = EngineFixture.entrypoint
        try:
            return super().declare_consumer(*args, **kwargs)
        finally:
            self.entrypoint = old

    def approve_upgrade(self, *scope):
        preview = self.machine('upgrade', *scope, '--dry-run')
        self.assertTrue(preview['ok'], preview)
        return self.machine('upgrade', *scope, '--approve-plan', preview['data']['plan_hash'])

    def assert_ready(self, result):
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['data']['workflow'][str(self.project)], 'complete')
        self.assertEqual(self.setup_rows(result)[0]['state'], 'published')
        self.assert_published()

    def test_unchanged_versions_reconcile_setup_and_missing_links_without_approval(self):
        capabilities = self.machine('capabilities')
        self.assertEqual(capabilities['data']['workflow']['setup_entrypoints'], ['register', 'install', 'repair', 'upgrade'])
        self.machine('integration', 'revoke', '--project', self.project)
        policy = (self.home / 'integration.json').read_bytes()
        self.assert_ready(self.approve_upgrade('--project', self.project))
        self.assertEqual(self.launches(), 1)
        again = self.machine('upgrade', '--project', self.project, '--offline')
        self.assertTrue(again['ok'], again)
        self.assertFalse(again['changed'])
        self.assertNotIn('setup', again['data'])
        (self.project / '.agents/skills/implement-rfc').unlink()
        repaired = self.machine('upgrade', '--project', self.project, '--offline')
        self.assertTrue(repaired['ok'], repaired)
        self.assertTrue((self.project / '.agents/skills/implement-rfc').is_symlink())
        self.assertEqual(self.launches(), 1)
        self.assertEqual((self.home / 'integration.json').read_bytes(), policy)

    def test_candidate_setup_and_cold_preview_apply_with_one_hash(self):
        (self.package / 'scripts/helper.py').write_text((self.package / 'scripts/helper.py').read_text() + '\n# next version\n')
        self.publish('next setup')
        self.machine('tap', 'fetch', 'agentskills')
        before = {str(path): path.read_bytes() for path in self.home.rglob('*') if path.is_file()}
        preview = self.machine('upgrade', '--project', self.project, '--dry-run')
        self.assertTrue(preview['ok'], preview)
        self.assertEqual(preview['data']['network'], 'none')
        self.assertTrue(preview['would_change'])
        self.assertEqual(before, {str(path): path.read_bytes() for path in self.home.rglob('*') if path.is_file()})
        self.assertEqual(self.launches(), 0)

        self.assertEqual(self.links(), [])
        result = self.machine('upgrade', '--project', self.project, '--approve-plan', preview['data']['plan_hash'])
        self.assert_ready(result)
        self.assertEqual(result['data']['network'], 'none')
        self.assertTrue(result['data']['consumers'][0]['changes'])

    def test_explicit_all_completes_project_and_personal_scope(self):
        shutil.copytree(CONSUMER_CONTEXT, self.personal / '.mask')
        self.declare_consumer(self.personal, ['implement-rfc'], user=True)
        result = self.approve_upgrade('--all')
        self.assert_ready(result)
        self.assertEqual(result['data']['workflow'][str(self.personal)], 'complete')
        self.assertTrue((self.personal / '.codex/agents/rfc-integrator.toml').is_file())
        self.assertEqual(self.launches(), 2)
        self.assertFalse(self.machine('upgrade', '--offline')['changed'])
        self.assertEqual(self.launches(), 2)

    def test_scoped_personal_setup_does_not_touch_project(self):
        shutil.copytree(CONSUMER_CONTEXT, self.personal / '.mask')
        self.declare_consumer(self.personal, ['implement-rfc'], user=True)
        result = self.approve_upgrade('--user')
        self.assertTrue(result['ok'], result)
        self.assertEqual(set(result['data']['workflow']), {str(self.personal)})
        self.assertEqual(self.roles(), [])
        self.assertEqual(self.links(), [])
        self.assertEqual(self.launches(), 1)

    def test_noninteractive_upgrade_requires_the_combined_review(self):
        result = self.machine('upgrade')
        self.assertEqual(result['error']['code'], 'confirmation.required')
        self.assertEqual(self.launches(), 0)
        self.assertEqual(self.links(), [])
        run = self.human('upgrade', '--no-update', stdin=subprocess.DEVNULL)
        self.assertEqual(run.returncode, 4, run.stderr)
        self.assertNotIn('[y/N]', run.stderr)
        self.assert_nothing_published()

    def test_changed_consumer_input_invalidates_preview_before_writes(self):
        preview = self.machine('upgrade', '--project', self.project, '--dry-run')
        (self.project / '.mask/skill-config/implement-rfc/project.md').write_text('changed input\n')
        result = self.machine('upgrade', '--project', self.project, '--approve-plan', preview['data']['plan_hash'])
        self.assertEqual(result['error']['code'], 'plan.stale')
        self.assertEqual(self.links(), [])
        self.assertEqual(self.launches(), 0)

    def test_failed_setup_reports_committed_links_and_never_ready(self):
        self.write_script(before='    raise RuntimeError("fixture failure")\n')
        self.publish('failing setup')
        self.machine('tap', 'fetch', 'agentskills')
        result = self.approve_upgrade('--project', self.project)
        self.assertEqual(result['error']['code'], 'setup.failed')
        self.assertEqual(result['transaction'], 'committed')
        self.assertTrue(result['changed'])
        self.assertEqual(self.setup_rows(result)[0]['state'], 'failed')
        self.assertEqual(len(self.links()), 2)
        self.assert_nothing_published()

    def test_upgrade_setup_crash_recovery_does_not_rerun_script(self):
        preview = self.machine('upgrade', '--project', self.project, '--dry-run')
        script = '''
import sys, os
sys.path.insert(0, sys.argv[1])
import mask, mask_fs
mask_fs.checkpoint = lambda label: os._exit(99) if label == 'setup.exited' else None
raise SystemExit(mask.main(sys.argv[2:]))
'''
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), 'upgrade', '--project', str(self.project),
                              '--approve-plan', preview['data']['plan_hash'], '--no-update', '--json'],
                             capture_output=True, text=True, env=self.environment(), timeout=60)
        self.assertEqual(run.returncode, 99, run.stdout + run.stderr)
        self.assertEqual(json.loads((self.home / 'pending.json').read_text())['operation'], 'ensure')
        self.assertEqual(self.machine('recover', '--complete')['error']['code'], 'setup.unverified')
        self.assertTrue(self.machine('recover', '--rollback')['ok'])
        self.assertEqual(self.launches(), 1)
        self.assertEqual(len(self.links()), 2)
        self.assert_nothing_published()

    def test_role_publication_rollback_keeps_committed_link_effects_truthful(self):
        preview = self.machine('upgrade', '--project', self.project, '--dry-run')
        script = '''
import sys
sys.path.insert(0, sys.argv[1])
import mask, mask_core, mask_fs
def checkpoint(label):
    if label == 'native_role':
        mask_core.fail('filesystem.failed', 'injected publication failure', 5)
mask_fs.checkpoint = checkpoint
raise SystemExit(mask.main(sys.argv[2:]))
'''
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), 'upgrade', '--project', str(self.project),
                              '--approve-plan', preview['data']['plan_hash'], '--no-update', '--json'],
                             capture_output=True, text=True, env=self.environment(), timeout=60)
        self.assertEqual(run.returncode, 5, run.stdout + run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual(result['transaction'], 'committed')
        self.assertTrue(result['changed'])
        self.assertEqual(result['data']['setup']['transactions'][0]['transaction'], 'rolled_back')
        self.assertTrue(all(row['status'] == 'applied' for row in result['actions'] if row['kind'] == 'link.create'))
        self.assertEqual(len(self.links()), 2)
        self.assertEqual(self.launches(), 1)
        self.assert_nothing_published()

    def test_new_candidate_regenerates_managed_roles(self):
        self.assert_ready(self.approve_upgrade('--project', self.project))
        helper = self.package / 'scripts/helper.py'
        helper.write_text(helper.read_text().replace('fixture-model-do-not-run', 'updated-fixture-model'))
        self.publish('updated native role')
        self.machine('tap', 'fetch', 'agentskills')
        result = self.approve_upgrade('--project', self.project)
        self.assertTrue(result['ok'], result)
        self.assertEqual(self.launches(), 2)
        self.assertIn('updated-fixture-model', (self.project / '.codex/agents/rfc-integrator.toml').read_text())
        self.assertEqual(result['data']['workflow'][str(self.project)], 'complete')

    @unittest.skipUnless(os.name == 'posix', 'POSIX terminal journey')
    def test_terminal_yes_completes_and_decline_preserves_incomplete_status(self):
        code, text = self.terminal('upgrade', '--no-update', '--project', self.project, answer=b'n\n')
        self.assertEqual(code, 4, text)
        self.assertEqual(self.launches(), 0)
        code, text = self.terminal('upgrade', '--no-update', '--project', self.project, answer=b'y\n')
        self.assertEqual(code, 0, text)
        self.assertEqual(text.count('[y/N]'), 1)
        self.assert_published()
        self.assertEqual(self.launches(), 1)

    @unittest.skipUnless(os.name == 'posix', 'POSIX terminal journey')
    def test_input_changed_while_prompting_refuses_before_setup(self):
        def change():
            (self.project / '.mask/skill-config/implement-rfc/project.md').write_text('concurrent edit\n')
        code, text = self.terminal('upgrade', '--no-update', '--project', self.project, answer=b'y\n', before_answer=change)
        self.assertEqual(code, 4, text)
        self.assertIn('plan.stale', text)
        self.assertEqual(self.links(), [])
        self.assertEqual(self.launches(), 0)
