"""Per-operation signed device receipts on a repository separate from intent."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
import tempfile

import mask_control as control
import mask_core as c
import mask_fleet as fleet


def receipt_ref(entry, target):
    return 'refs/heads/mask-receipts/' + fleet.identifier(target['device']) + '/' + fleet.identifier(entry['operation'])


@contextmanager
def scratch(settings):
    endpoint = dict(repository=settings['receipts'])
    with tempfile.TemporaryDirectory(prefix='mask-receipts-') as temp:
        root = Path(temp)
        c.git(root, '-c', 'init.templateDir=', 'init', '--bare', '--object-format=sha1', mutating=True)
        yield root, endpoint


def read_at(root, endpoint, ref, head):
    control.network(root, endpoint, 'fetch', '--no-tags', '--no-recurse-submodules', '--depth=1',
                    endpoint['repository'], ref, mutating=True)
    if c.git(root, 'rev-parse', 'FETCH_HEAD^{commit}') != head:
        c.fail('fleet.receipt_changed', 'The receipt ref moved while being read.', 4)
    if c.git(root, 'ls-tree', head) != c.git(root, 'ls-tree', head, '--', 'receipt.json'):
        c.fail('fleet.receipt_invalid', 'The receipt ref must contain only its signed device response.', 4)
    raw = c.git(root, 'cat-file', 'blob', head + ':receipt.json', binary=True, max_output=fleet.RECORD_BYTES)
    return fleet.record(raw)


def read(settings, entry, target):
    if 'receipts' not in settings:
        return None
    from mask_rollout import proof_result
    with scratch(settings) as (root, endpoint):
        ref = receipt_ref(entry, target)
        head = control.remote_head(root, endpoint, ref)
        if head is None:
            return None
        return proof_result(read_at(root, endpoint, ref, head), entry, target)


def publish(settings, entry, target, record):
    from mask_rollout import proof_result
    if proof_result(record, entry, target) is None:
        c.fail('fleet.receipt_invalid', 'Only a verified signed application can publish a receipt.', 4)
    ref = receipt_ref(entry, target)
    with scratch(settings) as (root, endpoint):
        head = control.remote_head(root, endpoint, ref)
        if head is not None:
            if proof_result(read_at(root, endpoint, ref, head), entry, target) is not None:
                return head
            c.fail('fleet.receipt_conflict', 'An unverified object occupies the device receipt ref.', 4)
        raw = fleet.signed_bytes(record)
        if len(raw) > fleet.RECORD_BYTES:
            c.fail('fleet.receipt_limit', 'Signed receipt exceeds its byte limit.', 4)
        blob = c.git(root, 'hash-object', '-w', '--stdin', input=raw, mutating=True)
        tree = c.git(root, 'mktree', input=f'100644 blob {blob}\treceipt.json\n'.encode(), mutating=True)
        commit = c.git(root, '-c', 'user.name=MASK receipt', '-c', 'user.email=mask@mask.invalid',
                       'commit-tree', '--no-gpg-sign', tree, '-m', 'Record exact MASK device receipt', mutating=True)
        try:
            control.network(root, endpoint, 'push', '--porcelain', '--no-follow-tags', '--force-with-lease=' + ref + ':',
                            endpoint['repository'], commit + ':' + ref, mutating=True)
        except c.MaskError:
            if control.remote_head(root, endpoint, ref) != commit:
                c.fail('fleet.receipt_publication_unknown', 'Device apply is durable but receipt publication is unconfirmed.', 4)
        return commit
