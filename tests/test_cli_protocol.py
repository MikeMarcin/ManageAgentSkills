import json
from pathlib import Path
import subprocess
import sys
import unittest

ENTRY = Path(__file__).resolve().parents[1] / 'mask.py'


class ProtocolTests(unittest.TestCase):
    def invoke(self, *args):
        run = subprocess.run([sys.executable, str(ENTRY), *args], capture_output=True, encoding="utf-8")
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
        self.assertTrue(commands['update']['network'])
        self.assertFalse(commands['apply']['network'])
        self.assertTrue(commands['project.require']['plan_guard'])
        self.assertTrue(any(a['name'] == 'ids' and a['repeatable'] for a in commands['project.require']['arguments']))

    def test_parser_errors_are_json(self):
        for args in [('wat',), ('init',), ('capabilities', '--wat'), ('project', 'set'), ('project', 'set', '--clear', '--skill', 'foo'), ('project', 'register', '.', '--project', '.')]:
            with self.subTest(args=args):
                run, data = self.invoke(*args, '--json')
                self.assertEqual(run.returncode, 2)
                self.assertEqual(data['error']['code'], 'invocation.invalid')
                self.assertFalse(data['changed'])

    def test_help_and_version(self):
        for args in [('--help',), ('project', 'require', '--help'), ('--version',)]:
            self.assertTrue(self.invoke(*args, '--json')[1]['ok'])

    def test_operand_json_is_not_a_flag(self):
        run = subprocess.run([sys.executable, str(ENTRY), 'skill', 'show', '--', '--json'], capture_output=True, encoding="utf-8")
        self.assertEqual(run.stdout, '')
        self.assertNotEqual(run.returncode, 0)
