"""Granted-source setup through public maintenance CLI and real signed subprocess RPC.

Only the SSH delivery is replaced; source fetches use disposable local bare Git.
"""
import json
from pathlib import Path
import sys
import time

import mask_core as c
import mask_fleet as fleet
import mask_rpc as rpc
from tests.public_support import ENTRY
from tests import test_fleet_maintenance as maintenance_fixture
from tests.test_fleet_rpc import FleetRpcFixture, URI


class FleetSetupTests(FleetRpcFixture):
    public = maintenance_fixture.FleetMaintenanceTests.public
    set_peer = maintenance_fixture.FleetMaintenanceTests.set_peer
    approve = maintenance_fixture.FleetMaintenanceTests.approve
    init_git = maintenance_fixture.FleetMaintenanceTests.init_git
    identity = maintenance_fixture.FleetMaintenanceTests.identity

    def setUp(self):
        super().setUp()
        self.cli(self.controller_home, 'tap', 'fixture', URI, '--pin-transport', env=self.env)
        self.cli(self.controller_home, 'tap', 'fetch', 'fixture', env=self.env)
        self.policy['epoch'] += 1
        self.policy['actions'] += ['upgrade-inspect', 'upgrade-apply']
        self.policy['scopes']['personal']['upgrade'] = True
        self.bind()
        self.context = self.personal / 'context.json'
        self.context.write_text('{"fixture": 1}\n', encoding='utf-8')
        self.sentinel = self.base / 'launches.txt'
        self.role = self.personal / '.codex/agents/fixture-worker.toml'
        self.lock = self.personal / '.mask/generated/alpha/native-roles.lock.json'
        self.package = self.source / 'skills/alpha'

    def bind(self):
        self.authorize(self.policy)
        self.set_peer('laptop', self.device, self.policy, self.device_home, ENTRY)

    def publish_setup(self, *, fail=False, static=False):
        contract = dict(inputs=[dict(id='context', path='context.json', kind='json', required=True)],
                        native_roles=[dict(agent='codex', name='fixture-worker', setup='prepare-roles')],
                        setup=[dict(id='prepare-roles', entrypoint='generate.py', inputs=['context'],
                                    package_inputs=['generate.py'], parameters={}, timeout_seconds=30,
                                    effects='staged-native-roles')])
        if static:
            content = b'name = "fixture-worker"\nmodel = "fixture-static-do-not-run"\n'
            (self.package / 'role.toml').write_bytes(content)
            contract.pop('setup')
            contract['native_roles'][0] = dict(agent='codex', name='fixture-worker',
                                              asset=dict(path='role.toml', sha256=c.digest(content)[7:]))
        else:
            script = '''import argparse, json
from pathlib import Path
parser = argparse.ArgumentParser()
for name in ('repo-root', 'output-root', 'request-file'):
    parser.add_argument('--' + name, type=Path, required=True)
args = parser.parse_args()
request = json.loads(args.request_file.read_text())
assert request['schema'] == 'mask.setup-request.v1'
assert all(len(row['sha256']) == 64 for row in request['inputs'])
with Path(SENTINEL).open('a') as stream:
    stream.write('launched\\n')
if FAIL:
    raise SystemExit(7)
for role in request['native_roles']:
    directory = args.output_root / role['agent']
    directory.mkdir(exist_ok=True)
    (directory / (role['name'] + '.toml')).write_text('name = "fixture-worker"\\nmodel = "fixture-generated-do-not-run"\\n')
'''.replace('SENTINEL', repr(str(self.sentinel))).replace('FAIL', repr(fail))
            (self.package / 'generate.py').write_text(script, encoding='utf-8')
        descriptor = dict(schema_version=1, **contract, scopes=dict(user=contract))
        (self.package / 'mask-workflow.json').write_text(c.text_json(descriptor), encoding='utf-8')
        self.git(self.source, 'add', 'skills')
        self.git(self.source, 'commit', '-qm', 'reviewed workflow candidate')
        self.git(self.source, 'push', '-q', str(self.remote), 'main')
        self.cli(self.controller_home, 'tap', 'fetch', 'fixture', env=self.env)
        return self.git(self.source, 'rev-parse', 'HEAD')

    def preview(self):
        return self.public('upgrade', '--scope', 'user', '--dry-run')['data']

    def apply(self, preview, *, code=0, drop=None):
        return self.public('upgrade', '--scope', 'user', '--approve-plan', preview['plan_hash'], code=code, drop=drop)

    def launches(self):
        return len(self.sentinel.read_text().splitlines()) if self.sentinel.exists() else 0

    def test_granted_setup_is_disclosed_signed_and_idempotent_with_backups(self):
        candidate = self.publish_setup()
        self.role.parent.mkdir(parents=True)
        previous = 'name = "fixture-worker"\nmodel = "local-role-do-not-run"\n'
        self.role.write_text(previous, encoding='utf-8')
        before_state = (self.device_home / 'state.json').read_bytes()
        before_link = self.link.readlink()
        preview = self.preview()
        [row] = preview['plan']['targets']
        self.assertEqual(row['status'], 'planned', row)
        self.assertEqual(row['request']['task'], row['task']['plan_hash'])
        [setup] = row['task']['setup']
        self.assertEqual(setup['coordinate'], 'fixture/alpha')
        self.assertEqual(setup['interpreter']['executable'], sys.executable)
        self.assertEqual(setup['inputs'][0]['sha256'], c.digest(self.context.read_bytes())[7:])
        replacements = [action for action in row['task']['actions'] if action['kind'] == 'file.backup_replace']
        self.assertEqual([action['path'] for action in replacements], [str(self.role)])
        self.assertEqual(replacements[0]['before_sha256'], c.digest(previous.encode())[7:])
        self.assertEqual(self.launches(), 0)
        self.assertEqual(self.role.read_text(), previous)
        self.assertEqual((self.device_home / 'state.json').read_bytes(), before_state)
        self.assertEqual(self.link.readlink(), before_link)
        self.assertFalse(self.lock.exists())
        result = self.apply(preview, drop='upgrade-apply', code=9)
        self.assertEqual(result['data']['device_results'][0]['status'], 'unknown')
        self.assertEqual(self.launches(), 1)
        replay = self.apply(preview)['data']
        self.assertTrue(replay['complete'])
        [row] = replay['device_results']
        self.assertEqual(row['receipt']['setup']['actions'][0]['state'], 'published')
        self.assertEqual(row['receipt']['host_load'], 'not_verified')
        self.assertEqual(json.loads(self.lock.read_text())['coordinate'], 'fixture/alpha')
        self.assertIn('fixture-generated-do-not-run', self.role.read_text())
        backups = list((self.device_home / 'backups').rglob('fixture-worker.toml'))
        self.assertEqual([path.read_text() for path in backups], [previous])
        state = json.loads((self.device_home / 'state.json').read_text())
        self.assertEqual(state['user']['last_lock']['packages'][0]['commit'], candidate)
        self.assertEqual(self.launches(), 1)
        current = self.preview()
        self.assertEqual(current['plan']['targets'][0]['task']['setup'], [])
        self.apply(current)
        self.assertEqual(self.launches(), 1)

    def test_invalid_and_stale_inputs_or_destinations_refuse_before_consumer_writes(self):
        self.publish_setup()
        baseline = (self.device_home / 'state.json').read_bytes(), self.link.readlink()
        for content in ('{', None):
            with self.subTest(content=content):
                if content is None:
                    self.context.unlink()
                else:
                    self.context.write_text(content)
                [row] = self.preview()['plan']['targets']
                self.assertEqual((row['status'], row['reason']), ('blocked', 'workflow.incomplete'))
                self.assertNotIn('request', row)
                self.assertEqual(self.launches(), 0)
        self.context.write_text('{"fixture": 1}\n')
        preview = self.preview()
        self.context.write_text('{"fixture": 2}\n')
        self.send(self.packet('upgrade-apply', preview['plan']['targets'][0]['request']), error='plan.stale')
        refused = self.apply(preview, code=4)
        self.assertEqual(refused['error']['code'], 'plan.stale')
        self.assertEqual(self.launches(), 0)
        self.context.write_text('{"fixture": 1}\n')
        preview = self.preview()
        self.role.parent.mkdir(parents=True)
        self.role.write_text('name = "fixture-worker"\nmodel = "concurrent"\n')
        self.send(self.packet('upgrade-apply', preview['plan']['targets'][0]['request']), error='plan.stale')
        refused = self.apply(preview, code=4)
        self.assertEqual(refused['error']['code'], 'plan.stale')
        self.assertEqual((self.device_home / 'state.json').read_bytes(), baseline[0])
        self.assertEqual(self.link.readlink(), baseline[1])
        self.assertFalse(self.lock.exists())
        self.assertEqual(self.launches(), 0)

    def test_source_scope_action_and_signed_task_authority_remain_required(self):
        self.publish_setup()
        preview = self.preview()
        [row] = preview['plan']['targets']
        payload = dict(row['request'])
        unreviewed = dict(payload)
        unreviewed.pop('task')
        self.send(self.packet('upgrade-apply', unreviewed), error='fleet.local_setup_required')
        self.send(self.packet('upgrade-apply', dict(payload, task=c.digest(b'tampered task'))), error='plan.stale')
        unsigned = self.packet('upgrade-apply', payload)
        unsigned['intent']['payload']['task'] = c.digest(b'unsigned tamper')
        self.send(unsigned, error='fleet.signature_invalid')
        self.send(self.packet('upgrade-apply', payload, expires=int(time.time()) - 1), error='fleet.intent_expired')
        for change in ('source', 'repository', 'scope', 'action'):
            with self.subTest(change=change):
                original = json.loads(json.dumps(self.policy))
                self.policy['epoch'] += 1
                scope = self.policy['scopes']['personal']
                if change == 'source':
                    scope['sources'] = {}
                elif change == 'repository':
                    scope['sources']['fixture']['repository'] = 'ssh://git@fleet-fixture.invalid/other.git'
                elif change == 'scope':
                    scope.pop('upgrade')
                else:
                    self.policy['actions'].remove('upgrade-apply')
                if change == 'repository':
                    path = self.base / 'mismatched-policy.json'
                    path.write_text(c.text_json(self.policy))
                    refused = self.cli(self.device_home, 'fleet', 'device', 'authorize', '--policy', path, '--dry-run', code=4)
                    self.assertEqual(refused['error']['code'], 'fleet.source_denied')
                    self.policy = dict(original, epoch=self.policy['epoch'] + 1)
                    self.bind()
                    continue
                self.bind()
                denied = 'fleet.source_denied' if change == 'source' else 'fleet.action_denied' if change == 'action' else 'fleet.upgrade_denied'
                self.send(self.packet('upgrade-apply', payload), error=denied)
                [blocked] = self.preview()['plan']['targets']
                self.assertEqual(blocked['status'], 'blocked')
                self.assertEqual(blocked['reason'], 'fleet.source_denied' if change in ('source', 'repository') else 'fleet.upgrade_denied')
                self.policy = dict(original, epoch=self.policy['epoch'] + 1)
                self.bind()
        self.assertEqual(self.launches(), 0)
        self.assertFalse(self.lock.exists())

    def test_static_role_replacement_uses_backup_without_running_setup(self):
        self.publish_setup(static=True)
        self.role.parent.mkdir(parents=True)
        self.role.write_text('name = "fixture-worker"\nmodel = "local"\n')
        previous = self.role.read_bytes()
        preview = self.preview()
        [row] = preview['plan']['targets']
        self.assertEqual(row['task']['setup'], [])
        self.assertTrue(any(action['kind'] == 'file.backup_replace' for action in row['task']['actions']))
        self.apply(preview)
        self.assertIn('fixture-static-do-not-run', self.role.read_text())
        self.assertEqual([path.read_bytes() for path in (self.device_home / 'backups').rglob('fixture-worker.toml')], [previous])
        self.assertEqual(self.launches(), 0)

    def test_failed_setup_keeps_activation_truthful_and_does_not_replay(self):
        candidate = self.publish_setup(fail=True)
        preview = self.preview()
        result = self.apply(preview, code=9)
        [row] = result['data']['device_results']
        self.assertEqual((row['status'], row['reason']), ('blocked', 'setup.failed'))
        self.assertEqual(self.launches(), 1)

        state = json.loads((self.device_home / 'state.json').read_text())
        self.assertEqual(state['user']['last_lock']['packages'][0]['commit'], candidate)
        self.assertFalse(self.role.exists())
        self.assertFalse(self.lock.exists())
        self.assertFalse((self.device_home / 'pending.json').exists())
        again = self.apply(preview, code=9)
        self.assertEqual(again['data']['device_results'][0]['reason'], 'fleet.setup_outcome_unknown')
        self.assertEqual(self.launches(), 1)

    def test_crashed_setup_requires_ordinary_recovery_and_never_replays(self):
        self.publish_setup()
        preview = self.preview()
        [row] = preview['plan']['targets']
        packet = self.packet('upgrade-apply', row['request'])
        crashed = self.run_rpc(rpc.frame(packet), crash='setup.exited')
        self.assertEqual(crashed.returncode, 91, crashed.stdout + crashed.stderr)
        self.assertEqual(self.launches(), 1)
        pending = json.loads((self.device_home / 'pending.json').read_text())
        self.assertEqual(pending['setup']['phase'], 'launched')
        self.send(packet, error='recovery.required')
        refused = self.cli(self.device_home, 'recover', '--complete', code=8, env=self.env)
        self.assertEqual(refused['error']['code'], 'setup.unverified')
        self.cli(self.device_home, 'recover', '--rollback', env=self.env)
        self.send(packet, error='fleet.setup_outcome_unknown')
        self.assertEqual(self.launches(), 1)
        self.assertFalse(self.role.exists())
        self.assertFalse(self.lock.exists())
        self.assertFalse((self.device_home / 'pending.json').exists())

    def test_combined_contribution_setup_uses_the_same_granted_task(self):
        self.policy['epoch'] += 1
        self.policy['scopes']['personal']['rollout'] = True
        self.bind()
        bare = self.base / 'desired.git'
        self.git(self.base, 'init', '--bare', str(bare))
        args = ('fleet', 'control', 'configure', bare)
        control = self.cli(self.controller_home, *args, '--dry-run')
        self.cli(self.controller_home, *args, '--approve-plan', control['data']['plan_hash'])
        install = self.public('install', 'fixture/alpha', '--dry-run')['data']
        self.public('install', 'fixture/alpha', '--approve-plan', install['plan_hash'])
        candidate = self.publish_setup()
        preview = self.preview()
        [row] = preview['plan']['targets']
        self.assertIn('profile', row['request'])
        self.assertEqual(row['task']['setup'][0]['coordinate'], 'fixture/alpha')
        result = self.apply(preview)['data']
        self.assertTrue(result['complete'])
        state = json.loads((self.device_home / 'state.json').read_text())
        [profile] = state['user']['profiles'].values()
        self.assertEqual(profile['lock']['packages'][0]['commit'], candidate)
        self.assertEqual(state['user']['last_lock']['packages'][0]['commit'], candidate)
        self.assertEqual(self.launches(), 1)

    def test_interrupted_replacement_rolls_back_from_the_ordinary_setup_journal(self):
        self.publish_setup()
        self.role.parent.mkdir(parents=True)
        previous = 'name = "fixture-worker"\nmodel = "preserve-me"\n'
        self.role.write_text(previous)
        [row] = self.preview()['plan']['targets']
        packet = self.packet('upgrade-apply', row['request'])
        crashed = self.run_rpc(rpc.frame(packet), crash='native_role')
        self.assertEqual(crashed.returncode, 91, crashed.stdout + crashed.stderr)
        pending = json.loads((self.device_home / 'pending.json').read_text())
        self.assertEqual(pending['setup']['phase'], 'staged')
        self.assertEqual([path.read_text() for path in (self.device_home / 'backups').rglob('fixture-worker.toml')], [previous])
        self.cli(self.device_home, 'recover', '--rollback', env=self.env)
        self.assertEqual(self.role.read_text(), previous)
        self.assertFalse(self.lock.exists())
        self.send(packet, error='fleet.setup_outcome_unknown')
        self.assertEqual(self.launches(), 1)

    def test_project_setup_precedes_the_canonical_controls_commit(self):
        project = self.base / 'project'
        self.init_git(project)
        self.cli(self.device_home, 'install', 'fixture/alpha', '--project', project, '--no-update', env=self.env)
        (project / 'context.json').write_text('{"project": 1}\n')
        (project / '.gitignore').write_text('.agents/\n.claude/\n.codex/\n.mask/generated/\n')
        for path in ('.mask.json', '.mask.lock.json', 'context.json', '.gitignore'):
            self.git(project, 'add', '-f', path)
        self.git(project, 'commit', '-qm', 'project controls')
        self.policy['epoch'] += 1
        self.policy['scopes']['project'] = dict(scope='project', root=str(project), upgrade=True, commit=True,
                                               sources={'fixture': dict(repository=URI, forward=False)})
        self.bind()
        candidate = self.publish_setup()
        args = ('upgrade', '--project-alias', 'project')
        preview = self.public(*args, '--dry-run')['data']
        [row] = preview['plan']['targets']
        self.assertEqual(row['task']['setup'][0]['scope'], 'project')
        result = self.public(*args, '--approve-plan', preview['plan_hash'])['data']
        [row] = result['device_results']
        self.assertEqual(row['receipt']['commit'], self.git(project, 'rev-parse', 'HEAD'))
        self.assertEqual(self.git(project, 'diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD'), '.mask.lock.json')
        self.assertEqual(json.loads((project / '.mask.lock.json').read_text())['packages'][0]['commit'], candidate)
        self.assertTrue((project / '.codex/agents/fixture-worker.toml').is_file())
        self.assertEqual(self.launches(), 1)

    def test_same_id_in_an_unrelated_profile_cannot_borrow_a_source_grant(self):
        self.cli(self.device_home, 'user', 'set-agents', 'fixture/alpha', 'claude', env=self.env)
        self.publish_setup()
        alternate_home = self.base / 'profile-mask-home'
        alternate_personal = self.base / 'profile-personal'
        alternate_personal.mkdir()
        (alternate_personal / 'context.json').write_text('{}\n')
        environment = dict(self.env, HOME=str(alternate_personal), USERPROFILE=str(alternate_personal))
        # Sort before fixture so the chosen workflow report belongs to this unchanged profile.
        other = 'ssh://git@fleet-fixture.invalid/other.git'
        for home in (self.device_home, alternate_home):
            self.cli(home, 'tap', 'a-other', other, '--pin-transport', env=environment)
            self.cli(home, 'tap', 'fetch', 'a-other', env=environment)
        install = ('install', 'a-other/alpha', '--user', '--agent', 'codex', '--no-update')
        preview = self.cli(alternate_home, *install, '--dry-run', env=environment)
        self.cli(alternate_home, *install, '--approve-plan', preview['data']['plan_hash'], env=environment)
        profile = self.base / 'profile'
        self.cli(alternate_home, 'user', 'export', '--output', profile, env=environment)
        subscribe = ('profile', 'subscribe', profile, '--user', '--name', 'unrelated')
        preview = self.cli(self.device_home, *subscribe, '--dry-run', env=self.env)
        self.cli(self.device_home, *subscribe, '--approve-plan', preview['data']['plan_hash'], env=self.env)
        self.role.unlink()
        self.sentinel.unlink()
        before = (self.device_home / 'state.json').read_bytes()
        [row] = self.preview()['plan']['targets']
        self.assertEqual((row['status'], row['reason']), ('blocked', 'fleet.local_drift'))
        self.assertEqual(self.launches(), 0)
        self.assertFalse(self.role.exists())
        self.assertEqual((self.device_home / 'state.json').read_bytes(), before)
