import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tests.support import Fixture, ENTRY

# The runtime modules update requires in a program candidate (mask_install.validate_program).
PROGRAM_MODULES = ('mask.py', 'mask_core.py', 'mask_fs.py', 'mask_git.py', 'mask_install.py', 'mask_ensure.py', 'mask_integration.py', 'mask_report.py', 'mask_present.py', 'mask_sources.py', 'mask_packages.py', 'mask_process.py', 'mask_provenance.py', 'mask_resolve.py', 'mask_store.py', 'mask_pinned.py', 'mask_selection.py', 'mask_adapters.py', 'mask_consent.py', 'mask_task.py', 'mask_workflow.py', 'mask_setup.py', 'mask_repair.py', 'mask_update.py', 'mask_cli.py', 'mask_lifecycle.py', 'mask_cleanup.py', 'mask_pin.py')

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
raise SystemExit(mask.main(['update', '--home', sys.argv[2], '--json']))
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

    def fault(self, program, fault, code):
        run = subprocess.run([sys.executable, '-B', '-c', FAULT, str(program), str(self.home), fault], capture_output=True, encoding='utf-8')
        self.assertEqual(run.returncode, code, run.stdout + run.stderr)
        return json.loads(run.stdout) if run.stdout.strip() else None

    def pending(self):
        return json.loads((self.home / 'pending.json').read_text(encoding='utf-8'))

    def test_program_update_separate_and_incompatible_refused(self):
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
        schema = author / 'schemas/machine.schema.json'
        original_schema = schema.read_bytes()
        changed_schema = json.loads(original_schema)
        changed_schema['title'] = 'Changed contract fixture'
        schema.write_text(json.dumps(changed_schema))
        self.git(author, 'add', 'schemas/machine.schema.json'); self.git(author, 'commit', '-m', 'changed schema'); self.git(author, 'push', 'origin', 'main')
        self.assertEqual(self.program(program, 'update', code=4)['error']['code'], 'source.candidate_invalid')
        schema.write_bytes(original_schema)
        path = author / 'mask.py'; path.write_text(path.read_text().replace('PROTOCOL_VERSION = 2', 'PROTOCOL_VERSION = 3'))
        self.git(author, 'add', 'mask.py', 'schemas/machine.schema.json'); self.git(author, 'commit', '-m', 'incompatible'); self.git(author, 'push', 'origin', 'main')
        self.assertEqual(self.program(program, 'update', code=4)['error']['code'], 'source.candidate_invalid')

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
