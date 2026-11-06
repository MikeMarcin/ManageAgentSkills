"""Public layered personal selections and explicit profile approval."""
import shutil

from tests.test_profiles import ProfileFixture
from tests.support import TAP


class ProfileContributionTests(ProfileFixture):
    def subscribe(self, profile, *options, **kwargs):
        return self.call('profile', 'subscribe', profile, '--user', '--name', 'shared', *options, **kwargs)

    def test_frozen_contribution_preserves_local_positive_agents_and_offline_revision(self):
        self.install_user('alpha', '--agent', 'claude')
        self.install_user('beta')
        profile = self.export()
        home, personal, env = self.other_machine()
        env.update(HOME=str(personal), USERPROFILE=str(personal))
        self.approve(env=env)
        self.install_user('alpha', '--agent', 'codex', env=env)
        local = (home / 'user.json').read_bytes(), (home / 'user.lock.json').read_bytes()
        preview = self.subscribe(profile, '--dry-run', env=env)
        receipt = self.subscribe(profile, '--approve-plan', preview['data']['plan_hash'], env=env)
        self.assertEqual(receipt['data']['profiles'][0]['freshness'], 'last_approved_offline')
        self.assertEqual((home / 'user.json').read_bytes(), local[0])
        for link in ('.agents/skills/alpha', '.claude/skills/alpha', '.agents/skills/beta', '.claude/skills/beta'):
            self.assertTrue((personal / link).is_symlink(), link)
        self.assertFalse(self.subscribe(profile, '--offline', env=env)['changed'])
        plain = self.base / 'local-only'
        effective = self.base / 'effective'
        self.call('user', 'export', '--output', plain, env=env)
        self.call('user', 'export', '--output', effective, '--effective', env=env)
        self.assertEqual([row['id'] for row in self.document(plain / 'selection.json')['skills']], ['alpha'])
        flat = self.document(effective / 'selection.json')
        self.assertEqual([row['id'] for row in flat['skills']], ['alpha', 'beta'])
        self.assertEqual(flat['skills'][0]['agents'], ['claude', 'codex'])
        self.assertIn('flattened', (effective / 'README.md').read_text(encoding='utf-8'))
        shutil.rmtree(profile)
        self.call('repair', '--user', '--offline', env=env)
        self.call('status', '--user', '--check', env=env)
        listing = self.call('list', '--user', env=env)['data']
        self.assertEqual(listing['links'], {'expected': 4, 'linked': 4})
        self.assertEqual([row['skill'] for row in listing['skills']], [TAP + '/alpha', TAP + '/beta'])
        self.call('profile', 'unsubscribe', 'shared', '--user', env=env)
        self.assertEqual((home / 'user.json').read_bytes(), local[0])
        self.assertEqual((home / 'user.lock.json').read_bytes(), local[1])
        self.assertTrue((personal / '.agents/skills/alpha').is_symlink())
        self.assertFalse((personal / '.claude/skills/alpha').exists())
        self.assertFalse((personal / '.agents/skills/beta').exists())

    def test_subscription_refuses_unapproved_and_incompatible_exact_artifacts(self):
        self.install_user('alpha')
        profile = self.export()
        home, personal, env = self.other_machine()
        env.update(HOME=str(personal), USERPROFILE=str(personal))
        self.call('tap', 'other', 'ssh://git@fixture.invalid/Other.git', '--pin-transport', env=env)
        self.assertEqual(self.subscribe(profile, '--offline', code=4, env=env)['error']['code'], 'source.unknown')
        self.approve(env=env)
        before = (home / 'state.json').read_bytes()
        self.assertEqual(self.subscribe(profile, '--offline', code=4, env=env)['error']['code'], 'artifact.unavailable')
        self.assertEqual((home / 'state.json').read_bytes(), before)
        self.assertFalse((home / 'user.json').exists())
        skill = self.source / 'skills/alpha/SKILL.md'
        skill.write_bytes(skill.read_bytes() + b'\nNew payload.\n')
        self.publish()
        self.git(self.base, '--git-dir=' + env['MASK_TEST_UPLOAD_PACK'], 'fetch', str(self.upstream), '+refs/heads/main:refs/heads/main')
        self.install_user('alpha', env=env)
        local = (home / 'user.json').read_bytes(), (home / 'user.lock.json').read_bytes(), (home / 'state.json').read_bytes()
        error = self.subscribe(profile, '--offline', code=4, env=env)['error']
        self.assertEqual(error['code'], 'selection.conflict')
        origins = {row['origin'] for row in error['details']['conflicts'][0]['resolutions']}
        self.assertEqual(origins, {'local', 'profile:shared'})
        self.assertEqual(tuple((home / name).read_bytes() for name in ('user.json', 'user.lock.json', 'state.json')), local)

    def test_subscribe_bootstraps_and_local_replace_preserves_subscription(self):
        self.install_user('beta')
        profile = self.export()
        home, personal, env = self.other_machine()
        env.update(HOME=str(personal), USERPROFILE=str(personal))
        self.approve(env=env)
        self.subscribe(profile, env=env)
        self.assertEqual(self.document(home / 'user.json')['skills'], [])
        self.assertTrue((personal / '.agents/skills/beta').is_symlink())
        self.assertEqual(self.call('untap', TAP, code=4, env=env)['error']['code'], 'source.referenced')
        self.install_user('alpha')
        self.call('uninstall', 'beta', '--user')
        local_profile = self.export('one-local-skill')
        self.call('user', 'import', local_profile, '--replace', env=env)
        self.assertEqual([row['id'] for row in self.document(home / 'user.json')['skills']], ['alpha'])
        self.assertTrue((personal / '.agents/skills/beta').is_symlink())
        self.call('profile', 'unsubscribe', 'shared', '--user', env=env)
        self.assertFalse((personal / '.agents/skills/beta').exists())
        self.assertTrue((personal / '.agents/skills/alpha').is_symlink())
