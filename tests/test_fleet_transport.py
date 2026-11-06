"""Fixture transport negatives and exact selected package delivery."""
import argparse
import base64
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
from unittest.mock import patch
from threading import Barrier

import mask_core as core
import mask_fleet as fleet
import mask_fleet_artifacts as artifacts
import mask_rpc as rpc
import mask_present as present
import mask_sources as sources
import mask_store as store
import mask_transport as transport
from tests.public_support import ENTRY
from tests.test_fleet_rpc import FleetRpcFixture


class FleetTransportTests(FleetRpcFixture):
    def peer(self):
        return dict(schema_version=1, device=self.device, authority=fleet.public_authority(self.policy),
                    host_key=self.controller['key'], launcher=dict(python=sys.executable, program=str(ENTRY),
                    home=str(self.device_home)), alias='fixture', ssh_config=None,
                    endpoint=dict(hostname='fixture.invalid', port=2222, user='fixture'))

    def test_fixed_launcher_runs_native_paths_with_spaces_unicode_and_quote(self):
        installed = self.base / "installed ü ' spaces"
        installed.mkdir()
        for source in ENTRY.parent.glob('mask*.py'):
            shutil.copy2(source, installed / source.name)
        peer = self.peer()
        peer['launcher']['program'] = str(installed / 'mask.py')
        invocation = transport.command(peer['launcher'], self.device['platform'])
        argv = (invocation.split() if os.name == 'nt' else ['/bin/sh', '-c', invocation])
        packet = self.packet('capabilities')
        process = subprocess.run(argv, input=rpc.frame(packet), capture_output=True, timeout=20)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(rpc.checked_response(process.stdout, packet['intent'], self.device)['data']['device'], self.device)
        with self.assertRaisesRegex(core.MaskError, 'reviewed installed mask.py'):
            transport.command(dict(peer['launcher'], program=str(installed / 'run.py')), self.device['platform'])
        windows = transport.command(dict(python='C:/Python/python.exe', program="C:/space ü ' quote/mask.py",
                                         home='C:/test home'), 'windows')
        decoded = base64.b64decode(windows.split()[-1]).decode('utf-16le')
        self.assertIn("space ü '' quote", decoded)
        self.assertTrue(decoded.endswith("'rpc' '--stdio'; exit $LASTEXITCODE"))

    def test_transport_pins_host_ignores_unsafe_config_and_marks_timeout_unknown(self):
        peer = self.peer()
        packet = self.packet('capabilities')
        response = rpc.frame(rpc.reply(self.device_home, packet))
        real_run = core.contained_run
        status = 'success'
        auth = dict(identityfile=['fixture file'], localforward=['unsafe'],
                    remotecommand=['anything'], sendenv=['*'], controlpath=['open'])
        ssh = fleet.tool('ssh')

        def runner(args, environment, **kwargs):
            if args[0] != ssh:
                return real_run(args, environment, **kwargs)
            for required in ('StrictHostKeyChecking=yes', 'ForwardAgent=no', 'ControlPath=none',
                             'GlobalKnownHostsFile=none', 'VerifyHostKeyDNS=no'):
                self.assertIn(required, args)
            self.assertNotIn('unsafe', args)
            self.assertNotIn('anything', args)
            self.assertNotIn('*', args)
            self.assertEqual(rpc.read_frame(io.BytesIO(kwargs['input_file'].read())), packet)
            if status == 'timeout':
                core.fail('fleet.ssh.timeout', 'fixture timeout', 4)
            if status == 'wrong-key':
                return 255, b'', b'Host key verification failed.'
            if status == 'auth':
                return 255, b'', b'Permission denied (publickey).'
            return 0, response, b''

        with patch.object(transport, 'config_for', return_value=(peer['endpoint'], auth)), patch.object(core, 'contained_run', side_effect=runner):
            self.assertEqual(transport.exchange(peer, packet)['status'], 'ok')
            for status, code in (('timeout', 'fleet.transport_unknown'), ('wrong-key', 'fleet.host_key_mismatch'),
                                 ('auth', 'fleet.ssh_auth_required')):
                with self.assertRaises(core.MaskError) as raised:
                    transport.exchange(peer, packet)
                self.assertEqual(raised.exception.code, code)
                self.assertEqual(raised.exception.details['operation'], packet['intent']['id'])
                if status == 'timeout':
                    self.assertEqual(raised.exception.details['outcome'], 'unknown')
        with patch.object(transport, 'config_for', return_value=(dict(peer['endpoint'], port=22), auth)):
            with self.assertRaisesRegex(core.MaskError, 'no longer resolves'):
                transport.exchange(peer, packet)

    def test_parallel_probe_preserves_each_result_and_human_refusal(self):
        peers = [dict(self.peer(), name=name) for name in ('reachable', 'unavailable')]
        barrier = Barrier(2, timeout=4)

        def probe(peer, controller, *, timeout):
            barrier.wait()
            if peer['name'] == 'unavailable':
                core.fail('fleet.ssh_auth_required', 'Fixture SSH auth refused.', 4)
            return {'adapters': ['codex']}

        args = argparse.Namespace(command='fleet.capability', parallel=2, timeout=2)
        output = dict(command=args.command, data={}, transaction='not_started')
        with patch.object(transport, 'peers', return_value=peers), patch.object(transport, 'probe', side_effect=probe):
            with self.assertRaises(core.MaskError) as result:
                transport.probe_all(self.controller_home, args, output)
        output['error'] = result.exception.as_dict()
        self.assertEqual([row['status'] for row in output['data']['devices']], ['reachable', 'unavailable'])
        rendered = present.render_error(output)
        self.assertIn('reachable: reachable', rendered)
        self.assertIn('unavailable: unavailable', rendered)
        self.assertIn('fleet.ssh_auth_required', rendered)

    def take_artifact_and_cache(self):
        row = fleet.data(self.device_home / 'user.lock.json')['packages'][0]
        packet = artifacts.packet(self.device_home, row)
        artifact, _ = store.location(self.device_home, row['payload_digest'], row['id'])
        config = core.config(core.read_json(self.device_home / 'config.json'))
        cache = sources.cached(self.device_home, row['source'], sources.selected(config, row['source']))
        artifact.rename(self.base / 'retained fixture artifact')
        cache.rename(self.base / 'retained fixture cache')
        return row, packet, artifact

    def test_exact_git_fetch_and_signed_forwarding_are_separate_paths(self):
        row, packet, artifact = self.take_artifact_and_cache()
        expected = packet['files'][0]['data']
        broken = self.base / 'deny source.py'
        broken.write_text('import sys\nprint("Permission denied (publickey).", file=sys.stderr)\nsys.exit(255)\n')
        actual_env = self.env.copy()
        self.env['GIT_SSH_COMMAND'] = f'"{Path(sys.executable).as_posix()}" "{broken.as_posix()}"'
        request = self.packet('prepare', dict(scope='personal'))
        self.send(request, error='git.auth_required')
        self.assertFalse(artifact.exists())
        invalid = dict(packet, files=[dict(packet['files'][0], path='../outside')])
        self.send(self.packet('prepare', dict(scope='personal', acquire='cached', artifacts=[invalid])), error='skill.path_invalid')
        changed = dict(packet, files=[dict(packet['files'][0], sha256='0' * 64)])
        self.send(self.packet('prepare', dict(scope='personal', acquire='cached', artifacts=[changed])), error='fleet.artifact_mismatch')
        unselected = dict(packet, coordinate='fixture/unrelated')
        self.send(self.packet('prepare', dict(scope='personal', acquire='cached', artifacts=[unselected])), error='fleet.artifact_unselected')
        self.assertFalse(artifact.exists())
        self.assertFalse((self.base / 'outside').exists())
        prepared = self.send(self.packet('prepare', dict(scope='personal', acquire='cached', artifacts=[packet])))
        self.assertEqual(prepared['status'], 'prepared')
        self.assertEqual(artifacts.packet(self.device_home, row)['files'][0]['data'], expected)
        self.assertEqual(self.send(self.packet('apply', dict(scope='personal', plan=prepared['result']['plan'])))['status'],
                         'applied_verified')
        artifact.rename(self.base / 'retained forwarded artifact')
        self.env = actual_env
        exact = self.prepare(sequence=2)
        self.assertEqual(exact['status'], 'prepared')
        self.assertEqual(artifacts.packet(self.device_home, row), packet)

    def test_forwarding_requires_per_source_grant(self):
        _, packet, artifact = self.take_artifact_and_cache()
        self.policy['epoch'] += 1
        self.policy['scopes']['personal']['sources']['fixture']['forward'] = False
        self.authorize(self.policy)
        self.send(self.packet('prepare', dict(scope='personal', acquire='cached', artifacts=[packet])),
                  error='fleet.artifact_forward_denied')
        self.assertFalse(artifact.exists())
