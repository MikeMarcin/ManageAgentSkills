import json
import unittest

import mask_core as c
import mask_resolve as r
import mask_selection as selection
from tests.support import Fixture


def contribution(origin, *, source='vendor', repository='https://example.invalid/skills', agents='all', commit='a' * 40, payload='1' * 64, when=None):
    binding = dict(source=source, id='alpha', agents=agents)
    if when:
        binding['when'] = when
    declaration = r.selection(dict(schema_version=2, sources={source: dict(repository=repository, ref='refs/heads/main')}, skills=[binding]))
    row = dict(source=source, id='alpha', repository=repository, path='skills/alpha', commit=commit,
               git_object_format='sha1', payload_digest='sha256:' + payload, metadata_digest=c.digest(b'null'), selector=dict(ref='refs/heads/main'))
    locked = r.lock(dict(schema_version=1, resolver='mask-lock-v1', selection_digest=r.selection_digest(declaration), packages=[row]), declaration)
    return dict(origin=origin, declaration=declaration, lock=locked)


def evaluate(rows, metadata=None):
    return selection.evaluate(rows, metadata if metadata is not None else {'vendor/alpha': None, 'other/alpha': None},
                              facts=dict(platform='linux', architecture='x86_64'), enabled_agents=['claude', 'codex'],
                              scope='project', root='/fixture', identity=dict(device=1, inode=2))


class ContributionTests(unittest.TestCase):
    def test_identical_artifact_unions_positive_edges_and_exact_origins(self):
        first = contribution('profile-one', agents=['codex'], commit='b' * 40)
        second = contribution('local', agents=['claude'], commit='a' * 40)
        third = contribution('profile-two', agents=['codex'], commit='c' * 40)
        result = evaluate([first, second, third])
        self.assertFalse(result['blocked'])
        self.assertEqual(result, evaluate([third, second, first]))
        self.assertEqual({row['agent'] for row in result['deployable']}, {'claude', 'codex'})
        codex = next(row for row in result['deployable'] if row['agent'] == 'codex')
        self.assertEqual(codex['origins'], ['profile-one', 'profile-two'])
        self.assertEqual({row['resolution']['commit'] for row in codex['resolutions']}, {'b' * 40, 'c' * 40})
        self.assertTrue(all(row['resolution']['commit'] == 'a' * 40 for row in result['deployable']))
        self.assertEqual({entry['resolution']['commit'] for row in result['outcomes'] for entry in row['resolutions']}, {'a' * 40, 'b' * 40, 'c' * 40})

    def test_content_metadata_provenance_or_authority_conflicts_never_choose_last(self):
        first = contribution('local')
        for field, value in [('payload_digest', 'sha256:' + '2' * 64), ('metadata_digest', 'sha256:' + '3' * 64), ('provenance_digest', 'sha256:' + '4' * 64), ('repository', 'https://example.invalid/other')]:
            second = contribution('profile')
            second['lock']['packages'][0][field] = value
            if field == 'repository':
                second['declaration']['sources']['vendor']['repository'] = value
                second['lock']['selection_digest'] = r.selection_digest(second['declaration'])
            with self.subTest(field=field):
                result = evaluate([first, second])
                self.assertTrue(result['blocked'])
                self.assertEqual(result, evaluate([second, first]))
                self.assertEqual(result['deployable'], [])
                self.assertEqual(result['conflicts'][0]['kind'], 'artifact_authority')
                self.assertEqual({row['origin'] for row in result['conflicts'][0]['resolutions']}, {'local', 'profile'})

    def test_inapplicable_different_artifact_keeps_attribution_without_metadata(self):
        unused = contribution('other-device', payload='2' * 64, when=dict(platforms=['windows']))
        result = evaluate([unused, contribution('local', agents=['codex'])], {'sha256:' + '1' * 64: None})
        self.assertFalse(result['blocked'])
        unused_row = next(row for row in result['outcomes'] if row['status'] == 'not_applicable')
        self.assertEqual(unused_row['origins'], ['other-device'])
        self.assertEqual(unused_row['resolutions'][0]['resolution']['payload_digest'], 'sha256:' + '2' * 64)
        self.assertEqual([row['agent'] for row in result['deployable']], ['codex'])

    def test_names_conflict_only_on_shared_agent_and_report_both_coordinates(self):
        first = contribution('local', agents=['codex'])
        second = contribution('profile', source='other', agents=['claude'])
        self.assertFalse(evaluate([first, second])['blocked'])
        second['declaration']['skills'][0]['agents'] = ['codex']
        second['lock']['selection_digest'] = r.selection_digest(second['declaration'])
        result = evaluate([first, second])
        self.assertTrue(result['blocked'])
        conflict = result['conflicts'][0]
        self.assertEqual(conflict['relative'], '.agents/skills/alpha')
        self.assertEqual({row['coordinate'] for row in conflict['candidates']}, {'vendor/alpha', 'other/alpha'})
        self.assertEqual({origin for row in conflict['candidates'] for origin in row['origins']}, {'local', 'profile'})


class PublicConflictTests(Fixture):
    def setUp(self):
        super().setUp()
        self.init()
        self.call('source', 'migrate')
        second = self.base / 'second source'
        self.git(self.base, 'clone', '--no-hardlinks', str(self.source), str(second))
        self.call('tap', 'add', 'other', str(second))
        self.call('source', 'fetch', 'legacy')
        self.call('source', 'fetch', 'other')
        self.declaration = dict(schema_version=2,
                                sources={'legacy': dict(repository=self.source.as_uri(), ref='refs/heads/main'),
                                         'other': dict(repository=second.as_uri(), ref='refs/heads/main')},
                                skills=[dict(source='legacy', id='alpha', agents=['codex']),
                                        dict(source='other', id='alpha', agents=['claude'])])
        (self.project / '.mask.json').write_text(json.dumps(self.declaration))
        self.call('lock')

    def test_public_disjoint_agents_and_collision_preserve_controls_and_content(self):
        before = self.snapshot()
        preview = self.call('project', 'register', '--apply', '--dry-run')
        self.assertEqual(before, self.snapshot())
        self.call('project', 'register', '--apply', '--expect-plan-hash', preview['data']['plan_hash'])
        codex = self.project / '.agents/skills/alpha'
        claude = self.project / '.claude/skills/alpha'
        self.assertTrue(codex.is_symlink() and claude.is_symlink())
        before = self.snapshot()
        result = self.call('project', 'set-agents', 'other/alpha', 'codex', '--apply', code=4)
        self.assertEqual(result['error']['code'], 'target.collision')
        candidates = result['error']['details']['conflicts'][0]['candidates']
        self.assertEqual({row['coordinate'] for row in candidates}, {'legacy/alpha', 'other/alpha'})
        self.assertTrue(all(row['resolution']['payload_digest'].startswith('sha256:') for row in candidates))
        self.assertEqual(before, self.snapshot())
        self.assertFalse(self.call('apply')['changed'])

    def test_public_scope_shadowing_warns_without_precedence_or_suppression(self):
        self.call('project', 'register', '--apply')
        personal = self.base / 'personal'
        personal.mkdir()
        (self.home / 'user.json').write_bytes((self.project / '.mask.json').read_bytes())
        (self.home / 'user.lock.json').write_bytes((self.project / '.mask.lock.json').read_bytes())
        result = self.call('user', 'register', '--user-home', personal, '--apply')
        self.assertEqual(len(result['data']['shadowing']), 2)
        before = self.snapshot()
        result = self.call('plan', '--all')
        self.assertEqual(before, self.snapshot())
        self.assertEqual(len(result['data']['shadowing']), 2)
        for row in result['data']['shadowing']:
            self.assertEqual(row['host_precedence'], 'not_assumed')
            self.assertEqual(row['user']['status'], 'observed')
            self.assertEqual(row['project']['status'], 'observed')
            self.assertIsNotNone(row['user']['coordinate'])
            self.assertIsNotNone(row['project']['payload_digest'])
        self.assertIn('target.scope_shadowing', {row['code'] for row in result['warnings']})
        self.assertEqual(len(self.call('project', 'show')['data']['shadowing']), 2)
        self.assertTrue((personal / '.agents/skills/alpha').is_symlink())
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())
