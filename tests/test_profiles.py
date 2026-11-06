"""Portable personal profiles through the public CLI and native directory links."""
import json
import os
from pathlib import Path
import shlex
import sys

from tests.public_support import PublicFixture
from tests.support import TAP


URI = 'ssh://git@fixture.invalid/AgentSkills.git'


class ProfileFixture(PublicFixture):
    def bootstrap(self):
        self.transport = self.base / 'fixture ssh.py'
        self.transport.write_text(
            'import os, subprocess\n'
            'raise SystemExit(subprocess.call(["git", "upload-pack", os.environ["MASK_TEST_UPLOAD_PACK"]]))\n',
            encoding='utf-8')
        self.approve()

    def environment(self, extra=None):
        # Only the SSH transport is replaced. Git serves real objects from a disposable
        # bare remote. The tap identity and endpoint-rewrite checks remain unchanged.
        env = super().environment()
        env.update(GIT_SSH_COMMAND=shlex.join([Path(sys.executable).as_posix(), self.transport.as_posix()]),
                   GIT_SSH_VARIANT='ssh', MASK_TEST_UPLOAD_PACK=str(self.upstream))
        return dict(env, **(extra or {}))

    def call(self, *args, code=0, **kwargs):
        run = self.raw(*args, '--json', **kwargs)
        self.assertEqual(run.returncode, code, run.stdout + run.stderr)
        self.assertEqual(run.stderr, '')
        return json.loads(run.stdout)

    def approve(self, **kwargs):
        self.call('tap', TAP, URI, '--pin-transport', **kwargs)

    def install_user(self, skill, *options, **kwargs):
        return self.call('install', TAP + '/' + skill, '--user', '--no-update', *options, **kwargs)

    def other_machine(self):
        home = self.base / 'second machine'
        personal = self.base / 'second personal home'
        personal.mkdir()
        upstream = self.base / 'other remote.git'
        self.git(self.base, 'clone', '--bare', str(self.upstream), str(upstream))
        return home, personal, dict(MASK_HOME=str(home), MASK_TEST_UPLOAD_PACK=str(upstream))

    def export(self, name='portable profile', *options):
        profile = self.base / name
        self.call('user', 'export', '--output', profile, *options)
        return profile

    @staticmethod
    def document(path):
        return json.loads(path.read_text(encoding='utf-8'))


class PortableProfileTests(ProfileFixture):
    def test_one_import_apply_acquires_exact_bytes_on_a_new_machine(self):
        self.install_user('alpha')
        profile = self.export()
        home, personal, env = self.other_machine()
        inspected = self.call('profile', 'inspect', profile, env=env)
        self.assertFalse(home.exists())
        self.assertEqual(inspected['data']['lock']['packages'], self.document(self.home / 'user.lock.json')['packages'])
        self.assertEqual(sorted(path.name for path in profile.iterdir()), ['README.md', 'selection.json', 'selection.lock.json'])
        combined = ''.join(path.read_text(encoding='utf-8') for path in profile.iterdir())
        for private in (str(self.home), str(self.personal), str(self.source), str(self.upstream)):
            self.assertNotIn(private, combined)
        self.approve(env=env)
        unavailable = self.call('user', 'import', profile, '--apply', '--offline', '--user-home', personal, env=env, code=4)
        self.assertEqual(unavailable['error']['code'], 'artifact.unavailable')
        self.assertFalse((home / 'user.json').exists())
        result = self.call('user', 'import', profile, '--apply', '--user-home', personal, env=env)
        self.assertTrue(result['changed'])
        self.assertEqual(self.document(home / 'user.lock.json'), inspected['data']['lock'])
        for directory in ('.agents/skills', '.claude/skills'):
            link = personal / directory / 'alpha'
            self.assertTrue(link.is_symlink())
            self.assertEqual((link / 'SKILL.md').read_bytes(), (self.personal / directory / 'alpha/SKILL.md').read_bytes())
            self.assertTrue(link.resolve().is_relative_to(home))
        self.assertFalse(self.call('user', 'import', profile, '--apply', env=env)['changed'])

    def test_replace_and_incremental_respect_local_and_unmanaged_membership(self):
        self.install_user('alpha', '--agent', 'codex')
        profile = self.export()
        home, personal, env = self.other_machine()
        env.update(HOME=str(personal), USERPROFILE=str(personal))
        self.approve(env=env)
        self.install_user('beta', env=env)
        unrelated = personal / '.agents/skills/unmanaged'
        unrelated.mkdir()
        self.call('user', 'import', profile, env=env)
        self.assertEqual([row['id'] for row in self.document(home / 'user.json')['skills']], ['alpha', 'beta'])
        self.assertFalse((personal / '.claude/skills/alpha').exists())
        self.assertTrue((personal / '.claude/skills/beta').is_symlink())
        self.call('user', 'import', profile, '--replace', env=env)
        self.assertFalse((personal / '.claude/skills/beta').exists())
        self.assertTrue(unrelated.is_dir())
        self.assertTrue((personal / '.agents/skills/alpha').is_symlink())

    def test_all_agent_export_freeze_and_stale_import_approval(self):
        self.install_user('alpha')
        self.call('user', 'set-agents', TAP + '/alpha', '--all')
        profile = self.export()
        frozen = self.export('frozen', '--freeze-agents')
        self.assertEqual(self.document(profile / 'selection.json')['skills'][0]['agents'], 'all')
        self.assertEqual(self.document(frozen / 'selection.json')['skills'][0]['agents'], ['claude', 'codex'])
        self.assertEqual(self.document(profile / 'selection.lock.json')['packages'], self.document(frozen / 'selection.lock.json')['packages'])
        home, personal, env = self.other_machine()
        self.approve(env=env)
        self.call('tap', 'fetch', TAP, env=env)
        preview = self.call('user', 'import', profile, '--user-home', personal, '--dry-run', env=env)
        self.assertFalse((home / 'user.json').exists())
        lockfile = profile / 'selection.lock.json'
        lockfile.write_bytes(lockfile.read_bytes() + b'\n')
        stale = self.call('user', 'import', profile, '--user-home', personal, '--approve-plan',
                          preview['data']['plan_hash'], env=env, code=4)
        self.assertEqual(stale['error']['code'], 'plan.stale')
        self.assertFalse((home / 'user.json').exists())

    def test_interrupted_first_import_rolls_back_absent_controls_and_completes_frozen_pair(self):
        self.install_user('alpha')
        profile = self.export()
        home, personal, env = self.other_machine()
        self.approve(env=env)
        self.call('tap', 'fetch', TAP, env=env)
        import subprocess
        script = """import os, sys
import mask, mask_fs
mask_fs.checkpoint = lambda label: os._exit(99) if label == 'manifest' else None
mask.main(sys.argv[1:])
"""
        for mode in ('--rollback', '--complete'):
            run = subprocess.run([sys.executable, '-B', '-c', script, 'user', 'import', str(profile), '--apply',
                                  '--user-home', str(personal), '--json'], cwd=self.entrypoint.parent,
                                 env=self.environment(env), capture_output=True, timeout=60)
            self.assertEqual(run.returncode, 99, run.stdout + run.stderr)
            self.assertTrue((home / 'pending.json').exists())
            self.call('recover', mode, env=env)
            self.assertFalse((home / 'pending.json').exists())
            self.assertEqual((home / 'user.json').exists(), mode == '--complete')
            self.assertEqual((home / 'user.lock.json').exists(), mode == '--complete')
            self.assertEqual((personal / '.agents/skills/alpha').is_symlink(), mode == '--complete')
