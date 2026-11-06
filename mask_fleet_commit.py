"""Bounded proof of a canonical control-only Git commit."""
from __future__ import annotations

import base64
import binascii
import hashlib
from pathlib import Path
import re
import tempfile

import mask_core as c
import mask_upgrade_commit as commits

LIMIT = 72 * 1024
OBJECTS = ('commit', 'parent', 'tree', 'parent_tree')


def refuse():
    c.fail('fleet.commit_proof_invalid', 'The transferred Git commit does not prove the approved control-only change.', 4)


def oid(kind, raw, algorithm):
    return hashlib.new(algorithm, f'{kind} {len(raw)}\0'.encode('ascii') + raw).hexdigest()


def object_type(key):
    return 'tree' if key.endswith('tree') else 'commit'


def object_id(raw, prefix):
    matches = [line[len(prefix):] for line in raw.partition(b'\n\n')[0].split(b'\n') if line.startswith(prefix)]
    if len(matches) != 1 or not re.fullmatch(rb'[0-9a-f]{40}|[0-9a-f]{64}', matches[0]):
        refuse()
    return matches[0].decode('ascii')


def pack(root, commit, timeout):
    algorithm = c.git(root, 'rev-parse', '--show-object-format', timeout=timeout)
    raw = {}
    for key, revision in zip(OBJECTS, (commit, commit + '^', commit + '^{tree}', commit + '^' + '^{tree}')):
        raw[key] = c.git(root, 'cat-file', object_type(key), revision, binary=True, timeout=timeout, max_output=LIMIT)
    if sum(map(len, raw.values())) > LIMIT:
        c.fail('fleet.commit_proof_limit', 'The canonical commit proof exceeds the bounded transfer allowance.', 4)
    return dict(commit=commit, format=algorithm,
                objects={key: base64.b64encode(value).decode('ascii') for key, value in raw.items()})


def unpack(packet):
    c.fields(packet, ('commit', 'format', 'objects'), family='fleet', versions=())
    algorithm = packet['format']
    if algorithm not in ('sha1', 'sha256'):
        refuse()
    c.fields(packet['objects'], OBJECTS, family='fleet', versions=())
    raw = {}
    try:
        for key in OBJECTS:
            data = packet['objects'][key]
            if not isinstance(data, str) or len(data) > 4 * LIMIT // 3 + 4:
                refuse()
            raw[key] = base64.b64decode(data, validate=True)
    except (ValueError, binascii.Error):
        refuse()
    if sum(map(len, raw.values())) > LIMIT:
        refuse()
    ids = {key: oid(object_type(key), value, algorithm) for key, value in raw.items()}
    if (ids['commit'], ids['parent'], ids['tree'], ids['parent_tree']) != (
            packet['commit'], object_id(raw['commit'], b'parent '),
            object_id(raw['commit'], b'tree '), object_id(raw['parent'], b'tree ')):
        refuse()
    return raw, ids


def entries(root, tree, timeout):
    data = c.git(root, 'ls-tree', '-z', tree, binary=True, timeout=timeout, max_output=2 * LIMIT)
    return dict((name, metadata) for metadata, _, name in (part.partition(b'\t') for part in data.split(b'\0') if part))


def write_object(root, kind, raw, timeout):
    return c.git(root, 'hash-object', '-w', '--stdin', '-t', kind, input=raw, timeout=timeout, mutating=True)


def verify(root, packet, approved, final, timeout, *, before_head):
    """Verify both Git trees against the reviewed path digests before importing any reachable object."""
    raw, ids = unpack(packet)
    algorithm = packet['format']
    if ids['parent'] != approved['parent'] or algorithm != c.git(root, 'rev-parse', '--show-object-format', timeout=timeout):
        refuse()
    with tempfile.TemporaryDirectory(prefix='mask-fleet-commit-') as directory:
        scratch = Path(directory)
        c.git(scratch, 'init', '--bare', '--object-format=' + algorithm, timeout=timeout)
        for key, value in raw.items():
            write_object(scratch, object_type(key), value, timeout)
        before = entries(scratch, ids['parent_tree'], timeout)
        after = entries(scratch, ids['tree'], timeout)
        controls = {path.encode('ascii') for path in commits.PATHS}
        if any(before.get(path) != after.get(path) for path in (before.keys() | after.keys()) - controls):
            refuse()
        for path in commits.PATHS:
            name = path.encode('ascii')
            previous = c.git(root, 'show', before_head + ':' + path, binary=True, timeout=timeout)
            before_oid = oid('blob', previous, algorithm).encode('ascii')
            after_oid = oid('blob', final[path], algorithm).encode('ascii')
            valid_modes = (b'100644 blob ', b'100755 blob ')
            if (c.digest(previous) != approved['controls'][path] or
                    before.get(name) not in {mode + before_oid for mode in valid_modes} or
                    after.get(name) not in {mode + after_oid for mode in valid_modes} or
                    before[name].split(b' ', 1)[0] != after[name].split(b' ', 1)[0]):
                refuse()
        message = c.git(scratch, 'log', '-1', '--format=%B', ids['commit'], timeout=timeout)
        if message != commits.MESSAGE:
            refuse()
        author = c.git(scratch, 'log', '-1', '--format=%an%x00%ae%x00%aI', ids['commit'], timeout=timeout).split('\0')
        if len(author) != 3 or any(not item or any(ord(char) < 32 for char in item) for item in author):
            refuse()
        updates = commits.control_entries(scratch, ids['commit'], commits.PATHS, timeout)
    return dict(commit=ids['commit'], parent=ids['parent'], author=author, message=message, updates=updates,
                raw={key: raw[key] for key in ('commit', 'tree')} if ids['parent'] == before_head else {})


def import_exact(root, proof, final, timeout):
    for value in final.values():
        write_object(root, 'blob', value, timeout)
    for kind, value in proof['raw'].items():
        write_object(root, kind, value, timeout)
