from pathlib import Path
from unittest.mock import patch
import argparse

import mask
import mask_core as c
import mask_report
from tests.support import Fixture


class InventoryTests(Fixture):
    def setUp(self):
        super().setUp()
        self.init()
        self.declare()
        self.call('project', 'register', self.project)

    def test_desired_owned_drift_and_unpinned_truth(self):
        before = self.snapshot()
        rows = self.call('inventory')['data']['rows']
        self.assertEqual({row['status'] for row in rows}, {'declared_not_deployed'})
        self.assertEqual(before, self.snapshot())
        self.call('apply')
        rows = self.call('skill', 'where-used', 'legacy/alpha')['data']['rows']
        self.assertEqual({row['status'] for row in rows}, {'managed_converged'})
        self.assertTrue(all(row['artifact'] is None and row['host_load'] == 'not_verified' for row in rows))
        leaf = self.project / '.agents/skills/alpha'
        leaf.unlink()
        rows = self.call('inventory')['data']['rows']
        self.assertEqual(next(row for row in rows if row['agent'] == 'codex')['status'], 'managed_drifted')
        self.call('skill', 'where-used', 'other/alpha', code=4)
        self.call('skill', 'where-used', 'alpha', code=2)

    def test_scope_filters_pagination_and_unavailable_cache(self):
        personal = self.base / 'personal'
        personal.mkdir()
        self.call('user', 'init')
        self.call('user', 'require', 'alpha')
        self.call('user', 'register', '--user-home', personal, '--apply')
        rows = self.call('skill', 'where-used', 'legacy/alpha', '--agent', 'codex', '--scope', 'user')['data']['rows']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['root'], str(personal))
        page = self.call('inventory', '--all', '--limit', '1')['data']
        self.assertEqual(page['total_rows'], 4)
        self.assertEqual(page['next_offset'], 1)
        self.assertEqual(len(page['rows']), 1)
        self.project.rename(self.base / 'unavailable')
        data = self.call('inventory', '--project', self.project, cwd=self.base)['data']
        self.assertFalse(data['complete'])
        self.assertEqual({row['status'] for row in data['rows']}, {'unavailable_consumer'})
        self.assertTrue(all(row['declaration_basis'] == 'cached_declaration' for row in data['rows']))

    def test_unmanaged_is_shallow_observational_and_never_adopted(self):
        directory = self.project / '.agents/skills'
        directory.mkdir(parents=True)
        external = self.base / 'external'
        external.mkdir()
        (external / 'private').write_text('must not read')
        (directory / 'neighbor').symlink_to(external, target_is_directory=True)
        (directory / 'alpha').mkdir()
        before = self.snapshot()
        data = self.call('inventory', '--include-unmanaged')['data']
        self.assertEqual(before, self.snapshot())
        neighbors = [row for row in data['rows'] if row['name'] == 'neighbor']
        self.assertEqual(len(neighbors), 1)
        self.assertEqual(neighbors[0]['status'], 'unmanaged_present')
        self.assertIsNone(neighbors[0]['source'])
        self.assertFalse(neighbors[0]['owned'])
        self.assertEqual(data['work']['payload_files_read'], 0)
        self.assertEqual(data['work']['directories_enumerated'], 1)

    def test_narrow_query_never_reads_payloads_or_unrelated_leaves(self):
        self.call('project', 'require', 'beta', '--apply')
        args = argparse.Namespace(command='skill.where-used', id='legacy/alpha', scope='project', agent='codex')
        with patch.object(c, 'package', side_effect=AssertionError('payload read')), patch.object(c, 'git', side_effect=AssertionError('Git scan')):
            output = mask.result()
            mask_report.dispatch(args, output, self.home)
        self.assertEqual(output['data']['work']['leaves_inspected'], 1)
        self.assertEqual(output['data']['work']['declarations_read'], 1)
        self.assertEqual(output['data']['work']['payload_files_read'], 0)
        self.assertEqual(len(output['data']['rows']), 1)

    def test_changed_declaration_and_missing_target_are_not_converged(self):
        self.call('apply')
        self.declare([])
        rows = self.call('inventory')['data']['rows']
        self.assertTrue(all(row['status'] == 'managed_drifted' and not row['declared'] for row in rows))
        self.declare()
        (self.source / 'skills/alpha').rename(self.source / 'skills/missing')
        self.assertTrue(all(row['status'] == 'managed_drifted' for row in self.call('inventory')['data']['rows']))

    def test_linked_parent_is_reported_without_traversal(self):
        outside = self.base / 'outside'
        outside.mkdir()
        (self.project / '.agents').symlink_to(outside, target_is_directory=True)
        before = self.snapshot()
        data = self.call('inventory', '--include-unmanaged')['data']
        self.assertFalse(data['complete'])
        self.assertEqual(before, self.snapshot())
        self.assertEqual(next(row for row in data['rows'] if row['agent'] == 'codex')['status'], 'blocked')
