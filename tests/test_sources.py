import json
import functools
import http.server
from pathlib import Path
import shlex
import shutil
import ssl
import subprocess
import sys
import threading

import mask_core as c
import mask_sources as sources
from tests.support import Fixture, ENTRY


class SourcesTests(Fixture):
    def setUp(self):
        super().setUp()
        self.remote = self.base / 'private' / 'AgentSkills.git'
        self.remote.parent.mkdir()
        self.git(self.base, 'clone', '--bare', str(self.source), str(self.remote))
        self.git(self.source, 'remote', 'add', 'origin', str(self.remote))
        self.init()

    def test_migration_preserves_declarations_links_and_noncanonical_config(self):
        self.declare()
        self.call('project', 'register', self.project, '--apply')
        state = (self.home / 'state.json').read_bytes()
        before = self.snapshot(self.project)
        path = self.home / 'config.json'
        path.write_text(json.dumps(json.loads(path.read_text()), indent=3) + '\n\n')
        initial = self.snapshot()
        preview = self.call('source', 'migrate', '--dry-run')
        self.assertEqual(initial, self.snapshot())
        self.assertTrue(preview['would_change'])
        actual = self.call('source', 'migrate', '--expect-plan-hash', preview['data']['plan_hash'])
        self.assertTrue(actual['changed'])
        self.assertEqual(state, (self.home / 'state.json').read_bytes())
        self.assertEqual(before, self.snapshot(self.project))
        self.assertFalse(self.call('source', 'migrate')['changed'])
        self.assertFalse(self.init()['changed'])
        self.assertFalse(self.call('apply', '--project', self.project)['changed'])
        self.assertEqual(self.call('tap', 'remove', 'legacy', code=4)['error']['code'], 'source.referenced')

    def test_independent_taps_fetch_and_removal_are_catalog_only(self):
        self.call('source', 'migrate')
        other = self.base / 'public' / 'AgentSkills.git'
        other.parent.mkdir()
        self.git(self.base, 'clone', '--bare', str(self.source), str(other))
        state = (self.home / 'state.json').read_bytes()
        before = self.snapshot()
        planned = self.call('tap', 'add', 'public', other, '--dry-run')
        self.assertEqual(before, self.snapshot())
        self.call('tap', 'add', 'public', other, '--expect-plan-hash', planned['data']['plan_hash'])
        self.assertFalse(self.call('tap', 'add', 'public', other)['changed'])
        self.assertEqual(self.call('tap', 'add', 'public', self.remote, code=4)['error']['code'], 'source.alias_conflict')
        before = self.snapshot()
        for name in ('legacy', 'public'):
            observed = self.call('source', 'show', name)
            self.assertTrue(observed['data']['resolution_required'])
            self.assertFalse(self.call('source', 'fetch', name, '--dry-run')['data']['fetch_effects']['attempted'])
        self.assertEqual(before, self.snapshot())
        roots = []
        for name in ('legacy', 'public'):
            fetched = self.call('source', 'fetch', name)
            roots.append(fetched['data']['binding']['cache'])
            self.assertTrue(fetched['data']['fetch_effects']['remote_refs_changed'])
            self.assertEqual(fetched['data']['cached_revision'], self.git(self.source, 'rev-parse', 'HEAD'))
            self.assertFalse(self.call('source', 'fetch', name)['data']['fetch_effects']['remote_refs_changed'])
        self.assertNotEqual(*roots)
        self.call('tap', 'remove', 'public')
        self.assertTrue(Path(roots[1]).is_dir())
        self.assertEqual(state, (self.home / 'state.json').read_bytes())
        self.assertFalse((self.project / '.agents').exists())

    def test_full_identity_and_transport_rewrite_refuse_before_fetch(self):
        self.call('source', 'migrate')
        other = self.base / 'other' / 'AgentSkills.git'
        other.parent.mkdir()
        self.git(self.base, 'clone', '--bare', str(self.source), str(other))
        self.git(self.source, 'remote', 'set-url', 'origin', str(other))
        for command in (('source', 'fetch'), ('update', '--dry-run')):
            self.assertEqual(self.call(*command, code=4)['error']['code'], 'source.identity_mismatch')
        self.git(self.source, 'remote', 'set-url', 'origin', str(self.remote))
        self.call('source', 'fetch', 'legacy')
        root = Path(self.call('source', 'show', 'legacy')['data']['binding']['cache'])
        # Source cache-local URL rewrites must not inherit approval either.
        self.git(root, 'config', 'url.' + str(other) + '.insteadOf', str(self.remote))
        self.assertEqual(self.call('source', 'fetch', 'legacy', code=4)['error']['code'], 'source.identity_mismatch')

    def test_unsafe_urls_and_cache_collisions(self):
        self.call('source', 'migrate')
        for value in ('https://user:TOPSECRET@example.test/org/repo', 'https://TOPSECRET@example.test/a',
                      'ext::TOPSECRET', 'http://example.test/repo', 'ssh://git@example.test/../repo',
                      'https://example.test/%252e%252e/repo', '-TOPSECRET'):
            result = self.call('tap', 'add', 'unsafe', value, code=3 if not value.startswith('-') else 2)
            if not value.startswith('-'):
                self.assertNotIn('TOPSECRET', json.dumps(result))
        self.call('tap', 'add', 'collision', self.remote)
        root = Path(self.call('source', 'show', 'collision')['data']['binding']['cache'])
        root.parent.mkdir(parents=True)
        root.mkdir()
        (root / 'unrelated').write_text('keep')
        self.call('source', 'fetch', 'collision', code=4)
        self.assertEqual((root / 'unrelated').read_text(), 'keep')

    def test_migration_and_plan_guards_are_explicit(self):
        self.assertTrue(self.call('source', 'list')['data']['migration_required'])
        self.assertEqual(self.call('tap', 'add', 'extra', self.remote, code=4)['error']['code'], 'source.migration_required')
        self.call('source', 'migrate')
        self.call('tap', 'add', 'extra', self.remote, '--expect-plan-hash', 'stale', code=4)
        self.assertEqual(set(self.call('source', 'list')['data']['sources']), {'legacy'})

    def test_repository_normalization_keeps_authority_boundaries(self):
        self.assertEqual(sources.repository('HTTPS://EXAMPLE.test:443/Org/Repo.git'), 'https://example.test/Org/Repo.git')
        self.assertEqual(sources.repository('git@example.test:Org/Repo.git'), 'ssh://git@example.test/~/Org/Repo.git')
        self.assertNotEqual(sources.repository('git@example.test:Org/Repo.git'), sources.repository('ssh://git@example.test/Org/Repo.git'))
        self.assertNotEqual(sources.repository('https://example.test/Org/Repo.git'), sources.repository('https://example.test/Org/Repo'))
        self.assertNotEqual(sources.repository('https://example.test/org/repo'), sources.repository('ssh://git@example.test/org/repo'))
        self.assertNotEqual(sources.repository('https://example.test/Org/Repo'), sources.repository('https://example.test/org/repo'))
        for value in ('git@example.test:~other/repo', 'git@example.test:--help'):
            with self.assertRaises(c.MaskError):
                sources.repository(value)

    def test_capabilities_and_recovery_retain_config_v2(self):
        self.call('source', 'migrate')
        config = (self.home / 'config.json').read_bytes()
        caps = self.call('capabilities')['data']
        self.assertEqual(caps['readable_versions']['machine'], [1, 2])
        commands = {item['name']: item for item in caps['commands']}
        self.assertFalse(commands['tap.add']['network'])
        self.assertTrue(commands['tap.add']['plan_guard'])
        self.assertTrue(commands['source.fetch']['network'])
        self.declare()
        self.call('project', 'register', self.project)
        script = """
import os,sys
sys.path.insert(0,sys.argv[1])
import mask,mask_fs
mask_fs.checkpoint = lambda label: os._exit(99) if label == 'link' else None
mask.main(['apply','--project',sys.argv[2],'--home',sys.argv[3],'--json'])
"""
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), str(self.project), str(self.home)], capture_output=True)
        self.assertEqual(run.returncode, 99, run.stdout + run.stderr)
        self.assertEqual(self.call('source', 'migrate', code=8)['error']['code'], 'recovery.required')
        self.call('recover', '--complete')
        self.assertEqual(config, (self.home / 'config.json').read_bytes())
        self.assertFalse(self.call('apply')['changed'])

    def test_scp_to_absolute_rewrite_refuses_without_a_second_ssh_connection(self):
        self.call('source', 'migrate')
        log = self.base / 'ssh-calls'
        shim = self.base / 'ssh-fixture.py'
        shim.write_text('import pathlib,subprocess,sys\n' +
                        'with pathlib.Path(' + repr(str(log)) + ').open("a") as f: f.write(repr(sys.argv)+"\\n")\n' +
                        'raise SystemExit(subprocess.call(["git","upload-pack",' + repr(str(self.remote)) + ']))\n')
        env = {'GIT_SSH_COMMAND': shlex.join([Path(sys.executable).as_posix(), shim.as_posix()]), 'GIT_SSH_VARIANT': 'ssh'}
        uri = 'git@example.test:Org/Repo.git'
        self.call('tap', 'add', 'ssh', uri)
        self.call('source', 'fetch', 'ssh', env=env)
        before = log.read_bytes()
        root = self.call('source', 'show', 'ssh')['data']['binding']['cache']
        self.git(root, 'config', 'url.ssh://git@example.test/Org/Repo.git.insteadOf', uri)
        self.assertEqual(self.call('source', 'fetch', 'ssh', env=env, code=4)['error']['code'], 'source.identity_mismatch')
        self.assertEqual(log.read_bytes(), before)

    def test_scoped_https_redirect_policy_cannot_expand_approval(self):
        openssl = shutil.which('openssl')
        if openssl is None:
            self.skipTest('Local TLS redirect fixture requires openssl to generate its disposable certificate.')
        cert, key = self.base / 'cert.pem', self.base / 'key.pem'
        subprocess.run([openssl, 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', str(key),
                        '-out', str(cert), '-days', '1', '-subj', '/CN=localhost'], check=True, capture_output=True)
        self.git(self.remote, 'update-server-info')
        requests = []
        class Handler(http.server.SimpleHTTPRequestHandler):
            def do_GET(handler):
                requests.append(handler.path)
                if handler.path.startswith('/approved.git/'):
                    handler.send_response(301)
                    handler.send_header('Location', handler.path.replace('/approved.git/', '/private/AgentSkills.git/', 1))
                    handler.end_headers()
                else:
                    super().do_GET()
            def log_message(handler, *args):
                pass
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Handler, directory=str(self.base)))
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, key)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            uri = 'https://localhost:' + str(server.server_port) + '/approved.git'
            config = self.base / 'fixture-git-config'
            config.write_text('[http "' + uri + '"]\nfollowRedirects = true\nsslVerify = false\n')
            env = {'GIT_CONFIG_GLOBAL': str(config), 'GIT_CONFIG_NOSYSTEM': '1'}
            self.call('source', 'migrate')
            self.call('tap', 'add', 'redirect', uri)
            result = self.call('source', 'fetch', 'redirect', env=env, code=4)
            self.assertEqual(result['error']['code'], 'source.redirect_policy')
            self.assertFalse(result['data']['fetch_effects']['attempted'])
            self.assertEqual(requests, [])
            config.write_text('[http "' + uri + '"]\nsslVerify = false\n')
            self.assertEqual(self.call('source', 'fetch', 'redirect', env=env, code=5)['error']['code'], 'git.failed')
            self.assertTrue(requests)
            self.assertTrue(all(path.startswith('/approved.git/') for path in requests))
            # The legacy fetch path uses the same effective policy guard.
            requests.clear()
            config.write_text('[http "' + uri + '"]\nfollowRedirects = true\nsslVerify = false\n')
            self.git(self.source, 'remote', 'set-url', 'origin', uri)
            from unittest.mock import patch
            import os
            import mask_git
            with patch.dict(os.environ, env):
                import mask
                with self.assertRaises(c.MaskError) as blocked:
                    mask_git.fetch(self.source, 'origin', 'main', 30, mask.result('source.fetch'))
                self.assertEqual(blocked.exception.code, 'source.redirect_policy')
            self.assertEqual(requests, [])
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
