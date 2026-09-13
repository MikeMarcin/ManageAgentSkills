"""Task commands install/remove/list through the public CLI (RFC-MASK-0018, MASK-0086).

Every check runs the program as a subprocess against a fresh temporary source,
machine home and consumer; nothing registers, declares or applies on behalf of
the command under test (ACCEPTANCE.md C01-C05, plus the per-binding, edited-file
and other-scope cases named by the card).
"""
import json
import shutil

from tests.public_support import PublicFixture, CONSUMER_CONTEXT
from tests.support import TAP


def links(root):
    return sorted(path.relative_to(root).as_posix() for path in root.rglob('*') if path.is_symlink())


class FreshScopes(PublicFixture):
    """C01/C02/C04: one task command from an unregistered project and personal scope."""

    def test_install_from_fresh_project_declares_registers_and_links(self):
        run = self.human('install', 'alpha')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertFalse(self.parses_as_result_envelope(run.stdout))
        self.assertIn(f'added: {TAP}/alpha', run.stdout)
        self.assertEqual(links(self.project), ['.agents/skills/alpha', '.claude/skills/alpha'])
        # RFC-MASK-0020: a fresh declaration on a tap catalog machine is a v2 selection of the fixture tap.
        self.assertEqual(json.loads((self.project / '.mask.json').read_text(encoding='utf-8')),
                         dict(schema_version=2, sources={TAP: dict(repository=self.upstream.as_uri(), packages='skills')},
                              default_agents=['claude', 'codex'], skills=[dict(source=TAP, id='alpha')]))
        registered = self.machine('project', 'list')['data']['projects']
        self.assertEqual([entry['root'] for entry in registered], [str(self.project)])
        listing = self.human('list')
        self.assertEqual(listing.returncode, 0, listing.stderr)
        self.assertIn('alpha', listing.stdout)
        self.assertIn('2 of 2 managed links in place', listing.stdout)

    def test_dry_run_from_fresh_project_writes_nothing(self):
        # A dry run never fetches; the machine's tap cache is acquired first, as the live checkout used to exist. The scope stays fresh.
        self.assertTrue(self.machine('source', 'fetch', TAP)['ok'])
        run = self.machine('install', 'alpha', '--dry-run')
        self.assertTrue(run['would_change'])
        self.assertFalse(run['changed'])
        self.assertTrue(run['data']['declaration_created'])
        self.assertFalse((self.project / '.mask.json').exists())
        self.assertEqual(links(self.project), [])
        self.assertEqual(self.machine('project', 'list')['data']['projects'], [])

    def test_install_user_from_fresh_personal_scope_leaves_project_alone(self):
        run = self.human('install', 'alpha', '--user', cwd=self.base)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(links(self.personal), ['.agents/skills/alpha', '.claude/skills/alpha'])
        self.assertFalse((self.project / '.mask.json').exists())
        self.assertEqual(json.loads((self.home / 'user.json').read_text(encoding='utf-8'))['skills'], [dict(source=TAP, id='alpha')])
        listing = self.machine('list', '--user', cwd=self.base)['data']
        self.assertEqual([row['skill'] for row in listing['skills']], [TAP + '/alpha'])
        self.assertEqual(listing['links'], dict(expected=2, linked=2))

    def test_reinstall_and_second_scope_are_independent_no_ops(self):
        self.assertTrue(self.machine('install', 'alpha')['ok'])
        self.assertTrue(self.machine('install', 'beta', '--user', cwd=self.base)['ok'])
        state_before = (self.home / 'state.json').read_text(encoding='utf-8')
        again = self.machine('install', 'alpha')
        self.assertFalse(again['changed'])
        self.assertFalse(again['would_change'])
        self.assertEqual(again['data']['already'], [TAP + '/alpha'])
        self.assertEqual((self.home / 'state.json').read_text(encoding='utf-8'), state_before)
        self.assertEqual(links(self.personal), ['.agents/skills/beta', '.claude/skills/beta'])
        removed = self.machine('remove', 'alpha')
        self.assertTrue(removed['changed'])
        self.assertEqual(links(self.project), [])
        self.assertEqual(links(self.personal), ['.agents/skills/beta', '.claude/skills/beta'])
        self.assertEqual(json.loads((self.home / 'user.json').read_text(encoding='utf-8'))['skills'], [dict(source=TAP, id='beta')])

    def test_remove_without_registration_and_unknown_skill_are_precise(self):
        run = self.human('remove', 'alpha')
        self.assertEqual(run.returncode, 3, run.stdout)
        self.assertIn('manifest.missing', run.stderr)
        self.assertTrue(self.machine('install', 'alpha')['ok'])
        unknown = self.machine('install', 'nothere')
        self.assertFalse(unknown['ok'])
        self.assertEqual(unknown['error']['code'], 'skill.unknown')
        self.assertEqual(links(self.project), ['.agents/skills/alpha', '.claude/skills/alpha'])

    def test_json_is_one_document_and_human_errors_go_to_stderr(self):
        run = self.raw('install', 'alpha', '--json')
        self.assertEqual(run.stderr, '')
        self.assertEqual(json.loads(run.stdout)['command'], 'install')
        run = self.human('install', 'alpha', '--agent', 'nope')
        self.assertNotEqual(run.returncode, 0)
        self.assertEqual(run.stdout, '')
        self.assertFalse(self.parses_as_result_envelope(run.stderr))


class PinnedScopes(PublicFixture):
    """C03/C05: v2 pins and per-binding targets are retained; bare names never pick a first match."""

    def pinned_project(self):
        # On a tap catalog machine a fresh install is already pinned; no migration is needed to reach v2 pins.
        self.assertTrue(self.machine('install', 'alpha', 'beta')['ok'])
        self.assertTrue(self.machine('project', 'set-agents', TAP + '/alpha', 'codex', '--apply')['ok'])
        return json.loads((self.project / '.mask.json').read_text(encoding='utf-8')), json.loads((self.project / '.mask.lock.json').read_text(encoding='utf-8'))

    def rows(self):
        return {row['id']: row for row in json.loads((self.project / '.mask.lock.json').read_text(encoding='utf-8'))['packages']}

    def test_v2_install_and_remove_retain_unrelated_pins_and_overrides(self):
        declaration, lock = self.pinned_project()
        before = {row['id']: row for row in lock['packages']}
        shutil.copytree(CONSUMER_CONTEXT, self.project / '.mask')  # implement-rfc declares consumer inputs; since MASK-0090 install cannot succeed without them.
        run = self.human('install', 'implement-rfc', '--agent', 'claude')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertNotIn('selection.command_unsupported', run.stderr)
        self.assertEqual(links(self.project), ['.agents/skills/alpha', '.agents/skills/beta', '.claude/skills/beta', '.claude/skills/implement-rfc'])
        after = self.rows()
        self.assertEqual({key: after[key] for key in before}, before)
        bindings = {row['id']: row for row in json.loads((self.project / '.mask.json').read_text(encoding='utf-8'))['skills']}
        self.assertEqual(bindings['alpha'].get('agents'), ['codex'])
        self.assertEqual(bindings['implement-rfc'].get('agents'), ['claude'])
        listing = self.machine('list')['data']
        states = {row['skill']: row['states'] for row in listing['skills']}
        self.assertEqual(states[TAP + '/alpha'], dict(claude='excluded', codex='linked'))
        self.assertEqual(states[TAP + '/implement-rfc'], dict(claude='linked', codex='excluded'))
        again = self.machine('install', 'implement-rfc')
        self.assertFalse(again['would_change'])
        self.assertEqual(bindings['implement-rfc'], {row['id']: row for row in json.loads((self.project / '.mask.json').read_text(encoding='utf-8'))['skills']}['implement-rfc'])
        removed = self.machine('remove', 'implement-rfc')
        self.assertTrue(removed['changed'])
        self.assertEqual(links(self.project), ['.agents/skills/alpha', '.agents/skills/beta', '.claude/skills/beta'])
        self.assertEqual(self.rows(), before)
        self.assertEqual(json.loads((self.project / '.mask.json').read_text(encoding='utf-8')), declaration)

    def test_removal_preserves_edited_files_and_refuses(self):
        self.pinned_project()
        leaf = self.project / '.claude/skills/beta'
        leaf.unlink()
        leaf.mkdir()
        (leaf / 'mine.md').write_text('edited\n', encoding='utf-8')
        run = self.human('remove', 'beta')
        self.assertEqual(run.returncode, 4, run.stdout)
        self.assertIn('target.collision', run.stderr)
        self.assertIn('no deployment changes were applied', run.stderr)
        self.assertEqual((leaf / 'mine.md').read_text(encoding='utf-8'), 'edited\n')
        self.assertIn('beta', [row['id'] for row in self.rows().values()])
        self.assertTrue((self.project / '.agents/skills/beta').is_symlink())

    def test_bare_name_in_two_sources_is_ambiguous_and_qualified_name_resolves(self):
        self.pinned_project()
        other = self.base / 'OtherSkills'
        (other / 'skills/alpha').mkdir(parents=True)
        (other / 'skills/alpha/SKILL.md').write_text('---\nname: alpha\ndescription: Other alpha\n---\n\nOther.\n', encoding='utf-8')
        self.git(other, 'init', '-b', 'main')
        self.git(other, 'config', 'user.name', 'Fixture')
        self.git(other, 'config', 'user.email', 'fixture@example.invalid')
        self.git(other, 'add', 'skills')
        self.git(other, 'commit', '-m', 'other alpha')
        self.assertTrue(self.machine('tap', 'add', 'other', str(other))['ok'])
        project_links = links(self.project)
        offline = self.machine('install', 'other/alpha', '--user', '--offline', cwd=self.base)
        self.assertEqual(offline['error']['code'], 'lock.resolution_required')
        self.assertFalse((self.home / 'user.json').exists())
        ambiguous = self.machine('install', 'alpha', '--user', cwd=self.base)
        self.assertEqual(ambiguous['error']['code'], 'skill.ambiguous')
        self.assertEqual(ambiguous['error']['details']['choices'], [TAP + '/alpha', 'other/alpha'])
        # Acquisitions are the taps fetched by this resolution: the fixture tap's cache is already warm from the pinned install.
        self.assertEqual(sorted(item['source'] for item in ambiguous['data']['acquisitions']), ['other'])
        self.assertFalse((self.home / 'user.json').exists())
        self.assertEqual(links(self.personal), [])
        qualified = self.machine('install', 'other/alpha', '--user', cwd=self.base)
        self.assertTrue(qualified['ok'], qualified)
        self.assertEqual(qualified['data']['network'], 'none')
        self.assertEqual(links(self.personal), ['.agents/skills/alpha', '.claude/skills/alpha'])
        self.assertEqual([row['source'] for row in json.loads((self.home / 'user.lock.json').read_text(encoding='utf-8'))['packages']], ['other'])
        self.assertEqual(self.rows().keys(), {'alpha', 'beta'})
        self.assertEqual(links(self.project), project_links)
