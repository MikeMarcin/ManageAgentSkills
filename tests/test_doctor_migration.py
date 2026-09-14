"""Doctor detection and migration of live-checkout machines and consumers (RFC-MASK-0020 AC04, cases M01-M12; MASK-0102).

Legacy starting states come from the schema-true builder in ``tests.legacy_support``. Every invocation is a
subprocess with a private MASK_HOME and personal home. Observational cases compare a snapshot of the whole
disposable base (machine home, consumers, the clone and its upstream) before and after.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

import mask_sources as sources
from tests.legacy_support import ENTRY, LegacyFixture, build_legacy_machine, git, remove_entry, snapshot, write_json
from tests.support import TAP
from tests.test_link_producers import CRASH

# The live-checkout program (RFC_BASE_SHA) whose recovery must refuse a doctor.migrate journal (M12).
PREVIOUS = 'b92372f'
# Every checkpoint a doctor.migrate journal passes, in order (M05).
LABELS = ('intent', 'link_unlinked', 'link', 'manifest', 'lock', 'config', 'state')

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


class MigrationFixture(LegacyFixture):
    """Observation helpers for doctor --migrate cases; every effect is compared through files, links and Git."""

    def read(self, path):
        return json.loads(Path(path).read_text(encoding='utf-8'))

    def rebuild(self, name, version=1, **options):
        """A fresh legacy machine under its own sub-base, for cases that need several starting states."""
        self.roots = build_legacy_machine(Path(self.temp.name).resolve() / name, version, **options)
        return self.roots

    def crash(self, label, *args):
        run = subprocess.run([sys.executable, '-B', '-c', CRASH, str(ENTRY.parent), label, *map(str, args), '--json'], capture_output=True,
                             encoding='utf-8', cwd=str(self.roots.base), env=self.environment(), timeout=120)
        self.assertEqual(run.returncode, 99, run.stdout + run.stderr)
        return self.read(self.roots.home / 'pending.json')

    def controls(self):
        """Exact bytes (or absence) of every control a migration may write."""
        roots = self.roots
        paths = (roots.home / 'config.json', roots.home / 'state.json', roots.home / 'user.json', roots.home / 'user.lock.json',
                 roots.project / '.mask.json', roots.project / '.mask.lock.json', roots.home / 'pending.json')
        return {str(path): path.read_bytes() if path.exists() else None for path in paths}

    def links(self):
        """Exact link text at every leaf the legacy records own."""
        result = {}
        for record in [*self.roots.state['projects'].values(), self.roots.state.get('user')]:
            for relative in (record or {}).get('links', {}):
                leaf = Path(record['root']) / relative
                result[str(leaf)] = os.readlink(leaf) if leaf.is_symlink() else None
        return result

    def clone_facts(self):
        roots = self.roots
        staged = subprocess.run(['git', '-C', str(roots.clone), 'ls-files', '--stage', '-z'], capture_output=True, check=True).stdout
        return dict(head=git(roots.clone, 'rev-parse', 'HEAD'), index=hashlib.sha256(staged).hexdigest(),
                    status=git(roots.clone, 'status', '--porcelain'), worktree=snapshot(roots.base, roots.clone),
                    upstream=snapshot(roots.base, roots.upstream) if roots.upstream.exists() else None)

    def assert_migrated(self, alias, head, *, fresh_cache=True):
        """M03: v3 config with the clone as tap, v2 declarations, locks at HEAD, frozen cache ref, pinned records and store links."""
        roots = self.roots
        config = self.read(roots.home / 'config.json')
        entry = config['sources'][alias]
        self.assertEqual(sorted(config), ['default_targets', 'git_timeout_seconds', 'schema_version', 'sources'])
        self.assertEqual((config['schema_version'], entry['authoring'], entry['ref'], entry['packages']), (3, str(roots.clone), 'main', 'skills'))
        state = self.read(roots.home / 'state.json')
        records = dict(state['projects'], **{state['user']['root']: state['user']})
        legacy_roots = (str(roots.project), str(roots.personal))
        self.assertEqual({root: records[root]['mode'] for root in legacy_roots}, dict.fromkeys(legacy_roots, 'pinned'))
        binding = dict(repository=entry['repository'], packages='skills', ref='refs/heads/main')
        for declaration, lock, skill in ((roots.project / '.mask.json', roots.project / '.mask.lock.json', 'alpha'),
                                         (roots.home / 'user.json', roots.home / 'user.lock.json', 'beta')):
            value = self.read(declaration)
            self.assertEqual((value['schema_version'], value['sources'], [(item['source'], item['id']) for item in value['skills']]), (2, {alias: binding}, [(alias, skill)]))
            rows = self.read(lock)['packages']
            self.assertEqual([(row['source'], row['id'], row['commit'], row['selector'], row['repository']) for row in rows],
                             [(alias, skill, head, dict(ref='refs/heads/main'), entry['repository'])])
        cache = Path(entry['cache'])
        self.assertEqual(git(cache, 'rev-parse', 'refs/mask/frozen/' + head), head)
        self.assertEqual(git(cache, 'for-each-ref', '--format=%(refname)', 'refs/mask/acquiring'), '')
        if fresh_cache:
            self.assertEqual(git(cache, 'for-each-ref', '--format=%(refname)', 'refs/mask/selected'), '')
            self.assertFalse((cache / 'mask-refs.json').exists())
        store = (roots.home / 'store' / 'v1').resolve()
        leaves = set()
        for root in legacy_roots:
            for relative, link in records[root]['links'].items():
                leaf = Path(root) / relative
                leaves.add(str(leaf))
                self.assertEqual(os.readlink(leaf), link['link_text'], leaf)
                self.assertTrue(leaf.resolve().is_relative_to(store), leaf)
                self.assertTrue((leaf / 'SKILL.md').is_file(), leaf)
        self.assertEqual(leaves, set(self.links()))
        self.assertFalse((roots.home / 'pending.json').exists())
        self.machine('doctor', '--check')
        return config


class MachineMigration(MigrationFixture):
    """M02-M10: doctor --migrate converts a live-checkout machine and every legacy consumer in one journal."""

    def test_dry_run_discloses_the_plan_writes_nothing_and_its_hash_binds_the_apply(self):
        roots = self.legacy_machine(1)
        head = git(roots.clone, 'rev-parse', 'HEAD')
        before = snapshot(roots.base, roots.base)
        preview = self.machine('doctor', '--migrate', '--dry-run')
        self.assertEqual(snapshot(roots.base, roots.base), before)
        migration = preview['data']['migration']
        binding = sources.binding(roots.home, 'agentskills', str(roots.upstream), 'main', 'skills', str(roots.clone))
        self.assertEqual((preview['would_change'], preview['changed'], preview['data']['network'], migration['config_before']), (True, False, 'none', roots.config))
        self.assertEqual(migration['config_after'], dict(schema_version=3, default_targets=['claude', 'codex'], git_timeout_seconds=30, sources=dict(agentskills=binding)))
        self.assertEqual(migration['proposed_tap'], dict(alias='agentskills', **binding))
        self.assertEqual(migration['acquisition'], dict(alias='agentskills', cache=binding['cache'], commit=head, source=str(roots.clone), transport='file'))
        self.assertEqual({action['kind'] for action in preview['actions']}, {'config.migrate', 'declaration.write', 'lock.write', 'link.create', 'state.record'})
        changes = {row['root']: row for row in migration['changes']}
        self.assertEqual(sorted(changes), sorted([str(roots.project), str(roots.personal)]))
        project = changes[str(roots.project)]
        self.assertEqual((project['declaration_before'], [row['commit'] for row in project['lock_after']['packages']]), (dict(schema_version=1, skills=['alpha']), [head]))
        recorded = roots.state['projects'][str(roots.project)]['links']
        self.assertEqual(sorted((link['relative'], link['before']) for link in project['links']), sorted((relative, link['link_text']) for relative, link in recorded.items()))
        self.assertTrue(all(str(roots.home / 'store' / 'v1') in link['after'] for link in project['links']), project['links'])
        guard = preview['data']['plan_hash']
        # A stale hash, a changed consumer control or a moved clone HEAD refuses plan.stale and writes nothing.
        self.assertEqual(self.machine('doctor', '--migrate', '--expect-plan-hash', 'sha256:' + '0' * 64, code=4)['error']['code'], 'plan.stale')
        declaration = roots.project / '.mask.json'
        original = declaration.read_bytes()
        declaration.write_bytes(original.replace(b'"alpha"', b'"alpha",\n    "beta"'))
        self.assertEqual(self.machine('doctor', '--migrate', '--expect-plan-hash', guard, code=4)['error']['code'], 'plan.stale')
        declaration.write_bytes(original)
        git(roots.clone, 'commit', '-q', '--allow-empty', '-m', 'moved')
        self.assertEqual(self.machine('doctor', '--migrate', '--expect-plan-hash', guard, code=4)['error']['code'], 'plan.stale')
        git(roots.clone, 'update-ref', 'refs/heads/main', head)
        self.assertEqual(snapshot(roots.base, roots.base), before)
        applied = self.machine('doctor', '--migrate', '--expect-plan-hash', guard)
        self.assertEqual((applied['transaction'], applied['data']['plan_hash']), ('committed', guard))
        self.assert_migrated('agentskills', head)

    def test_v1_machine_migrates_configuration_consumers_cache_store_and_links(self):
        roots = self.legacy_machine(1)
        facts = self.clone_facts()
        straggler = (roots.straggler / '.mask.json').read_bytes()
        data = self.machine('doctor', '--migrate')
        self.assertEqual((data['changed'], data['transaction'], data['data']['network']), (True, 'committed', 'none'))
        self.assertEqual({action['status'] for action in data['actions']}, {'applied'})
        self.assert_migrated('agentskills', facts['head'])
        # The clone (HEAD, index, status, worktree) and its upstream are only read; the unregistered straggler stays v1.
        self.assertEqual(self.clone_facts(), facts)
        self.assertEqual((roots.straggler / '.mask.json').read_bytes(), straggler)
        self.assertNotIn(str(roots.straggler), self.read(roots.home / 'state.json')['projects'])

    def test_v2_machine_keeps_its_legacy_alias_and_every_other_tap(self):
        roots = self.legacy_machine(2)
        self.machine('doctor', '--migrate')
        config = self.assert_migrated('legacy', git(roots.clone, 'rev-parse', 'HEAD'))
        self.assertEqual(config['sources'], dict(legacy=roots.config['sources']['legacy'], extra=roots.config['sources']['extra']))

    def test_crash_at_every_checkpoint_rolls_back_exactly_or_completes(self):
        roots = self.legacy_machine(1)
        head = git(roots.clone, 'rev-parse', 'HEAD')
        controls, links = self.controls(), self.links()
        for label in LABELS:
            with self.subTest(label=label):
                journal = self.crash(label, 'doctor', '--migrate')
                self.assertEqual((journal['operation'], journal['schema_version'], journal['files'][-1]['role']), ('doctor.migrate', 3, 'machine_config'))
                self.machine('recover', '--rollback')
                self.assertEqual(self.controls(), controls)
                self.assertEqual(self.links(), links)
        self.crash('lock', 'doctor', '--migrate')
        self.assertEqual(self.machine('recover', '--complete')['transaction'], 'committed')
        self.assert_migrated('agentskills', head)

    def test_empty_registry_migrates_configuration_only(self):
        roots = self.legacy_machine(1, project_skills=None, user_skills=None, straggler_skills=None)
        (roots.clone / 'untracked.txt').write_text('preserve', encoding='utf-8')
        controls = self.controls()
        journal = self.crash('intent', 'doctor', '--migrate')
        self.assertEqual((journal['operation'], journal['schema_version'], journal['selected'], journal['links'], [entry['role'] for entry in journal['files']], journal['migration']['cache']),
                         ('doctor.migrate', 3, [], [], ['machine_config'], None))
        self.machine('recover', '--rollback')
        self.assertEqual(self.controls(), controls)
        data = self.machine('doctor', '--migrate')
        self.assertIn('source.dirty', codes(data['warnings']))
        config = self.read(roots.home / 'config.json')
        self.assertEqual((config['schema_version'], sorted(config['sources']), config['sources']['agentskills']['authoring']), (3, ['agentskills'], str(roots.clone)))
        config_path = str(roots.home / 'config.json')
        self.assertEqual({key: value for key, value in self.controls().items() if key != config_path}, {key: value for key, value in controls.items() if key != config_path})
        self.assertEqual(sorted(path.name for path in roots.home.iterdir()), ['config.json', 'operation.lock', 'state.json'])
        self.assertEqual((roots.clone / 'untracked.txt').read_text(encoding='utf-8'), 'preserve')
        self.machine('doctor', '--check')

    def test_clone_conditions_refuse_typed_and_write_nothing(self):
        def dirty(roots):
            (roots.clone / 'untracked.txt').write_text('preserve', encoding='utf-8')

        def unborn(roots):
            git(roots.clone, 'checkout', '-q', '--orphan', 'unborn')
            git(roots.clone, 'branch', '-q', '-D', 'main')
            git(roots.clone, 'symbolic-ref', 'HEAD', 'refs/heads/main')

        def detached(roots):
            git(roots.clone, 'checkout', '-q', '--detach')

        def diverged(roots):
            git(roots.clone, 'commit', '-q', '--allow-empty', '-m', 'local only')
            remote = git(roots.clone, 'commit-tree', 'HEAD~1^{tree}', '-p', 'HEAD~1', '-m', 'remote only')
            git(roots.clone, 'update-ref', 'refs/remotes/origin/main', remote)

        def missing(roots):
            os.rename(roots.clone, roots.base / 'moved clone')

        cases = (('dirty', dirty, 'source.dirty', 4), ('unborn', unborn, 'migration.unborn', 4), ('detached', detached, 'source.identity_mismatch', 4),
                 ('diverged', diverged, 'source.identity_mismatch', 4), ('missing', missing, 'source.missing', 3))
        for name, prepare, code, exit_code in cases:
            with self.subTest(case=name):
                roots = self.rebuild(name)
                prepare(roots)
                before = snapshot(roots.base, roots.base)
                for args in (('--dry-run',), ()):
                    error = self.machine('doctor', '--migrate', *args, code=exit_code)['error']
                    self.assertEqual((error['code'], error['details']['blockers'][0]['code']), (code, code))
                    self.assertEqual(snapshot(roots.base, roots.base), before)
                if name == 'diverged':
                    self.assertEqual(error['details']['reason'], 'diverged')

    def test_a_legacy_consumer_that_selects_nothing_migrates_to_an_empty_v2_selection(self):
        roots = self.legacy_machine(1, project_skills=(), straggler_skills=None)
        self.machine('doctor', '--migrate')
        declaration = self.read(roots.project / '.mask.json')
        self.assertEqual((declaration['schema_version'], declaration['skills']), (2, []))
        self.assertEqual(self.read(roots.project / '.mask.lock.json')['packages'], [])
        record = self.read(roots.home / 'state.json')['projects'][str(roots.project)]
        self.assertEqual((record['mode'], record['links']), ('pinned', {}))
        self.assertFalse((roots.home / 'pending.json').exists())
        self.machine('doctor', '--check')

    def test_a_refusal_keeps_the_exit_code_of_its_typed_error(self):
        roots = self.legacy_machine(1)
        git(roots.clone, 'remote', 'set-url', 'origin', 'http://example.invalid/AgentSkills.git')
        before = snapshot(roots.base, roots.base)
        for args in (('--dry-run',), ()):
            error = self.machine('doctor', '--migrate', *args, code=3)['error']
            self.assertEqual((error['code'], error['details']['blockers'][0]['code']), ('source.identity_invalid', 'source.identity_invalid'))
        self.assertEqual(snapshot(roots.base, roots.base), before)

    def test_clone_without_remote_becomes_a_local_file_tap(self):
        roots = self.legacy_machine(1, remote=False)
        data = self.machine('doctor', '--migrate')
        self.assertIn('migration.local_only_source', codes(data['warnings']))
        config = self.assert_migrated('legacy', git(roots.clone, 'rev-parse', 'HEAD'))
        self.assertEqual((config['sources']['legacy']['repository'], config['sources']['legacy']['transport']), (roots.clone.as_uri(), str(roots.clone)))

    def test_v2_alias_conflict_refuses_and_another_alias_renames_the_legacy_tap(self):
        roots = self.legacy_machine(2)
        before = snapshot(roots.base, roots.base)
        for args in (('--dry-run',), ()):
            self.assertEqual(self.machine('doctor', '--migrate', '--alias', 'extra', *args, code=4)['error']['code'], 'source.alias_conflict')
        self.assertEqual(snapshot(roots.base, roots.base), before)
        self.machine('doctor', '--migrate', '--alias', 'other')
        config = self.assert_migrated('other', git(roots.clone, 'rev-parse', 'HEAD'))
        legacy = roots.config['sources']['legacy']
        renamed = sources.binding(roots.home, 'other', legacy['transport'], 'main', 'skills', legacy['authoring'])
        self.assertEqual(config['sources'], dict(extra=roots.config['sources']['extra'], other=renamed))
        self.assertNotEqual(renamed['cache'], legacy['cache'])

    def test_renaming_a_legacy_tap_a_pinned_consumer_names_refuses_and_pinned_consumers_stay_untouched(self):
        roots = self.legacy_machine(2)
        legacy_text = (roots.home / 'config.json').read_bytes()
        # A pinned consumer installed while the legacy binding was a plain tap; then the v2 configuration returns.
        write_json(roots.home / 'config.json', dict(schema_version=3, default_targets=roots.config['default_targets'], git_timeout_seconds=30,
                                                     sources=dict(legacy=roots.config['sources']['legacy'])))
        tapped = roots.base / 'pinned project'
        tapped.mkdir()
        git(tapped, 'init', '-q', '-b', 'main')
        self.machine('install', 'alpha', '--project', tapped)
        (roots.home / 'config.json').write_bytes(legacy_text)
        pinned_controls = {name: (tapped / name).read_bytes() for name in ('.mask.json', '.mask.lock.json')}
        pinned_links = {str(leaf): os.readlink(leaf) for leaf in (tapped / '.claude/skills/alpha', tapped / '.agents/skills/alpha')}
        before = snapshot(roots.base, roots.base)
        error = self.machine('doctor', '--migrate', '--alias', 'other', code=4)['error']
        self.assertEqual((error['code'], error['details']['root']), ('source.alias_conflict', str(tapped)))
        self.assertEqual(snapshot(roots.base, roots.base), before)
        self.machine('doctor', '--migrate')
        self.assert_migrated('legacy', git(roots.clone, 'rev-parse', 'HEAD'), fresh_cache=False)
        self.assertEqual({name: (tapped / name).read_bytes() for name in pinned_controls}, pinned_controls)
        self.assertEqual({leaf: os.readlink(leaf) for leaf in pinned_links}, pinned_links)

    def test_unpushed_head_migrates_with_a_warning(self):
        roots = self.legacy_machine(1)
        git(roots.clone, 'commit', '-q', '--allow-empty', '-m', 'local only')
        head = git(roots.clone, 'rev-parse', 'HEAD')
        upstream = snapshot(roots.base, roots.upstream)
        data = self.machine('doctor', '--migrate')
        self.assertIn('migration.unpublished_commit', codes(data['warnings']))
        self.assert_migrated('agentskills', head)
        self.assertNotEqual(git(roots.upstream, 'rev-parse', 'main'), head)
        self.assertEqual(snapshot(roots.base, roots.upstream), upstream)

    def test_scoped_migration_on_a_legacy_machine_is_an_invocation_error(self):
        roots = self.legacy_machine(1)
        before = snapshot(roots.base, roots.base)
        for args in (('--project', roots.project), ('--user',)):
            self.assertEqual(self.machine('doctor', '--migrate', *args, code=2)['error']['code'], 'invocation.invalid')
        self.assertEqual(snapshot(roots.base, roots.base), before)
        controls, links = self.controls(), self.links()
        self.crash('intent', 'doctor', '--migrate')
        pending = self.controls()
        self.assertEqual(self.machine('doctor', '--migrate', code=8)['error']['code'], 'recovery.required')
        self.assertEqual(self.controls(), pending)
        # Rollback restores every control and link; the prepared cache and store payloads are retained by design.
        self.machine('recover', '--rollback')
        self.assertEqual((self.controls(), self.links()), (controls, links))


class JournalHardening(MigrationFixture):
    """Review findings R1-1 and R1-2: a link edited before the writer lock is plan.stale, and a doctor.migrate journal carries no manifests."""

    RETARGET = ("import os,sys;sys.path.insert(0,sys.argv[1]);import mask,mask_core;real=mask_core.writer_lock\n"
                "def lock(home):\n"
                "    leaf=sys.argv[2]\n"
                "    os.rmdir(leaf) if os.name=='nt' else os.unlink(leaf)\n"
                "    os.symlink(sys.argv[3],leaf,target_is_directory=True)\n"
                "    mask_core.writer_lock=real\n"
                "    return real(home)\n"
                "mask_core.writer_lock=lock\n"
                "sys.exit(mask.main(sys.argv[4:]))")

    def test_a_link_edited_before_the_writer_lock_is_plan_stale_and_nothing_is_written(self):
        roots = self.legacy_machine(1)
        leaf = roots.project / '.claude/skills/alpha'
        elsewhere = str(roots.clone / 'skills' / 'beta')
        controls = self.controls()
        run = subprocess.run([sys.executable, '-B', '-c', self.RETARGET, str(ENTRY.parent), str(leaf), elsewhere, 'doctor', '--migrate', '--json'],
                             capture_output=True, encoding='utf-8', cwd=str(roots.base), env=self.environment(), timeout=180)
        self.assertEqual((run.returncode, json.loads(run.stdout)['error']['code']), (4, 'plan.stale'), run.stdout + run.stderr)
        self.assertEqual(self.controls(), controls)
        # The link the user retargeted is left exactly where they pointed it (os.readlink may spell it with a \\?\ prefix on Windows).
        self.assertTrue(leaf.is_symlink() and os.path.samefile(leaf, elsewhere), os.readlink(leaf))

    def test_a_doctor_migration_journal_with_manifest_entries_refuses_recovery(self):
        roots = self.legacy_machine(1)
        controls, links = self.controls(), self.links()
        journal = self.crash('intent', 'doctor', '--migrate')
        path = roots.home / 'pending.json'
        original = path.read_bytes()
        text = (roots.project / '.mask.json').read_text(encoding='utf-8')
        journal['manifests'] = [dict(root=str(roots.project), before=text, after=text)]
        path.write_text(json.dumps(journal, ensure_ascii=False, sort_keys=True, indent=2) + '\n', encoding='utf-8', newline='\n')
        tampered = snapshot(roots.base, roots.base)
        for mode in ('--complete', '--rollback'):
            with self.subTest(mode=mode):
                self.assertEqual(self.machine('recover', mode, code=8)['error']['code'], 'recovery.conflict')
                self.assertEqual(snapshot(roots.base, roots.base), tampered)
        path.write_bytes(original)
        self.machine('recover', '--rollback')
        self.assertEqual((self.controls(), self.links()), (controls, links))


class PreviousProgramRecovery(MigrationFixture):
    """M12: the previous program refuses a doctor.migrate journal; the current program still rolls it back."""

    def test_previous_program_refuses_a_doctor_migration_journal(self):
        program = ENTRY.parent
        if subprocess.run(['git', '-C', str(program), 'cat-file', '-e', PREVIOUS + '^{commit}'], capture_output=True).returncode:
            self.skipTest(f'the previous program revision {PREVIOUS} is not in this checkout')
        previous = Path(tempfile.mkdtemp(prefix='mask-previous-')).resolve()
        self.addCleanup(shutil.rmtree, previous, True)
        archive = subprocess.run(['git', '-C', str(program), 'archive', '--format=tar', PREVIOUS], capture_output=True, check=True).stdout
        with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
            bundle.extractall(previous, **(dict(filter='data') if hasattr(tarfile, 'data_filter') else {}))
        roots = self.legacy_machine(1)
        controls, links = self.controls(), self.links()
        self.crash('link', 'doctor', '--migrate')
        before = snapshot(roots.base, roots.base)
        for mode in ('--complete', '--rollback'):
            with self.subTest(mode=mode):
                run = subprocess.run([sys.executable, '-B', str(previous / 'mask.py'), 'recover', mode, '--json'], capture_output=True,
                                     encoding='utf-8', cwd=str(roots.base), env=self.environment(), timeout=120)
                self.assertEqual((run.returncode, json.loads(run.stdout)['error']['code']), (8, 'recovery.conflict'), run.stdout + run.stderr)
                self.assertEqual(snapshot(roots.base, roots.base), before)
        self.machine('recover', '--rollback')
        self.assertEqual((self.controls(), self.links()), (controls, links))
