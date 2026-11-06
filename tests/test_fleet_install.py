"""Exact rollout contributions use the device's ordinary subprocess RPC and journal."""
import mask_core as core
import mask_fleet_copy as curated
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

    def apply_profile(self, profile, sequence, *, alias='personal'):
        self.generation = rpc.state_at(self.device_home)['generation']
        payload = dict(scope=alias, profile=profile)
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

    def test_mapped_project_profile_leaves_personal_controls_unchanged(self):
        self.add_package('beta')
        project = self.base / 'mapped project'
        project.mkdir()
        self.git(project, 'init', '-q')
        self.cli(self.device_home, 'register', project, '--offline', env=self.env)
        self.policy['epoch'] = 2
        grant = self.policy['scopes']['personal']['sources']
        self.policy['scopes']['work'] = dict(scope='project', root=str(project), sources=grant, rollout=True)
        self.authorize(self.policy)
        personal = (self.device_home / 'user.json').read_bytes()
        declaration = (project / '.mask.json').read_bytes()
        result = self.apply_profile(self.profile('fixture/beta'), 2, alias='work')
        self.assertEqual(result['result']['scope_type'], 'project')
        self.assertTrue((project / '.agents/skills/beta').is_symlink())
        self.assertFalse((self.personal / '.agents/skills/beta').exists())
        self.assertEqual((project / '.mask.json').read_bytes(), declaration)
        self.assertEqual((self.device_home / 'user.json').read_bytes(), personal)

    def test_curated_publication_resumes_after_source_only_effect(self):
        authoring = self.base / 'curated authoring'
        repository = self.base / 'curated.git'
        authoring.mkdir()
        repository.mkdir()
        self.git(repository, 'init', '--bare', '-q')
        self.git(authoring, 'init', '-q', '-b', 'main')
        self.git(authoring, 'config', 'user.name', 'Fixture')
        self.git(authoring, 'config', 'user.email', 'fixture@example.invalid')
        seed = authoring / 'skills/seed'
        seed.mkdir(parents=True)
        (seed / 'SKILL.md').write_bytes(b'---\nname: seed\ndescription: Fixture\n---\n')
        self.git(authoring, 'add', 'skills')
        self.git(authoring, 'commit', '-qm', 'Fixture curated parent')
        self.git(authoring, 'remote', 'add', 'origin', str(repository))
        self.git(authoring, 'push', '-q', 'origin', 'main')
        self.cli(self.controller_home, 'tap', 'curated', repository, '--checkout', authoring, env=self.env)
        (authoring / 'unrelated.txt').write_text('staged fixture work')
        self.git(authoring, 'add', 'unrelated.txt')
        index = self.git(authoring, 'ls-files', '--stage')
        config = core.config(core.read_json(self.controller_home / 'config.json'))
        upstream = rollout.resolve_input(self.controller_home, config, 'fixture/alpha')
        effects = []
        for label, expected in [('first', 'published'), ('resume', 'already_published')]:
            scratch = self.base / label
            scratch.mkdir()
            row, effect, endpoint, observed = curated.prepare(self.controller_home, config, upstream, 'curated', scratch)
            self.assertEqual(curated.publish(config, scratch, row, effect, endpoint, observed), expected)
            effects.append(effect)
        self.assertEqual(effects[0], effects[1])
        self.assertEqual(self.git(authoring, 'ls-files', '--stage'), index)
        self.assertFalse((authoring / 'skills/alpha').exists())
        self.assertFalse((self.controller_home / 'fleet' / 'control.json').exists())
