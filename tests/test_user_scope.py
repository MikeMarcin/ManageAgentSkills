"""Personal scope beside project scope through the public CLI on a tap-first machine (RFC-MASK-0020; MASK-0100, MASK-0101).

A personal consumer is a v2 declaration in MASK_HOME/user.json with its lock. It starts through ``install --user`` (or
``user init`` and ``user register``); membership changes use ``install``/``remove`` and agent changes use ``set-agents``.
Path.home() reads USERPROFILE on Windows and HOME on POSIX; the fixture points both at ``self.personal``.
"""
import json
import os
import subprocess
import sys

import mask_store as store
from tests.support import ENTRY, TAP, Fixture

ALPHA, BETA = TAP + '/alpha', TAP + '/beta'


def links(root):
    return sorted(path.relative_to(root).as_posix() for path in root.rglob('*') if path.is_symlink())


def remove_link(path):
    """A Windows directory link is removed with rmdir, never followed."""
    os.rmdir(path) if os.name == 'nt' else path.unlink()


class UserScopeTests(Fixture):
    def setUp(self):
        super().setUp()
        self.init()

    def crash(self, label, *command):
        script = ("import os,sys;sys.path.insert(0,sys.argv[1]);import mask,mask_fs;"
                  "mask_fs.checkpoint=lambda label: os._exit(99) if label==sys.argv[2] else None;raise SystemExit(mask.main(sys.argv[3:]))")
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), label, *map(str, command), '--json'],
                             capture_output=True, encoding='utf-8', cwd=self.project, env=self.environment())
        self.assertEqual(run.returncode, 99, (run.stdout, run.stderr))

    def user_links(self):
        return sorted(json.loads((self.home / 'state.json').read_text(encoding='utf-8'))['user']['links'])

    def test_membership_agents_and_home_are_independent(self):
        chosen = self.base / 'personal ü home'
        chosen.mkdir()
        self.install(BETA)
        project_declaration = (self.project / '.mask.json').read_bytes()
        self.call('user', 'init')
        preview = self.call('user', 'register', '--user-home', chosen, '--dry-run')
        self.call('user', 'register', '--user-home', chosen, '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertFalse((chosen / '.mask.json').exists())
        self.assertFalse((chosen / '.agents').exists())
        # Move both home variables to prove the registered home wins for reads and for membership changes.
        different = {'HOME': str(self.base / 'different'), 'USERPROFILE': str(self.base / 'different')}
        shown = self.call('user', 'show', cwd=self.base, env=different)['data']
        self.assertEqual((shown['root'], shown['manifest_path'], shown['scope'], shown['mode']), (str(chosen), str(self.home / 'user.json'), 'user', 'pinned'))
        self.assertEqual(self.call('install', ALPHA, '--user', cwd=self.base, env=different)['data']['root'], str(chosen))
        store_root = (self.home / 'store' / 'v1').resolve()
        for agent_path in ('.agents', '.claude'):
            self.assertTrue((chosen / agent_path / 'skills/alpha').resolve().is_relative_to(store_root), agent_path)
        self.assertEqual(links(self.personal), [])
        self.install(BETA, user=True)
        self.call('remove', ALPHA, '--user')
        self.call('user', 'set-agents', BETA, 'codex', '--apply')
        self.assertEqual(links(chosen), ['.agents/skills/beta'])
        self.call('user', 'set-agents', BETA, '--inherit', '--apply')
        self.assertEqual(links(chosen), ['.agents/skills/beta', '.claude/skills/beta'])
        self.call('remove', BETA, '--user')
        self.assertEqual(links(chosen), [])
        self.assertEqual((self.project / '.mask.json').read_bytes(), project_declaration)
        self.assertEqual(links(self.project), ['.agents/skills/beta', '.claude/skills/beta'])
        before = self.snapshot()
        again = self.call('remove', BETA, '--user')
        self.assertEqual((again['changed'], [warning['code'] for warning in again['warnings']]), (False, ['selection.not_selected']))
        self.assertFalse(self.call('apply', '--user')['changed'])
        self.assertEqual(before, self.snapshot())

    def test_scope_selection_and_parser(self):
        self.install(BETA)
        self.call('project', 'set-agents', BETA, 'codex')  # Declaration only: a planned project link removal.
        self.install(ALPHA, user=True, agents=['codex'])
        self.call('user', 'set-agents', ALPHA, '--inherit')  # Declaration only: a planned personal link.
        self.assertTrue(self.call('apply')['changed'])
        self.assertEqual((links(self.project), links(self.personal)), (['.agents/skills/beta'], ['.agents/skills/alpha']))
        plan = self.call('plan', '--all')['data']
        self.assertEqual((len(plan['projects']), len(plan['users'])), (1, 1))
        self.call('apply', '--all')
        self.assertEqual(links(self.personal), ['.agents/skills/alpha', '.claude/skills/alpha'])
        self.assertTrue(self.call('doctor', '--all', '--check')['data']['healthy'])
        self.assertEqual(len(self.call('project', 'list')['data']['projects']), 1)
        for args in [('apply', '--user', '--all'), ('plan', '--user', '--project', self.project), ('doctor', '--user', '--all'),
                     ('user', 'set'), ('user', 'set-targets'), ('user', 'set-agents', ALPHA),
                     ('install', ALPHA, '--user', '--project', self.project), ('remove', ALPHA, '--user', '--project', self.project),
                     ('link', 'adopt', '--skill', 'alpha', '--target', 'codex', '--expect-source', self.source)]:
            self.assertEqual(self.call(*args, code=2)['error']['code'], 'invocation.invalid', args)
        caps = self.call('capabilities')['data']
        # A bumped write schema must stay readable; asserting only a literal let state v3 drift unnoticed.
        for name, version in caps['schemas'].items():
            if name in caps['readable_versions']:
                self.assertIn(version, caps['readable_versions'][name], name)
        self.assertEqual(caps['readable_versions']['state'], [1, 2, 3])
        commands = {item['name']: item for item in caps['commands']}
        self.assertIn('user.set-agents', commands)
        for name in ('install', 'remove', 'list', 'update'):
            self.assertIn('--user', [flag for argument in commands[name]['arguments'] for flag in argument['flags']], name)

    def test_collision_preflights_both_scopes_and_declaration_edit(self):
        self.install(BETA)
        self.call('project', 'set-agents', BETA, 'codex')  # Declaration only: the project has a planned link removal.
        self.install(ALPHA, user=True, agents=['codex'])
        leaf = self.personal / '.claude/skills/alpha'
        leaf.mkdir(parents=True)
        (leaf / 'mine').write_text('preserve')
        before = self.snapshot()
        self.assertEqual(self.call('user', 'set-agents', ALPHA, '--inherit', '--apply', code=4)['error']['code'], 'target.collision')
        self.assertEqual(before, self.snapshot())
        self.call('user', 'set-agents', ALPHA, '--inherit')
        before = self.snapshot()
        self.assertEqual(self.call('apply', '--all', code=4)['error']['code'], 'target.collision')
        self.assertEqual(before, self.snapshot())
        self.assertEqual(links(self.project), ['.agents/skills/beta', '.claude/skills/beta'], 'the project change is preflighted with the personal one')
        occupied = self.personal / '.agents/skills/beta'
        occupied.mkdir(parents=True)
        (occupied / 'mine').write_text('preserve')
        before = self.snapshot()
        self.assertEqual(self.call('install', BETA, '--user', code=4)['error']['code'], 'target.collision')
        self.assertEqual(before, self.snapshot())

    def test_linked_parent_and_cross_scope_overlap_refuse(self):
        target = self.base / 'external'
        target.mkdir()
        (self.personal / '.agents').symlink_to(target, target_is_directory=True)
        self.call('user', 'init')
        self.call('source', 'fetch')  # A live install acquires the tap before planning; a warm cache keeps the refusal effect-free.
        before = self.snapshot()
        self.assertEqual(self.call('user', 'register', '--user-home', self.personal, code=4)['error']['code'], 'target.parent_link')
        self.assertEqual(self.call('install', ALPHA, '--user', code=4)['error']['code'], 'target.parent_link')
        self.assertEqual(before, self.snapshot())
        self.assertEqual(list(target.iterdir()), [])
        (self.personal / '.agents').unlink()
        self.install(ALPHA, user=True)
        self.call('project', 'init', '--project', self.personal)
        self.assertEqual(self.call('project', 'register', self.personal, code=4)['error']['code'], 'target.overlap')
        nested = self.personal / '.agents/skills/nested'
        nested.mkdir(parents=True)
        self.call('project', 'init', '--project', nested)
        for args in (('project', 'register', nested), ('install', BETA, '--project', nested)):
            self.assertEqual(self.call(*args, code=4)['error']['code'], 'target.overlap', args)
        self.assertEqual(self.call('user', 'register', '--user-home', self.project, code=4)['error']['code'], 'user.already_registered')

    def test_stale_preview_and_observational_reads(self):
        self.install(ALPHA, user=True)
        self.call('user', 'set-agents', ALPHA, 'codex')  # Declaration only: a planned personal link removal.
        before = self.snapshot()
        preview = self.call('plan', '--user')
        self.assertTrue(preview['would_change'])
        for args in (('user', 'show'), ('doctor', '--user'), ('list', '--user'), ('apply', '--user', '--dry-run'),
                     ('install', BETA, '--user', '--dry-run'), ('remove', ALPHA, '--user', '--dry-run'), ('update', '--user', '--dry-run')):
            self.call(*args)
        self.assertEqual(before, self.snapshot())
        self.call('user', 'set-agents', ALPHA, 'claude')
        before = self.snapshot()
        self.assertEqual(self.call('apply', '--user', '--expect-plan-hash', preview['data']['plan_hash'], code=4)['error']['code'], 'plan.stale')
        self.assertEqual(before, self.snapshot())

    def test_v1_state_no_rewrite_upgrade_and_exact_rollback(self):
        # tap add bootstraps the empty registry as state v1; the first personal registration writes state v3 through a v3 journal.
        original = (self.home / 'state.json').read_bytes()
        self.assertEqual(json.loads(original)['schema_version'], 1)
        self.call('user', 'init')
        self.call('user', 'show')
        self.assertEqual(original, (self.home / 'state.json').read_bytes())
        self.crash('state', 'user', 'register', '--user-home', self.personal)
        pending = self.call('recover', '--inspect')['data']['pending']
        self.assertEqual((pending['schema_version'], pending['operation'], pending['before_state']['schema_version'], pending['after_state']['schema_version']),
                         (3, 'user.register', 1, 3))
        self.call('recover', '--rollback')
        self.assertEqual(original, (self.home / 'state.json').read_bytes())
        self.assertTrue((self.home / 'user.json').is_file())
        self.crash('intent', 'user', 'register', '--user-home', self.personal)
        self.call('recover', '--complete')
        state = json.loads((self.home / 'state.json').read_text(encoding='utf-8'))
        self.assertEqual((state['schema_version'], state['user']['root'], state['user']['mode']), (3, str(self.personal), 'pinned'))

    def test_mixed_scope_crash_and_user_declaration_recovery(self):
        self.install(BETA)
        self.call('project', 'set-agents', BETA, 'codex')
        self.install(ALPHA, user=True, agents=['codex'])
        self.call('user', 'set-agents', ALPHA, '--inherit')
        self.crash('link', 'apply', '--all')
        self.assertEqual(self.call('install', BETA, '--user', code=8)['error']['code'], 'recovery.required')
        self.call('recover', '--complete')
        self.assertTrue(self.call('doctor', '--all', '--check')['data']['healthy'])
        self.assertEqual((links(self.project), links(self.personal)), (['.agents/skills/beta'], ['.agents/skills/alpha', '.claude/skills/alpha']))
        controls = {name: (self.home / name).read_bytes() for name in ('user.json', 'user.lock.json', 'state.json')}
        for label in ('manifest', 'lock'):
            with self.subTest(checkpoint=label):
                self.crash(label, 'install', BETA, '--user')
                pending = self.call('recover', '--inspect')['data']['pending']
                self.assertEqual((pending['operation'], sorted(entry['role'] for entry in pending['files'])), ('install', ['user_declaration', 'user_lock']))
                self.call('recover', '--rollback')
                self.assertEqual({name: (self.home / name).read_bytes() for name in controls}, controls)
                self.assertEqual((links(self.project), links(self.personal)), (['.agents/skills/beta'], ['.agents/skills/alpha', '.claude/skills/alpha']))

    def test_recovery_preserves_user_declaration_and_replaced_link(self):
        self.install(ALPHA, user=True)
        self.crash('link', 'install', BETA, '--user')
        leaf = self.personal / '.agents/skills/beta'
        self.assertTrue(leaf.is_symlink(), 'the journal activated this link before the declaration and lock were written')
        declaration = (self.home / 'user.json').read_bytes()
        (self.home / 'user.json').write_text(json.dumps(dict(json.loads(declaration), default_agents=['codex'])) + '\n')
        before = self.snapshot()
        for mode in ('--rollback', '--complete'):
            self.assertEqual(self.call('recover', mode, code=8)['error']['code'], 'recovery.conflict', mode)
            self.assertEqual(before, self.snapshot())
        (self.home / 'user.json').write_bytes(declaration)
        remove_link(leaf)
        leaf.mkdir()
        (leaf / 'mine').write_text('replaced by the user')
        before = self.snapshot()
        for mode in ('--rollback', '--complete'):
            refused = self.call('recover', mode, code=8)['error']
            self.assertEqual((refused['code'], refused['details']['path']), ('recovery.conflict', str(leaf)), mode)
            self.assertEqual(before, self.snapshot())

    def test_adopt_unregister_keep_links_and_unavailable_home(self):
        self.install(ALPHA, user=True)
        row = json.loads((self.home / 'user.lock.json').read_text(encoding='utf-8'))['packages'][0]
        target = store.location(self.home, row['payload_digest'], 'alpha')[1]
        self.call('user', 'unregister', '--keep-links')
        self.assertIsNone(json.loads((self.home / 'state.json').read_text(encoding='utf-8')).get('user'))
        self.assertEqual(links(self.personal), ['.agents/skills/alpha', '.claude/skills/alpha'])
        self.call('user', 'register', '--user-home', self.personal)
        self.assertEqual(self.user_links(), [])
        for agent in ('codex', 'claude'):
            args = ('link', 'adopt', '--user', '--skill', 'alpha', '--target', agent, '--expect-source', target)
            preview = self.call(*args, '--dry-run')
            self.call(*args, '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertFalse(self.call('apply', '--user')['changed'])
        self.assertEqual(self.user_links(), ['.agents/skills/alpha', '.claude/skills/alpha'])
        self.call('user', 'unregister')
        self.assertEqual(links(self.personal), [])
        shown = self.call('user', 'show')['data']
        self.assertEqual((shown['registered'], shown['manifest']['skills']), (False, [dict(source=TAP, id='alpha')]))
        self.call('user', 'register', '--user-home', self.personal, '--apply')
        self.assertEqual(links(self.personal), ['.agents/skills/alpha', '.claude/skills/alpha'])
        moved = self.personal.rename(self.base / 'moved home')
        before = self.snapshot()
        for args in (('update', '--user'), ('update',), ('user', 'set-agents', ALPHA, 'codex', '--apply'), ('user', 'unregister')):
            refused = self.call(*args, code=4)['error']
            self.assertEqual((refused['code'], refused['details']['root']), ('user.unavailable', str(self.personal)), args)
        self.assertEqual([blocker['code'] for blocker in self.call('plan', '--user')['data']['blockers']], ['user.unavailable'])
        self.assertEqual(before, self.snapshot())
        self.call('user', 'unregister', '--keep-links')
        self.assertEqual(links(moved), ['.agents/skills/alpha', '.claude/skills/alpha'])
        self.assertEqual(self.call('plan', '--user', code=4)['error']['code'], 'user.not_registered')


class UserUpdateTests(Fixture):
    """A personal consumer beside a project consumer on the fixture tap; the fetching update validates and preflights both (MASK-0101)."""

    def setUp(self):
        super().setUp()
        self.init()
        self.install(ALPHA)
        self.install(BETA, user=True)

    def controls(self):
        return [self.snapshot(self.project), self.snapshot(self.personal)] + [(self.home / name).read_bytes() for name in ('state.json', 'user.json', 'user.lock.json')]

    def test_user_only_candidate_is_validated(self):
        self.git(self.source, 'rm', '-r', '-q', 'skills/beta')
        self.publish('remove the personal requirement')
        before = self.controls()
        refused = self.call('update', code=4)
        self.assertEqual((refused['error']['code'], refused['error']['details']['skill'], refused['transaction']), ('skill.unknown', BETA, 'not_started'))
        self.assertTrue(refused['data']['fetches'][TAP]['ok'])
        self.assertEqual(before, self.controls())
        self.assertFalse((self.home / 'pending.json').exists())
        self.assertTrue((self.personal / '.agents/skills/beta/SKILL.md').is_file())

    def test_unavailable_user_blocks_before_fetch(self):
        (self.source / 'skills/alpha/notes').write_text('never fetched')
        self.publish('upstream moves')
        self.personal.rename(self.base / 'moved personal')
        before = self.snapshot()  # Includes the tap cache: a fetch would change it.
        for args in (('update',), ('update', '--user')):
            refused = self.call(*args, code=4)
            self.assertEqual((refused['error']['code'], refused['error']['details']['root']), ('user.unavailable', str(self.personal)), args)
            self.assertNotIn('fetches', refused['data'])
        self.assertEqual(before, self.snapshot())
