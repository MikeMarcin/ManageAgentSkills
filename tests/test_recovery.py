import json
import subprocess
import sys

import mask_core as c
from tests.support import Fixture, ENTRY


class CrashFixture(Fixture):
    def crash(self, label, *command):
        script = """
import sys,os
sys.path.insert(0, sys.argv[1])
import mask,mask_fs
mask_fs.checkpoint = lambda label: os._exit(99) if label == sys.argv[2] else None
__import__('tests.engine_cli', fromlist=['main']).main(sys.argv[3:])
"""
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), label, *(command or ('apply',)), '--project', str(self.project), '--home', str(self.home), '--json'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 99, (run.stdout, run.stderr))
        self.assertTrue((self.home / 'pending.json').is_file())


class RecoveryTests(CrashFixture):
    """Tap-first: crash, rollback, doctor and busy-lock behavior on a registered, not yet applied v2 consumer."""
    def setUp(self):
        super().setUp(); self.init(); self.declare_pinned(); self.call('project', 'register', self.project)

    def test_crash_complete_and_inspect_are_explicit(self):
        self.crash('link')
        before = self.snapshot()
        self.assertIsNotNone(self.call('recover', '--inspect')['data']['pending'])
        self.assertEqual(before, self.snapshot())
        self.call('apply', code=8)
        self.call('recover', '--complete')
        self.assertFalse((self.home / 'pending.json').exists())
        self.assertFalse(self.call('apply')['changed'])

    def test_rollback_and_changed_leaf_preservation(self):
        self.crash('link')
        leaf = self.project / '.agents/skills/alpha'
        self.assertTrue(leaf.is_symlink())
        leaf.unlink(); leaf.mkdir(); (leaf / 'mine').write_text('preserve')
        before = self.snapshot()
        self.call('recover', '--rollback', code=8)
        self.assertEqual(before, self.snapshot())
        (leaf / 'mine').unlink(); leaf.rmdir()  # test-owned collision only
        self.call('recover', '--rollback')
        self.assertFalse(leaf.is_symlink())

    def test_doctor_is_observational_and_check_detects_drift(self):
        before = self.snapshot()
        self.assertFalse(self.call('doctor')['data']['healthy'])
        self.call('doctor', '--check', code=7)
        self.assertEqual(before, self.snapshot())
        self.call('apply')
        self.assertTrue(self.call('doctor', '--check')['data']['healthy'])

    def test_busy_lock(self):
        script = """
import sys,time
sys.path.insert(0,sys.argv[1])
from pathlib import Path
import mask_core
with mask_core.writer_lock(Path(sys.argv[2])):
    print('ready',flush=True)
    sys.stdin.read()
"""
        process = subprocess.Popen([sys.executable, '-B', '-c', script, str(ENTRY.parent), str(self.home)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        try:
            self.assertEqual(process.stdout.readline().strip(), 'ready')
            self.assertEqual(self.call('apply', code=6)['error']['code'], 'lock.busy')
        finally:
            process.communicate('')
        self.call('apply')

    def test_restart_after_declaration_lock_and_state(self):
        # Each typed control checkpoint of a journaled install: declaration, lock, then state.
        for label in ('manifest', 'lock', 'state'):
            with self.subTest(label=label):
                self.crash(label, 'install', 'beta')
                self.call('recover', '--complete')
                self.assertEqual([row['id'] for row in c.read_json(self.project / '.mask.json')['skills']], ['alpha', 'beta'])
                self.assertEqual([row['id'] for row in c.read_json(self.project / '.mask.lock.json')['packages']], ['alpha', 'beta'])
                self.assertTrue((self.project / '.agents/skills/beta').is_symlink())
                self.assertFalse(self.call('apply')['changed'])
                self.call('remove', 'beta', '--project', self.project)

    def test_mid_apply_external_declaration_edit_is_preserved(self):
        script = """
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import mask,mask_fs
edited = False
def checkpoint(label):
    global edited
    if label == 'link' and not edited:
        edited = True
        Path(sys.argv[3], '.mask.json').write_text('{"schema_version":2,"sources":{},"skills":[]}')
mask_fs.checkpoint = checkpoint
raise SystemExit(__import__('tests.engine_cli', fromlist=['main']).main(['install','beta','--home',sys.argv[2],'--project',sys.argv[3],'--json']))
"""
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), str(self.home), str(self.project)], capture_output=True, encoding='utf-8', env=self.environment())
        self.assertEqual(run.returncode, 8, run.stdout + run.stderr)
        self.assertEqual(json.loads((self.project / '.mask.json').read_text())['skills'], [])
        self.assertTrue((self.home / 'pending.json').exists())
        before = self.snapshot()
        self.call('recover', '--complete', code=8)
        self.call('recover', '--rollback', code=8)
        self.assertEqual(before, self.snapshot())
