"""Portable personal declarations and exact locks, through the ordinary task engine."""
from __future__ import annotations

import copy
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit

import mask_core as c
import mask_fs as fs
import mask_lifecycle as lifecycle
import mask_pinned as pinned
import mask_resolve as r
import mask_selection as selection
import mask_sources as sources
import mask_store as store
import mask_task as task


PORTABLE_FILES = ('selection.json', 'selection.lock.json')
ORIGIN = re.compile(r'bundle:[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*')


def pair(declaration, packages):
    declaration = r.selection(declaration)
    return declaration, r.lock(dict(schema_version=1, resolver='mask-lock-v1',
                                    selection_digest=r.selection_digest(declaration), packages=list(packages)), declaration)


def portable(declaration, locked):
    """Only portable repository authority and structured bundle annotations leave this machine."""
    declaration = copy.deepcopy(declaration)
    repositories = [entry['repository'] for entry in declaration['sources'].values()]
    for value in repositories:
        uri = urlsplit(value)
        if uri.scheme == 'file' or uri.username not in (None, 'git') or uri.path.startswith('/~/'):
            c.fail('profile.nonportable_source', 'Portable profiles require a repository identity independent of a local path or SSH account.', 4)
    bindings = list(declaration['skills'])
    for receipt in declaration.get('bundle_state', {}).get('bundles', {}).values():
        receipt['repository'] = sources.repository(receipt['repository'])
        bindings.extend(receipt['bindings'])
    for binding in bindings:
        annotations = [origin for origin in binding.get('introduced_by', []) if ORIGIN.fullmatch(origin)]
        binding.pop('introduced_by', None)
        if annotations:
            binding['introduced_by'] = annotations
    for entry in declaration['sources'].values():
        entry['repository'] = sources.repository(entry['repository'])
    return pair(declaration, (dict(row, repository=sources.repository(row['repository'])) for row in locked['packages']))


def location(value):
    return Path(value).expanduser().absolute()


def read_profile(value):
    root = location(value)
    manifest, lockfile = (root / name for name in PORTABLE_FILES)
    declaration, manifest_raw = r.read_model(manifest, 'selection')
    declaration = r.selection(declaration)
    locked, lock_raw = r.read_model(lockfile, 'lock')
    locked = r.lock(locked, declaration)
    declaration, locked = portable(declaration, locked)
    revision = c.digest(dict(selection=c.digest(manifest_raw), lock=c.digest(lock_raw)))
    return declaration, locked, revision


def local_pair(home, *, missing=False):
    declaration, _ = r.read_model(home / 'user.json', 'selection', missing=missing)
    locked, _ = r.read_model(home / 'user.lock.json', 'lock', missing=missing)
    if declaration is None and locked is None:
        return None, None
    declaration = r.selection(declaration)
    return declaration, r.lock(locked, declaration)


def personal_root(args, state):
    record = state.get('user')
    explicit = getattr(args, 'user_home', None)
    root = Path(explicit).expanduser().resolve() if explicit is not None else Path(record['root']) if record else Path.home().resolve()
    if record is not None and str(root) != record['root']:
        c.fail('user.already_registered', 'Select the registered personal home or unregister it first.', 4)
    if not root.is_dir():
        c.fail('user.not_found', 'The personal home must be an existing directory.', 4, root=str(root))
    return root


def targets(binding, declaration):
    return binding.get('agents', declaration['default_agents'])


def conflict(key, reason):
    c.fail('profile.conflict', 'Local and imported selections cannot be combined without changing their intent.', 4,
           skill=key, reason=reason, origins=['local', 'profile'])


def merge(local, incoming):
    """Merge exact controls while preserving independent target intent and bundle receipts."""
    before, old_lock = local
    after, imported_lock = incoming
    if before is None or before == after and old_lock == imported_lock:
        return after, imported_lock
    proposal = copy.deepcopy(before)
    existing = {r.coordinate(row): row for row in proposal['skills']}
    rows = {r.coordinate(row): row for row in old_lock['packages']}
    imported = {r.coordinate(row): row for row in imported_lock['packages']}
    for name, entry in after['sources'].items():
        prior = proposal['sources'].get(name)
        if prior is not None and (not sources.same(prior['repository'], entry['repository']) or prior['packages'] != entry['packages']):
            conflict(name, 'source_identity_or_layout')
        if prior is None:
            proposal['sources'][name] = entry
    for binding in after['skills']:
        key = r.coordinate(binding)
        prior = existing.get(key)
        incoming_agents = targets(binding, after)
        selector = r.declared_selector(after, binding)
        if prior is None:
            new = dict(binding, agents=incoming_agents)
            # Importing a binding does not inherit another contribution's default source ref.
            source_ref = proposal['sources'][binding['source']].get('ref')
            if selector != ({'ref': source_ref} if source_ref else None):
                new['version'] = selector or imported[key]['selector']
            proposal['skills'].append(new)
            rows[key] = imported[key]
            continue
        prior_agents = targets(prior, before)
        if prior.get('when') != binding.get('when'):
            conflict(key, 'conditions')
        if r.declared_selector(before, prior) != selector or r.payload_key(rows[key]) != r.payload_key(imported[key]):
            conflict(key, 'exact_resolution_or_selector')
        combined = 'all' if 'all' in (prior_agents, incoming_agents) else sorted(set(prior_agents) | set(incoming_agents))
        if combined != prior_agents:
            prior['agents'] = combined
        if binding.get('pinned'):
            prior['pinned'] = True
        annotations = sorted(set(prior.get('introduced_by', [])) | set(binding.get('introduced_by', [])))
        if annotations:
            prior['introduced_by'] = annotations
    if 'bundle_state' in before or 'bundle_state' in after:
        def ledger(declaration):
            return declaration.get('bundle_state', dict(manual=[r.coordinate(row) for row in declaration['skills']], bundles={}))
        left, right = ledger(before), ledger(after)
        receipts = dict(left['bundles'])
        for name, receipt in right['bundles'].items():
            if name in receipts and receipts[name] != receipt:
                conflict(name, 'bundle_revision')
            receipts[name] = receipt
        proposal['bundle_state'] = dict(manual=sorted(set(left['manual']) | set(right['manual'])), bundles=receipts)
    return pair(proposal, rows.values())


def subscriptions(value):
    if not isinstance(value, dict) or len(value) > 63:
        c.fail('profile.invalid', 'Expected at most 63 personal subscriptions.', 4)
    size = 0
    for name, receipt in value.items():
        c.skill_id(name)
        c.fields(receipt, ('revision', 'declaration', 'lock'), family='profile')
        if not isinstance(receipt['revision'], str) or not r.SHA.fullmatch(receipt['revision']):
            c.fail('profile.invalid', 'Subscription requires an exact profile revision.', 4)
        declaration = r.selection(receipt['declaration'])
        locked = r.lock(receipt['lock'], declaration)
        size += len(r.canonical(receipt, 'profile'))
        if size > r.MODEL_BYTES:
            c.fail('profile.limit', 'Frozen subscriptions exceed 4 MiB.', 4)
        if portable(declaration, locked) != (receipt['declaration'], receipt['lock']):
            c.fail('profile.invalid', 'Subscription controls must contain normalized portable data.', 4)
    return value


def layers(declaration, locked, profiles):
    return [dict(origin='local', declaration=declaration, lock=locked)] + [
        dict(origin='profile:' + name, declaration=receipt['declaration'], lock=receipt['lock'])
        for name, receipt in sorted(profiles.items())
    ]


def freshness(profiles):
    return [dict(profile=name, revision=receipt['revision'], freshness='last_approved_offline')
            for name, receipt in sorted(profiles.items())]


def prepare_layers(home, profiles, config, effects, *, root, offline=True):
    for receipt in profiles.values():
        declaration = receipt['declaration']
        observation = dict(root=str(root), effects={})
        effects.append(observation)
        store.ensure(home, declaration, receipt['lock'], config, offline=offline,
                     coordinates=selection.applicable_coordinates(declaration), effects=observation['effects'])


def freeze(home, declaration, locked):
    state, config = task.machine(home)
    root = Path((state.get('user') or {}).get('root', str(Path.home())))
    policy = selection.read_policy(home)[0]
    evaluated = pinned.effective_selection(home, declaration, locked, config, root=root, scope='user', policy_value=policy)
    selection.require_compatible(evaluated)
    supported = policy['enabled_agents']
    for binding in declaration['skills']:
        if targets(binding, declaration) != 'all':
            continue
        resolved = sorted({row['agent'] for row in evaluated['deployable'] if row['coordinate'] == r.coordinate(binding)})
        if not selection.applies(binding, selection.device()):
            resolved = supported
        if not resolved:
            c.fail('profile.targets_unrepresentable', 'An empty set of effective targets cannot be frozen as a portable binding.', 4,
                   skill=r.coordinate(binding))
        binding['agents'] = resolved
    if declaration['default_agents'] == 'all':
        if not supported:
            c.fail('profile.targets_unrepresentable', 'An empty default target set cannot be frozen.', 4)
        declaration['default_agents'] = supported
    for receipt in declaration.get('bundle_state', {}).get('bundles', {}).values():
        for binding in receipt['bindings']:
            if binding.get('agents') == 'all' and supported:
                binding['agents'] = supported
    return pair(declaration, locked['packages'])


def export(args, output, home):
    effective = getattr(args, 'effective', False)
    frozen = getattr(args, 'freeze_agents', False)
    declaration, locked = local_pair(home)
    if effective:
        state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
        for receipt in (state.get('user') or {}).get('profiles', {}).values():
            declaration, locked = merge((declaration, locked), (receipt['declaration'], receipt['lock']))
    declaration, locked = portable(declaration, locked)
    if frozen:
        declaration, locked = freeze(home, declaration, locked)
    destination = location(args.output)
    c.parents_safe(Path(destination.anchor), destination)
    if c.kind(destination) != 'missing' or c.kind(destination.parent) != 'directory':
        c.fail('profile.output', 'Export requires an absent output directory under an existing unlinked parent.', 4)
    action = dict(kind='profile.export', path=str(destination), status='planned')
    data = dict(output=str(destination), skills=len(locked['packages']), scope='user', network='none',
                effective=effective, frozen_agents=frozen, revision=c.digest(locked),
                default_agents=declaration['default_agents'],
                limitations=['All-agent targets resolve against the adapters on the importing machine.'] if not frozen else [])
    plan_hash = c.digest(dict(profile=locked, destination=str(destination), parent=c.identity(destination.parent), effective=effective, frozen=frozen))
    data['plan_hash'] = plan_hash
    output.update(data=data, actions=[action], would_change=True)
    if getattr(args, 'expect_plan_hash', plan_hash) != plan_hash:
        c.fail('plan.stale', 'The export changed; review it again.', 4)
    if output['dry_run']:
        return
    parent_identity = c.identity(destination.parent)
    with tempfile.TemporaryDirectory(prefix='.mask-profile-', dir=destination.parent) as temporary:
        stage = Path(temporary) / 'profile'
        stage.mkdir()
        for name, document in zip(PORTABLE_FILES, (declaration, locked)):
            raw = c.text_json(document)
            if len(raw.encode('utf-8')) > r.MODEL_BYTES:
                c.fail('profile.limit', 'Serialized profile controls exceed 4 MiB.', 4)
            (stage / name).write_text(raw, encoding='utf-8', newline='\n')
        (stage / 'README.md').write_text('Portable MASK personal profile.\n\n'
                                         + ('Subscriptions are flattened into explicit bindings.\n' if effective else 'Contains the local contribution.\n')
                                         + ('All-agent targets are frozen to the exporting adapter set.\n' if frozen else 'All-agent targets use the importing adapter set.\n'),
                                         encoding='utf-8', newline='\n')
        c.parents_safe(Path(destination.anchor), destination)
        if c.identity(destination.parent) != parent_identity:
            c.fail('plan.stale', 'The output directory parent changed during export.', 4)
        c.publish_directory(stage, destination)
    action['status'] = 'applied'
    output.update(changed=True, transaction='committed')


def prepare_exact(args, output, home, declaration, locked, config, root):
    """Find an exact cached view or acquire the approved commit before task review."""
    entries = r.approved(declaration, config)
    views = {}
    applicable = set(selection.applicable_coordinates(declaration))
    for row in locked['packages']:
        if r.coordinate(row) not in applicable:
            continue
        if c.kind(store.location(home, row['payload_digest'], row['id'])[0]) != 'missing':
            store.verify(home, row)
            continue
        entry = entries[row['source']]
        if not store.exact_cached(home, row, entry):
            if output['dry_run'] or getattr(args, 'offline', False) or getattr(args, 'expect_plan_hash', None):
                c.fail('artifact.unavailable', 'Exact profile content is unavailable locally. Run the task online to acquire the approved commit.', 4,
                       skill=r.coordinate(row), commit=row['commit'])
            effect = dict(skill=r.coordinate(row))
            observation = dict(root=str(root), effects=dict(acquisitions=[effect]))
            output['data'].setdefault('preparation', []).append(observation)
            try:
                sources.acquire_exact(home, row['source'], entry, row['commit'], config['git_timeout_seconds'], effect)
            finally:
                observation['effects']['network_attempted'] = effect.get('network_attempted', False)
        views[r.payload_key(row)] = r.verify_resolution(home, row['source'], entry, row)
    return views


def import_profile(args, output, home):
    if c.kind(home / 'pending.json') != 'missing':
        c.fail('recovery.required', 'Recover the pending operation first.', 8)
    state, config = task.machine(home)
    root = personal_root(args, state)
    if (state.get('user') or {}).get('mode') == 'dev-link':
        c.fail('dev_link.active', 'Return to pins before importing a personal profile.', 4)
    key = str(root)
    before = pinned.snapshot(home, [(root, 'user')])
    incoming, locked, revision = read_profile(args.location)
    replace = getattr(args, 'replace', False)
    previous = local_pair(home, missing=True)
    declaration, proposed_lock = (incoming, locked) if replace else merge(previous, (incoming, locked))
    views = prepare_exact(args, output, home, declaration, proposed_lock, config, root)
    def candidate():
        if read_profile(args.location)[2] != revision:
            c.fail('plan.stale', 'The portable profile changed during review.', 4)
        planned = fs.plan(config, state, [root], home=home, operation='install', user_root=root,
                          register=[key] if state.get('user') is None else [], proposals={key: declaration},
                          lock_proposals={key: proposed_lock}, payload_views=views, repair_roles=True, retire_files=False)
        planned['plan_hash'] = c.digest(dict(plan=planned['plan_hash'], profile=revision, replace=replace))
        return planned
    def prepare():
        effects = {}
        output['data'].setdefault('preparation', []).append(dict(root=key, effects=effects))
        store.ensure(home, declaration, proposed_lock, config, coordinates=selection.applicable_coordinates(declaration), effects=effects)
    lifecycle.execute(args, output, home, config, [root], before, candidate, prepare,
                      details=dict(root=key, scope='user', profile_revision=revision, replace=replace))


def change_subscription(args, output, home):
    if not getattr(args, 'user', False):
        c.fail('invocation.invalid', 'Use --user to select personal subscription policy.', 2)
    if c.kind(home / 'pending.json') != 'missing':
        c.fail('recovery.required', 'Recover the pending operation first.', 8)
    state, config = task.machine(home)
    root = personal_root(args, state)
    record = state.get('user') or {}
    if record.get('mode') == 'dev-link':
        c.fail('dev_link.active', 'Return to pins before changing a subscription.', 4)
    profiles = copy.deepcopy(record.get('profiles', {}))
    before = pinned.snapshot(home, [(root, 'user')])
    declaration, locked = local_pair(home, missing=True)
    subscribing = args.command == 'profile.subscribe'
    views, revision = {}, None
    if subscribing:
        name = getattr(args, 'name', None) or location(args.location).name
        c.skill_id(name)
        incoming, exact, revision = read_profile(args.location)
        receipt = dict(revision=revision, declaration=incoming, lock=exact)
        if profiles.get(name) == receipt:
            output['data'] = dict(profile=name, profiles=freshness(profiles), network='none')
            return
        profiles[name] = receipt
        subscriptions(profiles)
        views = prepare_exact(args, output, home, incoming, exact, config, root)
    else:
        name = c.skill_id(args.name)
        if name not in profiles:
            output['data'] = dict(profile=name, profiles=freshness(profiles), network='none')
            return
        del profiles[name]
    if declaration is None:
        if record:
            c.fail('selection.missing', 'Restore the registered personal controls before changing subscriptions.', 4)
        declaration, locked = pair(task.fresh_declaration(config), [])
    key = str(root)
    def candidate():
        if subscribing and read_profile(args.location)[2] != revision:
            c.fail('plan.stale', 'The portable profile changed during review.', 4)
        return fs.plan(config, state, [root], home=home, operation=args.command, user_root=root,
                       register=[] if record else [key], proposals={key: declaration}, lock_proposals={key: locked},
                       profile_proposals={key: profiles}, payload_views=views, repair_roles=True, retire_files=False)
    def prepare():
        effects = output['data'].setdefault('preparation', [])
        prepare_layers(home, profiles, config, effects, root=root)
    lifecycle.execute(args, output, home, config, [root], before, candidate, prepare,
                      details=dict(root=key, scope='user', profile=name, profiles=freshness(profiles)))


def dispatch(args, output, home):
    if args.command == 'profile.inspect':
        declaration, locked, revision = read_profile(args.location)
        output['data'] = dict(selection=declaration, lock=locked, revision=revision, skills=len(locked['packages']), network='none')
    elif args.command == 'user.export':
        export(args, output, home)
    else:
        try:
            if args.command == 'user.import':
                import_profile(args, output, home)
            else:
                change_subscription(args, output, home)
        finally:
            pinned.merge_preparation(output, completed=sys.exc_info()[0] is None)
