"""Human presentation for every registered command (MASK-0084, RFC-MASK-0018-AC02/AC03).

The subprocess cases use ``PublicFixture.human``, which never injects ``--json``;
the registry cases reject a command without an intentional renderer.
"""
import json
from pathlib import Path
import subprocess
import unittest

import mask
import mask_present as present
from tests.public_support import PublicFixture, PACK
from tests.support import TAP


class RendererRegistry(unittest.TestCase):
    def test_workflow_failures_group_files_by_consumer_without_flat_duplicate_list(self):
        output = mask.result('update')
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
        missing = sorted(set(mask.COMMANDS) - set(present.RENDERERS))
        self.assertEqual(missing, [])
        self.assertLessEqual({'help', 'version'}, set(present.RENDERERS))

    def test_every_command_and_argument_has_a_help_description(self):
        _, leaves = mask.make_parser()
        for command, parser in leaves.items():
            with self.subTest(command=command):
                self.assertTrue(parser.description)
                self.assertEqual([action.dest for action in parser._actions if not action.help], [])

    def test_selection_setter_help_points_to_install_and_remove(self):
        parser, leaves = mask.make_parser()
        for scope, flag in (('project', ''), ('user', ' --user')):
            for action in ('set', 'require', 'unrequire'):
                with self.subTest(command=f'{scope} {action}'):
                    text = ' '.join(mask.help_text(parser, leaves, [scope, action]).split())
                    for phrase in ('selection.command_unsupported', f'mask install ID{flag}', f'mask remove ID{flag}'):
                        self.assertIn(phrase, text)

    def test_renderers_tolerate_minimal_results_and_never_emit_json(self):
        for command in mask.COMMANDS:
            with self.subTest(command=command):
                text = present.render(mask.result(command))
                self.assertTrue(text.endswith('\n'))
                self.assertFalse(PublicFixture.parses_as_result_envelope(text))
                self.assertRaises(ValueError, json.loads, text)

    def test_legacy_fixture_renders_three_skill_rows_for_six_links(self):
        envelope = json.loads((PACK / 'fixtures/legacy-inventory.json').read_text(encoding='utf-8'))
        text = present.render(envelope)
        self.assertIn('3 skill row(s), 6 link(s)', text)
        lines = [line for line in text.splitlines() if line.startswith('  legacy/')]
        self.assertEqual(len(lines), 3, text)
        self.assertIn('CODEX', text)
        self.assertIn('CLAUDE', text)
        self.assertIn('legacy_unpinned', text)
        self.assertFalse(PublicFixture.parses_as_result_envelope(text))

    def test_control_characters_are_sanitized(self):
        self.assertEqual(present.clean('a\x1b[31mb\x07'), 'a?[31mb?')
        text = present.render_error(dict(mask.result('plan'), transaction='not_started', error=dict(code='x', message='bad\x1b[0m', details={}, remediation=[])))
        self.assertNotIn('\x1b', text)


class HumanTerminal(PublicFixture):
    def test_task_help_explains_scope_options_and_examples(self):
        for command, expected in (
            ('ensure', ('Examples:', '--allow-setup', 'SOURCE/ID:ACTION', 'Normal ensure', 'mask ensure --user', 'mask ensure --all --repair')),
            ('update', ('Examples:', 'ALL registered consumers', 'fetched once', 'update.incomplete', '--allow-ref-rebind', 'mask self update')),
            ('install', ('Examples:', 'Other selections are kept', 'every approved tap', 'never with --offline', 'mask install wizard --user')),
            ('doctor', ('Examples:', 'doctor --migrate', '--project PATH --alias NAME', 'mask doctor --migrate --dry-run')),
        ):
            with self.subTest(command=command):
                run = self.human(command, '--help')
                self.assertEqual(run.returncode, 0, run.stderr)
                for phrase in expected:
                    self.assertIn(phrase, ' '.join(run.stdout.split()))
                machine = self.machine(command, '--help')
                self.assertEqual(machine['data']['help'], run.stdout)
        root = self.human('--help').stdout
        self.assertIn('Start here:', root)
        self.assertIn('Bare update fetches each referenced tap once', root)
        self.assertIn('mask update --help', root)
        self.assertIn('mask doctor --migrate --dry-run', root)

    def test_v2_selection_setters_refuse_and_point_to_install_and_remove(self):
        # Owner decision Q4 (RFC-MASK-0021, MASK-0105): only install and remove edit a v2 declaration.
        shown = self.human('project', 'require', '--help')
        self.assertEqual(shown.returncode, 0, shown.stderr)
        for phrase in ('selection.command_unsupported', 'mask install ID', 'mask remove ID'):
            self.assertIn(phrase, ' '.join(shown.stdout.split()))
        self.assertTrue(self.machine('install', 'alpha')['ok'])
        self.assertTrue(self.machine('install', 'beta', '--user')['ok'])
        controls = [self.project / '.mask.json', self.project / '.mask.lock.json', self.home / 'user.json', self.home / 'state.json']
        before = [path.read_bytes() for path in controls]
        for args, scope in ((('project', 'require', 'beta'), ''), (('project', 'set', '--clear', '--project', self.project), ' --project PATH'),
                            (('user', 'unrequire', 'beta'), ' --user')):
            with self.subTest(args=args):
                run = self.human(*args)
                self.assertEqual((run.returncode, run.stdout), (4, ''), run.stderr)
                for phrase in ('code: selection.command_unsupported', f"'mask install ID{scope}'", f"'mask remove ID{scope}'"):
                    self.assertIn(phrase, run.stderr)
        self.assertEqual([path.read_bytes() for path in controls], before)

    def test_no_operand_shows_everyday_help_and_exits_zero(self):
        run = self.human()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('Everyday commands:', run.stdout)
        self.assertNotIn('"schema_version"', run.stdout)
        self.assertEqual(run.stderr, '')

    def test_version_is_a_version_line(self):
        run = self.human('--version')
        self.assertEqual((run.returncode, run.stdout), (0, f'mask {mask.VERSION}\n'))

    def test_group_and_leaf_help_are_text(self):
        for args, expected, code in ((('project',), 'subcommands: init', 2), (('project', '--help'), 'subcommands:', 0), (('inventory', '--help'), 'usage: mask inventory', 0)):
            with self.subTest(args=args):
                run = self.human(*args)
                self.assertEqual(run.returncode, code)
                self.assertIn(expected, run.stdout + run.stderr)
                self.assertFalse(self.parses_as_result_envelope(run.stdout))

    def test_inventory_shows_three_pinned_skill_rows_with_separate_agent_states(self):
        # Tap-first pinned rows (MASK-0102): one line per SOURCE/ID with a per-agent state column.
        self.assertTrue(self.machine('install', 'beta', '--project', self.project)['ok'])
        self.linked_consumer_with_stale_roles()
        run = self.human('inventory', '--project', self.project)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn('3 skill row(s), 6 link(s) shown of 6 total', run.stdout)
        lines = [line for line in run.stdout.splitlines() if line.startswith(f'  {TAP}/')]
        self.assertEqual(sorted(line.split()[0] for line in lines), [f'{TAP}/alpha', f'{TAP}/beta', f'{TAP}/implement-rfc'], run.stdout)
        self.assertTrue(all(line.split()[1:5] == [TAP, 'pinned', 'ok', 'ok'] for line in lines), run.stdout)
        self.assertIn('CLAUDE', run.stdout)
        self.assertIn('CODEX', run.stdout)
        self.assertIn('limitation:', run.stdout)
        self.assertNotIn('legacy', run.stdout)
        self.assertFalse(self.parses_as_result_envelope(run.stdout))
        page = self.human('inventory', '--project', self.project, '--limit', '2')
        self.assertIn('partial page', page.stdout)
        self.assertIn('--offset 2', page.stdout)
        self.assertIn('2 link(s) shown of 6 total', page.stdout)

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
        self.assertIn('would change (dry run)', preview.stdout)
        self.assertIn('link.create', preview.stdout)
        self.assertFalse((self.project / '.agents/skills/alpha').exists())
        applied = self.human('install', 'alpha')
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertIn('changed', applied.stdout.splitlines()[0])
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
