"""Public fleet tap commands and delegation across signed fixture RPC."""
import mask_core as c
import mask_fleet as fleet
import mask_rpc as rpc
from tests.public_support import ENTRY
from tests import test_fleet_maintenance as fixture
from tests.test_fleet_rpc import FleetRpcFixture

URI = 'ssh://git@fleet-fixture.invalid/central.git'
NAMESPACE = 'https://github.com/fixture-team'


class FleetTapTests(FleetRpcFixture):
    set_peer = fixture.FleetMaintenanceTests.set_peer
    public = fixture.FleetMaintenanceTests.public
    approve = fixture.FleetMaintenanceTests.approve

    def setUp(self):
        super().setUp()
        self.policy['epoch'] += 1
        self.policy['actions'] += [*fleet.TAP_ACTIONS, 'upgrade-inspect', 'upgrade-apply']
        self.policy['scopes']['personal'].update(rollout=True, upgrade=True)
        project = self.base / 'project'
        self.git(self.base, 'init', '-q', str(project))
        self.cli(self.device_home, 'register', '--project', project, '--offline', env=self.env)
        self.policy['scopes']['work'] = dict(scope='project', root=str(project), sources={}, rollout=True)
        self.policy['tap_management'] = dict(repositories=[URI], namespaces=[NAMESPACE], scopes=['personal'])
        self.authorize(self.policy)
        self.set_peer('laptop', self.device, self.policy, self.device_home, ENTRY)

    def review(self, *args):
        return self.public(*args, '--dry-run')['data']

    def apply(self, preview, *args, **options):
        return self.public(*args, '--approve-plan', preview['plan_hash'], **options)['data']

    def tap(self, home, name):
        return self.cli(home, 'tap', env=self.env)['data']['sources'].get(name)

    def second_device(self):
        home = self.base / 'second device'
        identity = self.cli(home, 'fleet', 'device', 'init', 'desktop', '--signing-key',
                            self.key('desktop signing key'))['data']['identity']
        grant = dict(self.policy['tap_management'], scopes=[])
        policy = dict(self.policy, scopes={}, tap_management=grant)
        self.approve(home, policy)
        self.set_peer('desktop', identity, policy, home, ENTRY)
        return home

    def test_public_add_fetch_install_upgrade_and_remove(self):
        args = ('tap', 'team', URI)
        before = fleet.descriptor(self.device_home)
        preview = self.review(*args)
        self.assertEqual(preview['plan']['targets'][0]['observation']['before'], None)
        self.assertEqual(preview['plan']['controller']['after']['repository'], URI)
        self.assertFalse((self.controller_home / 'config.json').exists())
        self.assertIsNone(self.tap(self.device_home, 'team'))
        self.public(*args, code=4)
        data = self.apply(preview, *args)
        self.assertTrue(data['complete'])
        self.assertTrue(data['device_results'][0]['receipt']['changed'])
        self.assertEqual(before, fleet.descriptor(self.device_home))
        self.assertEqual(self.tap(self.device_home, 'fixture')['repository'],
                         self.policy['scopes']['personal']['sources']['fixture']['repository'])
        self.assertEqual(list(self.public('tap')['data']['device_results'][0]['observation']['taps']), ['team'])
        self.assertFalse((self.controller_home / 'sources').exists())

        package = self.source / 'skills/beta'
        package.mkdir()
        skill = package / 'SKILL.md'
        skill.write_bytes(b'---\nname: beta\ndescription: Fixture skill\n---\n\nFleet tap fixture.\n')
        self.git(self.source, 'add', 'skills')
        self.git(self.source, 'commit', '-qm', 'add beta')
        self.git(self.source, 'push', '-q', str(self.remote), 'main')
        self.cli(self.controller_home, 'tap', 'fetch', 'team', env=self.env)
        control = self.base / 'desired.git'
        self.git(self.base, 'init', '--bare', str(control))
        command = ('fleet', 'control', 'configure', control)
        approval = self.cli(self.controller_home, *command, '--dry-run')['data']['plan_hash']
        self.cli(self.controller_home, *command, '--approve-plan', approval)

        install = ('install', 'team/beta')
        outside = self.review(*install, '--project-alias', 'work')
        self.assertEqual(outside['targets'][0]['blocked'], 'fleet.source_denied')
        forward = self.review(*install, '--forward')
        self.assertEqual(forward['targets'][0]['blocked'], 'fleet.artifact_forward_denied')
        preview = self.review(*install)
        applied = self.apply(preview, *install)
        self.assertTrue(applied['installed_everywhere'])
        self.assertTrue((self.personal / '.agents/skills/beta').is_symlink())

        denied = self.review('untap', 'team')
        self.assertEqual(denied['plan']['targets'][0]['reason'], 'source.referenced')
        self.assertFalse(self.apply(denied, 'untap', 'team', code=9)['complete'])
        self.assertIsNotNone(self.tap(self.controller_home, 'team'))

        # Both the locally selected and fleet profile upgrades must retain their
        # distinct authority. The controller needs both catalogs for resolution.
        static = self.policy['scopes']['personal']['sources']['fixture']['repository']
        self.cli(self.controller_home, 'tap', 'fixture', static, env=self.env)
        self.cli(self.controller_home, 'tap', 'fetch', 'fixture', env=self.env)
        skill.write_bytes(skill.read_bytes() + b'\nNew revision.\n')
        self.git(self.source, 'commit', '-qam', 'new beta')
        self.git(self.source, 'push', '-q', str(self.remote), 'main')
        self.cli(self.controller_home, 'tap', 'fetch', 'team', env=self.env)
        upgrade = self.apply(self.review('upgrade'), 'upgrade')
        self.assertTrue(upgrade['complete'])
        profiles = rpc.state_at(self.device_home)['user']['profiles']
        [profile] = profiles.values()
        self.assertEqual(profile['lock']['packages'][0]['commit'], self.git(self.source, 'rev-parse', 'HEAD'))

        remove = ('remove', 'team/beta', '--scope', 'user', '--device', 'laptop')
        self.assertTrue(self.apply(self.review(*remove), *remove)['complete'])
        subset = ('untap', 'team', '--device', 'laptop')
        self.assertTrue(self.apply(self.review(*subset), *subset)['complete'])
        self.assertIsNone(self.tap(self.device_home, 'team'))
        self.assertIsNotNone(self.tap(self.controller_home, 'team'))
        self.assertTrue(self.apply(self.review('untap', 'team'), 'untap', 'team')['complete'])
        self.assertIsNone(self.tap(self.controller_home, 'team'))
        self.assertTrue(self.link.is_symlink())

    def test_namespace_and_local_ownership_keep_other_peers_independent(self):
        desktop = self.second_device()
        url = NAMESPACE + '/skills.git'
        self.cli(desktop, 'tap', 'team', 'git@github.com:fixture-team/skills.git', '--pin-transport')
        existing = self.tap(desktop, 'team')
        command = ('tap', 'team', url)
        plan = self.review(*command)
        desktop_row, laptop_row = plan['plan']['targets']
        self.assertEqual((desktop_row['name'], desktop_row['reason']), ('desktop', 'fleet.tap_not_owned'))
        self.assertEqual((laptop_row['name'], laptop_row['status']), ('laptop', 'planned'))
        data = self.apply(plan, *command, code=9)
        self.assertFalse(data['complete'])
        self.assertEqual(data['controller_result']['status'], 'applied_verified')
        self.assertEqual(self.tap(desktop, 'team'), existing)
        self.assertEqual(self.tap(self.device_home, 'team')['repository'], url)

        laptop = ('--device', 'laptop')
        self.cli(self.device_home, 'tap', 'transport', 'team', 'git@github.com:fixture-team/skills.git')
        pinned = self.tap(self.device_home, 'team')
        self.assertEqual(pinned['transport_policy'], 'pinned')
        self.assertTrue(self.apply(self.review(*command, *laptop), *command, *laptop)['complete'])
        self.assertEqual(self.tap(self.device_home, 'team'), pinned)
        other = ('tap', 'another', NAMESPACE + '/another.git', *laptop)
        self.assertTrue(self.apply(self.review(*other), *other)['complete'])
        for repository in (NAMESPACE + '-lookalike/skills.git', 'https://github.com.evil.invalid/fixture-team/skills.git'):
            denied = self.review('tap', 'escape', repository, *laptop)['plan']['targets'][0]
            self.assertEqual(denied['reason'], 'fleet.tap_repository_denied')
        self.public('tap', 'escape', 'https://fixture@github.com/fixture-team/skills.git', '--dry-run', code=3)
        self.public('tap', 'escape', self.remote.as_uri(), '--dry-run', code=4)
        self.assertIsNone(self.tap(self.device_home, 'escape'))
        untouched = self.review('untap', 'team', '--device', 'desktop')
        self.assertEqual(untouched['plan']['targets'][0]['reason'], 'fleet.tap_not_owned')
        self.assertEqual(self.tap(desktop, 'team'), existing)

    def test_offline_then_lost_ack_and_revocation_use_exact_targets(self):
        desktop = self.second_device()
        args = ('tap', 'team', URI)
        preview = self.public(*args, '--dry-run', offline='desktop')['data']
        self.assertEqual(preview['plan']['targets'][0]['status'], 'offline')
        partial = self.apply(preview, *args, offline='desktop', drop='tap-apply', code=9)
        self.assertEqual([row['status'] for row in partial['device_results']], ['offline', 'unknown'])
        self.assertFalse((desktop / 'config.json').exists())
        self.assertFalse((self.controller_home / 'config.json').exists())
        self.assertIsNotNone(self.tap(self.device_home, 'team'))
        verified = self.apply(preview, *args, code=9)
        self.assertEqual([row['status'] for row in verified['device_results']], ['offline', 'applied_verified'])
        self.assertEqual(verified['controller_result']['status'], 'applied_verified')
        self.assertFalse((desktop / 'config.json').exists())
        narrowed = (*args, '--device', 'desktop')
        self.assertTrue(self.apply(self.review(*narrowed), *narrowed)['complete'])
        self.assertIsNotNone(self.tap(desktop, 'team'))

        revoke = ('fleet', 'device', 'revoke-controller')
        preview = self.cli(desktop, *revoke, '--dry-run')['data']['plan_hash']
        self.cli(desktop, *revoke, '--approve-plan', preview)
        result = self.public('tap', code=9)['data']['device_results']
        self.assertEqual((result[0]['status'], result[0]['reason']), ('blocked', 'fleet.controller_revoked'))
        self.assertEqual(result[1]['status'], 'observed')

    def test_committed_marker_recovers_receipt_and_rejects_stale_apply(self):
        args = ('tap', 'team', URI)
        preview = self.review(*args)
        row = preview['plan']['targets'][0]
        stale = self.packet('tap-apply', row['request'])
        changed_request = dict(row['request'], change=dict(row['request']['change'], ref='elsewhere'))
        self.send(self.packet('tap-apply', changed_request), error='plan.stale')
        partial = self.apply(preview, *args, fail_tap_receipt='laptop', code=9)
        self.assertEqual(partial['device_results'][0]['status'], 'unknown')
        self.assertIsNotNone(self.tap(self.device_home, 'team'))
        self.assertFalse((self.device_home / 'fleet' / 'tap-results').exists())
        self.assertTrue(self.apply(preview, *args)['complete'])
        self.assertTrue((self.device_home / 'fleet' / 'tap-results').is_dir())
        self.assertTrue(self.apply(self.review('untap', 'team'), 'untap', 'team')['complete'])
        self.send(stale, error='plan.stale')
        self.assertIsNone(self.tap(self.device_home, 'team'))
