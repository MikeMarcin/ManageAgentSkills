from pathlib import Path
import json
import mask_core as core
from tests.support import Fixture


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
        # Legacy live-checkout starting state until MASK-0100 retires the v1 catalog.
        self.legacy_init()
        (self.source / 'skills/alpha/install.py').write_text('raise RuntimeError("never execute")')
        before = self.snapshot()
        self.assertEqual(len(self.call('skill', 'list')['data']['skills']), 2)
        shown = self.call('skill', 'show', 'alpha', '--content')['data']
        self.assertEqual(shown['scope'], 'mask-package-v1'); self.assertIn('Fixture instructions', shown['content'])
        self.call('skill', 'validate', '--all')
        self.assertEqual(before, self.snapshot())

    def test_source_links_and_unsupported_metadata(self):
        # Legacy live-checkout starting state until MASK-0100 retires the v1 catalog.
        self.legacy_init()
        link = self.source / 'skills/alpha/support'
        link.symlink_to(self.project, target_is_directory=True)
        self.assertEqual(self.call('skill', 'show', 'alpha', code=3)['error']['code'], 'skill.path_escape')
        link.unlink()
        (self.source / 'skills/alpha/SKILL.md').write_text('---\nname: alpha\ndescription: |\n  multiline\n---\n')
        self.assertEqual(self.call('skill', 'show', 'alpha', code=3)['error']['code'], 'skill.metadata_unsupported')

    def test_strict_json_ids_config(self):
        for text in ['{"a":1,"a":2}', '{"a":NaN}']:
            with self.assertRaises(core.MaskError): core.parse_json(text)
        for value in ['../x', '-x', 'CON', 'con', 'lpt1', 'synced', 'A', 'x/y', 'C:x', 'a '*40]:
            with self.assertRaises(core.MaskError): core.skill_id(value)
        for value in [dict(schema_version=True, skills=[]), dict(schema_version=2, skills=[]), dict(schema_version=1, skills=[], typo=0), dict(schema_version=1, skills=['alpha', 'alpha']), dict(schema_version=1, skills=[], targets=[])]:
            with self.assertRaises(core.MaskError): core.manifest(value)
        self.init()
        path = self.home / 'config.json'
        value = json.loads(path.read_text()); value['git_timeout_seconds'] = True; path.write_text(json.dumps(value))
        self.call('config', 'show', code=3)

    def test_defaults_change_without_links(self):
        self.init()
        self.assertTrue(self.call('config', 'set', '--target', 'codex', '--git-timeout', '12')['changed'])
        before = self.snapshot()
        self.assertFalse(self.call('config', 'set', '--target', 'codex', '--git-timeout', '12')['changed'])
        self.assertEqual(before, self.snapshot())
        self.call('config', 'set', '--git-timeout', '0', code=2)
