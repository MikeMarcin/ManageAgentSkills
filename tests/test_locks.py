import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import mask_core as c
import mask_resolve as r
import mask_sources as s
from tests.support import Fixture


class ModelTests(unittest.TestCase):
    def selection(self):
        return dict(schema_version=2, sources={'vendor': {'repository': 'https://example.invalid/skills', 'ref': 'refs/heads/main'}}, skills=[{'source': 'vendor', 'id': 'alpha'}])

    def test_canonical_sets_defaults_and_complete_intent(self):
        first = self.selection()
        first['skills'][0].update(agents=['codex', 'claude'], introduced_by=['z', 'a'], when={'platforms': ['windows', 'linux']})
        other = copy.deepcopy(first)
        other['default_agents'] = 'all'
        other['sources']['vendor']['packages'] = 'skills'
        for key in ('agents', 'introduced_by'):
            other['skills'][0][key].reverse()
        other['skills'][0]['when']['platforms'].reverse()
        self.assertEqual(r.selection_digest(first), r.selection_digest(other))
        other['skills'][0]['introduced_by'].append('local')
        self.assertNotEqual(r.selection_digest(first), r.selection_digest(other))
        self.assertEqual(r.canonical({'ü': 'ß', 'a': 1}), '{"a":1,"ü":"ß"}'.encode())
        inherited = r.selection(self.selection())
        self.assertNotIn('agents', inherited['skills'][0])
        self.assertEqual(r.selection(inherited), inherited)
        explicit = copy.deepcopy(inherited)
        explicit['skills'][0]['agents'] = 'all'
        self.assertNotEqual(r.selection_digest(inherited), r.selection_digest(explicit))

    def test_closed_canonical_ref_unicode_and_legacy_state_seam(self):
        for raw in [b'{"a":1,"a":2}', b'{"a":1.0}', b'{"a":NaN}', b'{"a":9007199254740992}', b'{"a":-1}', b'{"a":"\\ud800"}', b'{"a":Infinity}']:
            with self.subTest(raw=raw), self.assertRaises(c.MaskError):
                r.parse(raw, 'selection')
        for field, value in [('extra', 1), ('skills', [dict(source='vendor', id='alpha', when={})]), ('sources', {'vendor': dict(repository='https://example.invalid/skills', ref='main')})]:
            bad = self.selection()
            bad[field] = value
            with self.subTest(field=field), self.assertRaises(c.MaskError):
                r.selection(bad)
        self.assertEqual(c.selection_manifest(self.selection())['schema_version'], 2)
        with self.assertRaises(c.MaskError):
            c.manifest(self.selection())
        self.assertEqual(c.manifest(dict(schema_version=1, skills=['beta', 'alpha']))['skills'], ['alpha', 'beta'])


class LockTests(Fixture):
    def setUp(self):
        super().setUp()
        self.init()
        self.call('source', 'migrate')
        self.git(self.source, 'config', 'core.autocrlf', 'false')
        self.declaration = dict(schema_version=2, sources={'legacy': dict(repository=self.source.as_uri(), ref='refs/heads/main')}, skills=[dict(source='legacy', id='alpha'), dict(source='legacy', id='beta', when={'platforms': ['windows']})])
        self.write_selection()
        self.target = self.project / '.mask.lock.json'

    def write_selection(self):
        (self.project / '.mask.json').write_text(json.dumps(self.declaration), encoding='utf-8')

    def fetch(self):
        self.call('source', 'fetch', 'legacy')

    def locked(self, *args, **kwargs):
        return self.call('lock', '--project', self.project, *args, **kwargs)

    def commit(self, text='change'):
        self.git(self.source, 'add', '.')
        self.git(self.source, 'commit', '-m', text)
        return self.git(self.source, 'rev-parse', 'HEAD')

    def test_public_offline_preview_raw_modes_digests_and_user_scope(self):
        skill = self.source / 'skills/alpha'
        (skill / 'SKILL.md').write_bytes(b'---\r\nname: alpha\r\ndescription: CRLF fixture\r\n---\r\nBody\r\n')
        (skill / 'script.py').write_bytes(b'raise RuntimeError("never execute")\r\n')
        (skill / 'empty').touch()
        (skill / 'mask-skill.json').write_bytes(b'{"schema_version":1,"agents":["codex","claude"]}\r\n')
        (skill / '.mask-provenance.json').write_bytes(b'{"publisher":"assertion"}\r\n')
        self.git(self.source, 'add', '.')
        self.git(self.source, 'update-index', '--chmod=+x', 'skills/alpha/script.py')
        self.git(self.source, 'commit', '-m', 'raw mode fixture')
        commit = self.git(self.source, 'rev-parse', 'HEAD')
        before = self.snapshot()
        self.assertEqual(self.locked('--dry-run', code=4)['error']['code'], 'lock.resolution_required')
        self.assertEqual(before, self.snapshot())
        self.fetch()
        before = self.snapshot()
        preview = self.locked('--dry-run')
        self.assertEqual(before, self.snapshot())
        self.assertFalse(preview['data']['portable'])
        self.assertEqual(preview['data']['network'], 'none')
        result = self.locked('--expect-plan-hash', preview['data']['plan_hash'])
        rows = result['data']['lock']['packages']
        self.assertEqual(len(rows), 2)  # Includes the windows-only binding on every OS.
        self.assertEqual(rows[0]['commit'], commit)
        self.assertEqual(rows[0]['provenance_digest'], c.digest((skill / '.mask-provenance.json').read_bytes()))
        config = c.config(c.read_json(self.home / 'config.json'))
        declaration, lock = r.read_exact_lock(self.project, home=self.home, config=config)
        cache = s.cached(self.home, 'legacy', config['sources']['legacy'])
        payload = r.frozen_payload(cache, rows[0])
        self.assertEqual(next(f.mode for f in payload.files if f.path == 'script.py'), '100755')
        self.assertEqual(next(f.data for f in payload.files if f.path == 'SKILL.md'), (skill / 'SKILL.md').read_bytes())
        self.assertEqual(rows[1]['metadata_digest'], c.digest(b'null'))
        self.assertNotEqual(rows[0]['metadata_digest'], rows[1]['metadata_digest'])
        (self.home / 'user.json').write_text(json.dumps(self.declaration))
        self.assertEqual(self.call('lock', '--user')['data']['lock'], lock)
        before = self.snapshot()
        self.assertFalse(self.locked()['changed'])
        self.assertEqual(before, self.snapshot())

    def test_retained_locks_selected_refresh_and_origin_only_edits(self):
        self.fetch()
        first = self.locked()['data']['lock']
        raw = self.target.read_bytes()
        (self.source / 'skills/alpha/data').write_bytes(b'next alpha')
        (self.source / 'skills/beta/data').write_bytes(b'next beta')
        next_commit = self.commit()
        self.fetch()
        self.assertFalse(self.locked()['changed'])
        self.assertEqual(self.target.read_bytes(), raw)
        selected = self.locked('--refresh', '--skill', 'legacy/alpha')['data']['lock']
        self.assertEqual(selected['packages'][0]['commit'], next_commit)
        self.assertEqual(selected['packages'][1], first['packages'][1])
        self.declaration['skills'][0]['introduced_by'] = ['local profile']
        self.write_selection()
        updated = self.locked()['data']['lock']
        self.assertEqual(updated['packages'], selected['packages'])
        self.assertNotEqual(updated['selection_digest'], selected['selection_digest'])
        self.assertEqual(self.locked('--skill', 'legacy/alpha', code=2)['error']['code'], 'invocation.invalid')

    def test_moved_annotated_tag_and_branch_rewrite_require_rebind(self):
        self.git(self.source, 'tag', '-a', 'release', '-m', 'release')
        self.declaration['skills'][0]['version'] = {'ref': 'refs/tags/release'}
        self.write_selection()
        self.fetch()
        self.call('source', 'inspect', 'legacy', '--ref', 'refs/tags/release')
        self.locked()
        (self.source / 'skills/alpha/data').write_text('next')
        next_commit = self.commit()
        self.git(self.source, 'tag', '-f', '-a', 'release', '-m', 'moved')
        self.fetch()
        self.call('source', 'inspect', 'legacy', '--ref', 'refs/tags/release')
        self.assertEqual(self.locked('--refresh', '--skill', 'legacy/alpha', code=4)['error']['code'], 'lock.ref_rebound')
        result = self.locked('--refresh', '--skill', 'legacy/alpha', '--allow-ref-rebind')
        self.assertEqual(result['data']['lock']['packages'][0]['commit'], next_commit)
        self.locked('--refresh', '--skill', 'legacy/beta')
        self.git(self.source, 'reset', '--hard', 'HEAD~1')
        self.fetch()
        self.assertEqual(self.locked('--refresh', '--skill', 'legacy/beta', code=4)['error']['code'], 'lock.ref_rebound')
        self.locked('--refresh', '--skill', 'legacy/beta', '--allow-ref-rebind')

    def test_exact_pin_never_moves_and_stale_preview_refuses(self):
        self.fetch()
        first = self.locked()['data']['lock']
        self.declaration['skills'][0]['version'] = {'commit': first['packages'][0]['commit']}
        self.write_selection()
        self.assertEqual(self.locked(code=4)['error']['code'], 'lock.stale')
        self.locked('--refresh', '--skill', 'legacy/alpha')
        preview = self.locked('--refresh', '--dry-run')
        (self.source / 'skills/beta/next').write_text('next')
        self.commit()
        self.fetch()
        before = self.target.read_bytes()
        self.assertEqual(self.locked('--refresh', '--expect-plan-hash', preview['data']['plan_hash'], code=4)['error']['code'], 'plan.stale')
        self.assertEqual(before, self.target.read_bytes())
        self.assertEqual(self.locked('--refresh')['data']['lock']['packages'][0], r.lock(json.loads(before))['packages'][0])

    def test_v2_missing_stale_coherent_guards_and_legacy_mutations(self):
        self.assertEqual(self.call('ensure', code=4)['error']['code'], 'integration.approval_required')
        self.assertEqual(self.call('apply', code=4)['error']['code'], 'project.not_registered')
        for args in [('project', 'show'), ('project', 'set', '--clear'), ('project', 'register')]:
            self.assertEqual(self.call(*args, code=4)['error']['code'], 'lock.missing')
        self.fetch()
        self.locked()
        self.call('integration', 'approve', '--project', self.project)
        self.declaration['skills'][0]['introduced_by'] = ['edit']
        self.write_selection()
        self.assertEqual(self.call('ensure', code=4)['error']['code'], 'lock.stale')
        self.locked()
        for args in [('ensure',), ('project', 'show')]:
            self.assertEqual(self.call(*args, code=4)['error']['code'], 'targeting.unsupported')
        self.assertEqual(self.call('apply', code=4)['error']['code'], 'project.not_registered')
        self.assertEqual(self.call('project', 'require', 'beta', code=4)['error']['code'], 'selection.command_unsupported')
        self.declare(['alpha'])
        self.call('project', 'require', 'beta')
        self.assertEqual(self.call('project', 'show')['data']['manifest']['skills'], ['alpha', 'beta'])

    def test_tampered_identity_path_format_digests_and_metadata_refuse(self):
        self.fetch()
        original = self.locked()['data']['lock']
        for field, value, error in [('path', 'skills/beta', 'skill.name_mismatch'), ('payload_digest', 'sha256:' + '0' * 64, 'lock.digest_mismatch'), ('metadata_digest', 'sha256:' + '0' * 64, 'lock.digest_mismatch'), ('repository', 'https://example.invalid/wrong', 'lock.stale')]:
            bad = copy.deepcopy(original)
            bad['packages'][0][field] = value
            self.target.write_text(json.dumps(bad))
            actual = self.locked(code=4)['error']['code']
            if field == 'path':
                self.assertIn(actual, ('skill.invalid', 'skill.name_mismatch', 'lock.path_mismatch'))
            else:
                self.assertEqual(actual, error)
        for field, value in [('git_object_format', 'sha256'), ('commit', 'a' * 39), ('path', '../escape'), ('extra', 1)]:
            bad = copy.deepcopy(original)
            bad['packages'][0][field] = value
            with self.subTest(field=field), self.assertRaises(c.MaskError):
                r.lock(bad)
        self.target.write_text(json.dumps(original))
        self.declaration['sources']['legacy']['packages'] = 'other'
        self.write_selection()
        self.assertEqual(self.locked(code=4)['error']['code'], 'source.identity_mismatch')
        with self.assertRaises(c.MaskError):
            r.metadata(b'{"schema_version":1,"execute":"script"}')

    def test_lock_is_network_free_and_rechecks_inputs_before_write(self):
        self.fetch()
        config = c.config(c.read_json(self.home / 'config.json'))
        with patch.object(s, 'fetch', side_effect=AssertionError('network')), patch.object(s, 'remote_refs', side_effect=AssertionError('network')):
            self.assertEqual(len(r.resolve_candidate(self.declaration, config, self.home)['packages']), 2)
        import argparse
        original = r.resolve_candidate
        def mutate(*args, **kwargs):
            result = original(*args, **kwargs)
            (self.project / '.mask.json').write_text('{}')
            return result
        with patch.object(r, 'resolve_candidate', side_effect=mutate), self.assertRaises(c.MaskError) as error:
            r.dispatch(argparse.Namespace(project=str(self.project)), dict(dry_run=False), self.home)
        self.assertEqual(error.exception.code, 'plan.stale')
        self.assertFalse(self.target.exists())

    def test_sha256_cache_and_full_commit_identity(self):
        other = self.base / 'sha256'
        other.mkdir()
        # Git versions supporting MASK's existing SHA-256 cache lane are required.
        self.git(other, 'init', '--object-format=sha256', '-b', 'main')
        self.git(other, 'config', 'user.name', 'Fixture')
        self.git(other, 'config', 'user.email', 'fixture@example.invalid')
        skill = other / 'SKILL.md'
        skill.write_bytes(b'---\nname: alpha\ndescription: SHA256 fixture\n---\nBody\n')
        self.git(other, 'add', '.')
        self.git(other, 'commit', '-m', 'sha256 fixture')
        self.call('tap', 'add', 'sha', other)
        self.call('source', 'fetch', 'sha')
        self.declaration = dict(schema_version=2, sources={'sha': dict(repository=other.as_uri())}, skills=[dict(source='sha', id='alpha')])
        self.write_selection()
        row = self.locked()['data']['lock']['packages'][0]
        self.assertEqual(row['git_object_format'], 'sha256')
        self.assertEqual(len(row['commit']), 64)
        self.assertEqual(row['path'], '.')
        self.assertEqual(row['selector'], {'ref': 'refs/heads/main'})

    def test_output_byte_limit_and_replaced_root_fail_before_publication(self):
        import argparse
        self.fetch()
        with patch.object(r, 'MODEL_BYTES', 700), self.assertRaises(c.MaskError) as error:
            r.dispatch(argparse.Namespace(project=str(self.project)), dict(dry_run=True), self.home)
        self.assertEqual(error.exception.code, 'lock.limit')
        self.assertFalse(self.target.exists())
        with patch.object(r, 'MODEL_BYTES', 9), self.assertRaises(c.MaskError) as error:
            r.parse('{"ü":"ß"}', 'selection')
        self.assertEqual(error.exception.code, 'selection.limit')
        original = r.resolve_candidate
        declaration = (self.project / '.mask.json').read_bytes()
        def replace_root(*args, **kwargs):
            candidate = original(*args, **kwargs)
            self.project.rename(self.base / 'retained-project')
            self.project.mkdir()
            (self.project / '.mask.json').write_bytes(declaration)
            return candidate
        with patch.object(r, 'resolve_candidate', side_effect=replace_root), self.assertRaises(c.MaskError) as error:
            r.dispatch(argparse.Namespace(project=str(self.project)), dict(dry_run=False), self.home)
        self.assertEqual(error.exception.code, 'plan.stale')
        self.assertFalse(self.target.exists())
        self.assertEqual((self.project / '.mask.json').read_bytes(), declaration)

    def test_frozen_index_missing_object_and_legacy_state_isolation(self):
        self.fetch()
        first = self.locked()['data']['lock']
        (self.source / 'mask-source.json').write_text(json.dumps(dict(schema_version=1, packages={'alpha': 'moved/alpha', 'beta': 'skills/beta'})))
        moved = self.source / 'moved'
        moved.mkdir()
        (self.source / 'skills/alpha').rename(moved / 'alpha')
        self.commit()
        self.fetch()
        self.assertEqual(self.locked()['data']['lock'], first)
        refreshed = self.locked('--refresh', '--skill', 'legacy/alpha')['data']['lock']
        self.assertEqual(refreshed['packages'][0]['path'], 'moved/alpha')
        bad = copy.deepcopy(refreshed)
        bad['packages'][0]['commit'] = '0' * 40
        self.target.write_text(json.dumps(bad))
        self.assertEqual(self.locked(code=4)['error']['code'], 'lock.resolution_required')
        self.target.write_text(json.dumps(refreshed))
        self.declare(['beta'])
        self.call('project', 'register')
        state = c.read_json(self.home / 'state.json')
        record = state['projects'][str(self.project)]
        record['last_manifest'] = self.declaration
        record['last_manifest_digest'] = c.digest(self.declaration)
        with self.assertRaises(c.MaskError):
            c.state(state)
