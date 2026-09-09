"""Public regression baseline for RFC-MASK-0018 and RFC-MASK-0019 (MASK-0083).

MASK-0088 turned the RFC-MASK-0019-AC01 rows: declared native roles now
participate in readiness and static assets deploy through the typed engine.

Each ``expectedFailure`` test states the behavior the RFCs require and fails on
the pre-implementation program. A later card that fixes a defect removes its
decorator; an unexpected success is the signal to do so. Nothing here prepares
the behavior under test: no ``--json`` injection, no pre-registration for the
fresh states and no role repair for the linked consumer.
"""
import json
import unittest

from tests.public_support import PublicFixture, MISSING_ROLE, STATIC_PACKAGE


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
    """RFC-MASK-0018-AC02: commands without --json must not print the result envelope (fixed by MASK-0084)."""

    def test_inventory_without_json_is_not_an_envelope(self):
        self.linked_consumer_with_stale_roles()
        run = self.human('inventory', '--project', self.project)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertFalse(self.parses_as_result_envelope(run.stdout), run.stdout[:200])

    def test_version_without_json_is_not_an_envelope(self):
        run = self.human('--version')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertFalse(self.parses_as_result_envelope(run.stdout), run.stdout[:200])

    def test_capabilities_without_json_is_not_an_envelope(self):
        run = self.human('capabilities')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertFalse(self.parses_as_result_envelope(run.stdout), run.stdout[:200])


class TaskCommandBaseline(PublicFixture):
    """RFC-MASK-0018-AC01: one task command from an unregistered scope."""

    def test_install_from_fresh_project(self):
        run = self.human('install', 'alpha')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())

    def test_install_user_from_fresh_personal_scope(self):
        run = self.human('install', 'alpha', '--user', cwd=self.base)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertTrue((self.personal / '.agents/skills/alpha').is_symlink())
        self.assertFalse((self.project / '.mask.json').exists())


class WorkflowReadinessBaseline(PublicFixture):
    """RFC-MASK-0019-AC01: declared native roles participate in readiness (W01)."""

    def test_ensure_check_fails_with_missing_integrator_role(self):
        self.linked_consumer_with_stale_roles()
        check = self.raw('ensure', '--project', self.project, '--check', '--json')
        data = json.loads(check.stdout)
        self.assertNotEqual(check.returncode, 0, 'ensure --check reported complete readiness with rfc-integrator absent')
        self.assertIn(MISSING_ROLE, check.stdout)
        self.assertFalse(data['ok'])

    def test_ensure_does_not_report_ready_with_missing_integrator_role(self):
        self.linked_consumer_with_stale_roles()
        run = self.raw('ensure', '--project', self.project, '--json')
        again = json.loads(run.stdout)
        self.assertNotEqual(again['data']['readiness'], 'ready_legacy_unpinned')
        # MASK-0088: the static package supplies the exact role bytes; no generator or script exists to run.
        self.assertEqual((self.project / f'.codex/agents/{MISSING_ROLE}.toml').read_bytes(), (STATIC_PACKAGE / f'runtime/roles/codex/{MISSING_ROLE}.toml').read_bytes())
        self.assertEqual((self.project / '.codex/agents/rfc-worker.toml').read_text(encoding='utf-8'), '# older rfc-worker definition for codex\n', 'the edited role is preserved')
        self.assertFalse(again['ok'])
        self.assertEqual(again['error']['code'], 'workflow.incomplete')


if __name__ == '__main__':
    unittest.main()
