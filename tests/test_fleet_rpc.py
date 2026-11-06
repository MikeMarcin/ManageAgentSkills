"""Bounded subprocess RPC and ordinary reconciliation recovery with disposable scopes."""
import json
import os
from pathlib import Path
import shlex
import struct
import subprocess
import sys
import time

import mask_core as core
import mask_fleet as fleet
import mask_rpc as rpc
from tests.test_fleet_identity import FleetFixture
from tests.public_support import ENTRY

URI = 'ssh://git@fleet-fixture.invalid/skills.git'
REVISION = core.digest(b'fleet fixture revision')


class FleetRpcFixture(FleetFixture):
    def setUp(self):
        super().setUp()
        self.controller, self.device = self.enroll_local()
        self.signer = fleet.get_identity(self.controller_home, 'controller')
        self.personal = self.base / 'personal home ü'
        self.personal.mkdir()
        self.remote = self.base / 'remote.git'
        self.source = self.base / 'source'
        self.source.mkdir()
        self.git(self.base, 'init', '--bare', '-q', str(self.remote))
        self.git(self.source, 'init', '-q', '-b', 'main')
        self.git(self.source, 'config', 'user.name', 'Fixture')
        self.git(self.source, 'config', 'user.email', 'fixture@example.invalid')
        skill = self.source / 'skills/alpha'
        skill.mkdir(parents=True)
        (skill / 'SKILL.md').write_bytes(b'---\nname: alpha\ndescription: Fixture skill\n---\n\nFleet fixture.\n')
        self.git(self.source, 'add', 'skills')
        self.git(self.source, 'commit', '-qm', 'fixture')
        self.git(self.source, 'push', '-q', str(self.remote), 'main')
        upload = self.base / 'upload fixture.py'
        upload.write_text('import os, subprocess\nraise SystemExit(subprocess.call(["git", "upload-pack", os.environ["MASK_FLEET_TEST_REMOTE"]]))\n')
        self.env = dict(os.environ, HOME=str(self.personal), USERPROFILE=str(self.personal),
                        GIT_SSH_COMMAND=shlex.join([Path(sys.executable).as_posix(), upload.as_posix()]),
                        GIT_SSH_VARIANT='ssh', MASK_FLEET_TEST_REMOTE=str(self.remote))
        self.cli(self.device_home, 'tap', 'fixture', URI, '--pin-transport', env=self.env)
        self.cli(self.device_home, 'install', 'fixture/alpha', '--user', '--no-update', env=self.env)
        self.link = self.personal / '.agents/skills/alpha'
        self.assertTrue(self.link.is_symlink())
        self.policy = dict(schema_version=1, controller=self.controller, epoch=1, minimum_sequence=1,
                           actions=list(fleet.ACTIONS), scopes={'personal': dict(scope='user', root=str(self.personal),
                               sources={'fixture': dict(repository=URI, forward=True)})})
        self.authorize(self.policy)
        self.generation = rpc.state_at(self.device_home)['generation']

    def git(self, root, *args):
        return subprocess.run(['git', '-C', str(root), *args], check=True, capture_output=True,
                              text=True, timeout=20).stdout.strip()

    def packet(self, action, payload=None, **kwargs):
        return rpc.request(self.signer, self.device, self.policy, action, payload or {},
                           revision=REVISION, generation=self.generation, **kwargs)

    def run_rpc(self, raw, *, crash=None):
        cli = ['--home', str(self.device_home), 'rpc', '--stdio']
        if crash is not None:
            script = ('import os, sys, mask, mask_fs; point = sys.argv.pop(1); '
                      'mask_fs.checkpoint = lambda name: os._exit(91) if name == point else None; '
                      'raise SystemExit(mask.main(sys.argv[1:]))')
            argv = [sys.executable, '-B', '-c', script, crash]
        else:
            argv = [sys.executable, '-B', str(ENTRY)]
        return subprocess.run([*argv, *cli], cwd=ENTRY.parent, env=self.env,
                              input=raw, capture_output=True, timeout=35)

    def send(self, packet, *, error=None):
        run = self.run_rpc(rpc.frame(packet))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stderr, b'')
        response = rpc.checked_response(run.stdout, packet['intent'], self.device)
        if error:
            self.assertEqual(response['status'], 'refused', response)
            self.assertEqual(response['error']['code'], error)
        else:
            self.assertEqual(response['status'], 'ok', response)
        return response['data']

    def prepare(self, **kwargs):
        return self.send(self.packet('prepare', dict(scope='personal'), **kwargs))

    def apply_packet(self, **kwargs):
        plan = self.prepare()['result']['plan']
        return self.packet('apply', dict(scope='personal', plan=plan), **kwargs)

    def query(self, packet, *, error=None):
        intent = packet['intent']
        return self.send(self.packet('receipt', dict(operation=intent['id'], digest=rpc.request_digest(intent))), error=error)

    def retarget(self, packet, **changes):
        intent = dict(packet['intent'], **changes)
        return dict(intent=intent, signature=fleet.sign(intent, self.signer, fleet.INTENT))


class FleetRpcTests(FleetRpcFixture):
    def test_schema_peer_signature_policy_and_expiry(self):
        packet = self.packet('capabilities')
        self.assertEqual(self.send(packet)['device'], self.device)
        for malformed in (
            struct.pack('!I', rpc.MAX_FRAME + 1), b'\0\0\0\4{',
            struct.pack('!I', 13) + b'{"x":1,"x":2}',
            rpc.frame(packet) + b'extra',
            rpc.frame(self.retarget(packet, action='exec', payload={'command': 'touch arbitrary'})),
            rpc.frame(self.retarget(packet, action='inspect', payload={'scope': '../root;echo'})),
            rpc.frame(self.retarget(packet, action='inspect', payload={'scope': 'personal', 'root': 'C:/private'})),
        ):
            run = self.run_rpc(malformed)
            self.assertEqual(run.returncode, 4, run.stdout + run.stderr)
            self.assertEqual(run.stdout, b'')
            self.assertLess(len(run.stderr), 100)
        self.send(self.retarget(packet, device='1' * 32), error='fleet.device_mismatch')
        self.send(self.retarget(packet, controller='2' * 32), error='fleet.controller_unknown')
        self.send(self.retarget(packet, expires=int(time.time()) - 1), error='fleet.intent_expired')
        self.send(self.retarget(packet, epoch=2), error='fleet.epoch_stale')
        self.send(self.retarget(packet, action='inspect', payload={'scope': 'absent'}), error='fleet.scope_denied')
        bad_signature = dict(packet, intent=dict(packet['intent'], generation=1234))
        self.send(bad_signature, error='fleet.signature_invalid')
        wrong_receipt = self.run_rpc(rpc.frame(packet)).stdout
        with self.assertRaisesRegex(core.MaskError, 'does not bind'):
            rpc.checked_response(wrong_receipt, self.packet('capabilities')['intent'], self.device)
        self.authorize(dict(self.policy, epoch=2, actions=['capabilities']))
        self.send(self.retarget(packet, epoch=2, action='inspect', payload={'scope': 'personal'}), error='fleet.action_denied')

    def test_apply_duplicate_conflict_and_stale_sequence(self):
        self.link.unlink()
        packet = self.apply_packet(sequence=2)
        first = self.send(packet)
        self.assertEqual(first['status'], 'applied_verified')
        self.assertTrue(first['result']['changed'])
        self.assertTrue(self.link.is_symlink())
        self.assertEqual(first, self.send(packet))
        self.assertEqual(first, self.query(packet))
        self.assertEqual(first['result']['bindings'][0]['coordinate'], 'fixture/alpha')
        local = fleet.get_identity(self.device_home, 'device')
        signed_wrong = rpc.reply(self.device_home, packet)['response']
        signed_wrong['data']['revision'] = core.digest(b'unrelated revision')
        envelope = dict(response=signed_wrong, signature=fleet.sign(signed_wrong, local, fleet.RECEIPT))
        with self.assertRaisesRegex(core.MaskError, 'differs from the request'):
            rpc.checked_response(rpc.frame(envelope), packet['intent'], self.device)
        self.assertNotIn(str(self.personal), json.dumps(first))
        self.send(self.retarget(packet, revision=core.digest(b'changed bytes')), error='fleet.operation_conflict')
        self.send(self.retarget(packet, id='2' * 32, sequence=1), error='fleet.sequence_stale')
        self.send(self.retarget(packet, id='3' * 32), error='fleet.sequence_stale')

    def test_interrupted_after_state_reconstructs_without_reapplying(self):
        self.link.unlink()
        packet = self.apply_packet()
        run = self.run_rpc(rpc.frame(packet), crash='state')
        self.assertEqual(run.returncode, 91, run.stderr)
        self.assertEqual(run.stdout, b'')
        self.assertTrue(self.link.is_symlink())
        self.send(packet, error='recovery.required')
        self.assertTrue((self.device_home / 'pending.json').exists())
        recovered = self.query(packet)
        self.assertEqual(recovered['status'], 'applied_verified')
        self.assertFalse((self.device_home / 'pending.json').exists())
        self.assertEqual(recovered, self.send(packet))

    def test_partial_refuses_until_ordinary_rollback(self):
        self.link.unlink()
        other = self.personal / '.claude/skills/alpha'
        other.unlink()
        packet = self.apply_packet()
        run = self.run_rpc(rpc.frame(packet), crash='link')
        self.assertEqual(run.returncode, 91, run.stderr)
        self.assertNotEqual(self.link.is_symlink(), other.is_symlink())
        self.query(packet, error='recovery.required')
        self.send(packet, error='recovery.required')
        self.cli(self.device_home, 'recover', '--rollback', env=self.env)
        self.assertFalse(self.link.is_symlink())
        self.assertFalse(other.is_symlink())
        self.assertEqual(self.query(packet)['status'], 'rolled_back')
        self.assertEqual(self.send(packet)['status'], 'rolled_back')

    def test_cancel_records_without_running_a_stale_plan(self):
        packet = self.packet('apply', dict(scope='personal', plan=core.digest(b'invalid plan')))
        self.send(packet, error='plan.stale')
        self.assertEqual(self.query(packet)['status'], 'accepted')
        target = packet['intent']
        cancellation = self.packet('cancel-request', dict(operation=target['id'], digest=rpc.request_digest(target)), sequence=2)
        canceled = self.send(cancellation)
        self.assertEqual(canceled['result']['status'], 'canceled')
        self.assertEqual(canceled, self.send(cancellation))
        self.assertEqual(self.send(packet)['status'], 'canceled')
        self.assertEqual(self.query(cancellation), canceled)
        self.policy = dict(self.policy, epoch=2, scopes={})
        self.authorize(self.policy)
        self.query(cancellation, error='fleet.scope_denied')
