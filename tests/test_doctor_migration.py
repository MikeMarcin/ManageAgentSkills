"""Doctor detection and migration of live-checkout machines and consumers (RFC-MASK-0020 AC04, cases M01-M12; MASK-0102).

Legacy starting states come from the schema-true builder in ``tests.legacy_support``. Every invocation is a
subprocess with a private MASK_HOME and personal home. Observational cases compare a snapshot of the whole
disposable base (machine home, consumers, the clone and its upstream) before and after.
"""
import os

import mask_sources as sources
from tests.legacy_support import LegacyFixture, git, remove_entry, snapshot
from tests.support import TAP

REMEDIATION = ['mask', 'doctor', '--migrate', '--dry-run']


def codes(items):
    return [item['code'] for item in items]


class DoctorReport(LegacyFixture):
    """M01: doctor reports what a migration would convert and --check exits 7, without writing anything."""

    def report(self, *args):
        before = snapshot(self.roots.base, self.roots.base)
        data = self.machine('doctor', *args)
        self.assertEqual(snapshot(self.roots.base, self.roots.base), before, args)
        return data

    def test_v1_machine_reports_the_tap_the_clone_and_every_legacy_consumer(self):
        roots = self.legacy_machine(1)
        data = self.report()
        migration = data['data']['migration']
        self.assertEqual((migration['required'], migration['machine'], migration['migratable'], migration['blockers']), (True, 'legacy_v1', True, []))
        binding = sources.binding(roots.home, 'agentskills', str(roots.upstream), 'main', 'skills', str(roots.clone))
        self.assertEqual(migration['proposed_tap'], dict(alias='agentskills', **binding))
        head = git(roots.clone, 'rev-parse', 'HEAD')
        self.assertEqual(migration['clone'], dict(root=str(roots.clone), head=head, branch='main', dirty=False, unborn=False, published=True))
        rows = {row['root']: row for row in migration['consumers']}
        self.assertEqual(sorted(rows), sorted([str(roots.project), str(roots.personal)]))
        project, personal = rows[str(roots.project)], rows[str(roots.personal)]
        summary = ('scope', 'registered', 'declaration_version', 'mode', 'skills', 'migratable', 'blockers')
        self.assertEqual([project[key] for key in summary], ['project', True, 1, 'legacy', ['alpha'], True, []])
        self.assertEqual([personal[key] for key in summary], ['user', True, 1, 'legacy', ['beta'], True, []])
        self.assertEqual(sorted((link['relative'], link['agent'], link['state']) for link in project['links']),
                         [('.agents/skills/alpha', 'codex', 'ok'), ('.claude/skills/alpha', 'claude', 'ok')])
        issue = data['data']['issues'][0]
        self.assertEqual((data['data']['healthy'], issue['code'], issue['details']['remediation']), (False, 'migration.required', REMEDIATION))
        self.assertEqual(self.machine('doctor', '--check', code=7)['error']['code'], 'state.drift')
        # An explicit scope reports only that consumer; the unregistered v1 declaration is reported, not refused.
        self.assertEqual([row['root'] for row in self.report('--user')['data']['migration']['consumers']], [str(roots.personal)])
        straggler = self.report('--project', roots.straggler)['data']['migration']
        self.assertEqual([[row[key] for key in summary] for row in straggler['consumers']], [['project', False, 1, None, ['alpha'], True, []]])
        self.assertEqual(straggler['proposed_tap']['alias'], 'agentskills')

    def test_v2_machine_keeps_its_legacy_alias(self):
        roots = self.legacy_machine(2)
        migration = self.report()['data']['migration']
        self.assertEqual((migration['machine'], migration['migratable']), ('legacy_v2', True))
        self.assertEqual(migration['proposed_tap'], dict(alias='legacy', **roots.config['sources']['legacy']))
        self.assertEqual(len(migration['consumers']), 2)

    def test_link_drift_and_clone_conditions_are_typed_blockers(self):
        roots = self.legacy_machine(1)
        drifted = roots.project / '.claude/skills/alpha'
        remove_entry(drifted)
        os.symlink(str(roots.clone / 'skills' / 'beta'), drifted, target_is_directory=True)
        remove_entry(roots.project / '.agents/skills/alpha')
        (roots.clone / 'untracked.txt').write_text('preserve', encoding='utf-8')
        git(roots.clone, 'commit', '-q', '--allow-empty', '-m', 'local only')
        data = self.report()
        migration = data['data']['migration']
        self.assertEqual((migration['clone']['dirty'], migration['clone']['published'], migration['migratable']), (True, False, False))
        self.assertEqual(codes(migration['blockers']), ['source.dirty'])
        project = next(row for row in migration['consumers'] if row['root'] == str(roots.project))
        self.assertEqual(sorted((link['relative'], link['state']) for link in project['links']),
                         [('.agents/skills/alpha', 'missing'), ('.claude/skills/alpha', 'drift')])
        self.assertEqual((project['migratable'], codes(project['blockers'])), (False, ['target.drift']))
        self.assertIn('migration.unpublished_commit', codes(data['warnings']))
        git(roots.clone, 'checkout', '-q', '--detach')
        self.assertIn('source.identity_mismatch', codes(self.report()['data']['migration']['blockers']))

    def test_empty_registry_migrates_configuration_only_and_a_dirty_clone_is_a_warning(self):
        roots = self.legacy_machine(1, project_skills=None, user_skills=None, straggler_skills=None)
        (roots.clone / 'untracked.txt').write_text('preserve', encoding='utf-8')
        data = self.report()
        migration = data['data']['migration']
        self.assertEqual((migration['consumers'], migration['blockers'], migration['migratable'], migration['proposed_tap']['alias']), ([], [], True, 'agentskills'))
        self.assertIn('source.dirty', codes(data['warnings']))

    def test_clone_without_remote_and_missing_clone(self):
        roots = self.legacy_machine(1, remote=False)
        data = self.report()
        migration = data['data']['migration']
        self.assertEqual((migration['proposed_tap']['alias'], migration['proposed_tap']['repository'], migration['clone']['published']),
                         ('legacy', roots.clone.as_uri(), 'unknown'))
        self.assertIn('migration.local_only_source', codes(data['warnings']))
        os.rename(roots.clone, roots.base / 'moved clone')
        migration = self.report()['data']['migration']
        self.assertEqual((codes(migration['blockers']), migration['proposed_tap'], migration['clone']['head']), (['source.missing'], None, None))


class CurrentMachineReport(LegacyFixture):
    """A tap machine still holding an unregistered v1 declaration reports it for migration; --check exits 7."""

    def test_unregistered_v1_declarations_on_a_tap_machine(self):
        roots = self.legacy_machine(1, project_skills=None)
        for name in ('config.json', 'state.json'):
            (roots.home / name).unlink()
        self.machine('tap', 'add', TAP, roots.upstream)
        self.assertEqual(self.machine('doctor')['data']['migration'],
                         dict(required=False, machine='current', proposed_tap=None, clone=None, consumers=[], blockers=[], migratable=True))
        before = snapshot(roots.base, roots.base)
        data = self.machine('doctor', '--project', roots.straggler)['data']
        migration = data['migration']
        self.assertEqual((migration['required'], migration['machine'], migration['proposed_tap'], migration['clone']), (True, 'current', None, None))
        self.assertEqual([(row['root'], row['registered'], row['declaration_version'], row['skills'], row['migratable']) for row in migration['consumers']],
                         [(str(roots.straggler), False, 1, ['alpha'], True)])
        self.assertEqual([(issue['code'], issue['details']['remediation']) for issue in data['issues']], [('migration.required', REMEDIATION)])
        self.assertEqual(self.machine('doctor', '--project', roots.straggler, '--check', code=7)['error']['code'], 'state.drift')
        personal = self.machine('doctor', '--user')['data']['migration']['consumers']
        self.assertEqual([(row['scope'], row['registered'], row['skills']) for row in personal], [('user', False, ['beta'])])
        self.assertEqual(snapshot(roots.base, roots.base), before)
        other = roots.base / 'other'
        other.mkdir()
        self.assertEqual(self.machine('doctor', '--project', other, code=4)['error']['code'], 'project.not_registered')
