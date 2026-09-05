import json
import os
from pathlib import Path
import subprocess
import sys
import time
from unittest.mock import patch
import mask_core as c
from tests.support import Fixture


class SubprocessTests(Fixture):
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
