import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ENTRY = Path(__file__).resolve().parents[1] / 'mask.py'


class ProtocolTests(unittest.TestCase):
    def setUp(self):
        # A private machine home, personal home and working directory: never the developer's own state or this checkout.
        self.temp = tempfile.TemporaryDirectory(prefix='mask-protocol-')
        self.addCleanup(self.temp.cleanup)
        self.options = dict(capture_output=True, encoding='utf-8', cwd=self.temp.name,
                            env=dict(os.environ, MASK_HOME=str(Path(self.temp.name) / 'machine'), HOME=self.temp.name, USERPROFILE=self.temp.name))

    def invoke(self, *args):
        run = subprocess.run([sys.executable, str(ENTRY), *args], **self.options)
        payload = json.loads(run.stdout)
        self.assertEqual(run.stderr, '')
        self.assertEqual(payload['ok'], run.returncode == 0)
        self.assertEqual(payload['schema_version'], 1)
        return run, payload

    def test_capabilities_and_global_placement(self):
        first = self.invoke('--json', 'capabilities')[1]
        second = self.invoke('capabilities', '--json')[1]
        self.assertEqual(first, second)
        commands = {c['name']: c for c in first['data']['commands']}
        self.assertTrue(commands['capabilities']['implemented'])
        self.assertTrue(commands['upgrade']['network'])
        self.assertFalse(commands['apply']['network'])
        self.assertTrue(commands['project.require']['plan_guard'])
        self.assertTrue(any(a['name'] == 'ids' and a['repeatable'] for a in commands['project.require']['arguments']))

    def test_parser_errors_are_json(self):
        for args in [('wat',), ('init', '--source', '.'), ('capabilities', '--wat'), ('project', 'set'), ('project', 'set', '--clear', '--skill', 'foo'), ('project', 'register', '.', '--project', '.')]:
            with self.subTest(args=args):
                run, data = self.invoke(*args, '--json')
                self.assertEqual(run.returncode, 2)
                self.assertEqual(data['error']['code'], 'invocation.invalid')
                self.assertFalse(data['changed'])

    def test_help_and_version(self):
        for args in [('--help',), ('project', 'require', '--help'), ('--version',)]:
            self.assertTrue(self.invoke(*args, '--json')[1]['ok'])

    def test_operand_json_is_not_a_flag(self):
        run = subprocess.run([sys.executable, str(ENTRY), 'skill', 'show', '--', '--json'], **self.options)
        self.assertEqual(run.stdout, '')
        self.assertNotEqual(run.returncode, 0)
