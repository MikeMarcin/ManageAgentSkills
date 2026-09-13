import json
from pathlib import Path

import mask_core as c
import mask_sources as sources
from tests.support import TAP, Fixture


def skill(name):
    return '---\nname: ' + name + '\ndescription: Frozen fixture\n---\n\nInstructions.\n'


class DiscoveryTests(Fixture):
    def setUp(self):
        super().setUp()
        self.init()

    def tap(self, name, files, layout='.', object_format='sha1'):
        author = self.base / (name + '-author')
        author.mkdir()
        self.git(author, 'init', '-b', 'main', '--object-format=' + object_format)
        self.git(author, 'config', 'user.name', 'Fixture')
        self.git(author, 'config', 'user.email', 'fixture@example.invalid')
        for path, content in files.items():
            target = author / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        self.git(author, 'add', '.')
        self.git(author, 'commit', '-m', 'source fixture')
        remote = self.base / (name + '.git')
        self.git(self.base, 'clone', '--bare', str(author), str(remote))
        self.git(author, 'remote', 'add', 'origin', str(remote))
        self.call('tap', 'add', name, remote, '--packages', layout)
        return author, remote

    def test_root_nested_and_qualified_lookup_never_select_duplicate_names(self):
        _, root_remote = self.tap('root', {'SKILL.md': skill('alpha')})
        _, nested_remote = self.tap('nested', {
            'groups/tools/gamma/SKILL.md': skill('gamma'),
            'mask-source.json': json.dumps({'schema_version': 1, 'packages': {'gamma': 'groups/tools/gamma'}})})
        before = self.snapshot()
        for remote in (root_remote, nested_remote):
            self.assertTrue(self.call('source', 'inspect', remote, '--dry-run')['data']['resolution_required'])
        self.assertEqual(before, self.snapshot())
        for name in (TAP, 'root', 'nested'):
            self.call('source', 'fetch', name)
        before = self.snapshot()
        self.assertEqual(self.call('skill', 'show', 'alpha', code=4)['error']['details']['choices'], [TAP + '/alpha', 'root/alpha'])
        self.assertIn('Instructions.', self.call('skill', 'show', 'root/alpha', '--content')['data']['content'])
        nested = self.call('skill', 'show', 'gamma')['data']
        self.assertEqual(nested['coordinate'], 'nested/gamma')
        self.assertEqual(nested['path'], 'groups/tools/gamma')
        self.assertEqual(len(self.call('skill', 'list')['data']['skills']), 4)
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.project / '.agents').exists())

    def test_raw_crlf_frontmatter_is_discovered_without_rewriting_bytes(self):
        author, remote = self.tap('crlf', {'skills/item/SKILL.md': skill('item')}, 'skills')
        self.git(author, 'config', 'core.autocrlf', 'false')
        raw = (skill('item') + 'Exact CRLF bytes.\n').replace('\n', '\r\n').encode('utf-8')
        (author / 'skills/item/SKILL.md').write_bytes(raw)
        self.git(author, 'add', '.')
        self.git(author, 'commit', '-m', 'raw CRLF package')
        self.git(author, 'push', 'origin', 'main')
        inspected = self.call('source', 'inspect', remote)['data']
        self.assertEqual(inspected['skills'][0]['id'], 'item')
        self.call('source', 'fetch', 'crlf')
        shown = self.call('skill', 'show', 'crlf/item', '--content')['data']
        self.assertEqual(shown['content'].encode('utf-8'), raw)
        self.assertTrue(self.call('skill', 'validate', 'crlf/item')['data']['valid'])

    def test_inspect_frozen_commit_and_offline_dry_run(self):
        author, remote = self.tap('history', {'skills/old/SKILL.md': skill('old')}, 'skills')
        old = self.git(author, 'rev-parse', 'HEAD')
        self.call('source', 'fetch', 'history')
        (author / 'skills/old/SKILL.md').write_text(skill('old') + 'Later revision.\n')
        self.git(author, 'add', '.')
        self.git(author, 'commit', '-m', 'later')
        self.git(author, 'push', 'origin', 'main')
        current = self.git(author, 'rev-parse', 'HEAD')
        self.assertNotEqual(old, current)
        observed = self.call('source', 'inspect', remote, '--ref', old, '--path', 'skills/old')['data']
        self.assertEqual(observed['commit'], old)
        self.assertEqual(observed['skills'][0]['commit'], old)
        # Inspecting a different ref does not change the configured source cursor.
        self.assertEqual(self.call('source', 'show', 'history')['data']['cached_revision'], old)
        before = self.snapshot()
        future = self.call('source', 'inspect', remote, '--dry-run')['data']
        self.assertEqual(future['object'], current)
        self.assertTrue(future['resolution_required'])
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.call('source', 'inspect', remote, '--ref', '0' * 40, code=5)['error']['code'], 'git.failed')
        self.assertEqual(self.call('source', 'show', 'history')['data']['cached_revision'], old)

    def test_ref_and_url_path_ambiguity_is_actionable(self):
        author, remote = self.tap('refs', {'docs/item/SKILL.md': skill('item')})
        self.git(author, 'branch', 'feature/docs')
        self.git(author, 'tag', 'feature')
        self.git(author, 'push', 'origin', '--all')
        self.git(author, 'push', 'origin', '--tags')
        self.call('source', 'fetch', 'refs')
        entry = self.call('source', 'show', 'refs')['data']['binding']
        refs = sources.cached_refs(Path(entry['cache']), entry)
        with self.assertRaises(c.MaskError) as ambiguous:
            sources.url_selection('feature/docs/item', 'tree', refs, None, None, 'main')
        self.assertEqual(ambiguous.exception.code, 'source.ref_path_ambiguous')
        self.assertEqual(len(ambiguous.exception.details['choices']), 2)
        self.assertEqual(sources.url_selection('feature/docs/item/SKILL.md', 'blob', refs, 'feature', None, 'main'), ('feature', 'docs/item'))
        self.git(author, 'tag', 'main')
        self.git(author, 'push', 'origin', '--tags')
        self.assertEqual(self.call('source', 'fetch', 'refs', code=4)['error']['code'], 'source.ref_ambiguous')
        self.assertEqual(self.call('source', 'inspect', remote, '--ref', 'refs/heads/main')['data']['skills'][0]['id'], 'item')

    def test_github_url_only_uses_explicit_approved_https_repository(self):
        self.call('tap', 'add', 'github', 'https://github.com/Owner/Repo.git')
        config = self.call('config', 'show')['data']['config']
        name, _, tail, kind = sources.locate_url(config, 'https://github.com/Owner/Repo/tree/feature/docs/item')
        self.assertEqual((name, tail, kind), ('github', 'feature/docs/item', 'tree'))
        before = self.snapshot()
        self.assertTrue(self.call('source', 'inspect', 'https://github.com/Owner/Repo/blob/main/SKILL.md', '--dry-run')['data']['resolution_required'])
        self.assertEqual(self.call('source', 'inspect', 'https://github.com/Other/Repo', '--dry-run', code=4)['error']['code'], 'source.unapproved')
        self.assertEqual(before, self.snapshot())

    def test_sha256_objects_and_explicit_catalog_alias(self):
        author, remote = self.tap('sha256', {'SKILL.md': skill('sha256')}, object_format='sha256')
        self.call('source', 'fetch', 'sha256')
        commit = self.git(author, 'rev-parse', 'HEAD')
        self.assertEqual(len(commit), 64)
        self.call('tap', 'add', 'second-alias', remote, '--packages', '.')
        self.assertEqual(self.call('source', 'inspect', remote, '--dry-run', code=4)['error']['code'], 'source.alias_ambiguous')
        self.assertEqual(self.call('source', 'inspect', 'sha256', '--dry-run')['data']['commit'], commit)

    def test_unindexed_overlap_and_duplicate_names_require_explicit_choice(self):
        author, remote = self.tap('overlap', {'SKILL.md': skill('outer'), 'nested/SKILL.md': skill('inner')})
        self.assertEqual(self.call('source', 'inspect', remote, code=4)['error']['code'], 'source.path_ambiguous')
        self.assertEqual(self.call('source', 'inspect', remote, '--path', 'nested')['data']['skills'][0]['id'], 'inner')
        (author / 'mask-source.json').write_text(json.dumps({'schema_version': 1, 'packages': {'inner': 'nested'}}))
        self.git(author, 'add', '.')
        self.git(author, 'commit', '-m', 'choose one interpretation')
        self.git(author, 'push', 'origin', 'main')
        self.assertEqual(len(self.call('source', 'inspect', remote)['data']['skills']), 1)
        _, duplicate = self.tap('duplicates', {'a/SKILL.md': skill('same'), 'b/SKILL.md': skill('same')})
        self.assertEqual(self.call('source', 'inspect', duplicate, code=4)['error']['code'], 'source.name_ambiguous')

    def test_index_cannot_add_authority_and_uncached_sources_are_not_ignored(self):
        _, remote = self.tap('active', {'SKILL.md': skill('active'), 'mask-source.json': json.dumps({
            'schema_version': 1, 'packages': {'active': '.'}, 'hooks': {'command': 'never-run'}})})
        self.assertEqual(self.call('source', 'inspect', remote, code=3)['error']['code'], 'source.invalid')
        self.call('source', 'fetch', TAP)
        self.assertEqual(self.call('skill', 'show', 'alpha', code=4)['error']['code'], 'source.resolution_required')
        self.assertEqual(self.call('skill', 'show', TAP + '/alpha')['data']['id'], 'alpha')
