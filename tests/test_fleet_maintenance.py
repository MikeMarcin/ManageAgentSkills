"""Public fleet maintenance with real signed subprocess RPC and disposable Git repositories."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import mask_core as c
import mask_fleet as fleet
import mask_transport as transport
from tests.public_support import ENTRY
from tests.test_fleet_rpc import FleetRpcFixture, URI


# Only SSH delivery is substituted. Both sides run the normal CLI and authenticate frames.
BRIDGE = r"""
import io, os, subprocess, sys
from pathlib import Path
sys.path.insert(0, sys.argv.pop(1))
import mask, mask_core, mask_rpc, mask_transport

def exchange(peer, packet, *, timeout, signed=False):
    launcher = peer['launcher']
    if os.environ.get('MASK_FLEET_OFFLINE') == peer['name']:
        mask_core.fail('fleet.transport_unknown', 'Fixture peer is disconnected.', 4)
    prefix = [launcher['python'], '-B', launcher['program']]
    if os.environ.get('MASK_FLEET_FAIL_TAP_RECEIPT') == peer['name'] and packet['intent']['action'] == 'tap-apply':
        prefix = [launcher['python'], '-B', '-c', '''
import mask, mask_fleet_taps
def refuse_receipt(*args):
    raise OSError("Fixture loses receipt publication after catalog commit.")
mask_fleet_taps.save_result = refuse_receipt
raise SystemExit(mask.main())
''']
    run = subprocess.run([*prefix, '--home',
                          launcher['home'], 'rpc', '--stdio'], input=mask_rpc.frame(packet),
                         capture_output=True, timeout=timeout)
    if run.returncode:
        raise RuntimeError((run.returncode, run.stdout, run.stderr))
    answer = mask_rpc.checked_response(run.stdout, packet['intent'], peer['device'])
    if os.environ.get('MASK_FLEET_DROP') == packet['intent']['action']:
        mask_core.fail('fleet.transport_unknown', 'Fixture drops the signed acknowledgement.', 4)
    return mask_rpc.read_frame(io.BytesIO(run.stdout)) if signed else answer

mask_transport.exchange = exchange
raise SystemExit(mask.main(sys.argv[1:]))
"""


class FleetMaintenanceTests(FleetRpcFixture):
    def setUp(self):
        super().setUp()
        self.cli(self.controller_home, 'tap', 'fixture', URI, '--pin-transport', env=self.env)
        self.cli(self.controller_home, 'tap', 'fetch', 'fixture', env=self.env)

    def public(self, *args, code=0, program=ENTRY, drop=None, offline=None, fail_tap_receipt=None):
        env = dict(self.env)
        for name, value in (('MASK_FLEET_DROP', drop), ('MASK_FLEET_OFFLINE', offline),
                            ('MASK_FLEET_FAIL_TAP_RECEIPT', fail_tap_receipt)):
            if value:
                env[name] = value
        run = subprocess.run([sys.executable, '-B', '-c', BRIDGE, str(program.parent), '--home',
                              str(self.controller_home), 'fleet', *args, '--json'],
                             env=env, capture_output=True, encoding='utf-8', timeout=160)
        self.assertEqual(run.returncode, code, run.stdout + run.stderr)
        self.assertEqual(run.stderr, '')
        return json.loads(run.stdout)

    def set_peer(self, name, device, policy, home, program):
        value = dict(schema_version=1, name=name, device=device, authority=fleet.public_authority(policy),
                     host_key=self.controller['key'], launcher=dict(python=sys.executable, program=str(program), home=str(home)),
                     alias=name, ssh_config=None, endpoint=dict(hostname='fixture.invalid', port=22, user='test'),
                     history=[], revoked=False)
        path = transport.peer_path(self.controller_home, name)
        fleet.put(path, value, fleet.data(path, missing=True))

    def approve(self, home, policy):
        path = self.base / 'maintenance policy.json'
        path.write_text(c.text_json(policy), encoding='utf-8')
        args = ('fleet', 'device', 'authorize', '--policy', path)
        preview = self.cli(home, *args, '--dry-run')
        self.cli(home, *args, '--approve-plan', preview['data']['plan_hash'])

    def init_git(self, root):
        root.mkdir()
        self.git(root, 'init', '-q', '-b', 'main')
        self.identity(root)

    def identity(self, root):
        self.git(root, 'config', 'user.name', 'Fleet Fixture')
        self.git(root, 'config', 'user.email', 'fleet@example.invalid')
        self.git(root, 'config', 'commit.gpgSign', 'false')
        self.git(root, 'config', 'core.autocrlf', 'false')

    def test_bare_install_and_legacy_skill_update(self):
        self.policy['epoch'] += 1
        self.policy['scopes']['personal']['rollout'] = True
        self.policy['scopes']['personal']['upgrade'] = True
        self.policy['actions'] += ['upgrade-inspect', 'upgrade-apply']
        self.authorize(self.policy)
        self.set_peer('laptop', self.device, self.policy, self.device_home, ENTRY)
        bare = self.base / 'desired.git'
        self.git(self.base, 'init', '--bare', str(bare))
        args = ('fleet', 'control', 'configure', bare)
        control = self.cli(self.controller_home, *args, '--dry-run')
        self.cli(self.controller_home, *args, '--approve-plan', control['data']['plan_hash'])
        preview = self.public('install', 'alpha', '--dry-run')['data']
        [row] = preview['targets']
        self.assertEqual((row['name'], row['scope'], preview['input']['mode']), ('laptop', 'personal', 'tap'))
        applied = self.public('install', 'alpha', '--approve-plan', preview['plan_hash'])['data']
        self.assertTrue(applied['complete'])
        legacy = self.public('update', 'fixture/alpha', '--all-devices', '--scope', 'user', '--dry-run')
        self.assertEqual(legacy['data']['action'], 'update')
        invalid = self.public('update', 'fixture/alpha', '--all', '--scope', 'user', '--dry-run', code=2)
        self.assertEqual(invalid['error']['code'], 'invocation.invalid')
        refused = self.public('install', 'https://github.com/fixture/skills/tree/main/alpha', '--dry-run', code=4)
        self.assertEqual(refused['error']['code'], 'fleet.mode_required')
        # Both the local selection and the controller contribution own alpha.
        # One approved upgrade must move both locks together or composition refuses.
        skill = self.source / 'skills/alpha/SKILL.md'
        skill.write_bytes(skill.read_bytes() + b'\nCo-owned update.\n')
        self.git(self.source, 'commit', '-qam', 'update co-owned skill')
        self.git(self.source, 'push', '-q', str(self.remote), 'main')
        candidate = self.git(self.source, 'rev-parse', 'HEAD')
        self.cli(self.controller_home, 'tap', 'fetch', 'fixture', env=self.env)
        review = self.public('upgrade', '--dry-run')['data']
        applied = self.public('upgrade', '--approve-plan', review['plan_hash'])['data']
        self.assertTrue(applied['complete'])
        direct, contribution = applied['device_results']
        self.assertEqual((direct['status'], contribution['status']), ('applied_verified', 'applied_verified'))
        self.assertTrue(contribution['contribution'])
        self.assertEqual(applied['control_publications'][0]['operation'], contribution['operation'])
        state = json.loads((self.device_home / 'state.json').read_text())
        self.assertEqual(state['user']['last_lock']['packages'][0]['commit'], candidate)
        [owned] = state['user']['profiles'].values()
        self.assertEqual(owned['lock']['packages'][0]['commit'], candidate)
        current = self.public('upgrade', '--dry-run')['data']
        self.assertIsNone(current['plan']['contributions'])
        replay = self.public('upgrade', '--approve-plan', review['plan_hash'])['data']
        self.assertEqual(replay['device_results'][1]['operation'], contribution['operation'])
        self.assertEqual(replay['control_publications'], [])

    def test_program_exact_checkout_and_lost_ack_recovery(self):
        author = self.base / 'program-source'
        self.init_git(author)
        for source in ENTRY.parent.glob('mask*.py'):
            shutil.copy2(source, author / source.name)
        shutil.copytree(ENTRY.parent / 'schemas', author / 'schemas')
        self.git(author, 'add', '.')
        self.git(author, 'commit', '-qm', 'program base')
        before = self.git(author, 'rev-parse', 'HEAD')
        bare = self.base / 'ManageAgentSkills.git'
        self.git(self.base, 'clone', '--bare', str(author), str(bare))
        controller = self.base / 'controller-program'
        device = self.base / 'device-program'
        desktop = self.base / 'desktop-program'
        for root in (controller, device, desktop):
            self.git(self.base, 'clone', '-q', str(bare), str(root))
            self.identity(root)
        self.policy['epoch'] += 1
        self.policy.update(program_origin=bare.as_uri(), actions=[*fleet.ACTIONS, 'program-inspect', 'program-update'])
        self.authorize(self.policy)
        self.set_peer('laptop', self.device, self.policy, self.device_home, device / 'mask.py')
        desktop_home = self.base / 'desktop'
        desktop_key = self.key('desktop key')
        desktop_device = self.cli(desktop_home, 'fleet', 'device', 'init', 'desktop',
                                  '--signing-key', desktop_key)['data']['identity']
        desktop_policy = dict(self.policy, scopes={})
        self.approve(desktop_home, desktop_policy)
        self.set_peer('desktop', desktop_device, desktop_policy, desktop_home, desktop / 'mask.py')
        (author / 'change.txt').write_text('reviewed\n', encoding='utf-8')
        self.git(author, 'add', 'change.txt')
        self.git(author, 'commit', '-qm', 'reviewed program change')
        self.git(author, 'push', '-q', str(bare), 'main')
        after = self.git(author, 'rev-parse', 'HEAD')
        (device / 'unrelated.txt').write_text('keep\n', encoding='utf-8')
        self.git(device, 'add', 'unrelated.txt')
        program = controller / 'mask.py'
        (device / 'change.txt').write_text('local work\n', encoding='utf-8')
        overlap = self.public('update', '--device', 'laptop', '--dry-run', program=program)['data']['plan']['targets'][0]
        self.assertEqual((overlap['status'], overlap['reason']), ('blocked', 'source.dirty'))
        self.assertEqual((device / 'change.txt').read_text(encoding='utf-8'), 'local work\n')
        (device / 'change.txt').unlink()
        preview = self.public('update', '--dry-run', program=program)['data']
        self.assertEqual(preview['plan']['candidate']['candidate'], after)
        self.assertEqual([row['name'] for row in preview['plan']['targets']], ['desktop', 'laptop'])
        selected = self.public('update', '--device', 'laptop', '--dry-run', program=program)['data']
        self.assertEqual([row['name'] for row in selected['plan']['targets']], ['laptop'])
        self.assertEqual(selected['plan']['selection']['devices'], ['laptop'])
        approved = preview['plan_hash']
        invalid = self.public('update', '--all', '--approve-plan', approved, program=program, code=2)
        self.assertEqual(invalid['error']['code'], 'invocation.invalid')
        self.assertEqual(invalid['transaction'], 'not_started')
        self.assertFalse((self.controller_home / 'fleet' / 'maintenance-plans').exists())
        self.assertEqual(self.git(device, 'rev-parse', 'HEAD'), before)
        self.assertEqual(self.git(desktop, 'rev-parse', 'HEAD'), before)
        self.assertFalse((device / 'change.txt').exists())
        self.assertEqual(self.git(device, 'rev-parse', 'refs/remotes/origin/main'), before)
        lost = self.public('update', '--approve-plan', approved, program=program, drop='program-update', code=9)
        self.assertEqual([row['status'] for row in lost['data']['device_results']], ['unknown', 'unknown'])
        self.assertEqual(self.git(device, 'rev-parse', 'HEAD'), after)
        self.assertEqual(self.git(desktop, 'rev-parse', 'HEAD'), after)
        retried = self.public('update', '--approve-plan', approved, program=program)['data']
        self.assertEqual([row['receipt']['after'] for row in retried['device_results']], [after, after])
        self.assertEqual(self.git(device, 'diff', '--cached', '--name-only'), 'unrelated.txt')
        self.assertEqual(self.git(controller, 'rev-parse', 'HEAD'), before)
        fleet_source = author / 'mask_fleet.py'
        fleet_source.write_bytes(fleet_source.read_bytes().replace(b"PROTOCOL = 'mask.rpc.v1'", b"PROTOCOL = 'mask.rpc.v2'"))
        self.git(author, 'commit', '-qam', 'incompatible fleet protocol')
        self.git(author, 'push', '-q', str(bare), 'main')
        incompatible = self.public('update', '--dry-run', program=program)['data']['plan']['targets'][0]
        self.assertEqual((incompatible['status'], incompatible['reason']),
                         ('incompatible', 'fleet.program_incompatible'))
        self.assertEqual(self.git(device, 'rev-parse', 'HEAD'), after)

    def test_canonical_project_fast_forward_and_cherry_pick_preserve_staging(self):
        project = self.base / 'main-project'
        self.init_git(project)
        peer_project = self.base / 'branch-project'
        fast_project = self.base / 'fast-project'
        dirty_project = self.base / 'dirty-project'
        self.cli(self.device_home, 'install', 'fixture/alpha', '--project', project, '--no-update', env=self.env)
        for control in ('.mask.json', '.mask.lock.json'):
            self.git(project, 'add', '-f', control)
        (project / '.gitignore').write_text('.agents/\n.claude/\n', encoding='utf-8')
        self.git(project, 'add', '.gitignore')
        self.git(project, 'commit', '-qm', 'base controls')
        bases = {}
        for name, root in [('feature', peer_project), ('same', fast_project), ('dirty', dirty_project)]:
            self.git(self.base, 'clone', '-q', str(project), str(root))
            self.identity(root)
            if name == 'feature':
                self.git(root, 'checkout', '-qb', 'feature')
                (root / 'feature.txt').write_text('feature branch\n', encoding='utf-8')
                self.git(root, 'add', 'feature.txt')
                self.git(root, 'commit', '-qm', 'feature only')
            bases[name] = self.git(root, 'rev-parse', 'HEAD')
            self.cli(self.device_home, 'register', '--project', root, env=self.env)
        grants = self.policy['scopes']
        for name, root in [('primary', project), ('feature', peer_project), ('same', fast_project), ('dirty', dirty_project)]:
            self.git(root, 'remote', 'set-url' if name != 'primary' else 'add', 'origin',
                     'ssh://git@fixture.invalid/one-project.git')
            grants[name] = dict(scope='project', root=str(root), upgrade=True, commit=True,
                                sources=grants['personal']['sources'])
        self.policy['epoch'] += 1
        self.policy['actions'] += ['upgrade-inspect', 'upgrade-apply']
        grants['personal']['upgrade'] = True
        self.authorize(self.policy)
        self.set_peer('laptop', self.device, self.policy, self.device_home, ENTRY)
        (peer_project / 'staged.txt').write_text('unchanged\n', encoding='utf-8')
        self.git(peer_project, 'add', 'staged.txt')
        dirty = dirty_project / '.mask.lock.json'
        dirty.write_bytes(dirty.read_bytes() + b'\n')
        self.cli(self.device_home, 'pin', 'fixture/alpha', '--user', env=self.env)
        skill = self.source / 'skills/alpha/SKILL.md'
        skill.write_bytes(skill.read_bytes() + b'\nUpdated fixture content.\n')
        self.git(self.source, 'commit', '-qam', 'update skill')
        self.git(self.source, 'push', '-q', str(self.remote), 'main')
        selected = self.git(self.source, 'rev-parse', 'HEAD')
        self.cli(self.controller_home, 'tap', 'fetch', 'fixture', env=self.env)
        preview = self.public('upgrade', '--all', '--dry-run')['data']
        [group] = preview['plan']['groups']
        self.assertEqual(group['repository'], 'fixture.invalid/one-project')
        result = self.public('upgrade', '--all', '--approve-plan', preview['plan_hash'], code=9)['data']
        outcomes = {row['scope']: row for row in result['device_results']}
        canonical = group['canonical'][1]
        canonical_commit = outcomes[canonical]['receipt']['commit']
        ff = {'primary', 'same'}.difference({canonical}).pop()
        self.assertEqual(outcomes[ff]['receipt']['commit'], canonical_commit)
        self.assertEqual(outcomes[ff]['receipt']['propagation'], 'fast_forward')
        self.assertEqual(outcomes['feature']['receipt']['propagation'], 'cherry_pick')
        self.assertEqual(self.git(peer_project, 'rev-parse', 'HEAD^'), bases['feature'])
        self.assertEqual(self.git(peer_project, 'diff', '--cached', '--name-only'), 'staged.txt')
        self.assertEqual(self.git(peer_project, 'diff-tree', '--no-commit-id', '--name-only', '-r', 'HEAD'), '.mask.lock.json')
        self.assertEqual(outcomes['dirty']['status'], 'blocked')
        self.assertEqual(self.git(dirty_project, 'rev-parse', 'HEAD'), bases['dirty'])
        self.assertNotIn('commit', outcomes['personal']['receipt'])
        for root in (project, peer_project, fast_project):
            self.assertEqual(json.loads((root / '.mask.lock.json').read_text())['packages'][0]['commit'], selected)

    def test_blocked_project_scopes_use_their_own_exact_candidate(self):
        project = self.base / 'primary'
        self.init_git(project)
        self.cli(self.device_home, 'install', 'fixture/alpha', '--project', project, '--no-update', env=self.env)
        controls = ('.mask.json', '.mask.lock.json')
        self.git(project, 'add', '-f', *controls)
        self.git(project, 'commit', '-qm', 'base controls')
        projects = {'primary': project}
        for name in ('current-dirty', 'current-diverged', 'stale-dirty', 'stale-diverged', 'local-drift'):
            root = self.base / name
            self.git(self.base, 'clone', '-q', str(project), str(root))
            self.identity(root)
            self.git(root, 'checkout', '-qb', name)
            self.cli(self.device_home, 'register', '--project', root, env=self.env)
            projects[name] = root
        grants = self.policy['scopes']
        for name, root in projects.items():
            self.git(root, 'remote', 'set-url' if root != project else 'add', 'origin',
                     'ssh://git@fixture.invalid/one-project.git')
            grants[name] = dict(scope='project', root=str(root), upgrade=True, commit=True,
                                sources=grants['personal']['sources'])
        self.policy['epoch'] += 1
        self.policy['actions'] += ['upgrade-inspect', 'upgrade-apply']
        self.authorize(self.policy)
        self.set_peer('laptop', self.device, self.policy, self.device_home, ENTRY)

        skill = self.source / 'skills/alpha/SKILL.md'
        skill.write_bytes(skill.read_bytes() + b'\nUpdated fixture content.\n')
        self.git(self.source, 'commit', '-qam', 'update skill')
        self.git(self.source, 'push', '-q', str(self.remote), 'main')
        selected = self.git(self.source, 'rev-parse', 'HEAD')
        for home in (self.controller_home, self.device_home):
            self.cli(home, 'tap', 'fetch', 'fixture', env=self.env)
        for name in ('current-dirty', 'current-diverged'):
            self.cli(self.device_home, 'upgrade', '--project', projects[name], '--no-update', env=self.env)
        self.git(projects['current-dirty'], 'add', '.mask.lock.json')
        self.cli(self.device_home, 'pin', 'fixture/alpha', '--project', projects['current-diverged'], env=self.env)
        for name in ('stale-dirty', 'stale-diverged'):
            path = projects[name] / '.mask.lock.json'
            path.write_bytes(path.read_bytes() + b'\n')
        for name in ('current-diverged', 'stale-diverged'):
            self.git(projects[name], 'commit', '-qam', 'different controls on this branch')
        for control in controls:
            shutil.copyfile(projects['current-diverged'] / control, projects['local-drift'] / control)
        missing_link = projects['current-dirty'] / '.agents/skills/alpha'
        missing_link.unlink()

        def project_state(root):
            return (self.git(root, 'rev-parse', 'HEAD'), self.git(root, 'symbolic-ref', 'HEAD'),
                    self.git(root, 'diff', '--cached', '--', *controls),
                    tuple((root / control).read_bytes() for control in controls))

        before = {name: project_state(root) for name, root in projects.items()}
        state_path = self.device_home / 'state.json'
        device_before = state_path.read_bytes()
        preview = self.public('upgrade', '--all', '--dry-run')['data']
        [group] = preview['plan']['groups']
        self.assertEqual(group['canonical'][1], 'primary')
        rows = {row['scope']: row for row in preview['plan']['targets']}
        self.assertEqual(rows['primary']['status'], 'planned')
        canonical_lock = rows['primary']['request']['candidate']['lock']
        self.assertEqual(canonical_lock['packages'][0]['commit'], selected)
        diverged_lock = json.loads((projects['current-diverged'] / '.mask.lock.json').read_text())
        self.assertNotEqual(diverged_lock, canonical_lock)
        for name in ('current-dirty', 'current-diverged'):
            self.assertEqual((rows[name]['status'], rows[name]['reason']), ('not_applicable', 'fleet.scope_current'))
            self.assertNotIn('request', rows[name])
        for name, reason in (('stale-dirty', 'fleet.controls_modified'), ('stale-diverged', 'fleet.controls_diverged'),
                             ('local-drift', 'fleet.local_drift')):
            self.assertEqual((rows[name]['status'], rows[name]['reason']), ('blocked', reason))

        args = ('upgrade', '--project-alias', 'current-dirty')
        no_work = self.public(*args, '--dry-run')
        self.assertFalse(no_work['would_change'])
        [standalone] = no_work['data']['plan']['groups']
        self.assertIsNone(standalone['canonical'])
        result = self.public(*args, '--approve-plan', no_work['data']['plan_hash'], drop='upgrade-apply')
        [row] = result['data']['device_results']
        self.assertEqual((row['status'], row['reason']), ('not_applicable', 'fleet.scope_current'))
        self.assertTrue(result['data']['complete'])
        self.assertFalse(result['changed'])
        self.assertFalse(missing_link.is_symlink())
        self.assertEqual(state_path.read_bytes(), device_before)
        self.assertEqual({name: project_state(root) for name, root in projects.items()}, before)

        stale = self.public('upgrade', '--project-alias', 'stale-dirty', '--dry-run')
        [row] = stale['data']['plan']['targets']
        self.assertEqual((row['status'], row['reason']), ('blocked', 'fleet.commit_ineligible'))
        applied = self.public('upgrade', '--all', '--approve-plan', preview['plan_hash'], code=9)['data']
        results = {row['scope']: row for row in applied['device_results']}
        self.assertEqual(results['primary']['status'], 'applied_verified')
        self.assertFalse(missing_link.is_symlink())
        for name, root in projects.items():
            if name != 'primary':
                self.assertEqual(project_state(root), before[name])
                self.assertEqual(results[name]['status'], rows[name]['status'])
                self.assertNotIn('receipt', results[name])
