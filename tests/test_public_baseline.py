"""Public regression baseline for RFC-MASK-0018 and RFC-MASK-0019 (MASK-0083).

Each ``expectedFailure`` test states the behavior the RFCs require and fails on
the pre-implementation program. A later card that fixes a defect removes its
decorator; an unexpected success is the signal to do so. Nothing here prepares
the behavior under test: no ``--json`` injection, no pre-registration for the
fresh states and no role repair for the linked consumer.
"""
import json
import unittest

from tests.public_support import PublicFixture, MISSING_ROLE


class StartingStates(PublicFixture):
    """The three starting states exist and are not quietly prepared."""

    def test_fresh_project_and_personal_scope_are_unregistered(self):
        self.assertFalse((self.project / '.mask.json').exists())
        self.assertFalse((self.personal / '.mask.json').exists())
        self.assertEqual(self.machine('project', 'list')['data'].get('projects', []), [])
        self.assertFalse((self.home / 'user.json').exists())

    def test_linked_consumer_retains_missing_and_stale_roles(self):
        self.linked_consumer_with_stale_roles()
        self.assertTrue((self.project / '.agents/skills/implement-rfc').is_symlink())
        self.assertTrue((self.project / '.codex/agents/rfc-worker.toml').is_file())
        self.assertFalse((self.project / f'.codex/agents/{MISSING_ROLE}.toml').exists())
        self.assertFalse((self.project / f'.claude/agents/{MISSING_ROLE}.md').exists())

    def test_human_helper_does_not_inject_json(self):
        run = self.human('capabilities')
        self.assertEqual(run.returncode, 0, run.stderr)
        machine = self.machine('capabilities')
        self.assertIn('capabilities', {c['name'] for c in machine['data']['commands']})


class HumanOutputBaseline(PublicFixture):
    """RFC-MASK-0018-AC02: commands without --json must not print the result envelope."""

    @unittest.expectedFailure
    def test_inventory_without_json_is_not_an_envelope(self):
        self.linked_consumer_with_stale_roles()
        run = self.human('inventory', '--project', self.project)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertFalse(self.parses_as_result_envelope(run.stdout), run.stdout[:200])

    @unittest.expectedFailure
    def test_version_without_json_is_not_an_envelope(self):
        run = self.human('--version')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertFalse(self.parses_as_result_envelope(run.stdout), run.stdout[:200])

    @unittest.expectedFailure
    def test_capabilities_without_json_is_not_an_envelope(self):
        run = self.human('capabilities')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertFalse(self.parses_as_result_envelope(run.stdout), run.stdout[:200])


class TaskCommandBaseline(PublicFixture):
    """RFC-MASK-0018-AC01: one task command from an unregistered scope."""

    @unittest.expectedFailure
    def test_install_from_fresh_project(self):
        run = self.human('install', 'alpha')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())

    @unittest.expectedFailure
    def test_install_user_from_fresh_personal_scope(self):
        run = self.human('install', 'alpha', '--user', cwd=self.base)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue((self.personal / '.agents/skills/alpha').is_symlink())
        self.assertFalse((self.project / '.mask.json').exists())


class WorkflowReadinessBaseline(PublicFixture):
    """RFC-MASK-0019-AC01: declared native roles participate in readiness (W01)."""

    @unittest.expectedFailure
    def test_ensure_check_fails_with_missing_integrator_role(self):
        self.linked_consumer_with_stale_roles()
        check = self.raw('ensure', '--project', self.project, '--check', '--json')
        data = json.loads(check.stdout)
        self.assertNotEqual(check.returncode, 0, 'ensure --check reported complete readiness with rfc-integrator absent')
        self.assertIn(MISSING_ROLE, check.stdout)
        self.assertFalse(data['ok'])

    @unittest.expectedFailure
    def test_ensure_does_not_report_ready_with_missing_integrator_role(self):
        self.linked_consumer_with_stale_roles()
        again = self.machine('ensure', '--project', self.project)
        self.assertNotEqual(again['data']['readiness'], 'ready_legacy_unpinned')
        self.assertFalse((self.project / f'.codex/agents/{MISSING_ROLE}.toml').exists(), 'no generator ran')


if __name__ == '__main__':
    unittest.main()
