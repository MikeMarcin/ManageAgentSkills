import json
import functools
import http.server
from pathlib import Path
import shlex
import shutil
import ssl
import subprocess
import sys
import tempfile
import threading

import mask_core as c
import mask_sources as sources
from tests.support import TAP, Fixture, ENTRY


class SourcesTests(Fixture):
    """Tap tests start from ``init`` (the fixture tap); ``self.remote`` is a second bare copy that the checkout names as its ``origin``.

    ``source migrate`` and its guards are retired (RFC-MASK-0021 AC05); tests/test_retired_paths.py covers their refusal.
    """

    def setUp(self):
        super().setUp()
        self.remote = self.base / 'private' / 'AgentSkills.git'
        self.remote.parent.mkdir()
        self.git(self.base, 'clone', '--bare', str(self.source), str(self.remote))
        self.git(self.source, 'remote', 'add', 'origin', str(self.remote))

    def test_independent_taps_fetch_and_removal_are_catalog_only(self):
        self.init()
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
        self.assertEqual(self.call('tap', 'add', 'extra', self.remote, '--expect-plan-hash', 'stale', code=4)['error']['code'], 'plan.stale')
        self.assertEqual(before, self.snapshot())
        for name in (TAP, 'public'):
            observed = self.call('source', 'show', name)
            self.assertTrue(observed['data']['resolution_required'])
            self.assertFalse(self.call('source', 'fetch', name, '--dry-run')['data']['fetch_effects']['attempted'])
        self.assertEqual(before, self.snapshot())
        roots = []
        for name in (TAP, 'public'):
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
        # A user-level Git URL rewrite points the approved tap transport at another repository. Every fetching command
        # refuses at the endpoint check, before any git fetch process runs; test_cache_local_url_rewrite_refuses_before_fetch
        # covers only a cache-local rewrite under source fetch NAME.
        self.init()
        self.install(TAP + '/alpha')
        self.install(TAP + '/beta', user=True)
        other = self.base / 'other' / 'AgentSkills.git'
        other.parent.mkdir()
        self.git(self.base, 'clone', '--bare', str(self.upstream), str(other))
        entry = json.loads((self.home / 'config.json').read_text(encoding='utf-8'))['sources'][TAP]
        rewrite = self.base / 'rewrite.gitconfig'
        self.git(self.base, 'config', '--file', str(rewrite), 'url.' + str(other) + '.insteadOf', entry['transport'])
        (self.source / 'skills/alpha/notes').write_text('never fetched while rewritten')
        head = self.publish('upstream moves')
        traces = tempfile.TemporaryDirectory(prefix='mask-trace-')
        self.addCleanup(traces.cleanup)
        before = self.snapshot()

        def rewritten(*args, code=4):
            # Git writes one trace2 event file per process; a fetch process would report cmd_name "fetch".
            trace = Path(tempfile.mkdtemp(dir=traces.name))
            result = self.call(*args, code=code, env={'GIT_CONFIG_GLOBAL': str(rewrite), 'GIT_TRACE2_EVENT': str(trace)})
            names = [json.loads(line).get('name') for path in trace.iterdir() for line in path.read_text(encoding='utf-8').splitlines() if '"cmd_name"' in line]
            self.assertNotIn('fetch', names, args)
            return result

        for args in (('source', 'fetch'), ('source', 'fetch', TAP), ('update', '--project', self.project)):
            self.assertEqual(rewritten(*args)['error']['code'], 'source.identity_mismatch', args)
        # The unscoped update isolates the refused tap: both consumers on it are blocked by the same refusal and nothing applies.
        result = rewritten('update')
        self.assertEqual((result['error']['code'], sorted(result['error']['details']['blocked']), result['changed']),
                         ('update.incomplete', sorted([str(self.personal), str(self.project)]), False))
        self.assertEqual({row['status']: row['error']['code'] for row in result['data']['consumers']}, {'blocked': 'source.identity_mismatch'})
        self.assertEqual(result['data']['fetches'][TAP]['error']['code'], 'source.identity_mismatch')
        self.assertEqual(before, self.snapshot())
        self.assertNotEqual(subprocess.run(['git', '-C', entry['cache'], 'cat-file', '-e', head + '^{commit}'], capture_output=True).returncode, 0)
        self.assertEqual(self.call('source', 'fetch', TAP)['data']['cached_revision'], head)
        # Removing the approval is catalog-only; it refuses while a registered consumer still references the tap.
        before = self.snapshot()
        refused = self.call('tap', 'remove', TAP, code=4)['error']
        self.assertEqual(refused['code'], 'source.referenced')
        self.assertEqual(before, self.snapshot())

    def test_cache_local_url_rewrite_refuses_before_fetch(self):
        self.init()
        other = self.base / 'other' / 'AgentSkills.git'
        other.parent.mkdir()
        self.git(self.base, 'clone', '--bare', str(self.source), str(other))
        self.call('source', 'fetch', TAP)
        root = Path(self.call('source', 'show', TAP)['data']['binding']['cache'])
        # Source cache-local URL rewrites must not inherit approval either.
        self.git(root, 'config', 'url.' + str(other) + '.insteadOf', str(self.upstream))
        self.assertEqual(self.call('source', 'fetch', TAP, code=4)['error']['code'], 'source.identity_mismatch')

    def test_unsafe_urls_and_cache_collisions(self):
        self.init()
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

    def test_capabilities_and_recovery_retain_config_v3(self):
        self.init()
        config = (self.home / 'config.json').read_bytes()
        caps = self.call('capabilities')['data']
        # Machine config v3 is written; v1 and v2 stay readable for migration only (RFC-MASK-0021, MASK-0101).
        self.assertEqual((caps['schemas']['machine'], caps['readable_versions']['machine'], caps['deployment_model']), (3, [1, 2, 3], 'taps'))
        commands = {item['name']: item for item in caps['commands']}
        self.assertFalse(commands['tap.add']['network'])
        self.assertTrue(commands['tap.add']['plan_guard'])
        self.assertTrue(commands['source.fetch']['network'])
        self.install(TAP + '/alpha')
        self.call('project', 'set-agents', TAP + '/alpha', 'codex')  # Declaration only: the pinned apply below removes the claude link.
        script = """
import os,sys
sys.path.insert(0,sys.argv[1])
import mask,mask_fs
mask_fs.checkpoint = lambda label: os._exit(99) if label == 'link' else None
mask.main(['apply','--project',sys.argv[2],'--home',sys.argv[3],'--json'])
"""
        run = subprocess.run([sys.executable, '-B', '-c', script, str(ENTRY.parent), str(self.project), str(self.home)], capture_output=True, env=self.environment())
        self.assertEqual(run.returncode, 99, run.stdout + run.stderr)
        for args in (('install', TAP + '/beta'), ('update',), ('source', 'fetch', TAP)):
            self.assertEqual(self.call(*args, code=8)['error']['code'], 'recovery.required', args)
        self.call('recover', '--complete')
        self.assertEqual(config, (self.home / 'config.json').read_bytes())
        self.assertFalse(self.call('apply')['changed'])
        self.assertEqual(sorted(path.relative_to(self.project).as_posix() for path in self.project.rglob('*') if path.is_symlink()), ['.agents/skills/alpha'])

    def test_scp_to_absolute_rewrite_refuses_without_a_second_ssh_connection(self):
        self.init()
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
            self.init()
            self.call('tap', 'add', 'redirect', uri)
            result = self.call('source', 'fetch', 'redirect', env=env, code=4)
            self.assertEqual(result['error']['code'], 'source.redirect_policy')
            self.assertFalse(result['data']['fetch_effects']['attempted'])
            self.assertEqual(requests, [])
            config.write_text('[http "' + uri + '"]\nsslVerify = false\n')
            self.assertEqual(self.call('source', 'fetch', 'redirect', env=env, code=5)['error']['code'], 'git.failed')
            self.assertTrue(requests)
            self.assertTrue(all(path.startswith('/approved.git/') for path in requests))
            # The checkout fetch path (legacy source fetch and mask_install) uses the same effective policy guard; it is called directly.
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
