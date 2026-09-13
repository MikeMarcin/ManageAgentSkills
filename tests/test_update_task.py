"""One-command safe updates through the public CLI (RFC-MASK-0018 AC04-AC06, MASK-0087; cases C16-C20).

Every check runs the program as a subprocess against a temporary source clone,
a local bare remote and legacy consumers created through the public ``install``
command. Nothing here injects ``--json`` outside the ``machine`` helper, copies
a hash on behalf of the human journey, or prepares the behavior under test.
"""
import json
import os
import select
import subprocess
import sys
import time
import unittest

from tests.public_support import ENTRY, PublicFixture


class SharedSourceFixture(PublicFixture):
    """A source tracking a local bare remote, one upstream author clone and one legacy consumer.

    Legacy live-checkout starting state until MASK-0101 retires the shared-checkout update.
    """

    bootstrap = PublicFixture.legacy_bootstrap

    def setUp(self):
        super().setUp()
        self.remote = self.base / 'AgentSkills.git'
        self.git(self.base, 'init', '--bare', str(self.remote))
        self.git(self.source, 'remote', 'add', 'origin', str(self.remote))
        self.git(self.source, 'push', '-u', 'origin', 'main')
        self.author = self.base / 'author'
        self.git(self.base, 'clone', '--branch', 'main', str(self.remote), str(self.author))
        self.git(self.author, 'config', 'user.name', 'Fixture')
        self.git(self.author, 'config', 'user.email', 'fixture@example.invalid')
        installed = self.human('install', 'alpha')
        self.assertEqual(installed.returncode, 0, installed.stderr)

    def push_upstream(self, text='Updated instructions.'):
        # Named apart from PublicFixture.upstream, the tap's bare repository path.
        path = self.author / 'skills/alpha/SKILL.md'
        path.write_text(path.read_text(encoding='utf-8') + '\n' + text + '\n', encoding='utf-8')
        self.git(self.author, 'add', 'skills')
        self.git(self.author, 'commit', '-m', 'upstream change')
        self.git(self.author, 'push', 'origin', 'main')
        return self.git(self.author, 'rev-parse', 'HEAD')

    def head(self):
        return self.git(self.source, 'rev-parse', 'HEAD')

    def tracking(self):
        return self.git(self.source, 'rev-parse', 'refs/remotes/origin/main')

    def second_project(self):
        other = self.base / 'other project'
        other.mkdir()
        self.git(other, 'init', '-b', 'main')
        installed = self.human('install', 'beta', '--project', other)
        self.assertEqual(installed.returncode, 0, installed.stderr)
        return other


class NormalUpdate(SharedSourceFixture):
    """C16: fetch, freeze, impact, activation and verification in one plain invocation."""

    def test_plain_update_fetches_and_activates_in_one_invocation(self):
        candidate = self.push_upstream()
        run = self.human('update')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertFalse(self.parses_as_result_envelope(run.stdout))
        self.assertNotIn('sha256:', run.stdout)
        self.assertIn('fetch: fetched', run.stdout)
        self.assertIn('shared source: affects 1 legacy scope(s) (all registered)', run.stdout)
        self.assertIn(str(self.project), run.stdout)
        self.assertEqual(self.head(), candidate)
        self.assertIn('Updated instructions.', (self.project / '.claude/skills/alpha/SKILL.md').read_text(encoding='utf-8'))
        self.assertFalse((self.home / 'pending.json').exists())
        again = self.human('update')
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn('no change needed', again.stdout)

    def test_json_reports_the_same_effects_as_one_document(self):
        candidate = self.push_upstream()
        done = self.machine('update')
        self.assertTrue(done['changed'])
        self.assertEqual(done['data']['source_after'], candidate)
        self.assertEqual(done['data']['scope']['affected'], [str(self.project)])
        self.assertEqual(self.head(), candidate)


class PreviewAndGuard(SharedSourceFixture):
    """C18: dry run, --offline and --expect-plan-hash never fetch; the guard binds the reviewed candidate."""

    def test_dry_run_and_offline_do_not_fetch(self):
        old = self.head()
        self.push_upstream()
        preview = self.machine('update', '--dry-run')
        self.assertFalse(preview['data']['fetch_effects']['attempted'])
        self.assertTrue(preview['data']['requires_fetch'])
        self.assertFalse(preview['would_change'])  # Nothing new is known until an explicit or normal fetch.
        self.assertEqual(self.tracking(), old)
        offline = self.human('update', '--offline')
        self.assertEqual(offline.returncode, 0, offline.stderr)
        self.assertIn('fetch: not attempted (cached candidate used)', offline.stdout)
        self.assertEqual(self.head(), old)
        self.assertEqual(self.tracking(), old)

    def test_guard_applies_the_previewed_candidate_even_after_the_remote_moves(self):
        reviewed = self.push_upstream()
        self.assertTrue(self.machine('source', 'fetch')['ok'])
        preview = self.machine('update', '--dry-run')
        self.assertTrue(preview['would_change'])
        newer = self.push_upstream('Later revision')
        done = self.machine('update', '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertTrue(done['changed'])
        self.assertFalse(done['data']['fetch_effects']['attempted'])
        self.assertEqual(self.head(), reviewed)
        self.assertNotEqual(self.head(), newer)
        self.assertTrue(self.machine('source', 'fetch')['ok'])
        stale = self.machine('update', '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertEqual(stale['error']['code'], 'plan.stale')
        self.assertEqual(self.head(), reviewed)


class ExpandedScope(SharedSourceFixture):
    """C19: a targeted legacy update discloses every affected scope; --yes cannot widen it."""

    def setUp(self):
        super().setUp()
        self.other = self.second_project()
        self.push_upstream()

    def affected(self):
        return sorted([str(self.project), str(self.other)])

    def test_json_and_redirected_invocations_refuse_with_the_proposal(self):
        old = self.head()
        refused = self.machine('update', '--project', self.project)
        self.assertEqual(refused['error']['code'], 'confirmation.required')
        proposal = refused['data']['confirmation']
        self.assertEqual((proposal['kind'], proposal['reason'], proposal['granted_by']), ('scope.expand', 'update.shared_source', None))
        self.assertEqual(sorted(proposal['scope']), self.affected())
        self.assertTrue(refused['data']['fetch_effects']['fetched'])  # Acquisition is reported; nothing was activated.
        self.assertEqual(self.head(), old)
        self.assertEqual(self.machine('update', '--project', self.project, '--yes')['error']['code'], 'confirmation.required')
        self.assertEqual(self.head(), old)
        text = self.human('update', '--project', self.project, stdin=subprocess.DEVNULL)
        self.assertEqual(text.returncode, 4, text.stderr)
        self.assertEqual(text.stdout, '')
        self.assertIn('confirmation.required', text.stderr)
        self.assertIn(str(self.other), text.stderr)
        self.assertNotIn('[y/N]', text.stderr)
        self.assertEqual(self.head(), old)
        self.assertFalse((self.home / 'pending.json').exists())

    def test_all_or_reviewed_hash_apply_the_disclosed_expansion(self):
        cold = self.machine('update', '--project', self.project, '--dry-run')
        self.assertFalse(cold['would_change'])  # Cold cache: no invented preview, no proposal.
        self.assertTrue(self.machine('source', 'fetch')['ok'])
        preview = self.machine('update', '--project', self.project, '--dry-run')
        self.assertTrue(preview['would_change'])
        self.assertEqual(preview['data']['confirmation']['granted_by'], None)
        self.assertFalse(preview['data']['fetch_effects']['attempted'])
        done = self.machine('update', '--project', self.project, '--expect-plan-hash', preview['data']['confirmation']['plan_hash'])
        self.assertTrue(done['changed'])
        self.assertEqual(done['data']['confirmation']['granted_by'], 'expect-plan-hash')
        self.assertEqual(sorted(done['data']['scope']['affected']), self.affected())
        self.assertEqual(self.head(), self.tracking())
        self.push_upstream('Second change')
        everything = self.machine('update', '--all')
        self.assertTrue(everything['changed'])
        self.assertNotIn('confirmation', everything['data'])
        self.assertEqual(self.head(), self.tracking())


class RecoveryAndBusy(SharedSourceFixture):
    """C20: pending recovery and a busy writer keep their existing exits; nothing is forced."""

    def test_pending_journal_refuses_before_any_fetch(self):
        self.push_upstream()
        pending = self.home / 'pending.json'
        pending.write_text('{"schema_version": 3}\n', encoding='utf-8')
        run = self.human('update')
        self.assertEqual(run.returncode, 8, run.stderr)
        self.assertIn('recovery.required', run.stderr)
        self.assertEqual(pending.read_text(encoding='utf-8'), '{"schema_version": 3}\n')
        self.assertNotEqual(self.tracking(), self.git(self.author, 'rev-parse', 'HEAD'))

    @unittest.skipUnless(os.name == 'posix', 'fcntl writer lock')
    def test_busy_writer_is_reported_not_bypassed(self):
        import fcntl
        self.push_upstream()
        old = self.head()
        with (self.home / 'operation.lock').open('a+b') as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            run = self.human('update')
        self.assertEqual(run.returncode, 6, run.stderr)
        self.assertIn('lock.busy', run.stderr)
        self.assertEqual(self.head(), old)


@unittest.skipUnless(os.name == 'posix', 'POSIX pseudoterminal prompt mechanics; native Windows console journeys are recorded separately')
class TerminalExpandedScope(SharedSourceFixture):
    """C19 on a pseudoterminal (macOS lane): yes applies in the same invocation; no keeps fetched objects unactivated."""

    def setUp(self):
        super().setUp()
        self.other = self.second_project()
        self.candidate = self.push_upstream()

    def terminal(self, *args, answer):
        import pty
        master, slave = pty.openpty()
        process = subprocess.Popen([sys.executable, '-B', str(ENTRY), *map(str, args)], stdin=slave, stdout=slave, stderr=slave,
                                   cwd=str(self.project), env=self.environment(), close_fds=True)
        os.close(slave)
        transcript = b''
        answered = False
        deadline = time.monotonic() + 60
        try:
            while time.monotonic() < deadline:
                ready, _, _ = select.select([master], [], [], 0.2)
                if ready:
                    try:
                        chunk = os.read(master, 4096)
                    except OSError:
                        break
                    if not chunk:
                        break
                    transcript += chunk
                if not answered and b'[y/N]' in transcript:
                    answered = True
                    os.write(master, answer)
                if process.poll() is not None and not ready:
                    break
            process.wait(timeout=10)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()
            os.close(master)
        self.assertTrue(answered, transcript.decode('utf-8', 'replace'))
        return process.returncode, transcript.decode('utf-8', 'replace')

    def test_yes_applies_to_every_disclosed_scope(self):
        code, text = self.terminal('update', '--project', self.project, answer=b'y\n')
        self.assertEqual(code, 0, text)
        self.assertIn('confirmation needed (update.shared_source)', text)
        self.assertIn(str(self.other), text)
        self.assertNotIn('sha256:', text)
        self.assertEqual(self.head(), self.candidate)
        self.assertFalse((self.home / 'pending.json').exists())

    def test_no_reports_retained_fetch_without_activation(self):
        old = self.head()
        code, text = self.terminal('update', '--project', self.project, answer=b'n\n')
        self.assertEqual(code, 4, text)
        self.assertIn('confirmation.declined', text)
        self.assertIn('fetch: fetched', text)
        self.assertEqual(self.head(), old)
        self.assertEqual(self.tracking(), self.candidate)
        self.assertFalse((self.home / 'pending.json').exists())
