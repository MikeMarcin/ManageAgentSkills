"""Local fleet identities and explicit device-side authority."""
from __future__ import annotations

import base64
from contextlib import nullcontext
from contextvars import ContextVar
import hashlib
import os
from pathlib import Path
import platform
import re
import shutil
import tempfile
import uuid

import mask_core as c
import mask_resolve as resolve
import mask_sources as sources

INTENT = 'mask-intent@mask.invalid'
RECEIPT = 'mask-receipt@mask.invalid'
SIGNING_PROVIDER = ContextVar('fleet_signing_provider', default=None)
PROTOCOL = 'mask.rpc.v1'
ACTIONS = ('capabilities', 'inspect', 'prepare', 'apply', 'receipt', 'cancel-request')
SUPPORTED_ACTIONS = ACTIONS + ('program-inspect', 'program-update', 'upgrade-inspect', 'upgrade-apply')
RECORD_BYTES = 256 * 1024
PUBLIC_FIELDS = ('schema_version', 'kind', 'id', 'name', 'key', 'fingerprint')
ED25519_PREFIX = b'\0\0\0\x0bssh-ed25519\0\0\0\x20'
TOKEN = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
MAX_INTEGER = 2 ** 53 - 1


def invalid(message):
    c.fail('fleet.invalid', message, 4)


def token(value):
    if not isinstance(value, str) or len(value) > 64 or not TOKEN.fullmatch(value) or value in c.RESERVED:
        invalid('Expected a bounded, lowercase fleet name.')
    return value


def identifier(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9a-f]{32}', value):
        invalid('Expected a full generated fleet identifier.')
    return value


def number(value, *, minimum=0):
    if type(value) is not int or not minimum <= value <= MAX_INTEGER:
        invalid('Expected a bounded nonnegative integer.')
    return value


def key_facts(value):
    if not isinstance(value, str) or not re.fullmatch(r'ssh-ed25519 [A-Za-z0-9+/]{68}', value):
        invalid('Expected an uncommented OpenSSH ED25519 public key.')
    raw = base64.b64decode(value.split()[1])
    if len(raw) != len(ED25519_PREFIX) + 32 or not raw.startswith(ED25519_PREFIX):
        invalid('Invalid OpenSSH ED25519 public key encoding.')
    return 'SHA256:' + base64.b64encode(hashlib.sha256(raw).digest()).decode('ascii').rstrip('=')


def identity(value, role, *, local=False):
    fields = PUBLIC_FIELDS + (('platform', 'architecture', 'protocols') if role == 'device' else ())
    c.fields(value, fields + (('signing_key',) if local else ()), family='fleet')
    identifier(value['id'])
    token(value['name'])
    if value['kind'] != role or value['fingerprint'] != key_facts(value['key']):
        invalid('Fleet identity role or fingerprint is invalid.')
    if role == 'device' and (value['platform'] not in ('macos', 'windows', 'linux') or
                             value['architecture'] not in ('x86_64', 'arm64', 'x86') or
                             value['protocols'] != [PROTOCOL]):
        invalid('Fleet device platform, architecture or protocol is unsupported.')
    if local and (not isinstance(value['signing_key'], str) or not Path(value['signing_key']).is_absolute()):
        invalid('Expected an absolute local signing key path.')
    return value


def public(value):
    return {key: entry for key, entry in value.items() if key != 'signing_key'}


def signed_bytes(value):
    return resolve.canonical(value, 'fleet')


def record(raw):
    try:
        value = c.parse_json(raw.decode('utf-8'), 'fleet')
        # The local scope identity can contain Windows volume and inode numbers.
        resolve.canonical(value, 'fleet', integer_limit=2 ** 128 - 1)
        return value
    except (UnicodeError, RecursionError):
        invalid('Invalid bounded UTF-8 fleet record.')


def data(path, *, missing=False, limit=RECORD_BYTES):
    c.parents_safe(Path(path.anchor), path)
    if missing and c.kind(path) == 'missing':
        return None
    return record(resolve.regular_bytes(path, limit))


def put(path, value, expected, *, limit=RECORD_BYTES):
    raw = c.read_text(path, 'fleet', missing=True)
    if (record(raw.encode('utf-8')) if raw is not None else None) != expected:
        c.fail('state.drift', 'Fleet state changed since it was read.', 4)
    encoded = c.text_json(value)
    if len(encoded.encode('utf-8')) > limit:
        invalid('Fleet record exceeds its byte limit.')
    return c.atomic_text(path, encoded, raw)


def path(home, name):
    return home / 'fleet' / (name + '.json')


def get_identity(home, role, *, missing=False):
    value = data(path(home, role), missing=True)
    if value is not None:
        return identity(value, role, local=True)
    if not missing:
        c.fail('fleet.identity_required', 'Initialize the local fleet signing identity first.', 4)


def tool(name):
    executable = shutil.which(name + '.exe' if os.name == 'nt' else name)
    if not executable:
        c.fail('fleet.provider_required', f'Install compatible OpenSSH {name} before using fleet.', 4)
    return executable


def signing_command(*args, input_file=None):
    env = dict(os.environ, SSH_ASKPASS_REQUIRE='never')
    env.pop('SSH_AUTH_SOCK', None)
    try:
        provider = SIGNING_PROVIDER.get() or tool('ssh-keygen')
        return c.contained_run([provider, *args], env, timeout=8, max_output=4096,
                               max_error=8192, family='fleet.signing', name='OpenSSH signing',
                               input_file=input_file)
    except OSError:
        c.fail('fleet.provider_required', 'OpenSSH ssh-keygen could not start.', 4)


def private_key(pathname):
    c.parents_safe(Path(pathname.anchor), pathname)
    if c.kind(pathname) != 'file':
        c.fail('fleet.signing_key_required', 'Provide an existing local ED25519 private signing key.', 4)
    code, raw, _ = signing_command('-y', '-P', '', '-f', str(pathname))
    if code:
        c.fail('fleet.signing_key_required', 'The signing key must be readable by noninteractive OpenSSH.', 4)
    try:
        key = ' '.join(raw.decode('utf-8').split()[:2])
    except UnicodeError:
        invalid('Invalid signing public key.')
    key_facts(key)
    return key


def sign(value, signer, namespace):
    pathname = Path(signer['signing_key'])
    if private_key(pathname) != signer['key']:
        c.fail('fleet.signing_identity_changed', 'The local private key no longer matches the enrolled identity.', 4)
    with tempfile.TemporaryDirectory(prefix='mask-sign-') as directory:
        payload = Path(directory).resolve() / 'payload'
        payload.write_bytes(signed_bytes(value))
        code, _, _ = signing_command('-Y', 'sign', '-P', '', '-n', namespace, '-f', str(pathname), str(payload))
        if code:
            c.fail('fleet.provider_required', 'OpenSSH file signing failed or is unavailable.', 4)
        signature = resolve.regular_bytes(payload.with_suffix('.sig'), 4096).decode('ascii')
    return signature.replace('\r\n', '\n')


def verify(value, signature, signer, namespace):
    if (not isinstance(signature, str) or len(signature) > 4096 or not re.fullmatch(
            r'-----BEGIN SSH SIGNATURE-----\n[A-Za-z0-9+/=\n]+-----END SSH SIGNATURE-----\n', signature)):
        c.fail('fleet.signature_invalid', 'Expected a bounded OpenSSH signature.', 4)
    identifier(signer['id'])
    key_facts(signer['key'])
    with tempfile.TemporaryDirectory(prefix='mask-verify-') as directory:
        root = Path(directory).resolve()
        allowed = root / 'allowed'
        signature_path = root / 'signature'
        payload = root / 'payload'
        allowed.write_bytes(f'{signer["id"]} {signer["key"]}\n'.encode('ascii'))
        signature_path.write_bytes(signature.encode('ascii'))
        payload.write_bytes(signed_bytes(value))
        # Windows OpenSSH file-signature verification can wait on a pipe even after EOF.
        with payload.open('rb') as handle:
            code, _, _ = signing_command('-Y', 'verify', '-f', str(allowed), '-I', signer['id'],
                                         '-n', namespace, '-s', str(signature_path), input_file=handle)
    if code:
        c.fail('fleet.signature_invalid', 'Signature did not verify for the enrolled key and namespace.', 4)


def local_platform():
    return {'Darwin': 'macos', 'Windows': 'windows', 'Linux': 'linux'}.get(platform.system())


def init(args, output, home, role):
    name = token(args.name)
    key_path = Path(args.signing_key).expanduser().absolute()
    key = private_key(key_path)
    proposed = dict(schema_version=1, kind=role, id=uuid.uuid4().hex, name=name,
                    key=key, fingerprint=key_facts(key), signing_key=str(key_path))
    if role == 'device':
        arch = platform.machine().lower()
        proposed.update(platform=local_platform(), architecture={'amd64': 'x86_64', 'aarch64': 'arm64',
                        'i386': 'x86', 'i686': 'x86'}.get(arch, arch), protocols=[PROTOCOL])
    identity(proposed, role, local=True)
    old = get_identity(home, role, missing=True)
    if old is not None:
        proposed['id'] = old['id']
        if proposed != old:
            c.fail('fleet.identity_exists', 'This fleet role already has a different local identity.', 4)
    other = get_identity(home, 'device' if role == 'controller' else 'controller', missing=True)
    if other and key == other['key']:
        invalid('Controller and device must have distinct signing keys.')
    probe = {'id': proposed['id'], 'kind': role, 'probe': PROTOCOL}
    namespace = INTENT if role == 'controller' else RECEIPT
    verify(probe, sign(probe, proposed, namespace), proposed, namespace)
    output['data'] = dict(identity=public(proposed), signing_provider='openssh-sshsig-ed25519')
    output['would_change'] = old is None
    if not output['dry_run'] and old is None:
        with c.writer_lock(home):
            other = get_identity(home, 'device' if role == 'controller' else 'controller', missing=True)
            if other and key == other['key']:
                invalid('Controller and device must have distinct signing keys.')
            output['changed'] = put(path(home, role), proposed, None)
        output['transaction'] = 'committed'


def authority(value, *, local=False):
    c.fields(value, ('schema_version', 'controller', 'epoch', 'minimum_sequence', 'actions', 'scopes'),
             ('program_origin', 'revoked') if local else ('program_origin',), 'fleet')
    identity(value['controller'], 'controller')
    number(value['epoch'], minimum=1)
    number(value['minimum_sequence'], minimum=1)
    actions = value['actions']
    if not isinstance(actions, list) or not actions or len(actions) > len(SUPPORTED_ACTIONS) or any(
            action not in SUPPORTED_ACTIONS for action in actions) or len(set(actions)) != len(actions):
        invalid('Choose a unique set of supported fleet actions.')
    if ('program_origin' in value) != bool({'program-inspect', 'program-update'} & set(actions)):
        invalid('A program grant requires its own explicit program_origin.')
    if 'program_origin' in value and sources.repository(value['program_origin']) != value['program_origin']:
        invalid('Program authority requires a canonical credential-free repository identity.')
    scopes = value['scopes']
    if not isinstance(scopes, dict) or len(scopes) > 32:
        invalid('Device policy may grant at most 32 scope aliases.')
    for alias, scope in scopes.items():
        token(alias)
        fields = ('scope', 'sources') + (('root',) if local else ())
        scope_options = ('rollout', 'upgrade', 'commit')
        c.fields(scope, fields, (*scope_options, 'root_identity') if local else scope_options, 'fleet')
        if 'rollout' in scope and scope['rollout'] is not True:
            invalid('Omit rollout unless explicitly granting desired profile changes.')
        if scope['scope'] not in ('project', 'user'):
            invalid('A fleet scope must be project or user.')
        if 'upgrade' in scope and scope['upgrade'] is not True:
            invalid('Omit upgrade unless explicitly granting skill upgrades.')
        if 'commit' in scope and (scope['commit'] is not True or scope['scope'] != 'project' or not scope.get('upgrade')):
            invalid('A Git commit grant requires a project scope with explicit upgrade authority.')
        if local and (not isinstance(scope['root'], str) or not 1 <= len(scope['root']) <= 4096 or
                      not Path(scope['root']).is_absolute()):
            invalid('Device scope roots require absolute local paths.')
        entries = scope['sources']
        if not isinstance(entries, dict) or len(entries) > 32:
            invalid('A fleet scope may grant at most 32 sources.')
        for name, entry in entries.items():
            token(name)
            c.fields(entry, ('repository', 'forward'), family='fleet')
            repository = resolve.repository(entry['repository'], 'fleet')
            if repository.startswith('file:') or repository != sources.repository(repository):
                invalid('Fleet sources require a canonical, credential-free network repository identity.')
            if type(entry['forward']) is not bool:
                invalid('Artifact forwarding permission must be boolean.')
    if 'revoked' in value and value['revoked'] is not True:
        invalid('Invalid controller revocation.')
    return value


def current_authority(home, *, missing=False):
    value = data(path(home, 'authority'), missing=True)
    if value is not None:
        authority(value, local=True)
        for scope in value['scopes'].values():
            observed = scope.get('root_identity')
            c.fields(observed, ('device', 'inode'), family='fleet')
            if any(type(part) is not int or not 0 <= part < 2 ** 128 for part in observed.values()):
                invalid('Invalid enrolled physical scope identity.')
        return value
    if not missing:
        c.fail('fleet.controller_unknown', 'No local controller authority is enrolled.', 4)


def public_authority(value):
    return dict(value, scopes={alias: {key: scope[key] for key in ('scope', 'sources', 'rollout', 'upgrade', 'commit') if key in scope}
                               for alias, scope in value['scopes'].items()})


def local_scope(scope, state):
    root = Path(scope['root'])
    record = c.consumer_records(state).get(str(root))
    if record is None or c.consumer_scope(state, root) != scope['scope']:
        c.fail('fleet.scope_unregistered', 'The authorized root must be a locally registered consumer.', 4)
    c.registered_root(root, record, scope['scope'])
    if scope.get('root_identity', record['root_identity']) != record['root_identity']:
        c.fail('fleet.scope_changed', 'The enrolled consumer directory identity changed.', 4)
    return root, record


def bind_authority(home, proposed):
    device = get_identity(home, 'device')
    if proposed['controller']['key'] == device['key']:
        invalid('Controller and device must have distinct signing keys.')
    state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
    config = c.config(c.read_json(home / 'config.json')) if any(
        scope['sources'] for scope in proposed['scopes'].values()) else None
    scopes, rollout_roots, upgrade_roots = {}, set(), set()
    for alias, scope in proposed['scopes'].items():
        if 'root_identity' in scope:
            invalid('MASK observes the physical scope identity during authorization.')
        root, record = local_scope(scope, state)
        if scope.get('rollout'):
            if root in rollout_roots:
                invalid('Each physical consumer may have only one rollout scope alias.')
            rollout_roots.add(root)
        if scope.get('upgrade'):
            if root in upgrade_roots:
                invalid('Each physical consumer may have only one upgrade scope alias.')
            upgrade_roots.add(root)
        for name, grant in scope['sources'].items():
            approved = sources.selected(config, name)
            if sources.repository(approved['repository']) != grant['repository']:
                c.fail('fleet.source_denied', 'The fleet source must match a locally approved repository.', 4)
        scopes[alias] = dict(scope, root=str(root), root_identity=record['root_identity'])
    return dict(proposed, scopes=scopes)


def review(output, args, candidate, previous):
    plan_hash = c.digest(dict(before=previous, after=candidate))
    output['data']['plan_hash'] = plan_hash
    output['would_change'] = previous != candidate
    if not output['dry_run'] and previous != candidate and getattr(args, 'approve_plan', None) != plan_hash:
        c.fail('confirmation.required', 'Preview this fleet trust change and pass --approve-plan with the reported hash.', 4)


def authorize(args, output, home):
    proposed = None if args.command.endswith('revoke-controller') else authority(
        data(Path(args.policy).expanduser().absolute()), local=True)
    if proposed and proposed.get('revoked'):
        invalid('Use fleet device revoke-controller to withdraw local authority.')
    with (c.writer_lock(home) if not output['dry_run'] else nullcontext()):
        before = current_authority(home, missing=True)
        if proposed is None:
            if before is None:
                c.fail('fleet.controller_unknown', 'No local controller authority is enrolled.', 4)
            candidate = dict(before, revoked=True)
        else:
            candidate = bind_authority(home, proposed)
            if before is not None and candidate != before and candidate['epoch'] <= before['epoch']:
                c.fail('fleet.epoch_stale', 'Changing controller authority requires a strictly newer epoch.', 4)
        output['data']['authority'] = public_authority(candidate)
        review(output, args, candidate, before)
        if not output['dry_run']:
            output['changed'] = put(path(home, 'authority'), candidate, before)
            if output['changed']:
                output['transaction'] = 'committed'


def descriptor(home):
    policy = current_authority(home)
    if policy.get('revoked'):
        c.fail('fleet.controller_revoked', 'The local controller authority is revoked.', 4)
    return dict(device=public(get_identity(home, 'device')), authority=public_authority(policy))


def dispatch(args, output, home):
    command = args.command
    if command == 'fleet.control.configure':
        import mask_control
        return mask_control.configure(args, output, home)
    if command.startswith('fleet.runner.') or command == 'fleet.sync' and getattr(args, 'local', False):
        import mask_runner
        return mask_runner.dispatch(args, output, home)
    if command == 'fleet.upgrade' or command == 'fleet.update' and not getattr(args, 'input', None):
        import mask_fleet_maintenance
        return mask_fleet_maintenance.dispatch(args, output, home)
    if command in ('fleet.install', 'fleet.update', 'fleet.remove', 'fleet.sync') or command.startswith('fleet.operation.'):
        import mask_rollout
        return mask_rollout.dispatch(args, output, home)
    if command in ('fleet.device.init', 'fleet.controller.init'):
        return init(args, output, home, command.split('.')[1])
    if command in ('fleet.device.authorize', 'fleet.device.revoke-controller'):
        return authorize(args, output, home)
    if command == 'fleet.device.descriptor':
        output['data'] = descriptor(home)
    elif command == 'fleet.controller.show':
        output['data'] = dict(identity=public(get_identity(home, 'controller')))
    else:
        import mask_transport
        return mask_transport.dispatch(args, output, home)
