"""Every link text MASK can produce names a store payload or an explicit dev link (RFC-MASK-0021 AC02, B07, U09; MASK-0102).

``LinkProducers`` enumerates every call in the product modules that creates a link or computes a link text, and
every directory ``mask_pinned.target`` can derive, against allowlists that name each target derivation.
``StoreTargetedLinks`` drives the public link producers on a tap-first machine: after each step every owned link
recorded in state.json and every link observed on disk resolves under MASK_HOME/store/v1, except the one explicit
``source dev-link``. ``LegacyRecordsYieldNoLinks`` shows a mode-less record refusing every planner entry point.
"""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from tests.fixture_files import git, snapshot
from tests.support import ENTRY, TAP, Fixture

PROGRAM = ENTRY.parent
ALPHA = TAP + '/alpha'
# (enclosing function, producer call, first argument) -> the derivation that makes the produced link text safe.
PRODUCERS = {
    ('mask_pinned.expected_links', 'creation_link_text', "store.location(home, row['payload_digest'], row['id'])[1]"):
        'store: the payload directory of an exact locked resolution',
    ('mask_fs.plan', 'creation_link_text', 'pinned.target(link, config, home)'):
        'explicit source dev-link: pinned.target of a link that carries its validated dev binding',
    ('mask_fs.set_link', 'symlink_to', 'wanted'):
        'journal replay: validate_pending proves the text is an owned record whose pinned.target is the store or a dev link, '
        'or, only when rolling back a doctor.migrate journal, the recorded legacy text: naming the journal\'s recorded checkout '
        'for a machine migration, or exactly equal to the before record for a tap-machine migration, which has no checkout',
}
# The only directories pinned.target derives; a link record with neither refuses migration.required.
TARGETS = {"Path(link['dev']['root']) / link['dev']['path']", "store.location(home, link['resolution']['payload_digest'], link['skill'])[1]"}
CRASH = "import os,sys;sys.path.insert(0,sys.argv[1]);import mask,mask_fs;mask_fs.checkpoint=lambda label: os._exit(99) if label==sys.argv[2] else None;__import__('tests.engine_cli', fromlist=['main']).main(sys.argv[3:])"


# Every spelling that creates a link or computes a link text: pathlib, os (also imported bare), the Win32 API through
# ctypes, and the shell's mklink. A new spelling here must be allowlisted in PRODUCERS with its target derivation.
LINK_CALLS = {'symlink_to', 'symlink', 'creation_link_text', 'link_to', 'hardlink_to', 'CreateSymbolicLink', 'CreateSymbolicLinkW', 'CreateSymbolicLinkA'}


def link_producers():
    found = set()

    def visit(node, module, scope):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                visit(child, module, scope + [child.name])
                continue
            if isinstance(child, ast.Call):
                function = child.func
                name = function.attr if isinstance(function, ast.Attribute) else getattr(function, 'id', None)
                if name in LINK_CALLS:
                    if name == 'symlink':
                        name = 'os.symlink'
                    found.add(('.'.join([module] + scope), name, ast.unparse(child.args[0]) if child.args else ''))
            elif isinstance(child, ast.Constant) and isinstance(child.value, str) and 'mklink' in child.value.lower():
                found.add(('.'.join([module] + scope), 'mklink', child.value))
            visit(child, module, scope)

    for path in sorted(PROGRAM.glob('mask*.py')):
        visit(ast.parse(path.read_text(encoding='utf-8'), filename=str(path)), path.stem, [])
    return found


class LinkProducers(unittest.TestCase):
    def test_every_link_producer_is_allowlisted_with_its_target_derivation(self):
        self.assertEqual(link_producers(), set(PRODUCERS))

    def test_owned_link_targets_are_store_payloads_or_explicit_dev_links(self):
        module = ast.parse((PROGRAM / 'mask_pinned.py').read_text(encoding='utf-8'))
        target = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == 'target')
        self.assertEqual({ast.unparse(node.value) for node in ast.walk(target) if isinstance(node, ast.Return)}, TARGETS)


class StoreTargetedLinks(Fixture):
    def links(self):
        return {str(leaf): os.readlink(leaf) for leaf in self.observed_links()}

    def observed_links(self):
        state = json.loads((self.home / 'state.json').read_text(encoding='utf-8'))
        roots = set(state['projects']) | ({state['user']['root']} if state.get('user') else set()) | {str(self.project), str(self.personal)}
        observed = set()
        for root in roots:
            for parent, directories, files in os.walk(root):
                directories[:] = [name for name in directories if name != '.git']
                observed.update(Path(parent) / name for name in directories + files if (Path(parent) / name).is_symlink())
        return observed

    def assert_store_links(self, dev=()):
        """Every recorded and observed link resolves under the store; only the named leaves are dev links to the authoring checkout."""
        store = (self.home / 'store' / 'v1').resolve()
        state = json.loads((self.home / 'state.json').read_text(encoding='utf-8'))
        records = dict(state['projects'], **({state['user']['root']: state['user']} if state.get('user') else {}))
        recorded, developing = set(), set()
        for root, record in records.items():
            for relative, link in record['links'].items():
                leaf = Path(root) / relative
                recorded.add(leaf)
                self.assertEqual(os.readlink(leaf), link['link_text'], leaf)
                if 'dev' in link:
                    developing.add(leaf)
                    self.assertEqual(leaf.resolve(), (Path(link['dev']['root']) / link['dev']['path']).resolve(), leaf)
                else:
                    self.assertTrue(leaf.resolve().is_relative_to(store), (leaf, link['link_text']))
                    self.assertTrue((leaf / 'SKILL.md').is_file(), leaf)
        self.assertEqual(developing, set(dev))
        self.assertEqual(self.observed_links(), recorded)
        return recorded

    def crash(self, label, *args):
        run = subprocess.run([sys.executable, '-B', '-c', CRASH, str(PROGRAM), label, *map(str, args), '--json'], capture_output=True,
                             encoding='utf-8', cwd=self.project, env=self.environment())
        self.assertEqual(run.returncode, 99, run.stdout + run.stderr)
        self.assertTrue((self.home / 'pending.json').is_file())

    def test_every_public_link_producer_targets_the_store(self):
        # B07: an authoring checkout whose origin names another repository is refused before the machine is created.
        self.git(self.source, 'remote', 'add', 'origin', str(self.base / 'elsewhere.git'))
        refused = self.call('tap', 'add', TAP, self.upstream, '--checkout', self.source, code=4)
        self.assertEqual(refused['error']['code'], 'source.identity_mismatch')
        self.assertFalse((self.home / 'config.json').exists())
        self.git(self.source, 'remote', 'set-url', 'origin', str(self.upstream))
        self.call('tap', 'add', TAP, self.upstream, '--checkout', self.source)
        self.assertEqual(json.loads((self.home / 'config.json').read_text(encoding='utf-8'))['sources'][TAP]['authoring'], str(self.source))
        project_links = [self.project / '.claude/skills/alpha', self.project / '.agents/skills/alpha']

        self.install('alpha')
        self.assertEqual(self.assert_store_links(), set(project_links))
        self.install('beta', user=True)
        self.assert_store_links()
        self.call('apply', '--project', self.project)
        self.assert_store_links()
        self.call('ensure', '--project', self.project)
        self.assert_store_links()

        other = self.base / 'registered later'
        other.mkdir()
        for name in ('.mask.json', '.mask.lock.json'):
            (other / name).write_bytes((self.project / name).read_bytes())
        self.call('project', 'register', '--project', other, '--apply')
        self.assertIn(other / '.agents/skills/alpha', self.assert_store_links())

        self.call('project', 'set-agents', ALPHA, 'claude', '--project', self.project, '--apply')
        self.assertNotIn(project_links[1], self.assert_store_links())
        # Pinned adoption: restore all agents in the declaration only, place the exact store link by hand, then adopt it.
        self.call('project', 'set-agents', ALPHA, '--inherit', '--project', self.project)
        os.symlink(os.readlink(project_links[0]), project_links[1], target_is_directory=True)
        self.call('link', 'adopt', '--project', self.project, '--skill', 'alpha', '--target', 'codex', '--expect-source', project_links[0].resolve())
        self.assertIn(project_links[1], self.assert_store_links())
        self.assertFalse(self.call('apply', '--project', self.project)['changed'])

        # A crash at the link checkpoint recovers to store links either way.
        before = self.links()
        self.crash('link', 'install', 'beta', '--project', self.project)
        self.call('recover', '--inspect')
        self.call('recover', '--rollback')
        self.assertEqual(self.links(), before)
        self.assert_store_links()
        self.crash('link', 'install', 'beta', '--project', self.project)
        self.call('recover', '--complete')
        self.assertIn(self.project / '.agents/skills/beta', self.assert_store_links())

        # B07: binding another authoring checkout changes no link target.
        before = self.links()
        self.call('tap', 'add', 'mirror', self.upstream, '--checkout', self.source)
        self.assertEqual(self.links(), before)

        # The only link into an authoring checkout is an explicit dev link, and --to-pinned returns it to the store.
        self.call('source', 'dev-link', ALPHA, '--project', self.project, '--authoring-root', self.source)
        self.assert_store_links(dev=project_links)
        self.call('source', 'dev-link', ALPHA, '--project', self.project, '--to-pinned')
        self.assert_store_links()
        self.assertEqual(self.links(), before)

