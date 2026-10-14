"""MASK-0115: actual public recovery, private fixtures only."""
import json
import os
import shutil
import sys
import unittest

import mask_core as c
from tests.public_support import PublicFixture


class DirectoryRebind(PublicFixture):
    def setUp(self):
        super().setUp()
        self.assertTrue(self.machine('install', 'alpha', '--no-update')['ok'])
        self.assertTrue(self.machine('integration', 'approve', '--project', self.project, '--linked-worktrees')['ok'])

    def controls(self):
        return {name: (self.home / name).read_bytes() for name in ('state.json', 'integration.json')}

    def renumber(self, *, user=False):
        path = self.home / 'state.json'
        state = json.loads(path.read_text())
        record = state['user'] if user else state['projects'][str(self.project)]
        record['root_identity']['device'] += 1
        path.write_text(c.text_json(state))
        if not user:
            path = self.home / 'integration.json'
            policy = json.loads(path.read_text())
            entry = policy['approvals'][str(self.project)]
            entry['identity']['device'] += 1
            entry['common_identity']['device'] += 1
            path.write_text(c.text_json(policy))

    def approved(self, *scope):
        preview = self.machine('register', *scope, '--rebind', '--dry-run')
        self.assertTrue(preview['ok'], preview)
        done = self.machine('register', *scope, '--rebind', '--approve-plan', preview['data']['plan_hash'])
        self.assertTrue(done['ok'], done)
        return done

    def test_reviewed_rebind_then_all_repair_and_unregister(self):
        self.renumber()
        before = self.controls()
        drift = self.machine('status', '--check')
        self.assertEqual(drift['error']['code'], 'state.drift')
        refused = self.raw('register', '--rebind', '--json')
        self.assertEqual(refused.returncode, 4)
        self.assertEqual(json.loads(refused.stdout)['error']['code'], 'confirmation.required')
        self.assertEqual(self.controls(), before)
        preview = self.machine('register', '--rebind', '--dry-run')
        self.assertEqual(self.controls(), before)
        done = self.machine('register', '--rebind', '--approve-plan', preview['data']['plan_hash'])
        self.assertTrue(done['ok'], done)
        state = json.loads((self.home / 'state.json').read_text())
        policy = json.loads((self.home / 'integration.json').read_text())
        self.assertEqual(state['projects'][str(self.project)]['root_identity'], c.identity(self.project))
        entry = policy['approvals'][str(self.project)]
        self.assertEqual(entry['identity'], c.identity(self.project))
        self.assertEqual(entry['common_identity'], c.identity(self.project / '.git'))
        self.assertTrue(entry['linked_worktrees'])
        self.assertTrue(self.machine('repair', '--all')['ok'])
        self.assertTrue(self.machine('status', '--check')['ok'])
        self.assertTrue(self.machine('integration', 'inspect', '--project', self.project)['data']['approved'])
        self.assertFalse((self.home / 'pending.json').exists())
        self.renumber()
        self.approved()
        unregistered = self.machine('unregister')
        self.assertTrue(unregistered['ok'], unregistered)
        self.assertFalse((self.project / '.agents/skills/alpha').exists())

    def test_personal_rebind_is_one_reviewed_step(self):
        self.assertTrue(self.machine('install', 'alpha', '--user', '--no-update')['ok'])
        self.renumber(user=True)
        self.approved('--user')
        self.assertTrue(self.machine('repair', '--all')['ok'])
        self.assertTrue(self.machine('status', '--user', '--check')['ok'])
        self.assertTrue(self.machine('unregister', '--user')['ok'])

    def test_real_replacement_and_common_directory_replacement_refuse(self):
        original = self.project.with_name('original retained')
        self.project.rename(original)
        shutil.copytree(original, self.project, symlinks=True)
        before = self.controls()
        refused = self.machine('register', '--rebind', '--dry-run')
        self.assertEqual(refused['error']['code'], 'project.identity_changed')
        self.assertEqual(self.controls(), before)
        shutil.rmtree(self.project)
        original.rename(self.project)
        oldgit = self.project / 'original-git'
        (self.project / '.git').rename(oldgit)
        shutil.copytree(oldgit, self.project / '.git')
        self.renumber()
        refused = self.machine('register', '--rebind', '--dry-run')
        self.assertEqual(refused['error']['code'], 'project.identity_changed')

    def test_collision_and_stale_approval_preserve_controls(self):
        self.renumber()
        preview = self.machine('register', '--rebind', '--dry-run')
        path = self.home / 'integration.json'
        policy = json.loads(path.read_text())
        policy['approvals'][str(self.project)]['inactive_branches'] = True
        path.write_text(c.text_json(policy))
        before = self.controls()
        stale = self.machine('register', '--rebind', '--approve-plan', preview['data']['plan_hash'])
        self.assertEqual(stale['error']['code'], 'plan.stale')
        self.assertEqual(self.controls(), before)

        leaf = self.project / '.agents/skills/alpha'
        leaf.unlink()
        leaf.mkdir()
        collision = self.machine('register', '--rebind', '--dry-run')
        self.assertEqual(collision['error']['code'], 'target.collision')
        self.assertEqual(self.controls(), before)

    def test_installed_integration_and_compatibility_authority_follow_rebind(self):
        common = self.project / '.git'
        installed = dict(root=str(self.project), identity=c.identity(self.project), common=str(common),
                         common_identity=c.identity(common), mode='directory', interpreter=str(sys.executable),
                         program=str(self.entrypoint.parent), home=str(self.home))
        installed['identity']['device'] += 1
        installed['common_identity']['device'] += 1
        path = self.home / 'integrations.json'
        path.write_text(c.text_json(dict(schema_version=1, installations={str(self.project): installed})))
        self.renumber()
        old = json.loads((self.home / 'state.json').read_text())['projects'][str(self.project)]['root_identity']
        override = dict(root=str(self.project), identity=old, coordinate='agentskills/alpha', reason='fixture', agents=['codex'])
        path = self.home / 'selection-policy.json'
        path.write_text(c.text_json(dict(schema_version=1, enabled_agents=['claude', 'codex'], overrides=[override])))
        self.approved()
        actual = json.loads((self.home / 'integrations.json').read_text())['installations'][str(self.project)]
        self.assertEqual(actual, dict(installed, identity=c.identity(self.project), common_identity=c.identity(common)))
        actual = json.loads(path.read_text())['overrides'][0]
        self.assertEqual(actual, dict(override, identity=c.identity(self.project)))

    def test_interrupted_controls_complete_or_rollback_without_new_authority(self):
        from tests.public_support import ENTRY
        wrapper = self.base / 'interrupt.py'
        wrapper.write_text('import sys, os\n' + f'sys.path.insert(0, {str(ENTRY.parent)!r})\n' +
                           'import mask, mask_fs\n' +
                           'mask_fs.checkpoint = lambda label: os._exit(79) if label == "rebind-control" else None\n' +
                           'sys.exit(mask.main())\n')
        for mode in ('rollback', 'complete'):
            with self.subTest(mode=mode):
                self.renumber()
                before = self.controls()
                preview = self.machine('register', '--rebind', '--dry-run')
                self.entrypoint = wrapper
                try:
                    crash = self.raw('register', '--rebind', '--approve-plan', preview['data']['plan_hash'], '--json')
                finally:
                    self.entrypoint = ENTRY
                self.assertEqual(crash.returncode, 79)
                self.assertTrue((self.home / 'pending.json').is_file())
                self.assertTrue(self.machine('recover', '--inspect')['ok'])
                recovered = self.machine('recover', '--' + mode)
                self.assertTrue(recovered['ok'], recovered)
                self.assertFalse((self.home / 'pending.json').exists())
                if mode == 'rollback':
                    self.assertEqual(self.controls(), before)
                    self.approved()
                self.assertTrue(self.machine('status', '--check')['ok'])

    @unittest.skipIf(os.name == 'nt', 'POSIX terminal required')
    def test_terminal_decline_and_confirmation(self):
        self.renumber()
        before = self.controls()
        code, text = self.terminal('register', '--rebind', answer=b'n\n')
        self.assertEqual(code, 4, text)
        self.assertEqual(self.controls(), before)
        code, text = self.terminal('register', '--rebind', answer=b'y\n')
        self.assertEqual(code, 0, text)
        self.assertEqual(text.count('[y/N]'), 1)
        self.assertTrue(self.machine('status', '--check')['ok'])
