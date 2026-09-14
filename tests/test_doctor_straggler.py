"""doctor --migrate on a tap machine (RFC-MASK-0021 AC04, case M11; MASK-0104).

A v3 machine created by ``tap add`` over the fixture upstream still holds a straggler: an unregistered v1 declaration
(project or personal), or a registered legacy (mode-less) record whose v1 declaration and clone links the live-checkout
program left behind. ``doctor --migrate --project PATH --alias NAME`` (or ``--user --alias NAME``) converts it with
install semantics in one ``doctor.migrate`` journal that has no ``migration`` field. Every invocation is a subprocess
with a private MASK_HOME and personal home.
"""
import json
import os
from pathlib import Path

import mask_core
import mask_resolve
from tests import test_doctor_migration as migration
from tests.legacy_support import git, snapshot, write_json
from tests.support import TAP

ALIAS = ('--alias', TAP)
# Every checkpoint a tap-machine doctor.migrate journal passes, in order; it has no machine configuration role.
LABELS = ('intent', 'link_unlinked', 'link', 'manifest', 'lock', 'state')
USAGE = 'doctor --migrate --project PATH --alias NAME'


class StragglerFixture(migration.MigrationFixture):
    """A legacy fixture whose configuration is replaced by ``tap add``; ``keep_state`` retains the legacy records."""

    def tap_machine(self, *, keep_state=False, **options):
        roots = self.legacy_machine(1, **options)
        (roots.home / 'config.json').unlink()
        if not keep_state:
            (roots.home / 'state.json').unlink()
        self.machine('tap', 'add', TAP, roots.upstream)
        return roots

    def everything(self):
        return snapshot(self.roots.base, self.roots.base)

    def head(self):
        return git(self.roots.upstream, 'rev-parse', 'main')

    def assert_converted(self, root, scope, skills):
        """A v2 declaration bound to the tap without a ref, a lock at the fetched commit, a pinned record and store links."""
        roots = self.roots
        entry = self.read(roots.home / 'config.json')['sources'][TAP]
        controls = (roots.home / 'user.json', roots.home / 'user.lock.json') if scope == 'user' else (root / '.mask.json', root / '.mask.lock.json')
        declaration = self.read(controls[0])
        self.assertEqual((declaration['schema_version'], declaration['sources'], [(item['source'], item['id']) for item in declaration['skills']]),
                         (2, {TAP: dict(repository=entry['repository'], packages='skills')}, [(TAP, skill) for skill in skills]))
        self.assertEqual([(row['source'], row['id'], row['commit']) for row in self.read(controls[1])['packages']], [(TAP, skill, self.head()) for skill in skills])
        state = self.read(roots.home / 'state.json')
        record = state['user'] if scope == 'user' else state['projects'][str(root)]
        self.assertEqual((record['root'], record['mode']), (str(root), 'pinned'))
        self.assertTrue({f'{path}/{skill}' for skill in skills for path in ('.claude/skills', '.agents/skills')} <= set(record['links']), record['links'])
        store = (roots.home / 'store' / 'v1').resolve()
        observed = set()
        for parent, directories, files in os.walk(root):
            directories[:] = [name for name in directories if name != '.git']
            observed.update(str((Path(parent) / name).relative_to(root).as_posix()) for name in directories + files if (Path(parent) / name).is_symlink())
        self.assertEqual(observed, set(record['links']))
        for relative, link in record['links'].items():
            leaf = root / relative
            self.assertEqual(os.readlink(leaf), link['link_text'], leaf)
            self.assertTrue(leaf.resolve().is_relative_to(store), leaf)
            self.assertTrue((leaf / 'SKILL.md').is_file(), leaf)
        self.assertFalse((roots.home / 'pending.json').exists())
        self.machine('doctor', *(('--user',) if scope == 'user' else ('--project', root)), '--check')


class UnregisteredStraggler(StragglerFixture):
    """M11: an unregistered v1 declaration is rewritten, resolved (fetching unless --offline), registered and linked."""

    def test_project_declaration_converts_with_install_semantics_and_a_rerun_is_a_no_op(self):
        roots = self.tap_machine(project_skills=None, user_skills=None)
        command = ('doctor', '--migrate', '--project', roots.straggler, *ALIAS)
        before = self.everything()
        # A cold cache: neither --offline nor --dry-run fetches, so both refuse before anything is written.
        for extra in (('--offline',), ('--dry-run',), ('--offline', '--dry-run')):
            with self.subTest(extra=extra):
                self.assertEqual(self.machine(*command, *extra, code=4)['error']['code'], 'lock.resolution_required')
                self.assertEqual(self.everything(), before)
        applied = self.machine(*command)
        self.assertEqual((applied['transaction'], applied['data']['network'], [row['source'] for row in applied['data']['acquisitions']]), ('committed', 'fetch', [TAP]))
        change = applied['data']['migration']['changes'][0]
        self.assertEqual((change['root'], change['scope'], change['registered'], change['declaration_before']), (str(roots.straggler), 'project', False, dict(schema_version=1, skills=['alpha'])))
        self.assert_converted(roots.straggler, 'project', ['alpha'])
        migrated = self.everything()
        rerun = self.machine(*command)
        self.assertEqual((rerun['would_change'], rerun['changed'], rerun['data']['migration']['required'], rerun['data']['migration']['consumers']), (False, False, False, []))
        self.assertEqual(self.everything(), migrated)

    def test_personal_declaration_without_a_record_becomes_a_registered_personal_scope(self):
        roots = self.tap_machine(project_skills=None, user_skills=None, straggler_skills=None)
        write_json(roots.home / 'user.json', dict(schema_version=1, skills=['beta']))
        self.machine('source', 'fetch', TAP)
        before = self.everything()
        preview = self.machine('doctor', '--migrate', '--user', *ALIAS, '--dry-run')
        self.assertEqual(self.everything(), before)
        change = preview['data']['migration']['changes'][0]
        self.assertEqual((preview['would_change'], preview['data']['network'], change['root'], change['scope'], change['registered']), (True, 'none', str(roots.personal), 'user', False))
        applied = self.machine('doctor', '--migrate', '--user', *ALIAS, '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertEqual((applied['transaction'], applied['data']['acquisitions'], applied['data']['plan_hash']), ('committed', [], preview['data']['plan_hash']))
        self.assert_converted(roots.personal, 'user', ['beta'])


class LegacyRecordOnTapMachine(StragglerFixture):
    """A registered mode-less record with a v1 declaration converts on a tap machine; recovery needs no checkout."""

    def test_crash_at_every_checkpoint_rolls_back_exactly_or_completes(self):
        roots = self.tap_machine(keep_state=True, user_skills=None, straggler_skills=None)
        self.machine('source', 'fetch', TAP)
        command = ('doctor', '--migrate', '--project', roots.project, *ALIAS)
        controls, links = self.controls(), self.links()
        self.assertTrue(all(text.endswith(os.path.join('AgentSkills', 'skills', 'alpha')) for text in links.values()), links)
        for label in LABELS:
            with self.subTest(label=label):
                journal = self.crash(label, *command)
                self.assertEqual((journal['operation'], journal['schema_version'], 'migration' in journal, journal['selected'], sorted(entry['role'] for entry in journal['files'])),
                                 ('doctor.migrate', 3, False, [str(roots.project)], ['project_declaration', 'project_lock']))
                self.machine('recover', '--rollback')
                self.assertEqual(self.controls(), controls)
                self.assertEqual(self.links(), links)
        self.crash('lock', *command)
        self.assertEqual(self.machine('recover', '--complete')['transaction'], 'committed')
        self.assert_converted(roots.project, 'project', ['alpha'])

    def test_a_tampered_after_selection_refuses_recovery_and_changes_nothing(self):
        roots = self.tap_machine(keep_state=True, user_skills=None, straggler_skills=None)
        self.machine('source', 'fetch', TAP)
        command = ('doctor', '--migrate', '--project', roots.project, *ALIAS)
        controls, links = self.controls(), self.links()
        journal = self.crash('intent', *command)
        path = roots.home / 'pending.json'
        original = path.read_bytes()
        # Narrow the after selection to one agent and keep every other record consistent with it, so only the recomputed mapping differs.
        files = {entry['role']: entry for entry in journal['files']}
        declaration = json.loads(files['project_declaration']['after'])
        declaration['default_agents'] = ['claude']
        declaration = mask_resolve.selection(declaration)
        lock = json.loads(files['project_lock']['after'])
        lock['selection_digest'] = mask_resolve.selection_digest(declaration)
        files['project_declaration']['after'], files['project_lock']['after'] = mask_core.text_json(declaration), mask_core.text_json(lock)
        journal['after_state']['projects'][str(roots.project)].update(last_manifest=declaration, last_manifest_digest=mask_resolve.selection_digest(declaration), last_lock=lock)
        journal['after_state_text'] = mask_core.text_json(journal['after_state'])
        path.write_bytes(mask_core.text_json(journal).encode('utf-8'))
        tampered = self.everything()
        for mode in ('--rollback', '--complete'):
            with self.subTest(mode=mode):
                error = self.machine('recover', mode, code=8)['error']
                self.assertEqual((error['code'], error['message']), ('recovery.conflict', 'Migrated selection differs from the observed v1 declaration.'))
                self.assertEqual(self.everything(), tampered)
        path.write_bytes(original)
        self.machine('recover', '--rollback')
        self.assertEqual((self.controls(), self.links()), (controls, links))
        self.assertEqual(self.machine(*command)['transaction'], 'committed')
        self.assert_converted(roots.project, 'project', ['alpha'])


class Refusals(StragglerFixture):
    def test_invocation_alias_declaration_and_pending_refusals_write_nothing(self):
        roots = self.tap_machine(keep_state=True, user_skills=None)
        self.machine('source', 'fetch', TAP)
        before = self.everything()
        cases = ((('--project', roots.straggler), 2, 'invocation.invalid'), ((*ALIAS,), 2, 'invocation.invalid'),
                 (('--all', *ALIAS), 2, 'invocation.invalid'), (('--project', roots.straggler, '--alias', 'unknown'), 4, 'source.unknown'))
        for args, exit_code, code in cases:
            for extra in ((), ('--dry-run',)):
                with self.subTest(args=args, extra=extra):
                    error = self.machine('doctor', '--migrate', *args, *extra, code=exit_code)['error']
                    self.assertEqual(error['code'], code)
                    if exit_code == 2:
                        self.assertIn(USAGE, error['message'])
                    self.assertEqual(self.everything(), before)
        # A registered legacy record that already declares a v2 selection is a report blocker, and it refuses.
        declaration = roots.project / '.mask.json'
        original = declaration.read_bytes()
        repository = self.read(roots.home / 'config.json')['sources'][TAP]['repository']
        write_json(declaration, dict(schema_version=2, sources={TAP: dict(repository=repository)}, skills=[dict(source=TAP, id='alpha')]))
        changed = self.everything()
        for extra in ((), ('--dry-run',)):
            error = self.machine('doctor', '--migrate', '--project', roots.project, *ALIAS, *extra, code=4)['error']
            self.assertEqual((error['code'], error['details']['blockers'][0]['code']), ('migration.declaration_unsupported', 'migration.declaration_unsupported'))
            self.assertEqual(self.everything(), changed)
        declaration.write_bytes(original)
        straggler = (roots.straggler / '.mask.json').read_bytes()
        self.crash('intent', 'doctor', '--migrate', '--project', roots.straggler, *ALIAS)
        pending = self.everything()
        self.assertEqual(self.machine('doctor', '--migrate', '--project', roots.project, *ALIAS, code=8)['error']['code'], 'recovery.required')
        self.assertEqual(self.everything(), pending)
        # Rolling back an unregistered conversion restores the v1 declaration and removes the created lock and registration.
        self.machine('recover', '--rollback')
        self.assertEqual(((roots.straggler / '.mask.json').read_bytes(), (roots.straggler / '.mask.lock.json').exists()), (straggler, False))
        self.assertNotIn(str(roots.straggler), self.read(roots.home / 'state.json')['projects'])
