"""Local fleet trust boundaries through the public CLI and real OpenSSH signatures."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

import mask_core as core
import mask_fleet as fleet
from tests.public_support import ENTRY


class FleetFixture(unittest.TestCase):
    def setUp(self):
        self.signing_tool = shutil.which('ssh-keygen.exe' if os.name == 'nt' else 'ssh-keygen')
        if self.signing_tool is None:
            self.skipTest('OpenSSH ssh-keygen is unavailable')
        temp = tempfile.TemporaryDirectory(prefix='mask-fleet ü ')
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()
        self.controller_home = self.base / 'controller'
        self.device_home = self.base / 'device'
        self.controller_key = self.key('controller key')
        self.device_key = self.key('device key')

    def key(self, name):
        path = self.base / name
        subprocess.run([self.signing_tool, '-q', '-t', 'ed25519', '-N', '', '-f', str(path)],
                       stdin=subprocess.DEVNULL, capture_output=True, check=True, timeout=12)
        return path

    def cli(self, home, *args, code=0, env=None):
        run = subprocess.run([sys.executable, '-B', str(ENTRY), '--home', str(home),
                              *map(str, args), '--json'], capture_output=True, encoding='utf-8',
                             stdin=subprocess.DEVNULL, timeout=40, env=env)
        self.assertEqual(run.returncode, code, run.stdout + run.stderr)
        self.assertEqual(run.stderr, '')
        return json.loads(run.stdout)

    def enroll_local(self):
        controller = self.cli(self.controller_home, 'fleet', 'controller', 'init', 'operator',
                              '--signing-key', self.controller_key)['data']['identity']
        device = self.cli(self.device_home, 'fleet', 'device', 'init', 'laptop',
                          '--signing-key', self.device_key)['data']['identity']
        return controller, device

    def authorize(self, policy, *, code=0):
        path = self.base / 'policy.json'
        path.write_text(core.text_json(policy), encoding='utf-8')
        preview = self.cli(self.device_home, 'fleet', 'device', 'authorize',
                           '--policy', path, '--dry-run', code=code)
        if not code:
            return self.cli(self.device_home, 'fleet', 'device', 'authorize', '--policy', path,
                            '--approve-plan', preview['data']['plan_hash'])


class FleetIdentityTests(FleetFixture):
    def test_cli_binds_stable_distinct_identities_and_revocation(self):
        preview = self.cli(self.device_home, 'fleet', 'device', 'init', 'laptop',
                           '--signing-key', self.device_key, '--dry-run')
        self.assertTrue(preview['would_change'])
        self.assertFalse(self.device_home.exists())
        controller, device = self.enroll_local()
        self.assertEqual(self.enroll_local(), (controller, device))
        self.assertNotEqual(controller['id'], device['id'])
        self.assertNotEqual(controller['fingerprint'], device['fingerprint'])
        self.assertNotIn(str(self.device_key), json.dumps(device))
        self.assertEqual(self.cli(self.device_home, 'fleet', 'controller', 'init', 'operator',
                                  '--signing-key', self.device_key, code=4)['error']['code'], 'fleet.invalid')
        policy = dict(schema_version=1, controller=controller, epoch=2, minimum_sequence=10,
                      actions=['capabilities', 'receipt'], scopes={})
        self.authorize(policy)
        result = self.cli(self.device_home, 'fleet', 'device', 'descriptor')
        self.assertEqual(result['data'], dict(device=device, authority=policy))
        missing = self.cli(self.device_home, 'fleet', 'device', code=2)
        self.assertIn('authorize', missing['error']['details']['subcommands'])
        capabilities = self.cli(self.device_home, 'capabilities')
        self.assertIn('fleet.device.authorize', [row['name'] for row in capabilities['data']['commands']])
        self.assertEqual(capabilities['data']['fleet']['protocol'], 'mask.rpc.v1')
        revoke = self.cli(self.device_home, 'fleet', 'device', 'revoke-controller', '--dry-run')
        self.cli(self.device_home, 'fleet', 'device', 'revoke-controller', '--approve-plan', revoke['data']['plan_hash'])
        self.assertEqual(self.cli(self.device_home, 'fleet', 'device', 'descriptor', code=4)['error']['code'],
                         'fleet.controller_revoked')
        self.authorize(policy, code=4)
        self.authorize(dict(policy, epoch=3))

    def test_provider_enforces_key_namespace_and_payload(self):
        controller, device = self.enroll_local()
        signer = fleet.get_identity(self.controller_home, 'controller')
        payload = dict(device=device['id'], message='fixture')
        signature = fleet.sign(payload, signer, fleet.INTENT)
        fleet.verify(payload, signature, controller, fleet.INTENT)
        for value, identity, namespace in ((dict(payload, message='changed'), controller, fleet.INTENT),
                                            (payload, device, fleet.INTENT), (payload, controller, fleet.RECEIPT)):
            with self.assertRaisesRegex(core.MaskError, 'did not verify'):
                fleet.verify(value, signature, identity, namespace)
        replacement = self.key('replacement')
        self.controller_key.write_bytes(replacement.read_bytes())
        with self.assertRaisesRegex(core.MaskError, 'no longer matches'):
            fleet.sign(payload, signer, fleet.INTENT)

    def test_only_registered_scopes_and_matching_source_authority(self):
        controller, _ = self.enroll_local()
        fake = self.base / 'unregistered'
        fake.mkdir()
        policy = dict(schema_version=1, controller=controller, epoch=1, minimum_sequence=1,
                      actions=['inspect'], scopes={'work': dict(scope='project', root=str(fake), sources={})})
        self.authorize(policy, code=4)
        personal = self.base / 'personal'
        personal.mkdir()
        remote = self.base / 'fixture.git'
        subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True, capture_output=True, timeout=12)
        self.cli(self.device_home, 'tap', 'fixture', remote)
        self.cli(self.device_home, 'register', '--user', '--offline',
                 env=dict(os.environ, HOME=str(personal), USERPROFILE=str(personal)))
        policy['scopes'] = {'personal': dict(scope='user', root=str(personal), sources={})}
        self.authorize(policy)
        result = self.cli(self.device_home, 'fleet', 'device', 'descriptor')['data']
        self.assertEqual(result['authority']['scopes'], {'personal': dict(scope='user', sources={})})
        self.assertNotIn(str(personal), json.dumps(result))
        policy['epoch'] += 1
        policy['scopes']['personal']['sources'] = {'tap': dict(repository='https://github.com/fixture/tap.git', forward=True)}
        self.authorize(policy, code=4)
