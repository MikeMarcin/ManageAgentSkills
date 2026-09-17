"""Tap-first bootstrap through the public CLI (RFC-MASK-0021 AC01 and the retired ``init --source``; MASK-0101).

The upstream is a local bare repository filled from a throwaway author checkout that
is deleted before MASK runs, so no working checkout of the skills exists anywhere on
disk. Every invocation uses a private MASK_HOME and personal home.
"""
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest

import mask_core as c
from tests.legacy_support import LegacyFixture, snapshot

ENTRY = Path(__file__).resolve().parents[1] / 'mask.py'
TAP = 'agentskills'


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, encoding='utf-8', check=True).stdout.strip()


def writable(function, path, _):
    os.chmod(path, stat.S_IWRITE)
    function(path)


class TapBootstrap(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mask-bootstrap-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.home = self.base / 'machine'
        self.personal = self.base / 'personal home'
        self.project = self.base / 'project with ü spaces'
        for directory in (self.personal, self.project):
            directory.mkdir()
        git(self.project, 'init', '-q', '-b', 'main')
        self.upstream = self.base / 'upstream' / 'AgentSkills.git'
        self.upstream.parent.mkdir()
        git(self.base, 'init', '-q', '--bare', '-b', 'main', str(self.upstream))
        author = Path(tempfile.mkdtemp(prefix='mask-bootstrap-author-'))
        try:
            git(author, 'init', '-q', '-b', 'main')
            git(author, 'config', 'user.name', 'Fixture')
            git(author, 'config', 'user.email', 'fixture@example.invalid')
            for name in ('alpha', 'beta'):
                (author / 'skills' / name).mkdir(parents=True)
                (author / 'skills' / name / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: Fixture skill\n---\n\nFixture only.\n', encoding='utf-8', newline='\n')
            git(author, 'add', 'skills')
            git(author, 'commit', '-q', '-m', 'fixture skills')
            git(author, 'push', '-q', str(self.upstream), 'main')
            self.head = git(author, 'rev-parse', 'HEAD')
        finally:
            shutil.rmtree(author, onerror=writable)

    def environment(self, home=None):
        env = dict(os.environ, MASK_HOME=str(home or self.home), HOME=str(self.personal), USERPROFILE=str(self.personal),
                   PYTHONDONTWRITEBYTECODE='1', GIT_TERMINAL_PROMPT='0')
        env.pop('MASK_USER_HOME', None)
        return env

    def machine(self, *args, code=0, home=None):
        run = subprocess.run([sys.executable, '-B', str(ENTRY), *map(str, args), '--json'], capture_output=True, encoding='utf-8',
                             cwd=str(self.project), env=self.environment(home), timeout=120)
        self.assertEqual(run.stderr, '', run.stderr)
        data = json.loads(run.stdout)
        self.assertEqual(run.returncode, code, run.stdout)
        self.assertEqual(data['ok'], code == 0, run.stdout)
        return data

    def snapshot(self):
        observed = {}
        for parent, directories, files in os.walk(self.base, followlinks=False):
            directories[:] = [name for name in directories if name != '.git' and not (Path(parent) / name).is_symlink()]
            for name in files + [d for d in os.listdir(parent) if (Path(parent) / d).is_symlink()]:
                path = Path(parent) / name
                key = path.relative_to(self.base).as_posix()
                observed[key] = ('link', os.readlink(path)) if path.is_symlink() else ('file', path.read_bytes())
        return observed

    def read(self, path):
        return json.loads(path.read_text(encoding='utf-8'))

    def assert_store_link(self, leaf, text=None):
        store = (self.home / 'store' / 'v1').resolve()
        self.assertEqual(c.kind(leaf), 'symlink', leaf)
        if text is not None:
            self.assertEqual(os.readlink(leaf), text)
        self.assertTrue(leaf.resolve().is_relative_to(store), (leaf, os.readlink(leaf)))
        self.assertTrue((leaf / 'SKILL.md').is_file(), leaf)

    def test_tap_add_bootstraps_an_empty_machine_without_fetching(self):
        before = self.snapshot()
        preview = self.machine('tap', 'add', TAP, self.upstream.as_uri(), '--dry-run')
        self.assertEqual([(a['kind'], a['status']) for a in preview['actions']], [('config.create', 'planned'), ('source.catalog', 'planned')])
        self.assertTrue(preview['would_change'])
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(c.kind(self.home / 'config.json'), 'missing')
        added = self.machine('tap', 'add', TAP, self.upstream.as_uri(), '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertEqual([(a['kind'], a['status']) for a in added['actions']], [('config.create', 'applied'), ('source.catalog', 'applied')])
        config = self.read(self.home / 'config.json')
        self.assertEqual(sorted(config), ['default_targets', 'git_timeout_seconds', 'schema_version', 'sources'])
        self.assertEqual((config['schema_version'], config['default_targets'], config['git_timeout_seconds']), (3, ['claude', 'codex'], 30))
        entry = config['sources'][TAP]
        self.assertEqual(list(config['sources']), [TAP])
        self.assertEqual((entry['repository'], entry['ref'], entry['packages'], entry['authoring']), (self.upstream.as_uri(), 'main', 'skills', None))
        self.assertEqual(Path(entry['cache']).parent, self.home / 'sources')
        self.assertEqual(self.read(self.home / 'state.json'), c.empty_state())
        self.assertEqual(c.kind(self.home / 'sources'), 'missing')
        self.assertFalse(self.machine('tap', 'add', TAP, self.upstream.as_uri())['changed'])
        self.assertFalse(self.machine('init')['changed'])

    def test_install_deploys_v2_consumers_from_the_store_with_no_checkout_on_disk(self):
        self.machine('tap', 'add', TAP, self.upstream)
        installed = self.machine('install', 'alpha', '--project', self.project)
        self.assertEqual((installed['data']['network'], len(installed['data']['acquisitions']), installed['transaction']), ('fetch', 1, 'committed'))
        declaration = self.read(self.project / '.mask.json')
        self.assertEqual((declaration['schema_version'], list(declaration['sources']), declaration['skills']), (2, [TAP], [dict(source=TAP, id='alpha')]))
        lock = self.read(self.project / '.mask.lock.json')
        self.assertEqual([(row['source'], row['id'], row['commit']) for row in lock['packages']], [(TAP, 'alpha', self.head)])
        caches = list((self.home / 'sources').iterdir())
        self.assertEqual(len(caches), 1)
        self.assertEqual(git(caches[0], 'rev-parse', '--is-bare-repository'), 'true')
        record = self.read(self.home / 'state.json')['projects'][str(self.project)]
        self.assertEqual((record['mode'], sorted(record['links'])), ('pinned', ['.agents/skills/alpha', '.claude/skills/alpha']))
        for relative, link in record['links'].items():
            self.assert_store_link(self.project / relative, link['link_text'])
        project_controls = [(self.project / name).read_bytes() for name in ('.mask.json', '.mask.lock.json')]
        self.machine('install', 'beta', '--user')
        self.assertEqual(self.read(self.home / 'user.json')['skills'], [dict(source=TAP, id='beta')])
        self.assertEqual(self.read(self.home / 'user.lock.json')['packages'][0]['commit'], self.head)
        for relative in ('.claude/skills/beta', '.agents/skills/beta'):
            self.assert_store_link(self.personal / relative)
        self.assertEqual([(self.project / name).read_bytes() for name in ('.mask.json', '.mask.lock.json')], project_controls)
        self.assertEqual(len(list((self.home / 'sources').iterdir())), 1)
        # No working checkout of the skills exists anywhere: every SKILL.md is inside the store, and the only work tree is the consumer.
        store = (self.home / 'store' / 'v1').resolve()
        outside = [str(path) for path in self.base.rglob('SKILL.md') if not path.resolve().is_relative_to(store)]
        self.assertEqual(outside, [])
        work_trees = sorted(str(path.parent) for path in self.base.rglob('.git'))
        self.assertEqual(work_trees, [str(self.project)])
        self.assertTrue(self.machine('doctor', '--all', '--check')['data']['healthy'])

    def test_offline_install_before_any_fetch_names_the_tap_and_writes_nothing(self):
        self.machine('tap', 'add', TAP, self.upstream)
        before = self.snapshot()
        refused = self.machine('install', 'alpha', '--offline', '--project', self.project, code=4)
        # A bare ID cannot be resolved while its only tap is unfetched (contract: source.unresolved names the taps).
        self.assertEqual(refused['error']['code'], 'source.unresolved')
        self.assertEqual(refused['error']['details']['unresolved'], [TAP])
        self.assertEqual(self.snapshot(), before)
        qualified = self.machine('install', TAP + '/alpha', '--offline', '--project', self.project, code=4)
        self.assertEqual((qualified['error']['code'], qualified['error']['details']['source']), ('lock.resolution_required', TAP))
        self.assertEqual(self.snapshot(), before)

    def test_init_writes_an_empty_catalog_and_refuses_the_retired_source_option(self):
        for args in (('--source', self.base), ('--source', self.base, '--remote', 'origin', '--branch', 'main')):
            refused = self.machine('init', *args, code=2)
            self.assertEqual(refused['error']['code'], 'invocation.invalid')
        self.assertEqual(c.kind(self.home), 'missing')
        self.machine('init', '--target', 'codex', '--git-timeout', '60')
        self.assertEqual(self.read(self.home / 'config.json'), dict(schema_version=3, default_targets=['codex'], git_timeout_seconds=60, sources={}))
        self.assertEqual(self.read(self.home / 'state.json'), c.empty_state())
        self.assertFalse(self.machine('init')['changed'])
        self.assertEqual(self.machine('init', '--target', 'claude', code=4)['error']['code'], 'config.already_initialized')
        added = self.machine('tap', 'add', TAP, self.upstream)
        self.assertEqual([a['kind'] for a in added['actions']], ['source.catalog'])
        self.machine('install', 'alpha', '--project', self.project)
        self.assertEqual(self.read(self.project / '.mask.json')['default_agents'], ['codex'])
        self.assert_store_link(self.project / '.agents/skills/alpha')
        self.assertEqual(c.kind(self.project / '.claude/skills/alpha'), 'missing')

    def test_capabilities_publish_machine_v3_and_the_new_init_arguments(self):
        caps = self.machine('capabilities')['data']
        self.assertEqual((caps['schemas']['machine'], caps['readable_versions']['machine']), (3, [1, 2, 3]))
        commands = {item['name']: item for item in caps['commands']}
        names = {argument['name'] for argument in commands['init']['arguments']}
        self.assertLessEqual({'target', 'git_timeout'}, names)
        self.assertFalse(names & {'source', 'remote', 'branch'})
        self.assertEqual((commands['tap.add']['network'], commands['tap.add']['plan_guard']), (False, True))
        schema = json.loads((ENTRY.parent / 'schemas/machine-v3.schema.json').read_text(encoding='utf-8'))
        self.assertEqual((schema['properties']['schema_version']['const'], sorted(schema['required'])), (3, ['default_targets', 'git_timeout_seconds', 'schema_version', 'sources']))
        union = json.loads((ENTRY.parent / 'schemas/machine.schema.json').read_text(encoding='utf-8'))
        self.assertIn({'$ref': 'machine-v3.schema.json'}, union['oneOf'])


class LegacyRecordsOnATapCatalog(LegacyFixture):
    """A v1 machine whose config.json is replaced by a bootstrapping tap add keeps its legacy records; they refuse typed."""

    def test_legacy_records_refuse_migration_required_and_write_nothing(self):
        roots = self.legacy_machine(1, straggler_skills=None)
        (roots.home / 'config.json').unlink()
        self.assertEqual([a['kind'] for a in self.machine('tap', 'add', TAP, roots.upstream)['actions']], ['config.create', 'source.catalog'])
        tapped = roots.base / 'tap project'
        tapped.mkdir()
        git(tapped, 'init', '-q', '-b', 'main')
        self.machine('install', 'alpha', '--project', tapped)
        observed = snapshot(roots.base, roots.home, roots.project, roots.personal, tapped)
        for args in (('upgrade',), ('upgrade', '--project', roots.project), ('upgrade', '--user')):
            refused = self.machine(*args, code=4)
            self.assertEqual(refused['error']['code'], 'migration.required', args)
        self.assertIn(str(roots.project), self.machine('upgrade', code=4)['error']['details']['roots'])
        adopt = self.machine('link', 'adopt', '--project', roots.project, '--skill', 'alpha', '--target', 'codex',
                             '--expect-source', roots.clone / 'skills/alpha', code=4)
        self.assertEqual(adopt['error']['code'], 'migration.required')
        inventory = self.machine('inventory', '--project', roots.project)['data']
        self.assertEqual((inventory['rows'], inventory['complete'], inventory['consumers'][0]['error']['code']), ([], False, 'migration.required'))
        self.assertEqual(snapshot(roots.base, roots.home, roots.project, roots.personal, tapped), observed)


if __name__ == '__main__':
    unittest.main()
