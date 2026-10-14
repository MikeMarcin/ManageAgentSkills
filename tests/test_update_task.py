"""One-command safe updates through the public CLI (RFC-MASK-0018 AC04-AC06, MASK-0087; cases C16-C18 and C20), on taps (RFC-MASK-0021, MASK-0103).

Every check runs the program as a subprocess against a local bare upstream approved as a
tap and a consumer created through the public ``install`` command; upstream changes reach
MASK only through a fetch. Nothing here injects ``--json`` outside the ``machine`` helper,
copies a hash on behalf of the human journey, or prepares the behavior under test.
"""
import json
import os
from pathlib import Path
import unittest

from tests.public_support import EngineFixture
from tests.support import TAP


class TapUpdateFixture(EngineFixture):
    """The fixture tap, one consumer installed through the public task, and upstream changes pushed with ``publish``."""

    def setUp(self):
        super().setUp()
        installed = self.human('install', 'alpha')
        self.assertEqual(installed.returncode, 0, installed.stderr)
        self.cache = Path(json.loads((self.home / 'config.json').read_text(encoding='utf-8'))['sources'][TAP]['cache'])

    def push_upstream(self, text='Updated instructions.'):
        path = self.source / 'skills/alpha/SKILL.md'
        path.write_text(path.read_text(encoding='utf-8') + '\n' + text + '\n', encoding='utf-8')
        return self.publish('upstream change')

    def locked(self):
        return json.loads((self.project / '.mask.lock.json').read_text(encoding='utf-8'))['packages'][0]['commit']

    def cached(self):
        """The tap cache's refs and recorded advertisement, which only a fetch changes."""
        return self.git(self.cache, 'for-each-ref', '--format=%(refname) %(objectname)'), (self.cache / 'mask-refs.json').read_bytes()


class NormalUpdate(TapUpdateFixture):
    """C16: fetch, resolution, disclosure, activation and verification in one plain invocation."""

    def test_plain_update_fetches_and_activates_in_one_invocation(self):
        candidate = self.push_upstream()
        run = self.human('upgrade')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertFalse(self.parses_as_result_envelope(run.stdout))
        self.assertNotIn('sha256:', run.stdout)
        self.assertIn(f'tap {TAP}: fetched new commits', run.stdout)
        self.assertIn('Upgraded 1 skill in 1 project.', run.stdout)
        self.assertNotIn(str(self.project), run.stdout)
        self.assertIn(f'  {TAP}/alpha -> {candidate[:7]} (1 location)', run.stdout)
        self.assertIn(f'-> {candidate[:7]}', run.stdout)
        self.assertNotIn('applied:', run.stdout)
        self.assertEqual(self.locked(), candidate)
        self.assertIn('Updated instructions.', (self.project / '.claude/skills/alpha/SKILL.md').read_text(encoding='utf-8'))
        self.assertFalse((self.home / 'pending.json').exists())
        again = self.human('upgrade')
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn('Already up to date (1 project).', again.stdout)
        self.assertNotIn(str(self.project), again.stdout)

    def test_the_retired_program_spelling_is_gone(self):
        # update against a real program clone is proven in tests.test_readme_journeys; this checkout is never fetched by a test.
        gone = self.raw('self', 'update')
        self.assertEqual((gone.returncode, gone.stdout), (2, ''), gone.stderr)
        preview = self.human('update', '--dry-run')
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertIn(f'tap {TAP}: used the cached copy (not fetched)', preview.stdout)

    def test_json_reports_the_same_effects_as_one_document(self):
        before = self.locked()
        candidate = self.push_upstream()
        done = self.machine('upgrade')
        self.assertEqual((done['changed'], done['transaction'], done['data']['network']), (True, 'committed', 'fetch'))
        self.assertEqual((done['data']['fetches'][TAP]['ok'], done['data']['fetches'][TAP]['after']), (True, candidate))
        [row] = done['data']['consumers']
        self.assertEqual((row['root'], row['status']), (str(self.project), 'updated'))
        self.assertEqual([(change['coordinate'], change['before_commit'], change['after_commit']) for change in row['changes']], [(TAP + '/alpha', before, candidate)])
        self.assertIn('link.create', {action['kind'] for action in done['actions']})
        self.assertEqual(self.locked(), candidate)


class PreviewAndGuard(TapUpdateFixture):
    """C17/C18: dry run, --offline and --expect-plan-hash never fetch; the guard binds the reviewed candidate."""

    def test_dry_run_and_offline_do_not_fetch(self):
        old, cache, lock = self.locked(), self.cached(), (self.project / '.mask.lock.json').read_bytes()
        self.push_upstream()
        preview = self.machine('upgrade', '--dry-run')
        self.assertEqual((preview['data']['fetches'][TAP]['attempted'], preview['data']['network']), (False, 'none'))
        self.assertFalse(preview['would_change'])  # Nothing new is known until an explicit or normal fetch.
        self.assertEqual(preview['data']['consumers'][0]['status'], 'unchanged')
        self.assertEqual((self.cached(), (self.project / '.mask.lock.json').read_bytes()), (cache, lock))
        offline = self.human('upgrade', '--offline')
        self.assertEqual(offline.returncode, 0, offline.stderr)
        self.assertIn(f'tap {TAP}: used the cached copy (not fetched)', offline.stdout)
        self.assertEqual((self.cached(), (self.project / '.mask.lock.json').read_bytes(), self.locked()), (cache, lock, old))

    def test_guard_applies_the_previewed_candidate_even_after_the_remote_moves(self):
        reviewed = self.push_upstream()
        self.assertTrue(self.machine('source', 'fetch')['ok'])
        preview = self.machine('upgrade', '--dry-run')
        self.assertTrue(preview['would_change'])
        newer = self.push_upstream('Later revision')
        done = self.machine('upgrade', '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertTrue(done['changed'])
        self.assertFalse(done['data']['fetches'][TAP]['attempted'])
        self.assertEqual(self.locked(), reviewed)
        self.assertNotEqual(self.locked(), newer)
        self.assertTrue(self.machine('source', 'fetch')['ok'])
        stale = self.machine('upgrade', '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertEqual(stale['error']['code'], 'plan.stale')
        self.assertEqual(self.locked(), reviewed)


# C19 (ExpandedScope, TerminalExpandedScope) is retired with the shared-checkout scope.expand consent (contracts/CLI.md, Update semantics).


class RecoveryAndBusy(TapUpdateFixture):
    """C20: pending recovery and a busy writer keep their existing exits; nothing is forced or fetched."""

    def test_pending_journal_refuses_before_any_fetch(self):
        cache = self.cached()
        self.push_upstream()
        pending = self.home / 'pending.json'
        pending.write_text('{"schema_version": 3}\n', encoding='utf-8')
        run = self.human('upgrade')
        self.assertEqual(run.returncode, 8, run.stderr)
        self.assertIn('recovery.required', run.stderr)
        self.assertEqual(pending.read_text(encoding='utf-8'), '{"schema_version": 3}\n')
        self.assertEqual(self.cached(), cache)

    def test_busy_writer_is_reported_not_bypassed(self):
        old, cache = self.locked(), self.cached()
        self.push_upstream()
        with (self.home / 'operation.lock').open('a+b') as handle:
            if os.name == 'nt':
                import msvcrt
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                run = self.human('upgrade')
            finally:
                if os.name == 'nt':
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        self.assertEqual(run.returncode, 6, run.stderr)
        self.assertIn('lock.busy', run.stderr)
        self.assertEqual((self.locked(), self.cached()), (old, cache))


if __name__ == '__main__':
    unittest.main()
