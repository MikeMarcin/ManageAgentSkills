"""Signed desired revisions on a dedicated, explicitly configured Git ref."""
from __future__ import annotations

from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from pathlib import Path
import re
import tempfile
import time

import mask_core as c
import mask_fleet as fleet
import mask_profiles as profiles
import mask_sources as sources

REF = 'refs/heads/mask-fleet'
NAMESPACE = 'mask-desired@mask.invalid'
MAX_HISTORY = 1024
MAX_REVISION = 2 * 1024 * 1024
MAX_DEVICES = 64
MAX_TTL = 30 * 24 * 3600
OPERATIONS = ('install', 'update', 'remove', 'cancel')
GIT_OID = re.compile(r'[0-9a-f]{40}')


def invalid(message):
    c.fail('fleet.control_invalid', message, 4)


def endpoint(value):
    value = sources.spelling(value)
    if len(value) > 2048:
        invalid('Control repository URI is too long.')
    return value


def settings(home, *, missing=False):
    value = fleet.data(fleet.path(home, 'control'), missing=missing)
    if value is not None:
        c.fields(value, ('schema_version', 'repository', 'epoch'), ('import_mode', 'receipts'), family='fleet')
        if endpoint(value['repository']) != value['repository'] or value.get('import_mode') not in (None, 'copy', 'tap'):
            invalid('Invalid local control configuration.')
        fleet.number(value['epoch'], minimum=1)
        validate_receipt_repository(value)
    return value


def configure(args, output, home):
    value = dict(schema_version=1, repository=endpoint(args.repository))
    if hasattr(args, 'epoch'):
        value['epoch'] = fleet.number(args.epoch, minimum=1)
    if hasattr(args, 'import_mode'):
        if args.import_mode not in ('copy', 'tap'):
            c.fail('invocation.invalid', 'Choose copy or tap for --import-mode.', 2)
        value['import_mode'] = args.import_mode
    if hasattr(args, 'receipts'):
        value['receipts'] = endpoint(args.receipts)
    validate_receipt_repository(value)
    path = fleet.path(home, 'control')
    with (nullcontext() if output['dry_run'] else c.writer_lock(home)):
        previous = settings(home, missing=True)
        if previous:
            value = dict(previous, **value)
            validate_receipt_repository(value)
        value.setdefault('epoch', 1)
        if previous and (value['repository'] != previous['repository'] or value['epoch'] < previous['epoch']):
            invalid('A control history cannot be replaced or lowered in place.')
        output['data']['control'] = value
        fleet.review(output, args, value, previous)
        if not output['dry_run']:
            output['changed'] = fleet.put(path, value, previous)
            if output['changed']:
                output['transaction'] = 'committed'


def validate_receipt_repository(value):
    if 'receipts' in value and (endpoint(value['receipts']) != value['receipts'] or
                                sources.same(value['receipts'], value['repository'])):
        invalid('Device receipts require a separate approved repository.')


def desired_profile(declaration, lock):
    declaration, lock = profiles.portable(declaration, lock)
    return dict(revision=c.digest(dict(declaration=declaration, lock=lock)), declaration=declaration, lock=lock)


def validate_profile(profile):
    profiles.subscriptions({'fleet': profile})
    if profile != desired_profile(profile['declaration'], profile['lock']):
        invalid('The fleet contribution does not bind its exact portable selection.')
    return profile


def target_key(target):
    return target['device'], target['scope']


def validate(value, control, signer):
    fields = ('schema_version', 'channel', 'controller', 'epoch', 'sequence', 'parent', 'operation', 'action',
              'created_at', 'expires', 'targets', 'input', 'source_effect')
    c.fields(value, fields, family='fleet')
    if value['channel'] != channel(control) or value['controller'] != signer['id']:
        invalid('Desired revision names a different control channel or signer.')
    for key in ('epoch', 'sequence', 'created_at', 'expires'):
        fleet.number(value[key], minimum=1)
    if not value['created_at'] < value['expires'] <= value['created_at'] + MAX_TTL:
        invalid('Desired revision has an invalid authorization window.')
    fleet.identifier(value['operation'])
    if value['parent'] is not None and (not isinstance(value['parent'], str) or not re.fullmatch(r'sha256:[a-f0-9]{64}', value['parent'])):
        invalid('Desired parent requires a full intent digest.')
    if value['action'] not in OPERATIONS or not isinstance(value['input'], dict):
        invalid('Unknown desired action or input.')
    if value['action'] == 'cancel':
        c.fields(value['input'], ('operation',), family='fleet', versions=())
        fleet.identifier(value['input']['operation'])
        if value['source_effect'] is not None:
            invalid('Cancel cannot authorize source publication.')
    effect = value['source_effect']
    if effect is not None:
        c.fields(effect, ('source', 'repository', 'ref', 'parent', 'commit', 'path'), family='fleet')
        fleet.token(effect['source'])
        if sources.repository(effect['repository']) != effect['repository']:
            invalid('Source publication requires a canonical repository.')
        sources.selector(effect['ref'])
        sources.package_path(effect['path'])
        if not all(isinstance(effect[key], str) and re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}', effect[key])
                   for key in ('parent', 'commit')):
            invalid('Source publication requires exact commit IDs.')
    targets = value['targets']
    if not isinstance(targets, list) or not 1 <= len(targets) <= MAX_DEVICES:
        invalid('Desired revisions require a bounded, nonempty target set.')
    keys = []
    for target in targets:
        c.fields(target, ('name', 'device', 'device_epoch', 'scope', 'scope_type', 'profile'),
                 ('identity', 'binding', 'blocked'), family='fleet')
        fleet.token(target['name'])
        fleet.identifier(target['device'])
        fleet.number(target['device_epoch'], minimum=1)
        if target['scope_type'] not in ('user', 'project'):
            invalid('Unsupported desired scope type.')
        fleet.token(target['scope'])
        if 'identity' in target and fleet.identity(target['identity'], 'device')['id'] != target['device']:
            invalid('Frozen target device identity differs from its enrolled ID.')
        if 'binding' in target and (not isinstance(target['binding'], str) or not re.fullmatch(r'sha256:[a-f0-9]{64}', target['binding'])):
            invalid('Frozen target binding requires an exact fingerprint.')
        if 'blocked' in target and (not isinstance(target['blocked'], str) or not re.fullmatch(r'[a-z0-9_.]{1,96}', target['blocked'])):
            invalid('Invalid target preflight blocker.')
        keys.append(target_key(target))
        if value['action'] == 'cancel':
            if target['profile'] is not None:
                invalid('Cancel cannot publish a replacement profile.')
        elif target['profile'] is not None:
            validate_profile(target['profile'])
    if keys != sorted(set(keys)) or len({target['name'] for target in targets}) != len(targets):
        invalid('Desired device/scope identities and names must be unique and canonical.')
    return value


def channel(control):
    return c.digest(dict(repository=sources.repository(control['repository']), ref=REF))


def intent_digest(value):
    return c.digest(fleet.signed_bytes(value))


def event(control, signer, history, action, operation, targets, input, source_effect=None, *, ttl=7 * 24 * 3600):
    parent = history[-1] if history else None
    now = int(time.time())
    value = dict(schema_version=1, channel=channel(control), controller=signer['id'], epoch=control['epoch'],
                 sequence=parent['sequence'] + 1 if parent else 1, parent=intent_digest(parent) if parent else None,
                 operation=operation, action=action, created_at=now, expires=now + ttl,
                 targets=sorted(targets, key=target_key), input=input, source_effect=source_effect)
    return validate(value, control, signer)


@dataclass
class History:
    control: dict
    root: Path
    head: str | None
    events: list

    def operation(self, operation):
        return next((entry for entry in self.events if entry['operation'] == operation), None)

    def effective(self):
        result = {}
        for entry in self.events:
            for target in entry['targets']:
                if 'blocked' in target:
                    continue
                key = target_key(target)
                if entry['action'] == 'cancel':
                    previous = result.get(key)
                    if previous and previous[0]['operation'] == entry['input'].get('operation'):
                        result[key] = (entry, target)
                else:
                    result[key] = (entry, target)
        return result


def network(root, control, *args, **kwargs):
    transport = control['repository']
    protocol = sources.scheme(transport)
    sources.endpoint(root, transport, sources.repository(transport))
    options = sources.network_options(root, transport) + [
        '-c', 'protocol.allow=never', '-c', f'protocol.{protocol}.allow=always']
    if args[0] == 'push':
        remote = 'mask-fleet-reviewed'
        c.git(root, 'config', '--local', '--replace-all', f'remote.{remote}.url', transport, mutating=True)
        c.git(root, 'config', '--local', '--replace-all', f'remote.{remote}.pushurl', transport, mutating=True)
        options.extend(('-c', f'remote.{remote}.mirror=false', '-c', 'push.gpgSign=false'))
        destinations = c.git(root, *options, 'remote', 'get-url', '--push', '--all', remote).splitlines()
        if destinations != [transport]:
            c.fail('fleet.push_endpoint_changed', 'Git rewrites the explicitly approved publication transport.', 4)
        args = tuple(remote if part == transport else part for part in args)
    return c.git(root, *options, *args, **kwargs)


def remote_head(root, control, ref=REF):
    raw = network(root, control, 'ls-remote', '--refs', control['repository'], ref, max_output=1024)
    if not raw:
        return None
    commit, sep, name = raw.partition('\t')
    if not sep or name != ref or not GIT_OID.fullmatch(commit):
        invalid('Control Git ref did not return one SHA-1 commit.')
    return commit


def read_history(root, head, control, signer):
    entries = []
    seen = set()
    if head is None:
        return entries
    commits = c.git(root, 'rev-list', '--max-count=' + str(MAX_HISTORY + 1), '--reverse', '--parents', head).splitlines()
    if not commits or len(commits) > MAX_HISTORY:
        invalid('Control history exceeds its supported revision bound.')
    parent_commit, parent_intent, epoch = None, None, 0
    for line in commits:
        commit, *parents = line.split()
        if parents != ([parent_commit] if parent_commit else []):
            invalid('Control history must be linear.')
        if c.git(root, 'ls-tree', commit) != c.git(root, 'ls-tree', commit, '--', 'intent.json'):
            invalid('A control revision must contain only its signed intent.')
        raw = c.git(root, 'cat-file', 'blob', commit + ':intent.json', binary=True, max_output=MAX_REVISION)
        packet = fleet.record(raw)
        c.fields(packet, ('intent', 'signature'), family='fleet')
        value = validate(packet['intent'], control, signer)
        fleet.verify(value, packet['signature'], signer, NAMESPACE)
        if (value['parent'] != parent_intent or value['sequence'] != len(entries) + 1
                or not epoch <= value['epoch'] <= control['epoch'] or value['operation'] in seen):
            invalid('Control history has a forked intent, reused operation, stale epoch or invalid sequence.')
        if value['action'] == 'cancel':
            original = next((entry for entry in entries if entry['operation'] == value['input'].get('operation')), None)
            if original is None or original['action'] == 'cancel' or not {
                    target_key(target) for target in value['targets']} <= {
                    target_key(target) for target in original['targets']}:
                invalid('Cancellation must name an earlier authorized operation and its target set.')
        entries.append(value)
        seen.add(value['operation'])
        parent_commit, parent_intent, epoch = commit, intent_digest(value), value['epoch']
    return entries


def high_water_path(home, control):
    return fleet.path(home, 'control-head-' + channel(control).split(':')[1])


def check_fresh(home, history):
    previous = fleet.data(high_water_path(home, history.control), missing=True)
    if previous:
        sequence = previous['sequence']
        if len(history.events) < sequence or intent_digest(history.events[sequence - 1]) != previous['intent']:
            c.fail('fleet.control_stale', 'Control history does not extend the latest locally observed desired revision.', 4)


def remember(home, history):
    if not history.events:
        return
    with c.writer_lock(home, name='fleet-control.lock'):
        check_fresh(home, history)
        pathname = high_water_path(home, history.control)
        before = fleet.data(pathname, missing=True)
        latest = history.events[-1]
        fleet.put(pathname, dict(sequence=latest['sequence'], intent=intent_digest(latest)), before)


@contextmanager
def snapshot(home, control, signer):
    with tempfile.TemporaryDirectory(prefix='mask-control-') as temporary:
        root = Path(temporary)
        c.git(root, '-c', 'init.templateDir=', 'init', '--bare', '--object-format=sha1', mutating=True)
        head = remote_head(root, control)
        if head is not None:
            def bound_fetch():
                if sources.cache_bytes(root) > sources.FETCH_BYTES:
                    c.fail('fleet.control_limit', 'Control fetch exceeded the local object storage budget.', 4)
            network(root, control, 'fetch', '--no-tags', '--no-recurse-submodules', '--no-auto-maintenance',
                    '--depth=' + str(MAX_HISTORY + 1), control['repository'], REF, mutating=True, monitor=bound_fetch)
            bound_fetch()
            if c.git(root, 'rev-parse', 'FETCH_HEAD^{commit}') != head:
                c.fail('fleet.control_conflict', 'Control ref moved during fetch. Read the new head and retry.', 4)
        history = History(control, root, head, read_history(root, head, control, signer))
        check_fresh(home, history)
        yield history


def publish(history, value, signer):
    if len(history.events) >= MAX_HISTORY:
        invalid('Control history has reached its revision limit.')
    expected = event(history.control, signer, history.events, value['action'], value['operation'],
                     value['targets'], value['input'], value['source_effect'], ttl=value['expires'] - value['created_at'])
    if (value['parent'], value['sequence'], value['epoch']) != (expected['parent'], expected['sequence'], expected['epoch']):
        invalid('Publication does not extend the authenticated desired head.')
    if history.operation(value['operation']) is not None:
        invalid('This operation is already present in the control history.')
    if value['action'] == 'cancel':
        original = history.operation(value['input']['operation'])
        if original is None or original['action'] == 'cancel' or not {
                target_key(target) for target in value['targets']} <= {
                target_key(target) for target in original['targets']}:
            invalid('Cancellation must name an earlier authorized operation and its target set.')
    raw = fleet.signed_bytes(dict(intent=value, signature=fleet.sign(value, signer, NAMESPACE)))
    if len(raw) > MAX_REVISION:
        invalid('Signed desired revision exceeds its byte limit.')
    root, control = history.root, history.control
    blob = c.git(root, 'hash-object', '-w', '--stdin', input=raw, mutating=True)
    tree = c.git(root, 'mktree', input=f'100644 blob {blob}\tintent.json\n'.encode(), mutating=True)
    parent = ['-p', history.head] if history.head else []
    commit = c.git(root, '-c', 'user.name=MASK fleet', '-c', 'user.email=mask@mask.invalid',
                   'commit-tree', '--no-gpg-sign', tree, *parent, '-m', 'MASK desired revision ' + value['operation'],
                   mutating=True)
    # Both the expected destination and the exact parent are bound. A competing
    # publisher or missing acknowledgement never causes a blind overwrite.
    if remote_head(root, control) != history.head:
        c.fail('fleet.control_conflict', 'Another publisher advanced the control ref. Review a new plan.', 4)
    try:
        network(root, control, 'push', '--porcelain', '--no-follow-tags',
                '--force-with-lease=' + REF + ':' + (history.head or ''), control['repository'],
                commit + ':' + REF, mutating=True)
    except c.MaskError:
        observed = remote_head(root, control)
        if observed != commit:
            if observed != history.head:
                c.fail('fleet.control_conflict', 'The expected control ref changed during publication.', 4)
            c.fail('fleet.control_publish_failed', 'The proposed revision is not the observed control head.', 4)
    history.head = commit
    history.events.append(value)
    return commit
