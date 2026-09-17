"""A refusal after retained store preparation reports no consumer transaction (MASK-0112).

``apply``, ``ensure``, ``install`` and ``update`` prepare MASK-owned store artifacts, and may acquire exact cache
objects, before their writer lock and before any consumer effect. A command that then refuses keeps
``transaction: not_started`` and lists what it kept in ``data.retained_preparation``; ``changed`` stays true because
store bytes changed, and nothing needs recovery. The public cases run ``mask`` as a subprocess on a cold store: the tap
cache holds the locked commit and the store holds nothing. ``install`` and ``update`` refuse after preparation only when
their inputs change meanwhile, so those cases inject that concurrent writer into the real dispatcher in-process.
"""
import contextlib
import copy
import io
import json
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

import mask
import mask_core as c
import mask_store as store
from tests.fixture_files import write_json
from tests.public_support import PublicFixture
from tests.support import TAP


class ColdStore(PublicFixture):
    """A declared and locked project whose tap cache holds the locked commit while the store holds no artifact."""

    def setUp(self):
        super().setUp()
        write_json(self.project / '.mask.json', dict(schema_version=2, sources={TAP: dict(repository=self.upstream.as_uri(), packages='skills')},
                                                     default_agents=['claude', 'codex'], skills=[dict(source=TAP, id='alpha')]))
        self.assertTrue(self.machine('source', 'fetch', TAP)['ok'])
        self.assertTrue(self.machine('lock', '--project', self.project)['ok'])
        self.assertFalse((self.home / 'store').exists())

    def artifact(self, digest=None):
        digest = digest or json.loads((self.project / '.mask.lock.json').read_text(encoding='utf-8'))['packages'][0]['payload_digest']
        return self.home / 'store/v1' / digest.removeprefix('sha256:') / 'payload/alpha'

    def set_aside(self):
        """Move the retained artifact out of the store (test-only), so the next run prepares from a cold store again."""
        root = self.artifact().parents[1]
        root.rename(self.base / ('set-aside-' + root.name))

    def consumer_bytes(self):
        """Every project entry outside .git, plus the registry, configuration, policy and journal files under MASK_HOME."""
        observed = {}
        for path in sorted(self.project.rglob('*')):
            relative = path.relative_to(self.project)
            if relative.parts[0] != '.git':
                observed[relative.as_posix()] = ('link', os.readlink(path)) if path.is_symlink() else ('file', path.read_bytes()) if path.is_file() else ('directory',)
        for name in ('config.json', 'state.json', 'pending.json', 'integration.json', 'selection-policy.json'):
            path = self.home / name
            observed[name] = path.read_bytes() if path.exists() else None
        return observed

    def links(self):
        return sorted(path for path in self.project.glob('.*/skills/*') if path.is_symlink())

    def assert_refused_with_retained_preparation(self, result, code, artifacts=None):
        self.assertEqual(result['error']['code'], code)
        self.assertEqual((result['ok'], result['transaction'], result['changed']), (False, 'not_started', True))
        retained = result['data']['retained_preparation']
        self.assertEqual([Path(path) for path in retained['artifacts']], artifacts or [self.artifact()])
        self.assertEqual(retained['acquisitions'], [])
        self.assertTrue(all(Path(path).is_dir() for path in retained['artifacts']))
        self.assertFalse((self.home / 'pending.json').exists())


class RefusedApplyAll(ColdStore):
    """A registered consumer, never applied, whose skill destination holds unmanaged content."""

    def setUp(self):
        super().setUp()
        self.assertTrue(self.machine('project', 'register', '--project', self.project)['ok'])
        self.assertFalse((self.home / 'store').exists())
        occupied = self.project / '.claude/skills/alpha'
        occupied.mkdir(parents=True)
        (occupied / 'mine.txt').write_text('unmanaged\n', encoding='utf-8')

    def test_refused_apply_all_discloses_retained_preparation_without_a_consumer_transaction(self):
        before = self.consumer_bytes()
        collision = self.machine('apply', '--all')
        self.assert_refused_with_retained_preparation(collision, 'target.collision')
        self.assertEqual(self.consumer_bytes(), before)
        self.assertEqual(self.links(), [])
        # A stale reviewed guard also refuses only after preparation.
        self.set_aside()
        stale = self.machine('apply', '--all', '--expect-plan-hash', 'sha256:' + '0' * 64)
        self.assert_refused_with_retained_preparation(stale, 'plan.stale')
        self.assertEqual(self.consumer_bytes(), before)
        self.assertEqual(self.links(), [])

    def test_human_refusal_names_retained_preparation_and_no_recovery(self):
        before = self.consumer_bytes()
        run = self.human('apply', '--all')
        self.assertEqual(run.returncode, 4, run.stderr)
        self.assertEqual(run.stdout, '')
        self.assertIn('target.collision', run.stderr)
        self.assertIn('retained preparation: 1 store artifact(s) and 0 cache acquisition(s) kept under MASK_HOME', run.stderr)
        self.assertIn('state: no deployment changes were applied', run.stderr)
        self.assertNotIn('recover', run.stderr)
        self.assertNotIn('link.create', run.stderr)  # Planned links that never ran are not listed as effects.
        self.assertTrue(self.artifact().is_dir())
        self.assertEqual(self.consumer_bytes(), before)


class RefusedManualEnsure(ColdStore):
    """An unapproved project: manual ensure hydrates the store from the cache offline, then consent is not given."""

    def test_json_consent_refusal_discloses_retained_preparation_without_a_consumer_transaction(self):
        before = self.consumer_bytes()
        refused = self.machine('ensure', '--project', self.project)
        self.assert_refused_with_retained_preparation(refused, 'confirmation.required')
        self.assertIsNone(refused['data']['confirmation']['granted_by'])
        self.assertEqual(self.consumer_bytes(), before)
        self.assertEqual(self.links(), [])

    def test_redirected_human_refusal_names_retained_preparation(self):
        before = self.consumer_bytes()
        run = self.human('ensure', '--project', self.project, stdin=subprocess.DEVNULL)
        self.assertEqual(run.returncode, 4, run.stderr)
        self.assertIn('confirmation.required', run.stderr)
        self.assertIn('retained preparation: 1 store artifact(s) and 0 cache acquisition(s) kept under MASK_HOME', run.stderr)
        self.assertIn('state: no deployment changes were applied', run.stderr)
        self.assertNotIn('recover --inspect', run.stderr)
        self.assertEqual(self.consumer_bytes(), before)

    @unittest.skipUnless(os.name == 'posix', 'POSIX pseudoterminal prompt; a declined native Windows console prompt is not automated')
    def test_declined_prompt_names_retained_preparation(self):
        before = self.consumer_bytes()
        code, text = self.terminal('ensure', '--project', self.project, answer=b'n\n')
        self.assertEqual(code, 4, text)
        self.assertIn('confirmation.declined', text)
        self.assertIn('retained preparation: 1 store artifact(s)', text)
        self.assertIn('state: no deployment changes were applied', text)
        self.assertEqual(self.consumer_bytes(), before)

    def test_applied_consumer_effects_keep_committed_reporting(self):
        applied = self.machine('ensure', '--project', self.project, '--yes')
        self.assertTrue(applied['ok'], applied['error'])
        self.assertEqual((applied['transaction'], applied['changed']), ('committed', True))
        self.assertEqual([Path(path) for path in applied['data']['retained_preparation']['artifacts']], [self.artifact()])
        self.assertEqual(len(self.links()), 2)
        again = self.machine('ensure', '--project', self.project)
        self.assertEqual((again['transaction'], again['changed']), ('not_needed', False))
        self.assertNotIn('retained_preparation', again['data'])


class ConcurrentWriterDuringPreparation(ColdStore):
    """install and update through the real dispatcher while another writer changes the registry during preparation."""

    def dispatch(self, *argv):
        original = store.ensure

        def prepare_then_write(*args, **kwargs):
            effects = original(*args, **kwargs)
            with c.writer_lock(self.home):
                state = c.state(c.read_json(self.home / 'state.json'))
                changed = copy.deepcopy(state)
                changed['generation'] += 1
                c.atomic_text(self.home / 'state.json', c.text_json(changed), c.read_text(self.home / 'state.json'))
            return effects

        stdout = io.StringIO()
        with patch.object(store, 'ensure', side_effect=prepare_then_write), contextlib.redirect_stdout(stdout):
            code = mask.main([*map(str, argv), '--home', str(self.home), '--json'])
        return code, json.loads(stdout.getvalue())

    def test_install_refused_after_preparation_reports_no_consumer_transaction(self):
        before = self.consumer_bytes()
        code, refused = self.dispatch('install', 'alpha', '--project', self.project)
        self.assertEqual(code, 4)
        self.assert_refused_with_retained_preparation(refused, 'plan.stale')
        after = self.consumer_bytes()
        self.assertNotEqual(after.pop('state.json'), before.pop('state.json'))  # Only the injected writer changed the registry.
        self.assertEqual(after, before)
        self.assertEqual(json.loads((self.home / 'state.json').read_text(encoding='utf-8'))['projects'], {})
        self.assertEqual(self.links(), [])

    def test_update_refused_after_preparation_reports_no_consumer_transaction(self):
        for name in ('.mask.json', '.mask.lock.json'):
            (self.project / name).unlink()  # install resolves and locks alpha itself, then deploys it from the store.
        installed = self.machine('install', 'alpha', '--project', self.project)
        self.assertTrue(installed['ok'], installed['error'])
        (self.source / 'skills/alpha/SKILL.md').write_text('---\nname: alpha\ndescription: Fixture skill\n---\n\nChanged upstream.\n', encoding='utf-8', newline='\n')
        self.publish('alpha changed upstream')
        before = self.consumer_bytes()
        code, refused = self.dispatch('upgrade', '--project', self.project)
        self.assertEqual(code, 4)
        change = refused['data']['consumers'][0]['changes'][0]
        self.assertTrue(refused['data']['fetches'][TAP]['ok'])
        self.assert_refused_with_retained_preparation(refused, 'plan.stale', [self.artifact(change['after_digest'])])
        after = self.consumer_bytes()
        self.assertNotEqual(after.pop('state.json'), before.pop('state.json'))
        self.assertEqual(after, before)  # The lock and the links still name the installed artifact.
