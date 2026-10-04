"""Optional upgrade commits through the shipped subprocess CLI and disposable Git roots."""
import json
from pathlib import Path
import subprocess
import sys
import unittest

from tests.public_support import PublicFixture, ENTRY
from tests import test_cli_v2 as public_cli
from tests import test_setup as setup_tests


class UpgradeCommit(PublicFixture):
    raw = public_cli.CliV2.raw

    def setUp(self):
        super().setUp()
        self.git(self.project, 'config', 'user.name', 'Fixture')
        self.git(self.project, 'config', 'user.email', 'fixture@example.invalid')
        (self.project / 'other.txt').write_text('base\n')
        self.git(self.project, 'add', 'other.txt')
        self.git(self.project, 'commit', '-m', 'initial project')
        self.assertTrue(self.machine('install', 'alpha')['ok'])

    def commit_controls(self, root=None):
        root = root or self.project
        self.git(root, 'add', '.mask.json', '.mask.lock.json')
        self.git(root, 'commit', '-m', 'record controls')

    def upgrade(self, *args, **kwargs):
        return self.machine('upgrade', '--commit', *args, **kwargs)

    def row(self, result, root=None):
        return next(row for row in result['data']['commits'] if row['root'] == str(root or self.project))

    def changed_paths(self, root=None):
        return self.git(root or self.project, 'diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').splitlines()

    def next_version(self):
        (self.source / 'skills/alpha/support.txt').write_text('new payload\n', encoding='utf-8', newline='\n')
        return self.publish()

    def hook(self, body, name='pre-commit', root=None):
        root = root or self.project
        path = Path(self.git(root, 'rev-parse', '--git-path', 'hooks/' + name))
        if not path.is_absolute():
            path = root / path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('#!/bin/sh\n' + body + '\n')
        path.chmod(0o755)
        return path

    def test_commit_only_untracked_controls_preserves_unrelated_staging_and_converges(self):
        (self.project / 'other.txt').write_text('staged\n')
        self.git(self.project, 'add', 'other.txt')
        staged = self.git(self.project, 'ls-files', '--stage', 'other.txt')
        (self.project / 'other.txt').write_text('unstaged\n')
        preview = self.upgrade('--dry-run')
        self.assertTrue(preview['ok'], preview)
        self.assertTrue(preview['would_change'])
        self.assertEqual(self.row(preview)['status'], 'planned')
        before = self.git(self.project, 'rev-parse', 'HEAD')
        run = self.upgrade('--approve-plan', preview['data']['plan_hash'])
        self.assertTrue(run['ok'], run)
        self.assertEqual(self.row(run)['status'], 'committed')
        self.assertEqual(self.changed_paths(), ['.mask.json', '.mask.lock.json'])
        self.assertEqual(self.git(self.project, 'rev-parse', 'HEAD^'), before)
        self.assertEqual(self.git(self.project, 'log', '-1', '--format=%s'), 'chore(mask): upgrade skills')
        self.assertEqual(self.git(self.project, 'ls-files', '--stage', 'other.txt'), staged)
        self.assertEqual((self.project / 'other.txt').read_text(), 'unstaged\n')
        self.assertEqual(self.git(self.project, 'diff', '--name-only', '--', '.mask.json', '.mask.lock.json'), '')
        self.assertEqual(self.git(self.project, 'diff', '--cached', '--name-only', '--', '.mask.json', '.mask.lock.json'), '')
        self.assertTrue(run['changed'])
        self.assertEqual(run['transaction'], 'not_needed')
        again = self.upgrade('--offline')
        self.assertTrue(again['ok'], again)
        self.assertFalse(again['changed'])
        self.assertEqual(self.row(again)['status'], 'not_needed')

    def test_defaults_flag_and_personal_only_reject_before_refresh(self):
        caps = self.machine('capabilities')
        upgrade = next(row for row in caps['data']['commands'] if row['name'] == 'upgrade')
        self.assertIn('commit', [arg['name'] for arg in upgrade['arguments']])
        self.assertIn('--commit', self.human('upgrade', '--help').stdout)
        head = self.git(self.project, 'rev-parse', 'HEAD')
        self.assertNotIn('commits', self.machine('upgrade')['data'])
        self.assertEqual(self.git(self.project, 'rev-parse', 'HEAD'), head)
        run = PublicFixture.raw(self, 'upgrade', '--user', '--commit', '--json')
        self.assertEqual(run.returncode, 2)
        self.assertEqual(json.loads(run.stdout)['error']['code'], 'invocation.invalid')
        self.assertFalse((self.home / 'refresh.json').exists())

    def test_full_partially_staged_controls_and_new_version_exclude_other_files(self):
        self.commit_controls()
        declaration = self.project / '.mask.json'
        # LF as MASK writes it: a CRLF working file would be committed as LF wherever core.autocrlf is set.
        declaration.write_text(declaration.read_text(encoding='utf-8') + '\n', encoding='utf-8', newline='\n')
        self.git(self.project, 'add', '.mask.json')
        declaration.write_text(declaration.read_text(encoding='utf-8') + '\n', encoding='utf-8', newline='\n')
        expected = declaration.read_bytes()
        (self.project / 'other.txt').write_text('staged unrelated\n')
        self.git(self.project, 'add', 'other.txt')
        staged = self.git(self.project, 'ls-files', '--stage', 'other.txt')
        candidate = self.next_version()
        run = self.upgrade('alpha')
        self.assertTrue(run['ok'], run)
        row = self.row(run)
        self.assertEqual(row['paths'], ['.mask.json', '.mask.lock.json'])
        self.assertEqual(row['included_existing_changes'], ['.mask.json'])
        self.assertEqual(self.git(self.project, 'ls-files', '--stage', 'other.txt'), staged)
        committed = subprocess.check_output(['git', '-C', str(self.project), 'show', 'HEAD:.mask.json'])
        self.assertEqual(committed, expected)
        self.assertEqual(json.loads((self.project / '.mask.lock.json').read_text(encoding='utf-8'))['packages'][0]['commit'], candidate)
        self.assertEqual(self.changed_paths(), ['.mask.json', '.mask.lock.json'])
        self.assertEqual(self.git(self.project, 'diff', '--cached', '--name-only', '--', '.mask.json', '.mask.lock.json'), '')

    def test_readonly_preview_and_git_control_and_intent_staleness(self):
        sentinel = self.project / 'hook-ran'
        self.hook('echo ran > hook-ran')
        index = self.project / '.git/index'
        before_index = index.read_bytes()
        before_controls = {name: (self.project / name).read_bytes() for name in ('.mask.json', '.mask.lock.json')}
        before_head = self.git(self.project, 'rev-parse', 'HEAD')
        preview = self.upgrade('--dry-run')
        self.assertTrue(preview['ok'], preview)
        self.assertFalse(sentinel.exists())
        self.assertEqual(index.read_bytes(), before_index)
        self.assertEqual(before_controls, {name: (self.project / name).read_bytes() for name in before_controls})
        self.assertEqual(self.git(self.project, 'rev-parse', 'HEAD'), before_head)
        approved = preview['data']['plan_hash']
        run = self.machine('upgrade', '--approve-plan', approved)
        self.assertEqual(run['error']['code'], 'plan.stale')
        for change in ('index', 'controls', 'head', 'branch'):
            with self.subTest(change=change):
                preview = self.upgrade('--dry-run')
                if change == 'index':
                    (self.project / 'other.txt').write_text('new staging\n')
                    self.git(self.project, 'add', 'other.txt')
                elif change == 'controls':
                    path = self.project / '.mask.lock.json'
                    path.write_text(path.read_text() + '\n')
                elif change == 'head':
                    self.git(self.project, 'commit', '--only', 'other.txt', '-m', 'external change')
                    sentinel.unlink(missing_ok=True)
                else:
                    self.git(self.project, 'checkout', '-b', 'new-branch')
                snapshot = {name: (self.project / name).read_bytes() for name in before_controls}
                run = self.upgrade('--approve-plan', preview['data']['plan_hash'])
                self.assertEqual(run['error']['code'], 'plan.stale', run)
                self.assertEqual(snapshot, {name: (self.project / name).read_bytes() for name in before_controls})
                self.assertFalse(sentinel.exists())

    def test_git_ineligible_candidates_refuse_before_consumer_effects(self):
        original = {name: (self.project / name).read_bytes() for name in ('.mask.json', '.mask.lock.json')}
        self.next_version()
        for marker in ('MERGE_HEAD', 'rebase-merge', 'rebase-apply', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'sequencer', 'BISECT_LOG'):
            with self.subTest(marker=marker):
                path = self.project / '.git' / marker
                path.write_text('in progress\n')
                run = self.upgrade()
                self.assertEqual(run['error']['code'], 'upgrade.commit_ineligible', run)
                self.assertEqual(self.row(run)['status'], 'blocked')
                self.assertEqual(original, {name: (self.project / name).read_bytes() for name in original})
                path.unlink()
        self.git(self.project, 'checkout', '--detach')
        run = self.upgrade()
        self.assertEqual(run['error']['code'], 'upgrade.commit_ineligible')
        self.git(self.project, 'checkout', 'main')
        (self.project / '.gitignore').write_text('.mask.json\n')
        run = self.upgrade('--dry-run')
        self.assertEqual(run['error']['code'], 'upgrade.commit_ineligible')

    def test_noop_detached_head_needs_no_commit_eligibility(self):
        self.commit_controls()
        self.git(self.project, 'checkout', '--detach')
        run = self.upgrade('--offline')
        self.assertTrue(run['ok'], run)
        self.assertEqual(self.row(run)['status'], 'not_needed')
        self.assertFalse(run['changed'])

    def test_linked_worktree_commit_uses_its_branch_and_index(self):
        self.commit_controls()
        main_head = self.git(self.project, 'rev-parse', 'HEAD')
        worktree = self.base / 'linked worktree'
        self.git(self.project, 'worktree', 'add', '-b', 'linked', str(worktree))
        self.assertTrue(self.machine('register', '--project', worktree)['ok'])
        candidate = self.next_version()
        run = self.upgrade('--project', worktree)
        self.assertTrue(run['ok'], run)
        self.assertEqual(self.row(run, worktree)['status'], 'committed')
        self.assertEqual(self.changed_paths(worktree), ['.mask.lock.json'])
        self.assertEqual(self.git(self.project, 'rev-parse', 'HEAD'), main_head)
        self.assertEqual(json.loads((worktree / '.mask.lock.json').read_text(encoding='utf-8'))['packages'][0]['commit'], candidate)
        self.assertEqual(self.git(worktree, 'symbolic-ref', '--short', 'HEAD'), 'linked')

    def test_hook_failure_preserves_upgrade_then_retry_commits_once(self):
        self.commit_controls()
        head = self.git(self.project, 'rev-parse', 'HEAD')
        candidate = self.next_version()
        hook = self.hook('echo ran > hook-ran\nexit 1')
        run = self.upgrade()
        self.assertEqual(run['error']['code'], 'upgrade.commit_failed', run)
        self.assertEqual(self.row(run)['status'], 'failed')
        self.assertEqual(run['transaction'], 'committed')
        self.assertTrue(run['changed'])
        self.assertEqual(self.git(self.project, 'rev-parse', 'HEAD'), head)
        self.assertTrue((self.project / 'hook-ran').exists())
        self.assertEqual(json.loads((self.project / '.mask.lock.json').read_text(encoding='utf-8'))['packages'][0]['commit'], candidate)
        hook.unlink()
        retry = self.upgrade('--offline')
        self.assertTrue(retry['ok'], retry)
        self.assertEqual(self.row(retry)['status'], 'committed')
        self.assertEqual(self.git(self.project, 'rev-parse', 'HEAD^'), head)
        self.assertEqual(self.row(self.upgrade('--offline'))['status'], 'not_needed')

    def test_all_retains_successes_and_blocks_only_ineligible_projects(self):
        self.commit_controls()
        other = self.base / 'blocked-project'
        other.mkdir()
        self.git(other, 'init', '-b', 'main')
        self.assertTrue(self.machine('install', 'alpha', '--project', other)['ok'])
        self.assertTrue(self.machine('install', 'alpha', '--user')['ok'])
        before = (other / '.mask.lock.json').read_bytes()
        candidate = self.next_version()
        run = self.upgrade('--all')
        self.assertEqual(run['error']['code'], 'upgrade.incomplete', run)
        self.assertEqual(self.row(run)['status'], 'committed')
        self.assertEqual(self.row(run, other)['status'], 'blocked')
        self.assertEqual(self.row(run, self.personal)['status'], 'not_applicable')
        self.assertEqual((other / '.mask.lock.json').read_bytes(), before)
        self.assertEqual(json.loads((self.home / 'user.lock.json').read_text(encoding='utf-8'))['packages'][0]['commit'], candidate)

    def test_all_commit_failure_keeps_success_and_reports_nested_error(self):
        other = self.base / 'other-project'
        other.mkdir()
        self.git(other, 'init', '-b', 'main')
        self.git(other, 'config', 'user.name', 'Fixture')
        self.git(other, 'config', 'user.email', 'fixture@example.invalid')
        (other / 'file').write_text('base')
        self.git(other, 'add', 'file')
        self.git(other, 'commit', '-m', 'initial')
        self.assertTrue(self.machine('install', 'alpha', '--project', other)['ok'])
        self.hook('exit 1', root=other)
        run = self.upgrade('--all')
        self.assertEqual(run['error']['code'], 'upgrade.incomplete', run)
        self.assertEqual(self.row(run)['status'], 'committed')
        self.assertEqual(self.row(run, other)['status'], 'failed')
        self.assertTrue(run['error']['details']['errors'])

    def test_hook_unexpected_tree_is_reported_and_preserved(self):
        self.hook('echo hook > extra\ngit add extra')
        run = self.upgrade()
        self.assertEqual(run['error']['code'], 'upgrade.commit_failed', run)
        self.assertEqual(self.row(run)['status'], 'failed')
        self.assertIsNotNone(self.row(run)['commit'])
        self.assertTrue(run['changed'])
        self.assertIn('extra', self.changed_paths())
        self.assertTrue((self.project / 'extra').exists())

    def test_git_timeout_after_created_commit_is_observed_without_duplicate(self):
        self.machine('config', 'set', '--git-timeout', '1')
        self.hook('echo started > hook-ran\nsleep 10', name='post-commit')
        run = self.upgrade()
        self.assertEqual(run['error']['code'], 'upgrade.commit_failed', run)
        self.assertEqual(self.row(run)['status'], 'committed')
        self.assertIsNotNone(self.row(run)['commit'])
        self.assertEqual(self.row(run)['error']['code'], 'git.timeout')
        self.assertTrue(run['changed'])
        again = self.upgrade('--offline')
        self.assertTrue(again['ok'], again)
        self.assertEqual(self.row(again)['status'], 'not_needed')

    def test_human_output_discloses_preview_commit_and_failure(self):
        preview = self.human('upgrade', '--commit', '--dry-run')
        self.assertEqual(preview.returncode, 0)
        self.assertIn('Git commit:', preview.stdout)
        self.assertIn('includes existing changes: .mask.json, .mask.lock.json', preview.stdout)
        self.assertIn('chore(mask): upgrade skills', preview.stdout)
        self.hook('exit 1')
        failure = self.human('upgrade', '--commit')
        self.assertEqual(failure.returncode, 5)
        self.assertIn(str(self.project), failure.stderr)
        self.assertIn('failed', failure.stderr)

    def test_missing_identity_and_signing_failure_preserve_controls(self):
        self.git(self.project, 'config', 'user.useConfigOnly', 'true')
        self.git(self.project, 'config', '--unset', 'user.name')
        self.git(self.project, 'config', '--unset', 'user.email')
        run = self.upgrade()
        self.assertEqual(run['error']['code'], 'upgrade.commit_failed', run)
        self.assertIsNone(self.row(run)['commit'])
        self.git(self.project, 'config', 'user.name', 'Fixture')
        self.git(self.project, 'config', 'user.email', 'fixture@example.invalid')
        self.git(self.project, 'config', 'commit.gpgsign', 'true')
        self.git(self.project, 'config', 'gpg.program', str(self.base / 'missing-gpg'))
        run = self.upgrade()
        self.assertEqual(run['error']['code'], 'upgrade.commit_failed', run)
        self.assertEqual(self.row(run)['status'], 'failed')
        self.assertIsNone(self.row(run)['commit'])
        self.assertEqual(self.git(self.project, 'ls-files', '--', '.mask.json', '.mask.lock.json'), '')

    def test_configured_hooks_and_hook_control_edits_are_preserved(self):
        directory = self.project / 'custom-hooks'
        directory.mkdir()
        self.git(self.project, 'config', 'core.hooksPath', str(directory))
        hook = directory / 'pre-commit'
        hook.write_text('#!/bin/sh\nprintf "\\n" >> .mask.json\necho ran > hook-ran\n')
        hook.chmod(0o755)
        before = (self.project / '.mask.json').read_bytes()
        run = self.upgrade()
        self.assertEqual(run['error']['code'], 'upgrade.commit_failed', run)
        self.assertTrue((self.project / 'hook-ran').exists())
        self.assertEqual((self.project / '.mask.json').read_bytes(), before + b'\n')
        self.assertIsNotNone(self.row(run)['commit'])
        self.assertEqual(self.row(run)['status'], 'failed')

    def test_concurrent_real_index_edit_survives_created_commit(self):
        (self.project / 'other.txt').write_text('concurrent staging\n')
        self.hook('unset GIT_INDEX_FILE\ngit add other.txt')
        run = self.upgrade()
        self.assertEqual(run['error']['code'], 'upgrade.commit_failed', run)
        self.assertIsNotNone(self.row(run)['commit'])
        self.assertIn('other.txt', self.git(self.project, 'diff', '--cached', '--name-only'))
        self.assertEqual(self.git(self.project, 'show', ':other.txt'), 'concurrent staging')

    def test_unmerged_index_refuses_and_preserves_index(self):
        oid = self.git(self.project, 'rev-parse', 'HEAD:other.txt')
        # Bytes: a text-mode stdin turns each \n into \r\n on Windows, and Git would read paths ending in \r.
        subprocess.run(['git', '-C', str(self.project), 'update-index', '--index-info'],
                       input=f'0 {"0" * 40}\tother.txt\n100644 {oid} 1\tother.txt\n100644 {oid} 2\tother.txt\n'.encode('utf-8'),
                       check=True)
        self.assertIn('other.txt', self.git(self.project, 'diff', '--name-only', '--diff-filter=U'))
        index = (self.project / '.git/index').read_bytes()
        run = self.upgrade()
        self.assertEqual(run['error']['code'], 'upgrade.commit_ineligible', run)
        self.assertEqual((self.project / '.git/index').read_bytes(), index)

    def test_changed_eligibility_invalidates_approved_preview(self):
        self.commit_controls()
        self.next_version()
        self.machine('tap', 'fetch')
        preview = self.upgrade('--dry-run')
        before = (self.project / '.mask.lock.json').read_bytes()
        (self.project / '.git/MERGE_HEAD').write_text('external operation\n')
        run = self.upgrade('--approve-plan', preview['data']['plan_hash'])
        self.assertEqual(run['error']['code'], 'plan.stale', run)
        self.assertEqual((self.project / '.mask.lock.json').read_bytes(), before)

    def test_existing_index_lock_survives_commit_bookkeeping_failure(self):
        index = (self.project / '.git/index').read_bytes()
        lock = self.project / '.git/index.lock'
        lock.write_bytes(b'external writer')
        run = self.upgrade()
        self.assertEqual(run['error']['code'], 'upgrade.commit_failed', run)
        self.assertIsNotNone(self.row(run)['commit'])
        self.assertTrue(run['changed'])
        self.assertEqual(lock.read_bytes(), b'external writer')
        self.assertEqual((self.project / '.git/index').read_bytes(), index)

    def test_commit_message_hook_effect_is_reported_and_preserved(self):
        self.hook('printf "%s\\n" changed-message > "$1"', name='commit-msg')
        run = self.upgrade()
        self.assertEqual(run['error']['code'], 'upgrade.commit_failed', run)
        self.assertIsNotNone(self.row(run)['commit'])
        self.assertEqual(self.git(self.project, 'log', '-1', '--format=%s'), 'changed-message')

    def test_bundle_upgrade_commits_changed_declaration_and_lock(self):
        index = dict(schema_version=1, packages={name: 'skills/' + name for name in ('alpha', 'beta')},
                     bundles={'fixture': dict(skills=[dict(source='agentskills', id='alpha')])})
        path = self.source / 'mask-source.json'
        path.write_text(json.dumps(index))
        self.git(self.source, 'add', 'mask-source.json')
        self.publish('bundle index')
        self.machine('tap', 'fetch')
        self.assertTrue(self.machine('bundle', 'install', 'agentskills/fixture')['ok'])
        self.commit_controls()
        index['bundles']['fixture']['skills'].append(dict(source='agentskills', id='beta'))
        path.write_text(json.dumps(index))
        self.git(self.source, 'add', 'mask-source.json')
        self.publish('expanded bundle')
        run = self.upgrade()
        self.assertTrue(run['ok'], run)
        self.assertEqual(self.changed_paths(), ['.mask.json', '.mask.lock.json'])
        self.assertEqual(self.row(run)['included_existing_changes'], [])
        self.assertEqual({row['id'] for row in json.loads((self.project / '.mask.json').read_text(encoding='utf-8'))['skills']}, {'alpha', 'beta'})

    def test_nonregular_controls_are_blocked_without_reading_or_replacing_them(self):
        other = self.base / 'regular-project'
        other.mkdir()
        self.git(other, 'init', '-b', 'main')
        self.git(other, 'config', 'user.name', 'Fixture')
        self.git(other, 'config', 'user.email', 'fixture@example.invalid')
        (other / 'base').write_text('base')
        self.git(other, 'add', 'base')
        self.git(other, 'commit', '-m', 'base')
        self.assertTrue(self.machine('install', 'alpha', '--project', other)['ok'])
        self.next_version()
        for name in ('.mask.json', '.mask.lock.json'):
            with self.subTest(control=name):
                control = self.project / name
                original = control.read_bytes()
                target = self.base / ('retained-' + name)
                control.rename(target)
                control.symlink_to(target)
                run = self.upgrade()
                self.assertEqual(run['error']['code'], 'upgrade.commit_ineligible', run)
                self.assertEqual(self.row(run)['status'], 'blocked')
                run = self.upgrade('--all')
                self.assertEqual(run['error']['code'], 'upgrade.incomplete', run)
                self.assertEqual(self.row(run)['status'], 'blocked')
                self.assertIn(self.row(run, other)['status'], ('committed', 'not_needed'))
                self.assertTrue(control.is_symlink())
                self.assertEqual(target.read_bytes(), original)
                control.unlink()
                target.rename(control)


class UpgradeCommitReadiness(setup_tests.SetupFixture):
    raw = public_cli.CliV2.raw

    def setUp(self):
        super().setUp()
        self.entrypoint = ENTRY
        self.git(self.project, 'config', 'user.name', 'Fixture')
        self.git(self.project, 'config', 'user.email', 'fixture@example.invalid')
        (self.project / 'base').write_text('base')
        self.git(self.project, 'add', 'base')
        self.git(self.project, 'commit', '-m', 'base')

    def test_setup_consent_and_readiness_precede_control_commit(self):
        refused = self.machine('upgrade', '--commit')
        self.assertEqual(refused['error']['code'], 'confirmation.required')
        self.assertEqual(refused['data']['commits'][0]['status'], 'not_attempted')
        self.assertEqual(self.launches(), 0)
        hook = self.project / '.git/hooks/pre-commit'
        hook.write_text('#!/bin/sh\ntest -f .mask/generated/implement-rfc/native-roles.lock.json || exit 1\necho ready > hook-ran\n')
        hook.chmod(0o755)
        preview = self.machine('upgrade', '--commit', '--dry-run')
        self.assertTrue(preview['ok'], preview)
        run = self.machine('upgrade', '--commit', '--approve-plan', preview['data']['plan_hash'])
        self.assertTrue(run['ok'], run)
        self.assertEqual(run['data']['commits'][0]['status'], 'committed')
        self.assertEqual(self.launches(), 1)
        self.assertTrue((self.project / 'hook-ran').exists())
        self.assertEqual(self.git(self.project, 'diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD').splitlines(),
                         ['.mask.json', '.mask.lock.json'])

    def test_failed_setup_starts_no_commit_and_preserves_applied_upgrade(self):
        self.write_script(before='    raise SystemExit(3)')
        self.publish('failed setup candidate')
        self.machine('tap', 'fetch')
        head = self.git(self.project, 'rev-parse', 'HEAD')
        preview = self.machine('upgrade', '--commit', '--dry-run')
        run = self.machine('upgrade', '--commit', '--approve-plan', preview['data']['plan_hash'])
        self.assertFalse(run['ok'], run)
        self.assertEqual(run['data']['commits'][0]['status'], 'not_attempted')
        self.assertEqual(run['transaction'], 'committed')
        self.assertTrue(run['changed'])
        self.assertEqual(self.git(self.project, 'rev-parse', 'HEAD'), head)
