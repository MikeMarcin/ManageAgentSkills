"""Tap-first inventory and where-used over pinned records (MASK-0102; RFC-MASK-0011-AC01, RFC-MASK-0021).

Every case drives the public CLI as a subprocess on a machine bootstrapped from local bare
upstreams approved as ``file`` taps, and every observation proves that the whole fixture
base, MASK_HOME included, is byte-identical afterwards.
"""
import json
import os
from types import SimpleNamespace

import mask_core as c
from tests.support import TAP, Fixture

ALPHA, BETA, VENDOR_ALPHA = TAP + '/alpha', TAP + '/beta', 'vendor/alpha'
ARTIFACT = ('payload_digest', 'metadata_digest', 'commit', 'selector')


def remove_link(path):
    """Remove one directory link without following it; Windows removes directory links with rmdir."""
    if os.name == 'nt' and path.is_dir():
        os.rmdir(path)
    else:
        path.unlink()


class InventoryTests(Fixture):
    # Development links need the fixture tap's approved authoring checkout; every other case starts from init().
    AUTHORING = {'test_dev_link_rows_follow_the_recorded_authoring_target'}

    def setUp(self):
        super().setUp()
        if self._testMethodName in self.AUTHORING:
            self.git(self.source, 'remote', 'add', 'origin', str(self.upstream))
            self.call('tap', 'add', TAP, self.upstream, '--checkout', self.source)
        else:
            self.init()
        self.install('alpha')

    def observe(self, *args, code=0, cwd=None):
        """One inventory or where-used call that must write nothing anywhere under the fixture base."""
        before = self.snapshot()
        result = self.call(*args, code=code, cwd=cwd)
        self.assertEqual(before, self.snapshot(), args)
        return result['data'] if code == 0 else result['error']

    def lock_row(self, identifier='alpha'):
        return next(row for row in c.read_json(self.project / '.mask.lock.json')['packages'] if row['id'] == identifier)

    def pick(self, rows, agent, skill=ALPHA, root=None):
        return next(row for row in rows if (row['agent'], row['skill'], row['root']) == (agent, skill, str(root or self.project)))

    def registered_copy(self, name):
        """A second consumer registered with the project's declaration and lock but without --apply, so nothing is linked."""
        other = self.base / name
        other.mkdir()
        for control in ('.mask.json', '.mask.lock.json'):
            (other / control).write_bytes((self.project / control).read_bytes())
        self.call('project', 'register', '--project', other)
        return other

    def vendor_tap(self):
        """A second approved tap whose alpha package has different bytes under the same ID."""
        source = self.base / 'Vendor'
        (source / 'skills/alpha').mkdir(parents=True)
        (source / 'skills/alpha/SKILL.md').write_text('---\nname: alpha\ndescription: Vendor skill\n---\n\nVendor instructions.\n')
        self.git(source, 'init', '-b', 'main')
        self.git(source, 'config', 'user.name', 'Fixture')
        self.git(source, 'config', 'user.email', 'fixture@example.invalid')
        self.git(source, 'add', 'skills')
        self.git(source, 'commit', '-m', 'vendor skills')
        upstream = self.base / 'upstream' / 'Vendor.git'
        self.git(self.base, 'init', '-q', '--bare', '-b', 'main', str(upstream))
        self.git(source, 'push', '-q', str(upstream), 'main')
        self.call('tap', 'add', 'vendor', upstream)
        return upstream

    def test_converged_rows_join_lock_artifact_source_and_compatibility(self):
        lock = self.lock_row()
        data = self.observe('inventory')
        self.assertEqual((data['source_mode'], data['network'], data['scope'], data['complete']), ('tap', 'none', 'selected_consumer', True))
        self.assertEqual(data['consumers'], [dict(root=str(self.project), scope='project', available=True, declaration_basis='live_declaration',
                                                  error=None, mode='pinned', reproducible=True)])
        self.assertEqual(sorted(row['agent'] for row in data['rows']), ['claude', 'codex'])
        for row in data['rows']:
            self.assertEqual(row['status'], 'managed_converged', row)
            self.assertEqual((row['skill'], row['name'], row['source'], row['package_path']),
                             (ALPHA, 'alpha', dict(alias=TAP, repository=self.upstream.as_uri()), lock['path']))
            self.assertEqual(row['artifact'], {field: lock[field] for field in ARTIFACT})
            self.assertEqual((row['recorded_source_revision'], row['content_mode'], row['declared'], row['origin'], row['owned']),
                             (None, 'pinned', True, 'local_declaration', True))
            self.assertEqual((row['compatibility'], row['host_load'], row['error'], row['actual']['type']), ('selected', 'not_verified', None, 'symlink'))
        self.assertFalse(any('legacy' in item.lower() or 'unpinned' in item.lower() for item in data['limitations']))
        self.assertNotIn('pinned_unsupported', json.dumps(data))

    def test_hand_retargeted_removed_link_and_missing_store_payload_drift(self):
        codex = self.project / '.agents/skills/alpha'
        elsewhere = self.base / 'elsewhere'
        elsewhere.mkdir()
        remove_link(codex)
        os.symlink(elsewhere, codex, target_is_directory=True)
        rows = self.observe('inventory')['rows']
        retargeted = self.pick(rows, 'codex')
        self.assertEqual((retargeted['status'], retargeted['owned'], retargeted['actual']), ('managed_drifted', True, dict(type='symlink', link_text=os.readlink(codex))))
        self.assertEqual(self.pick(rows, 'claude')['status'], 'managed_converged')
        remove_link(codex)
        removed = self.pick(self.observe('inventory')['rows'], 'codex')
        self.assertEqual((removed['status'], removed['actual']), ('managed_drifted', dict(type='missing', link_text=None)))
        (self.home / 'store').rename(self.home / 'store moved')
        claude = self.pick(self.observe('inventory')['rows'], 'claude')
        self.assertEqual((claude['status'], claude['actual']['type']), ('managed_drifted', 'symlink'))

    def test_registered_declaration_without_links_and_shallow_unmanaged_neighbors(self):
        other = self.registered_copy('registered only')
        data = self.observe('inventory', '--project', other)
        self.assertEqual(sorted((row['agent'], row['status'], row['owned'], row['actual']['type']) for row in data['rows']),
                         [('claude', 'declared_not_deployed', False, 'missing'), ('codex', 'declared_not_deployed', False, 'missing')])
        skills = other / '.agents/skills'
        skills.mkdir(parents=True)
        external = self.base / 'external'
        external.mkdir()
        (external / 'private').write_text('must not read')
        os.symlink(external, skills / 'neighbor', target_is_directory=True)
        (other / '.claude/skills/alpha').mkdir(parents=True)
        (other / '.claude/skills/alpha/mine').write_text('preserve')
        data = self.observe('inventory', '--project', other, '--include-unmanaged')
        self.assertEqual(len(data['rows']), 3)
        neighbor = next(row for row in data['rows'] if row['name'] == 'neighbor')
        self.assertEqual((neighbor['status'], neighbor['skill'], neighbor['source'], neighbor['artifact'], neighbor['owned'], neighbor['origin'], neighbor['content_mode'], neighbor['agent']),
                         ('unmanaged_present', None, None, None, False, 'unmanaged', 'unknown', 'codex'))
        occupied = self.pick(data['rows'], 'claude', root=other)
        self.assertEqual((occupied['status'], occupied['declared'], occupied['owned'], occupied['actual']['type']), ('unmanaged_present', True, False, 'directory'))
        self.assertEqual(self.pick(data['rows'], 'codex', root=other)['status'], 'declared_not_deployed')
        self.assertEqual((data['work']['directories_enumerated'], data['work']['payload_files_read']), (2, 0))
        self.assertNotIn('neighbor', {row['name'] for row in self.observe('inventory', '--project', other)['rows']})

    def test_linked_discovery_parent_is_blocked_and_never_traversed(self):
        other = self.registered_copy('linked parent')
        outside = self.base / 'outside'
        (outside / 'skills/hidden').mkdir(parents=True)
        os.symlink(outside, other / '.agents', target_is_directory=True)
        data = self.observe('inventory', '--project', other, '--include-unmanaged')
        self.assertFalse(data['complete'])
        self.assertEqual([item['code'] for item in data['consumers'][0]['discovery_errors']], ['target.parent_link'])
        codex = self.pick(data['rows'], 'codex', root=other)
        self.assertEqual((codex['status'], codex['error']['code']), ('blocked', 'target.parent_link'))
        self.assertNotIn('hidden', {row['name'] for row in data['rows']})

    def test_unavailable_consumer_reports_its_cached_selection_as_diagnostic(self):
        lock = self.lock_row()
        self.project.rename(self.base / 'renamed away')
        data = self.observe('inventory', '--project', self.project, cwd=self.base)
        self.assertFalse(data['complete'])
        consumer = data['consumers'][0]
        self.assertEqual((consumer['available'], consumer['declaration_basis'], consumer['error']['code']), (False, 'cached_pinned_selection', 'project.unavailable'))
        self.assertEqual(len(data['rows']), 2)
        for row in data['rows']:
            self.assertEqual((row['status'], row['declaration_basis'], row['skill'], row['artifact']['payload_digest'], row['actual']['type'], row['compatibility']),
                             ('unavailable_consumer', 'cached_pinned_selection', ALPHA, lock['payload_digest'], 'unknown', 'unspecified'))
        self.assertEqual((data['work']['declarations_read'], data['work']['locks_read'], data['work']['leaves_inspected']), (0, 0, 0))

    def test_dev_link_rows_follow_the_recorded_authoring_target(self):
        self.call('source', 'dev-link', ALPHA, '--project', self.project, '--authoring-root', self.source)
        data = self.observe('inventory')
        self.assertEqual((data['consumers'][0]['mode'], data['consumers'][0]['reproducible'], data['complete']), ('dev-link', False, True))
        self.assertEqual(len(data['rows']), 2)
        for row in data['rows']:
            self.assertEqual((row['content_mode'], row['status'], row['compatibility'], row['artifact']['payload_digest']),
                             ('dev_link', 'managed_converged', 'unspecified', self.lock_row()['payload_digest']))
        (self.source / 'skills/alpha').rename(self.source / 'skills/moved')
        self.assertEqual({row['status'] for row in self.observe('inventory')['rows']}, {'managed_drifted'})

    def test_same_id_from_two_taps_and_both_scopes_stay_distinct(self):
        vendor = self.vendor_tap()
        self.call('project', 'set-agents', ALPHA, 'codex', '--apply')
        self.install(VENDOR_ALPHA, agents=('claude',))
        self.install(VENDOR_ALPHA, user=True)
        data = self.observe('inventory', '--all')
        self.assertEqual((data['scope'], data['complete']), ('registered_local_consumers', True))
        self.assertEqual(sorted((item['scope'], item['root']) for item in data['consumers']), [('project', str(self.project)), ('user', str(self.personal))])
        self.assertEqual(sorted((row['scope'], row['agent'], row['skill'], row['source']['repository'], row['status']) for row in data['rows']), [
            ('project', 'claude', VENDOR_ALPHA, vendor.as_uri(), 'managed_converged'),
            ('project', 'codex', ALPHA, self.upstream.as_uri(), 'managed_converged'),
            ('user', 'claude', VENDOR_ALPHA, vendor.as_uri(), 'managed_converged'),
            ('user', 'codex', VENDOR_ALPHA, vendor.as_uri(), 'managed_converged')])
        self.assertNotEqual(self.pick(data['rows'], 'codex')['artifact']['payload_digest'], self.pick(data['rows'], 'claude', VENDOR_ALPHA)['artifact']['payload_digest'])
        where = self.observe('skill', 'where-used', VENDOR_ALPHA)
        self.assertEqual(sorted((row['scope'], row['agent']) for row in where['rows']), [('project', 'claude'), ('user', 'claude'), ('user', 'codex')])
        self.assertEqual([(row['scope'], row['agent']) for row in self.observe('skill', 'where-used', ALPHA)['rows']], [('project', 'codex')])
        narrow = self.observe('skill', 'where-used', VENDOR_ALPHA, '--scope', 'user', '--agent', 'codex')
        self.assertEqual([(row['root'], row['agent']) for row in narrow['rows']], [(str(self.personal), 'codex')])
        self.assertEqual(([item['scope'] for item in narrow['consumers']], narrow['work']['leaves_inspected']), (['user'], 1))
        self.assertEqual(self.observe('skill', 'where-used', 'unknown/alpha', code=4)['code'], 'source.unknown')
        for operands in (('alpha',), (ALPHA, '--agent', 'cursor'), (ALPHA, '--scope', 'fleet')):
            self.assertEqual(self.observe('skill', 'where-used', *operands, code=2)['code'], 'invocation.invalid', operands)

    def test_pagination_bounded_work_and_metadata_exclusion(self):
        self.call('project', 'set-targets', '--inherit', '--apply')
        (self.source / 'skills/beta/mask-skill.json').write_text(json.dumps(dict(schema_version=1, agents=['codex'])))
        self.publish('beta advertises codex only')
        self.call('source', 'fetch', TAP)
        self.install('beta')
        declaration, lock = ((self.project / name).read_bytes() for name in ('.mask.json', '.mask.lock.json'))
        full = self.observe('inventory')
        self.assertEqual(full['work'], dict(declarations_read=1, declaration_bytes_read=2 * len(declaration), locks_read=1, lock_bytes_read=2 * len(lock),
                                            payload_files_read=1, directories_enumerated=0, leaves_inspected=4))
        excluded, selected = self.pick(full['rows'], 'claude', BETA), self.pick(full['rows'], 'codex', BETA)
        self.assertEqual((excluded['status'], excluded['compatibility'], excluded['owned']), ('inapplicable', 'excluded_by_metadata', False))
        self.assertEqual((selected['status'], selected['compatibility']), ('managed_converged', 'selected'))
        page = self.observe('inventory', '--limit', '1')
        self.assertEqual((page['total_rows'], page['next_offset'], page['rows'], page['work']), (4, 1, full['rows'][:1], full['work']))
        last = self.observe('inventory', '--offset', '3', '--limit', '2')
        self.assertEqual((last['rows'], last['next_offset']), (full['rows'][3:], None))
        narrow = self.observe('skill', 'where-used', ALPHA, '--agent', 'codex', '--scope', 'project')
        self.assertEqual((len(narrow['rows']), narrow['work']['leaves_inspected'], narrow['work']['declarations_read'], narrow['work']['payload_files_read']), (1, 1, 1, 0))
        self.assertEqual(self.observe('inventory', '--limit', '0', code=2)['code'], 'invocation.invalid')
