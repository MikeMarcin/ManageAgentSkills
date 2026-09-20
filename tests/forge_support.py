"""A forge host without a network, for RFC-MASK-0022 (transport-neutral tap identity).

MASK reaches a tap only through ``git``, so a ``git`` found first on PATH stands in for the forge: a network
command (``ls-remote`` or ``fetch``) naming a forge URL is served from the fixture's local bare upstream, or
denied as a forge denies a machine without that credential, and is recorded in a log. Everything else, including
``ls-remote --get-url`` and so every endpoint-rewrite check, runs the real Git unchanged. A forge URL the fixture
did not map is denied, never sent to the real host. A ``gh`` beside it answers ``git_protocol`` from the
environment, so no developer machine's own ``gh`` leaks into a test.

Nothing here prepares MASK state: taps are added, fetched and deployed by the commands under test.
"""
import json
import os
from pathlib import Path
import shutil
import sys
import unittest

from tests.public_support import PublicFixture

HTTPS = 'https://github.com/Fixture/AgentSkills.git'
SCP = 'git@github.com:Fixture/AgentSkills.git'
SSH = 'ssh://git@github.com/Fixture/AgentSkills.git'
BARE_HTTPS = 'https://github.com/Fixture/AgentSkills'
LEGACY_SSH = 'ssh://git@github.com/~/Fixture/AgentSkills.git'  # How MASK spelled the scp form before RFC-MASK-0022; never a usable URL.
DENY = 'DENY'

GIT_SHIM = '''#!{python}
import json, os, sys
real, args = os.environ['MASK_TEST_REAL_GIT'], sys.argv[1:]
table = json.loads(os.environ.get('MASK_TEST_FORGE') or '{{}}')
network = any(word in ('ls-remote', 'fetch') for word in args) and '--get-url' not in args
forge = [word for word in args if word.startswith(('https://github.com/', 'ssh://git@github.com/', 'git@github.com:'))] if network else []
if forge:
    with open(os.environ['MASK_TEST_FORGE_LOG'], 'a', encoding='utf-8') as log:
        log.write(forge[0] + '\\n')
    target = table.get(forge[0], 'DENY')
    if target == 'DENY':
        sys.stderr.write('git@github.com: Permission denied (publickey).\\nfatal: Could not read from remote repository.\\n')
        sys.exit(128)
    served, index = [], 0
    while index < len(args):  # The local path stands in for the forge, so the protocol allow-list that named https or ssh is dropped.
        if args[index] == '-c' and index + 1 < len(args) and args[index + 1].startswith('protocol.'):
            index += 2
            continue
        served.append(target if args[index] == forge[0] else args[index])
        index += 1
    args = served
os.execv(real, [real, *args])
'''

GH_SHIM = '''#!{python}
import os, sys
answer = os.environ.get('MASK_TEST_GH', '')
if sys.argv[1:4] == ['config', 'get', 'git_protocol'] and answer:
    print(answer)
    sys.exit(0)
sys.exit(1)
'''


@unittest.skipIf(os.name == 'nt', 'The PATH shim is a POSIX script')
class ForgeFixture(PublicFixture):
    """The public fixture with its upstream served as ``github.com/Fixture/AgentSkills`` over HTTPS, SSH or both."""

    def raw(self, *args, **kwargs):
        if args and args[0] in ('install', 'upgrade'):
            args = (*args, '--no-update')
        return super().raw(*args, **kwargs)

    def bootstrap(self):
        self.shim = self.base / 'shim'
        self.shim.mkdir()
        for name, text in (('git', GIT_SHIM), ('gh', GH_SHIM)):
            path = self.shim / name
            path.write_text(text.format(python=sys.executable), encoding='utf-8')
            path.chmod(0o755)
        self.real_git = shutil.which('git')
        self.log = self.base / 'forge.log'
        self.serve(https=True, ssh=True)
        self.gh = ''

    def serve(self, *, https, ssh):
        """Which transports this machine can authenticate; the other is denied as a forge denies a missing credential."""
        upstream = str(self.upstream)
        self.forge = {HTTPS: upstream if https else DENY, BARE_HTTPS: upstream if https else DENY, SCP: upstream if ssh else DENY, SSH: upstream if ssh else DENY}

    def environment(self, extra=None):
        env = super().environment(extra)
        env.update(PATH=str(self.shim) + os.pathsep + env['PATH'], MASK_TEST_REAL_GIT=self.real_git, MASK_TEST_FORGE=json.dumps(self.forge),
                   MASK_TEST_FORGE_LOG=str(self.log), MASK_TEST_GH=self.gh)
        if extra:
            env.update(extra)
        return env

    def reached(self):
        """Forge URLs contacted since the last call, in order."""
        lines = self.log.read_text(encoding='utf-8').split() if self.log.exists() else []
        self.log.write_text('', encoding='utf-8')
        return lines

    def machine_home(self, name):
        """Another machine: its own MASK_HOME and personal home, sharing only the forge."""
        home, personal = self.base / name / 'machine', self.base / name / 'personal'
        personal.mkdir(parents=True)
        return dict(MASK_HOME=str(home), HOME=str(personal), USERPROFILE=str(personal))

    @staticmethod
    def document(path):
        return json.loads(Path(path).read_text(encoding='utf-8'))
