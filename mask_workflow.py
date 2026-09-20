"""Declared workflow prerequisites and typed native-role artifacts (RFC-MASK-0019).

A package may ship an optional passive ``mask-workflow.json`` beside SKILL.md
naming bounded consumer inputs and the native roles a selected agent needs.
Nothing here executes package code: static role assets are exact bytes verified
against the descriptor, consumer-checked-in roles are accepted through a portable
lock, and every deployment goes through the ordinary planned/journaled engine in
``mask_fs``. Modified, unknown, tracked or foreign files are observed and
preserved, never adopted or overwritten. Filesystem readiness is not host loading.
"""
from __future__ import annotations

import hashlib
import re
import tomllib
from pathlib import Path

import mask_core as c
import mask_adapters as adapters
import mask_packages as packages

DESCRIPTOR = 'mask-workflow.json'
DESCRIPTOR_BYTES = 1024 * 1024
ASSET_BYTES = 1024 * 1024
LIMITS = dict(inputs=32, native_roles=64, setup=8, package_inputs=128, parameters=32)
LOCK_NAME = 'native-roles.lock.json'
HEX_RE = re.compile(r'[a-f0-9]{64}')
# Supported passive native fields per adapter; anything else is refused rather than deployed blind.
CODEX_FIELDS = {'name', 'description', 'model', 'model_reasoning_effort', 'sandbox_mode', 'developer_instructions'}
CODEX_TABLES = {'agents': {'enabled'}}
CLAUDE_FIELDS = {'name', 'description', 'model', 'effort', 'maxTurns', 'permissionMode', 'tools', 'disallowedTools', 'color'}
ROUTE_FIELDS = {'codex': ('model', 'model_reasoning_effort'), 'claude': ('model', 'effort')}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def relative_path(value, family='workflow'):
    if not isinstance(value, str) or not 1 <= len(value.encode('utf-8', 'surrogateescape')) <= 1024:
        c.fail(family + '.invalid', 'Descriptor paths require bounded relative names.', 4)
    parts = value.split('/')
    if value.startswith('/') or '\\' in value or any(ord(ch) < 32 for ch in value) or any(part in ('', '.', '..') for part in parts):
        c.fail(family + '.invalid', 'Descriptor paths must be portable, contained and relative.', 4, path=value)
    return parts


def identifier(value, what):
    if not isinstance(value, str) or not 1 <= len(value) <= 64 or not c.ID_RE.fullmatch(value):
        c.fail('workflow.invalid', f'Invalid workflow {what} identifier.', 4)
    return value


def lock_relative(skill):
    """Canonical lock location: regenerable machine-local state beside the skill's other generated files."""
    return f'.mask/generated/{skill}/{LOCK_NAME}'


def legacy_lock_relative(skill):
    """Retired location beside the committed consumer inputs; still read so an upgrade keeps vouching."""
    return f'.mask/skill-config/{skill}/{LOCK_NAME}'


def paths(skill='{skill}'):
    """Consumer-relative public locations; the placeholder form is advertised by capabilities."""
    return dict(native_role_lock=lock_relative(skill), retired_native_role_locks=[legacy_lock_relative(skill)])


def retired_path(value, skill):
    parts = relative_path(value)
    try:
        packages.portable_path(value)
    except c.MaskError:
        c.fail('workflow.invalid', 'Retired paths must use portable file names.', 4, path=value)
    if len(parts) < 4 or parts[:3] not in (['.mask', 'generated', skill], ['.mask', 'skill-config', skill]) or value == lock_relative(skill):
        c.fail('workflow.invalid', 'Retired paths must be inside this skill\'s MASK configuration/generated directory, excluding its current lock.', 4, path=value)
    return value


class PackageView:
    """Read-only access to exact package bytes: a materialized directory or a validated in-memory payload."""

    def __init__(self, root=None, payload=None, files=None):
        self.root = Path(root) if root is not None else None
        self.files = {item.path: item.data for item in payload.files} if payload is not None else dict(files) if files is not None else None

    def read(self, relative, skill):
        if self.files is not None:
            return self.files.get(relative)
        path = self.root / relative
        c.parents_safe(self.root, path)
        observed = c.kind(path)
        if observed == 'missing':
            return None
        if observed != 'file':
            c.fail('workflow.invalid', 'Package entry must be a regular file.', 4, skill=skill, path=relative)
        return path.read_bytes()


def descriptor(view, skill, scope='project'):
    """Parse and validate the passive descriptor, or return None when the package declares nothing."""
    if not isinstance(view, PackageView):
        view = PackageView(root=view)
    data = view.read(DESCRIPTOR, skill)
    if data is None:
        return None
    if len(data) > DESCRIPTOR_BYTES:
        c.fail('workflow.invalid', 'The workflow descriptor exceeds its size bound.', 4, skill=skill)
    try:
        value = c.parse_json(data.decode('utf-8'), 'workflow')
    except UnicodeError:
        c.fail('workflow.invalid', 'The workflow descriptor must be UTF-8 JSON.', 4, skill=skill)
    if scope not in ('project', 'user'):
        c.fail('workflow.invalid', 'Unknown workflow consumer scope.', 4)
    c.fields(value, ('schema_version', 'inputs', 'native_roles'), ('setup', 'retired_paths', 'compatible_locks', 'scopes', 'profiles'), family='workflow')
    scopes = value.get('scopes', {})
    if not isinstance(scopes, dict) or set(scopes) - {'user'}:
        c.fail('workflow.invalid', 'Workflow scopes may contain only a complete user contract.', 4)
    base = {key: item for key, item in value.items() if key != 'scopes'}
    project = parse_contract(base, view, skill, sha256(data))
    personal = None
    if 'user' in scopes:
        c.fields(scopes['user'], ('inputs', 'native_roles'), ('setup', 'retired_paths', 'compatible_locks', 'profiles'), family='workflow')
        # A project lock cannot vouch for a different personal contract with fewer inputs.
        personal = parse_contract(dict(scopes['user'], schema_version=1), view, skill, sha256(b'user\0' + data))
    return personal if scope == 'user' and personal is not None else project


def parse_contract(value, view, skill, digest):
    """Validate one complete scope contract; inactive scope declarations are validated too."""
    inputs, ids, paths = [], set(), set()
    if not isinstance(value['inputs'], list) or len(value['inputs']) > LIMITS['inputs']:
        c.fail('workflow.invalid', 'Descriptor inputs must be a bounded list.', 4)
    for entry in value['inputs']:
        c.fields(entry, ('id', 'path', 'kind', 'required'), family='workflow')
        identifier(entry['id'], 'input')
        relative_path(entry['path'])
        if entry['kind'] not in ('json', 'text') or type(entry['required']) is not bool or entry['id'] in ids or entry['path'] in paths:
            c.fail('workflow.invalid', 'Descriptor inputs need unique ids/paths, a json/text kind and a boolean requirement.', 4)
        ids.add(entry['id'])
        paths.add(entry['path'])
        inputs.append(dict(entry))
    setup = {}
    if not isinstance(value.get('setup', []), list) or len(value.get('setup', [])) > LIMITS['setup']:
        c.fail('workflow.invalid', 'Descriptor setup actions must be a bounded list.', 4)
    for action in value.get('setup', []):
        c.fields(action, ('id', 'entrypoint', 'inputs', 'package_inputs', 'parameters', 'timeout_seconds', 'effects'), family='workflow')
        identifier(action['id'], 'setup')
        if action['id'] in setup:
            c.fail('workflow.invalid', 'Duplicate setup action id.', 4)
        packages.passive_path(packages.portable_path(action['entrypoint']))
        if not isinstance(action['inputs'], list) or len(set(action['inputs'])) != len(action['inputs']) or len(action['inputs']) > LIMITS['inputs'] or any(name not in ids for name in action['inputs']):
            c.fail('workflow.invalid', 'Setup inputs must reference declared consumer inputs once each.', 4)
        if not isinstance(action['package_inputs'], list) or not 1 <= len(action['package_inputs']) <= LIMITS['package_inputs'] or len(set(action['package_inputs'])) != len(action['package_inputs']):
            c.fail('workflow.invalid', 'Setup package inputs must be a unique bounded list.', 4)
        for item in action['package_inputs']:
            packages.passive_path(packages.portable_path(item))
        if not isinstance(action['parameters'], dict) or len(action['parameters']) > LIMITS['parameters'] or any(not isinstance(key, str) or type(item) not in (str, bool, int, type(None)) for key, item in action['parameters'].items()):
            c.fail('workflow.invalid', 'Setup parameters must be a small scalar map.', 4)
        if type(action['timeout_seconds']) is not int or not 1 <= action['timeout_seconds'] <= 120 or action['effects'] != 'staged-native-roles':
            c.fail('workflow.invalid', 'Setup actions need a 1-120 second timeout and staged-native-roles effects.', 4)
        setup[action['id']] = dict(action)
    roles = {}
    if not isinstance(value['native_roles'], list) or not 1 <= len(value['native_roles']) <= LIMITS['native_roles']:
        c.fail('workflow.invalid', 'Descriptor native roles must be a nonempty bounded list.', 4)
    for role in value['native_roles']:
        c.fields(role, ('agent', 'name'), ('asset', 'setup'), family='workflow')
        if role['agent'] not in adapters.BY_ID:
            c.fail('workflow.invalid', 'Native roles require a supported agent.', 4, agent=role['agent'])
        identifier(role['name'], 'role')
        key = (role['agent'], role['name'])
        if key in roles or ('asset' in role) == ('setup' in role):
            c.fail('workflow.invalid', 'Each native role needs exactly one producer and a unique agent/name.', 4, agent=role['agent'], name=role['name'])
        if 'asset' in role:
            c.fields(role['asset'], ('path', 'sha256'), family='workflow')
            packages.passive_path(packages.portable_path(role['asset']['path']))
            if not isinstance(role['asset']['sha256'], str) or not HEX_RE.fullmatch(role['asset']['sha256']):
                c.fail('workflow.invalid', 'Role assets need a lowercase hex SHA-256.', 4)
        elif role['setup'] not in setup:
            c.fail('workflow.invalid', 'Native role references an undeclared setup action.', 4, name=role['name'])
        roles[key] = dict(role)
    retired = value.get('retired_paths', [])
    if not isinstance(retired, list) or len(retired) > 32 or any(not isinstance(item, str) for item in retired) or len(set(retired)) != len(retired):
        c.fail('workflow.invalid', 'Retired paths must be a unique bounded list.', 4)
    for path in retired:
        retired_path(path, skill)
        if path in paths or any(path.startswith(item + '/') or item.startswith(path + '/') for item in paths):
            c.fail('workflow.invalid', 'An active input cannot be retired.', 4, path=path)
    compatible = value.get('compatible_locks', [])
    if not isinstance(compatible, list) or len(compatible) > 32:
        c.fail('workflow.invalid', 'Compatible locks must be a bounded list.', 4)
    for entry in compatible:
        c.fields(entry, ('contract_sha256', 'role_inputs_sha256'), family='workflow')
        if any(not isinstance(item, str) or not HEX_RE.fullmatch(item) for item in entry.values()):
            c.fail('workflow.invalid', 'Compatible locks require exact lowercase SHA-256 pairs.', 4)
    profiles = value.get('profiles', {})
    if not isinstance(profiles, dict) or len(profiles) > 32:
        c.fail('workflow.invalid', 'Profiles must be a bounded map of named role subsets.', 4)
    known = {agent + '/' + name for agent, name in roles}
    for name, profile in profiles.items():
        identifier(name, 'profile')
        c.fields(profile, ('native_roles',), family='workflow')
        selected = profile['native_roles']
        if (not isinstance(selected, list) or any(not isinstance(item, str) for item in selected)
                or len(selected) > LIMITS['native_roles'] or len(set(selected)) != len(selected)
                or not set(selected) <= known):
            c.fail('workflow.invalid', 'A profile must select declared agent/name roles once each; an empty list is allowed.', 4)
    return dict(skill=skill, view=view, digest=digest, inputs=inputs, roles=roles, setup=setup, profiles=profiles,
                retired_paths=retired, compatible_locks=compatible)


def asset(desc, role):
    """Exact static role bytes: a contained regular file whose hash and native fields are verified."""
    data = desc['view'].read(role['asset']['path'], desc['skill'])
    if data is None:
        c.fail('workflow.invalid', 'Role asset is missing or is not a regular file.', 4, skill=desc['skill'], path=role['asset']['path'])
    if len(data) > ASSET_BYTES or sha256(data) != role['asset']['sha256']:
        c.fail('workflow.invalid', 'Role asset bytes do not match the declared fingerprint.', 4, skill=desc['skill'], path=role['asset']['path'])
    native(role['agent'], role['name'], data, desc['skill'])
    return data


def native(agent, name, data, skill=None):
    """Passive parse of supported native fields; returns the configured route facts."""
    def refuse(message, **details):
        c.fail('workflow.role_invalid', message, 4, agent=agent, name=name, **({'skill': skill} if skill else {}), **details)
    try:
        text = data.decode('utf-8')
    except UnicodeError:
        refuse('Native role content must be UTF-8 text.')
    values = {}
    if agent == 'codex':
        try:
            parsed = tomllib.loads(text)
        except (tomllib.TOMLDecodeError, ValueError):
            refuse('Native role content is not valid TOML.')
        for key, value in parsed.items():
            if isinstance(value, dict):
                if key not in CODEX_TABLES or set(value) - CODEX_TABLES[key] or any(type(item) not in (str, bool, int) for item in value.values()):
                    refuse('Unsupported native role table.', field=key)
            elif key not in CODEX_FIELDS or type(value) not in (str, bool, int):
                refuse('Unsupported native role field.', field=key)
            else:
                values[key] = value
    elif agent == 'claude':
        lines = text.splitlines()
        if not lines or lines[0] != '---' or '---' not in lines[1:]:
            refuse('Native role content needs Markdown frontmatter.')
        for line in lines[1:lines.index('---', 1)]:
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            match = re.fullmatch(r'([A-Za-z][A-Za-z0-9_-]*):[ \t]*(.*)', line)
            if match is None:
                refuse('Native role frontmatter requires single-line key: value fields.')
            key, value = match.groups()
            if key not in CLAUDE_FIELDS or key in values:
                refuse('Unsupported or duplicate native role field.', field=key)
            value = value.strip()
            if not value or value[0] in '|>!&*[{':
                refuse('Native role frontmatter values must be single-line scalars.', field=key)
            if len(value) >= 2 and value[0] == value[-1] and value[0] in '"\'':
                value = value[1:-1]  # a plainly quoted scalar reports its content, not its quotes
            values[key] = value
    else:
        refuse('No built-in native role adapter for this agent.')
    if 'name' in values and values['name'] != name:
        refuse('Native role name differs from its declared role.', declared=str(values['name']))
    return {field: str(values[field]) for field in ROUTE_FIELDS[agent] if field in values}


def observe_inputs(root, desc):
    rows = []
    for entry in desc['inputs']:
        row = dict(id=entry['id'], path=entry['path'], kind=entry['kind'], required=entry['required'], state='missing', sha256=None)
        path = Path(root) / entry['path']
        c.parents_safe(Path(root), path)
        observed = c.kind(path)
        if observed == 'file':
            data = path.read_bytes()
            row['sha256'] = sha256(data)
            row['state'] = 'ok'
            try:
                text = data.decode('utf-8')
                if entry['kind'] == 'json':
                    c.parse_json(text, 'workflow')
            except (UnicodeError, c.MaskError):
                row['state'] = 'invalid'
        elif observed != 'missing':
            row['state'] = 'invalid'
        if row['state'] != 'ok' and not entry['required']:
            row['state'] = 'absent' if row['state'] == 'missing' else row['state']
        rows.append(row)
    return rows


def parse_lock(value):
    """Validate the portable lock shape (``mask.native-role-lock.v1``); optional fields carry setup provenance."""
    c.fields(value, ('schema_version', 'contract_sha256', 'inputs', 'roles'), ('schema', 'coordinate', 'action', 'role_inputs_sha256', 'parameters_sha256', 'input_paths'), family='workflow')
    if not isinstance(value['inputs'], dict) or not isinstance(value['roles'], list) or any(item is not None and (not isinstance(item, str) or not HEX_RE.fullmatch(item)) for item in value['inputs'].values()):
        c.fail('workflow.invalid', 'Invalid lock shape.', 4)
    for key in ('schema', 'coordinate', 'action', 'role_inputs_sha256', 'parameters_sha256'):
        if key in value and (not isinstance(value[key], str) or key.endswith('sha256') and not HEX_RE.fullmatch(value[key])):
            c.fail('workflow.invalid', 'Invalid lock provenance field.', 4, field=key)
    if 'input_paths' in value and (not isinstance(value['input_paths'], dict) or any(not isinstance(item, str) for item in value['input_paths'].values())):
        c.fail('workflow.invalid', 'Invalid lock input paths.', 4)
    rows = {}
    for row in value['roles']:
        c.fields(row, ('agent', 'name', 'sha256'), family='workflow')
        if row['agent'] not in adapters.BY_ID or not isinstance(row['sha256'], str) or not HEX_RE.fullmatch(row['sha256']):
            c.fail('workflow.invalid', 'Invalid lock role row.', 4)
        rows[(row['agent'], identifier(row['name'], 'role'))] = row['sha256']
    return dict(contract=value['contract_sha256'], inputs=value['inputs'], roles=rows, role_inputs=value.get('role_inputs_sha256'))


def read_lock(root, desc):
    """The portable lock that vouches for generated roles, or a reason it cannot, with the location it came from.

    The retired location is read only when the canonical one is absent, so a consumer that
    committed a lock before the move keeps vouching until it moves or drops the file.
    """
    root = Path(root)
    for relative in (lock_relative(desc['skill']), legacy_lock_relative(desc['skill'])):
        path = root / relative
        c.parents_safe(root, path)
        if c.kind(path) == 'missing':
            continue
        try:
            return parse_lock(c.read_json(path, 'workflow')), 'read', relative
        except c.MaskError:
            return None, 'invalid', relative
    return None, 'missing', None


def role_inputs(desc):
    """Digest of every setup action's declared package inputs; a change invalidates a prepared lock."""
    return c.digest({name: {path: c.digest(desc['view'].read(path, desc['skill']) or b'') for path in action['package_inputs']}
                     for name, action in sorted(desc['setup'].items())}).removeprefix('sha256:')


def lock_coherent(lock, desc, inputs):
    if lock is None:
        return False
    current = lock['contract'] == desc['digest'] and lock['role_inputs'] in (None, role_inputs(desc))
    compatible = dict(contract_sha256=lock['contract'], role_inputs_sha256=lock['role_inputs']) in desc.get('compatible_locks', [])
    if not (current or compatible):
        return False
    return all(lock['inputs'].get(row['id']) == row['sha256'] for row in inputs if row['required'] or row['state'] == 'ok')


def requirements(root, scope, record, bindings, targets, *, coordinates=None, staged=None, repair=False, profiles=None):
    """Compute declared roles for the selected bindings and observe every destination without changing it.

    ``bindings`` maps skill -> set of selected agents; ``targets`` maps skill -> PackageView
    (None when the exact package bytes are not available locally yet); ``coordinates`` maps
    skill -> SOURCE/ID; ``staged`` maps (skill, agent, name) -> validated setup output bytes
    that are published like assets (``mask_setup``).
    Returns per-skill readiness rows, journal-ready writes and the next ownership map.
    """
    root = Path(root)
    profiles = profiles or {}
    if set(profiles) - set(bindings):
        c.fail('workflow.profile_unknown', 'Profile selection names a skill not selected in this scope.', 4)
    coordinates, staged = coordinates or {}, staged or {}
    owned = dict((record or {}).get('native_roles', {}))
    contributions, reports = {}, []
    for skill in sorted(bindings):
        if targets[skill] is None:
            # Unavailable content is never "not declared": readiness stays unknown until the payload exists.
            reports.append(dict(skill=skill, workflow='unexamined', contract=None, inputs=[], roles=[], complete=False, detail='package content is not available locally; readiness was not examined'))
            continue
        desc = descriptor(targets[skill], skill, scope)
        if desc is None:
            if skill in profiles:
                c.fail('workflow.profile_unknown', 'Selected skill declares no workflow profiles.', 4, skill=skill)
            reports.append(dict(skill=skill, workflow='not_declared', contract=None, inputs=[], roles=[], complete=True))
            continue
        inputs = observe_inputs(root, desc)
        selected_profile = profiles.get(skill)
        if selected_profile is not None and selected_profile not in desc['profiles']:
            c.fail('workflow.profile_unknown', 'Unknown requirement profile for this scope.', 4, skill=skill, profile=selected_profile)
        selected_roles = set(desc['profiles'][selected_profile]['native_roles']) if selected_profile is not None else None
        lock, lock_state, lock_path = read_lock(root, desc)
        coherent = lock_coherent(lock, desc, inputs)
        report = dict(skill=skill, workflow='declared', contract=dict(descriptor=DESCRIPTOR, sha256=desc['digest'], lock=lock_state if not coherent else 'coherent', lock_path=lock_path),
                      package=dict(coordinate=coordinates.get(skill), root=str(desc['view'].root) if desc['view'].root is not None else None), inputs=inputs, roles=[], complete=True,
                      retired_paths=sorted(set(desc['retired_paths'] + ([legacy_lock_relative(skill)] if desc['setup'] else []))))
        if selected_profile is not None:
            report['selected_profile'] = selected_profile
        if any(row['state'] in ('missing', 'invalid') for row in inputs):
            report['complete'] = False
        for (agent, name), role in sorted(desc['roles'].items()):
            if selected_roles is not None and agent + '/' + name not in selected_roles:
                continue
            row = dict(skill=skill, agent=agent, name=name, producer='asset' if 'asset' in role else 'setup', path=None, state='not_applicable', ownership=None, route={}, host_load='not_verified')
            if agent in bindings[skill]:
                row['path'] = adapters.role_relative(agent, scope, name)
                if 'asset' in role:
                    data = asset(desc, role)
                    row['route'] = native(agent, name, data, skill)
                    row['expected_sha256'] = sha256(data)
                    contributions.setdefault(row['path'], []).append((skill, data, row))
                else:
                    data = staged.get((skill, agent, name))
                    row.update(setup=role['setup'], expected_sha256=lock['roles'].get((agent, name)) if coherent else None)
                    if data is not None:
                        row['route'] = native(agent, name, data, skill)
                        row['expected_sha256'] = sha256(data)
                    contributions.setdefault(row['path'], []).append((skill, data, row))
            report['roles'].append(row)
        reports.append(report)
    writes, next_owned, released = [], {}, []
    for relative, rows in sorted(contributions.items()):
        leaf = root / relative
        c.parents_safe(root, leaf)
        observed = c.kind(leaf)
        data = leaf.read_bytes() if observed == 'file' else None
        actual = sha256(data) if data is not None else None
        expectations = {row['expected_sha256'] for _, _, row in rows}
        holder = owned.get(relative)
        for skill, content, row in rows:
            row['observed_sha256'] = actual
            expected = row['expected_sha256']
            if observed not in ('missing', 'file'):
                row.update(state='collision', detail='a link or special entry occupies the destination; it is preserved')
            elif len(expectations) > 1:
                row.update(state='collision', detail='another selected skill requires different content at this destination; both producers are reported')
            elif expected is None:
                row.update(state='setup_required', detail='no coherent checked-in lock vouches for this generated role; approved setup can produce it')
                if actual is not None:
                    row['ownership'] = 'repository-owned' if holder is None else 'package-managed'
                    if holder is None:
                        # Setup already refuses to overwrite this file, so naming the lock alone would loop the operator.
                        row['detail'] = 'an unmanaged file occupies this destination; preserved. Restore a matching native-role lock or review the file before setup; rerunning ensure cannot replace it'
            elif actual == expected:
                row.update(state='ok', ownership='package-managed' if holder and holder['sha256'] == actual else 'repository-owned')
                if content is None:
                    # A lock-vouched generated role: its bytes were validated when published, so the same passive parse
                    # reports the configured route instead of an empty one.
                    row['route'] = native(row['agent'], row['name'], data, skill)
            elif content is None and actual is None:
                row.update(state='setup_required', detail='the checked-in lock names this generated role but no file exists; approved setup can produce it')
            elif content is None:
                row.update(state='modified', detail='content differs from the checked-in lock; it is preserved')
            elif actual is None:
                row.update(state='missing', action='create')
            elif holder and holder['sha256'] == actual:
                row.update(state='stale', action='update', ownership='package-managed')
            elif repair:
                row.update(state='stale', action='update', detail='will back up and replace this role file after task review')
            else:
                row.update(state='modified', ownership='package-managed' if holder else None, detail='content differs from the package asset and is not an unchanged managed output; it is preserved')
        first = rows[0][2]
        if first['state'] in ('missing', 'stale'):
            next_owned[relative] = dict(skill=first['skill'], agent=first['agent'], name=first['name'], sha256=first['expected_sha256'])
            writes.append(dict(root=str(root), relative=relative, skill=first['skill'], agent=first['agent'], name=first['name'],
                               before=data.decode('utf-8') if data is not None else None, after=rows[0][1].decode('utf-8')))
            if repair and data is not None:
                writes[-1]['repair'] = True
        elif holder is not None and holder['sha256'] == actual:
            next_owned[relative] = holder  # An unchanged managed output keeps its record, whatever the package now wants.
        elif holder is not None and first['state'] == 'modified':
            next_owned[relative] = holder  # An edited managed output is preserved and stays visibly managed-but-modified.
        elif holder is not None:
            released.append(dict(path=str(leaf), skill=holder['skill'], agent=holder['agent'], name=holder['name'],
                                 reason='deleted outside MASK' if actual is None else 'replaced outside MASK'))
    for relative, holder in sorted(owned.items()):
        if relative in contributions:
            continue
        if holder['skill'] in profiles:
            # A scoped observation never retires outputs belonging to another recipe.
            next_owned[relative] = holder
            continue
        leaf = root / relative
        c.parents_safe(root, leaf)
        data = leaf.read_bytes() if c.kind(leaf) == 'file' else None
        if data is not None and sha256(data) == holder['sha256']:
            writes.append(dict(root=str(root), relative=relative, skill=holder['skill'], agent=holder['agent'], name=holder['name'], before=data.decode('utf-8'), after=None))
        else:
            released.append(dict(path=str(leaf), skill=holder['skill'], agent=holder['agent'], name=holder['name'],
                                 reason='deleted before retirement' if data is None else 'changed before retirement'))
    for report in reports:
        if any(row['state'] not in ('ok', 'not_applicable', 'missing', 'stale') for row in report['roles']):
            report['complete'] = False
    return dict(reports=reports, writes=writes, owned=next_owned, released=released)


def validate_record_roles(value, scope):
    if not isinstance(value, dict):
        c.fail('state.invalid', 'Invalid native role ownership map.')
    for relative, entry in value.items():
        c.fields(entry, ('skill', 'agent', 'name', 'sha256'), family='state')
        c.skill_id(entry['skill'])
        if entry['agent'] not in adapters.BY_ID or not isinstance(entry['name'], str) or not c.ID_RE.fullmatch(entry['name']) or relative != adapters.role_relative(entry['agent'], scope, entry['name']) or not isinstance(entry['sha256'], str) or not HEX_RE.fullmatch(entry['sha256']):
            c.fail('state.invalid', 'Unsafe native role ownership record.')


def validate_pending_roles(pending, before, after):
    """Typed native-role journal entries must agree with both ownership sides."""
    seen = set()
    for entry in pending['native_roles']:
        c.fields(entry, ('root', 'relative', 'skill', 'agent', 'name', 'before', 'after'), ('repair',), family='recovery')
        if 'repair' in entry and (entry['repair'] is not True or pending['operation'] not in ('ensure', 'upgrade', 'install', 'remove') or entry['before'] is None or entry['after'] is None):
            c.fail('recovery.conflict', 'Unsafe repair transition.', 8)
        if entry['root'] not in pending['selected'] or entry['agent'] not in adapters.BY_ID or not isinstance(entry['name'], str) or not c.ID_RE.fullmatch(entry['name']):
            c.fail('recovery.conflict', 'Unsafe pending native role entry.', 8)
        c.skill_id(entry['skill'])
        selected_state = before if entry['root'] in c.consumer_records(before) else after
        if entry['relative'] != adapters.role_relative(entry['agent'], c.consumer_scope(selected_state, entry['root']), entry['name']):
            c.fail('recovery.conflict', 'Unsafe pending native role path.', 8)
        if (entry['root'], entry['relative']) in seen:
            c.fail('recovery.conflict', 'Duplicate pending native role transition.', 8)
        seen.add((entry['root'], entry['relative']))
        for side, state in (('before', before), ('after', after)):
            text = entry[side]
            holder = c.consumer_records(state).get(entry['root'], {}).get('native_roles', {}).get(entry['relative'])
            if text is None:
                if side == 'after' and holder is not None:
                    c.fail('recovery.conflict', 'Pending native role removal disagrees with ownership.', 8)
                continue
            if not isinstance(text, str) or len(text.encode('utf-8', 'surrogateescape')) > ASSET_BYTES:
                c.fail('recovery.conflict', 'Pending native role bytes exceed the supported text bounds.', 8)
            if side == 'before' and entry.get('repair'):
                continue  # Explicit repair preserves these observed bytes in a durable backup before replacing them.
            if holder is None or holder['sha256'] != sha256(text.encode('utf-8')):
                c.fail('recovery.conflict', 'Pending native role bytes disagree with ownership state.', 8)
        if entry['after'] is not None:
            native(entry['agent'], entry['name'], entry['after'].encode('utf-8'))


def current_text(entry):
    root = Path(entry['root'])
    leaf = root / entry['relative']
    c.parents_safe(root, leaf)
    observed = c.kind(leaf)
    if observed == 'missing':
        return None
    if observed != 'file':
        c.fail('recovery.conflict', 'A pending native role destination is not a regular file.', 8, path=str(leaf))
    try:
        return leaf.read_bytes().decode('utf-8')
    except UnicodeError:
        c.fail('recovery.conflict', 'A pending native role destination was replaced.', 8, path=str(leaf))


def check_roles(pending):
    for entry in pending.get('native_roles', []):
        if current_text(entry) not in (entry['before'], entry['after']):
            c.fail('recovery.conflict', 'A pending native role file was edited.', 8, path=str(Path(entry['root']) / entry['relative']))


def set_role(entry, side):
    leaf = Path(entry['root']) / entry['relative']
    actual = current_text(entry)
    if actual not in (entry['before'], entry['after']):
        c.fail('recovery.conflict', 'Native role precondition changed immediately before effect.', 8, path=str(leaf))
    wanted = entry[side]
    if actual == wanted:
        return
    if wanted is None:
        leaf.unlink()
        return
    c.atomic_text(leaf, wanted, actual)


def role_directories(intent):
    directories = set()
    for entry in intent.get('native_roles', []):
        if entry['after'] is not None:
            leaf = Path(entry['root']) / entry['relative']
            for parent in (leaf.parent.parent, leaf.parent):
                if c.kind(parent) == 'missing' and parent != Path(entry['root']):
                    directories.add(str(parent))
    return directories


def allowed_directories(root, scope):
    result = set()
    for agent in adapters.BY_ID:
        relative = adapters.role_relative(agent, scope, 'x')
        leaf = Path(root) / relative
        result.update((str(leaf.parent.parent), str(leaf.parent)))
    result.discard(str(root))
    return result


def summarize(reports, *, deployable=True):
    """One flat list of role/input facts that keep readiness incomplete; ``deployable`` also lists what a run would deploy."""
    rows = []
    for report in reports:
        if report['workflow'] == 'unexamined':
            rows.append(f"{report['skill']}: unexamined ({report['detail']})")
        for row in report['inputs']:
            if row['state'] in ('missing', 'invalid'):
                rows.append(f"{report['skill']} input {row['id']} ({row['path']}): {row['state']}")
        for row in report['roles']:
            if row['state'] not in ('ok', 'not_applicable') and (deployable or row['state'] not in ('missing', 'stale')):
                rows.append(f"{report['skill']} {row['agent']}/{row['name']}: {row['state']}")
    return rows
