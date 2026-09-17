"""In-process consent through the public CLI (RFC-MASK-0018 AC03/AC04/AC06; cases C13-C15).

The significant authority exercised here is one-time manual readiness for a
project that has no integration approval. Pipe tests prove that JSON, redirected
streams and event hooks never wait for input; the POSIX pseudoterminal tests
prove the prompt mechanics (yes, no, EOF, interruption, stale proposal). No helper
approves the project, registers it or renders anything before the command under
test; ``--json`` is injected only by the ``machine`` helper.
"""
import argparse
import os
import subprocess
import unittest

import mask_consent as consent
import mask_core as core
from tests.legacy_support import write_json
from tests.public_support import PublicFixture
from tests.support import TAP


class ConsentFixture(PublicFixture):
    def setUp(self):
        super().setUp()
        self.declare('alpha')
        self.assertTrue(self.machine('source', 'fetch', TAP)['ok'])
        self.assertTrue(self.machine('lock', '--project', self.project)['ok'])
        # The locked package bytes are in the store, as the live checkout was; nothing is registered, approved or linked.
        self.assertTrue(self.machine('source', 'fetch', '--locked', '--project', self.project)['ok'])

    def declare(self, *skills):
        """An unregistered v2 declaration of the fixture tap; its lock is written by the public ``lock`` command."""
        write_json(self.project / '.mask.json', dict(schema_version=2, sources={TAP: dict(repository=self.upstream.as_uri(), packages='skills')},
                                                     default_agents=['claude', 'codex'], skills=[dict(source=TAP, id=skill) for skill in skills]))

    def links(self):
        return sorted(path.relative_to(self.project).as_posix() for path in self.project.glob('.*/skills/*') if path.is_symlink())

    def assert_untouched(self):
        self.assertEqual(self.links(), [])
        self.assertFalse((self.home / 'integration.json').exists())
        self.assertFalse((self.home / 'pending.json').exists())


class PipedConsentTests(ConsentFixture):
    def test_json_reports_a_typed_proposal_without_waiting(self):
        refused = self.machine('ensure', '--project', self.project)
        self.assertFalse(refused['ok'])
        self.assertEqual(refused['error']['code'], 'confirmation.required')
        proposal = refused['data']['confirmation']
        self.assertEqual((proposal['kind'], proposal['reason'], proposal['granted_by']), ('readiness', 'integration.approval_required', None))
        self.assertEqual(proposal['scope'], [str(self.project)])
        self.assertTrue(proposal['plan_hash'].startswith('sha256:'))
        self.assertEqual(refused['data']['readiness'], 'confirmation_required')
        self.assert_untouched()
        # Reviewed automation can bind that exact frozen proposal without a human.
        granted = self.machine('ensure', '--project', self.project, '--expect-plan-hash', proposal['plan_hash'])
        self.assertTrue(granted['changed'])
        self.assertEqual(granted['data']['confirmation']['granted_by'], 'expect-plan-hash')
        self.assertEqual(len(self.links()), 2)
        self.assertFalse((self.home / 'integration.json').exists())

    def test_redirected_human_invocation_never_prompts(self):
        run = self.human('ensure', '--project', self.project, stdin=subprocess.DEVNULL)
        self.assertEqual(run.returncode, 4, run.stderr)
        self.assertEqual(run.stdout, '')
        self.assertIn('confirmation.required', run.stderr)
        self.assertIn(str(self.project), run.stderr)
        self.assertNotIn('[y/N]', run.stderr)
        self.assertFalse(self.parses_as_result_envelope(run.stderr))
        self.assert_untouched()

    def test_yes_grants_one_invocation_without_persisting_approval(self):
        done = self.machine('ensure', '--project', self.project, '--yes')
        self.assertTrue(done['changed'])
        self.assertEqual(done['data']['confirmation']['granted_by'], 'yes')
        self.assertEqual(done['data']['readiness'], 'ready_pinned')
        self.assertEqual(len(self.links()), 2)
        self.assertFalse((self.home / 'integration.json').exists())
        again = self.machine('ensure', '--project', self.project)
        self.assertFalse(again['changed'])
        self.assertNotIn('confirmation', again['data'])
        self.assertEqual(again['data']['approval'], 'not_approved')
        human = self.human('ensure', '--project', self.project, stdin=subprocess.DEVNULL)
        self.assertEqual(human.returncode, 0, human.stderr)
        self.assertIn('Automatic startup checks: not approved', human.stdout)
        # One-time consent did not become automatic readiness.
        event = self.machine('ensure', '--project', self.project, '--event', 'startup')
        self.assertEqual(event['error']['code'], 'integration.approval_required')

    def test_yes_does_not_widen_events_or_bypass_blockers(self):
        for event in ('startup', 'post-checkout'):
            refused = self.machine('ensure', '--project', self.project, '--event', event, '--yes')
            self.assertEqual(refused['error']['code'], 'integration.approval_required')
            self.assertNotIn('confirmation', refused['data'])
        leaf = self.project / '.claude/skills/alpha'
        leaf.mkdir(parents=True)
        (leaf / 'mine.txt').write_text('unmanaged\n', encoding='utf-8')
        collision = self.machine('ensure', '--project', self.project, '--yes')
        self.assertEqual(collision['error']['code'], 'target.collision')
        self.assertEqual((leaf / 'mine.txt').read_text(encoding='utf-8'), 'unmanaged\n')
        self.assertEqual(self.links(), [])
        self.assertFalse((self.home / 'integration.json').exists())

    def test_dry_run_shows_the_proposal_without_asking(self):
        preview = self.machine('ensure', '--project', self.project, '--dry-run')
        self.assertTrue(preview['ok'])
        self.assertTrue(preview['would_change'])
        self.assertEqual(preview['data']['confirmation']['granted_by'], None)
        self.assert_untouched()
        text = self.human('ensure', '--project', self.project, '--dry-run', stdin=subprocess.DEVNULL)
        self.assertEqual(text.returncode, 0, text.stderr)
        self.assertIn('one-time readiness consent', text.stdout)


class ConsentSeamTests(unittest.TestCase):
    def test_yes_grants_only_ordinary_kinds(self):
        proposal = consent.request('package.setup', 'setup.required', ['/x'], [], 'sha256:1', 'Run setup?')
        self.assertIsNone(consent.granted_by(argparse.Namespace(yes=True), proposal))
        # A package script is a NAMED kind: the exact plan hash alone grants nothing; it needs every subject named as well.
        self.assertIsNone(consent.granted_by(argparse.Namespace(expect_plan_hash='sha256:1'), proposal))
        named = consent.request('package.setup', 'setup.required', ['/x'], [], 'sha256:1', 'Run setup?', subjects=['src/skill:prepare'])
        self.assertIsNone(consent.granted_by(argparse.Namespace(expect_plan_hash='sha256:1', allow_setup=['src/other:prepare', 'bad entry']), named))
        self.assertEqual(consent.granted_by(argparse.Namespace(expect_plan_hash='sha256:1', allow_setup=['src/skill:prepare']), named), 'allow-setup')
        self.assertIsNone(consent.granted_by(argparse.Namespace(expect_plan_hash='sha256:other', allow_setup=['src/skill:prepare']), named))
        self.assertEqual(consent.granted_by(argparse.Namespace(expect_plan_hash='sha256:2'), consent.request('readiness', 'r', [], [], 'sha256:2', 'q')), 'expect-plan-hash')
        self.assertEqual(consent.granted_by(argparse.Namespace(yes=True), consent.request('readiness', 'r', [], [], 'sha256:2', 'q')), 'yes')
        with self.assertRaises(core.MaskError) as refused:
            consent.granted_by(argparse.Namespace(consented={'package.setup': 'sha256:old'}), proposal)
        self.assertEqual(refused.exception.code, 'plan.stale')
        with self.assertRaises(core.MaskError) as unknown:
            consent.request('anything', 'r', [], [], 'sha256:3', 'q')
        self.assertEqual(unknown.exception.exit_code, 10)

    def test_noninteractive_refusal_carries_the_proposal(self):
        output = dict(data={})
        proposal = consent.request('readiness', 'integration.approval_required', ['/p'], [], 'sha256:4', 'Ready?')
        with self.assertRaises(core.MaskError) as refused:
            consent.require(argparse.Namespace(json=True), output, proposal)
        self.assertEqual(refused.exception.code, 'confirmation.required')
        self.assertEqual(output['data']['confirmation'], proposal)


@unittest.skipUnless(os.name == 'posix', 'POSIX pseudoterminal prompt mechanics; native Windows console journeys are recorded separately')
class TerminalConsentTests(ConsentFixture):
    """Automated prompt mechanics on a pseudoterminal (macOS lane here; not native Windows qualification)."""

    def test_yes_completes_the_operation_in_the_same_invocation(self):
        code, text = self.terminal('ensure', '--project', self.project, answer=b'y\n')
        self.assertEqual(code, 0, text)
        self.assertIn('confirmation needed (integration.approval_required)', text)
        self.assertIn('one-time readiness granted by prompt', text)
        self.assertNotIn('sha256:', text)  # The plan hash stays inside the program.
        self.assertEqual(len(self.links()), 2)
        self.assertFalse((self.home / 'integration.json').exists())
        self.assertFalse((self.home / 'pending.json').exists())

    def test_no_and_eof_decline(self):
        for answer in (b'n\n', b'\n', b'\x04'):
            with self.subTest(answer=answer):
                code, text = self.terminal('ensure', '--project', self.project, answer=answer)
                self.assertEqual(code, 4, text)
                self.assertIn('confirmation.declined', text)
                self.assert_untouched()

    def test_interruption_at_the_prompt_runs_nothing(self):
        code, text = self.terminal('ensure', '--project', self.project, interrupt=True)
        self.assertEqual(code, 130, text)
        self.assertIn('invocation.interrupted', text)
        self.assert_untouched()

    def test_input_changed_after_the_prompt_is_a_stale_plan(self):
        def change_declaration():
            self.declare('alpha', 'beta')
            self.assertTrue(self.machine('lock', '--project', self.project)['ok'])
        code, text = self.terminal('ensure', '--project', self.project, answer=b'y\n', before_answer=change_declaration)
        self.assertEqual(code, 4, text)
        self.assertIn('plan.stale', text)
        self.assert_untouched()

    def test_lock_is_free_while_the_prompt_waits(self):
        def other_writer():
            result = self.machine('user', 'init')  # Another mutating command takes the writer lock while the prompt waits.
            self.assertTrue(result['changed'], result)
        code, text = self.terminal('ensure', '--project', self.project, answer=b'y\n', before_answer=other_writer)
        self.assertEqual(code, 0, text)  # The concurrent writer changed unrelated machine files, not this proposal's inputs.
        self.assertEqual(len(self.links()), 2)
