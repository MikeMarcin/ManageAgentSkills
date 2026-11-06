"""Controller status is based on exact signed device receipts."""
import argparse
import json
from unittest.mock import patch

import mask_control as control
import mask_core as core
import mask_fleet as fleet
import mask_present as present
import mask_rollout as rollout
import mask_rpc as rpc
import mask_transport as transport
from tests.test_fleet_rpc import FleetRpcFixture, URI


class FleetReceiptTests(FleetRpcFixture):
    def setUp(self):
        super().setUp()
        self.policy['epoch'] = 2
        self.policy['scopes']['personal']['rollout'] = True
        self.authorize(self.policy)
        self.cli(self.controller_home, 'tap', 'fixture', URI, '--pin-transport', env=self.env)
        self.cli(self.controller_home, 'tap', 'fetch', 'fixture', env=self.env)
        remote = self.base / 'control.git'
        remote.mkdir()
        core.git(remote, 'init', '--bare')
        arguments = ('fleet', 'control', 'configure', remote)
        preview = self.cli(self.controller_home, *arguments, '--dry-run')
        self.cli(self.controller_home, *arguments, '--approve-plan', preview['data']['plan_hash'])
        self.settings = control.settings(self.controller_home)
        self.peer = dict(schema_version=1, name='fixture', device=self.device, authority=fleet.public_authority(self.policy),
                         host_key=self.controller['key'], launcher=dict(python=str(self.base / 'python'),
                         program=str(self.base / 'mask.py'), home=str(self.device_home)), alias='fixture', ssh_config=None,
                         endpoint=dict(hostname='fixture.invalid', port=22, user='test'), history=[], revoked=False)
        fleet.put(transport.peer_path(self.controller_home, 'fixture'), self.peer, None)
        self.target = rollout.frozen_target(self.peer, argparse.Namespace(scope='user'), self.signer)
        config = core.config(core.read_json(self.controller_home / 'config.json'))
        row = rollout.resolve_input(self.controller_home, config, 'fixture/alpha')
        self.target['profile'], _ = rollout.contribution(None, 'fixture/alpha', 'install', row, config)
        self.details = dict(input='fixture/alpha', coordinate='fixture/alpha', mode='tap', forward=False, resolution=row)

    def exchange(self, peer, packet, *, timeout, signed):
        self.assertTrue(signed)
        process = self.run_rpc(rpc.frame(packet))
        self.assertEqual(process.returncode, 0, process.stderr)
        rpc.checked_response(process.stdout, packet['intent'], self.device)
        import io
        return rpc.read_frame(io.BytesIO(process.stdout))

    def test_apply_before_lost_reply_is_unknown_until_matching_signed_query(self):
        with control.snapshot(self.controller_home, self.settings, self.signer) as history:
            entry = control.event(self.settings, self.signer, history.events, 'install', 'a' * 32, [self.target], self.details)
            control.publish(history, entry, self.signer)

            def lose_reply(peer, packet, **kwargs):
                envelope = self.exchange(peer, packet, **kwargs)
                if packet['intent']['action'] == 'apply':
                    self.assertEqual(envelope['response']['data']['status'], 'applied_verified')
                    core.fail('fleet.transport_unknown', 'Fixture drops actual reply.', 4)
                return envelope

            with patch.object(transport, 'exchange', side_effect=lose_reply):
                first = rollout.deliver(self.controller_home, self.signer, history, entry, self.target)
            self.assertEqual(first['status'], 'unknown')
            with patch.object(transport, 'exchange', side_effect=self.exchange):
                verified = rollout.deliver(self.controller_home, self.signer, history, entry, self.target, observe_only=True)
            self.assertEqual(verified['status'], 'applied_verified')
            self.assertEqual(verified['host_load'], 'not_verified')
            self.assertEqual(verified['intent_digest'], control.intent_digest(entry))
            record = fleet.data(rollout.outcome_path(self.controller_home, entry, self.target))
            record['proof']['packet']['response']['data']['revision'] = 'sha256:' + '0' * 64
            with self.assertRaises(core.MaskError):
                rollout.proof_result(record, entry, self.target)
            result = self.cli(self.controller_home, 'fleet', 'operation', 'show', entry['operation'])
            self.assertTrue(result['data']['complete'])
            self.assertTrue(result['data']['installed_everywhere'])
            text = '\n'.join(present.fleet_rollout_lines(result['data']))
            self.assertIn('Agent host loading has not been verified.', text)

    def test_cancel_supersede_and_wait_preserve_incomplete_history(self):
        with control.snapshot(self.controller_home, self.settings, self.signer) as history:
            one = control.event(self.settings, self.signer, history.events, 'install', 'a' * 32, [self.target], self.details)
            control.publish(history, one, self.signer)
        waiting = self.cli(self.controller_home, 'fleet', 'operation', 'wait', one['operation'], '--timeout', 1)['data']
        self.assertTrue(waiting['timed_out'])
        self.assertFalse(waiting['complete'])
        args = ('fleet', 'operation', 'cancel', one['operation'])
        planned = self.cli(self.controller_home, *args, '--dry-run')['data']
        canceled = self.cli(self.controller_home, *args, '--approve-plan', planned['plan_hash'])['data']
        self.assertEqual(canceled['device_results'][0]['status'], 'canceled')
        self.assertFalse(canceled['installed_everywhere'])
        with control.snapshot(self.controller_home, self.settings, self.signer) as history:
            for label in ('b', 'c'):
                newer = control.event(self.settings, self.signer, history.events, 'install', label * 32, [self.target], self.details)
                control.publish(history, newer, self.signer)
        previous = self.cli(self.controller_home, 'fleet', 'operation', 'show', 'b' * 32)['data']
        self.assertEqual(previous['device_results'][0]['status'], 'superseded')
        self.assertFalse(previous['complete'])
