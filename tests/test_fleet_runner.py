"""Foreground pull, separate signed receipts and reversible scheduler ownership."""
import argparse
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as XML

import mask_control as control
import mask_core as core
import mask_fleet as fleet
import mask_fleet_receipts as receipts
import mask_fleet_schedule as schedule
import mask_rollout as rollout
import mask_runner as runner
from tests.test_fleet_rpc import FleetRpcFixture, URI


class FleetRunnerTests(FleetRpcFixture):
    def setUp(self):
        super().setUp()
        self.policy['epoch'] = 2
        self.policy['scopes']['personal']['rollout'] = True
        self.authorize(self.policy)
        self.cli(self.controller_home, 'tap', 'fixture', URI, '--pin-transport', env=self.env)
        for name in ('control.git', 'receipts.git'):
            root = self.base / name
            root.mkdir()
            core.git(root, 'init', '--bare')
        for home in (self.controller_home, self.device_home):
            args = ('fleet', 'control', 'configure', self.base / 'control.git', '--receipts', self.base / 'receipts.git')
            preview = self.cli(home, *args, '--dry-run')
            self.cli(home, *args, '--approve-plan', preview['data']['plan_hash'])
        self.settings = control.settings(self.controller_home)
        self.target = dict(name='laptop', device=self.device['id'], device_epoch=2, scope='personal',
                           scope_type='user', identity=self.device, profile=None)

    def commit_beta(self, text):
        path = self.source / 'skills' / 'beta' / 'SKILL.md'
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(f'---\nname: beta\ndescription: Runner fixture\n---\n\n{text}\n'.encode())
        self.git(self.source, 'add', 'skills')
        self.git(self.source, 'commit', '-qm', text)
        self.git(self.source, 'push', '-q', str(self.remote), 'main')
        self.cli(self.controller_home, 'tap', 'fetch', 'fixture', env=self.env)
        config = core.config(core.read_json(self.controller_home / 'config.json'))
        row = rollout.resolve_input(self.controller_home, config, 'fixture/beta')
        profile, _ = rollout.contribution(None, 'fixture/beta', 'install', row, config)
        return dict(self.target, profile=profile), row

    def test_public_local_sync_reaches_latest_approved_bytes_and_separate_signed_receipt(self):
        old, old_row = self.commit_beta('version one')
        latest, latest_row = self.commit_beta('version two')
        self.commit_beta('unapproved version three')
        with control.snapshot(self.controller_home, self.settings, self.signer) as history:
            for label, target, row in [('a', old, old_row), ('b', latest, latest_row)]:
                entry = control.event(self.settings, self.signer, history.events, 'install', label * 32, [target],
                                      dict(input='fixture/beta', coordinate='fixture/beta', mode='tap', forward=False, resolution=row))
                control.publish(history, entry, self.signer)
        result = self.cli(self.device_home, 'fleet', 'sync', '--local', env=self.env)['data']
        self.assertTrue(result['complete'])
        self.assertEqual(result['operation_ids'], ['b' * 32])
        self.assertTrue(self.link.is_symlink())
        self.assertIn('version two', (self.personal / '.agents/skills/beta/SKILL.md').read_text(encoding='utf-8'))
        self.assertEqual(receipts.read(self.settings, entry, latest)['status'], 'applied_verified')
        with receipts.scratch(self.settings) as (root, endpoint):
            self.assertIsNone(control.remote_head(root, endpoint, receipts.receipt_ref(dict(operation='a' * 32), old)))
        self.assertFalse(self.cli(self.device_home, 'fleet', 'sync', '--local', env=self.env)['changed'])
        controller = self.cli(self.controller_home, 'fleet', 'operation', 'show', entry['operation'])['data']
        self.assertTrue(controller['installed_everywhere'])

    def test_scheduler_plan_ownership_disable_and_tick_backoff(self):
        binding = dict(schema_version=1, platform='macos', user='501', name='com.mask.fleet.test',
                       path=str(self.base / 'test.plist'), interval=60, argv=runner.runner_argv(self.device_home))
        self.assertIn(b'StartCalendarInterval', schedule.mac_plist(binding))
        self.assertEqual(runner.next_tick(100, 60, 1, 5), 225)
        self.assertEqual(runner.next_tick(100, 3600, 6, 449), 3700)
        state = [False, False]

        def install(record):
            self.assertEqual(record, binding)
            state[:] = [True, True]

        def remove(record):
            self.assertEqual(record, binding)
            state[:] = [False, False]

        args = argparse.Namespace(command='fleet.runner.enable', interval=60)
        def output(dry_run):
            return dict(data={}, dry_run=dry_run, would_change=False)

        with patch.object(schedule, 'schedule_record', return_value=binding), patch.object(
                schedule, 'observe', side_effect=lambda record: tuple(state)), patch.object(
                schedule, 'install', side_effect=install), patch.object(schedule, 'remove', side_effect=remove):
            preview = output(True)
            runner.scheduler_command(args, preview, self.device_home)
            self.assertFalse(any(state))
            args.approve_plan = preview['data']['plan_hash']
            runner.scheduler_command(args, output(False), self.device_home)
            self.assertTrue(all(state))
            with patch.object(runner, 'converge', side_effect=core.MaskError('fleet.incomplete', 'Offline fixture.', 9)):
                failed = output(False)
                with self.assertRaises(core.MaskError):
                    runner.tick(self.device_home, failed)
                self.assertEqual(failed['data']['runner']['status'], 'backoff')
                self.assertEqual(failed['data']['runner']['last_error']['code'], 'fleet.incomplete')
                waiting = output(False)
                runner.tick(self.device_home, waiting)
                self.assertEqual(waiting['data']['runner']['status'], 'waiting')
            args.command = 'fleet.runner.disable'
            preview = output(True)
            runner.scheduler_command(args, preview, self.device_home)
            args.approve_plan = preview['data']['plan_hash']
            runner.scheduler_command(args, output(False), self.device_home)
            self.assertFalse(any(state))
            self.assertFalse(runner.read_record(self.device_home)['enabled'])

    def test_windows_scheduler_refuses_unowned_action(self):
        binding = dict(platform='windows', user='S-1-5-21-1', name='com.mask.fleet.test',
                       path=None, interval=300, start_boundary='2030-01-01T00:00:00+00:00',
                       argv=['C:/Program Files/Python/python.exe', 'mask.py', 'fleet'])
        raw = schedule.win_definition(binding)
        with patch.object(schedule, 'command', return_value=(0, raw, b'')):
            self.assertEqual(schedule.win_observe(binding), (True, True))
        substituted = schedule.win_definition(dict(binding, argv=['C:/other.exe']))
        with patch.object(schedule, 'command', return_value=(0, substituted, b'')):
            with self.assertRaisesRegex(core.MaskError, 'differs'):
                schedule.win_observe(binding)


    def test_windows_scheduler_refuses_changed_trigger_without_deleting_task(self):
        binding = dict(platform='windows', user='S-1-5-21-1', name='com.mask.fleet.test',
                       path=None, interval=300, start_boundary='2030-01-01T00:00:00+00:00',
                       argv=['C:/Program Files/Python/python.exe', 'mask.py', 'fleet'])
        namespace = {'t': schedule.TASK_NS}
        for parent, field, value in (
                ('Triggers/TimeTrigger/Repetition', 'Interval', 'PT1H'),
                ('Triggers/TimeTrigger', 'StartBoundary', '2031-01-01T00:00:00Z'),
                ('Triggers/TimeTrigger', 'EndBoundary', '2031-01-01T00:00:00Z'),
                ('Triggers/LogonTrigger', 'Enabled', 'false'),
                ('Settings', 'RunOnlyIfIdle', 'true')):
            with self.subTest(field=field):
                task = XML.fromstring(schedule.win_definition(binding))
                parent_node = task.find('/'.join('t:' + part for part in parent.split('/')), namespace)
                node = parent_node.find('t:' + field, namespace)
                if node is None:
                    node = XML.SubElement(parent_node, '{' + schedule.TASK_NS + '}' + field)
                node.text = value
                with patch.object(schedule, 'user_id', return_value=binding['user']), patch.object(
                        schedule, 'command', return_value=(0, XML.tostring(task), b'')) as command:
                    with self.assertRaisesRegex(core.MaskError, 'schedule differs'):
                        schedule.remove(binding)
                    command.assert_called_once_with('schtasks.exe', '/Query', '/TN', binding['name'], '/XML', '/HRESULT')
        normalized = schedule.win_definition(binding).decode('utf-16').replace('PT300S', 'PT5M').replace(
            '2030-01-01T00:00:00+00:00', '2030-01-01T00:00:00Z').replace('<RunLevel>LeastPrivilege</RunLevel>', '')
        account = 'fixture\\operator'
        normalized = normalized.replace('<LogonTrigger><UserId>' + binding['user'],
                                        '<LogonTrigger><UserId>' + account)
        with patch.object(schedule, 'command', return_value=(0, normalized.encode('utf-8'), b'')), patch.object(
                schedule, 'windows_identity', return_value=(account, binding['user'])):
            self.assertEqual(schedule.win_observe(binding), (True, True))

    def test_mac_scheduler_observes_exact_label_without_listing_gui_domain(self):
        path = self.base / 'Library' / 'LaunchAgents' / 'com.mask.fleet.test.plist'
        path.parent.mkdir(parents=True)
        record = dict(path=str(path), user='501', name='com.mask.fleet.test')
        with patch.object(schedule.Path, 'home', return_value=self.base), patch.object(
                schedule, 'command', return_value=(113, b'', b'Could not find service')) as query:
            self.assertEqual(schedule.mac_observe(record), (False, False))
            query.assert_called_once_with('/bin/launchctl', 'print', 'gui/501/com.mask.fleet.test')
            query.return_value = (112, b'', b'Could not find domain')
            with self.assertRaisesRegex(core.MaskError, 'could not be inspected'):
                schedule.mac_observe(record)

    def test_windows_scheduler_approval_persists_the_registered_start_boundary(self):
        binding = dict(schema_version=1, platform='windows', user='S-1-5-21-1', name='com.mask.fleet.test',
                       path=None, interval=300, argv=runner.runner_argv(self.device_home))
        installed = None

        def install(record):
            nonlocal installed
            installed = record
            self.assertEqual(runner.scheduler_binding(runner.read_record(self.device_home)), record)

        args = argparse.Namespace(command='fleet.runner.enable')
        with patch.object(schedule, 'schedule_record', side_effect=lambda *_: dict(binding)), patch.object(
                schedule, 'observe', side_effect=lambda record: (record == installed, record == installed)), patch.object(
                schedule, 'install', side_effect=install):
            preview = dict(data={}, dry_run=True)
            runner.scheduler_command(args, preview, self.device_home)
            self.assertNotIn('start_boundary', preview['data']['runner']['scheduler'])
            self.assertTrue(Path(preview['data']['runner']['signing_provider']).is_file())
            self.assertIsNone(runner.read_record(self.device_home))
            args.approve_plan = preview['data']['plan_hash']
            runner.scheduler_command(args, dict(data={}, dry_run=False), self.device_home)
            self.assertTrue(installed['start_boundary'].endswith('+00:00'))
            with patch.object(runner, 'converge') as converge:
                converge.side_effect = lambda *_: self.assertEqual(
                    fleet.SIGNING_PROVIDER.get(), preview['data']['runner']['signing_provider'])
                runner.tick(self.device_home, dict(data={}))
                converge.assert_called_once()
            self.assertIsNone(fleet.SIGNING_PROVIDER.get())
            repeated = dict(data={}, dry_run=True)
            runner.scheduler_command(args, repeated, self.device_home)
            self.assertFalse(repeated['would_change'])
