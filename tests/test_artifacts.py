import copy
from dataclasses import replace
import json
import os
from pathlib import Path
import shutil
from unittest.mock import patch

import mask_core as c
import mask_packages as p
import mask_resolve as r
import mask_sources as s
import mask_store as store
from tests.support import TAP, Fixture


class ArtifactTests(Fixture):
    def setUp(self):
        super().setUp()
        self.git(self.source, 'config', 'core.autocrlf', 'false')
        skill = self.source / 'skills/alpha'
        (skill / 'SKILL.md').write_bytes(b'---\r\nname: alpha\r\ndescription: Raw artifact\r\n---\r\nBody\r\n')
        (skill / 'run.py').write_bytes(b'raise RuntimeError("never execute")\r\n')
        (skill / 'nested').mkdir()
        (skill / 'nested/empty').touch()
        self.git(self.source, 'add', '.')
        self.git(self.source, 'update-index', '--chmod=+x', 'skills/alpha/run.py')
        self.git(self.source, 'commit', '-m', 'raw artifact fixture')
        # Push the exact commit: re-adding through publish() could reset the index-only executable bit on POSIX.
        self.git(self.source, 'push', '-q', str(self.upstream), 'HEAD:main')
        self.init()
        self.call('source', 'fetch', TAP)
        self.declaration = dict(schema_version=2, sources=self.binding(), skills=[dict(source=TAP, id='alpha')])
        (self.project / '.mask.json').write_text(json.dumps(self.declaration))
        self.resolved = self.call('lock')['data']['lock']
        self.row = self.resolved['packages'][0]
        self.config = c.config(c.read_json(self.home / 'config.json'))
        self.entry = self.config['sources'][TAP]
        self.cache = s.cached(self.home, TAP, self.entry)
        self.payload = r.verify_resolution(self.home, TAP, self.entry, self.row)

    def fetch_locked(self, *args, **kwargs):
        return self.call('source', 'fetch', '--locked', '--project', self.project, *args, **kwargs)

    def test_public_offline_preview_raw_materialization_and_warm_no_git(self):
        before = self.snapshot()
        result = self.fetch_locked('--offline', '--dry-run')
        self.assertTrue(result['would_change'])
        self.assertEqual(before, self.snapshot())
        result = self.fetch_locked('--offline')
        self.assertTrue(result['changed'])
        root, target = store.location(self.home, self.row['payload_digest'], 'alpha')
        self.assertEqual((target / 'SKILL.md').read_bytes(), (self.source / 'skills/alpha/SKILL.md').read_bytes())
        self.assertEqual((target / 'nested/empty').read_bytes(), b'')
        self.assertEqual((target / 'run.py').stat().st_nlink, 1)
        if os.name != 'nt':
            self.assertTrue((target / 'run.py').stat().st_mode & 0o111)
            self.assertFalse((target / 'run.py').stat().st_mode & 0o222)
        with patch.object(c, 'git', side_effect=AssertionError('warm store must not use Git')):
            effects = store.ensure(self.home, self.declaration, self.resolved, self.config)
        self.assertTrue(effects['artifacts'][0]['reused'])
        before = self.snapshot()
        self.assertFalse(self.fetch_locked('--offline')['changed'])
        self.assertEqual(before, self.snapshot())
        other = self.base / 'independent-store'
        other.mkdir()
        store.materialize(other, self.row, self.payload)
        other_root, _ = store.location(other, self.row['payload_digest'], 'alpha')
        self.assertEqual(self.snapshot(root), self.snapshot(other_root))

    def test_corrupt_bytes_extra_directories_modes_and_manifest_are_preserved(self):
        store.materialize(self.home, self.row, self.payload)
        root, target = store.location(self.home, self.row['payload_digest'], 'alpha')
        for damage in ('bytes', 'directory', 'manifest', 'mode'):
            if damage == 'mode' and os.name == 'nt':
                continue  # Logical modes are verified through the manifest on Windows.
            leaf = target / 'run.py'
            manifest_path = root / 'manifest.json'
            original, manifest_raw = leaf.read_bytes(), manifest_path.read_bytes()
            leaf.chmod(0o755)
            manifest_path.chmod(0o644)
            if damage == 'bytes': leaf.write_bytes(b'changed')
            elif damage == 'directory': (target / 'extra').mkdir()
            elif damage == 'manifest': manifest_path.write_text('{}')
            else: leaf.chmod(0o644)
            before = self.snapshot(root)
            with self.subTest(damage=damage), self.assertRaises(c.MaskError):
                store.materialize(self.home, self.row, self.payload)
            self.assertEqual(before, self.snapshot(root))
            if (target / 'extra').exists(): (target / 'extra').rmdir()
            leaf.write_bytes(original)
            leaf.chmod(0o555)
            manifest_path.write_bytes(manifest_raw)
            manifest_path.chmod(0o444)

    def test_interpreter_bytecode_never_corrupts_a_published_artifact(self):
        import subprocess
        import sys
        store.materialize(self.home, self.row, self.payload)
        root, target = store.location(self.home, self.row['payload_digest'], 'alpha')
        # A host imports a skill script through the managed link, and the interpreter leaves bytecode beside it.
        module = "import sys; sys.path.insert(0, sys.argv[1])\ntry:\n    import run\nexcept RuntimeError:\n    pass"
        environment = {key: value for key, value in os.environ.items() if key not in ('PYTHONDONTWRITEBYTECODE', 'PYTHONPYCACHEPREFIX')}
        subprocess.run([sys.executable, '-c', module, str(target)], env=environment, check=True)
        self.assertTrue(list((target / '__pycache__').glob('run.*.pyc')))
        self.assertTrue(store.materialize(self.home, self.row, self.payload)['reused'])
        self.assertFalse((target / '__pycache__').exists())
        # Anything that is not plainly bytecode is never deleted; it is refused and kept for inspection.
        (target / '__pycache__').mkdir()
        (target / '__pycache__/run.cpython-313.pyc').write_bytes(b'bytecode')
        (target / '__pycache__/notes.txt').write_text('not bytecode')
        with self.assertRaises(c.MaskError) as error:
            store.materialize(self.home, self.row, self.payload)
        self.assertEqual(error.exception.code, 'artifact.corrupt')
        self.assertEqual(sorted(item.name for item in (target / '__pycache__').iterdir()), ['notes.txt', 'run.cpython-313.pyc'])

    def test_forwarded_dataclass_cannot_bypass_raw_validation(self):
        mutations = [replace(self.payload, digest='sha256:'+'0'*64), replace(self.payload, files=self.payload.files+(self.payload.files[0],)), replace(self.payload, files=(p.PayloadFile('../escape','100644',b'bad'),)), replace(self.payload, files=(p.PayloadFile('SKILL.md','120000',b'target'),)), replace(self.payload, files=(p.PayloadFile('SKILL.md','100644',b'---\nname: alpha\ndescription: a\nhooks: live\n---\n'),))]
        for payload in mutations:
            with self.assertRaises(c.MaskError):
                store.materialize(self.home, self.row, payload)
        bad = dict(self.row, metadata_digest='sha256:'+'0'*64)
        with self.assertRaises(c.MaskError):
            store.materialize(self.home, bad, self.payload)
        self.assertFalse((self.home / 'store').exists())

    def test_public_exact_hydration_keeps_selectors_and_controls_unchanged(self):
        selected = c.git(self.cache, 'rev-parse', 'refs/mask/selected')
        refs = (self.cache / 'mask-refs.json').read_bytes()
        # Task-owned cache fixture: remove objects, preserving selector evidence.
        def remove_readonly(action, path, error):
            os.chmod(path, 0o600)
            action(path)
        shutil.rmtree(self.cache / 'objects', onerror=remove_readonly)
        (self.cache / 'objects').mkdir()
        (self.cache / 'objects/info').mkdir()
        (self.cache / 'objects/pack').mkdir()
        controls = {path: path.read_bytes() for path in [self.project/'.mask.json', self.project/'.mask.lock.json', self.home/'config.json']}
        self.assertEqual(self.fetch_locked('--offline', code=4)['error']['code'], 'artifact.unavailable')
        before = self.snapshot()
        preview = self.fetch_locked('--dry-run')
        self.assertTrue(preview['data']['effects']['artifacts'][0]['resolution_required'])
        self.assertEqual(before, self.snapshot())
        result = self.fetch_locked()
        self.assertTrue(result['data']['effects']['network_attempted'])
        self.assertEqual(c.git(self.cache, 'rev-parse', 'refs/mask/selected'), selected)
        self.assertEqual((self.cache / 'mask-refs.json').read_bytes(), refs)
        self.assertEqual({path:path.read_bytes() for path in controls}, controls)
        self.assertIsNone(c.git(self.cache, 'rev-parse', '--verify', 'FETCH_HEAD', optional=True))

    def test_missing_exact_commit_no_substitution_and_cache_rewrite_refusal(self):
        bad = copy.deepcopy(self.resolved)
        bad['packages'][0]['commit'] = '0'*40
        (self.project/'.mask.lock.json').write_text(json.dumps(bad))
        before = (self.cache/'mask-refs.json').read_bytes()
        self.git(self.cache, 'config', 'url.https://invalid.example/rewrite.insteadOf', self.entry['transport'])
        snapshot = self.snapshot()
        refused = self.fetch_locked(code=4)
        self.assertEqual(snapshot, self.snapshot())
        self.assertFalse(refused['changed'])
        self.assertEqual(refused['error']['code'], 'source.identity_mismatch')
        self.assertFalse(refused['data']['effects']['network_attempted'])
        self.git(self.cache, 'config', '--unset-all', 'url.https://invalid.example/rewrite.insteadOf')
        result = self.fetch_locked(code=4)
        self.assertEqual(result['error']['code'], 'artifact.unavailable')
        self.assertTrue(result['data']['effects']['acquisitions'][0]['retained_objects_possible'])
        self.assertEqual((self.cache/'mask-refs.json').read_bytes(), before)
        self.assertFalse((self.home/'store').exists())

    def test_concurrent_empty_collision_and_stage_failure_cleanup(self):
        native = c.publish_directory
        def collide(stage, target):
            target.mkdir()
            native(stage, target)
        effects = {}
        with patch.object(c, 'publish_directory', side_effect=collide), self.assertRaises(c.MaskError):
            store.materialize(self.home, self.row, self.payload, effects=effects)
        self.assertEqual(effects['retained_directories'], [str(self.home/'store'),str(self.home/'store/v1')])
        root, _ = store.location(self.home, self.row['payload_digest'], 'alpha')
        self.assertEqual(list(root.iterdir()), [])
        self.assertEqual(list(root.parent.glob('.mask-stage-*')), [])
        root.rmdir()
        with patch.object(c, 'publish_directory', side_effect=c.MaskError('fixture.failure', 'fixture', 4)), self.assertRaises(c.MaskError):
            store.materialize(self.home, self.row, self.payload)
        self.assertFalse(root.exists())
        self.assertEqual(list(root.parent.glob('.mask-stage-*')), [])

    def test_reuse_identical_payload_across_commits_and_source_approval(self):
        store.materialize(self.home, self.row, self.payload)
        row = dict(self.row, commit='a'*40)
        self.assertTrue(store.materialize(self.home, row, replace(self.payload,commit=row['commit']))['reused'])
        config = copy.deepcopy(self.config)
        config['sources'][TAP]['repository'] = 'https://invalid.example/other'
        with self.assertRaises(c.MaskError) as error:
            store.ensure(self.home, self.declaration, self.resolved, config)
        self.assertEqual(error.exception.code, 'source.identity_mismatch')

    def test_validated_subset_and_public_stage_failure_effects(self):
        effects = store.ensure(self.home, self.declaration, self.resolved, self.config, coordinates=[])
        self.assertEqual(effects['artifacts'], [])
        self.assertFalse((self.home/'store').exists())
        with self.assertRaises(c.MaskError):
            store.ensure(self.home, self.declaration, self.resolved, self.config, coordinates=[TAP + '/unknown'])
        import argparse
        output = dict(dry_run=False, changed=False, would_change=False)
        with patch.object(c, 'publish_directory', side_effect=c.MaskError('fixture.failure','fixture',4)), self.assertRaises(c.MaskError):
            store.dispatch(argparse.Namespace(project=str(self.project),offline=True), output, self.home)
        self.assertTrue(output['changed'])
        self.assertEqual(output['transaction'], 'partial')
        self.assertEqual(output['data']['effects']['artifacts'][0]['retained_directories'], [str(self.home/'store'),str(self.home/'store/v1')])
        self.assertEqual(list((self.home/'store/v1').glob('.mask-stage-*')), [])

    def test_fresh_machine_exact_cache_has_no_selected_cursor_or_advertisement(self):
        home = self.base / 'fresh-machine'
        home.mkdir()
        config = copy.deepcopy(self.config)
        config['sources'][TAP] = s.binding(home, TAP, str(self.upstream))
        (home/'config.json').write_text(c.text_json(config))
        result = self.call('source', 'fetch', '--locked', '--project', self.project, '--home', home)
        cache = s.cached(home, TAP, config['sources'][TAP])
        self.assertTrue(result['changed'])
        self.assertTrue(result['data']['effects']['acquisitions'][0]['cache_created'])
        self.assertFalse((cache/'mask-refs.json').exists())
        self.assertIsNone(c.git(cache,'rev-parse','--verify','refs/mask/selected',optional=True))
        self.assertIsNone(c.git(cache,'rev-parse','--verify','FETCH_HEAD',optional=True))
        self.assertEqual(c.git(cache,'rev-parse','--verify','refs/mask/frozen/'+self.row['commit']),self.row['commit'])
        store.verify(home,self.row)

    def test_manifest_encoding_size_and_hardlink_refusal(self):
        with patch.object(store,'MANIFEST_BYTES',32), self.assertRaises(c.MaskError) as error:
            store.materialize(self.home,self.row,self.payload,dry_run=True)
        self.assertEqual(error.exception.code,'artifact.limit')
        self.assertFalse((self.home/'store').exists())
        store.materialize(self.home,self.row,self.payload)
        root,target = store.location(self.home,self.row['payload_digest'],'alpha')
        pathname = root/'manifest.json'
        raw = pathname.read_bytes()
        pathname.chmod(0o644)
        pathname.write_bytes(raw.decode().encode('utf-16'))
        with self.assertRaises(c.MaskError) as error:
            store.verify(self.home,self.row)
        self.assertEqual(error.exception.code,'artifact.invalid')
        pathname.write_bytes(raw)
        os.link(target/'run.py',self.base/'unmanaged-hardlink')
        with self.assertRaises(c.MaskError) as error:
            store.verify(self.home,self.row)
        self.assertEqual(error.exception.code,'artifact.corrupt')
