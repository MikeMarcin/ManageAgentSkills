"""Pre-implementation baseline for RFC-MASK-0020 (MASK-0098).

``LegacyFixtureBytes`` is durable. The schema-true builder in
``tests.legacy_support`` writes v1 and v2 machines with a registered legacy
project, a registered legacy personal scope and an unregistered v1 declaration,
and the current parsers accept every byte unchanged. Later doctor-migration tests
start from these states.

``LiveCheckoutBaseline`` records the defect RFC-MASK-0020 removes, through the
public CLI, and proves the builder writes what the program wrote. It describes
retired behavior. MASK-0099 removed ``init --source``: its bytes were compared with
``v1_config`` at 82b4200 and the machine configuration now comes from the builder,
while the program still writes everything after it. MASK-0100 (clone links,
``source migrate``, ``migrate``) and MASK-0101 (fetching ``update``) replace the
remaining assertions when they land. Evidence: docs/development/tap-cutover-baseline.md.
"""
import json
import os
from pathlib import Path
import subprocess

import mask_core as c
import mask_sources as sources
from tests.legacy_support import (AGENT_PATHS, LegacyFixture, git, legacy_state, link_text, make_bare, make_clone, remove_entry,
                                  snapshot, text_json, v2_config, write_machine)

SCHEMAS = Path(__file__).resolve().parents[1] / 'schemas'


def schema(name):
    return json.loads((SCHEMAS / name).read_text(encoding='utf-8'))


class LegacyFixtureBytes(LegacyFixture):
    """Every legacy starting state parses unchanged and prepares nothing a later card must prove."""

    def canonical(self, path, parse):
        raw = path.read_bytes().decode('utf-8')
        value = c.parse_json(raw)
        self.assertEqual(parse(value), value, path)
        self.assertEqual(text_json(value), raw, path)
        return value

    def assert_schema_shape(self, value, rule):
        """Required and permitted keys follow the published machine schema, recursively through objects."""
        self.assertLessEqual(set(rule.get('required', ())), set(value))
        if rule.get('additionalProperties') is False:
            self.assertLessEqual(set(value), set(rule['properties']))
        if 'const' in rule.get('properties', {}).get('schema_version', {}):
            self.assertEqual(value['schema_version'], rule['properties']['schema_version']['const'])
        extra = rule.get('additionalProperties')
        for key, item in value.items():
            nested = rule.get('properties', {}).get(key, extra if isinstance(extra, dict) else None)
            if isinstance(item, dict) and isinstance(nested, dict) and nested.get('type') == 'object':
                self.assert_schema_shape(item, nested)

    def assert_legacy_consumers(self, roots, state):
        records = c.consumer_records(state)
        self.assertEqual(set(records), {str(roots.project), str(roots.personal)})
        self.assertEqual(c.consumer_scope(state, str(roots.personal)), 'user')
        head = git(roots.clone, 'rev-parse', 'HEAD')
        for record in records.values():
            self.assertNotIn('mode', record)
            self.assertEqual(record['last_manifest']['schema_version'], 1)
            self.assertEqual(record['last_source_revision'], head)
            for relative, link in record['links'].items():
                leaf = Path(record['root']) / relative
                self.assertEqual(c.kind(leaf), 'symlink', leaf)
                self.assertEqual(os.readlink(leaf), link['link_text'])
                self.assertTrue(os.path.samefile(leaf, roots.clone / 'skills' / link['skill']), leaf)
        self.assertEqual(sorted(records[str(roots.project)]['links']), ['.agents/skills/alpha', '.claude/skills/alpha'])
        self.assertEqual(sorted(records[str(roots.personal)]['links']), ['.agents/skills/beta', '.claude/skills/beta'])
        for declaration in (roots.project / '.mask.json', roots.home / 'user.json', roots.straggler / '.mask.json'):
            self.assertEqual(self.canonical(declaration, c.manifest)['schema_version'], 1)
        self.assertNotIn(str(roots.straggler), records)
        for prepared in (roots.home / 'sources', roots.home / 'store', roots.home / 'pending.json', roots.home / 'user.lock.json',
                         roots.project / '.mask.lock.json', roots.straggler / '.claude', roots.straggler / '.agents'):
            self.assertEqual(c.kind(prepared), 'missing', prepared)

    def test_v1_machine_with_legacy_project_personal_scope_and_unregistered_declaration(self):
        roots = self.legacy_machine(1)
        config = self.canonical(roots.home / 'config.json', c.config)
        self.assert_schema_shape(config, schema('machine-v1.schema.json'))
        self.assertEqual(config['source'], dict(root=str(roots.clone), remote='origin', branch='main'))
        state = self.canonical(roots.home / 'state.json', c.state)
        self.assertEqual((state['schema_version'], state['generation']), (2, 2))
        self.assert_legacy_consumers(roots, state)

    def test_v2_machine_keeps_the_clone_binding_beside_an_extra_tap(self):
        roots = self.legacy_machine(2)
        config = self.canonical(roots.home / 'config.json', c.config)
        self.assert_schema_shape(config, schema('machine-v2.schema.json'))
        self.assertEqual((config['legacy_source'], sorted(config['sources'])), ('legacy', ['extra', 'legacy']))
        self.assertEqual(config['sources']['legacy']['authoring'], str(roots.clone))
        self.assertEqual(config['sources']['legacy']['repository'], roots.upstream.as_uri())
        self.assertIsNone(config['sources']['extra']['authoring'])
        for name, entry in config['sources'].items():
            self.assertEqual(sources.binding(roots.home, name, entry['transport'], entry['ref'], entry['packages'], entry['authoring']), entry)
        state = self.canonical(roots.home / 'state.json', c.state)
        self.assert_legacy_consumers(roots, state)

    def test_empty_registry_and_a_clone_without_remote(self):
        roots = self.legacy_machine(1, remote=False, project_skills=None, user_skills=None, straggler_skills=None)
        self.canonical(roots.home / 'config.json', c.config)
        self.assertEqual(self.canonical(roots.home / 'state.json', c.state), c.empty_state())
        self.assertEqual(sorted(p.name for p in roots.home.iterdir()), ['config.json', 'state.json'])
        catalog = c.config(v2_config(roots, extra_tap=False))['sources']['legacy']
        self.assertEqual((catalog['transport'], catalog['repository']), (str(roots.clone), roots.clone.as_uri()))


class LiveCheckoutBaseline(LegacyFixture):
    """The base program deploys from the user's clone and never fetches for update; the builder reproduces its bytes."""

    def setUp(self):
        super().setUp()
        for directory in (self.roots.personal, self.roots.project):
            directory.mkdir(parents=True)
        git(self.roots.project, 'init', '-q', '-b', 'main')
        make_clone(self.roots)

    def written(self):
        return snapshot(self.roots.base, self.roots.home, self.roots.project, self.roots.personal)

    def live_checkout_machine(self):
        """The v1 configuration and empty state that the retired ``init --source CLONE`` wrote (compared at 82b4200)."""
        write_machine(self.roots, 1, project_skills=None, user_skills=None, straggler_skills=None)

    def assert_builder_reproduces(self, version, **options):
        """Remove only what the program wrote, let the builder write that state again and compare every byte and link."""
        observed = self.written()
        for key in observed:
            remove_entry(self.roots.base / key)
        write_machine(self.roots, version, straggler_skills=None, **options)
        self.assertEqual(self.written(), observed)

    def clone_links(self):
        return {key: value for key, value in self.written().items() if value[0] == 'link'}

    def publish(self, name):
        (self.roots.clone / 'skills/alpha' / (name + '.md')).write_text(name + '\n', encoding='utf-8', newline='\n')
        git(self.roots.clone, 'add', 'skills')
        git(self.roots.clone, 'commit', '-q', '-m', name)
        git(self.roots.clone, 'push', '-q', 'origin', 'main')
        return git(self.roots.clone, 'rev-parse', 'HEAD')

    def test_legacy_install_links_project_and_personal_scope_into_the_clone(self):
        roots = self.roots
        # The configuration bytes come from the builder; their equality with init --source output was observed at 82b4200.
        self.live_checkout_machine()
        self.machine('install', 'alpha', '--project', roots.project)
        self.machine('install', 'beta', '--user')
        for root, identifier in ((roots.project, 'alpha'), (roots.personal, 'beta')):
            for agent_path in AGENT_PATHS.values():
                leaf = root / agent_path / identifier
                self.assertEqual(os.readlink(leaf), link_text(roots.clone / 'skills' / identifier), leaf)
        (roots.clone / 'skills/alpha/unreviewed.md').write_text('edited in the clone\n', encoding='utf-8')
        for agent_path in AGENT_PATHS.values():
            self.assertEqual((roots.project / agent_path / 'alpha/unreviewed.md').read_text(encoding='utf-8'), 'edited in the clone\n')
        self.assert_builder_reproduces(1)

    def test_source_migrate_keeps_the_clone_as_the_legacy_binding(self):
        roots = self.roots
        self.live_checkout_machine()
        self.machine('install', 'alpha', '--project', roots.project)
        self.machine('install', 'beta', '--user')
        links = self.clone_links()
        self.machine('source', 'migrate')
        make_bare(roots.extra)
        self.machine('tap', 'add', 'extra', roots.extra)
        config = c.read_json(roots.home / 'config.json')
        self.assertEqual((config['source']['root'], config['sources']['legacy']['authoring']), (str(roots.clone), str(roots.clone)))
        self.assertEqual(self.clone_links(), links)
        self.assertTrue(all('mode' not in record for record in c.consumer_records(c.read_json(roots.home / 'state.json')).values()))
        self.assertEqual(c.kind(roots.home / 'sources'), 'missing')
        self.assert_builder_reproduces(2)

    def test_empty_registry_and_remote_less_clone_match_the_builder(self):
        roots = self.roots
        git(roots.clone, 'remote', 'remove', 'origin')
        self.live_checkout_machine()
        self.assertEqual((roots.home / 'state.json').read_bytes().decode('utf-8'), text_json(legacy_state()))
        self.machine('source', 'migrate')
        self.assertEqual((roots.home / 'config.json').read_bytes().decode('utf-8'), text_json(v2_config(roots, extra_tap=False)))
        self.assertEqual(c.kind(roots.home / 'sources'), 'missing')

    def test_pinned_update_resolves_from_the_cache_and_never_fetches(self):
        roots = self.roots
        lock = roots.project / '.mask.lock.json'

        def locked():
            return json.loads(lock.read_text(encoding='utf-8'))['packages'][0]['commit']

        self.live_checkout_machine()
        self.machine('install', 'alpha', '--project', roots.project)
        self.machine('source', 'migrate')
        self.machine('migrate', '--to-pinned', '--project', roots.project)
        first = locked()
        cache = Path(c.read_json(roots.home / 'config.json')['sources']['legacy']['cache'])
        second = self.publish('second')
        refused = self.machine('update', '--project', roots.project, code=4)
        self.assertEqual(refused['error']['code'], 'lock.resolution_required')
        self.assertEqual((c.kind(cache), locked()), ('missing', first))
        self.machine('source', 'fetch', 'legacy')
        self.machine('update', '--project', roots.project)
        self.assertEqual(locked(), second)
        third = self.publish('third')
        refs = git(cache, 'for-each-ref')
        self.assertFalse(self.machine('update', '--project', roots.project)['changed'])
        self.assertEqual((locked(), git(cache, 'for-each-ref')), (second, refs))
        self.assertNotEqual(subprocess.run(['git', '-C', str(cache), 'cat-file', '-e', third + '^{commit}'], capture_output=True).returncode, 0)
        self.machine('source', 'fetch', 'legacy')
        self.machine('update', '--project', roots.project)
        self.assertEqual(locked(), third)
