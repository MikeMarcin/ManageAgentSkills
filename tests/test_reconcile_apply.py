import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

import mask_core as c
import mask_resolve as r
import mask_store as store
from tests.support import ENTRY, TAP
from tests.support import Fixture


class ApplyTests(Fixture):
    """Tap-first: a registered, not yet applied v2 consumer of the fixture tap (the engine invariants once proven on a live checkout)."""
    def setUp(self):
        super().setUp(); self.init(); self.declare_pinned(); self.call('project', 'register', self.project)

    def artifact(self, identifier='alpha'):
        """The store artifact root and package directory of the locked identifier."""
        row = next(row for row in c.read_json(self.project / '.mask.lock.json')['packages'] if row['id'] == identifier)
        return store.location(self.home, row['payload_digest'], identifier)

    def test_convergence_guard_noop_owned_removal(self):
        preview = self.call('plan')
        self.call('apply', '--expect-plan-hash', preview['data']['plan_hash'])
        leaf = self.project / '.agents/skills/alpha'
        self.assertTrue(leaf.is_symlink()); self.assertTrue(leaf.is_dir())
        before = self.snapshot()
        self.assertFalse(self.call('apply')['changed']); self.assertEqual(before, self.snapshot())
        self.call('remove', 'alpha', '--project', self.project)
        self.assertFalse(leaf.exists()); self.assertFalse(leaf.is_symlink())
        self.assertTrue(leaf.parent.is_dir())
        self.assertEqual(c.read_json(self.project / '.mask.json')['skills'], [])

    def test_prospective_collision_keeps_declaration_and_other_links(self):
        self.call('apply')
        target = self.project / '.agents/skills/beta'; target.mkdir()
        (target / 'mine').write_text('owned by user')
        before = self.snapshot()
        self.assertEqual(self.install('beta', code=4)['error']['code'], 'target.collision')
        self.assertEqual(before, self.snapshot())
        self.assertTrue((self.project / '.agents/skills/alpha').is_symlink())

    def test_stale_guard_after_control_change_and_changed_owned_link(self):
        preview = self.call('plan')
        # Both controls change between preview and apply: alpha for codex only, with its coherent lock.
        declaration = c.read_json(self.project / '.mask.json')
        declaration['skills'][0]['agents'] = ['codex']
        lock = c.read_json(self.project / '.mask.lock.json')
        (self.project / '.mask.json').write_text(json.dumps(declaration) + '\n')
        (self.project / '.mask.lock.json').write_text(c.text_json(dict(lock, selection_digest=r.selection_digest(declaration))))
        self.assertEqual(self.call('apply', '--expect-plan-hash', preview['data']['plan_hash'], code=4)['error']['code'], 'plan.stale')
        self.assertFalse((self.project / '.agents').exists())
        self.assertFalse((self.home / 'pending.json').exists())
        self.call('apply')
        self.assertFalse((self.project / '.claude/skills/alpha').exists())
        leaf = self.project / '.agents/skills/alpha'; leaf.unlink()
        elsewhere = self.base / 'elsewhere'; elsewhere.mkdir()
        leaf.symlink_to(elsewhere, target_is_directory=True)
        before = self.snapshot()
        self.assertEqual(self.call('apply', code=4)['error']['code'], 'target.drift')
        self.assertEqual(before, self.snapshot())

    def test_missing_owned_link_is_recreated(self):
        self.call('apply'); leaf = self.project / '.agents/skills/alpha'; raw = os.readlink(leaf); leaf.unlink()
        self.call('apply'); self.assertTrue(leaf.is_symlink())
        self.assertEqual(os.readlink(leaf), raw)

    def repair_blocked_link(self, *args, winerror=448, fault='', code=0):
        # Inject only the Windows traversal error. The public CLI still creates and
        # removes real directory symlinks and uses its real journal and lockfiles.
        script = """
import os
from pathlib import Path
import sys
from unittest.mock import patch

import mask
import mask_fs

leaf = Path(sys.argv[1]) / '.agents/skills/alpha'
winerror, fault = int(sys.argv[2]), sys.argv[3]
stat, symlink_to = Path.stat, Path.symlink_to
blocked = winerror != 0

def probe(path, *args, **kwargs):
    if blocked and path == leaf / 'SKILL.md':
        error = OSError('injected Windows link traversal failure')
        error.winerror = winerror
        raise error
    return stat(path, *args, **kwargs)

def recreate(path, *args, **kwargs):
    global blocked
    symlink_to(path, *args, **kwargs)
    if path == leaf and fault != 'still_blocked':
        blocked = False

def checkpoint(label):
    if label == 'link_unlinked' and fault == 'crash':
        os._exit(99)
    if label == 'link' and fault == 'late_failure':
        raise OSError('injected late failure')

with patch.object(Path, 'stat', probe), patch.object(Path, 'symlink_to', recreate):
    mask_fs.checkpoint = checkpoint
    raise SystemExit(mask.main(['repair', '--project', sys.argv[1], '--offline', '--json', *sys.argv[4:]]))
"""
        run = subprocess.run([sys.executable, '-B', '-c', script, str(self.project), str(winerror), fault, *args],
                             cwd=ENTRY.parent, capture_output=True, encoding='utf-8', env=self.environment())
        self.assertEqual(run.returncode, code, (run.stdout, run.stderr))
        self.assertEqual(run.stderr, '')
        if code != 99:
            return json.loads(run.stdout)

    def test_repair_replaces_only_the_owned_link_blocked_by_winerror_448(self):
        self.call('apply')
        leaf = self.project / '.agents/skills/alpha'
        other = self.project / '.claude/skills/alpha'
        other_identity = other.lstat()
        before = self.snapshot()
        preview = self.repair_blocked_link('--dry-run')
        self.assertEqual([(a['kind'], a['path']) for a in preview['actions']], [('link.replace', str(leaf))])
        self.assertEqual(self.snapshot(), before)
        self.assertFalse(self.repair_blocked_link('--dry-run', winerror=5)['would_change'])
        approval = ('--approve-plan', preview['data']['plan_hash'])
        self.assertEqual(self.repair_blocked_link(*approval, winerror=0, code=4)['error']['code'], 'plan.stale')
        applied = self.repair_blocked_link(*approval)
        self.assertEqual((applied['transaction'], applied['actions'][0]['status']), ('committed', 'applied'))
        self.assertEqual(os.readlink(leaf), before[str(leaf.relative_to(self.base))][1])
        self.assertTrue((leaf / 'SKILL.md').is_file())
        other_after = other.lstat()
        self.assertEqual((other_after.st_ino, other_after.st_mtime_ns), (other_identity.st_ino, other_identity.st_mtime_ns))
        self.assertFalse(self.repair_blocked_link(winerror=0)['would_change'])

    def test_winerror_448_repair_recovers_from_an_interrupted_replacement(self):
        self.call('apply')
        leaf = self.project / '.agents/skills/alpha'
        for mode in ('--complete', '--rollback'):
            with self.subTest(mode=mode):
                self.repair_blocked_link(fault='crash', code=99)
                self.assertFalse(leaf.is_symlink())
                leaf.mkdir()
                self.assertEqual(self.call('recover', mode, code=8)['error']['code'], 'recovery.conflict')
                self.assertTrue(leaf.is_dir())
                leaf.rmdir()
                recovered = self.call('recover', mode)
                self.assertTrue((leaf / 'SKILL.md').is_file())
                if mode == '--rollback':
                    self.assertEqual(recovered['data']['retained_link_repairs'], [str(leaf)])
                self.assertFalse((self.home / 'pending.json').exists())

    def test_winerror_448_repair_reports_failed_and_retained_replacements(self):
        self.call('apply')
        failed = self.repair_blocked_link(fault='still_blocked', code=5)
        self.assertEqual(failed['error']['code'], 'target.untrusted_mount_point')
        self.assertFalse(failed['changed'])
        retained = self.repair_blocked_link(fault='late_failure', code=5)
        self.assertEqual(retained['transaction'], 'rolled_back')
        self.assertTrue(retained['changed'])
        self.assertEqual(retained['data']['retained_link_repairs'], [str(self.project / '.agents/skills/alpha')])
        self.assertFalse((self.home / 'pending.json').exists())

    def test_dangling_owned_link_is_removed(self):
        self.call('apply'); leaf = self.project / '.agents/skills/alpha'
        # The owned link dangles once its store artifact is gone.
        self.artifact()[0].rename(self.base / 'retained-artifact')
        self.assertTrue(leaf.is_symlink()); self.assertFalse(leaf.exists())
        self.call('remove', 'alpha', '--project', self.project)
        self.assertFalse(leaf.is_symlink())
        self.assertFalse((self.home / 'pending.json').exists())

    def test_dangling_owned_link_with_an_uncached_commit_refuses_without_a_journal(self):
        self.call('apply'); leaf = self.project / '.agents/skills/alpha'
        self.artifact()[0].rename(self.base / 'retained-artifact')
        # The approved cache no longer holds the locked commit: the whole tap cache is gone.
        Path(c.read_json(self.home / 'config.json')['sources'][TAP]['cache']).rename(self.base / 'retained-cache')
        before = self.snapshot()
        refused = self.call('remove', 'alpha', '--project', self.project, code=4)
        self.assertEqual((refused['error']['code'], refused['transaction']), ('artifact.unavailable', 'not_started'))
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.home / 'pending.json').exists())
        self.assertTrue(leaf.is_symlink())

    def test_unverifiable_old_artifact_refuses_before_any_journal(self):
        # Recovery verifies both artifact sides (RFC-MASK-0008), so apply refuses the old side's typed error before pending.json exists.
        self.call('apply'); leaf = self.project / '.agents/skills/alpha'
        self.artifact()[0].rename(self.base / 'retained-artifact')
        # Both controls drop alpha coherently; apply prepares only the new (empty) lock, so only the journal preflight sees the old side.
        declaration = dict(c.read_json(self.project / '.mask.json'), skills=[])
        lock = dict(c.read_json(self.project / '.mask.lock.json'), packages=[], selection_digest=r.selection_digest(declaration))
        (self.project / '.mask.json').write_text(json.dumps(declaration) + '\n')
        (self.project / '.mask.lock.json').write_text(c.text_json(lock))
        before = self.snapshot()
        self.assertEqual(self.call('apply', code=4)['error']['code'], 'artifact.unavailable')
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.home / 'pending.json').exists())
        self.assertTrue(leaf.is_symlink())

    def test_late_failure_rolls_back_links_but_reports_retained_directories(self):
        code = """
import sys
sys.path.insert(0, sys.argv[1])
import mask, mask_fs
fired = False
def fail(label):
    global fired
    if label == 'link' and not fired:
        fired = True
        raise OSError('injected late failure')
mask_fs.checkpoint = fail
raise SystemExit(__import__('tests.engine_cli', fromlist=['main']).main(['apply', '--project', sys.argv[2], '--home', sys.argv[3], '--json']))
"""
        run = subprocess.run([sys.executable, '-B', '-c', code, str(ENTRY.parent), str(self.project), str(self.home)], capture_output=True, encoding='utf-8', env=self.environment())
        data = json.loads(run.stdout)
        self.assertEqual(run.returncode, 5, run.stdout)
        self.assertEqual(data['transaction'], 'rolled_back'); self.assertTrue(data['changed'])
        self.assertFalse((self.project / '.agents/skills/alpha').is_symlink())
        self.assertFalse((self.home / 'pending.json').exists())
        self.assertTrue(data['data']['retained_directories'])

    def test_replaced_parent_refuses(self):
        self.call('apply')
        parent = self.project / '.agents'; moved = self.project / '.agents-retained'
        parent.rename(moved)
        parent.symlink_to(moved, target_is_directory=True)
        before = self.snapshot()
        self.assertEqual(self.call('apply', code=4)['error']['code'], 'target.parent_link')
        self.assertEqual(before, self.snapshot())

    @unittest.skipUnless(os.name == 'nt', 'native Windows symlink error mapping')
    def test_windows_missing_privilege_refusal(self):
        import mask_fs
        from unittest.mock import patch
        error = OSError('required privilege not held'); error.winerror = 1314
        entry = dict(root=str(self.project), relative='.agents/skills/alpha', before=None, after=mask_fs.creation_link_text(self.artifact()[1]))
        with patch.object(Path, 'symlink_to', side_effect=error):
            with self.assertRaises(mask_fs.c.MaskError) as caught:
                mask_fs.set_link(entry, 'after')
        self.assertEqual(caught.exception.code, 'target.symlink_unsupported')

    def test_unregister_preserves_declaration(self):
        self.call('apply'); self.call('project', 'unregister', self.project)
        self.assertTrue((self.project / '.mask.json').is_file())
        self.assertFalse((self.project / '.agents/skills/alpha').is_symlink())

    def test_all_projects_preflight_before_first_effect(self):
        other = self.base / 'second-project'; other.mkdir()
        self.declare_pinned(root=other, fetch=False)
        self.call('project', 'register', other)
        collision = other / '.claude/skills/alpha'; collision.mkdir(parents=True)
        # Warm the content store first: apply prepares artifacts outside the writer, and this test is about consumer effects.
        for root in (self.project, other):
            self.call('source', 'fetch', '--locked', '--project', root)
        before = self.snapshot()
        self.call('apply', '--all', code=4)
        self.assertEqual(before, self.snapshot())
        self.assertFalse((self.project / '.agents').exists())
