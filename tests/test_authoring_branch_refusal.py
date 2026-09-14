"""Authoring-checkout branch refusals through the public CLI (MASK-0108).

Every command that observes a tap's authoring checkout runs as a subprocess against disposable checkouts and local
repositories: ``tap add --checkout`` (a new alias, and a bootstrap of a fresh MASK_HOME), a curated import destination,
``skill record-adaptation``, ``source publish --commit`` and ``source dev-link``. A checkout on a branch other than the
tap's configured one refuses ``source.identity_mismatch`` and a detached HEAD refuses ``source.detached`` (both exit 4),
whether or not the checkout has an origin, and nothing is written. A checkout without an origin is identified by its own
path, so one that loses the origin naming its tap still refuses ``source.identity_mismatch``.
"""
from pathlib import Path
import unittest

from tests.support import TAP, Fixture

ALPHA = TAP + '/alpha'
GAMMA = 'skills/gamma'


class AuthoringFixture(Fixture):
    """The fixture tap with ``self.source`` as its authoring checkout, a pinned consumer of alpha and an unfetched vendor tap.

    With ``ORIGIN`` the checkout's origin names the tap upstream; without it the tap names the checkout's own path.
    """

    ORIGIN = True

    def setUp(self):
        super().setUp()
        self.fresh = self.base / 'fresh machine'
        if self.ORIGIN:
            self.git(self.source, 'remote', 'add', 'origin', str(self.upstream))
        self.url = self.upstream if self.ORIGIN else self.source
        self.call('tap', 'add', TAP, self.url, '--checkout', self.source)
        self.install(ALPHA)
        vendor = self.base / 'vendor'
        (vendor / GAMMA).mkdir(parents=True)
        (vendor / GAMMA / 'SKILL.md').write_bytes(b'---\nname: gamma\ndescription: Imported fixture\n---\nInstructions.\n')
        self.git(vendor, 'init', '-q', '-b', 'main')
        self.git(vendor, 'config', 'user.name', 'Fixture')
        self.git(vendor, 'config', 'user.email', 'fixture@example.invalid')
        self.git(vendor, 'add', '.')
        self.git(vendor, 'commit', '-q', '-m', 'vendor fixture')
        self.call('tap', 'add', 'vendor', vendor)

    def observations(self):
        """Every authoring-checkout observation, each as the invocation that would take effect."""
        return dict(
            tap_add=('tap', 'add', 'mirror', self.url, '--checkout', self.source),
            import_destination=('skill', 'import', 'vendor', '--mode', 'copy', '--into', TAP, '--path', GAMMA),
            record_adaptation=('skill', 'record-adaptation', ALPHA, '--note', 'Local edit'),
            publish=('source', 'publish', TAP, '--paths', 'skills/alpha', '--commit'),
            dev_link=('source', 'dev-link', ALPHA, '--project', self.project, '--authoring-root', self.source),
            tap_add_bootstrap=('tap', 'add', TAP, self.url, '--checkout', self.source, '--home', self.fresh))

    def effects(self):
        """The fixture tree, and what an observation could leave in the authoring repository besides its working tree.

        Any refused mutator on an empty MASK_HOME leaves its writer's ``operation.lock`` there, as the program did before
        MASK-0108 for an origin naming another repository. The fresh bootstrap home may hold that lock, never configuration or state.
        """
        lock = (self.fresh.name, str(Path(self.fresh.name) / 'operation.lock'))
        tree = {key: value for key, value in self.snapshot().items() if key not in lock}
        facts = {args: self.git(self.source, *args.split()) for args in
                 ('status --porcelain=v2 --branch', 'for-each-ref', 'ls-files --stage', 'worktree list --porcelain', 'count-objects -v')}
        return tree, facts

    def assert_refused(self, code, **details):
        before = self.effects()
        for name, args in self.observations().items():
            with self.subTest(observation=name):
                error = self.call(*args, code=4)['error']
                self.assertEqual(error['code'], code, error)
                self.assertLessEqual(details.items(), error.get('details', {}).items(), error)
                self.assertEqual(self.effects(), before)


class BranchRefusal(AuthoringFixture):
    def test_another_branch_refuses_identity_mismatch_and_writes_nothing(self):
        self.git(self.source, 'checkout', '-q', '-b', 'topic')
        self.assert_refused('source.identity_mismatch', branch='topic', configured_branch='main')

    def test_a_detached_head_refuses_detached_and_writes_nothing(self):
        self.git(self.source, 'checkout', '-q', '--detach')
        self.assert_refused('source.detached', configured_branch='main')

    def test_the_configured_branch_passes_every_observation(self):
        """Positive control: on its configured branch the same checkout gets past every observation; previews write nothing."""
        self.call('source', 'fetch', 'vendor')
        before = self.effects()
        self.call('tap', 'add', 'mirror', self.url, '--checkout', self.source, '--dry-run')
        self.assertTrue(self.call('skill', 'import', 'vendor', '--mode', 'copy', '--into', TAP, '--path', GAMMA, '--dry-run')['would_change'])
        self.assertEqual(self.call('skill', 'record-adaptation', ALPHA, '--note', 'Local edit', code=4)['error']['code'], 'provenance.absent')
        self.assertFalse(self.call('source', 'publish', TAP, '--paths', 'skills/alpha')['would_change'])
        self.assertEqual(self.call('source', 'dev-link', ALPHA, '--project', self.project, '--authoring-root', self.source, '--dry-run')['data']['mode'], 'dev-link')
        self.assertEqual(self.effects(), before)


class BranchRefusalWithoutOrigin(BranchRefusal):
    """The same refusals, codes and exits when the checkout has no origin."""

    ORIGIN = False


class MissingOrigin(AuthoringFixture):
    def test_a_checkout_that_loses_its_origin_keeps_refusing_identity_mismatch(self):
        # Without an origin the checkout is identified by its own path, which is not the tap upstream.
        self.git(self.source, 'remote', 'remove', 'origin')
        self.assert_refused('source.identity_mismatch')


if __name__ == '__main__':
    unittest.main()
