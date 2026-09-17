#!/usr/bin/env python3
"""Exercise the management skill's public command patterns in disposable local fixtures."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def verify(program):
    with tempfile.TemporaryDirectory(prefix='mask-examples-') as temporary:
        base = Path(temporary).resolve()
        source, project, home, remote = (base / name for name in ('AgentSkills', 'project ü spaces', 'machine', 'AgentSkills.git'))
        source.mkdir(); project.mkdir()
        def git(root, *args):
            return subprocess.run(['git', '-C', str(root), *map(str, args)], check=True, capture_output=True, encoding='utf-8').stdout.strip()
        git(source, 'init', '-b', 'main'); git(source, 'config', 'user.name', 'Fixture'); git(source, 'config', 'user.email', 'fixture@example.invalid')
        for name in ('alpha', 'beta'):
            path = source / 'skills' / name; path.mkdir(parents=True)
            (path / 'SKILL.md').write_text(f'---\nname: {name}\ndescription: Fixture instructions\n---\n\nExample.\n', encoding='utf-8')
        git(source, 'add', 'skills'); git(source, 'commit', '-m', 'fixture')
        git(base, 'init', '--bare', '-b', 'main', remote); git(source, 'remote', 'add', 'origin', remote); git(source, 'push', '-u', 'origin', 'main')
        git(project, 'init', '-b', 'main')
        env = dict(os.environ, MASK_HOME=str(home), PYTHONDONTWRITEBYTECODE='1')
        def call(*args, code=0):
            run = subprocess.run([sys.executable, '-B', str(program / 'mask.py'), *map(str, args), '--json'], cwd=project, env=env, capture_output=True, encoding='utf-8')
            assert run.returncode == code, (args, run.stdout, run.stderr)
            assert not run.stderr
            data = json.loads(run.stdout); assert data['ok'] == (code == 0)
            return data
        def links():
            return sorted(path.relative_to(project).as_posix() for path in project.rglob('*') if path.is_symlink())
        capabilities = call('capabilities')['data']
        assert capabilities['deployment_model'] == 'taps' and capabilities['schemas']['machine'] == 3
        # Tap-first bootstrap (RFC-MASK-0021): approving the local bare upstream creates machine config v3 and state.
        call('tap', 'add', 'agentskills', remote)
        call('config', 'show'); call('source', 'fetch')
        call('project', 'init', '--project', project); call('project', 'register', project)
        preview = call('install', 'alpha', '--project', project, '--dry-run')
        call('install', 'alpha', '--project', project, '--expect-plan-hash', preview['data']['plan_hash'])
        assert not call('install', 'alpha', '--project', project)['would_change']
        assert links() == ['.agents/skills/alpha', '.claude/skills/alpha']
        # A reviewed install preview goes stale once the tap cache moves under it.
        preview = call('install', 'beta', '--project', project, '--dry-run')
        support = source / 'skills/beta/support.txt'; support.write_text('changed')
        git(source, 'add', 'skills'); git(source, 'commit', '-m', 'support'); git(source, 'push', 'origin', 'main')
        call('source', 'fetch')
        assert call('install', 'beta', '--project', project, '--expect-plan-hash', preview['data']['plan_hash'], code=4)['error']['code'] == 'plan.stale'
        leaf = project / '.agents/skills/beta'; leaf.mkdir(); (leaf / 'preserve').write_text('user content')
        assert call('install', 'beta', '--project', project, code=4)['error']['code'] == 'target.collision'
        assert (leaf / 'preserve').read_text() == 'user content'
        assert 'beta' not in [row['id'] for row in json.loads((project / '.mask.json').read_text(encoding='utf-8'))['skills']]
        (leaf / 'preserve').unlink(); leaf.rmdir()  # Only our explicit test fixture.
        preview = call('install', 'beta', '--project', project, '--dry-run')
        call('install', 'beta', '--project', project, '--expect-plan-hash', preview['data']['plan_hash'])
        call('doctor', '--project', project, '--check')
        # A separate crashed process proves that public recovery resumes journal intent.
        injection = "import sys,os;sys.path.insert(0,sys.argv[1]);import mask,mask_fs;mask_fs.checkpoint=lambda label:os._exit(99) if label=='intent' else None;mask.main(sys.argv[2:])"
        run = subprocess.run([sys.executable, '-B', '-c', injection, str(program), 'remove', 'beta', '--project', str(project), '--json'], cwd=project, env=env, capture_output=True)
        assert run.returncode == 99
        assert call('recover', '--inspect')['data']['pending']['operation'] == 'remove'
        call('recover', '--complete'); assert not call('apply', '--project', project)['changed']
        assert links() == ['.agents/skills/alpha', '.claude/skills/alpha']
        removed = call('remove', 'beta', '--project', project)
        assert not removed['changed'] and [warning['code'] for warning in removed['warnings']] == ['selection.not_selected']
        author = base / 'author'; git(base, 'clone', '--branch', 'main', remote, author)
        git(author, 'config', 'user.name', 'Fixture'); git(author, 'config', 'user.email', 'fixture@example.invalid')
        with (author / 'skills/alpha/SKILL.md').open('a') as handle: handle.write('\nUpstream change.\n')
        git(author, 'add', 'skills'); git(author, 'commit', '-m', 'upstream'); git(author, 'push', 'origin', 'main')
        head = git(author, 'rev-parse', 'HEAD')
        # A dry run reviews only the fetched cache: the upstream push stays unseen until update fetches it.
        preview = call('upgrade', '--dry-run')
        assert preview['data']['network'] == 'none' and not preview['data']['fetches']['agentskills']['attempted']
        assert head not in [change['after_commit'] for row in preview['data']['consumers'] for change in row['changes']]
        updated = call('upgrade')
        assert updated['data']['network'] == 'fetch' and updated['changed']
        assert [row['commit'] for row in json.loads((project / '.mask.lock.json').read_text(encoding='utf-8'))['packages']] == [head]
        assert not call('upgrade')['changed']
        call('project', 'show', '--project', project); call('project', 'set-targets', '--project', project, '--inherit')
        call('project', 'unregister', project)
        assert (project / '.mask.json').is_file() and not (project / '.agents/skills/alpha').is_symlink()
        print('PASS: capabilities, add/remove/no-op, guarded stale refusal, collision preservation, crash recovery, frozen update, unregister; all fixtures removed on exit.')


import unittest

class EndToEndTests(unittest.TestCase):
    def test_public_management_sequence(self):
        verify(Path(__file__).resolve().parents[1])

    @unittest.skipUnless(os.environ.get('MASK_SHARED_SKILL'), 'Explicit canonical skill fixture is required for shared-context acceptance')
    def test_shared_context_through_native_links(self):
        import shutil
        shared = Path(os.environ['MASK_SHARED_SKILL']).resolve()
        contexts = Path(os.environ['MASK_CONTEXT_ROOT']).resolve()
        with tempfile.TemporaryDirectory(prefix='mask-context-') as temporary:
            base = Path(temporary).resolve(); source = base / 'AgentSkills'; source.mkdir()
            def git(root, *args):
                subprocess.run(['git', '-C', str(root), *map(str, args)], capture_output=True, check=True)
            git(source, 'init', '-b', 'main'); git(source, 'config', 'user.name', 'Fixture'); git(source, 'config', 'user.email', 'fixture@example.invalid')
            shutil.copytree(shared, source / 'skills/implement-rfc')
            git(source, 'add', 'skills'); git(source, 'commit', '-q', '-m', 'shared skill fixture')
            upstream = base / 'upstream' / 'AgentSkills.git'; upstream.parent.mkdir()
            git(base, 'init', '-q', '--bare', '-b', 'main', upstream); git(source, 'push', '-q', upstream, 'main')
            program = Path(__file__).resolve().parents[1] / 'mask.py'
            home = base / 'machine'
            def call(*args):
                run = subprocess.run([sys.executable, '-B', str(program), '--home', str(home), '--json', *map(str,args)], capture_output=True, encoding='utf-8')
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                return json.loads(run.stdout)
            call('tap', 'add', 'agentskills', upstream)
            store = (home / 'store' / 'v1').resolve()
            facts = []
            for name in ('ManageAgentSkills', 'AgentSkills'):
                root = base / ('consumer ' + name); root.mkdir()
                git(root, 'init', '-b', 'main')
                target = root / '.mask/skill-config/implement-rfc'; target.mkdir(parents=True)
                for filename in ('project.json', 'project.md'):
                    shutil.copyfile(contexts / name / filename, target / filename)
                call('install', 'implement-rfc', '--project', root)
                link = root / '.agents/skills/implement-rfc'
                record = json.loads((home / 'state.json').read_text(encoding='utf-8'))['projects'][str(root)]
                store_link = record['links']['.agents/skills/implement-rfc']['link_text']
                self.assertTrue(link.is_symlink()); self.assertTrue(link.resolve().is_relative_to(store))
                self.assertTrue(os.path.samefile(link, store_link))
                code = "import sys,json;sys.path.insert(0,sys.argv[1]);from project_config import resolve_context;c=resolve_context();print(json.dumps([c.config['project'],str(c.repo_root),str(c.asset_root)]))"
                run = subprocess.run([sys.executable,'-B','-c',code,str(link / 'scripts')],cwd=root,capture_output=True,encoding='utf-8')
                self.assertEqual(run.returncode,0,run.stderr); facts.append(json.loads(run.stdout))
            self.assertEqual([item[0] for item in facts],['mask','agent-skills'])
            self.assertEqual(facts[0][2],facts[1][2]); self.assertNotEqual(facts[0][1],facts[1][1])
