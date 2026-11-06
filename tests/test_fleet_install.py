"""Exact rollout contributions use the device's ordinary subprocess RPC and journal."""
import mask_core as core
import mask_fleet as fleet
import mask_rollout as rollout
import mask_rpc as rpc
from tests.test_fleet_rpc import FleetRpcFixture


class FleetInstallTests(FleetRpcFixture):
    def setUp(self):
        super().setUp()
        self.cli(self.controller_home, 'tap', 'fixture', self.policy['scopes']['personal']['sources']['fixture']['repository'],
                 '--pin-transport', env=self.env)
        self.cli(self.controller_home, 'tap', 'fetch', 'fixture', env=self.env)
        self.config = core.config(core.read_json(self.controller_home / 'config.json'))

    def grant_rollout(self):
        self.policy['epoch'] = 2
        self.policy['scopes']['personal']['rollout'] = True
        self.authorize(self.policy)

    def profile(self, name='fixture/alpha', previous=None, action='install'):
        row = rollout.resolve_input(self.controller_home, self.config, name) if action != 'remove' else None
        return rollout.contribution(previous, name, action, row, self.config)[0]

    def add_package(self, name):
        path = self.source / 'skills' / name
        path.mkdir()
        (path / 'SKILL.md').write_bytes(f'---\nname: {name}\ndescription: Fixture\n---\n\nExact.\n'.encode())
        self.git(self.source, 'add', 'skills')
        self.git(self.source, 'commit', '-qm', name)
        self.git(self.source, 'push', '-q', str(self.remote), 'main')
        self.cli(self.controller_home, 'tap', 'fetch', 'fixture', env=self.env)

    def apply_profile(self, profile, sequence):
        self.generation = rpc.state_at(self.device_home)['generation']
        payload = dict(scope='personal', profile=profile)
        revision = core.digest(dict(sequence=sequence))
        make = lambda action, data: rpc.request(self.signer, self.device, self.policy, action, data,
                                               revision=revision, sequence=sequence, generation=self.generation)
        plan = self.send(make('prepare', payload))['result']['plan']
        return self.send(make('apply', dict(payload, plan=plan)))

    def test_explicit_grant_and_local_pin_preserved_through_apply_and_remove(self):
        self.add_package('beta')
        profile = self.profile('fixture/beta')
        self.send(self.packet('prepare', dict(scope='personal', profile=profile)), error='fleet.rollout_denied')
        self.grant_rollout()
        self.cli(self.device_home, 'pin', 'fixture/alpha', '--user', env=self.env)
        before = (self.device_home / 'user.json').read_bytes()
        applied = self.apply_profile(profile, 2)
        self.assertEqual(applied['result']['contribution'], profile['revision'])
        self.assertEqual(applied['result']['host_load'], 'not_verified')
        beta = self.personal / '.agents/skills/beta'
        self.assertTrue(beta.is_symlink())
        self.assertEqual((self.device_home / 'user.json').read_bytes(), before)
        self.assertEqual(self.apply_profile(None, 3)['status'], 'applied_verified')
        self.assertFalse(beta.exists())
        self.assertTrue(self.link.is_symlink())
        self.assertEqual((self.device_home / 'user.json').read_bytes(), before)

    def test_signed_generation_and_exact_local_conflict_block_instead_of_overwrite(self):
        self.grant_rollout()
        with (self.source / 'skills/alpha/SKILL.md').open('ab') as file:
            file.write(b'New exact bytes for a separately held local skill.\n')
        self.add_package('beta')
        before = self.link.resolve()
        self.send(self.packet('prepare', dict(scope='personal', profile=self.profile())), error='selection.conflict')
        self.assertEqual(self.link.resolve(), before)
        self.assertFalse((self.device_home / 'pending.json').exists())
