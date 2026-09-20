"""Unavailable registered scopes are observations, not a global filesystem crash."""
import json
import subprocess
import sys

from tests.support import Fixture, TAP, ENTRY


class DoctorUnavailableTests(Fixture):
    def test_missing_project_and_personal_scopes_are_reported_and_preserved(self):
        self.init()
        self.install(TAP + '/alpha')
        self.install(TAP + '/beta', user=True)
        self.call('integration', 'approve', '--project', self.project)
        missing = self.base / 'deleted worktree'
        self.project.rename(missing)
        before = self.snapshot()
        result = self.call('doctor', '--all', '--check', cwd=self.base, code=7)
        self.assertEqual(result['error']['code'], 'state.drift')
        errors = result['data']['issues']
        unavailable = next(e for e in errors if e['code'] == 'project.unavailable')
        self.assertEqual(unavailable['details']['root'], str(self.project))
        self.assertIn('unregister', unavailable['remediation'][0]['message'])
        self.assertIn(str(self.personal), result['data']['workflow'])
        self.assertEqual(before, self.snapshot())
        repaired = self.call('ensure', '--all', '--repair', '--offline', '--yes', cwd=self.base, code=4)
        rows = {r['root']: r for r in repaired['data']['repair_results']}
        self.assertTrue(rows[str(self.personal)]['ok'])
        self.assertEqual(rows[str(self.project)]['error']['code'], 'project.unavailable')
        self.personal.rename(self.base / 'held-personal')
        before = self.snapshot()
        result = self.call('doctor', '--check', cwd=self.base, code=7)
        self.assertEqual({e['code'] for e in result['data']['issues']}, {'project.unavailable', 'user.unavailable'})
        self.assertEqual(before, self.snapshot())

    def test_top_level_oserror_reports_paths_and_errno(self):
        code = '''
import sys
sys.path.insert(0, sys.argv[1])
import mask
def fail(*args):
    raise FileNotFoundError(2, 'fixture failure', '/fixture/missing-root')
mask.dispatch = fail
raise SystemExit(__import__('tests.engine_cli', fromlist=['main']).main(['doctor', '--json']))
'''
        result = subprocess.run([sys.executable, '-c', code, str(ENTRY.parent)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 5)
        details = json.loads(result.stdout)['error']['details']
        self.assertEqual(details, dict(errno=2, filename='/fixture/missing-root'))
