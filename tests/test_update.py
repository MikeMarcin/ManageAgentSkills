"""Fetching, isolated update through the public CLI (RFC-MASK-0021 AC03; MASK-0103; retained-pack ACCEPTANCE.md U01-U09).

Two local bare repositories are ``file`` taps. Three consumers start through the public
``install`` task: the project selects agentskills/alpha, the personal scope selects
agentskills/beta and a second project selects second/gamma. Upstream pushes reach MASK only
through a fetch.

``git fetch`` processes are counted from Git's own trace2 event files, so no product code is
instrumented: each traced invocation points GIT_TRACE2_EVENT at a fresh directory, Git writes
one event file per process, and a process counts for a tap when its ``cmd_name`` is ``fetch``
and its argv names that tap's configured transport.
"""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

from tests.support import ENTRY, TAP, Fixture

READINESS = ENTRY.parent / 'docs/rfcs/assets/mask-corrective-ux-readiness/fixtures'
GENERATED, CONTEXT = READINESS / 'generated-package', READINESS / 'consumer/.mask'
SECOND = 'second'
ALPHA, BETA, GAMMA = TAP + '/alpha', TAP + '/beta', SECOND + '/gamma'
NO_FETCH = {TAP: 0, SECOND: 0}


class UpdateFixture(Fixture):
    """Two taps and three consumers, all created through the public CLI."""

    AUTHORING = {'test_u07_dev_link_consumer_is_skipped_unscoped_and_refused_when_scoped'}

    def setUp(self):
        super().setUp()
        traces = tempfile.TemporaryDirectory(prefix='mask-trace-')
        self.addCleanup(traces.cleanup)
        self.traces = Path(traces.name)
        self.author = self.base / 'Second'
        (self.author / 'skills/gamma').mkdir(parents=True)
        self.git(self.author, 'init', '-q', '-b', 'main')
        self.git(self.author, 'config', 'user.name', 'Fixture')
        self.git(self.author, 'config', 'user.email', 'fixture@example.invalid')
        (self.author / 'skills/gamma/SKILL.md').write_text('---\nname: gamma\ndescription: Fixture skill\n---\n\nFixture instructions.\n')
        self.git(self.author, 'add', 'skills')
        self.git(self.author, 'commit', '-q', '-m', 'gamma')
        self.second = self.base / 'upstream' / 'Second.git'
        self.git(self.base, 'init', '-q', '--bare', '-b', 'main', str(self.second))
        self.git(self.author, 'push', '-q', str(self.second), 'main')
        if self._testMethodName in self.AUTHORING:
            # Development links need the tap's approved authoring checkout, whose origin names the tap identity.
            self.git(self.source, 'remote', 'add', 'origin', str(self.upstream))
            self.call('tap', 'add', TAP, self.upstream, '--checkout', self.source)
        else:
            self.init()
        self.call('tap', 'add', SECOND, self.second)
        self.other = self.base / 'second project'
        self.other.mkdir()
        self.git(self.other, 'init', '-q', '-b', 'main')
        self.install(ALPHA)
        self.install(BETA, user=True)
        self.install(GAMMA, root=self.other)
        self.assert_store_links()

    def traced(self, *args, code=0):
        """One CLI invocation with a fresh trace2 directory: its result and the git fetch processes per tap."""
        trace = Path(tempfile.mkdtemp(dir=self.traces))
        result = self.call(*args, code=code, env={'GIT_TRACE2_EVENT': str(trace)})
        processes = {}
        for path in trace.iterdir():
            for line in path.read_text(encoding='utf-8').splitlines():
                event = json.loads(line)
                observed = processes.setdefault(event['sid'], {})
                if event['event'] == 'start':
                    observed['argv'] = event['argv']
                elif event['event'] == 'cmd_name':
                    observed['name'] = event['name']
        transports = {name: entry['transport'] for name, entry in json.loads((self.home / 'config.json').read_text(encoding='utf-8'))['sources'].items()}
        return result, {name: sum(item.get('name') == 'fetch' and transport in item.get('argv', ()) for item in processes.values())
                        for name, transport in transports.items()}

    def assert_store_links(self):
        """U09: every owned link recorded in state and present on disk resolves under MASK_HOME/store/v1; only an explicit dev-link differs."""
        state = json.loads((self.home / 'state.json').read_text(encoding='utf-8'))
        records = dict(state['projects'], **({state['user']['root']: state['user']} if state.get('user') else {}))
        store = (self.home / 'store' / 'v1').resolve()
        for root, record in records.items():
            for relative, link in record['links'].items():
                leaf = Path(root) / relative
                self.assertEqual(os.readlink(leaf), link['link_text'], leaf)
                if 'dev' not in link:
                    self.assertTrue(leaf.resolve().is_relative_to(store), (leaf, link['link_text']))
                    self.assertTrue((leaf / 'SKILL.md').is_file(), leaf)
            for parent in ('.claude/skills', '.agents/skills'):
                directory = Path(root) / parent
                for leaf in directory.iterdir() if directory.is_dir() else ():
                    self.assertIn(leaf.relative_to(root).as_posix(), record['links'], 'no unowned entry beside the owned links')

    def lock_path(self, root):
        return self.home / 'user.lock.json' if root == self.personal else root / '.mask.lock.json'

    def locked(self, root, coordinate):
        return next(row for row in json.loads(self.lock_path(root).read_text(encoding='utf-8'))['packages'] if row['source'] + '/' + row['id'] == coordinate)

    def rows(self, result):
        return {row['root']: row for row in result['data']['consumers']}

    def statuses(self, result):
        rows = self.rows(result)
        return [rows[str(root)]['status'] for root in (self.project, self.personal, self.other)]

    def move_alpha_and_beta(self, text):
        for identifier in ('alpha', 'beta'):
            (self.source / 'skills' / identifier / 'notes').write_text(text)
        return self.publish(text)

    def move_gamma(self, text='second tap change'):
        (self.author / 'skills/gamma/notes').write_text(text)
        self.git(self.author, 'add', '-A', 'skills')
        self.git(self.author, 'commit', '-q', '-m', text)
        self.git(self.author, 'push', '-q', str(self.second), 'HEAD:main')
        return self.git(self.author, 'rev-parse', 'HEAD')

    def select_tag(self, tag):
        declaration = json.loads((self.project / '.mask.json').read_text(encoding='utf-8'))
        declaration['skills'][0]['version'] = {'ref': 'refs/tags/' + tag}
        (self.project / '.mask.json').write_text(json.dumps(declaration))

    def crash(self, args, label='intent'):
        script = ("import os,sys;sys.path.insert(0,sys.argv[1]);import mask,mask_fs;"
                  "mask_fs.checkpoint=lambda label: os._exit(99) if label==sys.argv[2] else None;raise SystemExit(__import__('tests.engine_cli', fromlist=['main']).main(sys.argv[3:]))")
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), label, *map(str, args), '--json'],
                             capture_output=True, encoding='utf-8', cwd=self.project, env=self.environment())
        self.assertEqual(run.returncode, 99, run.stdout + run.stderr)


class FetchingUpdate(UpdateFixture):
    def test_u01_push_then_update_fetches_each_tap_once_and_isolates_the_other_tap(self):
        old = {ALPHA: self.locked(self.project, ALPHA), BETA: self.locked(self.personal, BETA)}
        untouched = self.lock_path(self.other).read_bytes()
        links = {root: os.readlink(root / '.agents/skills' / name) for root, name in ((self.project, 'alpha'), (self.personal, 'beta'), (self.other, 'gamma'))}
        head = self.move_alpha_and_beta('tap A moves')
        result, fetched = self.traced('upgrade')
        self.assertEqual(fetched, {TAP: 1, SECOND: 1})
        self.assertEqual((result['transaction'], result['changed'], result['data']['network']), ('committed', True, 'fetch'))
        self.assertEqual(self.statuses(result), ['updated', 'updated', 'unchanged'])
        rows = self.rows(result)
        for root, coordinate in ((self.project, ALPHA), (self.personal, BETA)):
            after = self.locked(root, coordinate)
            self.assertEqual(after['commit'], head)
            self.assertEqual(rows[str(root)]['changes'], [dict(coordinate=coordinate, before_commit=old[coordinate]['commit'], after_commit=head,
                                                              before_digest=old[coordinate]['payload_digest'], after_digest=after['payload_digest'],
                                                              selector=old[coordinate]['selector'])])
            self.assertNotEqual(os.readlink(root / '.agents/skills' / after['id']), links[root])
        self.assertEqual((rows[str(self.other)]['changes'], rows[str(self.other)]['error']), ([], None))
        self.assertEqual(self.lock_path(self.other).read_bytes(), untouched)
        self.assertEqual(os.readlink(self.other / '.agents/skills/gamma'), links[self.other])
        fetches = result['data']['fetches']
        self.assertEqual([fetches[TAP][key] for key in ('attempted', 'ok', 'after', 'remote_refs_changed', 'error')], [True, True, head, True, None])
        self.assertEqual([fetches[SECOND][key] for key in ('attempted', 'ok', 'remote_refs_changed', 'error')], [True, True, False, None])
        self.assert_store_links()
        again, fetched = self.traced('upgrade')
        self.assertEqual(fetched, {TAP: 1, SECOND: 1})
        self.assertFalse(again['changed'])
        self.assertEqual(self.statuses(again), ['unchanged'] * 3)

    def test_u01_one_journal_activates_every_updated_consumer(self):
        head = self.move_alpha_and_beta('journaled')
        self.crash(['upgrade'])
        pending = json.loads((self.home / 'pending.json').read_text(encoding='utf-8'))
        updated = {str(self.project), str(self.personal)}
        self.assertEqual(pending['operation'], 'upgrade')
        self.assertEqual(set(pending['selected']), updated | {str(self.other)})
        self.assertEqual({(entry['root'], entry['role']) for entry in pending['files']}, {(str(self.project), 'project_lock'), (str(self.personal), 'user_lock')})
        self.assertEqual({entry['root'] for entry in pending['links']}, updated)
        refused, fetched = self.traced('upgrade', code=8)
        self.assertEqual((refused['error']['code'], fetched), ('recovery.required', NO_FETCH))
        self.call('recover', '--complete')
        self.assertEqual([self.locked(self.project, ALPHA)['commit'], self.locked(self.personal, BETA)['commit']], [head, head])
        self.assert_store_links()
        self.assertEqual(self.statuses(self.call('upgrade')), ['unchanged'] * 3)

    def test_u02_unreachable_tap_blocks_only_its_consumers(self):
        untouched = self.lock_path(self.other).read_bytes()
        link = os.readlink(self.other / '.agents/skills/gamma')
        head = self.move_alpha_and_beta('tap A moves while tap B is gone')
        self.second.rename(self.second.with_name('Second moved away.git'))
        result, fetched = self.traced('upgrade', code=4)
        self.assertEqual((result['error']['code'], result['error']['details']['blocked']), ('upgrade.incomplete', [str(self.other)]))
        self.assertEqual((result['transaction'], result['changed']), ('committed', True))
        self.assertEqual(fetched[TAP], 1)
        self.assertLessEqual(fetched[SECOND], 1)
        self.assertEqual(self.statuses(result), ['updated', 'updated', 'blocked'])
        self.assertEqual(self.rows(result)[str(self.other)]['error']['code'], 'git.failed')
        fetches = result['data']['fetches']
        self.assertEqual((fetches[TAP]['ok'], fetches[SECOND]['attempted'], fetches[SECOND]['ok'], fetches[SECOND]['error']['code']), (True, True, False, 'git.failed'))
        self.assertEqual([self.locked(self.project, ALPHA)['commit'], self.locked(self.personal, BETA)['commit']], [head, head])
        self.assertEqual(self.lock_path(self.other).read_bytes(), untouched)
        self.assertEqual(os.readlink(self.other / '.agents/skills/gamma'), link)
        self.assert_store_links()
        human = subprocess.run([sys.executable, '-B', str(ENTRY), 'upgrade', '--all', '--no-update'], capture_output=True, encoding='utf-8', cwd=self.project, env=self.environment())
        self.assertEqual((human.returncode, human.stdout), (4, ''), human.stderr)
        for text in ('code: upgrade.incomplete', str(self.other), 'tap second: fetch failed (git.failed)', 'state: no deployment changes were applied'):
            self.assertIn(text, human.stderr)
        self.assertNotIn('tap agentskills: fetched, nothing new', human.stderr)

    def test_u03_scoped_update_on_an_unreachable_tap_is_a_plain_refusal(self):
        self.move_alpha_and_beta('tap A moves too')
        self.second.rename(self.second.with_name('Second moved away.git'))
        before = self.snapshot()
        refused, fetched = self.traced('upgrade', '--project', self.other, code=5)
        self.assertEqual((refused['error']['code'], refused['transaction'], refused['changed']), ('git.failed', 'not_started', False))
        self.assertEqual((refused['data']['fetches'][SECOND]['ok'], list(refused['data']['fetches']), fetched[TAP]), (False, [SECOND], 0))
        self.assertEqual(before, self.snapshot())
        self.assert_store_links()

    def test_u04_dry_run_and_offline_never_fetch_and_block_a_cold_selector(self):
        head = self.move_alpha_and_beta('tagged candidate')
        self.git(self.source, 'tag', 'v2')
        self.git(self.source, 'push', '-q', str(self.upstream), 'refs/tags/v2')
        self.select_tag('v2')
        before = self.snapshot()
        preview, fetched = self.traced('upgrade', '--dry-run')
        self.assertEqual(fetched, NO_FETCH)
        project = self.rows(preview)[str(self.project)]
        self.assertEqual((project['status'], project['requires_fetch'], project['error']['code']), ('blocked', True, 'lock.resolution_required'))
        self.assertEqual(self.statuses(preview)[1:], ['unchanged', 'unchanged'], 'without a fetch the cache has not moved')
        self.assertEqual({row['attempted'] for row in preview['data']['fetches'].values()}, {False})
        self.assertEqual(before, self.snapshot())
        offline, fetched = self.traced('upgrade', '--offline', code=4)
        self.assertEqual((offline['error']['code'], offline['error']['details']['blocked'], fetched), ('upgrade.incomplete', [str(self.project)], NO_FETCH))
        self.assertEqual(before, self.snapshot())
        scoped, fetched = self.traced('upgrade', '--project', self.project, '--offline', code=4)
        self.assertEqual((scoped['error']['code'], scoped['error']['details']['blocked'], fetched), ('upgrade.incomplete', [str(self.project)], NO_FETCH))
        self.assertEqual(before, self.snapshot())
        applied, fetched = self.traced('upgrade')
        self.assertEqual(fetched, {TAP: 1, SECOND: 1})
        self.assertEqual(self.statuses(applied), ['updated', 'updated', 'unchanged'])
        self.assertEqual([(row['selector'], row['commit']) for row in (self.locked(self.project, ALPHA), self.locked(self.personal, BETA))],
                         [({'ref': 'refs/tags/v2'}, head), ({'ref': 'refs/heads/main'}, head)])
        self.assert_store_links()

    def test_u04_guarded_rerun_never_fetches_and_binds_the_reviewed_candidate(self):
        self.move_alpha_and_beta('first candidate')
        self.call('source', 'fetch')
        before = self.snapshot()
        first, fetched = self.traced('upgrade', '--dry-run')
        self.assertEqual((fetched, self.statuses(first)), (NO_FETCH, ['updated', 'updated', 'unchanged']))
        self.assertEqual(before, self.snapshot())
        reviewed_head = self.move_alpha_and_beta('second candidate')
        self.call('source', 'fetch')
        before = self.snapshot()
        stale, fetched = self.traced('upgrade', '--expect-plan-hash', first['data']['plan_hash'], code=4)
        self.assertEqual((stale['error']['code'], fetched), ('plan.stale', NO_FETCH))
        self.assertEqual(before, self.snapshot())
        reviewed, fetched = self.traced('upgrade', '--dry-run')
        self.assertEqual(self.rows(reviewed)[str(self.project)]['changes'][0]['after_commit'], reviewed_head)
        self.move_alpha_and_beta('unreviewed upstream candidate')
        applied, fetched = self.traced('upgrade', '--expect-plan-hash', reviewed['data']['plan_hash'])
        self.assertEqual((fetched, applied['transaction'], applied['data']['plan_hash']), (NO_FETCH, 'committed', reviewed['data']['plan_hash']))
        self.assertEqual([self.locked(self.project, ALPHA)['commit'], self.locked(self.personal, BETA)['commit']], [reviewed_head, reviewed_head])
        self.assert_store_links()

    def test_u05_moved_tag_refuses_the_whole_invocation_without_allow_ref_rebind(self):
        original = self.git(self.source, 'rev-parse', 'HEAD')
        self.git(self.source, 'tag', '-a', 'release', '-m', 'release')
        self.git(self.source, 'push', '-q', str(self.upstream), 'refs/tags/release')
        self.select_tag('release')
        pinned, fetched = self.traced('upgrade')  # The fetch itself acquires the annotated tag; no source inspect is needed.
        self.assertEqual(fetched, {TAP: 1, SECOND: 1})
        self.assertEqual([self.locked(self.project, ALPHA)[key] for key in ('selector', 'commit')], [{'ref': 'refs/tags/release'}, original])
        moved = self.move_alpha_and_beta('the tag moves')
        self.git(self.source, 'tag', '-f', '-a', 'release', '-m', 'moved release')
        self.git(self.source, 'push', '-q', '--force', str(self.upstream), 'refs/tags/release')
        locks = {root: self.lock_path(root).read_bytes() for root in (self.project, self.personal, self.other)}
        refused, fetched = self.traced('upgrade', code=4)
        self.assertEqual(fetched[TAP], 1)
        self.assertEqual((refused['error']['code'], refused['error']['details']['skill'], refused['transaction']), ('lock.ref_rebound', ALPHA, 'not_started'))
        self.assertEqual({root: self.lock_path(root).read_bytes() for root in locks}, locks, 'a rebound selector refuses every consumer, not only its own')
        rebound, fetched = self.traced('upgrade', '--allow-ref-rebind')
        self.assertEqual(fetched[TAP], 1)
        self.assertEqual(self.rows(rebound)[str(self.project)]['changes'][0]['before_commit'], original)
        self.assertEqual([self.locked(self.project, ALPHA)['commit'], self.locked(self.personal, BETA)['commit']], [moved, moved])
        self.assert_store_links()

    def test_u06_empty_registry_exits_zero_without_fetch(self):
        empty = self.base / 'empty machine'
        self.call('tap', 'add', TAP, self.upstream, '--home', empty)
        before = self.snapshot()
        result, fetched = self.traced('upgrade', '--home', empty)
        self.assertEqual(fetched, NO_FETCH)
        self.assertIn('project.empty_registry', [warning['code'] for warning in result['warnings']])
        self.assertEqual((result['changed'], result['data']['consumers'], result['data']['fetches']), (False, [], {}))
        self.assertEqual(before, self.snapshot())
        self.assertFalse((empty / 'sources').exists())
        self.assertEqual(self.call('upgrade', '--home', empty, '--skill', ALPHA, code=2)['error']['code'], 'invocation.invalid')

    def test_u07_dev_link_consumer_is_skipped_unscoped_and_refused_when_scoped(self):
        self.call('source', 'dev-link', ALPHA, '--project', self.project, '--authoring-root', self.source)
        link = os.readlink(self.project / '.agents/skills/alpha')
        head = self.move_alpha_and_beta('tap A moves under a development link')
        result, fetched = self.traced('upgrade')
        self.assertEqual(fetched, {TAP: 1, SECOND: 1})
        self.assertEqual(self.statuses(result), ['skipped', 'updated', 'unchanged'])
        self.assertEqual([warning['root'] for warning in result['warnings'] if warning['code'] == 'dev_link.active'], [str(self.project)])
        self.assertEqual(os.readlink(self.project / '.agents/skills/alpha'), link)
        self.assertEqual(self.locked(self.personal, BETA)['commit'], head)
        self.assertEqual(self.statuses(self.call('upgrade', '--all')), ['skipped', 'unchanged', 'unchanged'])
        refused, fetched = self.traced('upgrade', '--project', self.project, code=4)
        self.assertEqual((refused['error']['code'], fetched), ('dev_link.active', NO_FETCH))
        self.assert_store_links()

    def test_u08_source_fetch_without_a_name_fetches_every_tap_and_deploys_nothing(self):
        head, second = self.move_alpha_and_beta('fetched only'), self.move_gamma()
        def consumers():
            return [self.snapshot(root) for root in (self.project, self.personal, self.other)] + [(self.home / name).read_bytes() for name in ('state.json', 'user.json', 'user.lock.json', 'config.json')]
        before = consumers()
        preview, fetched = self.traced('source', 'fetch', '--dry-run')
        self.assertEqual((fetched, {row['attempted'] for row in preview['data']['fetches'].values()}), (NO_FETCH, {False}))
        result, fetched = self.traced('source', 'fetch')
        self.assertEqual(fetched, {TAP: 1, SECOND: 1})
        self.assertEqual([(result['data']['fetches'][name]['ok'], result['data']['fetches'][name]['after']) for name in (TAP, SECOND)], [(True, head), (True, second)])
        self.assertEqual((result['changed'], result['actions']), (False, []))
        self.assertEqual(consumers(), before)
        self.assertEqual(self.rows(self.call('upgrade', '--dry-run'))[str(self.other)]['changes'][0]['after_commit'], second, 'a dry run reviews the fetched cache')
        self.second.rename(self.second.with_name('Second moved away.git'))
        later = self.move_alpha_and_beta('tap A is still fetched')
        refused, fetched = self.traced('source', 'fetch', code=5)
        self.assertEqual((refused['error']['code'], refused['error']['details']['failed']), ('git.failed', [SECOND]))
        self.assertEqual((fetched[TAP], refused['data']['fetches'][TAP]['ok'], refused['data']['fetches'][TAP]['after']), (1, True, later))
        self.assertEqual(consumers(), before)
        self.assert_store_links()
        empty = self.base / 'empty catalog'
        self.call('init', '--home', empty)
        self.assertEqual(self.call('source', 'fetch', '--home', empty)['data']['fetches'], {})

    def test_skill_scope_fetches_only_the_taps_of_the_named_bindings(self):
        self.move_alpha_and_beta('tap A moves')
        second = self.move_gamma()
        locks = {root: self.lock_path(root).read_bytes() for root in (self.project, self.personal)}
        result, fetched = self.traced('upgrade', '--skill', GAMMA)
        self.assertEqual(fetched, {TAP: 0, SECOND: 1})
        self.assertEqual((list(self.rows(result)), list(result['data']['fetches'])), ([str(self.other)], [SECOND]))
        self.assertEqual(self.locked(self.other, GAMMA)['commit'], second)
        self.assertEqual({root: self.lock_path(root).read_bytes() for root in locks}, locks)
        for skills in ([GAMMA, GAMMA], [TAP + '/absent']):
            refused, fetched = self.traced('upgrade', *[operand for skill in skills for operand in ('--skill', skill)], code=2)
            self.assertEqual((refused['error']['code'], fetched), ('invocation.invalid', NO_FETCH))
        self.assert_store_links()


class UpdateSafetyOnTaps(UpdateFixture):
    """Tap-model guarantees the retired shared-checkout update tests (tests/test_git_update.py) protected."""

    def consumer_controls(self):
        return [self.snapshot(root) for root in (self.project, self.personal, self.other)] + [(self.home / name).read_bytes() for name in ('state.json', 'user.json', 'user.lock.json')]

    def test_candidate_without_a_declared_skill_refuses_without_writing(self):
        # Product check: in a fetching run, a resolution error other than lock.resolution_required (mask_resolve.resolve_binding
        # skill.unknown) refuses the whole invocation in mask_update.dispatch before any plan or journal.
        self.git(self.source, 'rm', '-r', '-q', 'skills/beta')
        self.publish('beta removed upstream')
        before = self.consumer_controls()
        refused, fetched = self.traced('upgrade', code=4)
        self.assertEqual((refused['error']['code'], refused['error']['details']['skill'], refused['transaction'], fetched[TAP]), ('skill.unknown', BETA, 'not_started', 1))
        self.assertEqual(self.consumer_controls(), before)
        self.assertFalse((self.home / 'pending.json').exists())
        self.assert_store_links()

    def test_candidate_package_with_colliding_or_linked_entries_refuses(self):
        # Product check: mask_packages.validate (case-folded component collisions and the regular-blob rule) refuses the fetched
        # candidate during cache resolution, before anything is written.
        head = self.git(self.source, 'rev-parse', 'HEAD')
        blob = self.git(self.source, 'rev-parse', 'HEAD:skills/alpha/SKILL.md')
        before = self.consumer_controls()
        for entries, code in (((('100644', 'Docs/a.txt'), ('100644', 'docs/b.txt')), 'skill.path_ambiguous'), ((('120000', 'linked'),), 'skill.entry_unsupported')):
            self.git(self.source, 'read-tree', head)
            for mode, name in entries:
                self.git(self.source, 'update-index', '--add', '--cacheinfo', f'{mode},{blob},skills/alpha/{name}')
            candidate = self.git(self.source, 'commit-tree', self.git(self.source, 'write-tree'), '-p', head, '-m', 'invalid candidate')
            self.git(self.source, 'push', '-q', '--force', str(self.upstream), candidate + ':refs/heads/main')
            refused, fetched = self.traced('upgrade', code=4)
            self.assertEqual((refused['error']['code'], fetched[TAP]), (code, 1))
            self.assertEqual(self.consumer_controls(), before)
        self.git(self.source, 'read-tree', head)
        self.assert_store_links()

    def test_git_hooks_are_suppressed_during_the_update_fetch(self):
        # Product check: mask_core.git's core.hooksPath and hook.<event>.enabled overrides on the tap-cache fetch and its ref
        # updates (mask_sources.fetch and freeze).
        cache = Path(json.loads((self.home / 'config.json').read_text(encoding='utf-8'))['sources'][TAP]['cache'])
        marker = self.base / 'hook-ran'
        hook = cache / 'hooks' / 'reference-transaction'
        hook.parent.mkdir(exist_ok=True)
        hook.write_text('#!/bin/sh\n' + shlex.join(['touch', marker.as_posix()]) + '\n', newline='\n')
        hook.chmod(0o755)
        self.git(cache, 'update-ref', 'refs/fixture/probe', 'refs/mask/selected')
        self.assertTrue(marker.exists(), 'positive control: plain Git runs this cache hook for a ref update')
        self.git(cache, 'update-ref', '-d', 'refs/fixture/probe')
        marker.unlink()
        head = self.move_alpha_and_beta('hooks stay suppressed')
        result, fetched = self.traced('upgrade')
        self.assertEqual((fetched[TAP], result['data']['fetches'][TAP]['after'], self.locked(self.project, ALPHA)['commit']), (1, head, head))
        self.assertFalse(marker.exists())
        self.assert_store_links()

    def test_late_apply_failure_rolls_back_to_exact_prior_bytes(self):
        # Product check: mask_fs.execute restores the before side of the one update journal after links and a lock were written.
        before = self.consumer_controls()
        self.move_alpha_and_beta('rolled back')
        script = ("import sys\nsys.path.insert(0, sys.argv[1])\nimport mask, mask_fs\n"
                  "def fail(label):\n    if label == 'lock':\n        raise OSError('injected late failure')\n"
                  "mask_fs.checkpoint = fail\nraise SystemExit(__import__('tests.engine_cli', fromlist=['main']).main(sys.argv[2:]))\n")
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), 'upgrade', '--json'],
                             capture_output=True, encoding='utf-8', cwd=self.project, env=self.environment())
        data = json.loads(run.stdout)
        self.assertEqual((run.returncode, data['error']['code'], data['transaction']), (5, 'filesystem.failed', 'rolled_back'), run.stdout + run.stderr)
        self.assertEqual(self.consumer_controls(), before)
        self.assertFalse((self.home / 'pending.json').exists())
        self.assert_store_links()
        self.assertEqual(self.statuses(self.call('upgrade')), ['updated', 'updated', 'unchanged'])

    def test_setup_review_preserves_all_consumers_even_when_another_tap_is_blocked(self):
        package = self.source / 'skills/implement-rfc'
        shutil.copytree(GENERATED.with_name('static-package'), package)
        self.publish('static package')
        self.call('source', 'fetch', TAP)
        shutil.copytree(CONTEXT, self.project / '.mask')
        self.call('install', TAP + '/implement-rfc', '--project', self.project)
        shutil.rmtree(package)
        shutil.copytree(GENERATED, package)
        self.publish('candidate requires generated roles')
        self.second.rename(self.second.with_name('Second moved away.git'))
        before = self.consumer_controls()
        result = self.call('upgrade', code=4)
        self.assertEqual(result['error']['code'], 'confirmation.required')
        self.assertFalse(result['changed'])
        self.assertEqual(before, self.consumer_controls())
        self.assertEqual(result['data']['fetches'][SECOND]['ok'], False)
        self.assertEqual(self.rows(result)[str(self.other)]['status'], 'blocked')
        self.assert_store_links()

    def test_unavailable_consumer_refuses_before_any_fetch(self):
        # Product check: mask_update.dispatch checks every selected registered root (mask_core.registered_root) before the fetch phase.
        self.move_alpha_and_beta('never fetched')
        moved = self.other.rename(self.base / 'moved second project')
        try:
            refused, fetched = self.traced('upgrade', code=4)
        finally:
            moved.rename(self.other)
        self.assertEqual((refused['error']['code'], refused['error']['details']['root'], fetched), ('project.unavailable', str(self.other), NO_FETCH))
        self.assertNotIn('fetches', refused['data'])
        self.assert_store_links()


if __name__ == '__main__':
    import unittest
    unittest.main()
