"""Exact fleet package forwarding. Wire paths are package-relative regular files."""
from __future__ import annotations

import base64
import binascii

import mask_core as c
import mask_fleet as fleet
import mask_packages as packages
import mask_resolve as resolve
import mask_selection as selection
import mask_store as store

MAX_TRANSFER = 5 * 1024 * 1024
MAX_PACKAGES = 32
PACKET_FIELDS = ('coordinate', 'commit', 'payload_digest', 'files')
FILE_FIELDS = ('path', 'mode', 'size', 'sha256', 'data')


def exact_key(row):
    return resolve.coordinate(row), row['commit'], row['payload_digest']


def packet(home, row):
    """Build an exact package packet from a controller's verified local store."""
    payload = store.verify(home, row, as_payload=True)
    if payload.total_bytes > MAX_TRANSFER:
        c.fail('fleet.artifact_limit', 'This package exceeds the fleet forwarding limit. Use exact Git retrieval.', 4)
    return dict(coordinate=resolve.coordinate(row), commit=row['commit'], payload_digest=row['payload_digest'],
                files=[dict(entry.manifest_entry(), data=base64.b64encode(entry.data).decode('ascii'))
                       for entry in payload.files])


def applicable_rows(layers):
    for layer in layers:
        selected = set(selection.applicable_coordinates(layer['declaration']))
        for row in layer['lock']['packages']:
            if resolve.coordinate(row) in selected:
                yield row


def decode(value, row, remaining):
    files, size = [], 0
    if not isinstance(value, list) or not 1 <= len(value) <= packages.FILE_COUNT:
        fleet.invalid('Forwarded packages require a bounded, nonempty file list.')
    for entry in value:
        c.fields(entry, FILE_FIELDS, family='fleet')
        packages.portable_path(entry['path'])
        if entry['mode'] not in ('100644', '100755'):
            fleet.invalid('Forwarded entries must be regular files.')
        count = fleet.number(entry['size'])
        size += count
        encoded = entry['data']
        if size > remaining or not isinstance(encoded, str) or len(encoded) != 4 * ((count + 2) // 3):
            c.fail('fleet.artifact_limit', 'Forwarded files exceed the declared length or transfer bound.', 4)
        try:
            data = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError):
            fleet.invalid('Forwarded file bytes require base64.')
        if len(data) != count or 'sha256:' + str(entry['sha256']) != c.digest(data):
            c.fail('fleet.artifact_mismatch', 'Forwarded file bytes differ from their signed manifest.', 4)
        files.append(packages.PayloadFile(entry['path'], entry['mode'], data))
    if [entry.path for entry in files] != sorted(entry.path for entry in files):
        fleet.invalid('Forwarded file manifests require canonical path order.')
    payload = packages.validate_files(files, row['id'], commit=row['commit'], path=row['path'])
    return store.checked_payload(payload, row), size


def transfers(values, scope, layers):
    if not isinstance(values, list) or len(values) > MAX_PACKAGES:
        c.fail('fleet.artifact_limit', 'Too many forwarded packages in one request.', 4)
    allowed = {exact_key(row): row for row in applicable_rows(layers)}
    seen, prepared, total = set(), [], 0
    for entry in values:
        c.fields(entry, PACKET_FIELDS, family='fleet')
        key = tuple(entry[field] for field in PACKET_FIELDS[:-1])
        if any(not isinstance(item, str) for item in key) or key in seen:
            fleet.invalid('Expected unique exact package identities in forwarding.')
        row = allowed.get(key)
        if row is None:
            c.fail('fleet.artifact_unselected', 'A forwarded artifact must match a locally selected exact lock.', 4)
        if not scope['sources'][row['source']]['forward']:
            c.fail('fleet.artifact_forward_denied', 'The device owner has not authorized forwarding for that source.', 4)
        seen.add(key)
        payload, size = decode(entry['files'], row, MAX_TRANSFER - total)
        total += size
        prepared.append((row, payload))
    return prepared
