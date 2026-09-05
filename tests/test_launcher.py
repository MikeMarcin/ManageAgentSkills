import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tests.support import Fixture, ENTRY


class LauncherTests(Fixture):
    def test_install_dry_run_refusal_and_native_forwarding(self):
        directory = self.base / 'bin spaced ü'
        before = self.snapshot()
        self.call('self', 'install', '--bin-dir', directory, '--dry-run')
        self.assertEqual(before, self.snapshot())
        result = self.call('self', 'install', '--bin-dir', directory)
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

    def test_program_update_separate_and_incompatible_refused(self):
        remote = self.base / 'ManageAgentSkills.git'
        program = self.base / 'program spaced ü'
        self.git(self.base, 'init', '--bare', str(remote))
        self.git(self.base, 'clone', str(remote), str(program))
        self.git(program, 'checkout', '-b', 'main')
        for name in ('mask.py', 'mask_core.py', 'mask_fs.py', 'mask_git.py', 'mask_install.py'):
            shutil.copyfile(ENTRY.parent / name, program / name)
        shutil.copytree(ENTRY.parent / 'schemas', program / 'schemas')
        self.git(program, 'config', 'user.name', 'Fixture'); self.git(program, 'config', 'user.email', 'fixture@example.invalid')
        self.git(program, 'add', '.'); self.git(program, 'commit', '-m', 'program'); self.git(program, 'push', '-u', 'origin', 'main')
        author = self.base / 'program author'
        self.git(self.base, 'clone', '--branch', 'main', str(remote), str(author))
        self.git(author, 'config', 'user.name', 'Fixture'); self.git(author, 'config', 'user.email', 'fixture@example.invalid')
        self.init(); self.declare(); self.call('project', 'register', self.project, '--apply')
        source_head = self.git(self.source, 'rev-parse', 'HEAD'); before = self.snapshot(self.project)
        state_before = (self.home / 'state.json').read_bytes()
        with (author / 'mask.py').open('a') as handle: handle.write('\n# compatible fixture update\n')
        self.git(author, 'add', 'mask.py'); self.git(author, 'commit', '-m', 'compatible'); self.git(author, 'push', 'origin', 'main')
        def invoke(code=0):
            run = subprocess.run([sys.executable, '-B', str(program / 'mask.py'), 'self', 'update', '--home', str(self.home), '--json'], capture_output=True, encoding='utf-8')
            self.assertEqual(run.returncode, code, run.stdout + run.stderr)
            return json.loads(run.stdout)
        self.assertTrue(invoke()['data']['next_invocation_required'])
        self.assertEqual(source_head, self.git(self.source, 'rev-parse', 'HEAD'))
        self.assertEqual(before, self.snapshot(self.project))
        self.assertEqual(state_before, (self.home / 'state.json').read_bytes())
        self.assertFalse(invoke()['changed'])
        path = author / 'mask.py'; path.write_text(path.read_text().replace('PROTOCOL_VERSION = 1', 'PROTOCOL_VERSION = 2'))
        self.git(author, 'add', 'mask.py'); self.git(author, 'commit', '-m', 'incompatible'); self.git(author, 'push', 'origin', 'main')
        self.assertEqual(invoke(4)['error']['code'], 'source.candidate_invalid')
