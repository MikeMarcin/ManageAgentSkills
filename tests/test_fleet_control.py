"""Signed Git history, competing controller commands and rollback."""
import mask_control as control
import mask_core as core
import mask_fleet as fleet
from tests.test_fleet_identity import FleetFixture


class FleetControlTests(FleetFixture):
    def setUp(self):
        super().setUp()
        _, self.device = self.enroll_local()
        self.signer = fleet.get_identity(self.controller_home, 'controller')
        remote = self.base / 'control.git'
        remote.mkdir()
        core.git(remote, 'init', '--bare')
        arguments = ('fleet', 'control', 'configure', remote)
        preview = self.cli(self.controller_home, *arguments, '--dry-run')
        self.cli(self.controller_home, *arguments, '--approve-plan', preview['data']['plan_hash'])
        self.settings = control.settings(self.controller_home)
        self.target = dict(name='laptop', device=self.device['id'], device_epoch=1, scope='user',
                           scope_type='user', profile=None)

    def snapshot(self):
        return control.snapshot(self.controller_home, self.settings, self.signer)

    def proposal(self, history, label, action='remove', **data):
        return control.event(self.settings, self.signer, history.events, action, label * 32, [self.target], data)

    def test_two_publishers_cannot_overwrite_same_expected_head(self):
        with self.snapshot() as first, self.snapshot() as second:
            approved = self.proposal(first, 'a')
            self.assertEqual(approved['sequence'], 1)
            control.publish(first, approved, self.signer)
            control.remember(self.controller_home, first)
            with self.assertRaisesRegex(core.MaskError, 'Another publisher'):
                control.publish(second, self.proposal(second, 'b'), self.signer)
        with self.snapshot() as history:
            self.assertEqual(history.events, [approved])
            rollback = self.proposal(history, 'c', rollback_of=approved['operation'])
            self.assertEqual(rollback['parent'], control.intent_digest(approved))
            self.assertEqual(rollback['sequence'], 2)
            control.publish(history, rollback, self.signer)
        with self.snapshot() as history:
            self.assertEqual(history.events, [approved, rollback])

    def test_repository_cannot_hide_a_locally_observed_revision(self):
        with self.snapshot() as history:
            control.publish(history, self.proposal(history, 'a'), self.signer)
            control.remember(self.controller_home, history)
            control.network(history.root, self.settings, 'push', self.settings['repository'], ':' + control.REF)
        with self.assertRaisesRegex(core.MaskError, 'does not extend'):
            with self.snapshot():
                self.fail('A missing ref replaced observed history')

    def test_cancel_only_suppresses_the_current_matching_operation(self):
        with self.snapshot() as history:
            install = self.proposal(history, 'a', action='install')
            control.publish(history, install, self.signer)
            cancel = self.proposal(history, 'b', action='cancel', operation=install['operation'])
            control.publish(history, cancel, self.signer)
            self.assertEqual(history.effective()[control.target_key(self.target)][0], cancel)
            update = self.proposal(history, 'c', action='update')
            control.publish(history, update, self.signer)
            old_cancel = self.proposal(history, 'd', action='cancel', operation=install['operation'])
            control.publish(history, old_cancel, self.signer)
            self.assertEqual(history.effective()[control.target_key(self.target)][0], update)
