"""OpenSSH delivery through a pinned, fixed native MASK entrypoint."""
from __future__ import annotations

import base64
from concurrent.futures import ThreadPoolExecutor
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import shlex
import tempfile

import mask_core as c
import mask_fleet as fleet
import mask_rpc as rpc

PEER_LIMIT = 128
PROBE_REVISION = c.digest(b'mask-fleet-capability-v1')
HOST_KEY_ALIAS = 'mask-fleet-device'
BINDING_FIELDS = ('schema_version', 'device', 'authority', 'host_key', 'launcher')
PEER_FIELDS = (*BINDING_FIELDS, 'name', 'alias', 'ssh_config', 'endpoint', 'history', 'revoked')


def alias(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,252}', value):
        fleet.invalid('Choose a direct OpenSSH configuration alias.')
    return value


def validated_path(value, windows):
    if (not isinstance(value, str) or not 1 <= len(value) <= 768 or
            any(ord(ch) < 32 or ord(ch) == 127 for ch in value)):
        fleet.invalid('Fleet launcher paths must be bounded absolute local paths.')
    path = PureWindowsPath(value) if windows else PurePosixPath(value)
    if (not path.is_absolute() or '..' in path.parts or len(path.parts) < 2 or
            (windows and not re.fullmatch(r'[A-Za-z]:', path.drive)) or
            (windows and any(part.endswith((' ', '.')) or any(ch in part for ch in '<>:"|?*')
                             for part in path.parts[1:])) or
            (not windows and path.root != '/')):
        fleet.invalid('Fleet launcher paths must be absolute native paths on a local volume.')
    return path


def command(launcher, platform):
    c.fields(launcher, ('python', 'program', 'home'), family='fleet')
    windows = platform == 'windows'
    python, program, home = (validated_path(launcher[name], windows) for name in ('python', 'program', 'home'))
    if not re.fullmatch(r'python(?:3(?:\.[0-9]{1,2})?)?' + (r'\.exe' if windows else ''), python.name, re.I if windows else 0):
        fleet.invalid('Use the absolute native Python executable for the fixed launcher.')
    if (program.name.lower() if windows else program.name) != 'mask.py':
        fleet.invalid('The fleet launcher must name a reviewed installed mask.py.')
    args = [str(python), '-B', str(program), '--home', str(home), 'rpc', '--stdio']
    if windows:
        script = '& ' + ' '.join("'" + arg.replace("'", "''") + "'" for arg in args) + '; exit $LASTEXITCODE'
        encoded = base64.b64encode(script.encode('utf-16le')).decode('ascii')
        if len(encoded) > 6400:
            fleet.invalid('The Windows launcher exceeds its safe command length.')
        return 'powershell.exe -NoLogo -NoProfile -NonInteractive -EncodedCommand ' + encoded
    return 'exec ' + shlex.join(args)


def binding(value):
    c.fields(value, BINDING_FIELDS, family='fleet')
    device = fleet.identity(value['device'], 'device')
    authority = fleet.authority(value['authority'])
    if device['key'] == authority['controller']['key']:
        fleet.invalid('The device key must differ from the controller key.')
    fleet.key_facts(value['host_key'])
    command(value['launcher'], device['platform'])
    return value


def endpoint(value):
    c.fields(value, ('hostname', 'port', 'user'), family='fleet')
    if (not isinstance(value['hostname'], str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9.:%_-]{0,252}|::[0-9a-fA-F:]+', value['hostname']) or
            not isinstance(value['user'], str) or not re.fullmatch(r'[A-Za-z0-9_.@\\-]{1,128}', value['user']) or
            type(value['port']) is not int or not 1 <= value['port'] <= 65535):
        fleet.invalid('SSH alias must resolve to a bounded hostname, login and port.')
    return value


def config_for(ssh_alias, ssh_config=None):
    """Extract only the endpoint and authentication references from local SSH config."""
    try:
        config = ['-F', ssh_config] if ssh_config is not None else []
        code, raw, _ = c.contained_run([fleet.tool('ssh'), *config, '-G', '--', alias(ssh_alias)], os.environ,
                                      timeout=8, max_output=32768, max_error=8192,
                                      family='fleet.ssh', name='OpenSSH configuration')
        if code:
            c.fail('fleet.ssh_config_required', 'OpenSSH could not resolve the local alias.', 4)
        options = {}
        for line in raw.decode('utf-8').splitlines():
            key, space, value = line.partition(' ')
            if space:
                options.setdefault(key, []).append(value)
        for key in ('proxycommand', 'proxyjump'):
            if any(value != 'none' for value in options.get(key, [])):
                c.fail('fleet.ssh_proxy_unsupported', 'Enroll a direct SSH endpoint for the fixed transport.', 4)
        result = endpoint(dict(hostname=options['hostname'][0], port=int(options['port'][0]), user=options['user'][0]))
    except (KeyError, ValueError, OSError):
        c.fail('fleet.ssh_config_required', 'OpenSSH returned an unreadable local alias configuration.', 4)
    return result, options


def ssh_option(name, value):
    if any(ord(ch) < 32 or ch in '"\n\r' for ch in value):
        fleet.invalid('An SSH authentication reference cannot be safely represented.')
    return ['-o', f'{name}="{value}"']


def ssh_args(peer, config, pins, auth):
    address = peer['endpoint']
    options = ['BatchMode=yes', 'StrictHostKeyChecking=yes', 'GlobalKnownHostsFile=none',
               'KnownHostsCommand=none', 'HostKeyAlias=' + HOST_KEY_ALIAS, 'HostKeyAlgorithms=ssh-ed25519',
               'CheckHostIP=no', 'UpdateHostKeys=no', 'VerifyHostKeyDNS=no', 'ForwardAgent=no',
               'ClearAllForwardings=yes', 'ForwardX11=no', 'ControlMaster=no', 'ControlPath=none',
               'PermitLocalCommand=no', 'RequestTTY=no', 'ConnectTimeout=8',
               'PasswordAuthentication=no', 'KbdInteractiveAuthentication=no', 'PreferredAuthentications=publickey']
    args = [fleet.tool('ssh'), '-F', str(config), '-T']
    for value in options:
        args.extend(('-o', value))
    args += ssh_option('UserKnownHostsFile', pins.as_posix())
    for name in ('identitiesonly', 'identityagent', 'certificatefile'):
        for value in auth.get(name, []):
            args += ssh_option(name, value)
    # OpenSSH -i checks existence before expanding tokens. IdentityFile keeps
    # the same expansion semantics as the user's original configuration.
    for value in auth.get('identityfile', []):
        args += ssh_option('IdentityFile', value)
    return [*args, '-p', str(address['port']), '-l', address['user'], '--', address['hostname'],
            command(peer['launcher'], peer['device']['platform'])]


def exchange(peer, packet, *, timeout=30):
    intent = packet['intent']
    context = dict(operation=intent['id'], intent_digest=rpc.request_digest(intent))
    address, auth = config_for(peer['alias'], peer['ssh_config'])
    if address != peer['endpoint']:
        c.fail('fleet.endpoint_changed', 'The SSH alias no longer resolves to the enrolled endpoint.', 4)
    with tempfile.TemporaryDirectory(prefix='mask-ssh-') as directory:
        root = Path(directory)
        config, pins, request = (root / name for name in ('config', 'known-hosts', 'request'))
        config.write_bytes(b'')
        pins.write_text(HOST_KEY_ALIAS + ' ' + peer['host_key'] + '\n', encoding='ascii')
        request.write_bytes(rpc.frame(packet))
        args = ssh_args(peer, config, pins, auth)
        try:
            with request.open('rb') as handle:
                code, raw, stderr = c.contained_run(args, dict(os.environ, LC_ALL='C', SSH_ASKPASS_REQUIRE='never'),
                                                   timeout=timeout, max_output=rpc.MAX_FRAME + 4,
                                                   max_error=32768, input_file=handle,
                                                   family='fleet.ssh', name='OpenSSH transport')
        except (OSError, c.MaskError):
            c.fail('fleet.transport_unknown', 'SSH delivery outcome is unknown. Query the durable operation before retrying.',
                   4, outcome='unknown', **context)
    if code:
        if b'Host key verification failed' in stderr or b'REMOTE HOST IDENTIFICATION HAS CHANGED' in stderr:
            c.fail('fleet.host_key_mismatch', 'The server did not present its pinned SSH host key.', 4, **context)
        if code == 255 and b'Permission denied' in stderr:
            c.fail('fleet.ssh_auth_required', 'The enrolled SSH endpoint needs existing noninteractive public-key authentication.', 4, **context)
        c.fail('fleet.transport_unknown', 'SSH ended before a signed response was available. Query the durable operation.',
               4, outcome='unknown', **context)
    try:
        return rpc.checked_response(raw, intent, peer['device'])
    except c.MaskError as error:
        c.fail('fleet.response_unverified', 'The device response could not be verified. Query the durable operation.',
               4, outcome='unknown', refusal=error.code, **context)


def deliver(home, name, packet, *, timeout=30):
    """Deliver a frozen signed packet only through a currently enrolled binding."""
    peer = peer_at(home, name)
    intent = rpc.intent_shape(packet['intent'])
    if (intent['device'], intent['controller'], intent['epoch']) != (
            peer['device']['id'], peer['authority']['controller']['id'], peer['authority']['epoch']):
        c.fail('fleet.binding_changed', 'The frozen request no longer matches the enrolled binding.', 4)
    return exchange(peer, packet, timeout=timeout)


def probe(peer, controller, *, timeout=30):
    expected = peer['authority']
    if fleet.public(controller) != expected['controller']:
        c.fail('fleet.controller_changed', 'The binding names a different local controller identity.', 4)
    packet = rpc.request(controller, peer['device'], expected, 'capabilities', {}, revision=PROBE_REVISION)
    response = exchange(peer, packet, timeout=timeout)
    if response['status'] != 'ok':
        c.fail(response['error']['code'], 'The enrolled device refused the signed capability probe.', 4)
    observed = response['data']
    if observed.get('device') != peer['device'] or observed.get('authority') != expected:
        c.fail('fleet.binding_changed', 'Signed device identity or authority differs from the reviewed binding.', 4)
    return observed


def peer_path(home, name):
    return fleet.path(home, 'devices/' + fleet.token(name))


def peer_record(value):
    c.fields(value, PEER_FIELDS, family='fleet')
    binding({key: value[key] for key in BINDING_FIELDS})
    fleet.token(value['name'])
    alias(value['alias'])
    if value['ssh_config'] is not None and (not isinstance(value['ssh_config'], str) or not Path(value['ssh_config']).is_absolute()):
        fleet.invalid('Expected an absolute local SSH configuration path.')
    endpoint(value['endpoint'])
    if type(value['revoked']) is not bool or not isinstance(value['history'], list) or len(value['history']) > PEER_LIMIT:
        fleet.invalid('Invalid device revocation history.')
    for item in value['history']:
        c.fields(item, ('device', 'epoch', 'host_fingerprint'), family='fleet')
        fleet.identity(item['device'], 'device')
        fleet.number(item['epoch'], minimum=1)
        if not isinstance(item['host_fingerprint'], str) or not re.fullmatch(r'SHA256:[A-Za-z0-9+/]{43}', item['host_fingerprint']):
            fleet.invalid('Invalid revoked host fingerprint.')
    return value


def peer_at(home, name, *, missing=False, active=True):
    value = fleet.data(peer_path(home, name), missing=True)
    if value is None:
        if missing:
            return None
        c.fail('fleet.device_unknown', 'No enrolled device has that name.', 4)
    peer_record(value)
    if value['name'] != name:
        fleet.invalid('Fleet device record name disagrees with its location.')
    if active and value['revoked']:
        c.fail('fleet.device_revoked', 'The named fleet device is revoked.', 4)
    return value


def peers(home, *, active=True):
    directory = home / 'fleet' / 'devices'
    c.parents_safe(home, directory / 'scan')
    if c.kind(directory) == 'missing':
        return []
    names = []
    for path in directory.iterdir():
        if path.suffix == '.json':
            names.append(path.stem)
        if len(names) > PEER_LIMIT:
            c.fail('fleet.device_limit', 'The local device registry exceeds its bound.', 4)
    values = [peer_at(home, name, active=False) for name in sorted(names)]
    return [peer for peer in values if not active or not peer['revoked']]


def view(peer):
    return dict(name=peer['name'], alias=peer['alias'], device=peer['device'], authority=peer['authority'],
                endpoint=peer['endpoint'], host_fingerprint=fleet.key_facts(peer['host_key']),
                revoked=peer['revoked'], previous_bindings=len(peer['history']))


def same_device(left, right):
    return left['id'] == right['id'] or left['key'] == right['key']


def enrollment(home, args, output):
    name = fleet.token(args.name)
    path = peer_path(home, name)
    before = peer_at(home, name, missing=True, active=False)
    if args.command.endswith('.revoke'):
        if before is None:
            c.fail('fleet.device_unknown', 'No enrolled device has that name.', 4)
        candidate = dict(before, revoked=True)
    else:
        proposed = binding(fleet.data(Path(args.binding).expanduser().absolute()))
        config_path = getattr(args, 'ssh_config', None)
        config_path = str(Path(config_path).expanduser().absolute()) if config_path else None
        address, _ = config_for(args.ssh_config_alias, config_path)
        candidate = dict(proposed, name=name, alias=args.ssh_config_alias, ssh_config=config_path, endpoint=address,
                         history=list(before['history']) if before else [], revoked=False)
        if before and before['revoked']:
            candidate['history'].append(dict(device=before['device'], epoch=before['authority']['epoch'],
                                             host_fingerprint=fleet.key_facts(before['host_key'])))
        elif before and before != candidate:
            c.fail('fleet.device_exists', 'Revoke the existing binding before changing an enrolled device.', 4)
        for old in candidate['history']:
            if same_device(candidate['device'], old['device']) and (
                    candidate['authority']['epoch'] <= old['epoch']):
                c.fail('fleet.epoch_stale', 'Reenrolling a revoked identity requires a newer device authority epoch.', 4)
        peer_record(candidate)
    output['data'] = view(candidate)
    fleet.review(output, args, candidate, before)
    if not candidate['revoked']:
        controller = fleet.get_identity(home, 'controller')
        output['data']['capabilities'] = probe(candidate, controller)
    if not output['dry_run']:
        with c.writer_lock(home):
            if not candidate['revoked']:
                if fleet.get_identity(home, 'controller') != controller:
                    c.fail('fleet.controller_changed', 'Controller identity changed during enrollment.', 4)
                registered = peers(home, active=False)
                others = [peer for peer in registered if peer['name'] != name]
                for peer in others:
                    past = [(item['device'], item['epoch']) for item in peer['history']]
                    if peer['revoked']:
                        past.append((peer['device'], peer['authority']['epoch']))
                    elif same_device(peer['device'], candidate['device']):
                        c.fail('fleet.device_exists', 'That device identity already has another active binding.', 4)
                    if any(same_device(device, candidate['device']) and candidate['authority']['epoch'] <= epoch
                           for device, epoch in past):
                        c.fail('fleet.epoch_stale', 'That device identity was revoked under another name.', 4)
                if before is None and len(registered) >= PEER_LIMIT:
                    c.fail('fleet.device_limit', 'The local device registry is full.', 4)
            output['changed'] = fleet.put(path, candidate, before)
        if output['changed']:
            output['transaction'] = 'committed'


def probe_all(home, args, output):
    name = getattr(args, 'device', None)
    if name is not None and getattr(args, 'all', False):
        c.fail('invocation.invalid', 'Select --device NAME or --all.', 2)
    parallel = getattr(args, 'parallel', 4)
    timeout = getattr(args, 'timeout', 30)
    if not 1 <= parallel <= 16 or not 1 <= timeout <= 180:
        c.fail('invocation.invalid', 'Choose parallelism 1–16 and timeout 1–180 seconds.', 2)
    selected = [peer_at(home, name)] if name is not None else peers(home)
    if not selected:
        c.fail('fleet.no_devices', 'Enroll a device before using fleet probes.', 4)
    controller = fleet.get_identity(home, 'controller')

    def inspect(peer):
        result = dict(name=peer['name'], device_id=peer['device']['id'])
        try:
            observed = probe(peer, controller, timeout=timeout)
            result['status'] = 'reachable'
            if args.command == 'fleet.capability':
                result['capabilities'] = observed
        except OSError:
            error = c.MaskError('fleet.probe_io_failed', 'A local SSH probe resource could not be read or created.', 4)
            result.update(status='unavailable', error=error.as_dict())
        except c.MaskError as error:
            result.update(status='unavailable', error=error.as_dict())
        return result

    with ThreadPoolExecutor(max_workers=min(parallel, len(selected))) as pool:
        results = list(pool.map(inspect, selected))
    output['data']['devices'] = results
    if any(row['status'] != 'reachable' for row in results):
        c.fail('fleet.probe_incomplete', 'One or more enrolled devices did not answer the signed probe.', 4)


def dispatch(args, output, home):
    if args.command in ('fleet.device.enroll', 'fleet.device.revoke'):
        return enrollment(home, args, output)
    if args.command == 'fleet.device.show':
        output['data'] = view(peer_at(home, args.name, active=False))
    elif args.command == 'fleet.device.list':
        output['data']['devices'] = [view(peer) for peer in peers(home, active=False)]
    else:
        probe_all(home, args, output)
