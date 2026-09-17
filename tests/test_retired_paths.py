"""Retired live-checkout commands and the migration gate through the public CLI (RFC-MASK-0021 AC05, B08-B10; MASK-0102).

Legacy machines come from the schema-true builder in ``tests.legacy_support``. Every invocation uses a private
MASK_HOME and personal home, and every refusal is compared with a snapshot of the whole disposable base: machine
home, consumers, the clone and its upstream.
"""
import json
import subprocess
import sys

from tests.legacy_support import ENTRY, LegacyFixture, git, snapshot, write_json
from tests.support import TAP

REMEDIATION = ['mask', 'doctor', '--migrate', '--dry-run']
EXEMPT = {'capabilities', 'config.show', 'doctor', 'recover', 'self.status', 'self.install', 'self.uninstall', 'update'}
RETIRED = {'source.status', 'source.migrate', 'migrate'}
# Values for required operands. The gate refuses before any operand is interpreted, so they only need to parse.
VALUES = {'id': 'agentskills/alpha', 'ids': 'alpha', 'name': 'agentskills', 'url': 'file:///nowhere.git', 'path': '{project}',
          'agent': 'claude', 'mode': 'copy', 'into': 'agentskills', 'note': 'retired', 'reason': 'retired', 'skill': 'alpha',
          'target': 'claude', 'expect_source': '{project}', 'expect_identity': 'sha256:' + '0' * 64, 'bin_dir': '{bin}'}
# One member of each operand set that argument validation requires before dispatch.
EXTRA = {'config.set': ['--git-timeout', '30'], 'skill.validate': ['--all'], 'selection-policy.set': ['--agent', 'claude'],
         'project.set': ['--clear'], 'user.set': ['--clear'], 'project.set-targets': ['--inherit'], 'user.set-targets': ['--inherit'],
         'project.set-agents': ['--inherit'], 'user.set-agents': ['--inherit'], 'link.adopt': ['--project', '{project}'],
         'compatibility.override': ['--project', '{project}', '--agent', 'claude'], 'compatibility.clear': ['--project', '{project}']}


def minimal_argv(descriptor, **places):
    """Syntactically valid argv for a capabilities descriptor: its words plus every required operand."""
    words = descriptor['name'].split('.')
    for argument in descriptor['arguments']:
        if not argument['flags'] and argument['nargs'] in (None, '+'):
            words.append(VALUES[argument['name']])
        elif argument['flags'] and argument['required']:
            words.extend((argument['flags'][0], VALUES[argument['name']]))
    words.extend(EXTRA.get(descriptor['name'], ()))
    return [word.format(**places) for word in words]


class RetiredCommands(LegacyFixture):
    def test_capabilities_describe_only_the_tap_model(self):
        caps = self.machine('capabilities')['data']
        commands = {item['name']: item for item in caps['commands']}
        self.assertFalse(set(commands) & RETIRED)
        self.assertFalse({argument['name'] for argument in commands['init']['arguments']} & {'source', 'remote', 'branch'})
        self.assertEqual((caps['schemas']['machine'], caps['deployment_model']), (3, 'taps'))

    def test_retired_commands_are_invocation_errors_that_write_nothing(self):
        roots = self.legacy_machine(1)
        before = snapshot(roots.base, roots.base)
        for args in (('source', 'status'), ('source', 'migrate'), ('migrate',), ('migrate', '--to-pinned', '--project', roots.project)):
            with self.subTest(args=args):
                self.assertEqual(self.machine(*args, code=2)['error']['code'], 'invocation.invalid')
                self.assertEqual(snapshot(roots.base, roots.base), before)


class MigrationGate(LegacyFixture):
    """B09: on a v1 or v2 configuration only the exempt commands proceed; every other command refuses before any effect."""

    def raw(self, *args):
        run = subprocess.run([sys.executable, '-B', str(ENTRY), *map(str, args), '--json'], capture_output=True, encoding='utf-8',
                             cwd=str(self.roots.base), env=self.environment(), timeout=120)
        self.assertEqual(run.stderr, '', run.stderr)
        return run.returncode, json.loads(run.stdout)

    def assert_gate(self, version):
        roots = self.legacy_machine(version)
        places = dict(project=roots.project, bin=roots.base / 'bin')
        descriptors = self.machine('capabilities')['data']['commands']
        before = snapshot(roots.base, roots.base)
        gated = [item for item in descriptors if item['name'] not in EXEMPT]
        self.assertEqual(len(gated), len(descriptors) - len(EXEMPT))
        for descriptor in gated:
            args = minimal_argv(descriptor, **places)
            with self.subTest(command=descriptor['name'], args=args):
                error = self.machine(*args, code=4)['error']
                self.assertEqual(error['code'], 'migration.required')
                self.assertEqual((error['details']['schema_version'], error['details']['remediation']), (version, REMEDIATION))
                self.assertIn('mask doctor --migrate --dry-run', error['remediation'][0]['message'])
                self.assertEqual(snapshot(roots.base, roots.base), before)
        # The exempt commands proceed; self commands run only as a dry run or read-only status.
        shown = self.machine('config', 'show')['data']
        self.assertEqual((shown['config']['schema_version'], shown['migration_required']), (version, True))
        doctor = self.machine('doctor')['data']
        self.assertEqual((doctor['healthy'], doctor['issues'][0]['code'], doctor['issues'][0]['details']['remediation']), (False, 'migration.required', REMEDIATION))
        self.assertEqual(self.machine('doctor', '--check', code=7)['error']['code'], 'state.drift')
        self.assertIsNone(self.machine('recover', '--inspect')['data']['pending'])
        self.assertEqual(self.machine('self', 'status')['data']['program_root'], str(ENTRY.parent))
        self.assertTrue(self.machine('self', 'install', '--bin-dir', places['bin'], '--dry-run')['would_change'])
        # update inspects this program's own checkout read-only; a dirty or detached checkout is a typed refusal, never the gate.
        code, updated = self.raw('update', '--dry-run')
        self.assertIn(code, (0, 4), updated)
        self.assertNotEqual((updated['error'] or {}).get('code'), 'migration.required')
        self.assertEqual(snapshot(roots.base, roots.base), before)

    def test_v1_machine_refuses_every_non_exempt_command(self):
        self.assert_gate(1)

    def test_v2_machine_refuses_every_non_exempt_command(self):
        self.assert_gate(2)

    def test_retired_journals_are_shown_but_never_replayed(self):
        roots = self.legacy_machine(1)
        state_text = (roots.home / 'state.json').read_text(encoding='utf-8')
        config_text = (roots.home / 'config.json').read_text(encoding='utf-8')
        state, config = json.loads(state_text), json.loads(config_text)
        common = dict(schema_version=state['schema_version'], transaction_id='00000000-0000-4000-8000-000000000000', phase='prepared',
                      base_generation=state['generation'], selected=[str(roots.project)], links=[], manifests=[], before_state=state,
                      after_state=state, config=config, before_state_text=state_text, after_state_text=state_text, directories=[])
        clone_text = state['projects'][str(roots.project)]['links']['.claude/skills/alpha']['link_text']
        migration = dict(config_before=config_text, config_after=config_text, source={}, cache=None)
        shared = dict(scope='source', root=str(roots.clone), before='0' * 40, candidate='1' * 40)
        journals = (
            ('migration', dict(common, schema_version=3, operation='migrate', files=[], migration=dict(config_before=config_text, config_after=config_text, source={}))),
            # Only doctor.migrate may record a migration or the machine configuration; on any other operation both stay retired.
            ('migration', dict(common, schema_version=3, operation='upgrade', files=[], migration=migration)),
            ('migration', dict(common, schema_version=3, operation='apply', files=[dict(root=str(roots.home), role='machine_config', before=config_text, after=config_text)])),
            ('shared_checkout_update', dict(common, operation='upgrade', git=shared)),
            ('shared_checkout_update', dict(common, schema_version=3, operation='doctor.migrate', files=[], migration=migration, git=shared)),
            ('legacy_ownership', dict(common, operation='apply')),
            # A plain journal replaying a live-checkout link text is legacy ownership, never a replay.
            ('legacy_ownership', dict(common, operation='apply', links=[dict(root=str(roots.project), relative='.claude/skills/alpha', skill='alpha', target='claude', before=clone_text, after=clone_text)])),
        )
        for reason, journal in journals:
            with self.subTest(retired=reason, operation=journal['operation']):
                write_json(roots.home / 'pending.json', journal)
                before = snapshot(roots.base, roots.base)
                inspected = self.machine('recover', '--inspect')['data']
                self.assertEqual((inspected['pending'], inspected['retired']), (journal, reason))
                for mode in ('--complete', '--rollback'):
                    refused = self.machine('recover', mode, code=8)['error']
                    self.assertEqual((refused['code'], refused['details']['retired']), ('recovery.conflict', reason))
                self.assertEqual(snapshot(roots.base, roots.base), before)


class LegacyConsumerRemediation(LegacyFixture):
    """A v3 machine still holding a mode-less record: every consumer-level migration.required names the doctor remediation argv."""

    def test_consumer_refusals_carry_the_doctor_remediation(self):
        roots = self.legacy_machine(1, straggler_skills=None)
        (roots.home / 'config.json').unlink()
        self.machine('tap', 'add', TAP, roots.upstream)
        tapped = roots.base / 'tap project'
        tapped.mkdir()
        git(tapped, 'init', '-q', '-b', 'main')
        self.machine('install', 'alpha', '--project', tapped)
        # The legacy project keeps its mode-less record and clone links but now declares the same pinned v2 selection.
        for name in ('.mask.json', '.mask.lock.json'):
            (roots.project / name).write_bytes((tapped / name).read_bytes())
        before = snapshot(roots.base, roots.base)
        for args in (('upgrade',), ('apply', '--project', roots.project),
                     ('source', 'dev-link', TAP + '/alpha', '--project', roots.project, '--to-pinned')):
            with self.subTest(args=args):
                error = self.machine(*args, code=4)['error']
                self.assertEqual((error['code'], error['details']['remediation']), ('migration.required', REMEDIATION))
        consumers = self.machine('inventory', '--project', roots.project)['data']['consumers']
        self.assertEqual([(item['error']['code'], item['error']['details']['remediation']) for item in consumers], [('migration.required', REMEDIATION)])
        self.assertEqual(snapshot(roots.base, roots.base), before)
