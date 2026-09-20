"""Selected requirement sets through the public CLI; no model or setup launches."""
import copy
import json
from tests.test_setup import SetupFixture, SUBJECT
from tests.support import TAP
import mask_core as core
import mask_workflow as workflow


class WorkflowProfileTests(SetupFixture):
    def bootstrap(self):
        self.git(self.source, 'remote', 'add', 'origin', str(self.upstream))
        self.assertTrue(self.machine('tap', 'add', TAP, self.upstream, '--checkout', self.source)['ok'])

    def setUp(self):
        super().setUp()
        self.descriptor_path = self.package / 'mask-workflow.json'
        value = json.loads(self.descriptor_path.read_text())
        value['profiles'] = {'direct': {'native_roles': []},
                             'worker': {'native_roles': ['codex/rfc-integrator']}}
        personal = copy.deepcopy(value)
        del personal['schema_version']
        personal['inputs'] = []
        personal['setup'][0]['inputs'] = []
        value['scopes'] = {'user': personal}
        self.descriptor_path.write_text(json.dumps(value))
        self.publish('requirement profiles')
        # Materialize links through the normal entrypoint; role setup remains pending.
        self.machine('upgrade', '--project', self.project)
        self.machine('ensure', '--project', self.project)

    def selected(self, profile='direct', *extra):
        return self.machine('ensure', '--project', self.project, '--check',
                            '--workflow-profile', 'implement-rfc=' + profile, *extra)

    def test_missing_roles_pass_only_selected_core_and_checks_never_write(self):
        before = (self.home / 'state.json').read_bytes()
        self.assertFalse(self.machine('ensure', '--project', self.project, '--check')['ok'])
        selected = self.selected()
        self.assertTrue(selected['ok'], selected)
        self.assertEqual(selected['data']['workflow_readiness'][0]['skills'][0]['selected_profile'], 'direct')
        self.assertEqual(self.roles_of(selected), {})
        self.assertEqual((self.home / 'state.json').read_bytes(), before)
        self.assertEqual(self.launches(), 0)
        self.assertFalse(self.selected('worker')['ok'])
        config = self.project / '.mask/skill-config/implement-rfc/project.json'
        config.unlink()
        self.assertFalse(self.selected()['ok'])

    def test_existing_roles_are_not_retired_or_modified(self):
        preview = self.machine('ensure', '--project', self.project, '--dry-run')
        setup = self.machine('ensure', '--project', self.project, '--expect-plan-hash', preview['data']['plan_hash'], '--allow-setup', SUBJECT)
        self.assertTrue(setup['ok'], setup)
        role = self.project / '.codex/agents/rfc-integrator.toml'
        role.write_text('owner changed these unused role bytes\n')
        state = (self.home / 'state.json').read_bytes()
        selected = self.selected()
        self.assertTrue(selected['ok'], selected)
        self.assertFalse(any(a['kind'].startswith('native_role.') for a in selected['actions']))
        self.assertEqual((self.home / 'state.json').read_bytes(), state)
        self.assertEqual(role.read_text(), 'owner changed these unused role bytes\n')
        self.assertFalse(self.machine('ensure', '--project', self.project, '--check')['ok'])
        self.assertEqual(self.launches(), 1)

    def test_personal_and_invalid_selection(self):
        self.machine('install', 'implement-rfc', '--user')
        selected = self.machine('ensure', '--user', '--check', '--workflow-profile', 'implement-rfc=direct')
        self.assertTrue(selected['ok'], selected)
        self.assertFalse((self.personal / '.mask/skill-config').exists())
        for profile in ('unknown', 'worker'):
            self.assertFalse(self.selected(profile)['ok'])
        for args in (('--project', self.project), ('--all', '--check'),
                     ('--project', self.project, '--check', '--repair')):
            result = self.machine('ensure', *args, '--workflow-profile', 'implement-rfc=direct')
            self.assertEqual(result['error']['code'], 'invocation.invalid', result)
        self.assertFalse(self.machine('ensure', '--project', self.project, '--check', '--workflow-profile', 'absent=direct')['ok'])
        self.assertEqual(self.launches(), 0)

    def test_inactive_profile_validation_and_legacy_descriptor(self):
        value = json.loads(self.descriptor_path.read_text())
        for selected in (['codex/missing'], ['codex/rfc-integrator'] * 2, 'all', [None]):
            bad = copy.deepcopy(value)
            bad['profiles']['unused'] = {'native_roles': selected}
            self.descriptor_path.write_text(json.dumps(bad))
            with self.assertRaises(core.MaskError):
                workflow.descriptor(self.package, 'implement-rfc')
        value.pop('profiles'); value.pop('scopes')
        self.descriptor_path.write_text(json.dumps(value))
        self.assertEqual(workflow.descriptor(self.package, 'implement-rfc')['profiles'], {})

    def test_selected_profile_preserves_link_and_approval_guards(self):
        caps = self.machine('capabilities')['data']['workflow']
        self.assertEqual(caps['requirement_profiles'], 'workflow_requirement_profiles_v1')
        link = self.project / '.agents/skills/implement-rfc'
        link.unlink()
        link.symlink_to(self.package, target_is_directory=True)
        result = self.selected()
        self.assertFalse(result['ok'], result)
        self.assertEqual(self.launches(), 0)

    def test_development_checks_are_observational_in_both_scopes(self):
        self.machine('install', 'implement-rfc', '--user')
        for scope in (('--project', self.project), ('--user',)):
            command = ('source', 'dev-link', TAP + '/implement-rfc', *scope, '--authoring-root', self.source)
            preview = self.machine(*command, '--dry-run')
            self.assertTrue(preview['ok'], preview)
            applied = self.machine(*command, '--expect-plan-hash', preview['data']['plan_hash'])
            self.assertTrue(applied['ok'], applied)
            state = (self.home / 'state.json').read_bytes()
            selected = self.machine('ensure', *scope, '--check', '--workflow-profile', 'implement-rfc=direct')
            self.assertTrue(selected['ok'], selected)
            self.assertEqual(selected['data']['readiness'], 'ready_dev_link')
            self.assertFalse(selected['changed'])
            self.assertEqual((self.home / 'state.json').read_bytes(), state)
            self.assertFalse(self.machine('ensure', *scope, '--check')['ok'])
            ordinary = self.machine('ensure', *scope)
            self.assertEqual(ordinary['error']['code'], 'dev_link.active')
            self.assertEqual((self.home / 'state.json').read_bytes(), state)
        self.assertEqual(self.launches(), 0)
        config = self.project / '.mask/skill-config/implement-rfc/project.json'
        saved = config.read_bytes()
        config.unlink()
        self.assertFalse(self.selected()['ok'])
        config.write_bytes(saved)
        link = self.project / '.agents/skills/implement-rfc'
        link.unlink()
        link.symlink_to(self.deployed(), target_is_directory=True)
        self.assertFalse(self.selected()['ok'])
