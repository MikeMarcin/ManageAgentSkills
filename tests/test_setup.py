"""Approved staged setup through the public CLI (MASK-0089; RFC-MASK-0019 AC04/AC05, cases W06-W12).

Every case runs ``mask ensure`` as a subprocess against a disposable source and
consumer built from the retained generated-package fixture (model
``fixture-model-do-not-run``; never a real host). The fixture entrypoint is
replaced per scenario by a variant that records every launch in a sentinel file,
so "never executes" is proven by the sentinel staying absent. Prompts run on a
POSIX pseudoterminal; noninteractive proofs use pipes. No helper approves setup,
renders roles or applies a change on behalf of the command under test.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import unittest

from tests.legacy_support import write_json
from tests.public_support import CONSUMER_CONTEXT, ENTRY, PACK, PublicFixture
from tests.support import TAP

GENERATED = PACK / 'fixtures/generated-package'
COORDINATE = TAP + '/implement-rfc'
SUBJECT = COORDINATE + ':prepare-roles'

SCRIPT = '''#!/usr/bin/env python3
"""Test variant of the retained fixture generator: records each launch, then stages roles."""
import argparse, json, os, subprocess, sys, time
from pathlib import Path
import helper

SENTINEL = Path({sentinel!r})

def main():
    with SENTINEL.open('a', encoding='utf-8') as stream:
        stream.write(str(os.getpid()) + '\\n')
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo-root', type=Path, required=True)
    parser.add_argument('--output-root', type=Path, required=True)
    parser.add_argument('--request-file', type=Path, required=True)
    args = parser.parse_args()
    request = json.loads(args.request_file.read_text(encoding='utf-8'))
    assert request['schema'] == 'mask.setup-request.v1' and request['action'] == 'prepare-roles'
    assert all(len(row['sha256']) == 64 for row in request['inputs']), request['inputs']
{before}
    for role in request['native_roles']:
        directory = args.output_root / role['agent']
        directory.mkdir(exist_ok=True)
        directory.joinpath(helper.filename(role)).write_text(helper.render(role), encoding='utf-8')
{after}
    print('fixture stage written')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
'''

HELPER = '''"""Imported helper: its bytes are part of the frozen package."""
def filename(role):
    return role['name'] + ('.toml' if role['agent'] == 'codex' else '.md')

def render(role):
    if role['agent'] == 'codex':
        return 'name = "%s"\\nmodel = "fixture-model-do-not-run"\\n' % role['name']
    return '---\\nname: %s\\nmodel: fixture-model-do-not-run\\n---\\nFixture only.\\n' % role['name']
'''


class SetupFixture(PublicFixture):
    """Tap whose implement-rfc is the generated package (setup action), plus an approved, declared, pinned consumer without links."""

    def setUp(self):
        super().setUp()
        self.package = self.source / 'skills/implement-rfc'
        shutil.rmtree(self.package)
        shutil.copytree(GENERATED, self.package)
        self.sentinel = self.base / 'setup-launches.txt'
        self.write_script()
        self.publish('generated package')
        shutil.copytree(CONSUMER_CONTEXT, self.project / '.mask')
        self.declare_consumer(self.project, ['implement-rfc'])
        self.assertTrue(self.machine('integration', 'approve', '--project', self.project)['ok'])
        self.lock = self.project / '.mask/generated/implement-rfc/native-roles.lock.json'

    def declare_consumer(self, root, skills, *, user=False):
        """A registered v2 consumer of the fixture tap with a lock and no links: declaration, fetch, lock, hydrate, register.

        The locked package bytes are placed in the store, as the live checkout used to exist, so a dry-run preview
        examines the same package the applying run does; nothing is linked, approved or run.
        """
        write_json(self.home / 'user.json' if user else root / '.mask.json',
                   dict(schema_version=2, sources={TAP: dict(repository=self.upstream.as_uri(), packages='skills')},
                        default_agents=['claude', 'codex'], skills=[dict(source=TAP, id=skill) for skill in skills]))
        scope = ['--user'] if user else ['--project', root]
        self.assertTrue(self.machine('source', 'fetch', TAP)['ok'])
        self.assertTrue(self.machine('lock', *scope)['ok'])
        self.assertTrue(self.machine('source', 'fetch', '--locked', *scope)['ok'])
        self.assertTrue(self.machine('user', 'register')['ok'] if user else self.machine('project', 'register', '--project', root)['ok'])

    def deployed(self):
        """The locked implement-rfc package in the store: setup freezes and runs these bytes, never the author checkout."""
        row = next(row for row in json.loads((self.project / '.mask.lock.json').read_text(encoding='utf-8'))['packages'] if row['id'] == 'implement-rfc')
        return self.home / 'store/v1' / row['payload_digest'].removeprefix('sha256:') / 'payload/implement-rfc'

    def written_bytecode(self):
        """Bytecode in the deployed package that its locked commit does not contain; MASK writes none of its own."""
        commit = next(row['commit'] for row in json.loads((self.project / '.mask.lock.json').read_text(encoding='utf-8'))['packages'] if row['id'] == 'implement-rfc')
        committed = set()
        for line in self.git(self.source, 'ls-tree', '-r', '--name-only', commit, 'skills/implement-rfc').splitlines():
            parts = line.split('/')[2:]
            committed.update('/'.join(parts[:index]) for index in range(1, len(parts) + 1))
        root = self.deployed()
        return sorted(relative for relative in (path.relative_to(root).as_posix() for path in root.rglob('*')
                      if '__pycache__' in path.parts or path.suffix in ('.pyc', '.pyo')) if relative not in committed)

    def write_script(self, before='', after='', timeout=None):
        (self.package / 'scripts/prepare_fixture_roles.py').write_text(SCRIPT.format(sentinel=str(self.sentinel), before=before, after=after), encoding='utf-8')
        (self.package / 'scripts/helper.py').write_text(HELPER, encoding='utf-8')
        descriptor = self.package / 'mask-workflow.json'
        value = json.loads(descriptor.read_text(encoding='utf-8'))
        value['setup'][0]['package_inputs'] = ['scripts/prepare_fixture_roles.py', 'scripts/helper.py']
        if timeout is not None:
            value['setup'][0]['timeout_seconds'] = timeout
        descriptor.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

    def commit(self, message):
        """Publish the package edit and adopt it: fetch the tap, then the pinned update of the consumer (it never runs setup)."""
        self.publish(message)
        self.assertTrue(self.machine('source', 'fetch', TAP)['ok'])
        return self.machine('update', '--project', self.project)

    def launches(self):
        return len(self.sentinel.read_text(encoding='utf-8').splitlines()) if self.sentinel.exists() else 0

    def roles(self):
        return sorted(path.relative_to(self.project).as_posix() for path in self.project.glob('.*/agents/*'))

    def roles_of(self, result):
        return {(row['agent'], row['name']): row for entry in result['data']['workflow_readiness'] for skill in entry['skills'] for row in skill['roles']}

    def links(self):
        return sorted(path.relative_to(self.project).as_posix() for path in self.project.glob('.*/skills/*') if path.is_symlink())

    def assert_nothing_published(self):
        self.assertEqual(self.roles(), [])
        self.assertFalse(self.lock.exists())
        self.assertFalse((self.home / 'pending.json').exists())
        self.assertFalse((self.home / 'staging').exists())

    def assert_published(self, result=None):
        self.assertEqual(self.roles(), ['.claude/agents/rfc-integrator.md', '.codex/agents/rfc-integrator.toml'])
        self.assertEqual((self.project / '.codex/agents/rfc-integrator.toml').read_text(encoding='utf-8'), 'name = "rfc-integrator"\nmodel = "fixture-model-do-not-run"\n')
        lock = json.loads(self.lock.read_text(encoding='utf-8'))
        self.assertEqual((lock['schema'], lock['coordinate'], len(lock['roles'])), ('mask.native-role-lock.v1', COORDINATE, 2))
        self.assertFalse((self.home / 'pending.json').exists())
        self.assertFalse((self.home / 'staging').exists())
        self.assertFalse(list(self.package.glob('**/__pycache__')))
        self.assertEqual(self.written_bytecode(), [])
        if result is not None:
            self.assertTrue(result['ok'], result)
            self.assertEqual(result['data']['scope_readiness'][0]['workflow'], 'complete')
            self.assertEqual([row['state'] for row in result['data']['setup']['actions']], ['published'])

    def setup_rows(self, result):
        return result['data']['setup']['actions']


class NoninteractiveSetupTests(SetupFixture):
    def test_existing_unmanaged_roles_block_setup_before_prompt_or_execution(self):
        originals = {
            '.claude/agents/rfc-integrator.md': '# repository role\n',
            '.codex/agents/rfc-integrator.toml': 'name = "rfc-integrator"\nmodel = "custom"\n',
        }
        for relative, content in originals.items():
            path = self.project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
        for _ in range(2):
            preview = self.machine('ensure', '--project', self.project, '--dry-run')
            run = self.machine('ensure', '--project', self.project, '--expect-plan-hash', preview['data']['plan_hash'], '--allow-setup', SUBJECT)
            self.assertEqual(run['error']['code'], 'workflow.incomplete')
            self.assertEqual(self.setup_rows(run)[0]['state'], 'blocked')
            self.assertEqual(set(self.setup_rows(run)[0]['paths']), set(originals))
            self.assertNotIn('confirmation', run['data']['setup'])
            self.assertEqual(self.launches(), 0)
            self.assertFalse(self.lock.exists())
        human = self.human('ensure', '--project', self.project)
        self.assertEqual(human.returncode, 4)
        self.assertIn(str(self.project), human.stderr)
        self.assertIn('2 role file(s)', human.stderr)
        self.assertIn('Repeating setup or adding --yes will not overwrite', human.stderr)
        self.assertNotIn('Run this setup?', human.stderr)
        for relative, content in originals.items():
            self.assertEqual((self.project / relative).read_text(encoding='utf-8'), content)
            self.assertIn(relative, human.stderr)

    def test_json_reports_the_proposal_commits_links_and_runs_nothing(self):
        result = self.machine('ensure', '--project', self.project)
        self.assertEqual(result['error']['code'], 'workflow.incomplete')
        self.assertEqual(result['transaction'], 'committed')
        self.assertEqual(len(self.links()), 2)
        rows = self.setup_rows(result)
        self.assertEqual([(row['state'], row['subject'], row['granted_by']) for row in rows], [('consent_required', SUBJECT, None)])
        proposal = result['data']['setup']['confirmation']
        self.assertEqual((proposal['kind'], proposal['reason'], proposal['subjects'], proposal['plan_hash']), ('package.setup', 'setup.required', [SUBJECT], result['data']['plan_hash']))
        self.assertEqual(proposal['actions'][0]['path'], str(self.deployed() / 'scripts/prepare_fixture_roles.py'))
        self.assertIn('--allow-setup', result['error']['remediation'][0]['message'])
        self.assertEqual(self.launches(), 0)
        self.assert_nothing_published()

    def test_all_scope_reaches_the_setup_proposal_like_an_explicit_project(self):
        result = self.machine('ensure', '--all')
        self.assertEqual(result['error']['code'], 'workflow.incomplete')
        self.assertEqual([(row['state'], row['subject'], row['root']) for row in self.setup_rows(result)],
                         [('consent_required', SUBJECT, str(self.project))])
        self.assertEqual(self.launches(), 0)
        self.assert_nothing_published()

    def test_check_dry_run_yes_and_events_never_run_package_code(self):
        self.machine('ensure', '--project', self.project)  # Commits the links so every preview below shares one frozen plan.
        plan_hash = self.machine('ensure', '--project', self.project, '--dry-run')['data']['plan_hash']
        for options in (['--check'], ['--dry-run'], ['--yes'], ['--event', 'startup'], ['--event', 'post-checkout'],
                        ['--check', '--expect-plan-hash', plan_hash, '--allow-setup', SUBJECT],
                        ['--dry-run', '--expect-plan-hash', plan_hash, '--allow-setup', SUBJECT],
                        ['--event', 'startup', '--expect-plan-hash', plan_hash, '--allow-setup', SUBJECT]):
            with self.subTest(options=options):
                result = self.machine('ensure', '--project', self.project, *options)
                self.assertFalse(result['ok'])
                self.assertEqual(result['error']['code'], 'workflow.incomplete', result['error'])
                state = self.setup_rows(result)[0]['state']
                self.assertIn(state, ('not_run', 'consent_required'))
                self.assertEqual(state, 'consent_required' if options == ['--yes'] else 'not_run')
                self.assertEqual(self.launches(), 0)
                self.assert_nothing_published()
        human = self.human('ensure', '--project', self.project, stdin=subprocess.DEVNULL)
        self.assertEqual(human.returncode, 4, human.stderr)
        self.assertIn(f'setup {SUBJECT} in ', human.stderr)
        self.assertIn(': consent_required', human.stderr)
        self.assertIn('not sandboxed', human.stderr)
        self.assertNotIn('[y/N]', human.stderr)
        self.assertEqual(self.launches(), 0)
        self.assert_nothing_published()

    def test_check_mode_binds_the_expected_plan_hash_like_dry_run(self):
        self.machine('ensure', '--project', self.project)
        for mode in ('--check', '--dry-run'):
            with self.subTest(mode=mode):
                result = self.machine('ensure', '--project', self.project, mode, '--expect-plan-hash', 'deadbeef', '--allow-setup', SUBJECT)
                self.assertEqual(result['error']['code'], 'plan.stale', result.get('error'))
                self.assertEqual(self.launches(), 0)
        self.assert_nothing_published()

    def test_refused_setup_journal_leaves_no_stage(self):
        self.machine('ensure', '--project', self.project)  # Commits the links so the next preview is the frozen plan.
        plan_hash = self.machine('ensure', '--project', self.project)['data']['plan_hash']
        script = """
import sys
sys.path.insert(0, sys.argv[1])
import mask, mask_core, mask_fs
def refuse(pending, home):
    raise mask_core.MaskError('internal.invariant', 'injected journal refusal', 10)
mask_fs.validate_pending = refuse
raise SystemExit(mask.main(sys.argv[2:]))
"""
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), 'ensure', '--project', str(self.project), '--json',
                              '--expect-plan-hash', plan_hash, '--allow-setup', SUBJECT], capture_output=True, text=True, env=self.environment())
        self.assertEqual(run.returncode, 10, run.stdout + run.stderr)
        self.assertEqual(json.loads(run.stdout)['error']['code'], 'internal.invariant')
        self.assertFalse((self.home / 'pending.json').exists())
        self.assertEqual(self.launches(), 0)
        self.assert_nothing_published()

    def test_exact_plan_hash_with_named_action_runs_and_verifies(self):
        preview = self.machine('ensure', '--project', self.project)  # Commits the links; the setup proposal is reported.
        plan_hash = preview['data']['plan_hash']
        stale = self.machine('ensure', '--project', self.project, '--expect-plan-hash', plan_hash, '--allow-setup', SUBJECT)
        self.assertEqual(stale['error']['code'], 'plan.stale', 'the link commit changed the plan; automation must review the new preview')
        plan_hash = self.machine('ensure', '--project', self.project)['data']['plan_hash']
        # Foreign or partial grants name nothing.
        for options in (['--expect-plan-hash', plan_hash], ['--allow-setup', SUBJECT],
                        ['--expect-plan-hash', plan_hash, '--allow-setup', f'{TAP}/other:prepare-roles'],
                        ['--expect-plan-hash', plan_hash, '--allow-setup', 'other/implement-rfc:prepare-roles'],
                        ['--expect-plan-hash', plan_hash, '--allow-setup', f'{COORDINATE}:other']):
            with self.subTest(options=options):
                result = self.machine('ensure', '--project', self.project, *options)
                self.assertEqual(result['error']['code'], 'workflow.incomplete')
                self.assertEqual(self.setup_rows(result)[0]['state'], 'consent_required')
                self.assertEqual(self.launches(), 0)
        malformed = self.raw('ensure', '--project', self.project, '--json', '--expect-plan-hash', plan_hash, '--allow-setup', 'prepare-roles')
        self.assertEqual(malformed.returncode, 2)
        self.assertEqual(json.loads(malformed.stdout)['error']['code'], 'invocation.invalid')
        self.assertEqual(self.launches(), 0)
        self.assert_nothing_published()
        done = self.machine('ensure', '--project', self.project, '--expect-plan-hash', plan_hash, '--allow-setup', SUBJECT)
        self.assert_published(done)
        self.assertEqual(self.setup_rows(done)[0]['granted_by'], 'allow-setup')
        self.assertEqual([action['kind'] for action in done['actions']], ['native_role.write', 'native_role.write', 'state.record', 'native_role_lock.write'])
        self.assertEqual(self.launches(), 1)
        # The published roles are managed outputs vouched for by the lock; a plain rerun runs nothing.
        again = self.machine('ensure', '--project', self.project)
        self.assertTrue(again['ok'])
        self.assertFalse(again['changed'])
        self.assertNotIn('setup', again['data'])
        self.assertEqual(self.launches(), 1)
        # The lock-vouched generated role reports its configured route, still separate from host loading.
        for role in self.roles_of(again).values():
            self.assertEqual(role['state'], 'ok')
            self.assertEqual(role['route']['model'], 'fixture-model-do-not-run', role)
            self.assertEqual(role['host_load'], 'not_verified')
        # W09: a changed imported helper invalidates the prepared lock; nothing runs without fresh consent.
        (self.package / 'scripts/helper.py').write_text(HELPER + '\n# changed\n', encoding='utf-8')
        self.commit('helper changed')
        changed = self.machine('ensure', '--project', self.project)
        self.assertEqual(changed['error']['code'], 'workflow.incomplete')
        self.assertEqual(self.setup_rows(changed)[0]['state'], 'consent_required')
        self.assertEqual(self.launches(), 1)
        self.assertEqual(self.roles(), ['.claude/agents/rfc-integrator.md', '.codex/agents/rfc-integrator.toml'])


class SetupFailureTests(SetupFixture):
    def approve(self):
        """The unattended recipe: review a dry-run preview, then bind its exact hash and name the action."""
        plan_hash = self.machine('ensure', '--project', self.project, '--dry-run')['data']['plan_hash']
        return self.machine('ensure', '--project', self.project, '--expect-plan-hash', plan_hash, '--allow-setup', SUBJECT)

    def test_timeout_stops_the_owned_tree_and_publishes_nothing(self):
        survived = self.base / 'child-survived'
        child = f"import time; from pathlib import Path; time.sleep(3); Path({str(survived)!r}).touch()"
        self.write_script(before=f"    subprocess.Popen([sys.executable, '-c', {child!r}])\n    time.sleep(30)\n", timeout=1)
        self.commit('slow script')
        started = time.monotonic()
        result = self.approve()
        self.assertLess(time.monotonic() - started, 20)
        self.assertEqual(result['error']['code'], 'setup.failed')
        self.assertEqual(result['error']['details']['reason'], 'timeout')
        row = self.setup_rows(result)[0]
        self.assertEqual((row['state'], row['reason']), ('failed', 'timeout'))
        self.assertEqual(self.launches(), 1)
        self.assert_nothing_published()
        time.sleep(3.5)
        self.assertFalse(survived.exists(), 'the spawned child was terminated with the process tree')
        self.assertEqual(self.launches(), 1, 'no automatic rerun')

    def test_unsuccessful_exit_and_output_overflow_are_bounded_failures(self):
        self.write_script(after="    sys.stderr.write('generator refused\\n'); return 3\n")
        self.commit('failing script')
        result = self.approve()
        self.assertEqual(result['error']['code'], 'setup.failed')
        self.assertEqual(result['error']['details']['exit_status'], 3)
        self.assertIn('generator refused', self.setup_rows(result)[0]['stderr'])
        self.assert_nothing_published()
        self.write_script(before="    sys.stdout.write('x' * 200000); sys.stdout.flush()\n")
        self.commit('noisy script')
        result = self.approve()
        self.assertEqual(result['error']['details']['reason'], 'output_limit')
        self.assert_nothing_published()
        self.assertEqual(self.launches(), 2)

    def test_extra_symlink_traversing_and_unsupported_outputs_never_reach_the_consumer(self):
        valid = self.base / 'valid-role.toml'
        valid.write_text('name = "rfc-integrator"\nmodel = "fixture-model-do-not-run"\n', encoding='utf-8')
        cases = dict(
            extra="    (args.output_root / 'notes.txt').write_text('extra')\n",
            extra_directory="    (args.output_root / 'codex' / 'nested').mkdir()\n",
            symlink=f"    target = args.output_root / 'codex' / 'rfc-integrator.toml'; target.unlink(); os.symlink({str(valid)!r}, target)\n",
            traversing="    (args.output_root / '..' / 'escaped.toml').write_text('escaped')\n",
            unsupported="    (args.output_root / 'codex' / 'rfc-integrator.toml').write_text('name = \"rfc-integrator\"\\n[hooks]\\nenabled = true\\n')\n",
            renamed="    (args.output_root / 'codex' / 'rfc-integrator.toml').write_text('name = \"rfc-critical-integrator\"\\n')\n",
            missing="    (args.output_root / 'claude' / 'rfc-integrator.md').unlink()\n",
        )
        for index, (name, after) in enumerate(cases.items(), start=1):
            with self.subTest(case=name):
                self.write_script(after=after)
                self.commit(name)
                result = self.approve()
                self.assertEqual(result['error']['code'], 'setup.outputs_invalid', result['error'])
                self.assertEqual(self.setup_rows(result)[0]['state'], 'refused')
                self.assertEqual(self.launches(), index)
                self.assert_nothing_published()
        self.assertFalse((self.project / 'escaped.toml').exists())

    def test_new_collision_during_staging_is_preserved_not_overwritten(self):
        self.write_script(before="    (args.repo_root / '.claude' / 'agents').mkdir(parents=True, exist_ok=True)\n"
                                 "    (args.repo_root / '.claude' / 'agents' / 'rfc-integrator.md').write_text('# appeared during staging\\n')\n")
        self.commit('side effect')
        result = self.approve()
        self.assertEqual(result['error']['code'], 'workflow.incomplete')
        row = self.setup_rows(result)[0]
        self.assertEqual(row['state'], 'partial')
        self.assertIn('claude/rfc-integrator: modified', row['detail'])
        self.assertEqual((self.project / '.claude/agents/rfc-integrator.md').read_text(encoding='utf-8'), '# appeared during staging\n')
        self.assertEqual((self.project / '.codex/agents/rfc-integrator.toml').read_text(encoding='utf-8'), 'name = "rfc-integrator"\nmodel = "fixture-model-do-not-run"\n')
        self.assertTrue(self.lock.exists())
        self.assertFalse((self.home / 'pending.json').exists())
        # The lock vouches only for the role that actually published; recording the preserved
        # destination would make every later run report a mismatch the operator cannot resolve.
        lock = json.loads(self.lock.read_text(encoding='utf-8'))
        self.assertEqual([(row['agent'], row['name']) for row in lock['roles']], [('codex', 'rfc-integrator')])
        rerun = self.approve()
        self.assertEqual(rerun['error']['code'], 'workflow.incomplete')
        preserved = self.roles_of(rerun)[('claude', 'rfc-integrator')]
        self.assertEqual(preserved['state'], 'setup_required')
        self.assertIn('unmanaged file occupies this destination', preserved['detail'])
        self.assertEqual(self.roles_of(rerun)[('codex', 'rfc-integrator')]['state'], 'ok')
        self.assertEqual(self.launches(), 1, 'A preserved file must not prompt another futile setup run')
        self.assertEqual(self.setup_rows(rerun)[0]['state'], 'blocked')
        self.assertEqual([(row['agent'], row['name']) for row in json.loads(self.lock.read_text(encoding='utf-8'))['roles']], [('codex', 'rfc-integrator')])

    def test_deleted_managed_role_is_released_as_deleted_not_preserved(self):
        self.assert_published(self.approve())
        (self.project / '.codex/agents/rfc-integrator.toml').unlink()
        result = self.machine('ensure', '--project', self.project, '--check')
        self.assertEqual(result['error']['code'], 'readiness.drift')
        released = [row for row in result['warnings'] if row['code'] == 'native_role.released']
        self.assertEqual([row['reason'] for row in released], ['deleted outside MASK'])
        self.assertIn('was deleted outside MASK', released[0]['message'])
        self.assertNotIn('preserved', released[0]['message'])


    def test_post_run_changes_report_that_the_script_ran(self):
        # (a) The script edits a declared consumer input: the after-run recheck must not claim nothing ran.
        self.write_script(before="    (args.repo_root / '.mask/skill-config/implement-rfc/project.md').write_text('edited by the script\\n')\n")
        self.commit('input-mutating script')
        result = self.approve()
        self.assertEqual(result['error']['code'], 'setup.failed', result['error'])
        row = self.setup_rows(result)[0]
        self.assertEqual((row['state'], row['reason']), ('failed', 'post-run'))
        self.assertIn('side effects outside the stage are unknown', row['detail'])
        self.assertNotIn('nothing ran', row['detail'])
        self.assertEqual(self.launches(), 1)
        self.assert_nothing_published()
        # (b) W12: the script replaces a role directory with a file; the run is classified, not an internal crash.
        self.write_script(before="    (args.repo_root / '.claude').mkdir(exist_ok=True); (args.repo_root / '.claude' / 'agents').write_text('not a directory')\n")
        self.commit('parent-replacing script')
        result = self.approve()
        self.assertEqual(result['error']['code'], 'setup.failed', result['error'])
        row = self.setup_rows(result)[0]
        self.assertEqual((row['state'], row['reason']), ('failed', 'post-run'))
        self.assertEqual((self.project / '.claude/agents').read_text(encoding='utf-8'), 'not a directory', 'the observed object is preserved')
        self.assertEqual(self.launches(), 2)
        self.assertFalse(self.lock.exists())
        self.assertFalse((self.home / 'pending.json').exists())
        self.assertFalse((self.home / 'staging').exists())

    def test_shipped_bytecode_never_replaces_the_reviewed_source(self):
        import py_compile
        cache = self.package / 'scripts/__pycache__'
        cache.mkdir()
        rogue = self.base / 'helper.py'
        rogue.write_text(HELPER.replace('fixture-model-do-not-run', 'bytecode-model-do-not-run'), encoding='utf-8')
        py_compile.compile(str(rogue), cfile=str(cache / f'helper.cpython-{sys.version_info[0]}{sys.version_info[1]}.pyc'), invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
        self.commit('rogue bytecode')
        result = self.approve()
        self.assertTrue(result['ok'], result)
        shutil.rmtree(cache)  # The planted cache is the package's own; MASK wrote none of its own.
        self.assert_published(result)
        self.assertNotIn('bytecode-model', (self.project / '.claude/agents/rfc-integrator.md').read_text(encoding='utf-8'))


class SetupRecoveryTests(SetupFixture):
    def test_tampered_transaction_id_cannot_direct_stage_cleanup(self):
        pending = self.crash_at('setup.exited')
        pending['transaction_id'] = '..'
        (self.home / 'pending.json').write_text(json.dumps(pending), encoding='utf-8')
        before = sorted(path.name for path in self.home.iterdir())
        for mode in ('--inspect', '--rollback', '--complete'):
            with self.subTest(mode=mode):
                self.assertEqual(self.machine('recover', mode)['error']['code'], 'recovery.conflict')
        self.assertEqual(sorted(path.name for path in self.home.iterdir()), before, 'nothing outside the stage was removed')

    def crash_at(self, label):
        plan_hash = self.machine('ensure', '--project', self.project, '--dry-run')['data']['plan_hash']
        script = """
import sys, os
sys.path.insert(0, sys.argv[1])
import mask, mask_fs
mask_fs.checkpoint = lambda label: os._exit(99) if label == sys.argv[2] else None
mask.main(sys.argv[3:])
"""
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), label, 'ensure', '--project', str(self.project), '--json',
                              '--expect-plan-hash', plan_hash, '--allow-setup', SUBJECT], capture_output=True, text=True, env=self.environment())
        self.assertEqual(run.returncode, 99, run.stderr)
        self.assertTrue((self.home / 'pending.json').is_file())
        return json.loads((self.home / 'pending.json').read_text(encoding='utf-8'))

    def test_crash_after_launch_is_never_rerun_and_rolls_back_cleanly(self):
        pending = self.crash_at('setup.exited')
        self.assertEqual((pending['setup']['phase'], pending['setup']['skill'], pending['setup']['granted_by']), ('launched', 'implement-rfc', 'allow-setup'))
        self.assertNotIn('lock', pending['setup'])
        self.assertTrue((self.home / 'staging' / pending['transaction_id']).is_dir())
        self.assertEqual(self.launches(), 1)
        self.assertEqual(self.machine('ensure', '--project', self.project)['error']['code'], 'recovery.required')
        inspect = self.machine('recover', '--inspect')
        self.assertEqual(inspect['data']['setup'], dict(phase='launched', skill='implement-rfc', script_effects='unknown'))
        refused = self.machine('recover', '--complete')
        self.assertEqual(refused['error']['code'], 'setup.unverified')
        self.assertEqual(self.launches(), 1)
        self.assertEqual(self.roles(), [])
        human = self.human('recover', '--inspect', stdin=subprocess.DEVNULL)
        self.assertIn('script side effects are unknown and are not rolled back', human.stdout)
        rolled = self.machine('recover', '--rollback')
        self.assertEqual(rolled['transaction'], 'rolled_back')
        self.assert_nothing_published()
        self.assertEqual(self.launches(), 1)
        # A fresh invocation needs fresh consent; nothing was replayed from the journal.
        result = self.machine('ensure', '--project', self.project)
        self.assertEqual(self.setup_rows(result)[0]['state'], 'consent_required')
        self.assertEqual(self.launches(), 1)

    def test_crash_during_publication_completes_from_the_journal_without_rerunning(self):
        pending = self.crash_at('native_role')
        self.assertEqual(pending['setup']['phase'], 'staged')
        self.assertEqual(pending['setup']['lock']['relative'], '.mask/generated/implement-rfc/native-roles.lock.json')
        self.assertEqual(len(pending['native_roles']), 2)
        self.assertEqual(self.launches(), 1)
        self.assertEqual(self.machine('ensure', '--project', self.project)['error']['code'], 'recovery.required')
        completed = self.machine('recover', '--complete')
        self.assertEqual(completed['transaction'], 'committed')
        self.assertEqual(self.launches(), 1)
        self.assert_published()
        ready = self.machine('ensure', '--project', self.project)
        self.assertTrue(ready['ok'])
        self.assertEqual(ready['data']['scope_readiness'][0]['workflow'], 'complete')

    def test_crash_during_publication_can_roll_back_the_lock_and_roles(self):
        self.crash_at('native_role_lock')
        self.assertTrue(self.lock.exists() or self.roles(), 'the crash happened after the first published effect')
        rolled = self.machine('recover', '--rollback')
        self.assertEqual(rolled['transaction'], 'rolled_back')
        self.assert_nothing_published()
        self.assertEqual(self.launches(), 1)


@unittest.skipUnless(os.name == 'posix', 'POSIX pseudoterminal prompt mechanics; native Windows console journeys are recorded separately')
class TerminalSetupTests(SetupFixture):
    def test_yes_runs_validates_publishes_and_rechecks_in_one_invocation(self):
        code, text = self.terminal('ensure', '--project', self.project, answer=b'y\n')
        self.assertEqual(code, 0, text)
        self.assertIn('confirmation needed (setup.required)', text)
        self.assertIn('implement-rfc needs consumer-specific native role setup.', text)
        self.assertIn(f'Source: {COORDINATE} (content fingerprint ', text)
        self.assertIn(f"Run: Python {self.deployed() / 'scripts/prepare_fixture_roles.py'}", text)
        self.assertIn('This runs package code with your user permissions; it is not sandboxed.', text)
        self.assertIn('Run this setup? [y/N]', text)
        self.assertNotIn('sha256:', text)
        self.assertIn(f'setup {SUBJECT} in ', text)
        self.assertIn(': published', text)
        self.assertIn('implement-rfc: ready', text)
        self.assertNotIn('python3 ', text.split('Run this setup?')[1], 'no copy/paste command instruction')
        self.assertEqual(self.launches(), 1)
        self.assert_published()
        self.assertEqual(len(self.links()), 2)

    def test_no_and_eof_leave_setup_incomplete_with_links_committed(self):
        for answer in (b'n\n', b'\n', b'\x04'):
            with self.subTest(answer=answer):
                code, text = self.terminal('ensure', '--project', self.project, answer=answer)
                self.assertEqual(code, 4, text)
                self.assertIn('workflow.incomplete', text)
                self.assertIn(f'setup {SUBJECT} in ', text)
                self.assertIn(': declined', text)
                self.assertEqual(len(self.links()), 2)
                self.assertEqual(self.launches(), 0)
                self.assert_nothing_published()

    def test_entrypoint_changed_after_the_prompt_is_a_stale_plan(self):
        def change_entrypoint():
            self.write_script(after="    pass  # edited after the prompt\n")
            self.commit('edited after prompt')
        code, text = self.terminal('ensure', '--project', self.project, answer=b'y\n', before_answer=change_entrypoint)
        self.assertEqual(code, 4, text)
        self.assertIn('plan.stale', text)
        self.assertEqual(self.launches(), 0)
        self.assert_nothing_published()

    def test_interruption_at_the_prompt_runs_nothing(self):
        code, text = self.terminal('ensure', '--project', self.project, interrupt=True)
        self.assertEqual(code, 130, text)
        self.assertEqual(self.launches(), 0)
        self.assert_nothing_published()

    def test_unapproved_project_asks_readiness_then_setup(self):
        self.assertTrue(self.machine('integration', 'revoke', '--project', self.project)['ok'])
        code, text = self.terminal('ensure', '--project', self.project, answer=[b'y\n', b'y\n'])
        self.assertEqual(code, 0, text)
        self.assertIn('confirmation needed (integration.approval_required)', text)
        self.assertIn('confirmation needed (setup.required)', text)
        self.assertEqual(self.launches(), 1)
        self.assert_published()
        self.assertEqual(json.loads((self.home / 'integration.json').read_text(encoding='utf-8'))['approvals'], {}, 'one-time consent did not persist approval')
