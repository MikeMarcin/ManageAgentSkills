"""Human review and live terminal progress across real public lifecycle tasks."""
import io
import json
import os
from pathlib import Path
import re
import select
import subprocess
import sys
import threading
import time
import unittest
from unittest.mock import patch

import mask
import mask_present as present
import mask_progress as progress
from tests.public_support import PublicFixture, ENTRY
from tests import test_cli_v2 as lifecycle_cases
from tests.test_setup import SetupFixture


class TerminalPresentation(unittest.TestCase):
    def test_color_is_terminal_only_and_respects_no_color(self):
        stream = io.StringIO()
        stream.isatty = lambda: True
        with patch.dict(os.environ, {'TERM': 'xterm'}, clear=True):
            self.assertIn('\x1b[1;32m', present.paint('Ready.\n', stream))
            diagnostic = 'Example usage:\n  mask list\n\nError: Unknown command: mask blah\n'
            painted = present.paint(diagnostic, stream, tone='error')
            self.assertTrue(painted.startswith('Example usage:\n'))
            self.assertIn('\x1b[1;31mError: Unknown command: mask blah\x1b[0m\n', painted)
            with patch.dict(os.environ, {'NO_COLOR': ''}):
                self.assertEqual(present.paint('Ready.\n', stream), 'Ready.\n')
                self.assertEqual(present.paint(diagnostic, stream, tone='error'), diagnostic)
            stream.isatty = lambda: False
            self.assertEqual(present.paint('Ready.\n', stream), 'Ready.\n')

    def test_review_groups_links_but_keeps_setup_and_exact_replacements(self):
        # Action paths are native: MASK writes str(Path), so a POSIX literal never sits under a Windows root.
        repo, store = os.path.abspath(os.sep + 'repo'), os.path.join(os.path.abspath(os.sep + 'private'), 'store')
        actions = [dict(kind='link.create', path=os.path.join(repo, '.agents', 'skills', name), target=os.path.join(store, 'long-digest', name)) for name in ('one', 'two')]
        actions += [dict(kind='state.record'), dict(kind='lock.write', path=os.path.join(repo, '.mask.lock.json')),
                    dict(kind='setup.run', root=repo, skill='one', coordinate='tap/one', fingerprint='123456789abc',
                         path=os.path.join(store, 'hash', 'payload', 'one', 'scripts', 'setup.py'), interpreter='/python', native_roles=['codex/worker']),
                    dict(kind='file.backup_replace', path=os.path.join(repo, '.codex', 'agents', 'worker.toml'))]
        replaced = 'back up and replace ' + os.path.join(repo, '.codex', 'agents', 'worker.toml')
        text = present.render_confirmation(dict(kind='task', scope=[repo], actions=actions), mask.result('upgrade'))
        self.assertIn('2 skill links', text)
        self.assertIn('scripts/setup.py', text)  # A package-relative path is POSIX on every OS.
        self.assertIn('tap/one (123456789abc)', text)
        self.assertIn('codex/worker', text)
        self.assertIn(replaced, text)
        self.assertNotIn(store, text)
        self.assertNotIn('state.record', text)
        output = mask.result('upgrade', True)
        output['would_change'] = True
        output['data'].update(review=dict(kind='task', scope=[repo], actions=actions), plan_hash='review-hash')
        preview = present.render(output)
        self.assertIn(replaced, preview)
        self.assertIn('--approve-plan review-hash', preview)
        self.assertNotIn(store, preview)

    def test_progress_flushes_heartbeat_pauses_and_stops_on_exception(self):
        class Stream(io.StringIO):
            def isatty(self): return True
            def flush(self): self.flushed.set()
        stream = Stream(); stream.flushed = threading.Event()
        with patch.dict(os.environ, {'NO_COLOR': '1'}):
            with self.assertRaises(ValueError):
                with progress.reporting(True, 'Preparing', stream=stream, interval=.02):
                    self.assertTrue(stream.flushed.wait(.2))
                    deadline = time.monotonic() + 1
                    while '0s' not in stream.getvalue() and time.monotonic() < deadline:
                        time.sleep(.01)
                    self.assertIn('Preparing... 0s', stream.getvalue())
                    with progress.paused():
                        paused = stream.getvalue(); time.sleep(.06)
                        self.assertEqual(stream.getvalue(), paused)
                    raise ValueError('fixture')
            stopped = stream.getvalue(); time.sleep(.04)
            self.assertEqual(stream.getvalue(), stopped)
            self.assertIsNone(progress._active)

    def test_partial_result_uses_setup_outcomes_not_obsolete_diagnostics(self):
        output = mask.result('upgrade')
        output.update(ok=False, changed=True, transaction='partial', error=dict(code='recovery.required', message='Stopped',
            details={'cause': dict(code='recovery.conflict', message='Workspace changed', details={'root': '/two'})}, remediation=[]))
        output['data'].update(workflow_readiness_observation='before_setup', workflow_readiness=[dict(root='/one', scope='project', skills=[dict(skill='x', workflow='declared', complete=False, roles=[dict(state='setup_required',path='obsolete.toml')])])],
            setup=dict(actions=[dict(root='/one',subject='tap/x:setup',state='published'),dict(root='/two',subject='tap/x:setup',state='partial'),dict(root='/three',subject='tap/x:setup',state='granted')]))
        text=present.render_error(output)
        self.assertNotIn('obsolete.toml',text)
        self.assertNotIn('needs attention',text)
        for phrase in ('/one  tap/x:setup  done','/two  tap/x:setup  recovery needed','/three  tap/x:setup  not started','cause: Workspace changed','root: /two'):
            self.assertIn(phrase,text)


class PublicProgress(PublicFixture):
    bootstrap = lifecycle_cases.CliV2.bootstrap
    raw = lifecycle_cases.CliV2.raw
    setUp = lifecycle_cases.SetupV2.setUp
    write_script = SetupFixture.write_script
    reviewed = lifecycle_cases.SetupV2.reviewed

    @unittest.skipUnless(os.name == 'posix', 'POSIX terminal journey')
    def test_json_on_terminal_stays_one_document_without_color_or_progress(self):
        code, text = self.terminal('install', 'implement-rfc', '--dry-run', '--json', answer=[])
        self.assertEqual(code, 0, text)
        self.assertNotIn('\x1b', text)
        self.assertEqual(len(text.strip().splitlines()), 1)
        self.assertTrue(json.loads(text)['ok'])

    @unittest.skipUnless(os.name == 'posix', 'POSIX terminal journey')
    def test_upgrade_reports_activity_before_slow_setup_finishes(self):
        self.write_script(before="    if (args.repo_root / 'slow-setup').exists():\n        while not (args.repo_root / 'release-setup').exists():\n            time.sleep(.03)\n")
        self.publish('slow setup fixture')
        self.machine('tap', 'fetch')
        self.reviewed('install', 'implement-rfc')
        (self.project / '.codex/agents/rfc-integrator.toml').unlink()
        (self.project / 'slow-setup').touch()
        import pty
        master, slave = pty.openpty()
        process = subprocess.Popen([sys.executable, '-B', str(ENTRY), 'upgrade', '--no-update'], cwd=self.project,
                                   env=self.environment({'NO_COLOR':'1'}), stdin=slave, stdout=slave, stderr=slave)
        os.close(slave)
        text = ''; answered = released = False
        try:
            deadline=time.monotonic()+50
            while time.monotonic()<deadline:
                if select.select([master],[],[],.1)[0]:
                    try: chunk=os.read(master,65536)
                    except OSError: break
                    if not chunk: break
                    text+=chunk.decode('utf-8','replace')
                if '[y/N]' in text and not answered:
                    os.write(master,b'y\n'); answered=True
                if re.search(r'Running .*\.\.\. \d+s',text) and not released:
                    self.assertIsNone(process.poll(),text)
                    (self.project/'release-setup').touch(); released=True
                if process.poll() is not None:
                    break
            self.assertTrue(released,text)
            self.assertEqual(process.wait(timeout=10),0,text)
            self.assertLess(text.index('Approved; rechecking'),text.index('Running '))
            self.assertNotIn('\x1b',text)
        finally:
            if process.poll() is None:
                process.kill();process.wait()
            os.close(master)

    def test_public_partial_failure_retains_causes_and_publication_state(self):
        preview=self.machine('install','implement-rfc','--dry-run')
        script='''
import sys
sys.path.insert(0, sys.argv[1])
import mask, mask_fs, mask_core as c
original=mask_fs.restore
def fail_setup(pending, home, side, **kwargs):
    if 'setup' in pending:
        c.fail('fixture.' + side, 'Fixture publication refusal', 8, root=pending['setup']['root'])
    return original(pending,home,side,**kwargs)
mask_fs.restore=fail_setup
raise SystemExit(mask.main(sys.argv[2:]))
'''
        run=subprocess.run([sys.executable,'-B','-c',script,str(ENTRY.parent),'install','implement-rfc','--no-update','--approve-plan',preview['data']['plan_hash'],'--json'],
                           cwd=self.project,env=self.environment(),capture_output=True,text=True,timeout=60)
        self.assertEqual(run.stderr,'')
        result=json.loads(run.stdout)
        self.assertEqual(result['error']['code'],'recovery.required',result)
        self.assertEqual(result['error']['details']['cause']['code'],'fixture.after')
        self.assertEqual(result['error']['details']['rollback']['code'],'fixture.before')
        self.assertEqual(result['data']['setup']['actions'][0]['state'],'partial')
        self.assertEqual(result['data']['workflow_readiness_observation'],'before_setup')
        self.assertTrue((self.home/'pending.json').exists())
        self.assertTrue(any(a['status'] == 'failed' and a.get('effects') == 'unknown' for a in result['actions']))
        schema = json.loads((ENTRY.parent / 'schemas/result.schema.json').read_text(encoding='utf-8'))
        statuses = schema['properties']['actions']['items']['properties']['status']['enum']
        self.assertTrue(all(action['status'] in statuses for action in result['actions']))
