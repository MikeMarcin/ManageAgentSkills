"""Immutable raw-byte artifacts and explicit exact-commit hydration."""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import os
from pathlib import Path
import shutil
import tempfile

import mask_core as c
import mask_packages as p
import mask_resolve as r
import mask_sources as s
from mask_provenance import regular_bytes

MANIFEST_BYTES = 16 * 1024 * 1024
READ_ONLY = ContextVar('mask_store_read_only', default=False)


@contextmanager
def observational():
    """Inspection may report extra bytecode, but must never remove it."""
    token = READ_ONLY.set(True)
    try:
        yield
    finally:
        READ_ONLY.reset(token)


def location(home, digest, identifier):
    if not isinstance(digest, str) or not r.SHA.fullmatch(digest):
        c.fail('artifact.invalid', 'Artifact paths require a full SHA-256 payload digest.', 4)
    c.skill_id(identifier)
    root = Path(home) / 'store/v1' / digest[7:]
    c.parents_safe(Path(home.anchor), root / 'payload' / identifier)
    return root, root / 'payload' / identifier


def manifest(value):
    r.canonical(value, 'artifact')
    r.closed(value, ('schema_version', 'id', 'payload_digest', 'metadata_digest', 'files'), ('provenance_digest',), 'artifact')
    c.skill_id(value['id'])
    for field in ('payload_digest', 'metadata_digest', 'provenance_digest'):
        if field in value and (not isinstance(value[field], str) or not r.SHA.fullmatch(value[field])):
            c.fail('artifact.invalid', 'Invalid artifact digest.', 4)
    if not isinstance(value['files'], list) or len(value['files']) > p.FILE_COUNT:
        c.fail('artifact.invalid', 'Artifact file manifest exceeds its bound.', 4)
    names, total, directories = [], 0, set()
    for entry in value['files']:
        r.closed(entry, ('path', 'mode', 'size', 'sha256'), family='artifact')
        parts = p.portable_path(entry['path'])
        names.append(entry['path'])
        directories.update('/'.join(parts[:i]) for i in range(1, len(parts)))
        if entry['mode'] not in ('100644', '100755') or type(entry['size']) is not int or not 0 <= entry['size'] <= p.FILE_BYTES or not isinstance(entry['sha256'], str) or not r.SHA.fullmatch('sha256:' + entry['sha256']):
            c.fail('artifact.invalid', 'Invalid regular file manifest entry.', 4)
        total += entry['size']
    if total > p.PACKAGE_BYTES or len(names) + len(directories) > p.FILE_COUNT or names != sorted(set(names)):
        c.fail('artifact.invalid', 'Artifact manifest is unsorted, duplicated or exceeds package bounds.', 4)
    p.check_paths(names)
    if c.digest(value['files']) != value['payload_digest']:
        c.fail('artifact.corrupt', 'Manifest entries differ from artifact identity.', 4)
    return value


def checked_payload(payload, row):
    r.lock(dict(schema_version=1, resolver='mask-lock-v1', selection_digest='sha256:' + '0' * 64, packages=[row]))
    if not isinstance(payload, p.Payload):
        c.fail('artifact.invalid', 'Preparation requires a validated raw payload.', 4)
    checked = p.validate_files(payload.files, row['id'], commit=row['commit'], path=row['path'])
    actual = r.payload_digests(checked)
    expected = {field: row[field] for field in ('payload_digest', 'metadata_digest', 'provenance_digest') if field in row}
    if actual != expected or payload.digest != checked.digest or payload.total_bytes != checked.total_bytes or payload.id != row['id'] or payload.commit != row['commit'] or payload.path != row['path']:
        c.fail('artifact.digest_mismatch', 'Raw payload or metadata does not match the exact locked identity.', 4)
    return checked


def inventory(root):
    """Bounded no-follow enumeration includes otherwise invisible empty directories."""
    found, pending = {}, [root]
    while pending:
        directory = pending.pop()
        if c.kind(directory) != 'directory':
            c.fail('artifact.corrupt', 'Artifact contains a linked or special directory.', 4)
        with os.scandir(directory) as entries:
            for entry in entries:
                pathname = directory / entry.name
                relative = pathname.relative_to(root).as_posix()
                kind = c.kind(pathname)
                if kind not in ('directory', 'file') or kind == 'file' and pathname.lstat().st_nlink != 1:
                    c.fail('artifact.corrupt', 'Artifacts require unlinked regular files and real directories.', 4, path=relative)
                found[relative] = kind
                if len(found) > p.FILE_COUNT + 3 or len(pathname.relative_to(root).parts) > p.DEPTH + 2:
                    c.fail('artifact.corrupt', 'Artifact tree exceeds entry/depth bounds.', 4)
                if kind == 'directory':
                    pending.append(pathname)
    return found


BYTECODE = ('.pyc', '.pyo')


def shed_bytecode(root):
    """Remove interpreter bytecode from an owned artifact before its exact inventory is taken.

    A host that imports a skill's script through the managed link writes ``__pycache__`` beside it, which the
    inventory rightly refuses as an extra entry. Bytecode is never tolerated in place, because Python prefers
    a matching ``.pyc`` to the reviewed source; it is removed, and only when the directory holds nothing but
    regular bytecode files. Anything else stays for verification to refuse and a human to inspect.
    """
    directories = [root / 'payload'] if c.kind(root / 'payload') == 'directory' else []
    for directory in directories:
        with os.scandir(directory) as entries:
            children = [directory / entry.name for entry in entries]
        for child in children:
            if c.kind(child) != 'directory':
                continue
            if child.name != '__pycache__':
                directories.append(child)
                continue
            with os.scandir(child) as entries:
                droppings = [child / entry.name for entry in entries]
            if all(c.kind(item) == 'file' and item.suffix in BYTECODE for item in droppings):
                for item in droppings:
                    item.unlink()
                child.rmdir()


def verify_tree(root, row, *, clean_bytecode=True):
    r.lock(dict(schema_version=1, resolver='mask-lock-v1', selection_digest='sha256:' + '0' * 64, packages=[row]))
    if c.kind(root) != 'directory':
        c.fail('artifact.corrupt', 'Existing artifact root must be a real directory.', 4)
    original = c.identity(root)
    if clean_bytecode and not READ_ONLY.get():
        shed_bytecode(root)
    found = inventory(root)
    if found.get('manifest.json') != 'file':
        c.fail('artifact.corrupt', 'Artifact manifest is missing.', 4)
    raw = regular_bytes(root / 'manifest.json', MANIFEST_BYTES)
    try:
        value = manifest(c.parse_json(raw.decode('utf-8'), 'artifact'))
    except (UnicodeError, RecursionError):
        c.fail('artifact.invalid', 'Artifact manifest requires bounded UTF-8 JSON.', 4)
    if value['id'] != row['id'] or any(value.get(key) != row.get(key) for key in ('payload_digest', 'metadata_digest', 'provenance_digest')):
        c.fail('artifact.corrupt', 'Artifact manifest disagrees with the selected lock.', 4)
    prefix = 'payload/' + value['id']
    expected = {'manifest.json': 'file', 'payload': 'directory', prefix: 'directory'}
    files = []
    total = 0
    for entry in value['files']:
        relative = prefix + '/' + entry['path']
        parts = relative.split('/')
        expected.update(('/'.join(parts[:i]), 'directory') for i in range(1, len(parts)))
        expected[relative] = 'file'
        pathname = root / relative
        if found.get(relative) != 'file' or pathname.lstat().st_size != entry['size']:
            c.fail('artifact.corrupt', 'Artifact file is missing or has the wrong size.', 4, path=relative)
        if os.name != 'nt' and bool(pathname.lstat().st_mode & 0o111) != (entry['mode'] == '100755'):
            c.fail('artifact.corrupt', 'Artifact executable mode differs from its logical manifest.', 4, path=relative)
        data = regular_bytes(pathname, entry['size'])
        total += len(data)
        if total > p.PACKAGE_BYTES or c.digest(data) != 'sha256:' + entry['sha256']:
            c.fail('artifact.corrupt', 'Artifact bytes differ from its manifest.', 4, path=relative)
        files.append(p.PayloadFile(entry['path'], entry['mode'], data))
    if found != expected or inventory(root) != found or c.identity(root) != original:
        c.fail('artifact.corrupt', 'Artifact contains extra entries or changed during verification.', 4)
    payload = p.validate_files(files, row['id'], commit=row['commit'], path=row['path'])
    checked_payload(payload, row)
    if regular_bytes(root / 'manifest.json', MANIFEST_BYTES) != raw:
        c.fail('artifact.corrupt', 'Manifest changed during verification.', 4)
    return root / prefix


def verify(home, row):
    root, target = location(home, row['payload_digest'], row['id'])
    if c.kind(root) == 'missing':
        c.fail('artifact.unavailable', 'Exact artifact is absent from the local store.', 4, payload_digest=row['payload_digest'])
    return verify_tree(root, row)


def cleanup(stage, identity):
    if stage is None or c.kind(stage) == 'missing':
        return
    if c.kind(stage) != 'directory' or c.identity(stage) != identity:
        c.fail('artifact.stage_changed', 'Owned staging root changed; retained for inspection.', 4, path=str(stage))
    # Windows read-only attributes must be cleared only within this owned stage.
    for directory, dirs, files in os.walk(stage, followlinks=False):
        for name in files:
            pathname = Path(directory) / name
            if c.kind(pathname) == 'file':
                pathname.chmod(0o600)
    shutil.rmtree(stage)


def materialize(home, row, payload, *, dry_run=False, effects=None):
    checked = checked_payload(payload, row)
    root, target = location(home, row['payload_digest'], row['id'])
    effects = effects if effects is not None else {}
    effects.update(path=str(target), reused=False, created=False, retained_directories=[])
    if c.kind(root) != 'missing':
        verify_tree(root, row)
        effects['reused'] = True
        return effects
    value = manifest(dict(schema_version=1, id=row['id'], files=checked.manifest(), **r.payload_digests(checked)))
    serialized = r.canonical(value, 'artifact') + b'\n'
    if len(serialized) > MANIFEST_BYTES:
        c.fail('artifact.limit', 'Serialized artifact manifest exceeds 16 MiB.', 4)
    if dry_run:
        effects['would_create'] = True
        return effects
    c.parents_safe(Path(home.anchor), root / 'manifest.json')
    home_identity = c.identity(home)
    absent = [path for path in (home / 'store', root.parent) if c.kind(path) == 'missing']
    try:
        root.parent.mkdir(parents=True, exist_ok=True)
    finally:
        effects['retained_directories'] = [str(path) for path in absent if c.kind(path) == 'directory']
    parent_identity = c.identity(root.parent)
    stage = Path(tempfile.mkdtemp(prefix='.mask-stage-', dir=root.parent))
    identity = c.identity(stage)
    try:
        payload_root = stage / 'payload' / row['id']
        payload_root.mkdir(parents=True)
        for entry in checked.files:
            pathname = payload_root / entry.path
            pathname.parent.mkdir(parents=True, exist_ok=True)
            with pathname.open('xb') as handle:
                handle.write(entry.data)
                handle.flush()
                os.fsync(handle.fileno())
            pathname.chmod(0o555 if entry.mode == '100755' else 0o444)
        with (stage / 'manifest.json').open('xb') as handle:
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
        (stage / 'manifest.json').chmod(0o444)
        verify_tree(stage, row)
        c.parents_safe(Path(home.anchor), root / 'manifest.json')
        if c.identity(home) != home_identity or c.identity(root.parent) != parent_identity or c.identity(stage) != identity:
            c.fail('artifact.stage_changed', 'Store parent or staging identity changed before publication.', 4)
        try:
            c.publish_directory(stage, root)
        except c.MaskError as error:
            if error.code == 'import.collision':
                verify_tree(root, row)
                effects['reused'] = True
                return effects
            raise
        stage = None
        effects['created'] = True
        return effects
    finally:
        cleanup(stage, identity)


def exact_cached(home, row, entry):
    """Whether the approved tap cache already holds the exact locked commit; never fetches."""
    cache = s.cached(home, row['source'], entry)
    return cache is not None and c.peeled_commit(cache, row['commit']) == row['commit']


def cached_payload(home, row, config):
    """The exact locked bytes of an absent artifact, read from its approved tap cache, or None when the cache lacks the commit.

    A plan examines them so a preview sees the package the applying run materializes; nothing is fetched or written.
    """
    entry = s.selected(config, row['source'])
    return r.verify_resolution(home, row['source'], entry, row) if exact_cached(home, row, entry) else None


def ensure(home, declaration, resolved, config, *, offline=True, dry_run=False, effects=None, coordinates=None):
    """Prepare exact artifacts only. Default is cache-only; never activate links."""
    declaration = r.selection(declaration)
    resolved = r.lock(resolved, declaration)
    entries = r.approved(declaration, config)
    selected = {r.coordinate(row) for row in resolved['packages']}
    if coordinates is not None:
        if not isinstance(coordinates, (list, tuple, set)) or any(not isinstance(key, str) for key in coordinates) or len(set(coordinates)) != len(coordinates) or set(coordinates) - selected:
            c.fail('artifact.invalid', 'Preparation subset must contain unique selected coordinates.', 4)
        selected = set(coordinates)
    effects = effects if effects is not None else {}
    effects.update(network_attempted=False, acquisitions=[], artifacts=[])
    for row in resolved['packages']:
        if r.coordinate(row) not in selected:
            continue
        root, target = location(home, row['payload_digest'], row['id'])
        if c.kind(root) != 'missing':
            verify_tree(root, row)
            effects['artifacts'].append(dict(path=str(target), reused=True, created=False))
            continue
        entry = entries[row['source']]
        if not exact_cached(home, row, entry):
            if dry_run:
                effects['artifacts'].append(dict(path=str(target), created=False, resolution_required=True, commit=row['commit']))
                continue
            if offline:
                c.fail('artifact.unavailable', 'Exact locked commit is not cached; offline preparation cannot fetch or substitute it.', 4, commit=row['commit'])
            acquisition = dict(source=row['source'])
            effects['acquisitions'].append(acquisition)
            try:
                s.acquire_exact(home, row['source'], entry, row['commit'], config['git_timeout_seconds'], acquisition)
            finally:
                effects['network_attempted'] |= acquisition.get('network_attempted', False)
        payload = r.verify_resolution(home, row['source'], entry, row)
        observation = {}
        effects['artifacts'].append(observation)
        materialize(home, row, payload, dry_run=dry_run, effects=observation)
    return effects


def dispatch(args, output, home):
    scope = 'user' if getattr(args, 'user', False) else 'project'
    root = home if scope == 'user' else c.project_root(getattr(args, 'project', None))
    config = c.config(c.read_json(home / 'config.json'))
    declaration, resolved = r.read_exact_lock(root, scope, home, config, verify=False)
    output['data'] = dict(scope=scope, preparation_only=True, consumer_changes=False)
    effects = output['data']['effects'] = {}
    try:
        ensure(home, declaration, resolved, config, offline=getattr(args, 'offline', False), dry_run=output['dry_run'], effects=effects)
    finally:
        retained = any(entry.get('created') or entry.get('retained_directories') for entry in effects.get('artifacts', []))
        acquired = any(entry.get('cache_created') or entry.get('acquired') or entry.get('retained_objects_possible') for entry in effects.get('acquisitions', []))
        output['changed'] = bool(retained or acquired) and not output['dry_run']
        output['would_change'] = bool(retained or acquired or any(entry.get('would_create') or entry.get('resolution_required') for entry in effects.get('artifacts', [])))
        if output['changed']:
            output['transaction'] = 'committed' if sum(bool(entry.get('created') or entry.get('reused')) for entry in effects.get('artifacts', [])) == len(resolved['packages']) else 'partial'
