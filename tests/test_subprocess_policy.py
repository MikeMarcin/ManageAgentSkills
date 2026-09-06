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
