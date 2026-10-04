from pathlib import Path
import json
import os
import mask_core as core
from tests.support import TAP, Fixture


class CatalogTests(Fixture):
    def test_init_dry_run_and_noop(self):
        # init on an empty MASK_HOME writes an empty v3 tap catalog; it no longer selects a checkout.
        before = self.snapshot()
        preview = self.call('init', '--dry-run')
        self.assertFalse(preview['changed']); self.assertTrue(preview['would_change'])
        self.assertEqual(before, self.snapshot())
        self.assertTrue(self.call('init')['changed'])
        before = self.snapshot()
        self.assertFalse(self.call('init')['changed'])
        self.assertEqual(before, self.snapshot())
        self.assertEqual(self.call('config', 'show')['data']['config']['sources'], {})
        self.assertNotEqual(self.call('config', 'show')['data']['program_root'], str(self.source))

    def test_inspection_is_passive(self):
        # skill list/show/validate read the fetched tap cache (RFC-MASK-0021): nothing is written and package code never runs.
        self.init()
        marker = self.base / 'package-script-ran'
        (self.source / 'skills/alpha/install.py').write_text(f'from pathlib import Path\nPath({str(marker)!r}).write_text("executed")\n', encoding='utf-8', newline='\n')
        self.publish('package with a script')
        before = self.snapshot()
        unfetched = self.call('skill', 'list')['data']
        self.assertEqual((unfetched['skills'], unfetched['unresolved_sources']), ([], [TAP]))
        self.assertEqual(before, self.snapshot())
        self.call('source', 'fetch')
        before = self.snapshot()
        self.assertEqual([row['coordinate'] for row in self.call('skill', 'list')['data']['skills']], [TAP + '/alpha', TAP + '/beta'])
        shown = self.call('skill', 'show', 'alpha', '--content')['data']
        self.assertEqual(shown['validation'], 'metadata_only'); self.assertIn('Fixture instructions', shown['content'])
        validated = self.call('skill', 'validate', '--all')['data']['skills']
        self.assertEqual([(row['id'], row['scope'], row['validation']) for row in validated], [('alpha', 'mask-package-v1', 'payload'), ('beta', 'mask-package-v1', 'payload')])
        self.assertEqual(self.call('skill', 'validate', 'alpha')['data']['file_count'], 2)
        self.assertEqual(before, self.snapshot())
        self.assertFalse(marker.exists())

    def test_source_links_and_unsupported_metadata(self):
        # The unsafe package reaches MASK only through the tap upstream and a fetch; refusals are read from the cache.
        self.init()
        self.git(self.source, 'config', 'core.symlinks', 'true')  # Record the link as a Git link (mode 120000) on Windows too.
        link = self.source / 'skills/alpha/support'
        link.symlink_to(self.project, target_is_directory=True)
        self.publish('linked support entry')
        self.assertTrue(self.git(self.source, 'ls-tree', 'HEAD', 'skills/alpha/support').startswith('120000 blob '))
        self.call('source', 'fetch')
        before = self.snapshot()
        # Metadata inspection reads only SKILL.md; payload validation and install refuse the linked entry.
        self.assertEqual(self.call('skill', 'show', 'alpha')['data']['validation'], 'metadata_only')
        for args in (('skill', 'validate', 'alpha'), ('skill', 'validate', '--all'), ('install', 'alpha')):
            self.assertEqual(self.call(*args, code=4)['error']['code'], 'skill.entry_unsupported', args)
        self.assertEqual(before, self.snapshot())
        os.rmdir(link) if os.name == 'nt' else link.unlink()
        (self.source / 'skills/alpha/SKILL.md').write_text('---\nname: alpha\ndescription: |\n  multiline\n---\n', encoding='utf-8', newline='\n')
        self.publish('multiline metadata')
        self.call('source', 'fetch')
        before = self.snapshot()
        for args in (('skill', 'list'), ('skill', 'show', 'alpha'), ('skill', 'validate', 'alpha')):
            self.assertEqual(self.call(*args, code=3)['error']['code'], 'skill.metadata_unsupported', args)
        self.assertEqual(before, self.snapshot())

    def test_strict_json_ids_config(self):
        for text in ['{"a":1,"a":2}', '{"a":NaN}']:
            with self.assertRaises(core.MaskError): core.parse_json(text)
        for value in ['../x', '-x', 'CON', 'con', 'lpt1', 'synced', 'A', 'x/y', 'C:x', 'a '*40]:
            with self.assertRaises(core.MaskError): core.skill_id(value)
        for value in [dict(schema_version=True, skills=[]), dict(schema_version=1, skills=[]), dict(schema_version=2, skills=[]), dict(schema_version=2, sources={}, skills=[], typo=0)]:
            with self.assertRaises(core.MaskError): core.selection_manifest(value)
        self.init()
        path = self.home / 'config.json'
        value = json.loads(path.read_text(encoding='utf-8')); value['git_timeout_seconds'] = True; path.write_text(json.dumps(value))
        self.call('config', 'show', code=3)

    def test_defaults_change_without_links(self):
        self.init()
        self.assertTrue(self.call('config', 'set', '--target', 'codex', '--git-timeout', '12')['changed'])
        before = self.snapshot()
        self.assertFalse(self.call('config', 'set', '--target', 'codex', '--git-timeout', '12')['changed'])
        self.assertEqual(before, self.snapshot())
        self.call('config', 'set', '--git-timeout', '0', code=2)
