import json

import mask_core as c
import mask_provenance as provenance
from tests.test_imports import ImportFixture


class ProvenanceTests(ImportFixture):
    def test_direct_git_verification_and_explicit_adaptation_history(self):
        self.import_call()
        before = self.snapshot()
        observed = self.call('skill', 'provenance', 'legacy/gamma')['data']
        self.assertEqual(observed['verification'], 'verified_git_objects')
        self.assertEqual(observed['record_trust'], 'local_assertions')
        self.assertFalse(observed['unrecorded_adaptations'])
        self.assertEqual(before, self.snapshot())
        (self.target / 'raw.bin').write_bytes(b'adapted locally')
        observed = self.call('skill', 'provenance', 'legacy/gamma')['data']
        self.assertTrue(observed['unrecorded_adaptations'])
        before = self.snapshot()
        preview = self.call('skill', 'record-adaptation', 'legacy/gamma', '--note', 'Adapted binary fixture', '--dry-run')
        self.assertEqual(before, self.snapshot())
        result = self.call('skill', 'record-adaptation', 'legacy/gamma', '--note', 'Adapted binary fixture', '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertEqual(result['data']['changed_paths'], [str(self.target / provenance.RECORD)])
        observed = self.call('skill', 'provenance', 'legacy/gamma')['data']
        self.assertFalse(observed['unrecorded_adaptations'])
        self.assertEqual(observed['record']['adaptations'][0]['note'], 'Adapted binary fixture')
        self.assertEqual(observed['record']['upstream']['commit'], self.commit)
        self.assertFalse(self.call('skill', 'record-adaptation', 'legacy/gamma', '--note', 'No change')['changed'])

    def test_missing_history_and_missing_cache_never_invent_verified_origin(self):
        absent = self.call('skill', 'provenance', 'legacy/alpha')['data']
        self.assertEqual(absent['history'], 'absent')
        self.assertIsNone(absent['upstream'])
        self.assertEqual(self.call('skill', 'record-adaptation', 'legacy/alpha', '--note', 'Unknown history', code=4)['error']['code'], 'provenance.absent')
        self.import_call()
        self.call('tap', 'remove', 'vendor')
        observed = self.call('skill', 'provenance', 'legacy/gamma')['data']
        self.assertEqual(observed['verification'], 'recorded_only')
        self.assertIsNone(observed['verified_git_facts'])

    def test_tampered_upstream_manifest_cannot_claim_verified_facts(self):
        self.import_call()
        path = self.target / provenance.RECORD
        record = json.loads(path.read_bytes())
        record['upstream']['files'][0]['sha256'] = '0' * 64
        record['upstream']['payload_digest'] = c.digest(record['upstream']['files'])
        name = record['upstream']['files'][0]['path']
        next(item for item in record['curated']['files'] if item['path'] == name)['sha256'] = '0' * 64
        record['curated']['content_digest'] = c.digest(record['curated']['files'])
        path.write_text(c.text_json(record))
        observed = self.call('skill', 'provenance', 'legacy/gamma')['data']
        self.assertEqual(observed['verification'], 'mismatch')
        self.assertIsNone(observed['verified_git_facts'])

    def test_stale_adaptation_refuses_and_linked_observation_never_follows(self):
        self.import_call()
        path = self.target / 'raw.bin'
        path.write_bytes(b'first edit')
        preview = self.call('skill', 'record-adaptation', 'legacy/gamma', '--note', 'First edit', '--dry-run')
        path.write_bytes(b'second edit')
        self.assertEqual(self.call('skill', 'record-adaptation', 'legacy/gamma', '--note', 'First edit', '--expect-plan-hash', preview['data']['plan_hash'], code=4)['error']['code'], 'plan.stale')
        record = json.loads((self.target / provenance.RECORD).read_bytes())
        self.assertEqual(record['adaptations'], [])
        unrelated = self.base / 'private-file'
        unrelated.write_bytes(b'do not read through link')
        path.unlink()
        path.symlink_to(unrelated)
        self.assertEqual(self.call('skill', 'provenance', 'legacy/gamma', code=4)['error']['code'], 'skill.entry_unsupported')
        self.assertEqual(unrelated.read_bytes(), b'do not read through link')

    def test_tap_queries_use_frozen_cache_and_treat_embedded_records_as_assertions(self):
        self.fetch()
        before = self.snapshot()
        absent = self.call('skill', 'provenance', 'vendor/gamma')['data']
        self.assertEqual(absent['observation'], 'frozen_cache')
        self.assertEqual(absent['history'], 'absent')
        self.assertEqual(before, self.snapshot())
        self.import_call()
        self.git(self.source, 'add', 'skills/gamma')
        self.git(self.source, 'commit', '-m', 'fixture curated import')
        self.call('tap', 'add', 'published', self.source)
        self.call('source', 'fetch', 'published')
        published = self.call('skill', 'provenance', 'published/gamma')['data']
        self.assertEqual(published['record_trust'], 'publisher_assertions')
        self.assertEqual(published['verification'], 'verified_git_objects')
        self.assertEqual(published['observation'], 'frozen_cache')
        self.call('source', 'fetch', 'legacy')
        self.git(self.source, 'checkout', '-b', 'other')
        alternate = self.call('skill', 'provenance', 'legacy/gamma')['data']
        self.assertEqual(alternate['observation'], 'frozen_cache')
        self.assertEqual(self.call('skill', 'record-adaptation', 'legacy/gamma', '--note', 'Wrong branch', code=4)['error']['code'], 'source.detached')

    def test_root_skill_provenance_works_in_cached_and_authoring_scopes(self):
        (self.author / 'SKILL.md').write_text('---\nname: rootitem\ndescription: Root fixture\n---\n')
        (self.author / 'mask-source.json').write_text(json.dumps(dict(schema_version=1, packages={'rootitem': '.'})))
        self.advance()
        self.fetch()
        cached = self.call('skill', 'provenance', 'vendor/rootitem')['data']
        self.assertEqual(cached['observation'], 'frozen_cache')
        self.assertEqual(cached['observed_package']['path'], '.')
        self.call('tap', 'add', 'root-authoring', self.remote, '--checkout', self.author, '--packages', '.')
        authored = self.call('skill', 'provenance', 'root-authoring/rootitem')['data']
        self.assertEqual(authored['observation'], 'authoring')
        self.assertEqual(authored['history'], 'absent')
        result = self.call('skill', 'import', 'vendor', '--mode', 'copy', '--into', 'root-authoring', code=4)
        self.assertEqual(result['error']['code'], 'import.collision')
