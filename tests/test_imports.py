import argparse
import json
import os
from pathlib import Path
from unittest.mock import patch

import mask_core as c
import mask_packages as packages
import mask_provenance as provenance
from tests.support import Fixture


class ImportFixture(Fixture):
    def setUp(self):
        super().setUp()
        self.init()
        self.call('source', 'migrate')
        self.author = self.base / 'vendor-author'
        self.author.mkdir()
        self.git(self.author, 'init', '-b', 'main')
        self.git(self.author, 'config', 'user.name', 'Fixture')
        self.git(self.author, 'config', 'user.email', 'fixture@example.invalid')
        self.git(self.author, 'config', 'core.autocrlf', 'false')
        self.payload = self.author / 'skills/gamma'
        self.payload.mkdir(parents=True)
        (self.payload / 'SKILL.md').write_bytes(b'---\nname: gamma\ndescription: Imported fixture\n---\nInstructions.\n')
        (self.payload / 'raw.bin').write_bytes(b'\0\xff\r\n')
        (self.payload / 'empty').touch()
        (self.payload / 'run.py').write_bytes(b'raise RuntimeError("never execute")\n')
        (self.author / 'LICENSE').write_bytes(b'Root notice\r\n')
        (self.author / 'skills/NOTICE.md').write_bytes(b'Adjacent notice\n')
        self.git(self.author, 'add', '.')
        self.git(self.author, 'update-index', '--chmod=+x', 'skills/gamma/run.py')
        self.git(self.author, 'commit', '-m', 'vendor fixture')
        self.commit = self.git(self.author, 'rev-parse', 'HEAD')
        self.remote = self.base / 'vendor.git'
        self.git(self.base, 'clone', '--bare', str(self.author), str(self.remote))
        self.git(self.author, 'remote', 'add', 'origin', str(self.remote))
        self.call('tap', 'add', 'vendor', self.remote)
        self.target = self.source / 'skills/gamma'

    def fetch(self):
        self.call('source', 'fetch', 'vendor')

    def import_call(self, *args, **kwargs):
        return self.call('skill', 'import', 'vendor', '--mode', 'copy', '--into', 'legacy', '--path', 'skills/gamma', *args, **kwargs)

    def advance(self):
        self.git(self.author, 'add', '.')
        self.git(self.author, 'commit', '-m', 'changed fixture')
        self.git(self.author, 'push', 'origin', 'main')

    def direct_import(self):
        args = argparse.Namespace(command='skill.import', url='vendor', mode='copy', into='legacy', path='skills/gamma')
        output = dict(data={}, dry_run=False, changed=False, would_change=False)
        provenance.dispatch(args, output, self.home)
        return output


class ImportTests(ImportFixture):
    def test_preview_is_observational_and_import_preserves_raw_bytes_notices_and_index(self):
        before = self.snapshot()
        unresolved = self.import_call('--dry-run')
        self.assertTrue(unresolved['data']['resolution_required'])
        self.assertEqual(before, self.snapshot())
        self.fetch()
        (self.source / 'unrelated.txt').write_text('preserve staged work')
        self.git(self.source, 'add', 'unrelated.txt')
        index = (self.source / '.git/index').read_bytes()
        head = self.git(self.source, 'rev-parse', 'HEAD')
        before = self.snapshot()
        preview = self.import_call('--dry-run')
        self.assertTrue(preview['would_change'])
        self.assertEqual(before, self.snapshot())
        result = self.import_call('--expect-plan-hash', preview['data']['plan_hash'])
        self.assertTrue(result['changed'])
        self.assertEqual((self.target / 'raw.bin').read_bytes(), b'\0\xff\r\n')
        self.assertEqual((self.target / 'empty').read_bytes(), b'')
        self.assertEqual((self.target / '.mask-notices/0/NOTICE.md').read_bytes(), b'Adjacent notice\n')
        self.assertEqual((self.target / '.mask-notices/1/LICENSE').read_bytes(), b'Root notice\r\n')
        record = json.loads((self.target / provenance.RECORD).read_bytes())
        upstream = packages.validate(self.author, self.commit, 'skills/gamma', 'gamma')
        self.assertEqual(record['upstream']['files'], upstream.manifest())
        self.assertEqual(record['upstream']['payload_digest'], upstream.digest)
        self.assertNotEqual(record['curated']['content_digest'], upstream.digest)
        self.assertNotEqual(result['data']['artifact_payload_digest'], record['curated']['content_digest'])
        self.assertEqual(head, self.git(self.source, 'rev-parse', 'HEAD'))
        self.assertEqual(index, (self.source / '.git/index').read_bytes())
        self.assertEqual(sorted(result['data']['changed_paths']), sorted(str(item) for item in self.target.rglob('*') if item.is_file()))
        self.assertEqual(list((self.source / '.git').glob('mask-import-*')), [])
        if os.name != 'nt':
            self.assertTrue((self.target / 'run.py').stat().st_mode & 0o111)

    def test_existing_empty_concurrent_destination_is_never_replaced(self):
        self.fetch()
        native = c.publish_directory
        def collide(stage, target):
            self.assertTrue(stage.is_relative_to(self.source / '.git'))
            target.mkdir()
            native(stage, target)
        with patch.object(c, 'publish_directory', side_effect=collide), self.assertRaises(c.MaskError) as error:
            self.direct_import()
        self.assertEqual(error.exception.code, 'import.collision')
        self.assertEqual(list(self.target.iterdir()), [])
        self.assertEqual(list((self.source / '.git').glob('mask-import-*')), [])

    def test_existing_tracked_deleted_and_untracked_content_refuse(self):
        self.fetch()
        self.target.mkdir()
        (self.target / 'unrelated').write_text('keep')
        self.assertEqual(self.import_call(code=4)['error']['code'], 'import.collision')
        self.assertEqual((self.target / 'unrelated').read_text(), 'keep')
        self.git(self.source, 'add', 'skills/gamma/unrelated')
        (self.target / 'unrelated').unlink()
        self.target.rmdir()
        self.assertEqual(self.import_call(code=4)['error']['code'], 'import.collision')
        self.assertFalse(self.target.exists())

    def test_case_aliased_destination_component_is_preserved(self):
        self.fetch()
        alternate = self.source / 'skills/Gamma'
        alternate.mkdir()
        (alternate / 'unrelated').write_text('keep spelling and contents')
        self.assertEqual(self.import_call('--dry-run', code=4)['error']['code'], 'import.path_ambiguous')
        self.assertEqual((alternate / 'unrelated').read_text(), 'keep spelling and contents')

    def test_index_must_explicitly_map_new_package_and_guard_is_stale_on_change(self):
        self.fetch()
        index = self.source / 'mask-source.json'
        index.write_text(json.dumps(dict(schema_version=1, packages={'alpha': 'skills/alpha'})))
        self.assertEqual(self.import_call('--dry-run', code=4)['error']['code'], 'import.index_required')
        index.write_text(json.dumps(dict(schema_version=1, packages={'alpha': 'skills/alpha', 'gamma': 'skills/gamma'})))
        preview = self.import_call('--dry-run')
        index.write_text(index.read_text() + '\n')
        self.assertEqual(self.import_call('--expect-plan-hash', preview['data']['plan_hash'], code=4)['error']['code'], 'plan.stale')
        self.assertFalse(self.target.exists())
        self.import_call()

    def test_reserved_records_and_unsafe_packages_never_stage_or_publish(self):
        self.fetch()
        for relative, data in ((provenance.RECORD, b'{}'), (provenance.NOTICES + '/upstream', b'keep'),
                               ('.claude-plugin/plugin.json', b'{}')):
            with self.subTest(relative=relative):
                path = self.payload / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                self.advance()
                result = self.import_call(code=4)
                self.assertIn(result['error']['code'], ('import.provenance_collision', 'skill.activation_unsupported'))
                self.assertFalse(self.target.exists())
                self.assertEqual(list((self.source / '.git').glob('mask-import-*')), [])
                path.unlink()

    def test_mutated_staging_and_changed_config_refuse_before_publication(self):
        self.fetch()
        real = provenance.working_manifest
        def corrupt(stage, modes, **kwargs):
            if stage.name == 'payload':
                (stage / 'raw.bin').write_bytes(b'changed')
            return real(stage, modes, **kwargs)
        with patch.object(provenance, 'working_manifest', side_effect=corrupt), self.assertRaises(c.MaskError) as error:
            self.direct_import()
        self.assertEqual(error.exception.code, 'import.stage_invalid')
        self.assertFalse(self.target.exists())
        original = (self.home / 'config.json').read_bytes()
        def change_config(stage, modes, **kwargs):
            observed = real(stage, modes, **kwargs)
            value = json.loads(original)
            value['git_timeout_seconds'] += 1
            (self.home / 'config.json').write_text(c.text_json(value))
            return observed
        with patch.object(provenance, 'working_manifest', side_effect=change_config), self.assertRaises(c.MaskError) as error:
            self.direct_import()
        self.assertEqual(error.exception.code, 'plan.stale')
        self.assertFalse(self.target.exists())
        self.assertEqual(list((self.source / '.git').glob('mask-import-*')), [])

    def test_public_capabilities_and_one_package_selection(self):
        caps = {item['name']: item for item in self.call('capabilities')['data']['commands']}
        self.assertTrue(caps['skill.import']['network'])
        self.assertTrue(caps['skill.import']['plan_guard'])
        self.assertFalse(caps['skill.provenance']['network'])
        self.import_call('--mode', 'tap', code=2)
        second = self.author / 'skills/delta'
        second.mkdir()
        (second / 'SKILL.md').write_text('---\nname: delta\ndescription: Other fixture\n---\n')
        self.advance()
        self.assertEqual(self.call('skill', 'import', str(self.remote), '--mode', 'copy', '--into', 'legacy', code=4)['error']['code'], 'import.selection_required')
