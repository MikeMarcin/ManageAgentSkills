"""Tap line-ending policy through the public CLI under a core.autocrlf=true Git configuration (MASK-0107).

Every test first points GIT_CONFIG_GLOBAL at a disposable file that sets core.autocrlf=true. The fixture's own Git
and every MASK subprocess read it, so the cases mean the same on Windows, macOS and Linux; the real global and system
configurations are never written. Commands run as subprocesses and are judged by exit code, JSON stdout, stderr and
their filesystem and Git effects. Only ``AutocrlfFidelity`` calls ``mask_provenance.autocrlf`` in process, to compare
it with the bytes real Git stores.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from mask_packages import PayloadFile
import mask_provenance as provenance
import mask_sources as sources
from tests.legacy_support import LegacyFixture, write_json
from tests.support import ENTRY, TAP, Fixture

ALPHA = TAP + '/alpha'
PACKAGE = 'skills/alpha'
SKILL = PACKAGE + '/SKILL.md'
POLICY = dict(default='exact', values=['exact', 'autocrlf'], opt_in='tap add --autocrlf')
EDITED = b'---\r\nname: alpha\r\ndescription: Fixture skill\r\n---\r\n\r\nEdited with CRLF line endings.\r\n'


def codes(items):
    return [item['code'] for item in items]


class AutocrlfGit:
    """Mixin: this test's Git, and every process it starts, reads a disposable global configuration with core.autocrlf=true."""

    def force_autocrlf(self):
        directory = tempfile.TemporaryDirectory(prefix='mask-autocrlf-')
        self.addCleanup(directory.cleanup)
        config = Path(directory.name) / 'gitconfig'
        config.write_text('[core]\n\tautocrlf = true\n', encoding='utf-8', newline='\n')
        environment = patch.dict(os.environ, GIT_CONFIG_GLOBAL=str(config))
        environment.start()
        self.addCleanup(environment.stop)
        effective = subprocess.run(['git', 'config', '--global', '--get', 'core.autocrlf'], capture_output=True, encoding='utf-8', check=True)
        self.assertEqual(effective.stdout.strip(), 'true')


class LineEndingFixture(AutocrlfGit, Fixture):
    """The tap-first fixture under core.autocrlf=true. The author checkout ``self.source`` holds LF files, as tests.support writes them."""

    def setUp(self):
        self.force_autocrlf()
        super().setUp()
        self.assertEqual(self.git(self.source, 'config', '--get', 'core.autocrlf'), 'true')
        self.assertNotIn(b'\r', (self.source / SKILL).read_bytes())

    def entry(self):
        return json.loads((self.home / 'config.json').read_text(encoding='utf-8'))['sources'][TAP]

    def locked_digest(self):
        return json.loads((self.project / '.mask.lock.json').read_text(encoding='utf-8'))['packages'][0]['payload_digest']

    def blob(self, root, spec):
        return subprocess.run(['git', '-C', str(root), 'cat-file', 'blob', spec], capture_output=True, check=True).stdout

    def converted_clone(self):
        """A clone of the tap upstream checked out under core.autocrlf=true: its working files are CRLF copies of LF blobs."""
        clone = self.base / 'converted clone'
        self.git(self.base, 'clone', '-q', str(self.upstream), str(clone))
        self.git(clone, 'config', 'user.name', 'Fixture')
        self.git(clone, 'config', 'user.email', 'fixture@example.invalid')
        self.assertEqual((clone / SKILL).read_bytes(), self.blob(clone, 'HEAD:' + SKILL).replace(b'\n', b'\r\n'))
        self.assertEqual(self.git(clone, 'status', '--porcelain'), '')
        return clone

    def git_facts(self, root):
        """What a publication or a development link could leave in a checkout's repository."""
        return dict(head=self.git(root, 'rev-parse', 'HEAD'), refs=self.git(root, 'for-each-ref', '--format=%(objectname) %(refname)'),
                    index=self.git(root, 'ls-files', '--stage'), worktrees=self.git(root, 'worktree', 'list', '--porcelain'),
                    objects=self.git(root, 'count-objects', '-v'))

    def mask_publish(self, *extra, code=0):
        return self.call('source', 'publish', TAP, '--paths', PACKAGE, *extra, code=code)

    def dev_link(self, root, *extra, code=0):
        return self.call('source', 'dev-link', ALPHA, '--project', self.project, '--authoring-root', root, *extra, code=code)

    def mode(self):
        return self.call('project', 'show')['data']['mode']


class ExactTap(LineEndingFixture):
    """A1, A2 and the MASK-0099 defect: a tap added without the opt-in keeps exact bytes."""

    def test_unchanged_lf_package_publishes_no_change_and_an_edit_publishes_exact_bytes(self):
        added = self.authoring_init()
        self.assertEqual((added['data']['line_endings'], self.entry()['line_endings']), ('exact', 'exact'))
        # Git would convert in this checkout, so the exact tap warns even though these files are LF.
        self.assertIn('source.line_endings_conversion', codes(added['warnings']))
        head = self.git(self.source, 'rev-parse', 'HEAD')
        for extra in ((), ('--commit',)):
            with self.subTest(extra=extra):
                unchanged = self.mask_publish(*extra)
                self.assertEqual((unchanged['would_change'], unchanged['changed'], unchanged['data']['created_commit'], unchanged['data']['line_endings']),
                                 (False, False, None, 'exact'))
        self.assertEqual(self.git(self.source, 'for-each-ref', 'refs/mask'), '')
        notes = b'new file\r\nwith CRLF\r\n'
        (self.source / SKILL).write_bytes(EDITED)
        (self.source / PACKAGE / 'notes.txt').write_bytes(notes)
        preview = self.mask_publish('--commit', '--dry-run')
        self.assertTrue(preview['would_change'])
        result = self.mask_publish('--commit', '--expect-plan-hash', preview['data']['plan_hash'])
        commit = result['data']['created_commit']
        self.assertEqual((result['data']['line_endings'], result['data']['created_ref'], self.git(self.source, 'rev-parse', 'HEAD')),
                         ('exact', 'refs/mask/published/' + commit, head))
        self.assertEqual(self.blob(self.source, commit + ':' + SKILL), EDITED)
        self.assertEqual(self.blob(self.source, commit + ':' + PACKAGE + '/notes.txt'), notes)

    def test_exact_tap_over_a_converted_clone_warns_then_refuses_before_any_effect(self):
        clone = self.converted_clone()
        added = self.call('tap', 'add', TAP, self.upstream, '--checkout', clone)
        warnings = [item for item in added['warnings'] if item['code'] == 'source.line_endings_conversion']
        self.assertEqual([(item['path'], item['autocrlf']) for item in warnings], [(str(clone), 'true')])
        self.assertEqual((added['data']['line_endings'], self.entry()['line_endings']), ('exact', 'exact'))
        self.install('alpha')
        before = (self.snapshot(), self.git_facts(clone))
        details = dict(source=TAP, root=str(clone), paths=[SKILL], autocrlf='true')
        attempts = (('source', 'publish', TAP, '--paths', PACKAGE), ('source', 'publish', TAP, '--paths', PACKAGE, '--commit'),
                    ('source', 'dev-link', ALPHA, '--project', self.project, '--authoring-root', clone, '--dry-run'),
                    ('source', 'dev-link', ALPHA, '--project', self.project, '--authoring-root', clone))
        for index, args in enumerate(attempts):
            with self.subTest(attempt=index):
                error = self.call(*args, code=4)['error']
                self.assertEqual((error['code'], error['details']), ('source.line_endings_converted', details))
                self.assertEqual((self.snapshot(), self.git_facts(clone)), before)
        self.assertEqual((self.git(clone, 'for-each-ref', 'refs/mask'), self.mode()), ('', 'pinned'))
        # The remediation the refusal names: stop converting in this checkout, delete the unedited file and check it out again.
        # (Git leaves a stat-clean converted file in place, so it must be deleted first; other converted files stay as they were.)
        self.git(clone, 'config', 'core.autocrlf', 'false')
        (clone / SKILL).unlink()
        self.git(clone, 'checkout', '--', SKILL)
        self.assertEqual(((clone / SKILL).read_bytes(), self.git(clone, 'status', '--porcelain', '--', SKILL)), (self.blob(clone, 'HEAD:' + SKILL), ''))
        self.assertFalse(self.mask_publish()['would_change'])
        self.assertEqual(self.dev_link(clone, '--dry-run')['data']['development'], [dict(coordinate=ALPHA, root=str(clone), payload_digest=self.locked_digest())])

    def test_dev_link_of_an_unchanged_package_observes_the_locked_payload_digest(self):
        self.authoring_init()
        self.install('alpha')
        planned = [dict(coordinate=ALPHA, root=str(self.source), payload_digest=self.locked_digest())]
        preview = self.dev_link(self.source, '--dry-run')
        self.assertEqual((preview['data']['line_endings'], preview['data']['development']), ('exact', planned))
        applied = self.dev_link(self.source, '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertEqual((applied['data']['development'], self.mode()), (planned, 'dev-link'))
        self.call('source', 'dev-link', ALPHA, '--project', self.project, '--to-pinned')
        self.assertEqual(self.mode(), 'pinned')


class AutocrlfTap(LineEndingFixture):
    """A2 and A3: a tap registered with --autocrlf applies Git's core.autocrlf=true check-in conversion and discloses it."""

    def setUp(self):
        super().setUp()
        self.clone = self.converted_clone()
        self.added = self.call('tap', 'add', TAP, self.upstream, '--checkout', self.clone, '--autocrlf')
        self.install('alpha')

    def test_the_opt_in_is_recorded_and_disclosed_without_a_conversion_warning(self):
        self.assertEqual(self.added['data']['line_endings'], 'autocrlf')
        self.assertNotIn('source.line_endings_conversion', codes(self.added['warnings']))
        self.assertEqual(self.entry()['line_endings'], 'autocrlf')
        shown = self.call('source', 'show', TAP)['data']
        self.assertEqual((shown['line_endings'], shown['binding']['line_endings']), ('autocrlf', 'autocrlf'))

    def test_a_converted_clone_publishes_no_change_and_dev_links_the_locked_digest(self):
        unchanged = self.mask_publish()
        self.assertEqual((unchanged['would_change'], unchanged['data']['line_endings']), (False, 'autocrlf'))
        planned = [dict(coordinate=ALPHA, root=str(self.clone), payload_digest=self.locked_digest())]
        preview = self.dev_link(self.clone, '--dry-run')
        self.assertEqual((preview['data']['line_endings'], preview['data']['development']), ('autocrlf', planned))
        self.dev_link(self.clone, '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertEqual(self.mode(), 'dev-link')
        self.call('source', 'dev-link', ALPHA, '--project', self.project, '--to-pinned')
        self.assertEqual(self.mode(), 'pinned')

    def test_a_crlf_edit_publishes_the_blobs_git_itself_stores(self):
        files = {SKILL: EDITED, PACKAGE + '/notes.txt': b'new file\r\nwith CRLF\r\n', PACKAGE + '/data.bin': b'binary\r\n\x00payload\r\n'}
        for relative, data in files.items():
            (self.clone / relative).write_bytes(data)
        head = self.git(self.clone, 'rev-parse', 'HEAD')
        preview = self.mask_publish('--commit', '--dry-run')
        self.assertTrue(preview['would_change'])
        result = self.mask_publish('--commit', '--expect-plan-hash', preview['data']['plan_hash'])
        commit = result['data']['created_commit']
        self.assertEqual((result['data']['line_endings'], self.git(self.clone, 'rev-parse', 'HEAD')), ('autocrlf', head))
        for relative in files:
            with self.subTest(path=relative):
                oracle = self.git(self.clone, '-c', 'core.autocrlf=true', 'hash-object', '--path', relative, relative)
                self.assertEqual(self.git(self.clone, 'rev-parse', commit + ':' + relative), oracle)
        # Git converted the text files and kept the binary file's bytes.
        self.assertEqual(self.blob(self.clone, commit + ':' + SKILL), EDITED.replace(b'\r\n', b'\n'))
        self.assertEqual(self.blob(self.clone, commit + ':' + PACKAGE + '/data.bin'), files[PACKAGE + '/data.bin'])

    def test_committed_line_ending_attributes_refuse_unsupported_before_any_effect(self):
        (self.clone / '.gitattributes').write_bytes(b'*.md text\n')
        self.git(self.clone, 'add', '.gitattributes')
        self.git(self.clone, 'commit', '-q', '-m', 'text attribute')
        before = (self.snapshot(), self.git_facts(self.clone))
        details = dict(attributes=[dict(path=SKILL, attribute='text', value='set')])
        attempts = (('source', 'publish', TAP, '--paths', PACKAGE), ('source', 'publish', TAP, '--paths', PACKAGE, '--commit'),
                    ('source', 'dev-link', ALPHA, '--project', self.project, '--authoring-root', self.clone, '--dry-run'))
        for index, args in enumerate(attempts):
            with self.subTest(attempt=index):
                error = self.call(*args, code=4)['error']
                self.assertEqual((error['code'], error['details']), ('source.line_endings_unsupported', details))
                self.assertEqual((self.snapshot(), self.git_facts(self.clone)), before)


class EntryWrittenBeforeThePolicy(LineEndingFixture):
    """A4: a v3 catalog entry without line_endings keeps exact bytes, keeps working and is kept byte-for-byte."""

    def test_an_entry_without_the_field_keeps_exact_bytes_and_every_command(self):
        self.authoring_init()
        config = self.home / 'config.json'
        value = json.loads(config.read_text(encoding='utf-8'))
        self.assertEqual(value['sources'][TAP].pop('line_endings'), 'exact')
        write_json(config, value)
        written = config.read_bytes()
        shown = self.call('source', 'show', TAP)['data']
        self.assertEqual((shown['line_endings'], 'line_endings' in shown['binding']), ('exact', False))
        self.install('alpha')
        (self.source / SKILL).write_bytes((self.source / SKILL).read_bytes() + b'\nA later LF revision.\n')
        head = self.publish('later revision')
        self.call('source', 'fetch', TAP)
        self.assertTrue(self.call('update', '--project', self.project)['changed'])
        self.assertEqual(json.loads((self.project / '.mask.lock.json').read_text(encoding='utf-8'))['packages'][0]['commit'], head)
        unchanged = self.mask_publish()
        self.assertEqual((unchanged['would_change'], unchanged['data']['line_endings']), (False, 'exact'))
        planned = [dict(coordinate=ALPHA, root=str(self.source), payload_digest=self.locked_digest())]
        preview = self.dev_link(self.source, '--dry-run')
        self.assertEqual((preview['data']['line_endings'], preview['data']['development']), ('exact', planned))
        self.dev_link(self.source, '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertEqual(self.mode(), 'dev-link')
        self.call('source', 'dev-link', ALPHA, '--project', self.project, '--to-pinned')
        self.assertEqual(config.read_bytes(), written)
        again = self.call('tap', 'add', TAP, self.upstream, '--checkout', self.source)
        self.assertEqual((again['would_change'], again['changed'], again['data']['line_endings']), (False, False, 'exact'))
        self.assertEqual(config.read_bytes(), written)
        refused = self.call('tap', 'add', TAP, self.upstream, '--checkout', self.source, '--autocrlf', code=4)
        self.assertEqual(refused['error']['code'], 'source.alias_conflict')
        self.assertEqual(config.read_bytes(), written)


class MigrationWritesTheDefault(AutocrlfGit, LegacyFixture):
    """doctor --migrate writes line_endings exact on every tap: the new v1 tap and the kept, renamed and extra v2 taps."""

    def setUp(self):
        self.force_autocrlf()
        super().setUp()

    def policies(self, catalog):
        return {name: entry.get('line_endings') for name, entry in catalog.items()}

    def migrate(self, alias, names, *args):
        """The doctor report, the dry run and the written configuration all carry the exact default."""
        # The plain report takes no --alias, so it proposes the default alias; the dry run proposes the chosen one.
        self.assertEqual(self.machine('doctor')['data']['migration']['proposed_tap']['line_endings'], 'exact')
        preview = self.machine('doctor', '--migrate', *args, '--dry-run')['data']['migration']
        self.assertEqual((preview['proposed_tap']['alias'], preview['proposed_tap']['line_endings']), (alias, 'exact'))
        self.assertEqual(self.policies(preview['config_after']['sources']), dict.fromkeys(names, 'exact'))
        self.machine('doctor', '--migrate', *args)
        catalog = json.loads((self.roots.home / 'config.json').read_text(encoding='utf-8'))['sources']
        self.assertEqual(self.policies(catalog), dict.fromkeys(names, 'exact'))
        return catalog

    def without_policy(self, entry):
        return {key: value for key, value in entry.items() if key != 'line_endings'}

    def test_v1_machine_migrates_to_an_exact_tap(self):
        roots = self.legacy_machine(1)
        catalog = self.migrate('agentskills', ['agentskills'])
        self.assertEqual(catalog['agentskills'], sources.binding(roots.home, 'agentskills', str(roots.upstream), 'main', 'skills', str(roots.clone)))

    def test_v2_machine_keeps_its_legacy_and_extra_taps_with_the_exact_default(self):
        roots = self.legacy_machine(2)
        self.assertFalse(any('line_endings' in entry for entry in roots.config['sources'].values()))
        catalog = self.migrate('legacy', ['legacy', 'extra'])
        self.assertEqual({name: self.without_policy(entry) for name, entry in catalog.items()}, roots.config['sources'])

    def test_v2_machine_renames_its_legacy_tap_with_the_exact_default(self):
        roots = self.legacy_machine(2)
        catalog = self.migrate('other', ['other', 'extra'], '--alias', 'other')
        legacy = roots.config['sources']['legacy']
        self.assertEqual(catalog['other'], sources.binding(roots.home, 'other', legacy['transport'], 'main', 'skills', legacy['authoring']))
        self.assertEqual(self.without_policy(catalog['extra']), roots.config['sources']['extra'])


class PolicySurfaces(LineEndingFixture):
    """A5: capabilities, tap add help and the machine v3 schema describe the policy."""

    def test_capabilities_advertise_the_default_the_values_and_the_opt_in_flag(self):
        caps = self.call('capabilities')['data']
        self.assertEqual(caps['line_endings'], POLICY)
        arguments = {item['name']: item for item in {command['name']: command for command in caps['commands']}['tap.add']['arguments']}
        flag = arguments['autocrlf']
        self.assertEqual((flag['flags'], flag['type'], flag['required'], flag['repeatable'], flag['nargs']), (['--autocrlf'], 'boolean', False, False, 0))

    def test_tap_add_help_describes_exact_bytes_and_the_opt_in(self):
        run = subprocess.run([sys.executable, '-B', str(ENTRY), 'tap', 'add', '--help'], capture_output=True, encoding='utf-8',
                             cwd=str(self.project), env=self.environment(), timeout=60)
        self.assertEqual((run.returncode, run.stderr), (0, ''))
        text = ' '.join(run.stdout.split())
        for phrase in ('A tap keeps exact bytes', '--autocrlf', 'core.autocrlf=true', '(default: exact bytes)'):
            self.assertIn(phrase, text)
        self.assertEqual(self.call('tap', 'add', '--help')['data']['help'], run.stdout)

    def test_machine_v3_schema_describes_the_optional_policy_and_fits_written_entries(self):
        schema = json.loads((ENTRY.parent / 'schemas/machine-v3.schema.json').read_text(encoding='utf-8'))
        shape = schema['properties']['sources']['additionalProperties']
        self.assertEqual(shape['properties']['line_endings'], dict(enum=['exact', 'autocrlf']))
        self.assertNotIn('line_endings', shape['required'])
        self.assertIs(shape['additionalProperties'], False)
        self.call('tap', 'add', TAP, self.upstream)
        self.call('tap', 'add', 'converting', self.upstream, '--autocrlf')
        catalog = json.loads((self.home / 'config.json').read_text(encoding='utf-8'))['sources']
        self.assertEqual({name: entry['line_endings'] for name, entry in catalog.items()}, {TAP: 'exact', 'converting': 'autocrlf'})
        for name, entry in catalog.items():
            with self.subTest(tap=name):
                self.assertLessEqual(set(shape['required']), set(entry))
                self.assertLessEqual(set(entry), set(shape['properties']))


class AutocrlfFidelity(AutocrlfGit, unittest.TestCase):
    """``mask_provenance.autocrlf`` against the bytes real Git stores under core.autocrlf=true."""

    NEW = (('plain CRLF text', b'one\r\ntwo\r\n'), ('no CRLF', b'one\ntwo\n'), ('lone CR', b'one\r\ntwo\rthree\r\n'),
           ('NUL', b'one\r\n\x00two\r\n'), ('mostly control bytes', b'\x01\x02\x03\x04\r\n'),
           ('one control byte per 127 printable', b'a' * 127 + b'\x01\r\n'), ('one control byte per 128 printable', b'a' * 128 + b'\x01\r\n'),
           ('trailing 0x1a', b'text\r\n\x1a'), ('inner 0x1a', b'text\r\n\x1a!'), ('empty', b''))

    def setUp(self):
        self.force_autocrlf()
        directory = tempfile.TemporaryDirectory(prefix='mask-autocrlf-fidelity-')
        self.addCleanup(directory.cleanup)
        self.repo = Path(directory.name).resolve()
        for args in (('init', '-q', '-b', 'main'), ('config', 'user.name', 'Fixture'), ('config', 'user.email', 'fixture@example.invalid')):
            self.git(*args)

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], capture_output=True, check=True).stdout

    def test_new_files_convert_exactly_as_git_hash_object_stores_them(self):
        converted = []
        for index, (name, data) in enumerate(self.NEW):
            with self.subTest(case=name):
                path = f'case-{index}.md'
                (self.repo / path).write_bytes(data)
                oid = self.git('-c', 'core.autocrlf=true', 'hash-object', '-w', '--path=' + path, path).strip().decode('ascii')
                stored = self.git('cat-file', 'blob', oid)
                self.assertEqual(provenance.autocrlf(data), stored)
                if stored != data:
                    converted.append(name)
        # Git really converted under this configuration, and only the cases its text statistics call text.
        self.assertEqual(converted, ['plain CRLF text', 'one control byte per 128 printable', 'trailing 0x1a'])

    def test_the_committed_copy_decides_conversion_as_git_add_does(self):
        # hash-object does not consult the index, so the blob git add stages over the committed one is the oracle for
        # Git's rule: only a committed text copy that already holds CRLF keeps an edit unconverted.
        cases = (('committed CRLF text', b'old\r\nline\r\n', b'newer\r\nline\r\n', False),
                 ('committed LF text', b'old\nline\n', b'newer\r\nline\r\n', True),
                 ('committed lone CR', b'old\rline\n', b'newer\r\nline\r\n', True),
                 ('committed NUL with CRLF', b'old\r\n\x00line\r\n', b'newer\r\nline\r\n', True))
        for index, (name, old, new, converts) in enumerate(cases):
            with self.subTest(case=name):
                path = f'committed-{index}.md'
                (self.repo / path).write_bytes(old)
                self.git('-c', 'core.autocrlf=false', 'add', '--', path)
                self.git('commit', '-q', '-m', name)
                self.assertEqual(self.git('cat-file', 'blob', 'HEAD:' + path), old)
                (self.repo / path).write_bytes(new)
                self.git('-c', 'core.autocrlf=true', 'add', '--', path)
                staged = self.git('cat-file', 'blob', ':' + path)
                self.assertEqual(provenance.autocrlf(new, PayloadFile(path, '100644', old)), staged)
                self.assertEqual(staged, new.replace(b'\r\n', b'\n') if converts else new)


if __name__ == '__main__':
    unittest.main()
