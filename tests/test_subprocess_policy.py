import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
import mask_core as c
from tests.support import Fixture


class SubprocessTests(Fixture):
    @unittest.skipUnless(os.name == 'nt', 'Windows suspended Job Object prerequisite path')
    def test_windows_assignment_failure_never_runs_suspended_program(self):
        from mask_process import WindowsJob
        marker = self.base / 'uncontained'
        real = subprocess.Popen
        def fake(command, **kwargs):
            return real([sys.executable, '-c', 'from pathlib import Path;Path(' + repr(str(marker)) + ').touch()'], **kwargs)
        with patch.object(c.subprocess, 'Popen', fake), patch.object(WindowsJob, 'start', side_effect=OSError('fixture assignment refusal')):
            with self.assertRaises(c.MaskError) as error:
                c.git(self.source, 'status')
        self.assertEqual(error.exception.code, 'git.containment_unavailable')
        self.assertFalse(marker.exists())

    @unittest.skipUnless(os.name == 'nt', 'Windows suspended Job Object prerequisite path')
    def test_windows_spawn_resumes_its_recorded_thread_without_a_system_snapshot(self):
        # MASK-0134: a snapshot of every thread on the machine cost about 68 ms per Git process.
        from mask_process import WindowsJob
        with patch.object(WindowsJob, 'sole_thread', side_effect=OSError('fixture: no snapshot expected')) as walk:
            self.assertEqual(c.git(self.source, 'rev-parse', '--is-inside-work-tree'), 'true')
        walk.assert_not_called()
        real = WindowsJob.sole_thread
        with patch('mask_process.recorded_spawn', lambda start: (start(), None)), \
                patch.object(WindowsJob, 'sole_thread', autospec=True, side_effect=real) as walk:
            self.assertEqual(c.git(self.source, 'rev-parse', '--is-inside-work-tree'), 'true')
        walk.assert_called_once()

    @unittest.skipUnless(os.name == 'nt', 'Windows suspended Job Object prerequisite path')
    def test_windows_thread_of_another_process_is_never_resumed(self):
        import threading
        marker = self.base / 'uncontained'
        real = subprocess.Popen
        def fake(command, **kwargs):
            return real([sys.executable, '-c', 'from pathlib import Path;Path(' + repr(str(marker)) + ').touch()'], **kwargs)
        with patch.object(c.subprocess, 'Popen', fake), \
                patch('mask_process.recorded_spawn', lambda start: (start(), threading.get_native_id())):
            with self.assertRaises(c.MaskError) as error:
                c.git(self.source, 'status')
        self.assertEqual(error.exception.code, 'git.containment_unavailable')
        self.assertFalse(marker.exists())

    def test_input_reaches_the_child_and_stdin_closes(self):
        data = b'stdin bytes\n' * 20000  # Larger than a pipe buffer, so writing must not wait for the child to finish.
        expected = subprocess.run(['git', 'hash-object', '--stdin'], input=data, capture_output=True, check=True).stdout.decode().strip()
        self.assertEqual(c.git(self.source, 'hash-object', '--stdin', input=data), expected)

    def test_pipe_read_failure_never_returns_a_partial_observation(self):
        real = subprocess.Popen
        class BrokenPipe:
            def __init__(self, stream): self.stream = stream
            def read1(self, size): raise OSError('fixture read failure')
            def close(self): self.stream.close()
        def fake(command, **kwargs):
            process = real([sys.executable, '-c', 'import time;time.sleep(20)'], **kwargs)
            process.stdout = BrokenPipe(process.stdout)
            return process
        with patch.object(c.subprocess, 'Popen', fake), self.assertRaises(c.MaskError) as error:
            c.git(self.source, 'status', '--porcelain')
        self.assertEqual(error.exception.code, 'git.output_failed')

    def test_output_limit_contains_helper_after_leader_exit(self):
        ready, marker = self.base / 'started', self.base / 'survived-exit'
        child = ('import time;from pathlib import Path;Path(' + repr(str(ready)) + ').touch();'
                 'time.sleep(1);Path(' + repr(str(marker)) + ').touch()')
        parent = ('import subprocess,sys,time;from pathlib import Path;'
                  'subprocess.Popen([sys.executable,"-c",' + repr(child) + '],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);'
                  '\nwhile not Path(' + repr(str(ready)) + ').exists():time.sleep(0.01)\n'
                  'sys.stdout.buffer.write(b"x"*100000);sys.stdout.flush()')
        real = subprocess.Popen
        def fake(command, **kwargs):
            return real([sys.executable, '-c', parent], **kwargs)
        with patch.object(c.subprocess, 'Popen', fake), self.assertRaises(c.MaskError) as error:
            c.git(self.source, 'status', max_output=32)
        self.assertEqual(error.exception.code, 'git.output_limit')
        self.assertTrue(ready.exists())
        time.sleep(1.1)
        self.assertFalse(marker.exists())

    def test_output_limit_terminates_spawned_tree_and_bounds_both_streams(self):
        for stream in ('stdout', 'stderr'):
            marker = self.base / ('survived-' + stream)
            child = 'import time;from pathlib import Path;time.sleep(1);Path(' + repr(str(marker)) + ').touch()'
            parent = ('import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",' + repr(child) + ']);'
                      'sys.' + stream + '.buffer.write(b"x"*1000000);sys.' + stream + '.flush();time.sleep(20)')
            real = subprocess.Popen
            def fake(command, **kwargs):
                return real([sys.executable, '-c', parent], **kwargs) if command[0] == 'git' else real(command, **kwargs)
            with patch.object(c.subprocess, 'Popen', fake), self.assertRaises(c.MaskError) as error:
                c.git(self.source, 'fetch', max_output=32, timeout=5)
            self.assertEqual(error.exception.code, 'git.output_limit')
            time.sleep(1.1)
            self.assertFalse(marker.exists())

    def test_repository_selection_sanitized_and_auth_redacted(self):
        with patch.dict(os.environ, {'GIT_DIR': str(self.project / '.git'), 'GIT_WORK_TREE': str(self.project)}):
            self.assertEqual(c.git(self.source, 'rev-parse', '--show-toplevel'), str(self.source).replace('\\', '/'))
        real = subprocess.Popen
        captured = {}
        def fake(command, **kwargs):
            captured.update(kwargs['env'])
            return real([sys.executable, '-c', "import sys;sys.stderr.write('Authentication failed https://token-secret@example.invalid');sys.exit(1)"], **kwargs)
        with patch.object(c.subprocess, 'Popen', fake):
            with self.assertRaises(c.MaskError) as error: c.git(self.source, 'fetch')
        self.assertEqual(error.exception.code, 'git.auth_required')
        self.assertNotIn('token-secret', str(error.exception.as_dict()))
        self.assertEqual(captured['GIT_TERMINAL_PROMPT'], '0')
        self.assertEqual(captured['GCM_INTERACTIVE'], 'never')

    def test_timeout_terminates_spawned_helper_tree(self):
        marker = self.base / 'helper-survived'
        ready = self.base / 'helper-ready'
        child = "import time;from pathlib import Path;Path(" + repr(str(ready)) + ").write_text('ready');time.sleep(2);Path(" + repr(str(marker)) + ").write_text('unsafe')"
        parent = 'import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",' + repr(child) + ']);time.sleep(20)'
        real = subprocess.Popen
        def fake(command, **kwargs):
            return real([sys.executable, '-c', parent], **kwargs) if command[0] == 'git' else real(command, **kwargs)
        with patch.object(c.subprocess, 'Popen', fake):
            with self.assertRaises(c.MaskError) as error: c.git(self.source, 'fetch', timeout=0.7, mutating=True)
        self.assertEqual(error.exception.code, 'git.timeout')
        self.assertTrue(ready.exists())
        time.sleep(2)
        self.assertFalse(marker.exists())


class SpawnBudgetTests(Fixture):
    """Every Git question is a process. These bounds fail loudly when a change reintroduces per-call latency or fan-out."""

    @unittest.skipIf(os.name == 'nt', 'Windows process creation alone exceeds this bound')
    def test_a_fast_child_is_noticed_without_waiting_out_a_poll_tick(self):
        # Twenty finished children used to cost twenty fixed 10 ms sleeps; the bound is loose enough for a loaded machine.
        c.git(self.source, 'rev-parse', 'HEAD')
        baseline = min(self.timed(lambda: subprocess.run(['git', '-C', str(self.source), 'rev-parse', 'HEAD'],
                                                        stdout=subprocess.DEVNULL, check=True)) for _ in range(20))
        best = min(self.timed(lambda: c.git(self.source, 'rev-parse', 'HEAD')) for _ in range(20))
        self.assertLess(best - baseline, 0.008, 'supervision should not add a polling tick to native process startup')

    def timed(self, action):
        start = time.perf_counter()
        action()
        return time.perf_counter() - start

    def test_one_install_stays_within_its_git_process_budget(self):
        import contextlib
        import io
        import mask
        self.init()
        spawned, real = [], c.contained_run
        def counting(command, *args, **kwargs):
            spawned.append(command)
            return real(command, *args, **kwargs)
        with patch.object(c, 'contained_run', counting), patch.dict(os.environ, self.environment()), \
                contextlib.redirect_stdout(io.StringIO()) as stdout:
            code = __import__('tests.engine_cli', fromlist=['main']).main(['install', 'alpha', '--project', str(self.project), '--home', str(self.home), '--json'])
        self.assertEqual(code, 0, stdout.getvalue())
        # 96 with the task pipeline: review/preparation rechecks and final readiness
        # add root observations to the original 83-call transaction budget.
        self.assertLessEqual(len(spawned), 100, 'install spawns more Git processes than its budget; look for repeated object-addressed questions')
