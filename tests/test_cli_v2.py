"""Accepted public lifecycle and default scopes, through the real CLI."""
import json
from pathlib import Path
import shutil

from tests.public_support import PublicFixture, ENTRY
from tests.support import TAP


class CliV2(PublicFixture):
    entrypoint = ENTRY
    def bootstrap(self):
        self.assertTrue(self.machine('tap', TAP, self.upstream)['ok'])

    def raw(self, *args, **kwargs):
        # Qualification never updates the real program checkout.
        if args and args[0] in ('install', 'upgrade') and '--no-update' not in args:
            args = (*args, '--no-update')
        return PublicFixture.raw(self, *args, **kwargs)

    def test_checkout_user_all_and_outside_default(self):
        self.assertTrue(self.machine('install', 'alpha')['ok'])
        self.assertTrue(self.machine('install', 'beta', '--user')['ok'])
        other = self.base / 'other'
        other.mkdir()
        self.git(other, 'init', '-b', 'main')
        self.assertTrue(self.machine('install', 'alpha', '--project', other)['ok'])
        before = {root: (root / '.mask.lock.json').read_bytes() for root in (self.project, other)}
        user = (self.home / 'user.lock.json').read_bytes()
        (self.source / 'skills/alpha/SKILL.md').write_text('---\nname: alpha\ndescription: Next version\n---\nNew.\n')
        self.publish()
        run = self.machine('upgrade')
        self.assertTrue(run['ok'], run)
        self.assertEqual(run['data']['scopes'], [dict(root=str(self.project), scope='project')])
        self.assertNotEqual(before[self.project], (self.project / '.mask.lock.json').read_bytes())
        self.assertEqual(before[other], (other / '.mask.lock.json').read_bytes())
        self.assertEqual(user, (self.home / 'user.lock.json').read_bytes())
        run = self.machine('upgrade', '--all')
        self.assertTrue(run['ok'], run)
        self.assertEqual(len(run['data']['scopes']), 3)
        for command in ('upgrade', 'repair', 'status'):
            outside = self.machine(command, cwd=self.base)
            self.assertEqual(outside['error']['code'], 'scope.required', outside)
            self.assertFalse(self.machine(command, '--all', '--user')['ok'])
        self.assertTrue(self.machine('status', '--user')['ok'])
        self.assertEqual(len(self.machine('list', '--all')['data']['consumers']), 3)
        self.assertEqual(self.machine()['command'], 'status')

    def test_preview_fresh_install_is_frozen_and_no_consumer_files_exist(self):
        self.assertTrue(self.machine('tap', 'fetch')['ok'])
        preview = self.machine('install', 'alpha', '--dry-run')
        self.assertTrue(preview['ok'], preview)
        self.assertNotIn('plan', preview['data'])
        self.assertFalse((self.project / '.mask.json').exists())
        run = self.machine('install', 'alpha', '--approve-plan', preview['data']['plan_hash'])
        self.assertTrue(run['ok'], run)
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())
        self.assertTrue(self.machine('uninstall', 'alpha')['ok'])
        self.assertFalse((self.project / '.agents/skills/alpha').exists())
        self.assertTrue(self.machine('unregister')['ok'])
        self.assertTrue((self.project / '.mask.json').exists())

    def test_register_fresh_linked_worktree_preserves_lock(self):
        self.assertTrue(self.machine('install', 'alpha')['ok'])
        self.git(self.project, 'config', 'user.name', 'Fixture')
        self.git(self.project, 'config', 'user.email', 'fixture@example.invalid')
        self.git(self.project, 'add', '.mask.json', '.mask.lock.json')
        self.git(self.project, 'commit', '-m', 'selection')
        worktree = self.base / 'worktree'
        self.git(self.project, 'worktree', 'add', '-b', 'fixture', worktree)
        before = (worktree / '.mask.lock.json').read_bytes()
        run = self.machine('register', cwd=worktree)
        self.assertTrue(run['ok'], run)
        self.assertTrue((worktree / '.agents/skills/alpha').is_symlink())
        self.assertEqual(before, (worktree / '.mask.lock.json').read_bytes())
        self.assertFalse(self.machine('register', cwd=worktree)['changed'])

    def test_pin_and_unpin_all_keep_version_until_upgrade(self):
        self.assertTrue(self.machine('install', 'alpha', 'beta')['ok'])
        self.assertTrue(self.machine('pin', 'alpha')['ok'])
        self.assertTrue(next(row for row in self.machine('list')['data']['skills'] if row['id'] == 'alpha')['pinned'])
        self.assertIn('HELD', self.human('list').stdout)
        self.assertTrue(all(row['pinned'] for row in self.machine('list', '--all')['data']['rows'] if row['name'] == 'alpha'))
        original = json.loads((self.project / '.mask.lock.json').read_text())['packages']
        for name in ('alpha', 'beta'):
            (self.source / f'skills/{name}/SKILL.md').write_text(f'---\nname: {name}\ndescription: New\n---\nNew.\n')
        self.publish()
        run = self.machine('upgrade')
        self.assertTrue(run['ok'], run)
        after = json.loads((self.project / '.mask.lock.json').read_text())['packages']
        self.assertEqual(original[0], after[0])
        self.assertNotEqual(original[1]['commit'], after[1]['commit'])
        self.assertTrue(self.machine('unpin', '--all')['ok'])
        self.assertEqual(after, json.loads((self.project / '.mask.lock.json').read_text())['packages'])
        self.assertTrue(self.machine('upgrade')['ok'])
        self.assertNotEqual(original[0]['commit'], json.loads((self.project / '.mask.lock.json').read_text())['packages'][0]['commit'])
        self.assertTrue(self.machine('install', 'alpha', '--user')['ok'])
        self.assertTrue(self.machine('pin', '--all', '--user')['ok'])
        self.assertTrue(json.loads((self.home / 'user.json').read_text())['skills'][0]['pinned'])
        self.assertFalse(self.machine('pin', 'alpha', '--all')['ok'])
        self.assertFalse(self.machine('pin')['ok'])

    def test_breaking_surface_help_and_catalog(self):
        for old in ('ensure', 'doctor', 'apply', 'plan', 'remove', 'inventory'):
            self.assertEqual(self.machine(old)['error']['code'], 'invocation.invalid')
        self.assertTrue(self.machine('tap', 'fetch')['ok'])
        self.assertEqual(len(self.machine('search', 'alpha')['data']['skills']), 1)
        self.assertEqual(self.machine('info', 'alpha')['data']['id'], 'alpha')
        workflow = self.machine('info', 'implement-rfc')['data']['workflow']
        self.assertTrue(workflow['project']['roles'])
        self.assertIsInstance(workflow['project']['roles'], list)
        self.assertEqual(self.machine('capabilities')['schema_version'], 2)
        self.assertEqual(self.machine('integration', 'run', '--event', 'manual')['error']['code'], 'invocation.invalid')
        self.assertIn('This checkout:', self.human('--help').stdout)
        self.assertEqual(self.human('tap').returncode, 0)
        self.assertTrue(self.machine('register')['ok'])

    def test_previews_status_and_repair_accept_and_preserve_cached_bytecode(self):
        self.assertTrue(self.machine('install', 'alpha')['ok'])
        payload = (self.project / '.agents/skills/alpha').resolve()
        bytecode = payload / '__pycache__/untracked.pyc'
        bytecode.parent.mkdir()
        bytecode.write_bytes(b'host-generated cache')
        for command in (('upgrade', '--dry-run'), ('repair', '--dry-run'), ('status',), ('cleanup', '--dry-run')):
            result = self.machine(*command)
            self.assertTrue(result['ok'], result)
            self.assertEqual(bytecode.read_bytes(), b'host-generated cache')
        self.assertTrue(self.machine('repair')['ok'])
        self.assertEqual(bytecode.read_bytes(), b'host-generated cache')

    def test_normal_linked_import_preserves_preview_consent_and_readiness(self):
        import os
        import subprocess
        import sys
        (self.source / 'skills/alpha/helper.py').write_text('VALUE = 42\n')
        self.publish('importable helper')
        self.assertTrue(self.machine('tap', 'fetch')['ok'])
        self.assertTrue(self.machine('install', 'alpha')['ok'])
        linked = self.project / '.agents/skills/alpha'
        preview = self.machine('repair', '--dry-run')
        self.assertTrue(preview['ok'], preview)
        environment = {key: value for key, value in os.environ.items()
                       if key not in ('PYTHONDONTWRITEBYTECODE', 'PYTHONPYCACHEPREFIX')}
        subprocess.run([sys.executable, '-c',
                        'import sys; sys.path.insert(0, sys.argv[1]); import helper; assert helper.VALUE == 42',
                        str(linked)], env=environment, check=True)
        caches = list((linked / '__pycache__').glob('helper.*.pyc'))
        self.assertTrue(caches)
        before = {path.name: path.read_bytes() for path in caches}
        second = self.machine('repair', '--dry-run')
        self.assertEqual(second['data']['plan_hash'], preview['data']['plan_hash'])
        applied = self.machine('repair', '--approve-plan', preview['data']['plan_hash'])
        self.assertTrue(applied['ok'], applied)
        for command in (('status', '--check'), ('upgrade', '--dry-run'), ('upgrade',), ('repair',), ('cleanup', '--dry-run')):
            result = self.machine(*command)
            self.assertTrue(result['ok'], result)
        self.assertEqual({path.name: path.read_bytes() for path in caches}, before)


from tests.test_setup import SetupFixture, GENERATED
from tests.public_support import CONSUMER_CONTEXT


class SetupV2(SetupFixture):
    entrypoint = ENTRY
    bootstrap = CliV2.bootstrap
    raw = CliV2.raw

    def setUp(self):
        PublicFixture.setUp(self)
        self.package = self.source / 'skills/implement-rfc'
        shutil.rmtree(self.package)
        shutil.copytree(GENERATED, self.package)
        self.sentinel = self.base / 'setup-launches.txt'
        self.write_script()
        self.publish('generated package')
        shutil.copytree(CONSUMER_CONTEXT, self.project / '.mask')
        self.lock = self.project / '.mask/generated/implement-rfc/native-roles.lock.json'
        self.assertTrue(self.machine('tap', 'fetch')['ok'])

    def reviewed(self, *args):
        preview = self.machine(*args, '--dry-run')
        self.assertTrue(preview['ok'], preview)
        run = self.machine(*args, '--approve-plan', preview['data']['plan_hash'])
        self.assertTrue(run['ok'], run)
        return run

    def test_install_review_preserves_checkout_then_runs_setup_once(self):
        before = (self.home / 'state.json').read_bytes()
        run = self.machine('install', 'implement-rfc')
        self.assertEqual(run['error']['code'], 'confirmation.required', run)
        self.assertFalse((self.project / '.mask.json').exists())
        self.assertEqual(before, (self.home / 'state.json').read_bytes())
        self.assertEqual(self.links(), [])
        self.assertEqual(self.launches(), 0)
        run = self.reviewed('install', 'implement-rfc')
        self.assertEqual(self.launches(), 1)
        self.assertEqual(run['data']['workflow'][str(self.project)], 'complete')
        self.assertFalse(self.machine('install', 'implement-rfc')['changed'])
        self.assertEqual(self.launches(), 1)

    def test_pinned_upgrade_keeps_commit_and_repairs_missing_generated_roles(self):
        self.reviewed('install', 'implement-rfc')
        self.assertTrue(self.machine('pin', 'implement-rfc')['ok'])
        old = (self.project / '.mask.lock.json').read_bytes()
        path = self.project / '.codex/agents/rfc-integrator.toml'
        path.unlink()
        (self.package / 'scripts/helper.py').write_text((self.package / 'scripts/helper.py').read_text() + '\n# newer\n')
        self.publish()
        self.assertTrue(self.machine('tap', 'fetch')['ok'])
        run = self.reviewed('upgrade')
        self.assertEqual(old, (self.project / '.mask.lock.json').read_bytes())
        self.assertTrue(path.is_file())
        self.assertEqual(self.launches(), 2)

    def test_modified_role_replacement_review_and_backup(self):
        self.reviewed('install', 'implement-rfc')
        path = self.project / '.codex/agents/rfc-integrator.toml'
        custom = 'name = "rfc-integrator"\nmodel = "custom"\n'
        path.write_text(custom)
        state = (self.home / 'state.json').read_bytes()
        refused = self.machine('repair')
        self.assertEqual(refused['error']['code'], 'confirmation.required', refused)
        self.assertEqual(path.read_text(), custom)
        self.assertEqual(state, (self.home / 'state.json').read_bytes())
        actions = refused['data']['review']['actions']
        self.assertIn(str(path), [row['path'] for row in actions if row['kind'] == 'file.backup_replace'])
        repaired = self.reviewed('repair')
        self.assertNotEqual(path.read_text(), custom)
        self.assertTrue(any(Path(row['path']).read_text() == custom for row in repaired['data']['backups']))
        preview = self.machine('cleanup', '--dry-run')
        self.assertTrue(preview['ok'], preview)
        self.assertTrue(any(row['kind'] == 'backup' for row in preview['data']['candidates']), preview)
        clean = self.machine('cleanup', '--approve-plan', preview['data']['plan_hash'])
        self.assertTrue(clean['ok'], clean)
        self.assertTrue(path.exists())
        self.assertFalse(list((self.home / 'backups').iterdir()))

    def test_stale_setup_review_does_not_create_declaration(self):
        preview = self.machine('install', 'implement-rfc', '--dry-run')
        (self.project / '.mask/skill-config/implement-rfc/project.md').write_text('changed input\n')
        run = self.machine('install', 'implement-rfc', '--approve-plan', preview['data']['plan_hash'])
        self.assertEqual(run['error']['code'], 'plan.stale', run)
        self.assertFalse((self.project / '.mask.json').exists())
        self.assertEqual(self.launches(), 0)

    def test_failure_reports_committed_links_but_never_readiness(self):
        self.write_script(before='    raise RuntimeError("fixture failure")\n')
        self.publish('fails')
        self.machine('tap', 'fetch')
        preview = self.machine('install', 'implement-rfc', '--dry-run')
        run = self.machine('install', 'implement-rfc', '--approve-plan', preview['data']['plan_hash'])
        self.assertEqual(run['error']['code'], 'setup.failed', run)
        self.assertTrue(run['changed'])
        self.assertEqual(run['transaction'], 'committed')
        self.assertEqual(len(self.links()), 2)
        self.assertEqual(self.launches(), 1)

    def test_one_terminal_review_and_decline_preserve_consumers(self):
        import os
        if os.name == 'nt':
            self.skipTest('POSIX terminal test; native Windows console remains separate')
        code, text = self.terminal('install', 'implement-rfc', '--no-update', answer=b'n\n')
        self.assertEqual(code, 4, text)
        self.assertEqual(text.count('[y/N]'), 1)
        self.assertFalse((self.project / '.mask.json').exists())
        self.assertEqual(self.launches(), 0)
        code, text = self.terminal('install', 'implement-rfc', '--no-update', answer=b'y\n')
        self.assertEqual(code, 0, text)
        self.assertEqual(text.count('[y/N]'), 1)
        self.assertEqual(self.launches(), 1)

    def test_public_setup_crash_recovery_never_reruns_script(self):
        import subprocess, sys
        preview = self.machine('install', 'implement-rfc', '--dry-run')
        script = """
import sys, os
sys.path.insert(0, sys.argv[1])
import mask, mask_fs
mask_fs.checkpoint = lambda label: os._exit(99) if label == 'setup.exited' else None
raise SystemExit(mask.main(sys.argv[2:]))
"""
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), 'install', 'implement-rfc',
                              '--no-update', '--approve-plan', preview['data']['plan_hash'], '--json'],
                             cwd=self.project, env=self.environment(), capture_output=True, text=True, timeout=60)
        self.assertEqual(run.returncode, 99, run.stdout + run.stderr)
        self.assertEqual(self.machine('recover', '--complete')['error']['code'], 'setup.unverified')
        self.assertTrue(self.machine('recover', '--rollback')['ok'])
        self.assertEqual(self.launches(), 1)
        self.assertEqual(len(self.links()), 2)

    def test_agent_setter_reviews_new_generated_roles_before_selection_change(self):
        self.reviewed('install', 'implement-rfc', '--agent', 'codex')
        before = (self.project / '.mask.json').read_bytes()
        refused = self.machine('project', 'set-agents', 'agentskills/implement-rfc', 'claude', 'codex')
        self.assertEqual(refused['error']['code'], 'confirmation.required', refused)
        self.assertEqual(before, (self.project / '.mask.json').read_bytes())
        ready = self.reviewed('project', 'set-agents', 'agentskills/implement-rfc', 'claude', 'codex')
        self.assertEqual(ready['data']['workflow'][str(self.project)], 'complete')
        self.assertTrue((self.project / '.claude/agents/rfc-integrator.md').is_file())


class CleanupV2(PublicFixture):
    entrypoint = ENTRY
    bootstrap = CliV2.bootstrap
    raw = CliV2.raw

    def test_untapped_cache_cleanup_and_unknown_file_protection(self):
        self.assertTrue(self.machine('tap', 'fetch')['ok'])
        cache = Path(json.loads((self.home / 'config.json').read_text())['sources'][TAP]['cache'])
        self.assertTrue(self.machine('untap', TAP)['ok'])
        unknown = cache / 'objects/notes'
        unknown.write_text('unrelated file')
        preview = self.machine('cleanup', '--dry-run')
        self.assertEqual(preview['data']['candidates'], [])
        self.assertTrue(any(row['path'] == str(cache) for row in preview['data']['preserved']))
        unknown.unlink()  # The fixture owner removes its own file; MASK must preserve it.
        preview = self.machine('cleanup', '--dry-run')
        self.assertEqual([row['kind'] for row in preview['data']['candidates']], ['source-cache'], preview)
        result = self.machine('cleanup', '--approve-plan', preview['data']['plan_hash'])
        self.assertTrue(result['ok'], result)
        self.assertFalse(cache.exists())

    def test_cleanup_references_unknown_content_and_stale_review(self):
        self.assertTrue(self.machine('install', 'alpha')['ok'])
        old = next((self.home / 'store/v1').iterdir())
        (self.source / 'skills/alpha/SKILL.md').write_text('---\nname: alpha\ndescription: Updated\n---\nNew.\n')
        self.publish()
        self.assertTrue(self.machine('upgrade')['ok'])
        unknown = self.home / 'store/v1/unknown'
        unknown.mkdir()
        (unknown / 'mine').write_text('mine')
        preview = self.machine('cleanup', '--dry-run')
        self.assertTrue(preview['ok'], preview)
        self.assertEqual([row['path'] for row in preview['data']['candidates']], [str(old)])
        refused = self.machine('cleanup')
        self.assertEqual(refused['error']['code'], 'confirmation.required')
        self.assertTrue(old.exists())
        self.assertTrue(self.machine('pin', 'alpha')['ok'])
        stale = self.machine('cleanup', '--approve-plan', preview['data']['plan_hash'])
        self.assertEqual(stale['error']['code'], 'plan.stale')
        preview = self.machine('cleanup', '--dry-run')
        result = self.machine('cleanup', '--approve-plan', preview['data']['plan_hash'])
        self.assertTrue(result['ok'], result)
        self.assertFalse(old.exists())
        self.assertEqual((unknown / 'mine').read_text(), 'mine')
        self.assertTrue((self.home / 'operation.lock').exists())
        self.assertTrue(self.machine('status')['data']['healthy'])

    def test_cleanup_lifecycle_lock_blocks_during_preparation(self):
        import mask_core
        self.machine('install', 'alpha')
        with mask_core.writer_lock(self.home, name='lifecycle.lock'):
            run = self.machine('cleanup')
            self.assertEqual(run['error']['code'], 'lock.busy', run)
