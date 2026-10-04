import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from tests.support import Fixture, ENTRY

# The runtime modules update requires in a program candidate (mask_install.protocol_version).
PROGRAM_MODULES = ('mask.py', 'mask_core.py', 'mask_fs.py', 'mask_git.py', 'mask_install.py', 'mask_ensure.py', 'mask_integration.py', 'mask_report.py', 'mask_present.py', 'mask_sources.py', 'mask_packages.py', 'mask_process.py', 'mask_provenance.py', 'mask_resolve.py', 'mask_store.py', 'mask_pinned.py', 'mask_selection.py', 'mask_adapters.py', 'mask_consent.py', 'mask_task.py', 'mask_bundles.py', 'mask_workflow.py', 'mask_setup.py', 'mask_repair.py', 'mask_update.py', 'mask_cli.py', 'mask_lifecycle.py', 'mask_cleanup.py', 'mask_pin.py', 'mask_progress.py')

# Runs update from a program checkout with one injected fault: a crash at the Git checkpoint after the checkout
# advanced, a failing fast-forward merge, or a failure of the journal effects after the checkout advanced.
FAULT = """
import os, sys
sys.path.insert(0, sys.argv[1])
import mask, mask_core, mask_fs
fault = sys.argv[3]
if fault == 'crash-at-git':
    mask_fs.checkpoint = lambda label: os._exit(99) if label == 'git' else None
elif fault == 'merge-fails':
    original_git = mask_core.git
    def git(root, *args, **kwargs):
        if args and args[0] == 'merge':
            raise OSError('injected merge failure')
        return original_git(root, *args, **kwargs)
    mask_core.git = git
elif fault == 'fails-after-advance':
    original_restore = mask_fs.restore
    def restore(pending, home, side, **kwargs):
        if side == 'after':
            raise OSError('injected failure after the checkout advanced')
        return original_restore(pending, home, side, **kwargs)
    mask_fs.restore = restore
raise SystemExit(mask.main(['update', '--home', sys.argv[2], '--json', *sys.argv[4:]]))
"""


class LauncherTests(Fixture):
    def test_install_dry_run_refusal_and_native_forwarding(self):
        directory = self.base / 'bin spaced ü'
        before = self.snapshot()
        self.call('self', 'install', '--bin-dir', directory, '--dry-run')
        self.assertEqual(before, self.snapshot())
        result = self.call('self', 'install', '--bin-dir', directory, env={'PATH': str(directory) + os.pathsep + os.environ['PATH']})
        self.assertTrue(result['data']['on_path'])
        launcher = result['data']['launcher']
        self.assertFalse(self.call('self', 'install', '--bin-dir', directory)['changed'])
        args = [launcher, 'self', 'status', '--home', str(self.home), '--json']
        run = subprocess.run(args, capture_output=True, encoding='utf-8', shell=False)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout)['data']['program_root'], str(ENTRY.parent))
        run = subprocess.run([launcher, 'bogus', '--json'], capture_output=True, encoding='utf-8', shell=False)
        self.assertEqual(run.returncode, 2)
        Path(launcher).write_text('unrelated executable')
        self.call('self', 'install', '--bin-dir', directory, code=4)
        self.assertEqual(Path(launcher).read_text(), 'unrelated executable')

    def program_checkout(self):
        """A program checkout tracking a local bare remote, plus a separate author clone that publishes candidates."""
        remote = self.base / 'ManageAgentSkills.git'
        program = self.base / 'program spaced ü'
        self.git(self.base, 'init', '--bare', str(remote))
        self.git(self.base, 'clone', str(remote), str(program))
        self.git(program, 'checkout', '-b', 'main')
        for name in PROGRAM_MODULES:
            shutil.copyfile(ENTRY.parent / name, program / name)
        shutil.copytree(ENTRY.parent / 'schemas', program / 'schemas')
        self.git(program, 'config', 'user.name', 'Fixture'); self.git(program, 'config', 'user.email', 'fixture@example.invalid')
        (program / '.gitattributes').write_text('schemas/*.schema.json text eol=crlf\n')
        self.git(program, 'add', '.'); self.git(program, 'commit', '-m', 'program'); self.git(program, 'push', '-u', 'origin', 'main')
        for schema in (program / 'schemas').glob('*.schema.json'):
            schema.write_bytes(schema.read_bytes().replace(b'\r\n', b'\n').replace(b'\n', b'\r\n'))
        self.git(program, 'add', 'schemas')  # Refresh stat data after checkout-equivalent conversion.
        author = self.base / 'program author'
        self.git(self.base, 'clone', '--branch', 'main', str(remote), str(author))
        self.git(author, 'config', 'user.name', 'Fixture'); self.git(author, 'config', 'user.email', 'fixture@example.invalid')
        return program, author

    def publish_program(self, author, text='compatible fixture update'):
        with (author / 'mask.py').open('a') as handle: handle.write('\n# ' + text + '\n')
        self.git(author, 'add', 'mask.py'); self.git(author, 'commit', '-m', text); self.git(author, 'push', 'origin', 'main')
        return self.git(author, 'rev-parse', 'HEAD')

    def program(self, program, *args, code=0):
        """One invocation of the program checkout itself; recovery of its journal must run the same program root."""
        run = subprocess.run([sys.executable, '-B', str(program / 'mask.py'), *map(str, args), '--home', str(self.home), '--json'], capture_output=True, encoding='utf-8')
        self.assertEqual(run.returncode, code, run.stdout + run.stderr)
        return json.loads(run.stdout)

    def fault(self, program, fault, code, *extra):
        run = subprocess.run([sys.executable, '-B', '-c', FAULT, str(program), str(self.home), fault, *extra], capture_output=True, encoding='utf-8')
        self.assertEqual(run.returncode, code, run.stdout + run.stderr)
        return json.loads(run.stdout) if run.stdout.strip() else None

    def pending(self):
        return json.loads((self.home / 'pending.json').read_text(encoding='utf-8'))

    def publish_schema(self, author, change, name='machine-v3.schema.json', message='schema change'):
        """Publish one edited schema; ``change`` mutates the parsed document in place."""
        path = author / 'schemas' / name
        document = json.loads(path.read_bytes())
        change(document)
        path.write_text(json.dumps(document, indent=2) + '\n')
        self.git(author, 'add', str(path)); self.git(author, 'commit', '-m', message); self.git(author, 'push', 'origin', 'main')
        return self.git(author, 'rev-parse', 'HEAD')

    def program_text(self, program, *args):
        """A human (non-JSON) invocation with redirected streams: it never prompts."""
        run = subprocess.run([sys.executable, '-B', str(program / 'mask.py'), *map(str, args), '--home', str(self.home)], capture_output=True, encoding='utf-8', stdin=subprocess.DEVNULL)
        return run.returncode, run.stdout, run.stderr

    def program_terminal(self, program, answer):
        """mask update on a POSIX pseudoterminal, answering its one [y/N] question."""
        import pty, select, time
        master, slave = pty.openpty()
        process = subprocess.Popen([sys.executable, '-B', str(program / 'mask.py'), 'update', '--home', str(self.home)], stdin=slave, stdout=slave, stderr=slave,
                                   env=dict(os.environ, TERM='xterm', NO_COLOR='1') if answer is None else dict(os.environ, TERM='xterm'), close_fds=True)
        os.close(slave)
        transcript, answered, deadline = b'', False, time.monotonic() + 60
        try:
            while time.monotonic() < deadline:
                ready, _, _ = select.select([master], [], [], 0.2)
                if ready:
                    try:
                        chunk = os.read(master, 4096)
                    except OSError:
                        break
                    if not chunk:
                        break
                    transcript += chunk
                if not answered and b'[y/N]' in transcript:
                    os.write(master, answer or b'\n')
                    answered = True
                if process.poll() is not None and not ready:
                    break
            process.wait(timeout=10)
        finally:
            if process.poll() is None:
                process.kill(); process.wait()
            os.close(master)
        return process.returncode, transcript.decode('utf-8', 'replace'), answered

    def assert_readable(self, text):
        self.assertNotIn('\x1b', text)
        self.assertNotIn('\x0e', text)
        self.assertLessEqual(max(len(line) for line in text.splitlines()), 80, text)

    def test_program_update_separate_and_comment_only_schema_change_needs_no_question(self):
        program, author = self.program_checkout()
        self.init(); self.install('alpha')
        source_head = self.git(self.source, 'rev-parse', 'HEAD'); before = self.snapshot(self.project)
        state_before = (self.home / 'state.json').read_bytes()
        self.publish_program(author, 'compatible')
        self.assertTrue(self.program(program, 'update')['data']['program']['next_invocation_required'])
        self.assertEqual(source_head, self.git(self.source, 'rev-parse', 'HEAD'))
        self.assertEqual(before, self.snapshot(self.project))
        self.assertEqual(state_before, (self.home / 'state.json').read_bytes())
        self.assertFalse(self.program(program, 'update')['changed'])
        candidate = self.publish_schema(author, lambda schema: schema.update(title='Changed contract fixture', description='Reworded.'))
        code, stdout, stderr = self.program_text(program, 'update')
        self.assertEqual(code, 0, stderr)
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), candidate)
        self.assertIn('MASK updated:', stdout)
        self.assertRegex(stdout, r'machine-v3\.schema\.json +comment +wording only')
        self.assert_readable(stdout)

    def test_additive_schema_change_is_shown_and_approved_exactly(self):
        program, author = self.program_checkout()
        self.init()
        before = self.git(program, 'rev-parse', 'HEAD')
        candidate = self.publish_schema(author, lambda schema: schema['properties'].update(fixture_note={'type': 'string'}))
        refused = self.program(program, 'update', code=4)
        self.assertEqual(refused['error']['code'], 'confirmation.required')
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), before)
        self.assertTrue(refused['data']['fetches']['agentskills']['ok'])  # Taps are fetched even though MASK waits for review.
        self.assertEqual(refused['data']['confirmation']['kind'], 'program.migration')
        migration = refused['data']['program']['program_migration']
        self.assertEqual(refused['data']['program']['status'], 'review')
        self.assertEqual([(row['file'], row['change'], row['summary']) for row in migration['schemas']],
                         [('machine-v3.schema.json', 'additive', 'adds optional fixture_note')])
        self.assertEqual((migration['protocol'], migration['breaking'], migration['commits']), ({'before': 2, 'after': 2}, False, 1))
        code, stdout, stderr = self.program_text(program, 'update')
        self.assertEqual((code, stdout), (4, ''))
        self.assertIn('error: MASK update needs your approval: it changes 1 schema.', stderr)
        self.assertRegex(stderr, r'machine-v3\.schema\.json +additive +adds optional fixture_note')
        self.assertIn('state: MASK was not moved; taps were fetched', stderr)
        self.assertIn(f"hash: {migration['plan_hash']}", stderr)
        self.assert_readable(stderr)
        stale = self.program(program, 'update', '--approve-plan', 'sha256:' + '0' * 64, code=4)
        self.assertEqual(stale['error']['code'], 'plan.stale')
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), before)
        approved = self.program(program, 'update', '--approve-plan', migration['plan_hash'])
        self.assertEqual(approved['data']['program']['status'], 'updated')
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), candidate)

    def test_breaking_schema_and_protocol_changes_are_marked(self):
        program, author = self.program_checkout()
        self.publish_schema(author, lambda schema: schema['properties'].pop('forge_hosts'))
        refused = self.program(program, 'update', code=4)
        row, = refused['data']['program']['program_migration']['schemas']
        self.assertEqual((row['change'], row['summary']), ('breaking', 'removes forge_hosts'))
        def require_new_property(schema):
            schema['properties']['forge_hosts'] = {'type': 'object'}
            schema['required'].append('forge_hosts')
        self.publish_schema(author, require_new_property)
        row, = self.program(program, 'update', code=4)['data']['program']['program_migration']['schemas']
        self.assertEqual(row['change'], 'breaking')
        path = author / 'mask.py'; path.write_text(path.read_text().replace('PROTOCOL_VERSION = 2', 'PROTOCOL_VERSION = 3'))
        self.git(author, 'add', 'mask.py'); self.git(author, 'commit', '-m', 'incompatible'); self.git(author, 'push', 'origin', 'main')
        refused = self.program(program, 'update', code=4)
        self.assertEqual(refused['data']['program']['program_migration']['protocol'], {'before': 2, 'after': 3})
        code, _, stderr = self.program_text(program, 'update')
        self.assertEqual(code, 4)
        self.assertIn('protocol: v2 -> v3, a new protocol', stderr)
        self.assertIn('Some existing files may no longer validate with this version.', stderr)
        self.assert_readable(stderr)
        (author / 'mask.py').write_text('PROTOCOL_VERSION = "two"\n')
        self.git(author, 'add', 'mask.py'); self.git(author, 'commit', '-m', 'unreadable'); self.git(author, 'push', 'origin', 'main')
        self.assertEqual(self.program(program, 'update', code=4)['error']['code'], 'source.candidate_invalid')

    @unittest.skipUnless(os.name == 'posix', 'POSIX pseudoterminal prompt; native Windows console journeys are recorded separately')
    def test_terminal_update_asks_once_and_applies_or_declines(self):
        program, author = self.program_checkout()
        self.init()
        before = self.git(program, 'rev-parse', 'HEAD')
        candidate = self.publish_schema(author, lambda schema: schema['properties'].update(fixture_note={'type': 'string'}))
        for answer in (b'n\n', None):  # An explicit no, then a bare Enter (the default) with NO_COLOR.
            code, text, asked = self.program_terminal(program, answer)
            self.assertTrue(asked, text)
            self.assertEqual(code, 4, text)
            self.assertIn('You declined, so MASK was not updated.', text)
            self.assertIn('tap agentskills: fetched', text)
            self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), before)
        self.assertNotIn('\x1b[', text)  # NO_COLOR on a terminal stays plain.
        code, text, asked = self.program_terminal(program, b'y\n')
        self.assertEqual((code, asked), (0, True), text)
        self.assertEqual(text.count('[y/N]'), 1)
        for expected in ('This update changes the files MASK uses to describe your setup.', 'Protocol   v2, unchanged',
                         'Your existing projects and taps stay valid with this version.', 'Taps were fetched.',
                         f'Update MASK to {candidate[:7]}? [y/N]', 'MASK updated:'):
            self.assertIn(expected, text)
        self.assertIn('\x1b[32madditive', text)  # The class word is colored on a terminal.
        self.assertNotIn('sha256:', text)  # The plan hash stays inside the program.
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), candidate)

    def test_approved_migration_recovers_without_asking_again(self):
        program, author = self.program_checkout()
        candidate = self.publish_schema(author, lambda schema: schema['properties'].update(fixture_note={'type': 'string'}))
        plan_hash = self.program(program, 'update', code=4)['data']['program']['program_migration']['plan_hash']
        self.fault(program, 'crash-at-git', 99, '--approve-plan', plan_hash)
        self.assertEqual(self.pending()['git']['consent'], plan_hash)
        journal = (self.home / 'pending.json').read_text(encoding='utf-8')
        (self.home / 'pending.json').write_text(journal.replace(plan_hash, 'sha256:' + '1' * 64), encoding='utf-8')
        self.assertEqual(self.program(program, 'recover', '--complete', code=4)['error']['code'], 'plan.stale')
        (self.home / 'pending.json').write_text(journal, encoding='utf-8')
        self.program(program, 'recover', '--complete')
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), candidate)
        self.assertFalse((self.home / 'pending.json').exists())

    def test_background_refresh_waits_for_a_manual_review(self):
        program, author = self.program_checkout()
        self.init()
        before = self.git(program, 'rev-parse', 'HEAD')
        self.publish_schema(author, lambda schema: schema['properties'].update(fixture_note={'type': 'string'}))
        installed = self.program(program, 'install', 'alpha', '--project', self.project)
        self.assertIn('update.review_required', [warning['code'] for warning in installed['warnings']])
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), before)

    # The update checkout journal (mask_git.advance, mask_git.recover_git and the git branch of mask_fs.execute):
    # the program checkout only ever moves forward to the reviewed candidate and is never reset.

    def test_crash_after_program_advance_completes_and_never_resets_the_checkout(self):
        program, author = self.program_checkout()
        before = self.git(program, 'rev-parse', 'HEAD')
        candidate = self.publish_program(author)
        self.fault(program, 'crash-at-git', 99)
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), candidate)
        self.assertEqual((self.pending()['phase'], self.pending()['git']['before'], self.pending()['git']['candidate']), ('git_advanced', before, candidate))
        refused = self.program(program, 'recover', '--rollback', code=8)
        self.assertEqual((refused['error']['code'], refused['transaction']), ('recovery.conflict', 'partial'))
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), candidate)
        self.assertTrue((self.home / 'pending.json').exists())
        self.program(program, 'recover', '--complete')
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), candidate)
        self.assertFalse((self.home / 'pending.json').exists())

    def test_failed_program_merge_keeps_a_partial_journal_and_rolls_back_without_reset(self):
        program, author = self.program_checkout()
        before = self.git(program, 'rev-parse', 'HEAD')
        self.publish_program(author)
        result = self.fault(program, 'merge-fails', 8)
        self.assertEqual((result['error']['code'], result['transaction'], result['changed']), ('recovery.required', 'partial', True))
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), before)
        self.assertEqual(self.pending()['phase'], 'git_started')
        self.program(program, 'recover', '--rollback')
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), before)
        self.assertFalse((self.home / 'pending.json').exists())

    def test_failure_after_program_advance_keeps_the_journal_for_completion(self):
        program, author = self.program_checkout()
        candidate = self.publish_program(author)
        result = self.fault(program, 'fails-after-advance', 8)
        self.assertEqual((result['error']['code'], result['transaction']), ('recovery.required', 'partial'))
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), candidate)
        self.assertEqual(self.pending()['phase'], 'git_advanced')
        self.program(program, 'recover', '--complete')
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), candidate)
        self.assertFalse((self.home / 'pending.json').exists())
