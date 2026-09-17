"""Transport-neutral tap identity and convention-following transport (RFC-MASK-0022 AC01-AC06).

Every check runs the public CLI as a subprocess against ``tests.forge_support``'s network-free forge; only the
normalizer's own table is exercised in-process. "Another machine" is another MASK_HOME and personal home.
"""
import json
import unittest

import mask_core as c
import mask_resolve as r
import mask_sources as sources
from tests.forge_support import BARE_HTTPS, ForgeFixture, HTTPS, LEGACY_SSH, SCP, SSH
from tests.support import TAP


class Normalizer(unittest.TestCase):
    """AC01/AC02: one identity per forge repository; strict everywhere else."""

    def setUp(self):
        self.addCleanup(lambda: (sources.ACTIVE_FORGES.clear(), sources.ACTIVE_FORGES.update(sources.FORGE_HOSTS)))

    def test_forge_spellings_fold_to_one_https_identity(self):
        for host in sorted(sources.FORGE_HOSTS):
            canonical = f'https://{host}/Org/Repo.git'
            for value in (f'https://{host}/Org/Repo', canonical, f'ssh://git@{host}/Org/Repo.git', f'git@{host}:Org/Repo.git', f'git@{host}:Org/Repo',
                          f'ssh://git@{host}/~/Org/Repo.git', f'HTTPS://{host.upper()}:443/Org/Repo.git/'):
                self.assertEqual(sources.repository(value), canonical, value)
        self.assertNotEqual(sources.repository('https://github.com/Org/Repo'), sources.repository('https://github.com/org/repo'))  # Path case is kept.
        self.assertEqual(sources.scp('https://github.com/Org/Repo.git'), 'git@github.com:Org/Repo.git')

    def test_other_shapes_and_other_hosts_stay_strict(self):
        for value in ('ssh://bob@github.com/Org/Repo.git', 'ssh://git@github.com:2222/Org/Repo.git', 'https://github.com:8443/Org/Repo.git'):
            self.assertEqual(sources.repository(value), sources.spelling(value), value)
            self.assertFalse(sources.same(value, 'https://github.com/Org/Repo.git'), value)
        self.assertEqual(sources.repository('git@example.test:Org/Repo.git'), 'ssh://git@example.test/~/Org/Repo.git')
        self.assertFalse(sources.same('https://example.test/Org/Repo.git', 'ssh://git@example.test/Org/Repo.git'))
        self.assertFalse(sources.same('https://example.test/Org/Repo.git', 'https://example.test/Org/Repo'))
        for value in ('https://user:secret@github.com/Org/Repo.git', 'https://github.com/Org/Repo.git?x=1', 'https://github.com/Org/../Repo.git', 'http://github.com/Org/Repo.git'):
            with self.assertRaises(c.MaskError, msg=value):
                sources.repository(value)

    def test_a_machine_opts_a_host_in_and_a_project_file_cannot(self):
        config = dict(c.empty_config(), forge_hosts=['example.test'])
        c.config(config)
        self.assertTrue(sources.same('https://example.test/Org/Repo.git', 'git@example.test:Org/Repo.git'))
        c.config(c.empty_config())  # The next machine configuration read does not inherit the opt-in.
        self.assertFalse(sources.same('https://example.test/Org/Repo.git', 'git@example.test:Org/Repo.git'))
        for bad in (['Example.test'], ['example.test', 'example.test'], 'example.test', [''], ['-x.test']):
            with self.assertRaises(c.MaskError, msg=bad):
                c.config(dict(c.empty_config(), forge_hosts=bad))
        declaration = dict(schema_version=2, sources={TAP: dict(repository='https://example.test/Org/Repo.git')}, skills=[])
        for poisoned in (dict(declaration, forge_hosts=['example.test']), dict(declaration, sources={TAP: dict(repository='https://example.test/Org/Repo.git', forge_hosts=['example.test'])})):
            with self.assertRaises(c.MaskError) as refused:
                r.selection(poisoned)
            self.assertEqual(refused.exception.code, 'selection.invalid')
        lock = dict(schema_version=1, resolver='mask-lock-v1', selection_digest='sha256:' + '0' * 64, packages=[], forge_hosts=['example.test'])
        with self.assertRaises(c.MaskError):
            r.lock(lock)

    def test_every_derived_transport_is_a_spelling_of_the_tap_identity(self):
        """AC06: transport selection cannot leave the equivalence class."""
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as temp:
            for typed in ('https://github.com/Org/Repo', 'git@github.com:Org/Repo.git', 'ssh://git@github.com/~/Org/Repo.git'):
                entry = sources.binding(Path(temp), 'tap', typed)
                ways = sources.transports(Path(temp), 'tap', entry)
                self.assertEqual(sorted({sources.scheme(way) for way, _ in ways}), ['https', 'ssh'])
                for way, _ in ways:
                    self.assertTrue(sources.same(way, entry['repository']), way)
                    self.assertNotIn('/~/', way)
            strict = sources.binding(Path(temp), 'tap', 'git@example.test:Org/Repo.git')
            self.assertEqual(sources.transports(Path(temp), 'tap', strict), [('git@example.test:Org/Repo.git', 'catalog')])


class Deploying(ForgeFixture):
    def committed(self, recorded, *, host=None):
        """A project directory holding only what a repository would commit, with ``recorded`` as the spelling an older program wrote."""
        if not (self.project / '.mask.lock.json').exists():
            self.assertTrue(self.machine('tap', 'add', TAP, HTTPS)['ok'])
            self.assertEqual(self.human('install', 'alpha').returncode, 0)
        declaration, lock = self.document(self.project / '.mask.json'), self.document(self.project / '.mask.lock.json')
        declaration['sources'][TAP]['repository'] = recorded
        for row in lock['packages']:
            row['repository'] = recorded
        lock['selection_digest'] = r.selection_digest(declaration)
        clone = self.base / ('clone-' + str(len(list(self.base.glob('clone-*')))))
        clone.mkdir()
        self.git(clone, 'init', '-q', '-b', 'main')
        (clone / '.mask.json').write_text(json.dumps(declaration, indent=2) + '\n', encoding='utf-8')
        (clone / '.mask.lock.json').write_text(json.dumps(lock, indent=2) + '\n', encoding='utf-8')
        return clone

    def files(self, root):
        return (root / '.mask.json').read_bytes(), (root / '.mask.lock.json').read_bytes()


class OneIdentity(Deploying):
    """AC01 and AC05: any committed spelling deploys, unchanged, on a machine approved with any other."""

    def test_every_committed_spelling_meets_every_approved_spelling(self):
        for recorded in (HTTPS, BARE_HTTPS, SSH, LEGACY_SSH):
            for typed in (HTTPS, BARE_HTTPS, SSH, SCP):
                with self.subTest(recorded=recorded, typed=typed):
                    clone, other = self.committed(recorded), self.machine_home(f'{len(list(self.base.glob("clone-*")))}')
                    before = self.files(clone)
                    added = self.machine('tap', 'add', TAP, typed, env=other, cwd=clone)
                    self.assertEqual((added['ok'], added['data']['config']['sources'][TAP]['repository']), (True, HTTPS))
                    # A fresh machine acquires exactly the locked commit; ensure itself never fetches.
                    acquired = self.machine('source', 'fetch', '--locked', '--project', clone, env=other, cwd=clone)
                    self.assertTrue(acquired['ok'], acquired)
                    ensured = self.raw('ensure', '--yes', env=other, cwd=clone)
                    self.assertEqual(ensured.returncode, 0, ensured.stderr)
                    self.assertEqual(self.files(clone), before)
                    self.assertTrue((clone / '.claude/skills/alpha/SKILL.md').is_file())
                    self.assertNotIn(LEGACY_SSH, self.reached())

    def test_a_write_takes_the_canonical_spelling_and_a_spelling_alone_never_writes(self):
        clone, other = self.committed(LEGACY_SSH), self.machine_home('writer')
        self.assertTrue(self.machine('tap', 'add', TAP, SCP, env=other, cwd=clone)['ok'])
        self.assertTrue(self.machine('source', 'fetch', '--locked', '--project', clone, env=other, cwd=clone)['ok'])
        self.assertEqual(self.raw('ensure', '--yes', env=other, cwd=clone).returncode, 0)
        before, old = self.files(clone), self.document(clone / '.mask.lock.json')['packages'][0]
        quiet = self.machine('upgrade', '--project', clone, env=other, cwd=clone)
        self.assertEqual((quiet['ok'], quiet['changed'], self.files(clone)), (True, False, before))
        path = self.source / 'skills/alpha/SKILL.md'
        path.write_text(path.read_text(encoding='utf-8') + '\nNewer.\n', encoding='utf-8')
        candidate = self.publish('newer')
        moved = self.machine('upgrade', '--project', clone, env=other, cwd=clone)
        self.assertTrue(moved['changed'], moved)
        row = self.document(clone / '.mask.lock.json')['packages'][0]
        self.assertEqual((row['repository'], row['commit']), (HTTPS, candidate))
        self.assertEqual(self.files(clone)[0], before[0])  # upgrade writes only the lock; the declaration keeps its bytes.
        added = self.machine('install', 'beta', '--project', clone, env=other, cwd=clone)
        self.assertTrue(added['ok'], added)
        self.assertEqual(self.document(clone / '.mask.json')['sources'][TAP]['repository'], HTTPS)
        self.assertEqual({item['repository'] for item in self.document(clone / '.mask.lock.json')['packages']}, {HTTPS})
        self.assertEqual(old['payload_digest'], [item for item in moved['data']['consumers'][0]['changes']][0]['before_digest'])


class StrictElsewhere(Deploying):
    """AC02 through the CLI: another host keeps HTTPS and SSH apart until this machine says otherwise."""

    def test_mismatch_refuses_until_the_machine_opts_the_host_in(self):
        clone, other = self.committed('ssh://git@example.test/Fixture/AgentSkills.git'), self.machine_home('strict')
        self.assertTrue(self.machine('tap', 'add', TAP, 'https://example.test/Fixture/AgentSkills.git', env=other, cwd=clone)['ok'])
        refused = self.machine('ensure', '--yes', env=other, cwd=clone)
        self.assertEqual(refused['error']['code'], 'source.identity_mismatch')
        opted = self.machine('config', 'set', '--forge-host', 'example.test', env=other, cwd=clone)
        self.assertEqual((opted['changed'], opted['data']['config']['forge_hosts']), (True, ['example.test']))
        accepted = self.machine('ensure', '--yes', '--offline', env=other, cwd=clone)
        self.assertNotEqual((accepted.get('error') or {}).get('code'), 'source.identity_mismatch', accepted)
        cleared = self.machine('config', 'set', '--clear-forge-hosts', env=other, cwd=clone)
        self.assertNotIn('forge_hosts', cleared['data']['config'])


class TransportByConvention(ForgeFixture):
    """AC03: origin, then a proven hint, then gh, then the other scheme; no prompt and never the /~/ URI."""

    def add(self, typed=HTTPS, *extra):
        added = self.machine('tap', 'add', TAP, typed, *extra)
        self.assertTrue(added['ok'], added)
        return added['data']['config']['sources'][TAP]

    def test_a_project_follows_its_origin(self):
        for origin, first in (('git@github.com:Someone/App.git', SCP), ('https://github.com/Someone/App.git', HTTPS)):
            with self.subTest(origin=origin):
                home, project = self.machine_home('origin-' + sources.scheme(origin)), self.base / ('app-' + sources.scheme(origin))
                project.mkdir()
                self.git(project, 'init', '-q', '-b', 'main')
                self.git(project, 'remote', 'add', 'origin', origin)
                self.assertTrue(self.machine('tap', 'add', TAP, SCP if first == HTTPS else HTTPS, env=home)['ok'])  # The typed URL says the opposite.
                self.reached()
                self.machine('install', 'alpha', '--dry-run', env=home, cwd=project)  # A dry run never contacts the forge, whatever it reports.
                self.assertEqual(self.reached(), [])
                fetched = self.machine('install', 'alpha', env=home, cwd=project)
                self.assertTrue(fetched['ok'], fetched)
                self.assertEqual(self.reached()[0], first)
                report = fetched['data']['acquisitions'][0]['transports'][TAP]
                self.assertEqual((report['transport'], report['chosen_by'], report['tried']), (first, 'origin', []))

    def test_personal_scope_uses_gh_then_the_typed_url_then_the_probe_and_remembers_what_worked(self):
        self.add(HTTPS)
        self.gh = 'ssh'
        first = self.machine('update', '--dry-run')  # Contacts nothing.
        self.assertEqual((first['ok'], self.reached()), (True, []))
        fetched = self.machine('source', 'fetch', TAP)
        self.assertEqual((fetched['ok'], self.reached()[0]), (True, SCP))
        self.assertEqual(fetched['data']['transports'][TAP]['chosen_by'], 'gh')
        shown = self.machine('source', 'show', TAP)['data']
        self.assertEqual((shown['transport'], shown['transport_policy'], shown['chosen_by']), (SCP, 'derived', 'gh'))
        self.gh = 'https'  # A transport a fetch proved now outranks gh's stated preference.
        again = self.machine('source', 'fetch', TAP)
        self.assertEqual((self.reached()[0], again['data']['transports'][TAP]['chosen_by']), (SCP, 'hint'))
        self.gh = ''
        home = self.machine_home('no-gh')
        self.assertTrue(self.machine('tap', 'add', TAP, SCP, env=home)['ok'])
        plain = self.machine('source', 'fetch', TAP, env=home)
        self.assertEqual((self.reached()[0], plain['data']['transports'][TAP]['chosen_by']), (SCP, 'catalog'))

    def test_a_transport_that_cannot_authenticate_falls_back_and_says_so(self):
        self.add(HTTPS)
        self.assertEqual(self.human('install', 'alpha').returncode, 0)
        self.serve(https=False, ssh=True)  # This machine has an SSH key and no HTTPS credential.
        path = self.source / 'skills/alpha/SKILL.md'
        path.write_text(path.read_text(encoding='utf-8') + '\nNewer.\n', encoding='utf-8')
        self.publish('newer')
        self.reached()
        upgraded = self.human('upgrade')
        self.assertEqual(upgraded.returncode, 0, upgraded.stderr)
        self.assertEqual(self.reached()[:2], [HTTPS, SCP])
        self.assertIn(f'reached over {SCP} after {HTTPS} (git.auth_required) did not answer', upgraded.stdout)
        self.assertEqual(self.machine('source', 'show', TAP)['data']['transport'], SCP)  # Remembered: the next fetch starts there.
        self.machine('update')
        self.assertEqual(self.reached()[0], SCP)
        self.serve(https=False, ssh=False)
        nothing = self.machine('source', 'fetch', TAP)
        self.assertEqual((nothing['error']['code'], [item['transport'] for item in nothing['error']['details']['tried']]), ('git.auth_required', [SCP, HTTPS]))

    def test_a_catalog_from_before_the_rfc_never_uses_the_tilde_uri(self):
        self.add(SCP)
        config = self.document(self.home / 'config.json')
        entry = config['sources'][TAP]
        # What the previous program wrote for ``tap add git@github.com:...``: a strict identity, its cache key, and no transport policy.
        entry.update(repository=LEGACY_SSH, cache=str(sources.cache_path(self.home, TAP, LEGACY_SSH)))
        del entry['transport_policy']
        (self.home / 'config.json').write_text(c.text_json(config), encoding='utf-8')
        installed = self.human('install', 'alpha')
        self.assertEqual(installed.returncode, 0, installed.stderr)
        self.assertEqual(set(self.reached()), {SCP})
        self.assertEqual(self.document(self.project / '.mask.json')['sources'][TAP]['repository'], HTTPS)


class Pinning(ForgeFixture):
    """AC04: a pin is explicit, machine-local and exclusive."""

    def test_a_pinned_tap_tries_nothing_else_and_derive_unpins(self):
        added = self.machine('tap', 'add', TAP, HTTPS, '--pin-transport')
        self.assertEqual((added['data']['config']['sources'][TAP]['transport'], added['data']['config']['sources'][TAP]['transport_policy']), (HTTPS, 'pinned'))
        self.serve(https=False, ssh=True)
        refused = self.machine('source', 'fetch', TAP)
        self.assertEqual((refused['error']['code'], self.reached()), ('git.auth_required', [HTTPS]))
        before = (self.home / 'config.json').read_bytes()
        other = self.machine('tap', 'transport', TAP, 'git@github.com:Someone/Else.git')
        self.assertEqual((other['error']['code'], (self.home / 'config.json').read_bytes()), ('source.identity_mismatch', before))
        self.assertEqual(self.machine('tap', 'transport', TAP)['error']['code'], 'invocation.invalid')
        preview = self.machine('tap', 'transport', TAP, SSH, '--dry-run')
        self.assertEqual((preview['would_change'], preview['changed'], (self.home / 'config.json').read_bytes()), (True, False, before))
        pinned = self.machine('tap', 'transport', TAP, SSH)
        self.assertEqual((pinned['changed'], pinned['data']['transport'], pinned['data']['transport_policy']), (True, SCP, 'pinned'))
        fetched = self.machine('source', 'fetch', TAP)
        self.assertEqual((fetched['ok'], self.reached(), fetched['data']['transports'][TAP]['chosen_by']), (True, [SCP, SCP], 'pinned'))
        self.assertEqual(self.human('install', 'alpha').returncode, 0)
        for committed in ('.mask.json', '.mask.lock.json'):
            text = (self.project / committed).read_text(encoding='utf-8')
            self.assertFalse(any(word in text for word in ('transport', 'pinned', 'git@', 'forge_hosts')), committed)
        derived = self.machine('tap', 'transport', TAP, '--derive')
        self.assertEqual((derived['changed'], derived['data']['transport_policy']), (True, 'derived'))
        self.serve(https=True, ssh=False)
        self.reached()
        self.assertTrue(self.machine('source', 'fetch', TAP)['ok'])
        self.assertEqual(self.reached()[:2], [SCP, HTTPS])


class Boundaries(ForgeFixture):
    """AC06: the guarantees transport selection must not loosen."""

    def test_a_git_rewrite_to_another_repository_refuses_before_any_contact(self):
        self.assertTrue(self.machine('tap', 'add', TAP, HTTPS)['ok'])
        (self.personal / '.gitconfig').write_text('[url "https://github.com/Evil/Skills.git"]\n\tinsteadOf = ' + HTTPS + '\n', encoding='utf-8')
        refused = self.machine('source', 'fetch', TAP)
        self.assertEqual((refused['error']['code'], self.reached()), ('source.identity_mismatch', []))
        (self.personal / '.gitconfig').write_text('[url "' + SCP + '"]\n\tinsteadOf = ' + HTTPS + '\n', encoding='utf-8')
        allowed = self.machine('source', 'fetch', TAP)  # A rewrite that stays inside the identity is the user's own transport choice.
        self.assertTrue(allowed['ok'], allowed)

    def test_credentials_and_redirect_policy_still_refuse(self):
        self.assertEqual(self.machine('tap', 'add', TAP, 'https://user:token@github.com/Fixture/AgentSkills.git')['error']['code'], 'source.identity_invalid')
        self.assertTrue(self.machine('tap', 'add', TAP, HTTPS)['ok'])
        (self.personal / '.gitconfig').write_text('[http "https://github.com/"]\n\tfollowRedirects = true\n', encoding='utf-8')
        refused = self.machine('source', 'fetch', TAP)
        self.assertEqual((refused['error']['code'], self.reached()), ('source.redirect_policy', []))


if __name__ == '__main__':
    unittest.main()
