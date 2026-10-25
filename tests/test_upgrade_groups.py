"""upgrade --all upgrades once per repository and propagates the result (MASK-0146).

Unit tests cover identity normalization, grouping and canonical selection. The integration test uses
real Git: two linked worktrees and two clones of one repository, a clone with modified controls and an
unrelated repository, all registered in one disposable MASK home.
"""
import json
from pathlib import Path
import subprocess
import sys
import unittest

import mask_upgrade_groups as groups
from tests.public_support import PublicFixture
from tests.support import TAP


def member(root, *, common=None, origin=None, branch='main', head='h', default='main', upstream=None,
           controls=None, head_controls=None, operation=False):
    controls = controls or {'.mask.json': 'a', '.mask.lock.json': 'b'}
    return dict(root=root, scope='project', git=True, common_dir=common or root + '/.git', origin=origin, branch=branch,
                head=head, default_branch=default, upstream=upstream, controls=controls,
                head_controls=controls if head_controls is None else head_controls, operation=operation)


class Identity(unittest.TestCase):
    def test_network_spellings_of_one_repository_normalize_together(self):
        root = Path.cwd()
        spellings = ['https://github.com/Owner/Repo.git', 'https://user@GitHub.com/Owner/Repo/', 'git@github.com:Owner/Repo.git',
                     'ssh://git@github.com:22/Owner/Repo', 'ssh://git@github.com/Owner/Repo.git']
        self.assertEqual({groups.normalize_url(url, root) for url in spellings}, {'github.com/Owner/Repo'})
        self.assertNotEqual(groups.normalize_url('git@github.com:Owner/Fork.git', root), 'github.com/Owner/Repo')

    def test_local_paths_resolve_and_do_not_look_like_scp(self):
        root = Path.cwd().resolve()
        local = groups.normalize_url(str(root / 'remote' / 'app.git'), root)
        self.assertTrue(local.startswith('file:'), local)
        self.assertEqual(groups.normalize_url('remote/app.git', root), local)
        self.assertEqual(groups.normalize_url((root / 'remote' / 'app.git').as_uri(), root), local)


class Grouping(unittest.TestCase):
    def test_worktrees_and_clones_union_and_singletons_stay_independent(self):
        rows = [member('/a', common='/a/.git', origin='host/r'), member('/b', common='/a/.git', origin=None),
                member('/c', origin='host/r'), member('/d', origin='host/other'), dict(member('/e'), git=False)]
        found = groups.partition(rows)
        self.assertEqual([[row['root'] for row in group] for group in found], [['/a', '/b', '/c']])
        self.assertEqual(groups.identity(found[0]), 'host/r')

    def test_canonical_prefers_invoking_then_default_branch_then_clean_then_path(self):
        rows = [member('/a', branch='feature'), member('/b'), member('/c', controls={'x': '1'}, head_controls={'x': '2'}), member('/d')]
        self.assertEqual(groups.choose(rows, '/a', True, set())[0]['root'], '/a')
        chosen, reason = groups.choose(rows, None, True, set())
        self.assertEqual((chosen['root'], reason), ('/b', 'default_branch_first_path'))
        chosen, reason = groups.choose([member('/z'), member('/c', controls={'x': '1'}, head_controls={'x': '2'})], None, True, set())
        self.assertEqual(chosen['root'], '/z')

    def test_ambiguity_detached_operations_and_dev_links(self):
        self.assertEqual(groups.choose([member('/a', branch='x'), member('/b', branch='y')], None, True, set()), (None, 'ambiguous'))
        chosen, reason = groups.choose([member('/a', branch=None), member('/b', branch='y')], None, True, set())
        self.assertEqual((chosen['root'], reason), ('/b', 'only_candidate'))
        # Without --commit a detached checkout can carry the upgrade.
        self.assertEqual(groups.choose([member('/a', branch=None), member('/b', branch=None)], None, False, set()), (None, 'ambiguous'))
        self.assertEqual(groups.choose([member('/a', operation=True), member('/b')], None, True, {'/b'}), (None, 'no_candidate'))
        unknown = [member('/a', branch='trunk', default=None), member('/b', branch='master', default=None)]
        self.assertEqual(groups.choose(unknown, None, True, set())[0]['root'], '/b')
        upstream = [member('/a', branch='local', upstream='origin/main'), member('/b', branch='other')]
        self.assertEqual(groups.choose(upstream, None, True, set())[0]['root'], '/a')

    def test_adoption_requires_the_canonical_start(self):
        start = {'.mask.json': 'a', '.mask.lock.json': 'b'}
        final = {'.mask.json': 'a', '.mask.lock.json': 'c'}
        item = lambda row: dict(group=dict(git=row))
        self.assertEqual(groups.adoption(item(member('/m')), start, final, True), ('adopt', 'same_controls'))
        self.assertEqual(groups.adoption(item(member('/m', controls=final)), start, final, True), ('current', 'already_adopted'))
        dirty = member('/m', controls=start, head_controls={'.mask.json': 'a', '.mask.lock.json': 'old'})
        self.assertEqual(groups.adoption(item(dirty), start, final, True), ('independent', 'controls_modified'))
        self.assertEqual(groups.adoption(item(dirty), start, final, False), ('adopt', 'same_controls'))
        behind = member('/m', controls={'.mask.json': 'a', '.mask.lock.json': 'old'})
        self.assertEqual(groups.adoption(item(behind), start, final, True), ('independent', 'controls_diverged'))


class RepositoryGroups(PublicFixture):
    """One repository with a primary checkout, two linked worktrees and three clones, plus an unrelated repository."""

    def raw(self, *args, cwd=None, env=None, stdin=subprocess.DEVNULL):
        # Seven checkouts in one activation outgrow the shared 60-second bound on a loaded Windows host.
        return subprocess.run([sys.executable, '-B', str(self.entrypoint), *map(str, args)], capture_output=True, encoding='utf-8',
                              cwd=str(cwd or self.project), env=self.environment(env), stdin=stdin, timeout=300)

    def identity(self, root):
        self.git(root, 'config', 'user.name', 'Fixture')
        self.git(root, 'config', 'user.email', 'fixture@example.invalid')

    def commit_file(self, root, name, text):
        (root / name).write_text(text, encoding='utf-8', newline='\n')
        self.git(root, 'add', name)
        self.git(root, 'commit', '-q', '-m', 'change ' + name)
        return self.git(root, 'rev-parse', 'HEAD')

    def setUp(self):
        super().setUp()
        self.identity(self.project)
        first = self.commit_file(self.project, 'other.txt', 'base\n')
        self.assertTrue(self.machine('install', 'alpha')['ok'])
        self.git(self.project, 'add', '.mask.json', '.mask.lock.json')
        self.git(self.project, 'commit', '-q', '-m', 'record controls')
        controls = self.git(self.project, 'rev-parse', 'HEAD')
        self.origin = self.base / 'remote' / 'app.git'
        self.origin.parent.mkdir()
        self.git(self.base, 'init', '-q', '--bare', '-b', 'main', str(self.origin))
        self.git(self.project, 'remote', 'add', 'origin', str(self.origin))
        self.git(self.project, 'push', '-q', '-u', 'origin', 'main')
        self.git(self.project, 'remote', 'set-head', 'origin', 'main')
        # The detached worktree stays on the controls commit; main then moves past it with an unrelated change.
        self.detached = self.base / 'worktree detached'
        self.git(self.project, 'worktree', 'add', '-q', '--detach', str(self.detached), controls)
        self.base_head = self.commit_file(self.project, 'other.txt', 'second\n')
        self.git(self.project, 'push', '-q', 'origin', 'main')
        self.feature = self.base / 'worktree feature'
        self.git(self.project, 'worktree', 'add', '-q', '-b', 'feature', str(self.feature))
        self.same = self.base / 'clone same'
        self.ahead = self.base / 'clone ahead'
        self.dirty = self.base / 'clone dirty'
        for clone in (self.same, self.ahead, self.dirty):
            self.git(self.base, 'clone', '-q', str(self.origin), str(clone))
            self.identity(clone)
        self.ahead_head = self.commit_file(self.ahead, 'local.txt', 'local work\n')
        declaration = self.dirty / '.mask.json'
        declaration.write_bytes(declaration.read_bytes() + b'\n')
        self.unrelated = self.base / 'unrelated'
        self.unrelated.mkdir()
        self.git(self.unrelated, 'init', '-q', '-b', 'main')
        self.identity(self.unrelated)
        self.commit_file(self.unrelated, 'file.txt', 'base\n')
        self.assertTrue(self.machine('install', 'alpha', '--project', self.unrelated)['ok'])
        self.git(self.unrelated, 'add', '.mask.json', '.mask.lock.json')
        self.git(self.unrelated, 'commit', '-q', '-m', 'record controls')
        for root in (self.detached, self.feature, self.same, self.ahead, self.dirty):
            self.assertTrue(self.machine('register', '--project', root)['ok'], root)
        self.first = first

    def head(self, root, ref='HEAD'):
        return self.git(root, 'rev-parse', ref)

    def locked(self, root):
        return json.loads((root / '.mask.lock.json').read_text(encoding='utf-8'))['packages'][0]['commit']

    def commit_row(self, result, root):
        return next(row for row in result['data']['commits'] if row['root'] == str(root))

    def test_all_commit_upgrades_once_and_propagates_to_worktrees_and_clones(self):
        (self.source / 'skills/alpha/support.txt').write_text('new payload\n', encoding='utf-8', newline='\n')
        candidate = self.publish()
        self.assertTrue(self.machine('tap', 'fetch', TAP)['ok'])
        heads = {root: self.head(root) for root in (self.unrelated, self.dirty)}
        preview = self.machine('upgrade', '--all', '--commit', '--dry-run')
        self.assertTrue(preview['ok'], preview)
        [group] = preview['data']['groups']
        self.assertEqual(group['canonical'], str(self.project))
        self.assertEqual(group['reason'], 'invoking_checkout')
        self.assertTrue(group['identity'].startswith('file:'), group)
        actions = {row['root']: row['action'] for row in group['members']}
        self.assertEqual(actions, {str(self.project): 'canonical', str(self.feature): 'adopt', str(self.detached): 'adopt',
                                   str(self.same): 'adopt', str(self.ahead): 'adopt', str(self.dirty): 'independent'})
        self.assertNotIn(str(self.unrelated), actions)
        self.assertEqual(self.commit_row(preview, self.detached)['detached'], True)
        self.assertEqual({str(root): self.commit_row(preview, root)['propagation'] for root in (self.feature, self.same, self.ahead, self.detached)},
                         {str(self.feature): 'fast_forward', str(self.same): 'fast_forward', str(self.ahead): 'cherry_pick', str(self.detached): 'cherry_pick'})
        self.assertEqual(self.commit_row(preview, self.dirty)['status'], 'uncommitted')
        self.assertEqual(self.commit_row(preview, self.unrelated)['status'], 'planned')
        human = self.human('upgrade', '--all', '--commit', '--dry-run')
        self.assertIn('Repository ', human.stdout)
        self.assertIn('detached HEAD', human.stdout)
        self.assertEqual(self.head(self.project), self.base_head)

        run = self.machine('upgrade', '--all', '--commit', '--approve-plan', preview['data']['plan_hash'])
        self.assertTrue(run['ok'], run)
        canonical = self.head(self.project)
        self.assertEqual(self.head(self.project, 'HEAD^'), self.base_head)
        self.assertEqual(self.commit_row(run, self.project)['status'], 'committed')
        # Worktree on another branch and a clone at the same commit are fast-forwarded to the very same commit.
        for root in (self.feature, self.same):
            row = self.commit_row(run, root)
            self.assertEqual((row['status'], row['propagation'], row['commit']), ('committed', 'fast_forward', canonical), row)
            self.assertEqual(self.head(root), canonical)
            self.assertEqual(self.git(root, 'status', '--porcelain', '--', '.mask.json', '.mask.lock.json'), '')
        self.assertEqual(self.git(self.feature, 'symbolic-ref', '--short', 'HEAD'), 'feature')
        self.assertEqual(self.git(self.same, 'rev-parse', '--abbrev-ref', 'HEAD'), 'main')
        self.assertEqual(self.head(self.same, 'origin/main'), self.base_head)  # Nothing pushed, no remote-tracking ref moved.
        self.assertEqual(self.head(self.origin, 'main'), self.base_head)
        # A clone with local work and the detached worktree get a cherry-pick of the canonical commit.
        for root, parent in ((self.ahead, self.ahead_head), (self.detached, None)):
            row = self.commit_row(run, root)
            self.assertEqual((row['status'], row['propagation']), ('committed', 'cherry_pick'), row)
            self.assertEqual(self.head(root, 'HEAD^'), parent or row['before_head'])
            self.assertEqual(self.git(root, 'log', '-1', '--format=%an%n%ad%n%B', 'HEAD'), self.git(self.project, 'log', '-1', '--format=%an%n%ad%n%B', canonical))
            self.assertEqual(self.git(root, 'diff', '--name-only', 'HEAD^', 'HEAD').splitlines(), ['.mask.lock.json'])
            self.assertEqual(self.git(root, 'status', '--porcelain', '--', '.mask.json', '.mask.lock.json'), '')
        self.assertTrue(self.commit_row(run, self.detached)['detached_only'])
        self.assertFalse(self.commit_row(run, self.ahead)['detached_only'])
        # No branch names the detached cherry-pick; none was created or moved for it.
        self.assertEqual([line for line in self.git(self.detached, 'branch', '--contains', 'HEAD').splitlines() if not line.startswith('* (')], [])
        # Identical lock bytes everywhere the result was adopted.
        expected = (self.project / '.mask.lock.json').read_bytes()
        for root in (self.feature, self.detached, self.same, self.ahead):
            self.assertEqual((root / '.mask.lock.json').read_bytes(), expected, root)
            self.assertTrue((root / '.agents/skills/alpha').exists(), root)
        self.assertEqual(self.locked(self.project), candidate)
        # The fallback clone is upgraded on its own and left uncommitted; the unrelated repository commits on its own.
        self.assertEqual(self.head(self.dirty), heads[self.dirty])
        self.assertEqual(self.locked(self.dirty), candidate)
        self.assertEqual(self.commit_row(run, self.dirty)['status'], 'uncommitted')
        self.assertEqual(self.head(self.unrelated, 'HEAD^'), heads[self.unrelated])
        self.assertEqual(self.commit_row(run, self.unrelated)['status'], 'committed')
        # Exactly one upgrade commit object per repository: every propagated copy is the canonical patch.
        again = self.machine('upgrade', '--all', '--commit', '--offline')
        self.assertTrue(again['ok'], again)
        self.assertFalse(any(row['status'] == 'committed' for row in again['data']['commits']), again['data']['commits'])

    def test_failed_canonical_commit_propagates_nothing(self):
        hook = Path(self.git(self.project, 'rev-parse', '--git-path', 'hooks/pre-commit'))
        hook = hook if hook.is_absolute() else self.project / hook
        hook.parent.mkdir(parents=True, exist_ok=True)
        hook.write_text('#!/bin/sh\nexit 1\n')
        hook.chmod(0o755)
        (self.source / 'skills/alpha/support.txt').write_text('new payload\n', encoding='utf-8', newline='\n')
        candidate = self.publish()
        heads = {root: self.head(root) for root in (self.project, self.feature, self.same, self.ahead, self.detached)}
        run = self.machine('upgrade', '--all', '--commit')
        self.assertEqual(run['error']['code'], 'upgrade.incomplete', run)
        self.assertEqual(self.commit_row(run, self.project)['status'], 'failed')
        for root in (self.feature, self.same, self.ahead, self.detached):
            row = self.commit_row(run, root)
            self.assertEqual((row['status'], row['error']['code']), ('not_attempted', 'upgrade.canonical_commit_missing'), row)
        self.assertEqual({root: self.head(root) for root in heads}, heads)
        self.assertEqual(self.commit_row(run, self.unrelated)['status'], 'committed')
        # The applied upgrade is preserved everywhere, as for a single checkout.
        self.assertEqual(self.locked(self.same), candidate)

    def test_independent_restores_per_checkout_commits_and_requires_all(self):
        (self.source / 'skills/alpha/support.txt').write_text('new payload\n', encoding='utf-8', newline='\n')
        self.publish()
        run = self.raw('upgrade', '--independent', '--json')
        self.assertEqual(run.returncode, 2)
        self.assertEqual(json.loads(run.stdout)['error']['code'], 'invocation.invalid')
        result = self.machine('upgrade', '--all', '--independent', '--commit')
        self.assertNotIn('groups', result['data'])
        statuses = {row['root']: row['status'] for row in result['data']['commits']}
        self.assertEqual(statuses[str(self.feature)], 'committed')
        self.assertEqual(statuses[str(self.same)], 'committed')
        self.assertNotEqual(self.head(self.same), self.head(self.project))
        self.assertEqual(statuses[str(self.detached)], 'blocked')

    def test_without_commit_members_adopt_identical_controls_and_ambiguity_blocks(self):
        (self.source / 'skills/alpha/support.txt').write_text('new payload\n', encoding='utf-8', newline='\n')
        candidate = self.publish()
        result = self.machine('upgrade', '--all', cwd=self.base)
        self.assertTrue(result['ok'], result)
        [group] = result['data']['groups']
        self.assertEqual(group['reason'], 'default_branch_first_path')
        self.assertEqual(group['canonical'], str(self.ahead))  # 'clone ahead' sorts first among clean main checkouts.
        expected = (self.ahead / '.mask.lock.json').read_bytes()
        for root in (self.project, self.feature, self.detached, self.same):
            self.assertEqual((root / '.mask.lock.json').read_bytes(), expected, root)
        self.assertEqual(self.locked(self.dirty), candidate)
        self.assertNotIn('commits', result['data'])
        heads = {root: self.head(root) for root in (self.project, self.feature, self.same)}
        self.assertEqual(heads[self.project], self.base_head)


class AmbiguousGroup(PublicFixture):
    def test_two_feature_worktrees_without_default_branch_block_unless_invoked_inside(self):
        self.git(self.project, 'config', 'user.name', 'Fixture')
        self.git(self.project, 'config', 'user.email', 'fixture@example.invalid')
        (self.project / 'file').write_text('base\n')
        self.git(self.project, 'add', 'file')
        self.git(self.project, 'commit', '-q', '-m', 'initial')
        self.git(self.project, 'checkout', '-q', '-b', 'one')
        self.assertTrue(self.machine('install', 'alpha')['ok'])
        self.git(self.project, 'add', '.mask.json', '.mask.lock.json')
        self.git(self.project, 'commit', '-q', '-m', 'controls')
        self.git(self.project, 'branch', '-q', '-D', 'main')
        other = self.base / 'two'
        self.git(self.project, 'worktree', 'add', '-q', '-b', 'two', str(other))
        self.assertTrue(self.machine('register', '--project', other)['ok'])
        (self.source / 'skills/alpha/support.txt').write_text('new payload\n', encoding='utf-8', newline='\n')
        self.publish()
        outside = self.machine('upgrade', '--all', '--commit', cwd=self.base)
        self.assertEqual(outside['error']['code'], 'upgrade.incomplete', outside)
        self.assertEqual({row['error']['code'] for row in outside['data']['consumers'] if row['status'] == 'blocked'}, {'upgrade.group_ambiguous'})
        inside = self.machine('upgrade', '--all', '--commit', '--offline', cwd=other)
        self.assertTrue(inside['ok'], inside)
        self.assertEqual(inside['data']['groups'][0]['canonical'], str(other))
        self.assertEqual(self.git(self.project, 'rev-parse', 'HEAD'), self.git(other, 'rev-parse', 'HEAD'))


if __name__ == '__main__':
    unittest.main()
