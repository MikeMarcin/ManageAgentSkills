import dataclasses
import json
import unittest

import mask
import mask_adapters as adapters
import mask_core as c
import mask_integration as integration
import mask_packages as packages
import mask_resolve as resolve
from tests.support import ENTRY


class AdapterTests(unittest.TestCase):
    def test_runtime_paths_capabilities_and_scope_contract(self):
        self.assertEqual(set(adapters.BY_ID), {'claude', 'codex'})
        self.assertEqual(mask.ADAPTERS, c.ADAPTERS)
        self.assertEqual(c.ADAPTERS, adapters.paths())
        _, leaves = __import__('tests.engine_cli', fromlist=['make_parser']).make_parser()
        advertised = mask.capabilities(leaves)['adapter_contracts']
        self.assertEqual(advertised, adapters.capabilities())
        for adapter in adapters.BUILTINS:
            data = adapter.describe()
            self.assertEqual(data['host_load'], 'not_verified')
            self.assertEqual(data['platforms']['linux'], 'best_effort_unverified')
            for scope in ('project', 'user'):
                self.assertEqual(adapters.relative(adapter.id, scope, 'alpha'), adapter.path(scope) + '/alpha')
                root = ENTRY.parent
                self.assertEqual(integration.host_file(dict(root=str(root), mode=adapter.id, scope=scope)), root / adapter.config_path(scope))
        self.assertEqual(adapters.BY_ID['claude'].gate, 'warning')
        self.assertEqual(adapters.BY_ID['codex'].gate, 'documented_stop_unverified')
        values = dataclasses.asdict(adapters.BUILTINS[0])
        for field in ('platform_evidence', 'evidence', 'host_load', 'host_gate_enforcement'):
            values.pop(field)
        values['id'] = 'future'
        future = adapters.Adapter(**values).describe()
        self.assertEqual(future['platforms'], {})
        self.assertIsNone(future['evidence'])
        self.assertEqual(future['host_load'], 'not_verified')
        self.assertNotIn('future', mask.capabilities(leaves)['targets'])

    def test_all_persisted_adapter_enums_match_audited_ids(self):
        count = 0
        def walk(value):
            nonlocal count
            if isinstance(value, dict):
                if 'enum' in value and set(value['enum']) & set(adapters.BY_ID):
                    self.assertEqual(set(value['enum']), set(adapters.BY_ID))
                    count += 1
                for nested in value.values():
                    walk(nested)
            elif isinstance(value, list):
                for nested in value:
                    walk(nested)
        for path in (ENTRY.parent / 'schemas').glob('*.json'):
            with self.subTest(schema=path.name):
                walk(json.loads(path.read_text(encoding='utf-8')))
        self.assertGreaterEqual(count, 12)

    def test_reserved_and_active_package_boundaries_derive_from_data(self):
        for name in adapters.RESERVED_NAMES:
            with self.assertRaises(c.MaskError):
                c.skill_id(name)
        for component in adapters.HAZARDOUS_COMPONENTS:
            with self.subTest(component=component), self.assertRaises(c.MaskError) as caught:
                packages.passive_path(['assets', component, 'file'])
            self.assertEqual(caught.exception.code, 'skill.activation_unsupported')
        for name in adapters.HAZARDOUS_FILES:
            with self.subTest(name=name), self.assertRaises(c.MaskError):
                packages.passive_path(['assets', name])
        for suffix in adapters.COMMON_SUFFIXES:
            with self.assertRaises(c.MaskError):
                packages.passive_path(['assets', *suffix])
        for field in adapters.ACTIVE_FRONTMATTER:
            text = '---\nname: alpha\ndescription: Passive\n' + field + ': forbidden\n---\n'
            with self.subTest(field=field), self.assertRaises(c.MaskError):
                packages.passive_frontmatter(text)
        packages.passive_path(['scripts', 'example.py'])

    def test_future_publisher_assertion_is_not_requested_adapter_support(self):
        value = resolve.metadata(resolve.canonical(dict(schema_version=1, agents=['future'])))
        self.assertEqual(value['agents'], ['future'])
        from tests.test_selection_conflicts import contribution, evaluate
        result = evaluate([contribution('local')], {'vendor/alpha': value})
        self.assertFalse(result['blocked'])
        self.assertEqual({row['status'] for row in result['outcomes']}, {'excluded_by_metadata'})
        self.assertEqual(result['deployable'], [])
        with self.assertRaises(c.MaskError):
            resolve.agents(['future'])
