"""Scope-specific workflow contracts exercised through the disposable public CLI."""
import copy
import json
import shutil

import mask_workflow as workflow

from tests.test_setup import SetupFixture, SUBJECT


class WorkflowScopeTests(SetupFixture):
    def setUp(self):
        super().setUp()
        self.descriptor_path = self.package / 'mask-workflow.json'
        value = json.loads(self.descriptor_path.read_text())
        personal = copy.deepcopy(value)
        del personal['schema_version']
        personal['inputs'] = []
        personal['setup'][0]['inputs'] = []
        personal['setup'][0]['parameters'] = {'mode': 'personal'}
        value['scopes'] = {'user': personal}
        self.descriptor_path.write_text(json.dumps(value))
        self.write_script(before="    assert request['scope'] == 'user'\n    assert request['inputs'] == []\n    assert request['parameters'] == {'mode': 'personal'}\n    assert not (args.repo_root / '.git').exists()")
        self.commit('scope contracts')
        shutil.rmtree(self.project / '.mask')

    def install_personal(self):
        result = self.machine('install', 'implement-rfc', '--user')
        self.assertEqual(result['error']['code'], 'workflow.incomplete', result)
        return result

    def test_personal_setup_without_project_inputs_and_project_stays_incomplete(self):
        self.install_personal()
        for flags in (('--check',), ('--dry-run',), ('--yes',), ('--event', 'startup')):
            result = self.machine('ensure', '--user', *flags)
            self.assertFalse(result['ok'])
            self.assertEqual(self.launches(), 0)
        preview = self.machine('ensure', '--user', '--dry-run')
        result = self.machine('ensure', '--user', '--expect-plan-hash', preview['data']['plan_hash'], '--allow-setup', SUBJECT)
        self.assertTrue(result['ok'], result)
        self.assertEqual(self.launches(), 1)
        for relative in ('.codex/agents/rfc-integrator.toml', '.claude/agents/rfc-integrator.md', '.mask/generated/implement-rfc/native-roles.lock.json'):
            self.assertTrue((self.personal / relative).is_file(), relative)
        self.assertFalse((self.personal / '.mask/skill-config').exists())
        self.assertFalse((self.personal / '.git').exists())
        self.assertTrue(self.machine('ensure', '--user', '--check')['ok'])
        lock_path = self.personal / '.mask/generated/implement-rfc/native-roles.lock.json'
        original_lock = lock_path.read_text()
        copied_lock = json.loads(original_lock)
        copied_lock['contract_sha256'] = workflow.descriptor(self.package, 'implement-rfc', 'project')['digest']
        lock_path.write_text(json.dumps(copied_lock))
        copied = self.machine('ensure', '--user', '--check')
        self.assertFalse(copied['ok'])
        self.assertTrue(any(row['state'] == 'setup_required' for row in self.roles_of(copied).values()))
        self.assertEqual(self.launches(), 1)
        lock_path.write_text(original_lock)
        project = self.machine('ensure', '--project', self.project)
        self.assertEqual(project['error']['code'], 'workflow.incomplete')
        self.assertEqual(self.launches(), 1)
        role = self.personal / '.codex/agents/rfc-integrator.toml'
        role.write_text('name = "rfc-integrator"\nmodel = "changed"\n')
        self.assertFalse(self.machine('ensure', '--user')['ok'])
        self.assertIn('changed', role.read_text())
        self.assertEqual(self.launches(), 1)

    def test_project_lock_cannot_vouch_for_personal_roles(self):
        project = workflow.descriptor(self.package, 'implement-rfc', 'project')
        personal = workflow.descriptor(self.package, 'implement-rfc', 'user')
        self.assertNotEqual(project['digest'], personal['digest'])
        lock = dict(contract=project['digest'], role_inputs=workflow.role_inputs(personal), inputs={})
        self.assertFalse(workflow.lock_coherent(lock, personal, []))

    def test_scope_change_invalidates_exact_setup_consent(self):
        capabilities = self.machine('capabilities')['data']['workflow']
        self.assertEqual(capabilities['scope_contracts'], ['project', 'user'])
        self.assertTrue(capabilities['setup_request_scope'])
        self.install_personal()
        preview = self.machine('ensure', '--user', '--dry-run')
        value = json.loads(self.descriptor_path.read_text())
        value['scopes']['user']['setup'][0]['parameters']['mode'] = 'changed'
        self.descriptor_path.write_text(json.dumps(value))
        refused = self.machine('ensure', '--user', '--expect-plan-hash', preview['data']['plan_hash'], '--allow-setup', SUBJECT)
        self.assertEqual(refused['error']['code'], 'plan.stale')
        self.assertEqual(self.launches(), 0)

    def test_personal_collision_blocks_setup(self):
        self.install_personal()
        role = self.personal / '.codex/agents/rfc-integrator.toml'
        role.parent.mkdir(parents=True, exist_ok=True)
        role.write_text('unmanaged')
        result = self.machine('ensure', '--user')
        self.assertEqual(result['data']['setup']['actions'][0]['state'], 'blocked')
        self.assertEqual(role.read_text(), 'unmanaged')
        self.assertEqual(self.launches(), 0)

    def test_invalid_inactive_scope_refuses_project_and_ambiguous_keys_refuse(self):
        original = json.loads(self.descriptor_path.read_text())
        for change in ('missing-inputs', 'project-override', 'unknown-scope', 'nested-scopes'):
            value = copy.deepcopy(original)
            if change == 'missing-inputs':
                del value['scopes']['user']['inputs']
            elif change == 'nested-scopes':
                value['scopes']['user']['scopes'] = {}
            else:
                value['scopes']['project' if change == 'project-override' else 'personal'] = value['scopes']['user']
            self.descriptor_path.write_text(json.dumps(value))
            result = self.machine('ensure', '--project', self.project)
            self.assertEqual(result['error']['code'], 'workflow.invalid', result)
        self.assertEqual(self.launches(), 0)
