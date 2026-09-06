import json
import hashlib
from pathlib import Path
import subprocess
import sys
from unittest.mock import patch

import mask_core as c
import mask_packages as packages
import mask_sources as sources
from tests.support import Fixture, ENTRY


class ImportSafetyTests(Fixture):
    def frozen(self, files=None):
        root = self.source / 'skills/alpha'
        for name, data in (files or {}).items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        self.git(self.source, 'add', '.')
        self.git(self.source, 'commit', '--allow-empty', '-m', 'payload fixture')
        return self.git(self.source, 'rev-parse', 'HEAD')

    def validate(self, commit):
        return packages.validate(self.source, commit, 'skills/alpha', 'alpha')

    def prepare_public(self):
        self.init()
        self.call('source', 'migrate')
        self.call('source', 'fetch', 'legacy')

    def limited_cli(self, policy, expected):
        script = ('import sys;sys.path.insert(0,' + repr(str(ENTRY.parent)) + ');'
                  'import mask_packages as p,mask;')
        script += ';'.join('p.' + key + '=' + str(value) for key, value in policy.items())
        script += ';sys.argv=' + repr(['mask', 'skill', 'validate', 'legacy/alpha', '--home', str(self.home), '--json'])
        script += ';raise SystemExit(mask.main())'
        result = subprocess.run([sys.executable, '-B', '-c', script], capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        self.assertEqual(result.stderr, '')
        return json.loads(result.stdout)

    def test_exact_bytes_modes_frozen_commit_and_passive_public_validation(self):
        marker = self.base / 'executed'
        commit = self.frozen({'raw.bin': b'\0\xff\r\n', 'empty': b'', 'provenance.json': b'{"origin":"fixture"}',
                              'install.py': ('from pathlib import Path;Path(' + repr(str(marker)) + ').touch()').encode(),
                              '.gitattributes': b'raw.bin filter=hostile\n'})
        self.git(self.source, 'update-index', '--chmod=+x', 'skills/alpha/install.py')
        self.git(self.source, 'commit', '-m', 'executable logical mode')
        commit = self.git(self.source, 'rev-parse', 'HEAD')
        command = sys.executable + ' ' + str(self.source / 'skills/alpha/install.py')
        self.git(self.source, 'config', 'filter.hostile.smudge', command)
        self.git(self.source, 'config', 'filter.hostile.required', 'true')
        (self.source / '.git/hooks/post-checkout').write_text('#!/bin/sh\n' + command + '\n')
        (self.source / '.git/hooks/post-checkout').chmod(0o755)
        payload = self.validate(commit)
        values = {item.path: item for item in payload.files}
        self.assertEqual(values['raw.bin'].data, b'\0\xff\r\n')
        self.assertEqual(values['empty'].data, b'')
        self.assertEqual(values['install.py'].mode, '100755')
        manifest = payload.manifest()
        self.assertIn(dict(path='raw.bin', mode='100644', size=4,
                           sha256=hashlib.sha256(b'\0\xff\r\n').hexdigest()), manifest)
        self.assertTrue(any(item['path'] == 'provenance.json' for item in manifest))
        self.assertEqual([item['path'] for item in manifest], sorted(values))
        self.assertEqual(payload.digest, c.digest(manifest))
        self.prepare_public()
        (self.source / 'skills/alpha/raw.bin').write_bytes(b'changed authoring')
        before = self.snapshot()
        result = self.call('skill', 'validate', 'legacy/alpha')['data']
        self.assertEqual(result['commit'], commit)
        self.assertEqual(result['payload_digest'], payload.digest)
        self.assertEqual(result['validation'], 'payload')
        self.call('skill', 'validate', '--all')
        self.assertEqual(before, self.snapshot())
        self.assertFalse(marker.exists())

    def test_public_activation_and_lfs_refusals(self):
        self.frozen({'.claude-plugin/plugin.json': b'{}'})
        self.prepare_public()
        self.assertEqual(self.call('skill', 'validate', 'legacy/alpha', code=4)['error']['code'],
                         'skill.activation_unsupported')
        (self.source / 'skills/alpha/.claude-plugin/plugin.json').unlink()
        self.frozen({'asset': b'version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 12\n'})
        self.call('source', 'fetch', 'legacy')
        self.assertEqual(self.call('skill', 'validate', 'legacy/alpha', code=4)['error']['code'], 'skill.lfs_unsupported')

    def test_frontmatter_and_dynamic_shell_forms_refuse_without_execution(self):
        marker = self.base / 'frontmatter-executed'
        command = sys.executable + ' -c "from pathlib import Path;Path(' + repr(str(marker)) + ').touch()"'
        self.prepare_public()
        for extra, body in (
                ('hooks:\n  SessionStart: ' + command + '\n', 'Instructions.'),
                ('"hooks": {}\n', 'Instructions.'),
                ("'allowed-tools': Bash(*)\n", 'Instructions.'),
                ('allowed-tools: Bash(*)\n', 'Instructions.'),
                ('{hooks: {SessionStart: run}}\n', 'Instructions.'),
                ('metadata: &active\n  command: run\n<<: *active\n', 'Instructions.'),
                ('mcpServers: {}\n', 'Instructions.'),
                ('plugins: []\n', 'Instructions.'),
                ('', '!`' + command + '`'),
                ('', '```!\n' + command + '\n```')):
            with self.subTest(extra=extra, body=body):
                self.frozen({'SKILL.md': ('---\nname: alpha\ndescription: Fixture skill\n' + extra + '---\n' + body).encode()})
                self.call('source', 'fetch', 'legacy')
                result = self.call('skill', 'validate', 'legacy/alpha', code=4)
                self.assertIn(result['error']['code'], ('skill.activation_unsupported', 'skill.metadata_unsupported'))
                self.assertFalse(marker.exists())
        self.frozen({'SKILL.md': b'---\nname: alpha\ndescription: "Passive description"\nlicense: MIT\ncompatibility: Python 3\nmetadata:\n  author: Example\n  version: "1.0"\n---\nInstructions.\n'})
        self.call('source', 'fetch', 'legacy')
        self.call('skill', 'validate', 'legacy/alpha')

    def test_public_resource_policy_checks_zero_and_multiple_files_before_reads(self):
        self.frozen({'a': b'12345678', 'b': b'abcdefgh', 'empty': b''})
        self.prepare_public()
        size = (self.source / 'skills/alpha/SKILL.md').stat().st_size
        self.assertEqual(self.limited_cli({'FILE_BYTES': size, 'PACKAGE_BYTES': size + 16}, 0)['data']['file_count'], 4)
        for policy in ({'FILE_BYTES': 0}, {'PACKAGE_BYTES': size + 15}, {'FILE_COUNT': 3}, {'TREE_BYTES': 1}):
            with self.subTest(policy=policy):
                result = self.limited_cli(policy, 5 if 'TREE_BYTES' in policy else 4)
                self.assertIn(result['error']['code'], ('skill.limit', 'git.output_limit'))
        with patch.object(packages, 'PACKAGE_BYTES', size + 15), patch.object(c, 'git', wraps=c.git) as calls:
            with self.assertRaises(c.MaskError):
                self.validate(self.git(self.source, 'rev-parse', 'HEAD'))
            self.assertFalse(any(call.args[1:3] == ('cat-file', 'blob') for call in calls.call_args_list))
        self.assertEqual((packages.FILE_BYTES, packages.PACKAGE_BYTES, packages.FILE_COUNT, packages.DEPTH),
                         (64 * 1024 * 1024, 256 * 1024 * 1024, 10000, 32))

    def test_portable_components_case_unicode_depth_and_activation(self):
        for path in ('../escape', '/absolute', 'a/../b', 'a\\b', 'a:b', 'nul.txt', 'x/COM1.log',
                     'x/lpt¹', 'bad.', 'bad ', 'x\x01', 'cafe\u0301/x', '/'.join(['a'] * 33)):
            with self.subTest(path=path), self.assertRaises(c.MaskError):
                packages.check_paths([path])
        for paths in (['A/first', 'a/second'], ['dir', 'dir/file'], ['File', 'file']):
            with self.subTest(paths=paths), self.assertRaises(c.MaskError):
                packages.check_paths(paths)
        for path in ('.codex/config.toml', '.claude/settings.json', '.mcp.json', 'mcp.json',
                     'hooks/hooks.json', 'nested/.codex-plugin/plugin.json', '.git/config', '.gitmodules'):
            with self.subTest(path=path), self.assertRaises(c.MaskError) as error:
                packages.check_paths([path])
            self.assertEqual(error.exception.code, 'skill.activation_unsupported')

    def test_raw_git_symlink_and_submodule_modes_refused(self):
        oid = self.git(self.source, 'rev-parse', 'HEAD:skills/alpha/SKILL.md')
        for mode, kind, object_id in (('120000', 'blob', oid),
                                      ('160000', 'commit', self.git(self.source, 'rev-parse', 'HEAD'))):
            with self.subTest(mode=mode):
                self.git(self.source, 'update-index', '--add', '--cacheinfo', mode + ',' + object_id + ',skills/alpha/special')
                self.git(self.source, 'commit', '-m', 'special mode')
                with self.assertRaises(c.MaskError) as error:
                    self.validate(self.git(self.source, 'rev-parse', 'HEAD'))
                self.assertEqual(error.exception.code, 'skill.entry_unsupported')
                self.git(self.source, 'update-index', '--force-remove', 'skills/alpha/special')

    def test_index_selected_package_does_not_scan_unrelated_tree(self):
        self.frozen()
        (self.source / 'mask-source.json').write_text(json.dumps(dict(schema_version=1, packages={'alpha': 'skills/alpha'})))
        self.frozen()
        self.prepare_public()
        entry = self.call('source', 'show', 'legacy')['data']['binding']
        with patch.object(sources, 'tree_entries', side_effect=AssertionError('unrelated recursive scan')):
            rows = sources.discover(Path(entry['cache']), 'legacy', entry, self.git(self.source, 'rev-parse', 'HEAD'), identifier='alpha')
        self.assertEqual([row['id'] for row in rows], ['alpha'])
        self.call('skill', 'validate', 'legacy/alpha')

    def test_fetch_storage_refusal_preserves_selected_commit_and_reports_staging(self):
        self.frozen()
        self.prepare_public()
        before = self.call('source', 'show', 'legacy')['data']['cached_revision']
        self.frozen({'new': b'new payload'})
        config = self.call('config', 'show')['data']['config']
        output = dict(data={})
        # Simulate growth visible only after a very fast fetch has completed.
        real_git = c.git
        completed = False
        def git(root, *args, **kwargs):
            nonlocal completed
            result = real_git(root, *args, **kwargs)
            if 'fetch' in args:
                completed = True
            return result
        with patch.object(c, 'git', side_effect=git), patch.object(sources, 'cache_bytes', side_effect=lambda root: sources.CACHE_BYTES + 1 if completed else 0):
            with self.assertRaises(c.MaskError) as error:
                sources.fetch(self.home, 'legacy', config['sources']['legacy'], 30, output)
        self.assertEqual(error.exception.code, 'source.fetch_limit')
        effects = output['data']['fetch_effects']
        self.assertFalse(effects['remote_refs_changed'])
        self.assertTrue(effects['retained_objects_possible'])
        self.assertTrue(effects['staging_ref'].startswith('refs/mask/acquiring/'))
        self.assertEqual(self.call('source', 'show', 'legacy')['data']['cached_revision'], before)
        self.assertEqual(self.git(Path(config['sources']['legacy']['cache']), 'rev-parse', effects['staging_ref']),
                         self.git(self.source, 'rev-parse', 'HEAD'))
