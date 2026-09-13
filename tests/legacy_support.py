"""Schema-true legacy starting states for RFC-MASK-0020 (MASK-0098).

The live-checkout program at RFC_BASE_SHA ``b92372f`` wrote these files. The
builder writes the same bytes directly, without running MASK, so doctor-migration
tests can start from what that program left on disk after its commands are
retired. ``tests.test_legacy_baseline`` proves that the base program's own output
equals these bytes and that the current parsers accept them unchanged.

The builder never fetches a cache, materializes a store, writes a lock or a
pending journal, converts a declaration or registers the unregistered v1
declaration. Later cards prove those effects through the public CLI.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

ENTRY = Path(__file__).resolve().parents[1] / 'mask.py'
# Built-in agent paths; project and personal scope use the same relative paths.
AGENT_PATHS = {'claude': '.claude/skills', 'codex': '.agents/skills'}
DEFAULT_TARGETS = ('claude', 'codex')


def text_json(value):
    """The base program's on-disk JSON form (``mask_core.text_json``)."""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'


def digest(value):
    """The base program's canonical JSON digest (``mask_core.digest``)."""
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


def link_text(target):
    """The directory-link text the base program recorded (``mask_fs.creation_link_text``)."""
    raw = str(target)
    if os.name == 'nt' and not raw.startswith('\\\\?\\'):
        return '\\\\?\\UNC\\' + raw[2:] if raw.startswith('\\\\') else '\\\\?\\' + raw
    return raw


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], capture_output=True, encoding='utf-8', check=True).stdout.strip()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as handle:
        handle.write(text_json(value))


def layout(base):
    """Fixed roots under one disposable base; nothing is created here."""
    base = Path(base)
    return SimpleNamespace(base=base, home=base / 'machine', personal=base / 'personal home',
                           project=base / 'project with ü spaces', straggler=base / 'unregistered project',
                           clone=base / 'AgentSkills', upstream=base / 'upstream' / 'AgentSkills.git',
                           extra=base / 'upstream' / 'extra.git')


def add_skill(clone, identifier, description='Fixture skill'):
    root = clone / 'skills' / identifier
    root.mkdir(parents=True)
    (root / 'SKILL.md').write_text(f'---\nname: {identifier}\ndescription: {description}\n---\n\nFixture only.\n',
                                   encoding='utf-8', newline='\n')
    return root


def make_clone(roots, skills=('alpha', 'beta'), remote=True, branch='main'):
    """The user's authoring clone with committed packages, pushed to a local bare upstream when ``remote``."""
    roots.clone.mkdir(parents=True)
    git(roots.clone, 'init', '-b', branch)
    git(roots.clone, 'config', 'user.name', 'Fixture')
    git(roots.clone, 'config', 'user.email', 'fixture@example.invalid')
    for identifier in skills:
        add_skill(roots.clone, identifier)
    git(roots.clone, 'add', 'skills')
    git(roots.clone, 'commit', '-m', 'fixture skills')
    if remote:
        make_bare(roots.upstream, branch)
        git(roots.clone, 'remote', 'add', 'origin', str(roots.upstream))
        git(roots.clone, 'push', '-q', 'origin', branch)


def make_bare(path, branch='main'):
    path.mkdir(parents=True)
    git(path, 'init', '-q', '--bare', '-b', branch)


def v1_config(roots, *, targets=DEFAULT_TARGETS, remote='origin', branch='main', timeout=30):
    """What ``init --source CLONE`` wrote."""
    return dict(schema_version=1, source=dict(root=str(roots.clone), remote=remote, branch=branch),
                default_targets=sorted(targets), git_timeout_seconds=timeout)


def source_binding(home, name, transport, *, ref='main', packages='skills', authoring=None):
    """A catalog entry for an absolute local transport (``mask_sources.binding``)."""
    local = Path(transport).resolve()
    identity = local.as_uri()
    return dict(repository=identity, transport=str(local),
                cache=str(Path(home) / 'sources' / (name + '-' + digest(identity)[7:23] + '.git')),
                ref=ref, packages=packages, authoring=authoring)


def v2_config(roots, *, alias='legacy', extra_tap=True, **options):
    """What ``source migrate`` and then ``tap add extra PATH`` wrote; the clone stays the legacy authoring root."""
    config = v1_config(roots, **options)
    remote = subprocess.run(['git', '-C', str(roots.clone), 'remote', 'get-url', config['source']['remote']],
                            capture_output=True, encoding='utf-8')
    transport = remote.stdout.strip() if remote.returncode == 0 else str(roots.clone)
    catalog = {alias: source_binding(roots.home, alias, transport, ref=config['source']['branch'], authoring=str(roots.clone))}
    if extra_tap:
        catalog['extra'] = source_binding(roots.home, 'extra', roots.extra)
    config.update(schema_version=2, legacy_source=alias, sources=catalog)
    return config


def legacy_record(roots, root, skills, *, default_targets=DEFAULT_TARGETS):
    """A mode-less consumer record and its v1 declaration, as legacy ``install`` registered them."""
    declaration = dict(schema_version=1, skills=sorted(skills))
    links = {AGENT_PATHS[agent] + '/' + identifier: dict(skill=identifier, target=agent, link_text=link_text(roots.clone / 'skills' / identifier))
             for identifier in declaration['skills'] for agent in sorted(default_targets)}
    info = Path(root).stat()
    record = dict(root=str(root), root_identity=dict(device=info.st_dev, inode=info.st_ino), last_manifest=declaration,
                  last_manifest_digest=digest(declaration), last_source_revision=git(roots.clone, 'rev-parse', 'HEAD'), links=links)
    return declaration, record


def legacy_state(project_records=(), user_record=None):
    """State v1, or v2 once a personal record exists; one generation per registering transaction."""
    state = dict(schema_version=1 if user_record is None else 2, generation=len(project_records) + int(user_record is not None),
                 projects={record['root']: record for record in project_records}, launchers={})
    if user_record is not None:
        state['user'] = user_record
    return state


def create_links(root, record):
    for relative, link in sorted(record['links'].items()):
        leaf = Path(root) / relative
        leaf.parent.mkdir(parents=True, exist_ok=True)
        os.symlink(link['link_text'], leaf, target_is_directory=True)


def write_machine(roots, version=1, *, project_skills=('alpha',), user_skills=('beta',), straggler_skills=('alpha',), extra_tap=True):
    """Write a legacy machine over an existing clone and consumer directories; ``None`` omits a consumer."""
    if version not in (1, 2):
        raise ValueError('legacy machines are version 1 or 2')
    config = v1_config(roots) if version == 1 else v2_config(roots, extra_tap=extra_tap)
    projects, user = [], None
    if project_skills is not None:
        declaration, record = legacy_record(roots, roots.project, project_skills)
        write_json(roots.project / '.mask.json', declaration)
        create_links(roots.project, record)
        projects.append(record)
    if user_skills is not None:
        declaration, user = legacy_record(roots, roots.personal, user_skills)
        write_json(roots.home / 'user.json', declaration)
        create_links(roots.personal, user)
    if straggler_skills is not None:
        write_json(roots.straggler / '.mask.json', dict(schema_version=1, skills=sorted(straggler_skills)))
    state = legacy_state(projects, user)
    write_json(roots.home / 'config.json', config)
    write_json(roots.home / 'state.json', state)
    return config, state


def build_legacy_machine(base, version=1, *, remote=True, **options):
    """A complete legacy starting state: clone, machine, legacy project, legacy personal scope, unregistered declaration."""
    roots = layout(base)
    for directory in (roots.personal, roots.project, roots.straggler):
        directory.mkdir(parents=True)
    git(roots.project, 'init', '-q', '-b', 'main')
    make_clone(roots, remote=remote)
    if version == 2 and options.get('extra_tap', True):
        make_bare(roots.extra)
    roots.config, roots.state = write_machine(roots, version, **options)
    return roots


def remove_entry(path):
    """Remove one file or link; a Windows directory link is removed with rmdir, never followed."""
    if os.name == 'nt' and path.is_symlink() and path.is_dir():
        os.rmdir(path)
    else:
        path.unlink()


def snapshot(base, *roots, ignore=('.git', 'operation.lock')):
    """Files and links (not directories) under ``roots``, keyed relative to ``base``; links are never followed."""
    observed = {}
    for root in roots:
        for parent, directories, files in os.walk(root, followlinks=False):
            directories[:] = [name for name in directories if name not in ignore]
            for name in directories + files:
                path = Path(parent) / name
                if name in ignore:
                    continue
                key = path.relative_to(base).as_posix()
                if path.is_symlink():
                    observed[key] = ('link', os.readlink(path))
                elif path.is_file():
                    observed[key] = ('file', path.read_bytes())
    return observed


class LegacyFixture(unittest.TestCase):
    """A disposable base with private MASK_HOME and personal home; nothing is prepared until a test asks."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='mask-legacy-')
        self.addCleanup(self.temp.cleanup)
        self.roots = layout(Path(self.temp.name).resolve())

    def legacy_machine(self, version=1, **options):
        self.roots = build_legacy_machine(self.roots.base, version, **options)
        return self.roots

    def environment(self):
        # Path.home() reads USERPROFILE on Windows and HOME on POSIX; both point at the fixture's personal home.
        env = dict(os.environ, MASK_HOME=str(self.roots.home), HOME=str(self.roots.personal), USERPROFILE=str(self.roots.personal),
                   PYTHONDONTWRITEBYTECODE='1', GIT_TERMINAL_PROMPT='0')
        env.pop('MASK_USER_HOME', None)
        return env

    def machine(self, *args, code=0):
        run = subprocess.run([sys.executable, '-B', str(ENTRY), *map(str, args), '--json'], capture_output=True, encoding='utf-8',
                             cwd=str(self.roots.base), env=self.environment(), timeout=120)
        self.assertEqual(run.stderr, '', run.stderr)
        data = json.loads(run.stdout)
        self.assertEqual(run.returncode, code, run.stdout)
        self.assertEqual(data['ok'], code == 0, run.stdout)
        return data
