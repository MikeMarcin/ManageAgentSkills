"""A pinned ensure preview on a cold store binds the plan hash of the run that applies (MASK-0111).

Every case runs ``mask`` as a subprocess. The tap cache holds the locked commit (``source fetch`` and ``lock``) and
the store holds no artifact, as on a machine that has not yet deployed a committed declaration and lock. The static
implement-rfc fixture declares native roles and the generated one declares setup; planned role writes and setup
identities bind the plan hash, so a cold preview that leaves them unexamined disagrees with the applying run, which
materializes the package first. Git's trace2 event files show that no command here fetches, and a byte snapshot of
MASK_HOME shows that the preview writes nothing, neither to the store nor to the tap cache. A real change to the
declaration, lock or a policy between preview and apply still refuses.
"""
import json
from pathlib import Path
import shutil
import tempfile

from tests.legacy_support import write_json
from tests.public_support import CONSUMER_CONTEXT, PublicFixture
from tests.support import TAP
from tests.test_setup import SUBJECT, SetupFixture


def declaration(upstream, skills, agents=('claude', 'codex')):
    """A v2 declaration of the fixture tap; ``agents=None`` leaves the default, every agent."""
    value = dict(schema_version=2, sources={TAP: dict(repository=upstream.as_uri(), packages='skills')}, skills=[dict(source=TAP, id=skill) for skill in skills])
    if agents is not None:
        value['default_agents'] = list(agents)
    return value


class ColdStorePreview(PublicFixture):
    def setUp(self):
        super().setUp()
        traces = tempfile.TemporaryDirectory(prefix='mask-trace-')
        self.addCleanup(traces.cleanup)
        self.traces = Path(traces.name)
        shutil.copytree(CONSUMER_CONTEXT, self.project / '.mask')
        self.declare('alpha', 'implement-rfc')
        fetched, fetches = self.traced('source', 'fetch', TAP)
        self.assertTrue(fetched['ok'])
        self.assertGreaterEqual(fetches, 1)  # The trace counts real fetches, so a zero below is evidence.
        self.assertTrue(self.machine('lock', '--project', self.project)['ok'])
        self.assertFalse((self.home / 'store').exists())

    def declare(self, *skills, agents=('claude', 'codex')):
        write_json(self.project / '.mask.json', declaration(self.upstream, skills, agents))

    def traced(self, *args):
        """One JSON invocation and the number of git fetch processes it started, read from Git's own trace2 event files."""
        trace = Path(tempfile.mkdtemp(dir=self.traces))
        result = self.machine(*args, env={'GIT_TRACE2_EVENT': str(trace)})
        events = [json.loads(line) for path in trace.iterdir() for line in path.read_text(encoding='utf-8').splitlines()]
        return result, sum(event['event'] == 'cmd_name' and event['name'] == 'fetch' for event in events)

    def home_bytes(self):
        """Every entry under MASK_HOME with its file bytes: control files, the tap cache and the store."""
        return {path.relative_to(self.home).as_posix(): path.read_bytes() if path.is_file() else None for path in sorted(self.home.rglob('*'))}

    def deployed(self):
        links = sorted(path for path in self.project.glob('.*/skills/*') if path.is_symlink())
        roles = sorted(path for path in self.project.glob('.*/agents/*') if path.is_file())
        return links, roles

    def test_approved_cold_preview_binds_the_applying_run_without_fetch_or_materialization(self):
        self.assertTrue(self.machine('integration', 'approve', '--project', self.project)['ok'])
        before = self.home_bytes()
        preview, fetches = self.traced('ensure', '--project', self.project, '--dry-run')
        self.assertEqual(fetches, 0)
        self.assertEqual(self.home_bytes(), before)  # Neither the store nor the tap cache changed.
        applied, fetches = self.traced('ensure', '--project', self.project, '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertTrue(applied['ok'], applied['error'])
        self.assertEqual((applied['transaction'], applied['data']['readiness'], fetches), ('committed', 'ready_pinned', 0))
        links, roles = self.deployed()
        self.assertEqual(len(links), 4)
        self.assertTrue(roles)
        # The preview examined the exact locked bytes from the cache, so it disclosed the roles the applying run wrote.
        self.assertTrue(preview['ok'], preview['error'])
        self.assertEqual(sorted(Path(action['path']) for action in preview['actions'] if action['kind'] == 'native_role.write'), roles)

    def test_unapproved_cold_preview_proposal_grants_the_applying_run(self):
        before = self.home_bytes()
        preview, fetches = self.traced('ensure', '--project', self.project, '--dry-run')
        self.assertEqual(fetches, 0)
        self.assertEqual(self.home_bytes(), before)
        proposal = preview['data']['confirmation']
        self.assertEqual(proposal['plan_hash'], preview['data']['plan_hash'])
        applied, fetches = self.traced('ensure', '--project', self.project, '--expect-plan-hash', proposal['plan_hash'])
        self.assertTrue(applied['ok'], applied['error'])
        self.assertEqual((applied['data']['confirmation']['granted_by'], fetches), ('expect-plan-hash', 0))
        self.assertEqual(len(self.deployed()[0]), 4)
        self.assertFalse((self.home / 'integration.json').exists())
        self.assertTrue(preview['ok'], preview['error'])

    def assert_stale_after(self, change):
        """A cold preview, a real change to its inputs, then the guarded run: it refuses plan.stale and deploys nothing."""
        self.assertTrue(self.machine('integration', 'approve', '--project', self.project)['ok'])
        preview = self.machine('ensure', '--project', self.project, '--dry-run')
        self.assertTrue(preview['data']['plan_hash'].startswith('sha256:'))
        change()
        refused = self.machine('ensure', '--project', self.project, '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertEqual(refused['error']['code'], 'plan.stale')
        self.assertEqual(self.deployed(), ([], []))
        self.assertEqual(json.loads((self.home / 'state.json').read_text(encoding='utf-8'))['projects'], {})
        self.assertFalse((self.home / 'pending.json').exists())

    def test_changed_declaration_still_refuses_stale(self):
        def change():
            self.declare('alpha', 'beta', 'implement-rfc')
            self.assertTrue(self.machine('lock', '--project', self.project)['ok'])
        self.assert_stale_after(change)

    def test_changed_lock_still_refuses_stale(self):
        def change():
            (self.source / 'skills/alpha/SKILL.md').write_text('---\nname: alpha\ndescription: Fixture skill\n---\n\nChanged upstream.\n', encoding='utf-8', newline='\n')
            self.publish('alpha changed upstream')
            self.assertTrue(self.machine('source', 'fetch', TAP)['ok'])
            declared, locked = ((self.project / name).read_bytes() for name in ('.mask.json', '.mask.lock.json'))
            self.assertTrue(self.machine('lock', '--project', self.project, '--refresh')['ok'])
            self.assertEqual((self.project / '.mask.json').read_bytes(), declared)
            self.assertNotEqual((self.project / '.mask.lock.json').read_bytes(), locked)
        self.assert_stale_after(change)

    def test_changed_integration_policy_still_refuses_stale(self):
        self.assert_stale_after(lambda: self.assertTrue(self.machine('integration', 'approve', '--project', self.project, '--allow-locked-fetch', TAP)['ok']))

    def test_changed_selection_policy_still_refuses_stale(self):
        # Every agent by default, so disabling one changes the deployment without blocking explicit agent intent.
        self.declare('alpha', 'implement-rfc', agents=None)
        self.assertTrue(self.machine('lock', '--project', self.project)['ok'])
        self.assert_stale_after(lambda: self.assertTrue(self.machine('selection-policy', 'set', '--agent', 'claude')['ok']))


class ColdStoreSetupPreview(SetupFixture):
    """The generated implement-rfc package, registered and approved, whose locked bytes are only in the tap cache."""

    def declare_consumer(self, root, skills, *, user=False):
        write_json(root / '.mask.json', declaration(self.upstream, skills))
        self.assertTrue(self.machine('source', 'fetch', TAP)['ok'])
        self.assertTrue(self.machine('lock', '--project', root)['ok'])
        self.assertTrue(self.machine('project', 'register', '--project', root)['ok'])

    def test_cold_preview_binds_the_setup_identity_the_applying_run_executes(self):
        self.assertFalse((self.home / 'store').exists())
        preview = self.machine('ensure', '--project', self.project, '--dry-run')
        self.assertFalse((self.home / 'store').exists())
        self.assertEqual(self.launches(), 0)
        applied = self.machine('ensure', '--project', self.project, '--expect-plan-hash', preview['data']['plan_hash'], '--allow-setup', SUBJECT)
        self.assertEqual(self.launches(), 1, applied['error'])
        self.assert_published(applied)
        # The preview proposed the same frozen setup action instead of blocking on an absent package directory.
        rows = self.setup_rows(preview)
        self.assertEqual([row.get('subject') for row in rows], [SUBJECT])
        self.assertNotIn('blocked', [row['state'] for row in rows])
