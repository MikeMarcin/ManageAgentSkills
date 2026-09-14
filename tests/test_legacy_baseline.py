"""Legacy starting states and the retired live-checkout paths for RFC-MASK-0021 (MASK-0100, MASK-0102).

``LegacyFixtureBytes`` is durable. The schema-true builder in ``tests.legacy_support`` writes v1 and v2 machines
with a registered legacy project, a registered legacy personal scope and an unregistered v1 declaration. The
current parsers accept every byte unchanged; machine configuration parses only with ``legacy=True`` and the
default refuses it with ``migration.required``. Later doctor-migration tests start from these states.

``LiveCheckoutBaseline`` recorded, through the public CLI, the defect RFC-MASK-0021 removes and proved that the
builder writes what the base program wrote (observed at 82b4200 and b92372f). Since MASK-0102 it is a retired-path
baseline over the same builder states: every command that linked into or extended the clone now refuses before any
effect. Evidence: docs/development/tap-cutover-baseline.md.
"""
import json
import os
from pathlib import Path

import mask_core as c
import mask_sources as sources
from tests.legacy_support import LegacyFixture, git, make_bare, snapshot, text_json, v2_config

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

    def legacy_config(self, path):
        """Machine configuration parses for migration only; every other reader refuses it."""
        value = self.canonical(path, lambda item: c.config(item, legacy=True))
        with self.assertRaises(c.MaskError) as refused:
            c.config(value)
        self.assertEqual((refused.exception.code, refused.exception.exit_code, refused.exception.details['schema_version']),
                         ('migration.required', 4, value['schema_version']))
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
        config = self.legacy_config(roots.home / 'config.json')
        self.assert_schema_shape(config, schema('machine-v1.schema.json'))
        self.assertEqual(config['source'], dict(root=str(roots.clone), remote='origin', branch='main'))
        state = self.canonical(roots.home / 'state.json', c.state)
        self.assertEqual((state['schema_version'], state['generation']), (2, 2))
        self.assert_legacy_consumers(roots, state)

    def test_v2_machine_keeps_the_clone_binding_beside_an_extra_tap(self):
        roots = self.legacy_machine(2)
        config = self.legacy_config(roots.home / 'config.json')
        self.assert_schema_shape(config, schema('machine-v2.schema.json'))
        self.assertEqual((config['legacy_source'], sorted(config['sources'])), ('legacy', ['extra', 'legacy']))
        self.assertEqual(config['sources']['legacy']['authoring'], str(roots.clone))
        self.assertEqual(config['sources']['legacy']['repository'], roots.upstream.as_uri())
        self.assertIsNone(config['sources']['extra']['authoring'])
        for name, entry in config['sources'].items():
            # A v2 entry never carries the tap line-ending policy the current binding adds (MASK-0109); otherwise they are equal.
            current = sources.binding(roots.home, name, entry['transport'], entry['ref'], entry['packages'], entry['authoring'])
            self.assertEqual((current.pop('line_endings'), 'line_endings' in entry, current), ('exact', False, entry))
        state = self.canonical(roots.home / 'state.json', c.state)
        self.assert_legacy_consumers(roots, state)

    def test_empty_registry_and_a_clone_without_remote(self):
        roots = self.legacy_machine(1, remote=False, project_skills=None, user_skills=None, straggler_skills=None)
        self.legacy_config(roots.home / 'config.json')
        self.assertEqual(self.canonical(roots.home / 'state.json', c.state), c.empty_state())
        self.assertEqual(sorted(p.name for p in roots.home.iterdir()), ['config.json', 'state.json'])
        catalog = c.config(v2_config(roots, extra_tap=False), legacy=True)['sources']['legacy']
        self.assertEqual((catalog['transport'], catalog['repository']), (str(roots.clone), roots.clone.as_uri()))


class LiveCheckoutBaseline(LegacyFixture):
    """Retired-path baseline: on the builder states the live-checkout program left, its clone-linking commands refuse.

    Removed commands are invocation errors (exit 2); the migration gate refuses the rest (exit 4). A snapshot of the
    whole disposable base (machine home, consumers, clone and upstream) is unchanged by every refusal.
    """

    def assert_refused(self, *args, code, error):
        before = snapshot(self.roots.base, self.roots.base)
        self.assertEqual(self.machine(*args, code=code)['error']['code'], error, args)
        self.assertEqual(snapshot(self.roots.base, self.roots.base), before, args)

    def test_legacy_install_no_longer_links_into_the_clone(self):
        roots = self.legacy_machine(1, project_skills=None, user_skills=None, straggler_skills=None)
        for args in (('install', 'alpha', '--project', roots.project), ('install', 'beta', '--user')):
            self.assert_refused(*args, code=4, error='migration.required')
        self.assertFalse([path for root in (roots.project, roots.personal) for path in root.rglob('*') if path.is_symlink()])

    def test_registered_clone_links_are_refused_not_reconciled(self):
        roots = self.legacy_machine(1)
        for args in (('apply', '--all'), ('ensure', '--project', roots.project), ('update',), ('update', '--user'),
                     ('link', 'adopt', '--project', roots.project, '--skill', 'alpha', '--target', 'codex', '--expect-source', roots.clone / 'skills/alpha')):
            self.assert_refused(*args, code=4, error='migration.required')

    def test_source_migrate_and_tap_add_no_longer_extend_the_clone_binding(self):
        roots = self.legacy_machine(1)
        make_bare(roots.extra)
        self.assert_refused('source', 'migrate', code=2, error='invocation.invalid')
        self.assert_refused('tap', 'add', 'extra', roots.extra, code=4, error='migration.required')
        self.assertEqual(c.kind(roots.home / 'sources'), 'missing')

    def test_empty_registry_and_remote_less_clone_refuse_the_retired_source_commands(self):
        self.legacy_machine(1, remote=False, project_skills=None, user_skills=None, straggler_skills=None)
        for args in (('source', 'migrate'), ('source', 'status')):
            self.assert_refused(*args, code=2, error='invocation.invalid')
        self.assert_refused('source', 'fetch', 'legacy', code=4, error='migration.required')

    def test_pin_migration_and_cache_updates_are_retired_on_a_v2_machine(self):
        roots = self.legacy_machine(2)
        self.assert_refused('migrate', '--to-pinned', '--project', roots.project, code=2, error='invocation.invalid')
        for args in (('source', 'fetch', 'legacy'), ('update', '--project', roots.project), ('lock', '--project', roots.project)):
            self.assert_refused(*args, code=4, error='migration.required')
        self.assertEqual(c.kind(roots.home / 'sources'), 'missing')
