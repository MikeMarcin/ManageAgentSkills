import json
import os
from pathlib import Path

import mask_core as c
from tests.support import TAP, Fixture

ALPHA = TAP + '/alpha'


def authoring_init(fixture):
    """Bootstrap the fixture tap with ``fixture.source`` as its approved authoring checkout; its origin names the tap identity."""
    fixture.git(fixture.source, 'remote', 'add', 'origin', str(fixture.upstream))
    return fixture.call('tap', 'add', TAP, fixture.upstream, '--checkout', fixture.source)


class UpdateTests(Fixture):
    # Development links and publication from the fixture tap need its approved authoring checkout; the rest start from init().
    AUTHORING = {'test_dev_link_dirty_scope_and_guarded_return', 'test_development_recovery_binds_live_authoring_and_typed_extension',
                 'test_publication_index_mapping_and_retained_object_failure'}

    def setUp(self):
        super().setUp()
        authoring_init(self) if self._testMethodName in self.AUTHORING else self.init()
        self.install('alpha')

    def test_selected_update_isolates_consumers_and_uses_cached_candidate(self):
        other = self.base / 'other'
        other.mkdir()
        (other / '.mask.json').write_bytes((self.project / '.mask.json').read_bytes())
        (other / '.mask.lock.json').write_bytes((self.project / '.mask.lock.json').read_bytes())
        self.call('project', 'register', '--project', other, '--apply')
        before = c.read_json(self.home / 'state.json')['projects'][str(other)]
        old = os.readlink(other / '.agents/skills/alpha')
        (self.source / 'skills/alpha/version').write_bytes(b'raw\r\n')
        self.publish('next')
        self.call('source', 'fetch', TAP)
        snapshot = self.snapshot()
        preview = self.call('update', '--project', self.project, '--skill', ALPHA, '--dry-run')
        self.assertEqual(snapshot, self.snapshot())
        self.call('update', '--project', self.project, '--skill', ALPHA, '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertEqual(c.read_json(self.home / 'state.json')['projects'][str(other)], before)
        self.assertEqual(os.readlink(other / '.agents/skills/alpha'), old)
        self.assertNotEqual(os.readlink(self.project / '.agents/skills/alpha'), old)
        self.assertFalse(self.call('update', '--project', self.project)['changed'])

    def test_all_selected_skill_preserves_disjoint_consumer(self):
        self.call('source', 'fetch', TAP)
        other = self.base / 'beta-only'
        other.mkdir()
        declaration = c.read_json(self.project / '.mask.json')
        declaration['skills'] = [dict(source=TAP, id='beta')]
        (other / '.mask.json').write_text(json.dumps(declaration))
        self.call('lock', '--project', other)
        self.call('project', 'register', '--project', other, '--apply')
        record = c.read_json(self.home / 'state.json')['projects'][str(other)]
        lock_bytes = (other / '.mask.lock.json').read_bytes()
        beta_link = os.readlink(other / '.agents/skills/beta')
        alpha_link = os.readlink(self.project / '.agents/skills/alpha')
        for identifier in ('alpha', 'beta'):
            (self.source / 'skills' / identifier / 'new-version').write_text(identifier)
        self.publish('both packages move')
        self.call('source', 'fetch', TAP)
        before = self.snapshot()
        for skills in ([TAP + '/absent'], [ALPHA, ALPHA]):
            arguments = [operand for skill in skills for operand in ('--skill', skill)]
            self.call('update', '--all', *arguments, code=2)
            self.assertEqual(before, self.snapshot())
        preview = self.call('update', '--all', '--skill', ALPHA, '--dry-run')
        self.assertEqual(before, self.snapshot())
        self.call('update', '--all', '--skill', ALPHA, '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertNotEqual(os.readlink(self.project / '.agents/skills/alpha'), alpha_link)
        self.assertEqual(c.read_json(self.home / 'state.json')['projects'][str(other)], record)
        self.assertEqual((other / '.mask.lock.json').read_bytes(), lock_bytes)
        self.assertEqual(os.readlink(other / '.agents/skills/beta'), beta_link)

    def test_dev_link_dirty_scope_and_guarded_return(self):
        other = self.base / 'other-dev'
        other.mkdir()
        (other / '.mask.json').write_bytes((self.project / '.mask.json').read_bytes())
        (other / '.mask.lock.json').write_bytes((self.project / '.mask.lock.json').read_bytes())
        self.call('project', 'register', '--project', other, '--apply')
        old = os.readlink(self.project / '.agents/skills/alpha')
        (self.source / 'skills/alpha/local').write_text('dirty edit')
        preview = self.call('source', 'dev-link', ALPHA, '--project', self.project, '--authoring-root', self.source, '--dry-run')
        self.call('source', 'dev-link', ALPHA, '--project', self.project, '--authoring-root', self.source, '--expect-plan-hash', preview['data']['plan_hash'])
        state = c.state(c.read_json(self.home / 'state.json'))
        self.assertEqual(state['projects'][str(self.project)]['mode'], 'dev-link')
        self.assertEqual(os.readlink(other / '.agents/skills/alpha'), old)
        self.assertFalse(self.call('project', 'show')['data']['reproducible'])
        self.assertFalse(self.call('inventory')['data']['consumers'][0]['reproducible'])
        self.assertEqual(self.call('apply', code=4)['error']['code'], 'dev_link.active')
        self.call('source', 'fetch', TAP)
        self.assertEqual(self.call('update', '--project', self.project, code=4)['error']['code'], 'dev_link.active')
        (self.source / 'skills/alpha/local').write_text('later edit')
        self.call('source', 'dev-link', ALPHA, '--project', self.project, '--to-pinned')
        self.assertEqual(os.readlink(self.project / '.agents/skills/alpha'), old)
        self.assertEqual((self.source / 'skills/alpha/local').read_text(), 'later edit')
        self.assertFalse(self.call('apply')['changed'])

    def test_isolated_publication_exact_paths_and_separate_push(self):
        remote = self.base / 'publication.git'
        remote.mkdir()
        self.git(remote, 'init', '--bare', '-b', 'main')
        self.git(self.source, 'remote', 'add', 'origin', str(remote))
        self.git(self.source, 'push', 'origin', 'main')
        self.call('tap', 'add', 'publisher', str(remote), '--checkout', self.source)
        head = self.git(self.source, 'rev-parse', 'HEAD')
        (self.source / 'unrelated').write_text('staged elsewhere')
        self.git(self.source, 'add', 'unrelated')
        index = self.git(self.source, 'ls-files', '--stage')
        # Publication hashes unfiltered working bytes; undo the Windows CRLF smudge of the committed LF fixture text.
        skill = self.source / 'skills/alpha/SKILL.md'
        skill.write_bytes(skill.read_bytes().replace(b'\r\n', b'\n'))
        (self.source / 'skills/alpha/published').write_bytes(b'raw\r\n')
        marker = self.base / 'executed-marker'
        helper = self.base / 'helper.sh'
        helper.write_text('#!/bin/sh\ntouch "' + str(marker) + '"\nexit 1\n')
        helper.chmod(0o755)
        self.git(self.source, 'config', 'core.fsmonitor', str(helper))
        self.git(self.source, 'config', 'commit.gpgsign', 'true')
        self.git(self.source, 'config', 'gpg.program', str(helper))
        preview = self.call('source', 'publish', 'publisher', '--paths', 'skills/alpha', '--commit', '--push', '--dry-run')
        result = self.call('source', 'publish', 'publisher', '--paths', 'skills/alpha', '--commit', '--push', '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertTrue(result['data']['pushed'])
        commit = result['data']['created_commit']
        self.assertNotEqual(commit, head)
        self.git(self.source, 'config', 'core.fsmonitor', 'false')
        self.assertEqual(self.git(self.source, 'rev-parse', 'HEAD'), head)
        self.assertEqual(self.git(self.source, 'ls-files', '--stage'), index)
        self.assertEqual(self.git(remote, 'rev-parse', 'refs/heads/main'), commit)
        self.assertEqual(self.git(self.source, 'diff-tree', '--no-commit-id', '--name-only', '-r', commit), 'skills/alpha/published')
        self.assertFalse(marker.exists())
        self.assertEqual(len(self.git(self.source, 'worktree', 'list', '--porcelain').split('worktree ')), 2)
        self.call('source', 'publish', 'publisher', '--paths', '../unrelated', '--commit', code=3)

    def test_fixed_commit_and_rebound_selector_updates(self):
        self.call('source', 'fetch', TAP)
        original = c.read_json(self.project / '.mask.lock.json')['packages'][0]['commit']
        self.git(self.source, 'tag', 'release')
        self.git(self.source, 'push', '-q', str(self.upstream), 'refs/tags/release')
        self.call('source', 'inspect', TAP, '--ref', 'refs/tags/release')
        declaration = c.read_json(self.project / '.mask.json')
        declaration['skills'][0]['version'] = {'ref': 'refs/tags/release'}
        (self.project / '.mask.json').write_text(json.dumps(declaration))
        self.call('update', '--project', self.project)
        (self.source / 'skills/alpha/new').write_text('new')
        self.publish('tag moved')
        self.git(self.source, 'tag', '-f', 'release')
        self.git(self.source, 'push', '-q', '--force', str(self.upstream), 'refs/tags/release')
        self.call('source', 'inspect', TAP, '--ref', 'refs/tags/release')
        self.assertEqual(self.call('update', '--project', self.project, code=4)['error']['code'], 'lock.ref_rebound')
        self.call('update', '--project', self.project, '--allow-ref-rebind')
        declaration['skills'][0]['version'] = {'commit': original}
        (self.project / '.mask.json').write_text(json.dumps(declaration))
        self.call('update', '--project', self.project)
        self.assertEqual(c.read_json(self.project / '.mask.lock.json')['packages'][0]['commit'], original)
        self.assertFalse(self.call('update', '--project', self.project)['changed'])


class RecoveryUpdateTests(UpdateTests):
    # Reuse setup without inheriting the existing test methods into this class.
    test_selected_update_isolates_consumers_and_uses_cached_candidate = None
    test_all_selected_skill_preserves_disjoint_consumer = None
    test_all_selected_skill_preserves_disjoint_consumer = None
    test_dev_link_dirty_scope_and_guarded_return = None
    test_isolated_publication_exact_paths_and_separate_push = None
    test_fixed_commit_and_rebound_selector_updates = None

    def crash(self, command, label='intent'):
        import subprocess, sys
        from tests.support import ENTRY
        script = "import os,sys;sys.path.insert(0,sys.argv[1]);import mask,mask_fs;mask_fs.checkpoint=lambda label: os._exit(99) if label==sys.argv[2] else None;mask.main(sys.argv[3:])"
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), label, *command, '--home', str(self.home), '--json'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 99, run.stdout + run.stderr)

    def test_changed_selector_journal_binds_before_bytes(self):
        self.call('source', 'fetch', TAP)
        commit = c.read_json(self.project / '.mask.lock.json')['packages'][0]['commit']
        declaration = c.read_json(self.project / '.mask.json')
        declaration['skills'][0]['version'] = {'commit': commit}
        (self.project / '.mask.json').write_text(json.dumps(declaration))
        self.crash(['update', '--project', str(self.project)])
        original = (self.project / '.mask.lock.json').read_bytes()
        (self.project / '.mask.lock.json').write_bytes(original + b' ')
        before = self.snapshot()
        self.call('recover', '--complete', code=8)
        self.assertEqual(before, self.snapshot())
        (self.project / '.mask.lock.json').write_bytes(original)
        self.call('recover', '--complete')
        self.assertEqual(c.read_json(self.project / '.mask.lock.json')['packages'][0]['selector'], {'commit': commit})

    def test_development_recovery_binds_live_authoring_and_typed_extension(self):
        import copy
        self.crash(['source', 'dev-link', ALPHA, '--project', str(self.project), '--authoring-root', str(self.source)], 'link_unlinked')
        journal = c.read_json(self.home / 'pending.json')
        bad = copy.deepcopy(journal)
        bad.pop('development')
        (self.home / 'pending.json').write_bytes(c.text_json(bad).encode('utf-8'))
        self.call('recover', '--complete', code=8)
        (self.home / 'pending.json').write_bytes(c.text_json(journal).encode('utf-8'))
        dirty = self.source / 'skills/alpha/recovery-edit'
        dirty.write_text('preserve')
        self.call('recover', '--rollback', code=8)
        self.assertEqual(dirty.read_text(), 'preserve')
        dirty.unlink()
        self.call('recover', '--rollback')
        self.assertFalse(self.call('apply')['changed'])

    def test_cold_update_metadata_and_source_effects_preserve_intent(self):
        (self.source / 'skills/alpha/mask-skill.json').write_text(json.dumps(dict(schema_version=1, agents='generic')))
        self.publish('cold generic update')
        self.call('source', 'fetch', TAP)
        before = self.snapshot()
        preview = self.call('update', '--project', self.project, '--dry-run')
        self.assertEqual(before, self.snapshot())
        result = self.call('update', '--project', self.project, '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertTrue(result['changed'])
        self.assertFalse(self.call('apply')['changed'])

    def test_publication_index_mapping_and_retained_object_failure(self):
        import mask
        from unittest.mock import patch
        mapping = self.source / 'mask-source.json'
        mapping.write_text(json.dumps(dict(schema_version=1, packages={'alpha': 'skills/alpha'})))
        before = self.snapshot()
        self.assertEqual(self.call('source', 'publish', TAP, '--paths', 'skills/alpha', '--commit', code=4)['error']['code'], 'source.publish_index_required')
        self.assertEqual(before, self.snapshot())
        self.git(self.source, 'add', 'mask-source.json')
        self.git(self.source, 'commit', '-m', 'selected committed mapping')
        (self.source / 'skills/alpha/publish').write_text('new bytes')
        original = c.git
        def fail(root, *args, **kwargs):
            if args and args[0] == 'write-tree':
                c.fail('fixture.write_tree', 'Injected tree failure.', 5)
            return original(root, *args, **kwargs)
        parser, leaves = mask.make_parser()
        args = parser.parse_args(['source', 'publish', TAP, '--paths', 'skills/alpha', '--commit', '--home', str(self.home)])
        output = mask.result('source.publish')
        with patch.object(c, 'git', side_effect=fail), self.assertRaises(c.MaskError):
            mask.dispatch(args, output, leaves)
        self.assertTrue(output['changed'])
        self.assertEqual(output['transaction'], 'partial')
        self.assertTrue(output['data']['retained_objects_possible'])
        self.assertTrue(output['data']['temporary_worktree_removed'])
        self.assertIsNone(output['data']['created_commit'])
        self.assertEqual(output['data']['phase'], 'objects')
        result = self.call('source', 'publish', TAP, '--paths', 'skills/alpha', '--commit')
        self.assertIsNotNone(result['data']['created_commit'])
        self.assertFalse(result['data']['pushed'])

    def test_publication_uncertain_push_retains_commit_and_unknown_result(self):
        import mask
        from unittest.mock import patch
        remote = self.base / 'uncertain.git'
        remote.mkdir()
        self.git(remote, 'init', '--bare', '-b', 'main')
        self.git(self.source, 'remote', 'add', 'origin', str(remote))
        self.git(self.source, 'push', 'origin', 'main')
        self.call('tap', 'add', 'publisher', str(remote), '--checkout', self.source)
        head = self.git(self.source, 'rev-parse', 'HEAD')
        (self.source / 'skills/alpha/publish').write_text('push bytes')
        original = c.git
        def uncertain(root, *args, **kwargs):
            result = original(root, *args, **kwargs)
            if 'push' in args:
                c.fail('git.timeout', 'Injected lost push acknowledgement.', 5)
            return result
        parser, leaves = mask.make_parser()
        args = parser.parse_args(['source', 'publish', 'publisher', '--paths', 'skills/alpha', '--commit', '--push', '--home', str(self.home)])
        output = mask.result('source.publish')
        with patch.object(c, 'git', side_effect=uncertain), self.assertRaises(c.MaskError):
            mask.dispatch(args, output, leaves)
        self.assertEqual(output['transaction'], 'partial')
        self.assertTrue(output['changed'])
        self.assertIsNone(output['data']['pushed'])
        self.assertEqual(output['data']['push_outcome'], 'unknown')
        self.assertEqual(self.git(remote, 'rev-parse', 'main'), output['data']['created_commit'])
        self.assertNotEqual(output['data']['created_commit'], head)
        self.assertTrue(output['data']['temporary_worktree_removed'])
