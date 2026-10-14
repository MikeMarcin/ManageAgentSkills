import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from tests.support import Fixture, ENTRY

# Every runtime module, so a new one can never be missing from the disposable program checkout.
PROGRAM_MODULES = tuple(sorted(path.name for path in ENTRY.parent.glob('mask*.py')))

# Runs update from a program checkout with one injected fault: a crash at the Git checkpoint after the checkout
# advanced, a crash just after update --stash recorded its stash, a failing fast-forward merge, or a failure of
# the journal effects after the checkout advanced.
FAULT = """
import os, sys
sys.path.insert(0, sys.argv[1])
import mask, mask_core, mask_fs
fault = sys.argv[3]
if fault == 'crash-at-git':
    mask_fs.checkpoint = lambda label: os._exit(99) if label == 'git' else None
elif fault == 'crash-at-stash':
    mask_fs.checkpoint = lambda label: os._exit(99) if label == 'stash' else None
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
    def test_update_requires_every_runtime_module_of_a_candidate(self):
        # A module missing from this list lets update advance to a candidate that cannot import it.
        import mask_install
        self.assertEqual(sorted(mask_install.RUNTIME_MODULES), list(PROGRAM_MODULES))

    def test_install_dry_run_refusal_and_native_forwarding(self):
        directory = self.base / 'bin spaced ü'
        before = self.snapshot()
        self.call('self', 'install', '--bin-dir', directory, '--dry-run')
        self.assertEqual(before, self.snapshot())
        result = self.call('self', 'install', '--bin-dir', directory, env={'PATH': str(directory) + os.pathsep + os.environ['PATH']})
        self.assertTrue(result['data']['on_path'])
        launcher = result['data']['launcher']
        self.assertEqual(result['data']['launchers'], [str(directory / name) for name in (('mask.cmd', 'mask') if os.name == 'nt' else ('mask',))])
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

    def test_ahead_only_update_is_current_preserves_work_and_fetches_taps(self):
        program, author = self.program_checkout()
        upstream = self.git(program, 'rev-parse', 'HEAD')
        with (program / 'mask.py').open('a') as handle:
            handle.write('\n# local authoring commit\n')
        self.git(program, 'add', 'mask.py')
        self.git(program, 'commit', '-m', 'local authoring')
        local = self.git(program, 'rev-parse', 'HEAD')
        self.dirty(program, modified=['mask.py'], untracked=['notes.txt'], staged=['staged.txt'])
        self.init()
        self.call('source', 'fetch', 'agentskills')
        self.add_skill('new-skill')
        self.publish('new tap skill')
        status = self.git(program, 'status', '--porcelain')
        index = self.git(program, 'diff', '--cached')
        contents = {name: (program / name).read_bytes() for name in ('mask.py', 'notes.txt', 'staged.txt')}
        state = (self.home / 'state.json').read_bytes()
        result = self.program(program, 'update')
        row = result['data']['program']
        self.assertEqual((row['status'], row['relation']), ('current', 'ahead'))
        self.assertEqual((row['program_before'], row['program_after'], row['candidate']), (local, local, upstream))
        self.assertEqual(row['remote_freshness'], 'fetched')
        self.assertFalse(row['next_invocation_required'])
        self.assertFalse(result['changed'])
        self.assertFalse(result['would_change'])
        self.assertTrue(result['data']['fetches']['agentskills']['ok'])
        self.assertTrue(result['data']['fetches']['agentskills']['remote_refs_changed'])
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), local)
        self.assertEqual(self.git(program, 'status', '--porcelain'), status)
        self.assertEqual(self.git(program, 'diff', '--cached'), index)
        self.assertEqual({name: (program / name).read_bytes() for name in contents}, contents)
        self.assertEqual((self.home / 'state.json').read_bytes(), state)
        self.assertFalse((self.home / 'pending.json').exists())
        preview = self.program(program, 'update', '--dry-run')
        self.assertEqual(preview['data']['program']['status'], 'current')
        self.assertEqual(preview['data']['program']['remote_freshness'], 'last_fetched')
        self.assertFalse(preview['data']['fetches']['agentskills']['attempted'])
        self.assertEqual(self.git(program, 'status', '--porcelain'), status)
        import mask_present
        text = mask_present.render(result)
        self.assertIn('no newer upstream version', text)
        self.assertIn('local commits are kept', text)
        self.assertNotIn('MASK was not updated', text)
        self.assertNotIn('(-)', text)
        self.assertIn('last-fetched remote', mask_present.render(preview))

    def test_diverged_update_keeps_its_hold_and_local_commit(self):
        program, author = self.program_checkout()
        (program / 'local.txt').write_text('local work\n')
        self.git(program, 'add', 'local.txt')
        self.git(program, 'commit', '-m', 'local work')
        local = self.git(program, 'rev-parse', 'HEAD')
        self.publish_program(author)
        result = self.program(program, 'update')
        self.assertEqual((result['data']['program']['status'], result['data']['program']['code']),
                         ('held', 'source.diverged'))
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), local)

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
        environment = dict(os.environ, TERM='xterm')
        environment.pop('NO_COLOR', None)
        if answer is None:
            environment['NO_COLOR'] = '1'
        master, slave = pty.openpty()
        process = subprocess.Popen([sys.executable, '-B', str(program / 'mask.py'), 'update', '--home', str(self.home)], stdin=slave, stdout=slave, stderr=slave,
                                   env=environment, close_fds=True)
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

    def test_output_only_breaking_change_names_the_field_and_spares_files(self):
        program, author = self.program_checkout()
        self.publish_schema(author, lambda schema: schema['properties']['data'].pop('properties', None), name='result.schema.json')
        self.program(program, 'update', '--approve-plan', self.program(program, 'update', code=4)['data']['program']['program_migration']['plan_hash'])
        self.publish_schema(author, lambda schema: schema['properties']['data'].update(properties={'commits': {'type': 'array'}}), name='result.schema.json')
        row, = self.program(program, 'update', code=4)['data']['program']['program_migration']['schemas']
        self.assertEqual((row['file'], row['change'], row['summary'], row['audience']), ('result.schema.json', 'breaking', 'now constrains data.commits', 'output'))
        code, _, stderr = self.program_text(program, 'update')
        self.assertEqual(code, 4)
        self.assertIn("Only MASK's --json output changes shape; your files are unaffected.", stderr)
        self.assertNotIn('Some existing files may no longer validate', stderr)
        self.assert_readable(stderr)
        self.publish_schema(author, lambda schema: schema['properties'].pop('forge_hosts'))
        refused = self.program(program, 'update', code=4)
        self.assertEqual([row['audience'] for row in refused['data']['program']['program_migration']['schemas']], ['files', 'output'])
        self.assertIn('Some existing files may no longer validate with this version.', self.program_text(program, 'update')[2])

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

    # MASK-0133: uncommitted work in the program checkout holds update only where the fast-forward would touch it.

    def dirty(self, program, *, modified=(), untracked=(), staged=()):
        """Uncommitted work in the program checkout: an appended line, a new untracked file, a new staged file."""
        for name in modified:
            with (program / name).open('a', encoding='utf-8', newline='\n') as handle:
                handle.write('\n# local edit\n')
        for name in untracked + staged:
            (program / name).parent.mkdir(parents=True, exist_ok=True)
            (program / name).write_text('local ' + name + '\n', encoding='utf-8', newline='\n')
        if staged:
            self.git(program, 'add', '--', *staged)

    def publish_files(self, author, *names, text='published'):
        """Publish new files beside a compatible program change."""
        for name in names:
            (author / name).parent.mkdir(parents=True, exist_ok=True)
            (author / name).write_text(text + ' ' + name + '\n', encoding='utf-8', newline='\n')
        self.git(author, 'add', '--', *names)
        return self.publish_program(author, text)

    def stashes(self, program):
        return self.git(program, 'stash', 'list', '--format=%H').split()

    def test_dirty_checkout_fast_forwards_when_the_update_touches_none_of_it(self):
        program, author = self.program_checkout()
        before = self.git(program, 'rev-parse', 'HEAD')
        self.dirty(program, modified=('mask_adapters.py',), untracked=('notes/todo.txt',), staged=('staged.txt',))
        local = sorted(self.git(program, 'status', '--porcelain', '--untracked-files=all').splitlines())
        candidate = self.publish_program(author)
        result = self.program(program, 'update')
        self.assertEqual(result['data']['program']['status'], 'updated')
        self.assertEqual(result['data']['program']['preserved'], ['mask_adapters.py', 'notes/todo.txt', 'staged.txt'])
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), candidate)
        self.assertEqual(sorted(self.git(program, 'status', '--porcelain', '--untracked-files=all').splitlines()), local)
        self.assertEqual(self.git(program, 'diff', '--cached', '--name-only'), 'staged.txt')  # Staging survives too.
        self.assertTrue((program / 'mask_adapters.py').read_text(encoding='utf-8').endswith('# local edit\n'))
        self.assertEqual(self.stashes(program), [])
        self.publish_program(author, 'second')
        code, stdout, stderr = self.program_text(program, 'update')
        self.assertEqual(code, 0, stderr)
        self.assertIn('MASK updated:', stdout)
        self.assertIn('Kept 3 uncommitted paths in place; the update does not touch them.', stdout)
        self.assert_readable(stdout)
        # Interrupted fast-forwards of the same dirty checkout recover in both directions.
        head = self.git(program, 'rev-parse', 'HEAD')
        self.publish_program(author, 'third')
        self.fault(program, 'merge-fails', 8)
        self.program(program, 'recover', '--rollback')
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), head)
        self.assertFalse((self.home / 'pending.json').exists())
        self.fault(program, 'merge-fails', 8)
        completed = self.program(program, 'recover', '--complete')
        self.assertEqual(completed['transaction'], 'committed')
        latest = self.git(author, 'rev-parse', 'HEAD')
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), latest)
        self.publish_program(author, 'fourth')
        self.fault(program, 'crash-at-git', 99)
        self.program(program, 'recover', '--complete')
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), self.git(author, 'rev-parse', 'HEAD'))
        self.assertEqual(sorted(self.git(program, 'status', '--porcelain', '--untracked-files=all').splitlines()), local)
        self.assertNotEqual(before, self.git(program, 'rev-parse', 'HEAD'))
        # Overlapping dirt still blocks completing a recovery, and rollback still clears the journal.
        self.publish_program(author, 'fifth')
        self.fault(program, 'merge-fails', 8)
        self.dirty(program, modified=('mask.py',))
        refused = self.program(program, 'recover', '--complete', code=4)
        self.assertEqual((refused['error']['code'], refused['error']['details']['blocking_paths']), ('source.dirty', ['mask.py']))
        self.program(program, 'recover', '--rollback')
        self.assertFalse((self.home / 'pending.json').exists())

    def test_overlapping_changes_hold_the_program_and_name_the_way_out(self):
        program, author = self.program_checkout()
        self.init()
        before = self.git(program, 'rev-parse', 'HEAD')
        names = [f'extra/{letter}.txt' for letter in 'abcdef']
        self.publish_files(author, *names, text='clash')
        self.dirty(program, modified=('mask.py', 'mask_adapters.py'), untracked=tuple(names))
        held = self.program(program, 'update')  # A hold is reported, not a failure.
        program_row = held['data']['program']
        self.assertEqual((program_row['status'], program_row['code']), ('held', 'source.dirty'))
        self.assertEqual(program_row['blocking_paths'], sorted(names + ['mask.py']))
        self.assertEqual(program_row['preserved'], ['mask_adapters.py'])
        self.assertTrue(held['data']['fetches']['agentskills']['ok'])
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), before)
        code, stdout, stderr = self.program_text(program, 'update')
        self.assertEqual(code, 0, stderr)
        self.assertIn('MASK was not updated: your uncommitted changes touch files this update changes.', stdout)
        self.assertIn('In the way: 7 changed paths', stdout)
        for name in names[:5]:
            self.assertIn('    ' + name + '\n', stdout)
        self.assertNotIn(names[5], stdout)
        self.assertIn('    and 2 more', stdout)
        self.assertIn('mask update --stash', stdout)
        self.assertIn('tap agentskills: fetched', stdout)
        self.assert_readable(stdout)
        self.assertEqual(self.stashes(program), [])

    def test_file_where_the_update_has_a_directory_blocks(self):
        program, author = self.program_checkout()
        self.publish_files(author, 'docs2/guide.txt', text='folder')
        self.dirty(program, untracked=('docs2',))
        held = self.program(program, 'update')
        self.assertEqual(held['data']['program']['blocking_paths'], ['docs2'])

    def test_stash_moves_only_the_blocking_paths_and_never_applies_them(self):
        program, author = self.program_checkout()
        before = self.git(program, 'rev-parse', 'HEAD')
        candidate = self.publish_files(author, 'extra/new.txt', text='with a file')
        self.dirty(program, modified=('mask.py', 'mask_adapters.py'), untracked=('extra/new.txt', 'notes.txt'))
        edited = (program / 'mask.py').read_text(encoding='utf-8')
        self.git(program, 'fetch', 'origin')  # A dry run contacts nothing; it previews the last fetched candidate.
        preview = self.program(program, 'update', '--dry-run', '--stash')
        self.assertEqual(preview['data']['program']['status'], 'behind')
        self.assertEqual(preview['data']['program']['stash']['paths'], ['extra/new.txt', 'mask.py'])
        self.assertIsNone(preview['data']['program']['stash']['commit'])
        self.assertEqual((self.git(program, 'rev-parse', 'HEAD'), self.stashes(program)), (before, []))
        self.assertEqual((program / 'mask.py').read_text(encoding='utf-8'), edited)
        result = self.program(program, 'update', '--stash')
        program_row = result['data']['program']
        stash = program_row['stash']
        self.assertEqual(program_row['status'], 'updated')
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), candidate)
        self.assertEqual(self.stashes(program), [stash['commit']])  # Made once, never popped or applied.
        self.assertRegex(stash['message'], rf'^mask update {before[:7]}\.\.{candidate[:7]} \d{{4}}-\d\d-\d\dT\d\d:\d\d:\d\dZ$')
        self.assertEqual(self.git(program, 'stash', 'list', '--format=%gs'), 'On main: ' + stash['message'])
        self.assertEqual((stash['paths'], stash['inspect']), (['extra/new.txt', 'mask.py'], f"git stash show -p {stash['commit']}"))
        self.assertEqual(program_row['preserved'], ['mask_adapters.py', 'notes.txt'])
        self.assertIn('# local edit', self.git(program, 'show', stash['commit'] + ':mask.py'))
        self.assertEqual(self.git(program, 'show', stash['commit'] + '^3:extra/new.txt'), 'local extra/new.txt')
        self.assertEqual((program / 'extra/new.txt').read_text(encoding='utf-8'), 'with a file extra/new.txt\n')
        self.assertEqual((self.git(program, 'diff', '--name-only'), self.git(program, 'ls-files', '--others')), ('mask_adapters.py', 'notes.txt'))
        # The human result names the stash and how to look at it.
        self.publish_program(author, 'again')
        self.dirty(program, modified=('mask.py',))
        code, stdout, stderr = self.program_text(program, 'update', '--stash')
        self.assertEqual(code, 0, stderr)
        newest = self.stashes(program)[0]
        self.assertEqual(len(self.stashes(program)), 2)
        self.assertIn('Stashed 1 path that the update changed:', stdout)
        self.assertIn(f'stash:   {newest}\n  message: mask update ', stdout)
        self.assertIn(f'stash show -p {newest}', stdout)
        self.assertIn('MASK never pops or applies this stash', stdout)
        # With nothing in the way, --stash does nothing extra.
        latest = self.publish_program(author, 'clean')
        plain = self.program(program, 'update', '--stash')
        self.assertNotIn('stash', plain['data']['program'])
        self.assertEqual((self.git(program, 'rev-parse', 'HEAD'), len(self.stashes(program))), (latest, 2))
        code, _, stderr = self.program_text(program, 'upgrade', '--stash')
        self.assertEqual(code, 2, stderr)
        self.assertIn('--stash', stderr)

    def test_failure_after_the_stash_keeps_it_journaled_and_recovery_reports_it(self):
        program, author = self.program_checkout()
        before = self.git(program, 'rev-parse', 'HEAD')
        candidate = self.publish_program(author)
        self.dirty(program, modified=('mask.py',), untracked=('notes.txt',))
        failed = self.fault(program, 'merge-fails', 8, '--stash')
        self.assertEqual((failed['error']['code'], failed['transaction']), ('recovery.required', 'partial'))
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), before)
        recorded = self.pending()['git']['stash']
        self.assertEqual((self.stashes(program), recorded['paths']), ([recorded['commit']], ['mask.py']))
        self.assertEqual(failed['data']['stash']['commit'], recorded['commit'])
        self.assertEqual(self.git(program, 'status', '--porcelain', '--untracked-files=all'), '?? notes.txt')
        inspected = self.program(program, 'recover')
        self.assertEqual(inspected['data']['pending']['git']['stash'], recorded)
        code, stdout, _ = self.program_text(program, 'recover', '--rollback', '--dry-run')
        self.assertEqual(code, 0)
        self.assertIn('update --stash was setting aside 1 path:', stdout)
        self.assertIn(f"stash show -p {recorded['commit']}", stdout)
        rolled = self.program(program, 'recover', '--rollback')
        self.assertEqual(rolled['data']['stash']['commit'], recorded['commit'])
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), before)
        self.assertEqual(self.stashes(program), [recorded['commit']])
        self.assertFalse((self.home / 'pending.json').exists())
        # A crash right after the stash is recorded completes forward and still names it.
        self.dirty(program, modified=('mask.py',))
        self.fault(program, 'crash-at-stash', 99, '--stash')
        recorded = self.pending()['git']['stash']
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), before)
        completed = self.program(program, 'recover', '--complete')
        self.assertEqual(completed['data']['stash']['commit'], recorded['commit'])
        self.assertEqual(self.git(program, 'rev-parse', 'HEAD'), candidate)
        self.assertEqual(len(self.stashes(program)), 2)

    # MASK-0133: Git Bash on Windows runs an extensionless sh launcher beside mask.cmd.

    def test_launcher_style_follows_its_name(self):
        import mask_install
        record = dict(program_root=str(ENTRY.parent), interpreter=str(Path(sys.executable).resolve()))
        batch = mask_install.launcher_text(record, str(self.base / 'mask.cmd'))
        self.assertTrue(batch.startswith('@echo off\r\nrem MASK owned launcher v1\r\n'))
        shell = mask_install.launcher_text(record, str(self.base / 'mask'))
        self.assertTrue(shell.startswith('#!/bin/sh\n# MASK owned launcher v1\nexec '))
        self.assertNotIn('\r', shell)
        self.assertIn(ENTRY.as_posix(), shell)
        if os.name == 'nt':
            self.assertNotIn('\\', shell)
        self.assertEqual(mask_install.LAUNCHERS, ('mask.cmd', 'mask') if os.name == 'nt' else ('mask',))

    @unittest.skipUnless(os.name == 'nt', 'Windows writes mask.cmd and a Git Bash launcher side by side')
    def test_windows_writes_a_git_bash_launcher_beside_mask_cmd(self):
        directory = self.base / 'bin spaced'
        directory.mkdir()
        batch, shell = directory / 'mask.cmd', directory / 'mask'
        shell.write_text('#!/bin/sh\necho mine\n', encoding='utf-8', newline='\n')
        first = self.call('self', 'install', '--bin-dir', directory)
        self.assertEqual((first['data']['launcher'], first['data']['launchers']), (str(batch), [str(batch)]))
        self.assertEqual([row['path'] for row in first['data']['kept']], [str(shell)])
        self.assertIn('launcher.collision', [warning['code'] for warning in first['warnings']])
        self.assertEqual(shell.read_text(encoding='utf-8'), '#!/bin/sh\necho mine\n')
        shell.unlink()
        again = self.call('self', 'install', '--bin-dir', directory)  # Rerunning adds the missing sh launcher.
        self.assertTrue(again['changed'])
        self.assertEqual([(action['kind'], action['path'], action['status']) for action in again['actions']], [('launcher.install', str(shell), 'applied')])
        raw = shell.read_bytes()
        self.assertTrue(raw.startswith(b'#!/bin/sh\n# MASK owned launcher v1\n'))
        self.assertNotIn(b'\r', raw)
        self.assertNotIn(b'\\', raw)
        self.assertIn(ENTRY.as_posix().encode(), raw)
        launchers = json.loads((self.home / 'state.json').read_text(encoding='utf-8'))['launchers']
        self.assertEqual(sorted(launchers), sorted([str(batch), str(shell)]))
        self.assertFalse(self.call('self', 'install', '--bin-dir', directory)['changed'])
        bash = git_bash()
        if bash is not None:
            run = subprocess.run([str(bash), '-c', 'command -v mask >/dev/null && mask self status --home "$1" --json', 'bash', str(self.home)],
                                 capture_output=True, encoding='utf-8', env=dict(os.environ, PATH=str(directory) + os.pathsep + os.environ['PATH']))
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertEqual(json.loads(run.stdout)['data']['program_root'], str(ENTRY.parent))
        shell.write_bytes(raw + b'# mine\n')
        partial = self.call('self', 'uninstall')
        self.assertEqual((partial['data']['removed'], [row['path'] for row in partial['data']['kept']]), ([str(batch)], [str(shell)]))
        self.assertTrue(shell.exists())
        shell.write_bytes(raw)
        self.assertEqual(self.call('self', 'uninstall')['data']['removed'], [str(shell)])
        self.assertFalse(shell.exists() or batch.exists())
        both = self.call('self', 'install', '--bin-dir', directory)
        self.assertEqual([action['path'] for action in both['actions']], [str(batch), str(shell)])
        self.assertEqual(sorted(self.call('self', 'uninstall')['data']['removed']), sorted([str(batch), str(shell)]))


def git_bash():
    """Git for Windows' own bash, never the WSL launcher in System32."""
    found = shutil.which('git')
    if not found:
        return None
    base = Path(found).resolve().parent.parent
    for root in (base, base.parent):
        for candidate in (root / 'bin' / 'bash.exe', root / 'usr' / 'bin' / 'bash.exe'):
            if candidate.is_file():
                return candidate
    return None
