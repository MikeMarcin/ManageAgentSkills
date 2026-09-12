"""Declared native roles without rendering (MASK-0088, RFC-MASK-0019 AC01/AC02/AC03/AC06).

Every case runs the public CLI as a subprocess against a disposable source and
consumer. The synthetic pack fixtures use ``fixture-model-do-not-run`` and are
never installed into a real host directory.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from tests.support import Fixture, ENTRY

PACK = ENTRY.parent / 'docs/rfcs/assets/mask-corrective-ux-readiness'
STATIC = PACK / 'fixtures/static-package'
GENERATED = PACK / 'fixtures/generated-package'
CONTEXT = PACK / 'fixtures/consumer/.mask'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


class WorkflowFixture(Fixture):
    def setUp(self):
        super().setUp()
        self.init()

    def add_package(self, name, package):
        shutil.copytree(package, self.source / 'skills' / name)
        self.git(self.source, 'add', 'skills')
        self.git(self.source, 'commit', '-q', '-m', f'add {name}')

    def consumer(self, skills, targets=None):
        shutil.copytree(CONTEXT, self.project / '.mask')
        self.declare(skills, targets)
        self.call('project', 'register', self.project)
        self.call('integration', 'approve', '--project', self.project)

    def roles(self, data, skill='implement-rfc'):
        for entry in data['data']['workflow_readiness']:
            for item in entry['skills']:
                if item['skill'] == skill:
                    return {(row['agent'], row['name']): row for row in item['roles']}
        return {}

    def contract(self, data, skill='implement-rfc'):
        for entry in data['data']['workflow_readiness']:
            for item in entry['skills']:
                if item['skill'] == skill:
                    return item['contract']
        return {}

    def owned(self):
        return json.loads((self.home / 'state.json').read_text(encoding='utf-8'))['projects'][str(self.project)].get('native_roles', {})


class StaticRoles(WorkflowFixture):
    def setUp(self):
        super().setUp()
        self.add_package('implement-rfc', STATIC)

    def test_missing_roles_deploy_exactly_and_edited_roles_are_preserved(self):
        self.consumer(['alpha', 'implement-rfc'])
        stale = self.project / '.codex/agents/rfc-worker.toml'
        stale.parent.mkdir(parents=True)
        stale.write_text('# older rfc-worker definition\n', encoding='utf-8')
        check = self.call('ensure', '--check', code=7)
        self.assertEqual(check['error']['code'], 'readiness.drift')
        self.assertEqual(self.roles(check)[('codex', 'rfc-integrator')]['state'], 'missing')
        self.assertEqual(self.roles(check)[('codex', 'rfc-worker')]['state'], 'modified')
        self.assertFalse((self.project / '.codex/agents/rfc-integrator.toml').exists())
        result = self.call('ensure', code=4)
        self.assertEqual(result['error']['code'], 'workflow.incomplete')
        self.assertEqual(result['transaction'], 'committed')
        self.assertEqual(result['data']['readiness'], 'workflow_incomplete')
        self.assertTrue((self.project / '.agents/skills/implement-rfc').is_symlink())
        for agent, suffix in (('codex', 'toml'), ('claude', 'md')):
            leaf = self.project / f'.{agent}/agents/rfc-integrator.{suffix}'
            self.assertEqual(leaf.read_bytes(), (STATIC / f'runtime/roles/{agent}/rfc-integrator.{suffix}').read_bytes())
            self.assertFalse(leaf.is_symlink())
        self.assertEqual(stale.read_text(encoding='utf-8'), '# older rfc-worker definition\n')
        integrator = self.roles(result)[('codex', 'rfc-integrator')]
        self.assertEqual(integrator['route'], {'model': 'fixture-model-do-not-run'})
        self.assertEqual(integrator['host_load'], 'not_verified')
        self.assertIn('.codex/agents/rfc-integrator.toml', self.owned())
        self.assertNotIn('.codex/agents/rfc-worker.toml', self.owned())
        again = self.call('ensure', code=4)
        self.assertFalse(again['changed'])
        self.assertEqual(again['error']['details']['workflow'], ['implement-rfc codex/rfc-worker: modified'])
        stale.unlink()
        ready = self.call('ensure')
        self.assertEqual(ready['data']['readiness'], 'ready_legacy_unpinned')
        self.assertEqual(ready['data']['scope_readiness'][0]['workflow'], 'complete')
        self.assertEqual(stale.read_bytes(), (STATIC / 'runtime/roles/codex/rfc-worker.toml').read_bytes())
        before = self.snapshot()
        self.assertFalse(self.call('ensure')['changed'])
        self.call('ensure', '--check')
        self.assertEqual(before, self.snapshot())

    def test_human_output_names_the_missing_role_and_keeps_json_out(self):
        self.consumer(['implement-rfc'])
        run = subprocess.run([sys.executable, '-B', str(ENTRY), 'ensure', '--check', '--project', str(self.project)], capture_output=True, encoding='utf-8',
                             env=dict(os.environ, MASK_HOME=str(self.home), PYTHONDONTWRITEBYTECODE='1'), stdin=subprocess.DEVNULL)
        self.assertEqual(run.returncode, 7)
        self.assertIn('.codex/agents/rfc-integrator.toml', run.stderr)
        self.assertIn('role file(s): missing', run.stderr)
        self.assertIn('implement-rfc: needs deployment', run.stderr)
        self.assertNotIn('implement-rfc: ready', run.stderr)
        self.assertNotIn('{', run.stdout + run.stderr)

    def test_selected_targets_bound_the_requirement_set(self):
        self.consumer(['implement-rfc'], targets=['codex'])
        result = self.call('ensure')
        roles = self.roles(result)
        self.assertEqual(roles[('claude', 'rfc-integrator')]['state'], 'not_applicable')
        self.assertIsNone(roles[('claude', 'rfc-integrator')]['path'])
        self.assertEqual(roles[('codex', 'rfc-integrator')]['state'], 'ok')
        self.assertFalse((self.project / '.claude').exists())
        self.assertTrue((self.project / '.codex/agents/rfc-integrator.toml').is_file())

    def test_fresh_clone_with_tracked_roles_passes_without_adoption(self):
        origin = self.base / 'origin'
        origin.mkdir()
        self.git(origin, 'init', '-b', 'main')
        self.git(origin, 'config', 'user.name', 'Fixture')
        self.git(origin, 'config', 'user.email', 'fixture@example.invalid')
        shutil.copytree(CONTEXT, origin / '.mask')
        (origin / '.mask.json').write_text(json.dumps(dict(schema_version=1, skills=['implement-rfc'])) + '\n')
        for agent, suffix in (('codex', 'toml'), ('claude', 'md')):
            shutil.copytree(STATIC / f'runtime/roles/{agent}', origin / f'.{agent}/agents')
        (origin / 'README.md').write_text('consumer docs\n')
        self.git(origin, 'add', '-A')
        self.git(origin, 'commit', '-q', '-m', 'checked-in roles')
        clone = self.base / 'clone'
        subprocess.run(['git', 'clone', '-q', str(origin), str(clone)], check=True, capture_output=True)
        self.call('project', 'register', clone, cwd=clone)
        self.call('integration', 'approve', '--project', clone, cwd=clone)
        result = self.call('ensure', '--project', clone, cwd=clone)
        self.assertEqual(result['data']['scope_readiness'][0]['workflow'], 'complete')
        self.assertFalse([a for a in result['actions'] if a['kind'].startswith('native_role')])
        roles = self.roles(result)
        self.assertEqual({row['state'] for row in roles.values()}, {'ok'})
        self.assertEqual({row['ownership'] for row in roles.values()}, {'repository-owned'})
        self.assertNotIn('native_roles', json.loads((self.home / 'state.json').read_text(encoding='utf-8'))['projects'][str(clone)])
        self.assertEqual(self.git(clone, 'status', '--porcelain', '--untracked-files=no'), '', 'tracked bytes and index unchanged')
        # W05: unrelated content changes do not touch the role fingerprint.
        (clone / 'README.md').write_text('consumer docs, edited\n')
        before = self.snapshot(clone)
        self.call('ensure', '--project', clone, '--check', cwd=clone)
        self.assertEqual(before, self.snapshot(clone))
        # Removing the skill keeps repository-owned roles.
        self.call('project', 'unrequire', 'implement-rfc', '--project', clone, '--apply', cwd=clone)
        self.assertTrue((clone / '.codex/agents/rfc-integrator.toml').is_file())
        self.assertEqual(sorted(line.split()[-1] for line in self.git(clone, 'status', '--porcelain', '--untracked-files=no').splitlines()), ['.mask.json', 'README.md'])

    def test_unrequire_retires_unchanged_managed_roles_and_releases_edited_ones(self):
        self.consumer(['alpha', 'implement-rfc'])
        self.call('ensure')
        edited = self.project / '.codex/agents/rfc-scout.toml'
        edited.write_text('# my local scout\n', encoding='utf-8')
        result = self.call('project', 'unrequire', 'implement-rfc', '--apply')
        removed = [a for a in result['actions'] if a['kind'] == 'native_role.remove']
        self.assertEqual(len(removed), 15)
        self.assertEqual([w['code'] for w in result['warnings']], ['native_role.released'])
        self.assertTrue(edited.is_file())
        self.assertFalse((self.project / '.codex/agents/rfc-integrator.toml').exists())
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())
        self.assertEqual(self.owned(), {})

    def test_crash_rolls_back_or_completes_role_writes(self):
        self.consumer(['implement-rfc'])
        script = """
import sys,os
sys.path.insert(0, sys.argv[1])
import mask,mask_fs
mask_fs.checkpoint = lambda label: os._exit(99) if label == sys.argv[2] else None
mask.main(sys.argv[3:])
"""
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), 'native_role', 'ensure', '--project', str(self.project), '--home', str(self.home), '--json'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 99, run.stderr)
        self.assertTrue((self.home / 'pending.json').is_file())
        pending = json.loads((self.home / 'pending.json').read_text(encoding='utf-8'))
        self.assertEqual(pending['schema_version'], 3)
        self.assertEqual(len(pending['native_roles']), 16)
        self.assertEqual(self.call('ensure', code=8)['error']['code'], 'recovery.required')
        self.call('recover', '--rollback')
        self.assertFalse((self.project / '.codex/agents/rfc-integrator.toml').exists())
        self.assertFalse((self.project / '.agents/skills/implement-rfc').exists())
        self.assertEqual(self.owned(), {})
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), 'native_role', 'ensure', '--project', str(self.project), '--home', str(self.home), '--json'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 99, run.stderr)
        first = self.project / '.claude/agents/rfc-integrator.md'  # The first journal entry, already written before the crash.
        self.assertTrue(first.is_file())
        first.write_text('# replaced during recovery\n', encoding='utf-8')
        self.assertEqual(self.call('recover', '--complete', code=8)['error']['code'], 'recovery.conflict')
        first.unlink()
        self.call('recover', '--complete')
        self.assertEqual((self.project / '.codex/agents/rfc-integrator.toml').read_bytes(), (STATIC / 'runtime/roles/codex/rfc-integrator.toml').read_bytes())
        self.assertEqual(self.call('ensure')['data']['scope_readiness'][0]['workflow'], 'complete')

    def test_invalid_assets_and_role_content_block_readiness(self):
        self.consumer(['implement-rfc'])
        asset = self.source / 'skills/implement-rfc/runtime/roles/codex/rfc-integrator.toml'
        descriptor = self.source / 'skills/implement-rfc/mask-workflow.json'
        original = asset.read_bytes()
        asset.write_bytes(original + b'# drifted\n')
        self.assertEqual(self.call('ensure', code=4)['error']['code'], 'workflow.invalid')
        self.assertFalse((self.project / '.agents/skills/implement-rfc').exists())
        value = json.loads(descriptor.read_text(encoding='utf-8'))

        def republish(data):
            asset.write_bytes(data)
            for role in value['native_roles']:
                if role['asset']['path'].endswith('codex/rfc-integrator.toml'):
                    role['asset']['sha256'] = sha256(data)
            descriptor.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')
        republish(original + b'[hooks]\nenabled = true\n')
        refused = self.call('ensure', code=4)
        self.assertEqual(refused['error']['code'], 'workflow.role_invalid')
        self.assertEqual(refused['error']['details']['field'], 'hooks')
        republish(original.replace(b'name = "rfc-integrator"', b'name = "rfc-critical-integrator"'))
        drift = self.call('ensure', code=4)
        self.assertEqual(drift['error']['code'], 'workflow.role_invalid')
        self.assertEqual(drift['error']['details']['declared'], 'rfc-critical-integrator')
        republish(original)
        self.assertEqual(self.call('ensure')['data']['scope_readiness'][0]['workflow'], 'complete')

    def test_two_skills_with_different_role_bytes_collide_and_are_preserved(self):
        other = self.source / 'skills/other-flow'
        shutil.copytree(STATIC, other)
        (other / 'SKILL.md').write_text('---\nname: other-flow\ndescription: Second synthetic workflow\n---\n\nFixture only.\n', encoding='utf-8')
        asset = other / 'runtime/roles/codex/rfc-integrator.toml'
        data = asset.read_bytes().replace(b'Fixture identity only.', b'Other identity only.')
        asset.write_bytes(data)
        value = json.loads((other / 'mask-workflow.json').read_text(encoding='utf-8'))
        value['native_roles'] = [role for role in value['native_roles'] if role['asset']['path'].endswith('codex/rfc-integrator.toml')]
        value['native_roles'][0]['asset']['sha256'] = sha256(data)
        (other / 'mask-workflow.json').write_text(json.dumps(value) + '\n', encoding='utf-8')
        self.git(self.source, 'add', 'skills')
        self.git(self.source, 'commit', '-q', '-m', 'second workflow')
        self.consumer(['implement-rfc', 'other-flow'])
        result = self.call('ensure', code=4)
        self.assertEqual(result['error']['code'], 'workflow.incomplete')
        self.assertEqual(self.roles(result)[('codex', 'rfc-integrator')]['state'], 'collision')
        self.assertEqual(self.roles(result, 'other-flow')[('codex', 'rfc-integrator')]['state'], 'collision')
        self.assertFalse((self.project / '.codex/agents/rfc-integrator.toml').exists())
        self.assertTrue((self.project / '.codex/agents/rfc-worker.toml').is_file())


class CheckedInGeneratedRoles(WorkflowFixture):
    """Consumer-checked-in generated roles vouched for by the portable lock; no script ever runs."""

    def setUp(self):
        super().setUp()
        self.add_package('implement-rfc', GENERATED)
        self.consumer(['implement-rfc'])
        self.roles_dir = {agent: self.project / f'.{agent}/agents' for agent in ('codex', 'claude')}
        self.roles_dir['codex'].mkdir(parents=True)
        self.roles_dir['claude'].mkdir(parents=True)
        (self.roles_dir['codex'] / 'rfc-integrator.toml').write_text('name = "rfc-integrator"\nmodel = "fixture-model-do-not-run"\n', encoding='utf-8')
        (self.roles_dir['claude'] / 'rfc-integrator.md').write_text('---\nname: rfc-integrator\nmodel: fixture-model-do-not-run\n---\n\nFixture.\n', encoding='utf-8')
        self.lock = self.project / '.mask/generated/implement-rfc/native-roles.lock.json'
        self.write_lock()

    def write_lock(self, path=None):
        path = path or self.lock
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = (self.source / 'skills/implement-rfc/mask-workflow.json').read_bytes()
        path.write_text(json.dumps(dict(
            schema_version=1, contract_sha256=sha256(descriptor),
            inputs={'project-config': sha256((self.project / '.mask/skill-config/implement-rfc/project.json').read_bytes()),
                    'project-rules': sha256((self.project / '.mask/skill-config/implement-rfc/project.md').read_bytes())},
            roles=[dict(agent='codex', name='rfc-integrator', sha256=sha256((self.roles_dir['codex'] / 'rfc-integrator.toml').read_bytes())),
                   dict(agent='claude', name='rfc-integrator', sha256=sha256((self.roles_dir['claude'] / 'rfc-integrator.md').read_bytes()))]), indent=2) + '\n', encoding='utf-8')

    def test_coherent_lock_passes_and_relevant_changes_invalidate_it(self):
        result = self.call('ensure')
        roles = self.roles(result)
        self.assertEqual({row['state'] for row in roles.values()}, {'ok'})
        self.assertEqual({row['ownership'] for row in roles.values()}, {'repository-owned'})
        self.assertEqual(roles[('codex', 'rfc-integrator')]['producer'], 'setup')
        self.assertEqual(self.owned(), {})
        self.assertFalse(list(self.project.glob('**/__pycache__')))
        # W04: a relevant consumer input change makes the lock stale; nothing is overwritten or executed.
        config = self.project / '.mask/skill-config/implement-rfc/project.json'
        config.write_text(config.read_text(encoding='utf-8').replace('fixture-only', 'edited-route'), encoding='utf-8')
        stale = self.call('ensure', code=4)
        self.assertEqual(stale['error']['code'], 'workflow.incomplete')
        self.assertEqual({row['state'] for row in self.roles(stale).values()}, {'setup_required'})
        self.assertEqual((self.roles_dir['codex'] / 'rfc-integrator.toml').read_text(encoding='utf-8'), 'name = "rfc-integrator"\nmodel = "fixture-model-do-not-run"\n')
        self.write_lock()
        self.call('ensure')
        # An edited role output no longer matches the lock.
        (self.roles_dir['claude'] / 'rfc-integrator.md').write_text('---\nname: rfc-integrator\nmodel: other\n---\n', encoding='utf-8')
        edited = self.call('ensure', code=4)
        self.assertEqual(self.roles(edited)[('claude', 'rfc-integrator')]['state'], 'modified')
        self.assertEqual(self.roles(edited)[('codex', 'rfc-integrator')]['state'], 'ok')
        # A missing lock cannot vouch at all.
        self.lock.unlink()
        missing = self.call('ensure', code=4)
        self.assertEqual({row['state'] for row in self.roles(missing).values()}, {'setup_required'})
        self.assertEqual(self.call('ensure', '--check', code=4)['error']['code'], 'workflow.incomplete')

    def test_retired_lock_location_still_vouches_and_the_canonical_one_wins(self):
        legacy = self.project / '.mask/skill-config/implement-rfc/native-roles.lock.json'
        self.lock.unlink()
        self.write_lock(legacy)
        result = self.call('ensure')
        roles = self.roles(result)
        self.assertEqual({row['state'] for row in roles.values()}, {'ok'})
        self.assertEqual(self.contract(result)['lock_path'], '.mask/skill-config/implement-rfc/native-roles.lock.json')
        # The canonical location is authoritative when both exist: a stale retired file cannot override it.
        self.write_lock()
        self.assertEqual(self.contract(self.call('ensure'))['lock_path'], '.mask/generated/implement-rfc/native-roles.lock.json')
        legacy.write_text('not a lock\n', encoding='utf-8')
        self.assertEqual(self.contract(self.call('ensure'))['lock_path'], '.mask/generated/implement-rfc/native-roles.lock.json')
        # With no canonical lock, an unreadable retired file is reported at the path it was read from.
        self.lock.unlink()
        invalid = self.call('ensure', code=4)
        self.assertEqual(self.contract(invalid)['lock'], 'invalid')
        self.assertEqual(self.contract(invalid)['lock_path'], '.mask/skill-config/implement-rfc/native-roles.lock.json')

    def test_missing_required_input_is_one_actionable_requirement(self):
        (self.project / '.mask/skill-config/implement-rfc/project.md').unlink()
        result = self.call('ensure', code=4)
        self.assertEqual(result['error']['details']['workflow'][0], 'implement-rfc input project-rules (.mask/skill-config/implement-rfc/project.md): missing')
