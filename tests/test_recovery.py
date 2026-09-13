import json
import os
from pathlib import Path
import subprocess
import sys
from tests.support import Fixture, ENTRY
from tests.test_manifest_registry import declare_pinned


class CrashFixture(Fixture):
    def crash(self, label, *command):
        script = """
import sys,os
sys.path.insert(0, sys.argv[1])
import mask,mask_fs
mask_fs.checkpoint = lambda label: os._exit(99) if label == sys.argv[2] else None
mask.main(sys.argv[3:])
"""
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), label, *(command or ('apply',)), '--project', str(self.project), '--home', str(self.home), '--json'], capture_output=True, text=True)
        self.assertEqual(run.returncode, 99, (run.stdout, run.stderr))
        self.assertTrue((self.home / 'pending.json').is_file())


class RecoveryTests(CrashFixture):
    """Tap-first: crash, rollback, doctor and busy-lock behavior on a registered, not yet applied v2 consumer."""
    def setUp(self):
        super().setUp(); self.init(); declare_pinned(self); self.call('project', 'register', self.project)

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


class LegacyRecoveryTests(CrashFixture):
    """Legacy live-checkout starting state until MASK-0100 retires this behavior (v1 require crash, clone-path adoption)."""
    def setUp(self):
        super().setUp(); self.legacy_init(); self.declare(); self.call('project', 'register', self.project)

    def test_restart_after_manifest_and_state(self):
        for label in ('manifest', 'state'):
            with self.subTest(label=label):
                self.crash(label, 'project', 'require', 'beta', '--apply')
                self.call('recover', '--complete')
                self.assertEqual(self.call('project', 'show')['data']['manifest']['skills'], ['alpha', 'beta'])
                self.call('project', 'unrequire', 'beta', '--apply')

    def test_adopt_exact_link_without_replacing_it(self):
        leaf = self.project / '.agents/skills/alpha'; leaf.parent.mkdir(parents=True)
        relative = os.path.relpath(self.source / 'skills/alpha', leaf.parent)
        leaf.symlink_to(relative, target_is_directory=True)
        before = os.readlink(leaf)
        preview = self.call('link', 'adopt', '--project', self.project, '--skill', 'alpha', '--target', 'codex', '--expect-source', self.source / 'skills/alpha', '--dry-run')
        self.call('link', 'adopt', '--project', self.project, '--skill', 'alpha', '--target', 'codex', '--expect-source', self.source / 'skills/alpha', '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertEqual(before, os.readlink(leaf))
        self.call('apply'); self.assertEqual(before, os.readlink(leaf))

    def test_mid_apply_external_manifest_edit_is_preserved(self):
        script = """
import sys,json
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import mask,mask_fs
edited = False
def checkpoint(label):
    global edited
    if label == 'link' and not edited:
        edited = True
        Path(sys.argv[3], '.mask.json').write_text('{"schema_version":1,"skills":[]}')
mask_fs.checkpoint = checkpoint
raise SystemExit(mask.main(['project','require','beta','--apply','--home',sys.argv[2],'--project',sys.argv[3],'--json']))
"""
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), str(self.home), str(self.project)], capture_output=True, encoding='utf-8')
        self.assertEqual(run.returncode, 8, run.stdout + run.stderr)
        self.assertEqual(json.loads((self.project / '.mask.json').read_text())['skills'], [])
        self.assertTrue((self.home / 'pending.json').exists())
        self.call('recover', '--complete', code=8)
