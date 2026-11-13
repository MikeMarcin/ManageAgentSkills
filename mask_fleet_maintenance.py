"""Signed, separately authorized fleet maintenance and its durable result records."""
from __future__ import annotations

import ast
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
import re
import tempfile
import time

import mask_core as c
import mask_fleet as fleet
import mask_git as git
import mask_install as install
import mask_rollout as rollout
import mask_rpc as rpc
import mask_sources as sources
import mask_transport as transport

OID = re.compile('[0-9a-f]{40}|[0-9a-f]{64}')
REF = 'refs/heads/main'
TTL = 7 * 24 * 3600
PLAN_LIMIT = 8 * 1024 * 1024
PROGRAM = ('program-inspect', 'program-update')
UPGRADE = ('upgrade-inspect', 'upgrade-apply')


def program_root():
    return Path(__file__).resolve().parent


def validate_payload(action, value):
    if action.startswith('program-'):
        if sources.repository(value['origin']) != value['origin'] or not isinstance(value['candidate'], str) or not OID.fullmatch(value['candidate']):
            rpc.invalid('Program maintenance requires an exact commit and canonical repository identity.')
    if 'observed' in value:
        rpc.digest(value['observed'])
    if action == 'upgrade-inspect' and (('candidate' in value) != ('observed' in value) or
                                      'profile' in value and 'candidate' not in value):
        rpc.invalid('Exact upgrade inspection binds a candidate and its original observation.')
    if 'task' in value:
        rpc.digest(value['task'])
    if action == 'upgrade-inspect' and 'candidate' in value:
        c.fields(value['candidate'], ('declaration', 'lock'), family='rpc', versions=())
    if action == 'upgrade-apply':
        c.fields(value['candidate'], ('declaration', 'lock'), family='rpc', versions=())
        if ('profile' in value) != ('desired' in value):
            rpc.invalid('An upgrade contribution must bind its exact published desired revision.')
        if 'profile' in value:
            if value['profile'] is None:
                rpc.invalid('Fleet upgrade cannot remove a contribution.')
            c.fields(value['desired'], ('sequence', 'revision'), family='rpc', versions=())
            fleet.number(value['desired']['sequence'], minimum=1)
            rpc.digest(value['desired']['revision'])
        commit = value['commit']
        if commit is None:
            return
        c.fields(commit, ('role', 'parent', 'controls', 'final'), ('source', 'proof'), 'rpc', versions=())
        if (commit['role'] not in ('canonical', 'member') or not isinstance(commit['parent'], str) or
                not OID.fullmatch(commit['parent']) or
                (commit['role'] == 'member') != ('source' in commit and 'proof' in commit) or
                commit['role'] == 'canonical' and ('source' in commit or 'proof' in commit)):
            rpc.invalid('Invalid project commit authority in an exact upgrade.')
        for key in ('controls', 'final'):
            c.fields(commit[key], ('.mask.json', '.mask.lock.json'), family='rpc', versions=())
            for digest in commit[key].values():
                rpc.digest(digest)


def config_at(home):
    raw = c.read_json(home / 'config.json', default={})
    return c.config(raw) if raw else None


def origin(root, timeout):
    configured = c.git(root, 'config', '--local', '--get-all', 'remote.origin.url', optional=True, timeout=timeout)
    if not configured or len(configured.splitlines()) != 1:
        c.fail('source.remote_unknown', 'Program origin must have one configured repository.', 4)
    identity = sources.repository(configured)
    sources.endpoint(root, 'origin', identity)
    effective = c.git(root, 'remote', 'get-url', 'origin', timeout=timeout)
    if sources.repository(effective) != identity:
        c.fail('source.identity_mismatch', 'Program origin resolves outside its approved repository.', 4)
    return identity, effective


def network_options(root, endpoint):
    return sources.network_options(root, endpoint) + [
        '-c', 'protocol.allow=never', '-c', 'protocol.' + sources.scheme(endpoint) + '.allow=always']


def advertised(root, endpoint, timeout):
    answer = c.git(root, *network_options(root, endpoint), 'ls-remote', '--refs', '--exit-code', endpoint, REF,
                   timeout=timeout, max_output=1024)
    oid, _, ref = answer.partition('\t')
    if ref != REF or not OID.fullmatch(oid):
        c.fail('source.candidate_invalid', 'Program origin did not advertise one main commit.', 4)
    return oid


@contextmanager
def program_objects(root, endpoint, candidate, timeout):
    """Preview downloads objects into an owned temporary repository."""
    if c.peeled_commit(root, candidate) == candidate:
        yield root
        return
    with tempfile.TemporaryDirectory(prefix='mask-fleet-program-') as name:
        scratch = Path(name)
        object_format = c.git(root, 'rev-parse', '--show-object-format', timeout=timeout)
        c.git(scratch, 'init', '--bare', '--object-format=' + object_format, timeout=timeout)
        objects = c.git(root, 'rev-parse', '--path-format=absolute', '--git-path', 'objects', timeout=timeout)
        (scratch / 'objects' / 'info' / 'alternates').write_text(objects.replace('\\', '/') + '\n', encoding='utf-8')
        sources.endpoint(scratch, endpoint, sources.repository(endpoint))
        c.git(scratch, *network_options(scratch, endpoint), 'fetch', '--no-tags', '--no-write-fetch-head',
              '--no-recurse-submodules', endpoint, REF + ':refs/mask/program', timeout=timeout, mutating=True)
        if c.peeled_commit(scratch, 'refs/mask/program') != candidate:
            c.fail('plan.stale', 'Program origin changed during preview.', 4)
        yield scratch


def fleet_protocol(root, revision):
    source = c.git(root, 'show', revision + ':mask_fleet.py', binary=True)
    try:
        constants = [ast.literal_eval(node.value) for node in ast.parse(source).body if isinstance(node, ast.Assign)
                     and any(isinstance(target, ast.Name) and target.id == 'PROTOCOL' for target in node.targets)]
    except (ValueError, SyntaxError, UnicodeError):
        constants = []
    return constants[0] if len(constants) == 1 else None


def program_origin(home, payload, policy):
    root = program_root()
    config = config_at(home)
    timeout = min((config or {}).get('git_timeout_seconds', 30), 20)
    approved = payload['origin']
    if policy.get('program_origin') != approved:
        c.fail('fleet.program_origin_denied', 'The device did not approve this program repository.', 4)
    actual, endpoint = origin(root, timeout)
    if actual != approved:
        c.fail('fleet.program_origin_denied', 'The program checkout origin differs from its device grant.', 4)
    return root, approved, endpoint, config, timeout


def program_observation(payload, context, objects):
    root, approved, endpoint, _, timeout = context
    observed = git.checkout_preconditions(root, 'origin', 'main', 'ManageAgentSkills', timeout, clean=False)
    before, candidate = observed['revision'], payload['candidate']
    local = git.local_changes(root, timeout) if observed['dirty'] else []
    if before != candidate and c.git(objects, 'merge-base', '--is-ancestor', before, candidate, optional=True, timeout=timeout) is None:
        code = 'source.ahead' if c.git(objects, 'merge-base', '--is-ancestor', candidate, before, optional=True, timeout=timeout) is not None else 'source.diverged'
        c.fail(code, 'The program cannot fast-forward to the exact fleet candidate.', 4)
    blocked = git.blocking_paths(root, candidate, local, timeout, objects=objects, before=before) if before != candidate else []
    if blocked:
        c.fail('source.dirty', 'Local changes touch the exact fleet program candidate.', 4, blocking_paths=blocked)
    try:
        migration = install.program_migration(objects, before, candidate) if before != candidate else None
    except c.MaskError as error:
        if error.code != 'source.candidate_invalid':
            raise
        c.fail('fleet.program_incompatible', 'The candidate does not contain a readable compatible MASK program.', 4)
    if migration and (migration['breaking'] or fleet_protocol(objects, candidate) != fleet.PROTOCOL):
        c.fail('fleet.program_incompatible', 'The candidate changes an incompatible program schema or fleet protocol.', 4)
    detail = dict(before=before, candidate=candidate, origin=approved, preserved=local, migration=migration)
    detail['observation'] = c.digest(dict(detail, checkout=c.identity(root), endpoint=endpoint))
    return detail


def durable_path(home, name, value):
    return fleet.path(home, name + '/' + value.removeprefix('sha256:'))


def observation_facts(intent):
    return {name: intent[name] for name in ('device', 'controller', 'epoch', 'revision', 'action', 'payload')}


def program_action(home, intent, device, policy):
    from contextlib import nullcontext

    payload = intent['payload']
    key = c.digest(observation_facts(intent))
    path = durable_path(home, 'program-results', key)
    inspecting = intent['action'] == PROGRAM[0]
    with nullcontext() if inspecting else c.writer_lock(home):
        rpc.recheck_authority(home, intent, device, policy)
        rpc.pending_guard(home)
        receipt = fleet.data(path, missing=True) if not inspecting else None
        if receipt and receipt.get('status') == 'applied_verified':
            return receipt
        if receipt:
            context = program_origin(home, payload, policy)
            root, _, _, _, timeout = context
            if c.git(root, 'rev-parse', 'HEAD', timeout=timeout) == payload['candidate']:
                detail = program_observation(payload, context, root)
                return apply_program(home, payload, context, root, key, path, receipt, detail)
    context = program_origin(home, payload, policy)
    root, _, endpoint, _, timeout = context
    candidate = payload['candidate']
    if advertised(root, endpoint, timeout) != candidate:
        c.fail('plan.stale', 'The program origin no longer advertises the reviewed commit.', 4)
    with program_objects(root, endpoint, candidate, timeout) as objects:
        if inspecting:
            return program_observation(payload, context, objects)
        with c.writer_lock(home):
            rpc.recheck_authority(home, intent, device, policy)
            rpc.pending_guard(home)
            if program_origin(home, payload, policy) != context:
                c.fail('plan.stale', 'Program authority changed during exact preparation.', 4)
            detail = program_observation(payload, context, objects)
            return apply_program(home, payload, context, objects, key, path, receipt, detail)


def apply_program(home, payload, context, objects, key, path, receipt, detail):
    root, _, _, config, timeout = context
    if receipt is None and detail['observation'] != payload['observed']:
        c.fail('plan.stale', 'Program observation changed since the controller reviewed it.', 4)
    if receipt is not None and detail['before'] != payload['candidate'] and receipt['observation'] != detail['observation']:
        c.fail('plan.stale', 'Interrupted program update no longer matches the reviewed checkout.', 4)
    result = dict(operation=key, candidate=payload['candidate'], observation=payload['observed'],
                  before=receipt['before'] if receipt else detail['before'], status='accepted')
    if receipt is None:
        fleet.put(path, result, None)
    if detail['before'] != payload['candidate']:
        if objects != root:
            sources.endpoint(root, str(objects), objects.as_uri())
            c.git(root, '-c', 'protocol.allow=never', '-c', 'protocol.file.allow=always', 'fetch',
                  '--no-tags', '--no-write-fetch-head', '--no-recurse-submodules', str(objects), 'refs/mask/program',
                  timeout=timeout, mutating=True)
        if program_observation(payload, context, root) != detail:
            c.fail('plan.stale', 'Program checkout changed before application.', 4)
        install.advance_program(home, root, config, rpc.state_at(home), detail['before'],
                                payload['candidate'], detail['migration'], {'data': {}, 'actions': []}, timeout)
    finished = dict(result, status='applied_verified', after=payload['candidate'], host_load='not_verified')
    fleet.put(path, finished, result)
    return finished


def perform(home, intent, device, policy):
    action = intent['action']
    if action.endswith('-inspect'):
        rpc.pending_guard(home)
        if action == UPGRADE[0] and 'candidate' in intent['payload']:
            with c.writer_lock(home, name='lifecycle.lock'):
                upgrade_prepare(home, intent, policy, None)
                with c.writer_lock(home):
                    rpc.recheck_authority(home, intent, device, policy)
                    rpc.pending_guard(home)
                    task = upgrade_action(home, intent, policy)
                    task['preparation'] = dict(acquire='exact', retained='device-cache-and-store',
                                               consumer_changes=False, package_code_executed=False)
                    return task
        return program_action(home, intent, device, policy) if action in PROGRAM else upgrade_action(home, intent, policy)
    with c.writer_lock(home, name='lifecycle.lock'):
        if action in PROGRAM:
            return program_action(home, intent, device, policy)
        with c.writer_lock(home):
            rpc.recheck_authority(home, intent, device, policy)
            rpc.pending_guard(home)
            path = durable_path(home, 'upgrade-results', c.digest(observation_facts(intent)))
            receipt = fleet.data(path, missing=True)
            if receipt and receipt['status'] == 'applied_verified':
                return receipt
        upgrade_prepare(home, intent, policy, receipt)
        with c.writer_lock(home):
            rpc.recheck_authority(home, intent, device, policy)
            rpc.pending_guard(home)
            return upgrade_action(home, intent, policy)


def exchange(peer, signer, action, payload, revision, timeout):
    packet = rpc.request(signer, peer['device'], peer['authority'], action, payload, revision=revision)
    proof = transport.exchange(peer, packet, timeout=timeout, signed=True)
    return proof['response'], proof


def failure_row(error, *, dispatch=False):
    code = error if isinstance(error, str) else error.code
    if code in ('fleet.response_unverified', 'fleet.commit_outcome_unknown', 'fleet.commit_proof_limit'):
        status = 'unknown'
    elif code in rollout.DISCONNECTED:
        status = 'unknown' if dispatch else 'offline'
    elif code in ('fleet.maintenance_incompatible', 'fleet.upgrade_setup_incompatible', 'fleet.program_incompatible', 'fleet.tap_management_incompatible',
                  'rpc.version_unsupported'):
        status = 'incompatible'
    elif code == 'recovery.required':
        status = 'recovery_required'
    else:
        status = 'blocked'
    return dict(status=status, reason=code)


def target(peer, scope=None):
    return dict(name=peer['name'], device=peer['device']['id'], binding=rollout.binding_digest(peer), scope=scope)


def inspect_target(peer, signer, action, payload, timeout, target, *, capability='maintenance'):
    try:
        caps = transport.probe(peer, signer, timeout=timeout)
        if caps.get(capability) != 1:
            return dict(target, **failure_row('fleet.' + capability + '_incompatible'))
        result, _ = exchange(peer, signer, action, payload, c.digest(payload), timeout)
        if result['status'] == 'refused':
            return dict(target, **failure_row(result['error']['code']))
        return dict(target, status='observed', observation=result['data'])
    except c.MaskError as error:
        return dict(target, **failure_row(error))
    except OSError:
        return dict(target, **failure_row('fleet.probe_io_failed'))


def program_plan(peers, signer, timeout):
    root = program_root()
    identity, endpoint = origin(root, timeout)
    git.checkout_preconditions(root, 'origin', 'main', 'ManageAgentSkills', timeout, clean=False)
    payload = dict(origin=identity, candidate=advertised(root, endpoint, timeout))

    def inspect(peer):
        row = target(peer)
        if peer['authority'].get('program_origin') != identity or not set(PROGRAM) <= set(peer['authority']['actions']):
            return dict(row, **failure_row('fleet.program_denied'))
        row = inspect_target(peer, signer, PROGRAM[0], payload, timeout, row)
        if row['status'] == 'observed':
            row.update(status='planned', request=dict(payload, observed=row['observation']['observation']))
        return row

    with ThreadPoolExecutor(max_workers=min(8, len(peers))) as executor:
        return dict(kind='program', candidate=payload, targets=list(executor.map(inspect, peers)))


def send_update(home, signer, digest, row, action, timeout, *, verify_receipt=None):
    peer = transport.peer_at(home, row['name'], missing=True, active=False)
    if peer is None or peer['revoked'] or rollout.binding_digest(peer) != row['binding']:
        return dict(row, **failure_row('fleet.binding_changed'))
    payload = row['request']
    expected = c.digest(dict(device=peer['device']['id'], controller=signer['id'], epoch=peer['authority']['epoch'],
                             revision=digest, action=action, payload=payload))
    receipt_path = durable_path(home, 'maintenance-receipts', c.digest(dict(plan=digest, device=row['device'], scope=row['scope'])))
    saved = fleet.data(receipt_path, missing=True)
    if saved:
        proof = saved['proof']
        fleet.verify(proof['response'], proof['signature'], peer['device'], fleet.RECEIPT)
        if proof['response']['data'].get('operation') != expected:
            c.fail('fleet.response_unverified', 'Saved maintenance receipt does not bind this request.', 4)
        if verify_receipt is not None:
            verify_receipt(proof['response']['data'], row)
        return dict(row, status='applied_verified', receipt=proof['response']['data'])
    try:
        response, proof = exchange(peer, signer, action, payload, digest, timeout)
        if response['status'] == 'refused':
            return dict(row, **failure_row(response['error']['code'], dispatch=True))
        receipt = response['data']
        if receipt.get('operation') != expected or receipt.get('status') != 'applied_verified':
            c.fail('fleet.response_unverified', 'Signed maintenance receipt does not bind the reviewed device request.', 4)
        if verify_receipt is not None:
            verify_receipt(receipt, row)
        fleet.put(receipt_path, dict(proof=proof), None)
        return dict(row, status='applied_verified', receipt=receipt)
    except c.MaskError as error:
        return dict(row, **failure_row(error, dispatch=True))


def dispatch(args, output, home):
    kind = 'program' if args.command == 'fleet.update' else 'upgrade'
    if kind == 'program' and (hasattr(args, 'scope') or hasattr(args, 'project_alias') or getattr(args, 'forward', False)):
        c.fail('invocation.invalid', 'Program updates select devices and do not take skill scopes or artifact forwarding.', 2)
    signer = fleet.get_identity(home, 'controller')
    timeout = rollout.timeout_option(args)
    approval = getattr(args, 'approve_plan', None)
    path = durable_path(home, 'maintenance-plans', approval) if approval and re.fullmatch('sha256:[0-9a-f]{64}', approval) else None
    saved = fleet.data(path, missing=True, limit=PLAN_LIMIT) if path else None
    if saved:
        plan = saved['plan']
        if c.digest(plan) != approval or plan['kind'] != kind or plan['selection'] != selection(args):
            c.fail('plan.stale', 'Use the same maintenance command and target selection as the approved preview.', 4)
        if int(time.time()) >= saved['expires']:
            c.fail('plan.stale', 'This maintenance authorization expired. Review a new preview.', 4)
    else:
        peers = rollout.choose_devices(args, home, default_all=True)
        builder = program_plan if kind == 'program' else lambda peers, signer, timeout: upgrade_plan(home, args, peers, signer, timeout)
        plan = dict(builder(peers, signer, timeout), selection=selection(args))
    digest = c.digest(plan)
    output['data'].update(plan_hash=digest, kind=kind, plan=plan, host_load='not_verified')
    if kind == 'program':
        output['would_change'] = any(row['status'] == 'planned' and
                                     row['observation']['before'] != row['observation']['candidate'] for row in plan['targets'])
    else:
        output['would_change'] = bool(plan.get('contributions')) or any(row['status'] == 'planned' for row in plan['targets'])
    if output['dry_run']:
        return
    if approval != digest:
        c.fail('plan.stale' if approval else 'confirmation.required', 'Preview the exact maintenance plan and pass its --approve-plan hash.', 4)
    if not saved:
        fleet.put(path, dict(plan=plan, expires=int(time.time()) + TTL), None, limit=PLAN_LIMIT)
    action = PROGRAM[1] if kind == 'program' else UPGRADE[1]
    if kind == 'program':
        rows = [send_update(home, signer, digest, row, action, timeout) if row['status'] == 'planned' else row
                for row in plan['targets']]
        publications = []
    else:
        rows, publications = deliver_upgrade(home, signer, digest, plan, timeout)
        output['data']['control_publications'] = publications
    complete = all(row['status'] in ('applied_verified', 'not_applicable') for row in rows)
    output['data'].update(device_results=rows, complete=complete)
    output['changed'] = bool(publications) or any(row.get('receipt', {}).get('before') != row.get('receipt', {}).get('after')
                            or row.get('receipt', {}).get('changed') or row.get('newly_observed') for row in rows)
    if output['changed']:
        output['transaction'] = 'committed'
    if not complete:
        c.fail('fleet.incomplete', 'Some reviewed devices or scopes have no verified maintenance result.', 9)


def selection(args):
    return dict(devices=sorted(getattr(args, 'device', [])), scope=getattr(args, 'scope', None),
                project_alias=getattr(args, 'project_alias', None))


def scope_observation(home, alias, policy):
    import mask_fs as fs
    import mask_resolve as resolve
    import mask_selection as selection_policy
    import mask_upgrade_commit as commits
    import mask_upgrade_groups as groups

    scope = policy['scopes'][alias]
    if not scope.get('upgrade'):
        c.fail('fleet.upgrade_denied', 'The device did not grant skill upgrades in this scope.', 4)
    state, config = rpc.state_at(home), config_at(home)
    root, record = fleet.local_scope(scope, state)
    scope = fleet.effective_scope(policy, alias, (config or {}).get('sources', {}))
    if record.get('dev_links'):
        c.fail('dev_link.active', 'Fleet cannot upgrade development links.', 4)
    declaration, locked = resolve.read_exact_lock(root, scope['scope'], home, config, verify=False)
    if (declaration, locked) != (record['last_manifest'], record['last_lock']):
        c.fail('fleet.local_drift', 'Reconcile local declaration and lock edits before fleet upgrade.', 4)
    scope_sources(scope, config, locked)
    timeout = (config or {}).get('git_timeout_seconds', 30)
    description = git_before = None
    if scope['scope'] == 'project':
        description = groups.describe(root, 'project', timeout)
        if description['git']:
            git_before = commits.observation(root, timeout)
            index_clean = c.git(root, 'diff', '--cached', '--quiet', 'HEAD', '--', *commits.PATHS,
                                optional=True, timeout=timeout) is not None
            description['clean'] = groups.clean(description) and index_clean
            description['eligible'] = commits.eligibility(root, git_before, timeout, detached=True) is None
            # A common directory identifies worktrees on this enrolled endpoint only.
            description['common_dir'] = c.digest(description['common_dir'])
            if (description['origin'] or '').startswith('file:'):
                description['origin'] = None
        description.pop('root')
    links = []
    for path in sorted(record['links']):
        c.parents_safe(root, root / path)
        links.append((path, fs.link_value(root / path)))
    observation = c.digest(dict(scope=scope, controls=(declaration, locked), record=record,
                                git=git_before, links=links, config=config, policy=selection_policy.read_policy(home)[0]))
    contribution = record.get('profiles', {}).get('fleet-' + policy['controller']['id'])
    data = dict(observation=observation, declaration=declaration, lock=locked,
                contribution=contribution['revision'] if contribution else None,
                scope_type=scope['scope'], git=description)
    if alias in policy.get('tap_management', {}).get('scopes', []):
        data['tap_sources'] = fleet.managed_taps(policy, config['sources'])
    if len(fleet.signed_bytes(data)) > fleet.RECORD_BYTES // 3:
        c.fail('fleet.scope_limit', 'The exact upgrade controls exceed the bounded fleet observation size.', 4)
    return data, root, scope, state, config, git_before, timeout


def scope_sources(scope, config, locked):
    for row in locked['packages']:
        name = row['source']
        approved = sources.selected(config, name)
        grant = scope['sources'].get(name)
        if not grant or not sources.same(grant['repository'], approved['repository']) or not sources.same(grant['repository'], row['repository']):
            c.fail('fleet.source_denied', 'The upgrade candidate uses a source outside the locally granted scope.', 4)


def verify_upgrade_pair(before, candidate):
    import mask_resolve as resolve

    if not isinstance(candidate, dict) or set(candidate) != {'declaration', 'lock'}:
        rpc.invalid('An exact upgrade requires declaration and lock controls.')
    declaration = resolve.selection(candidate['declaration'])
    locked = resolve.lock(candidate['lock'], declaration)
    if declaration != before['declaration']:
        c.fail('fleet.selection_changed', 'Fleet upgrades preserve locally declared selections.', 4)
    after = {resolve.coordinate(row): row for row in locked['packages']}
    held = {resolve.coordinate(binding) for binding in declaration['skills'] if binding.get('pinned')}
    for row in before['lock']['packages']:
        coordinate = resolve.coordinate(row)
        replacement = after[coordinate]
        if ((coordinate in held or 'commit' in row['selector']) and replacement != row or
                replacement['selector'] != row['selector'] or not sources.same(replacement['repository'], row['repository'])):
            c.fail('fleet.pin_conflict', 'Fleet upgrades preserve held versions, exact selectors and tap identities.', 4)
    return declaration, locked


def git_fingerprint(observed):
    return c.digest({key: observed[key] for key in ('head', 'top', 'branch', 'git_dir', 'index', 'index_fingerprint')})


def proposed_profiles(intent, scope, config, record):
    payload = intent['payload']
    profiles = record.get('profiles', {})
    if 'profile' not in payload:
        return None, []
    name = rpc.contribution_name(intent)
    previous = profiles.get(name)
    if not scope.get('rollout') or not previous or previous.get('fleet_controller') != intent['controller']:
        c.fail('fleet.rollout_denied', 'A combined upgrade requires the controller’s existing locally authorized contribution.', 4)
    profile = payload['profile']
    verify_upgrade_pair(previous, {key: profile[key] for key in ('declaration', 'lock')})
    scope_sources(scope, config, profile['lock'])
    return dict(profiles, **{name: dict(profile, fleet_controller=intent['controller'])}), [previous, profile]


def upgrade_prepare(home, intent, policy, receipt):
    payload = intent['payload']
    before, root, scope, state, config, _, _ = scope_observation(home, payload['scope'], policy)
    declaration, locked = verify_upgrade_pair(before, payload['candidate'])
    scope_sources(scope, config, locked)
    if before['observation'] != payload['observed'] and (
            not receipt or (declaration, locked) != (before['declaration'], before['lock'])):
        c.fail('plan.stale', 'Skill scope changed since the controller reviewed it.', 4)
    record = c.consumer_records(state)[str(root)]
    layers = [dict(declaration=declaration, lock=locked),
              dict(declaration=before['declaration'], lock=before['lock'])]
    _, contribution_layers = proposed_profiles(intent, scope, config, record)
    layers.extend(contribution_layers)
    # Acquire only the individually granted local choices. Other profile layers stay owned.
    rpc.prepare_artifacts(home, intent,
                          (state, config, root, scope, layers, record.get('profiles', {})))


def activate_upgrade(home, intent, state, root, scope, config, declaration, locked, before):
    import mask_fs as fs

    record = c.consumer_records(state)[str(root)]
    subscriptions, contribution_layers = proposed_profiles(intent, scope, config, record)
    planned = fs.plan(config, state, [root], home=home, proposals={str(root): declaration},
                      lock_proposals={str(root): locked}, operation='upgrade', retire_files=False,
                      profile_proposals={str(root): subscriptions} if subscriptions is not None else None,
                      repair_roles=True)
    fs.ensure_applicable(planned)
    before_links = record['links']
    after_links = c.consumer_records(planned['intent']['after_state'])[str(root)]['links']
    import mask_resolve as resolve
    locks = [before['lock'], locked, *(layer['lock'] for layer in contribution_layers)]
    allowed = {resolve.coordinate(row) for control in locks for row in control['packages']}
    if any(resolve.coordinate(link['resolution']) not in allowed for effect in planned['intent']['links']
           for link in (before_links.get(effect['relative']), after_links.get(effect['relative'])) if link):
        c.fail('fleet.local_drift', 'Reconcile unrelated links before applying the reviewed fleet upgrade.', 4)
    import mask_setup as setup
    rows = setup.proposals(planned, repair=True)
    for action in rows:
        packages = [row for control in locks for row in control['packages']
                    if resolve.coordinate(row) == action['coordinate']]
        if not packages:
            c.fail('fleet.local_drift', 'Reconcile unrelated native roles before fleet upgrade.', 4)
        for role in action.get('native_roles', []):
            producers = [link['resolution'] for link in after_links.values()
                         if link['skill'] == action['skill'] and link['target'] == role['agent']]
            if not producers or any(resolve.coordinate(row) != action['coordinate'] for row in producers):
                c.fail('fleet.local_drift', 'A setup role belongs to another package contribution.', 4)
        scope_sources(scope, config, dict(packages=packages))
    for effect in planned['intent'].get('native_roles', []):
        packages = [link['resolution'] for links in (before_links, after_links) for link in links.values()
                    if link['skill'] == effect['skill'] and link['target'] == effect['agent']]
        if not packages or any(resolve.coordinate(row) not in allowed for row in packages):
            c.fail('fleet.local_drift', 'Reconcile unrelated native roles before fleet upgrade.', 4)
        if effect['after'] is not None:
            producer = next(skill['package']['coordinate'] for report in planned.get('workflow_readiness', [])
                            for skill in report['skills'] if skill['skill'] == effect['skill'])
            if any(resolve.coordinate(row) != producer for row in packages):
                c.fail('fleet.local_drift', 'A native role belongs to another package contribution.', 4)
        scope_sources(scope, config, dict(packages=packages))
    return planned


def upgrade_task(planned):
    """Use the ordinary task review to bind setup, inputs and replacement before-bytes."""
    from types import SimpleNamespace
    import mask
    import mask_lifecycle as lifecycle
    import mask_setup as setup

    rows = setup.proposals(planned, repair=True)
    output = mask.result('fleet.upgrade', dry_run=True)
    lifecycle.review(SimpleNamespace(command='fleet.upgrade'), output, planned, rows)
    inputs = [item for report in planned.get('workflow_readiness', []) for skill in report['skills']
              for item in skill['inputs'] if item['state'] in ('missing', 'invalid')]
    if inputs or any(row['state'] == 'blocked' for row in rows):
        c.fail('workflow.incomplete', 'Required consumer inputs or setup are unavailable; no consumer changes were applied.', 4,
               inputs=inputs, setup=rows)
    # Include all role observations, including absent generated destinations, and passive input checks.
    # Bind this scope, not the device-wide generation: another reviewed scope may apply first.
    intent = planned['intent']
    projection = {key: value for key, value in intent.items() if key not in ('before_state', 'after_state')}
    for side in ('before_state', 'after_state'):
        projection[side] = {root: c.consumer_records(intent[side])[root] for root in intent['selected']}
    planned['plan_hash'] = c.digest(dict(task=projection, setup=[row.get('fingerprint', row) for row in rows],
                                       actions=output['data']['review']['actions'],
                                       readiness=planned.get('workflow_readiness', [])))
    task = dict(plan_hash=planned['plan_hash'], actions=output['data']['review']['actions'], setup=rows,
                workflow_readiness=planned.get('workflow_readiness', []))
    return task, rows


def execute_upgrade_setup(home, root, config, task, rows):
    import mask
    import mask_fs as fs
    import mask_setup as setup

    observed = {(skill['skill'], role['agent'], role['name']): role.get('observed_sha256')
                for report in task['workflow_readiness'] for skill in report['skills'] for role in skill['roles']}
    for row in rows:
        row.update(state='granted', granted_by='approve-plan')

    def replan(staged=None):
        planned = fs.plan(config, rpc.state_at(home), [root], home=home, operation='ensure',
                          repair_roles=True, retire_files=False, staged_roles=staged)
        fs.ensure_applicable(planned)
        for report in planned.get('workflow_readiness', []):
            for skill in report['skills']:
                for role in skill['roles']:
                    group = [row for row in rows if row['state'] == 'granted' and row['skill'] == skill['skill'] and
                             dict(agent=role['agent'], name=role['name']) in row['native_roles']]
                    if group and role.get('observed_sha256') != observed[(skill['skill'], role['agent'], role['name'])]:
                        setup.stale(group, staged is not None, 'a reviewed role destination changed')
        return planned

    output = mask.result('fleet.upgrade')
    output['data']['setup'] = dict(actions=rows)
    setup.execute(output, home, replan, rows)
    final = replan()
    if any(not entry['complete'] for entry in final.get('workflow_readiness', [])):
        c.fail('workflow.incomplete', 'Fleet setup did not complete workflow readiness.', 4)
    return output


def execute_scope(home, planned, desired_intent, key):
    import mask
    import mask_fs as fs

    output = mask.result('fleet.upgrade')
    output['actions'] = list(planned['actions'])
    if desired_intent is None:
        fs.execute(planned, home, output)
        return output
    if not planned['would_change']:
        return output
    # The ordinary fleet journal owns the profile and the ordinary pinned
    # journal owns its matching local lock. Both publish in one transaction.
    payload = {name: desired_intent['payload'][name] for name in ('scope', 'profile')}
    journal_intent = dict(desired_intent, action='apply', id=key[7:39], payload=dict(payload, plan=planned['plan_hash']),
                          generation=planned['intent']['before_state']['generation'])
    record = rpc.operation_record(journal_intent)
    path = rpc.operation_path(home, record['id'])
    previous = fleet.data(path, missing=True)
    if previous and previous['status'] != 'accepted':
        c.fail('fleet.operation_conflict', 'The combined profile and local lock transition already has a recorded outcome.', 4)
    fleet.put(path, record, previous)
    rpc.commit_plan(home, journal_intent, record, planned, output=output)
    return output


def upgrade_action(home, intent, policy):
    import mask_fleet_commit as transfer
    import mask_upgrade_commit as commits

    payload = intent['payload']
    alias = payload['scope']
    if intent['action'] == UPGRADE[0] and 'candidate' not in payload:
        return scope_observation(home, alias, policy)[0]
    key = c.digest(observation_facts(intent))
    path = durable_path(home, 'upgrade-results', key)
    receipt = fleet.data(path, missing=True)
    if receipt and receipt['status'] == 'applied_verified':
        return receipt
    before, root, scope, state, config, git_before, timeout = scope_observation(home, alias, policy)
    declaration, locked = verify_upgrade_pair(before, payload['candidate'])
    scope_sources(scope, config, locked)
    if intent['action'] == UPGRADE[0]:
        if before['observation'] != payload['observed']:
            c.fail('plan.stale', 'Skill scope changed during exact candidate inspection.', 4)
        planned = activate_upgrade(home, intent, state, root, scope, config, declaration, locked, before)
        return upgrade_task(planned)[0]
    commit = payload['commit']
    if receipt is None and before['observation'] != payload['observed']:
        c.fail('plan.stale', 'Skill scope changed since the controller reviewed it.', 4)
    if receipt and before['observation'] != payload['observed'] and (declaration, locked) != (before['declaration'], before['lock']):
        c.fail('plan.stale', 'Interrupted skill upgrade no longer matches the reviewed scope.', 4)
    git_row = final = received = None
    if commit:
        if not scope.get('commit') or not git_before or not before['git']['eligible']:
            c.fail('fleet.commit_denied', 'The scope has no eligible explicit project commit grant.', 4)
        if receipt is None and not before['git']['clean']:
            c.fail('fleet.controls_modified', 'Project controls or their staging differ from HEAD.', 4)
        if receipt is None and before['git']['controls'] != commit['controls']:
            c.fail('plan.stale', 'The reviewed commit starts from different controls.', 4)
        if commit['role'] == 'canonical' and not git_before['branch']:
            c.fail('fleet.commit_ineligible', 'A canonical project commit requires an attached branch.', 4)
        expected_head = receipt['before_head'] if receipt else git_before['head']
        final = commits.controls(root)
        if locked != before['lock']:
            final['.mask.lock.json'] = c.text_json(locked).encode('utf-8')
        final_digests = {name: c.digest(data) for name, data in final.items()}
        if final_digests != commit['final']:
            c.fail('plan.stale', 'The reviewed commit would use different final controls.', 4)
        if commit['role'] == 'member':
            received = transfer.verify(root, commit['proof'], commit, final, timeout, before_head=expected_head)
        elif commit['parent'] != expected_head:
            c.fail('plan.stale', 'Canonical project head changed since approval.', 4)
        git_row = commits.result_row(root, 'project')
        git_row.update(status='planned', before_head=expected_head, after_head=git_before['head'],
                       paths=[name for name in commits.PATHS if c.git(root, 'show', expected_head + ':' + name, binary=True, timeout=timeout) != final[name]],
                       detached=git_before['branch'] is None)
        if receipt and git_before['head'] != expected_head:
            # A lost acknowledgement after the ordinary Git commit needs no second commit.
            observed = transfer.pack(root, git_before['head'], timeout)
            check = dict(parent=expected_head, controls=commit['controls'])
            transfer.verify(root, observed, check, final, timeout, before_head=expected_head)
            if not before['git']['clean'] or received and received['parent'] == expected_head and received['commit'] != observed['commit']:
                c.fail('fleet.commit_outcome_unknown', 'The prior Git transition needs local index inspection.', 4)
            git_row.update(status='committed', commit=git_before['head'])
        elif receipt and git_fingerprint(git_before) != receipt['git_before']:
            c.fail('fleet.commit_outcome_unknown', 'Project Git state changed after the upgrade was accepted.', 4)
    elif scope['scope'] == 'project' and locked != before['lock']:
        c.fail('fleet.commit_denied', 'Changed project controls require a reviewed canonical commit or propagation.', 4)
    desired_intent = None
    if 'desired' in payload:
        desired = payload['desired']
        if desired['sequence'] < policy['minimum_sequence']:
            c.fail('fleet.sequence_stale', 'The published contribution is below the enrolled sequence floor.', 4)
        desired_intent = dict(intent, sequence=desired['sequence'], revision=desired['revision'])
        rpc.sequence_guard(home, desired_intent)
    planned = activate_upgrade(home, intent, state, root, scope, config, declaration, locked, before)
    task, setup_rows = upgrade_task(planned)
    if receipt is None:
        needs_review = setup_rows or any(row.get('repair') for row in planned['intent'].get('native_roles', []))
        if (('task' in payload and payload['task'] != task['plan_hash']) or
                ('task' not in payload and needs_review)):
            c.fail('plan.stale' if 'task' in payload else 'fleet.local_setup_required',
                   'Review the exact device setup and native role task before fleet apply.', 4)
    elif setup_rows:
        # A lost setup reply or failed launch is never permission to execute package code again.
        c.fail('fleet.setup_outcome_unknown', 'Inspect and repair the interrupted setup locally, then review a new fleet plan.', 4)
    if scope_observation(home, alias, policy)[0]['observation'] != before['observation']:
        c.fail('plan.stale', 'Skill scope changed during exact artifact preparation.', 4)
    if receipt is None:
        receipt = dict(operation=key, status='accepted', changed=planned['would_change'] or bool(commit) or bool(setup_rows),
                       before_head=git_before['head'] if git_before else None,
                       git_before=git_fingerprint(git_before) if git_before else None)
        fleet.put(path, receipt, None)
    if desired_intent is not None:
        rpc.sequence_guard(home, desired_intent, advance=True)
    activation = execute_scope(home, planned, desired_intent, key)
    setup_output = execute_upgrade_setup(home, root, config, task, setup_rows)
    if git_row and git_row['status'] == 'planned':
        if received is None:
            commits.execute(git_row, git_before, final, timeout)
        else:
            git_before['detached'] = True
            commits.propagate(git_row, git_before, final, dict(status='committed', commit=received['commit']),
                              timeout, received=received)
        if git_row['status'] != 'committed' or git_row['error']:
            c.fail('fleet.commit_outcome_unknown', 'The skills were applied but the Git result requires inspection.', 4)
    result = dict(receipt, status='applied_verified', host_load='not_verified')
    if setup_rows:
        result['setup'] = setup_output['data']['setup']
    backups = activation['data'].get('backups', []) + setup_output['data'].get('backups', [])
    if backups:
        result['backups'] = backups
    if git_row:
        result['commit'] = git_row['commit']
        result['propagation'] = git_row.get('propagation') or (
            'canonical' if received is None else 'fast_forward' if received['parent'] == git_row['before_head'] else 'cherry_pick')
        if received is None:
            result['proof'] = transfer.pack(root, result['commit'], timeout)
            transfer.verify(root, result['proof'], commit, final, timeout, before_head=git_row['before_head'])
    fleet.put(path, result, receipt)
    return result


def scope_aliases(args, peer):
    requested = getattr(args, 'scope', None)
    alias = getattr(args, 'project_alias', None)
    grants = peer['authority']['scopes']
    if alias:
        fleet.token(alias)
        if requested not in (None, 'project'):
            c.fail('invocation.invalid', 'A mapped project alias selects project scope.', 2)
        return [alias]
    if requested not in (None, 'user'):
        c.fail('invocation.invalid', 'Use --scope user or --project-alias ALIAS.', 2)
    return [name for name, grant in sorted(grants.items())
            if grant.get('upgrade') and (requested is None or grant['scope'] == requested)]


def upgrade_plan(home, args, peers, signer, timeout):
    from contextlib import nullcontext
    import mask_control as control
    import mask_resolve as resolve
    import mask_update
    import mask_upgrade_groups as groups

    config = config_at(home)
    if config is None:
        c.fail('config.missing', 'Initialize the controller and fetch its approved tap catalogs before fleet upgrade.', 4)
    if getattr(args, 'forward', False):
        c.fail('invocation.invalid', 'Fleet upgrade acquires only the exact selected objects from each device’s approved taps.', 2)
    jobs = []
    by_peer = {peer['name']: peer for peer in peers}
    for peer in peers:
        aliases = scope_aliases(args, peer)
        jobs.extend((peer, alias) for alias in aliases or [None])
    if len(jobs) > control.MAX_DEVICES:
        c.fail('fleet.scope_limit', 'Select at most 64 fleet device/scope targets in one upgrade.', 4)

    def inspect(job):
        peer, alias = job
        row = target(peer, alias)
        grant = peer['authority']['scopes'].get(alias, {})
        if not alias and not getattr(args, 'scope', None):
            return dict(row, status='not_applicable', reason='fleet.no_upgrade_scopes')
        if not grant.get('upgrade') or not set(UPGRADE) <= set(peer['authority']['actions']):
            return dict(row, **failure_row('fleet.upgrade_denied'))
        if getattr(args, 'project_alias', None) and grant['scope'] != 'project':
            return dict(row, **failure_row('fleet.scope_unmapped'))
        return inspect_target(peer, signer, UPGRADE[0], dict(scope=alias), timeout, row)

    with ThreadPoolExecutor(max_workers=min(8, len(jobs))) as executor:
        rows = list(executor.map(inspect, jobs))
    described = {}
    for index, row in enumerate(rows):
        if row['status'] != 'observed':
            continue
        observation = row['observation']
        row['scope_type'] = observation['scope_type']
        fact = observation['git']
        if not fact or not fact['git']:
            continue
        key = f'{index:03d}'
        described[key] = dict(fact, root=key, common_dir=row['device'] + '/' + fact['common_dir'])
    grouped = groups.partition(list(described.values()))
    in_group = {fact['root'] for group in grouped for fact in group}
    grouped.extend([fact] for key, fact in described.items() if key not in in_group)
    groups_data = []
    memo = {}

    def candidate_for(observation):
        declaration, locked = observation['declaration'], observation['lock']
        key = c.digest((declaration, locked))
        if key not in memo:
            memo[key] = dict(declaration=declaration, lock=resolve.resolve_candidate(
                declaration, config, home, locked, refresh=True))
        return memo[key]

    def authorize_candidate(row, candidate):
        scope = fleet.effective_scope(by_peer[row['name']]['authority'], row['scope'],
                                      row['observation'].get('tap_sources', {}))
        scope_sources(scope, config, candidate['lock'])

    def plan_row(row, candidate, commit=None):
        authorize_candidate(row, candidate)
        row['changes'] = mask_update.changes(row['observation']['lock'], candidate['lock'])
        row.update(status='planned', request=dict(scope=row['scope'], observed=row['observation']['observation'],
                                                  candidate=candidate, commit=commit))

    def project_blocker(row, reason):
        # A Git blocker matters only when this scope needs a change to its own controls.
        observation = row['observation']
        try:
            candidate = candidate_for(observation)
            if candidate['lock'] == observation['lock']:
                authorize_candidate(row, candidate)
                row.update(status='not_applicable', reason='fleet.scope_current')
                return
        except c.MaskError as error:
            reason = error
        row.update(failure_row(reason))

    for group in grouped:
        eligible = [fact for fact in group if fact['clean'] and fact['eligible']
                    and by_peer[rows[int(fact['root'])]['name']]['authority']['scopes'][rows[int(fact['root'])]['scope']].get('commit')]
        canonical, reason = groups.choose(eligible, None, True, ())
        groups_data.append(dict(repository=groups.identity(group), reason=reason,
                                canonical=target_ref(rows[int(canonical['root'])]) if canonical else None,
                                members=[target_ref(rows[int(fact['root'])]) for fact in group]))
        if not canonical:
            for fact in group:
                row = rows[int(fact['root'])]
                project_blocker(row, 'upgrade.group_ambiguous' if eligible else 'fleet.commit_ineligible')
            continue
        main = rows[int(canonical['root'])]
        try:
            candidate = candidate_for(main['observation'])
            changed = candidate['lock'] != main['observation']['lock']
            after = dict(canonical['controls'])
            if changed:
                after['.mask.lock.json'] = c.digest(c.text_json(candidate['lock']).encode('utf-8'))
            commit = dict(role='canonical', parent=canonical['head'], controls=canonical['controls'], final=after)
            plan_row(main, candidate, commit if changed else None)
        except c.MaskError as error:
            main.update(failure_row(error))
        for fact in group:
            row = rows[int(fact['root'])]
            if fact is canonical:
                continue
            if not fact['clean'] or not fact['eligible']:
                project_blocker(row, 'fleet.controls_modified')
            elif main['status'] != 'planned':
                project_blocker(row, 'upgrade.canonical_blocked')
            elif fact['controls'] != canonical['controls']:
                project_blocker(row, 'fleet.controls_diverged')
            elif changed and fact not in eligible:
                project_blocker(row, 'fleet.commit_denied')
            else:
                try:
                    plan_row(row, candidate, dict(commit, role='member', source=target_ref(main)) if changed else None)
                except c.MaskError as error:
                    row.update(failure_row(error))
    for row in rows:
        if row['status'] != 'observed':
            continue
        try:
            candidate = candidate_for(row['observation'])
            if row['scope_type'] == 'project' and candidate['lock'] != row['observation']['lock']:
                row.update(failure_row('fleet.commit_ineligible'))
            else:
                plan_row(row, candidate)
        except c.MaskError as error:
            row.update(failure_row(error))
    settings = control.settings(home, missing=True)
    with control.snapshot(home, settings, signer) if settings else nullcontext(None) as history:
        contributions = contribution_plan(history, rows, by_peer, signer, candidate_for)

    def inspect_task(row):
        if row['status'] != 'planned':
            return row
        payload = {name: row['request'][name] for name in ('scope', 'observed', 'candidate', 'profile')
                   if name in row['request']}
        exact = inspect_target(by_peer[row['name']], signer, UPGRADE[0], payload, timeout,
                               target(by_peer[row['name']], row['scope']), capability='upgrade_setup')
        if exact['status'] != 'observed':
            row.update(status=exact['status'], reason=exact['reason'])
            row.pop('request')
        else:
            row['task'] = exact['observation']
            row['request']['task'] = row['task']['plan_hash']
        return row

    by_device = {}
    for row in rows:
        by_device.setdefault(row['device'], []).append(row)

    def inspect_device(device_rows):
        # Exact acquisition/planning shares one device writer lock across its scope aliases.
        for row in device_rows:
            inspect_task(row)

    with ThreadPoolExecutor(max_workers=min(8, len(by_device))) as executor:
        list(executor.map(inspect_device, by_device.values()))
    if contributions:
        blocked = {tuple(target_ref(row)) for row in rows if row['status'] not in ('planned', 'not_applicable')}
        contributions['batches'] = [[target for target in batch if tuple(control.target_key(target)) not in blocked]
                                    for batch in contributions['batches']]
        contributions['batches'] = [batch for batch in contributions['batches'] if batch]
        if not contributions['batches']:
            contributions = None
    for row in rows:
        if 'observation' in row:
            row['observation'].pop('declaration')
            row['observation'].pop('lock')
    return dict(kind='upgrade', targets=rows, groups=groups_data, contributions=contributions)


def target_ref(row):
    return [row['device'], row['scope']]


def contribution_plan(history, rows, peers, signer, candidate_for):
    if history is None:
        return None
    import mask_control as control

    effective = history.effective()
    updated = []
    actions = set(UPGRADE) | {'inspect', 'prepare', 'apply', 'receipt'}
    for row in rows:
        peer = peers[row['name']]
        previous = effective.get(tuple(target_ref(row)))
        if previous is None or previous[0]['action'] == 'cancel' or not previous[1]['profile']:
            continue
        target = previous[1]
        scope = peer['authority']['scopes'].get(row['scope'], {})
        if (not scope.get('upgrade') or not scope.get('rollout') or
                not actions <= set(peer['authority']['actions']) or fleet.public(signer) != peer['authority']['controller']):
            continue
        profile = target['profile']
        try:
            candidate = candidate_for(profile)
            if candidate['lock'] == profile['lock']:
                continue
            proposed = dict(target, name=peer['name'], identity=peer['device'], binding=row['binding'],
                            device_epoch=peer['authority']['epoch'],
                            profile=control.desired_profile(candidate['declaration'], candidate['lock']))
            rollout.validate_sources(proposed, peer, False, row.get('observation', {}).get('tap_sources', {}))
            if 'blocked' in proposed:
                raise c.MaskError(proposed['blocked'], 'Fleet profile upgrade is outside its current scope grant.', 4)
            if row['status'] == 'planned' and row['observation']['contribution'] == profile['revision']:
                row['request']['profile'] = proposed['profile']
            updated.append(proposed)
        except c.MaskError as error:
            row['contribution_error'] = error.code
    batches = []
    for target in updated:
        for batch in batches:
            if target['name'] not in {member['name'] for member in batch}:
                batch.append(target)
                break
        else:
            batches.append([target])
    return dict(channel=control.channel(history.control), head=history.head, batches=batches) if batches else None


def deliver_upgrade(home, signer, digest, plan, timeout):
    from contextlib import nullcontext
    import mask_control as control

    proposal = plan['contributions']
    settings = control.settings(home, missing=True) if proposal else None
    history_context = (control.snapshot(home, settings, signer)
                       if settings and control.channel(settings) == proposal['channel'] else nullcontext(None))
    with history_context as history:
        published, failures, publications = publish_contributions(home, signer, digest, history, proposal)
        results = deliver_upgrade_scopes(home, signer, digest, plan, published, timeout)
        if history:
            pairs = list(published.values())
            contribution_rows = rollout.fanout(home, signer, history, pairs, timeout=timeout)
            results.extend(dict(row, contribution=True, operation=entry['operation'])
                           for row, (entry, _) in zip(contribution_rows, pairs))
        return results + failures, publications


def deliver_upgrade_scopes(home, signer, digest, plan, published, timeout):
    import mask_control as control

    def apply(row, key, *, proof=None):
        request = dict(row['request'])
        if 'profile' in request:
            entry_target = published.get(key)
            if not entry_target or entry_target[1]['profile'] != request['profile']:
                return dict(row, **failure_row('fleet.control_conflict'))
            entry, _ = entry_target
            request['desired'] = dict(sequence=entry['sequence'], revision=control.intent_digest(entry))
        if proof is not None:
            request['commit'] = dict(request['commit'], proof=proof)
        result = send_update(home, signer, digest, dict(row, request=request), UPGRADE[1], timeout)
        return dict(result, request=row['request'])

    completed = {}
    deferred = []
    for row in plan['targets']:
        request = row.get('request')
        commit = request['commit'] if request else None
        key = tuple(target_ref(row))
        if commit and commit['role'] == 'member':
            deferred.append((key, row, commit))
        elif row['status'] == 'planned':
            completed[key] = apply(row, key)
        else:
            completed[key] = row
    for key, row, commit in deferred:
        canonical = completed[tuple(commit['source'])]
        proof = canonical.get('receipt', {}).get('proof')
        if not proof:
            completed[key] = dict(row, **failure_row('upgrade.canonical_commit_missing'))
            continue
        completed[key] = apply(row, key, proof=proof)
    rows = [completed[tuple(target_ref(row))] for row in plan['targets']]
    for row in list(rows):
        if row.get('contribution_error'):
            rows.append(dict(name=row['name'], scope=row['scope'], contribution=True,
                             **failure_row(row['contribution_error'])))
    return rows


def publish_contributions(home, signer, digest, history, proposal):
    if proposal is None:
        return {}, [], []
    import mask_control as control

    batches = proposal['batches']
    def failed(batch, code):
        return [dict(rollout.base_result(target), contribution=True, **failure_row(code, dispatch=True)) for target in batch]

    if history is None:
        return {}, [row for batch in batches for row in failed(batch, 'fleet.control_changed')], []
    published, rows, publications = {}, [], []
    operations = [c.digest((digest, index)).split(':')[1][:32] for index in range(len(batches))]
    for index, (operation, batch) in enumerate(zip(operations, batches)):
        entry = history.operation(operation)
        if entry is None:
            prefix = history.events[-index:] if index else []
            if ((not index and history.head != proposal['head']) or
                    (index and [item['operation'] for item in prefix] != operations[:index])):
                rows.extend(failed(batch, 'fleet.control_conflict'))
                continue
            entry = control.event(history.control, signer, history.events, 'update', operation, batch,
                                  {'kind': 'fleet.upgrade', 'plan': digest, 'forward': False})
            try:
                revision = control.publish(history, entry, signer)
                publications.append(dict(operation=operation, commit=revision))
                control.remember(home, history)
            except c.MaskError as error:
                rows.extend(failed(batch, error.code))
                continue
        if entry['targets'] != sorted(batch, key=control.target_key) or entry['input'].get('plan') != digest:
            rows.extend(failed(batch, 'fleet.operation_conflict'))
            continue
        for target in entry['targets']:
            key = control.target_key(target)
            if history.effective().get(key) != (entry, target):
                rows.extend(failed([target], 'fleet.operation_superseded'))
            else:
                published[key] = (entry, target)
    return published, rows, publications
