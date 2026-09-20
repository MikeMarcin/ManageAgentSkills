"""Human presentation for every registered command (MASK-0084, RFC-MASK-0018-AC02/AC03).

The subprocess cases use ``EngineFixture.human``, which never injects ``--json``;
the registry cases reject a command without an intentional renderer.
"""
import json
from pathlib import Path
import subprocess
import unittest

import mask
import mask_cli
import mask_present as present
from tests.public_support import PublicFixture, EngineFixture, PACK
from tests.support import TAP


class RendererRegistry(unittest.TestCase):
    def test_workflow_failures_group_files_by_consumer_without_flat_duplicate_list(self):
        output = mask.result('upgrade')
        output['error'] = dict(code='workflow.incomplete', message='Incomplete',
                               details={'workflow': ['implement-rfc codex/rfc-integrator: setup_required'] * 2},
                               remediation=[{'message': 'Run ensure --project ROOT again'}])
        output['data']['workflow_readiness'] = [
            dict(root=root, scope='project', complete=False, skills=[dict(skill='implement-rfc', workflow='declared', complete=False,
                 roles=[dict(agent='codex', name='rfc-integrator', path='.codex/agents/rfc-integrator.toml',
                             state='setup_required', observed_sha256='existing', ownership='repository-owned', detail='Existing file is preserved')])])
            for root in ('/projects/one', '/projects/two')]
        text = present.render_error(output)
        self.assertIn('project: /projects/one', text)
        self.assertIn('project: /projects/two', text)
        self.assertEqual(text.count('.codex/agents/rfc-integrator.toml'), 2)
        self.assertNotIn('implement-rfc codex/rfc-integrator: setup_required', text)
        self.assertNotIn('--project ROOT', text)
        self.assertIn('no deployment changes were', text)

    def test_every_registered_command_has_an_intentional_renderer(self):
        missing = sorted(set(mask_cli.definitions(mask.COMMANDS)) - set(present.RENDERERS))
        self.assertEqual(missing, [])
        self.assertLessEqual({'help', 'version'}, set(present.RENDERERS))

    def test_every_command_and_argument_has_a_help_description(self):
        _, leaves = mask.make_parser()
        for command, parser in leaves.items():
            with self.subTest(command=command):
                self.assertTrue(parser.description)
                self.assertEqual([action.dest for action in parser._actions if not action.help], [])

    def test_renderers_tolerate_minimal_results_and_never_emit_json(self):
        for command in mask_cli.definitions(mask.COMMANDS):
            with self.subTest(command=command):
                text = present.render(mask.result(command))
                self.assertTrue(text.endswith('\n'))
                self.assertFalse(EngineFixture.parses_as_result_envelope(text))
                self.assertRaises(ValueError, json.loads, text)

    def test_control_characters_are_sanitized(self):
        self.assertEqual(present.clean('a\x1b[31mb\x07'), 'a?[31mb?')
        text = present.render_error(dict(mask.result('plan'), transaction='not_started', error=dict(code='x', message='bad\x1b[0m', details={}, remediation=[])))
        self.assertNotIn('\x1b', text)


class PublicHelp(PublicFixture):
    def test_task_help_explains_scopes_and_examples(self):
        for command, expected in (
            ('repair', ('Examples:', '--approve-plan', 'pinned state', 'mask repair --all')),
            ('upgrade', ('Examples:', 'this checkout', 'every registered checkout', '--no-update', 'mask upgrade --user')),
            ('install', ('Examples:', 'complete their setup', '--user', 'mask install implement-rfc')),
            ('status', ('Examples:', 'without changing files', '--check', 'mask status --all')),
        ):
            with self.subTest(command=command):
                run = self.human(command, '--help')
                self.assertEqual(run.returncode, 0, run.stderr)
                for phrase in expected:
                    self.assertIn(phrase, ' '.join(run.stdout.split()))
                self.assertEqual(self.machine(command, '--help')['data']['help'], run.stdout)
        root = self.human('--help').stdout
        self.assertIn('This checkout:', root)
        self.assertIn('Shared resources', root)
        self.assertIn('mask COMMAND --help', root)

    def test_no_operand_reports_status(self):
        self.assertTrue(self.machine('register')['ok'])
        run = self.human()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('Status: ready.', run.stdout)
        self.assertNotIn('"schema_version"', run.stdout)
        self.assertEqual(run.stderr, '')

    def test_version_is_a_version_line(self):
        run = self.human('--version')
        self.assertEqual((run.returncode, run.stdout), (0, f'mask {mask.VERSION}\n'))

    def test_group_and_leaf_help_are_text(self):
        for args, expected, code in ((('project',), 'subcommand', 2), (('project', '--help'), 'mask project set-agents', 0), (('list', '--help'), 'usage: mask list', 0)):
            with self.subTest(args=args):
                run = self.human(*args)
                self.assertEqual(run.returncode, code)
                self.assertIn(expected, run.stdout + run.stderr)
                self.assertFalse(self.parses_as_result_envelope(run.stdout))


class HumanTerminal(EngineFixture):
    def test_inventory_shows_three_pinned_skill_rows_with_separate_agent_states(self):
        # Tap-first pinned rows (MASK-0102): one line per SOURCE/ID with a per-agent state column.
        self.assertTrue(self.machine('install', 'beta', '--project', self.project)['ok'])
        self.linked_consumer_with_stale_roles()
        run = self.human('inventory', '--project', self.project)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('Inventory: 3 skills, 6 links', run.stdout)
        lines = [line for line in run.stdout.splitlines() if line.startswith(f'  {TAP}/')]
        self.assertEqual(sorted(line.split()[0] for line in lines), [f'{TAP}/alpha', f'{TAP}/beta', f'{TAP}/implement-rfc'], run.stdout)
        self.assertTrue(all(line.split()[1:4] == ['pinned', 'ok', 'ok'] for line in lines), run.stdout)
        self.assertIn('CLAUDE', run.stdout)
        self.assertIn('CODEX', run.stdout)
        self.assertIn('note:', run.stdout)
        self.assertNotIn('legacy', run.stdout)
        self.assertFalse(self.parses_as_result_envelope(run.stdout))
        page = self.human('inventory', '--project', self.project, '--limit', '2')
        self.assertIn('More rows follow this page', page.stdout)
        self.assertIn('--offset 2', page.stdout)
        self.assertIn('2 links shown of 6', page.stdout)

    def test_unregistered_inventory_is_a_readable_refusal(self):
        self.assertTrue(self.machine('project', 'init')['ok'])
        run = self.human('inventory')
        self.assertEqual(run.returncode, 4, run.stderr)
        self.assertEqual(run.stdout, '')
        self.assertIn('error: Inventory requires a registered consumer.', run.stderr)
        self.assertIn('next: Register the project first', run.stderr)
        machine = self.raw('inventory', '--json')
        self.assertEqual(machine.returncode, 4)
        self.assertEqual(json.loads(machine.stdout)['error']['code'], 'project.not_registered')
        self.assertEqual(machine.stderr, '')

    def test_every_day_commands_render_text(self):
        self.assertTrue(self.machine('project', 'init')['ok'])
        self.assertTrue(self.machine('project', 'register')['ok'])
        for args in (('capabilities',), ('skill', 'list'), ('project', 'list'), ('project', 'show'), ('config', 'show'), ('self', 'status'), ('plan',), ('doctor',), ('recover', '--inspect')):
            with self.subTest(args=args):
                run = self.human(*args)
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assertTrue(run.stdout.endswith('\n'))
                self.assertFalse(self.parses_as_result_envelope(run.stdout), run.stdout[:200])
                self.assertNotIn('{', run.stdout.splitlines()[0])

    def test_change_commands_render_text_and_keep_json_effects_identical(self):
        self.assertTrue(self.machine('project', 'init')['ok'])
        self.assertTrue(self.machine('project', 'register')['ok'])
        self.assertTrue(self.machine('source', 'fetch', TAP)['ok'])  # A dry run never fetches the tap.
        preview = self.human('install', 'alpha', '--dry-run')
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertIn('Would install 1 skill', preview.stdout)
        self.assertIn('dry run: nothing applied', preview.stdout)
        self.assertIn('2 skill links; save locked versions', preview.stdout)
        self.assertFalse((self.project / '.agents/skills/alpha').exists())
        applied = self.human('install', 'alpha')
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertIn('Installed 1 skill', applied.stdout.splitlines()[0])
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())
        again = self.machine('install', 'alpha')
        self.assertFalse(again['changed'])

    def test_redirected_output_and_operands_keep_the_selected_format(self):
        run = self.raw('skill', 'show', '--', '--json')
        self.assertEqual(run.stdout, '')
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('error:', run.stderr)
        machine = self.raw('skill', 'list', '--json')
        self.assertEqual(len(machine.stdout.strip().splitlines()), 1)
        self.assertTrue(json.loads(machine.stdout)['ok'])
        env = {'NO_COLOR': '1', 'COLUMNS': '40'}
        narrow = self.human('capabilities', env=env)
        self.assertEqual(narrow.returncode, 0)
        self.assertIn('inventory', narrow.stdout)
        self.assertNotIn('\x1b', narrow.stdout)


if __name__ == '__main__':
    unittest.main()
