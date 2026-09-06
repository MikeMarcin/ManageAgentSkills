"""Closed portable selections and exact, cache-only resolution locks.

No operation in this module fetches, checks out, materializes or executes a package.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
import re

import mask_core as c
import mask_packages as p
import mask_sources as s
from mask_provenance import regular_bytes

MODEL_BYTES = 4 * 1024 * 1024
BINDINGS = 4096
METADATA_BYTES = 1024 * 1024
PLATFORMS = {'windows', 'macos', 'linux'}
ARCHITECTURES = {'x86_64', 'arm64', 'x86'}
SHA = re.compile(r'sha256:[0-9a-f]{64}')
OID = re.compile(r'(?:[0-9a-f]{40}|[0-9a-f]{64})')


def invalid(family, message):
    c.fail(family + '.invalid', message, 4)


def canonical(value, family='selection'):
    """Canonical UTF-8 bytes; callers validate closed schemas before hashing."""
    def walk(item, depth=0):
        if depth > 32:
            invalid(family, 'JSON nesting exceeds 32 levels.')
        if item is None or type(item) is bool:
            return
        if type(item) is int:
            if not 0 <= item <= 2 ** 53 - 1:
                invalid(family, 'Integers must be nonnegative JSON-safe integers.')
        elif isinstance(item, str):
            try:
                item.encode('utf-8')
            except UnicodeError:
                invalid(family, 'Invalid Unicode scalar value.')
        elif isinstance(item, list):
            for child in item:
                walk(child, depth + 1)
        elif isinstance(item, dict):
            for key, child in item.items():
                if not isinstance(key, str):
                    invalid(family, 'JSON object keys must be strings.')
                walk(key, depth + 1)
                walk(child, depth + 1)
        else:
            invalid(family, 'Floats and non-JSON values are unsupported.')
    walk(value)
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')


def parse(raw, family):
    try:
        size = len(raw.encode('utf-8')) if isinstance(raw, str) else len(raw)
    except UnicodeError:
        invalid(family, 'Invalid Unicode scalar value.')
    if size > MODEL_BYTES:
        c.fail(family + '.limit', 'Declaration or lock exceeds 4 MiB.', 4)
    try:
        value = c.parse_json(raw.decode('utf-8') if isinstance(raw, bytes) else raw, family)
    except (UnicodeError, RecursionError):
        invalid(family, 'Invalid or excessively nested UTF-8 JSON.')
    canonical(value, family)
    return value


def closed(value, required, optional=(), family='selection', versions=(1,)):
    c.fields(value, required, optional, family, versions=versions)


def strings(value, family, *, choices=None, empty=False, limit=64, length=500):
    if not isinstance(value, list) or len(value) > limit or not empty and not value:
        invalid(family, 'Expected a bounded nonempty string set.')
    if any(not isinstance(v, str) or not 1 <= len(v) <= length or any(ord(ch) < 32 for ch in v) for v in value):
        invalid(family, 'Invalid bounded string set entry.')
    if len(set(value)) != len(value) or choices is not None and set(value) - choices:
        invalid(family, 'Duplicate or unsupported set entry.')
    return sorted(value)


def agents(value):
    return 'all' if value == 'all' else strings(value, 'selection', choices=set(c.ADAPTERS))


def ref(value, family):
    s.selector(value)
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in value) or not value.startswith(('refs/heads/', 'refs/tags/')) or any(part.startswith('.') or part.endswith('.lock') or not part for part in value.split('/')):
        invalid(family, 'Portable refs must be fully qualified refs/heads/... or refs/tags/... names.')
    return value


def selector(value, family='selection'):
    if not isinstance(value, dict) or len(value) != 1 or not set(value) <= {'commit', 'ref'}:
        invalid(family, 'Select exactly one full commit or fully qualified ref.')
    if 'commit' in value:
        if not isinstance(value['commit'], str) or not OID.fullmatch(value['commit']):
            invalid(family, 'Commit selectors require a full lowercase SHA-1 or SHA-256 object ID.')
    else:
        ref(value['ref'], family)
    return dict(value)


def repository(value, family):
    if not isinstance(value, str) or not value.startswith(('https://', 'ssh://', 'file://')) or s.repository(value) != value:
        invalid(family, 'Repository identity must be a canonical credential-free URI; file URIs are machine-local only.')
    return value


def path(value):
    if value != '.':
        p.portable_path(value)
    return value


def selection(value):
    canonical(value)
    closed(value, ('schema_version', 'sources', 'skills'), ('default_agents',), versions=(2,))
    if not isinstance(value['sources'], dict) or len(value['sources']) > 256:
        invalid('selection', 'Expected at most 256 source bindings.')
    sources = {}
    for name, entry in value['sources'].items():
        c.skill_id(name)
        s.alias(name)
        closed(entry, ('repository',), ('ref', 'packages'))
        sources[name] = dict(repository=repository(entry['repository'], 'selection'), packages=path(entry.get('packages', 'skills')))
        if 'ref' in entry:
            sources[name]['ref'] = ref(entry['ref'], 'selection')
    if not isinstance(value['skills'], list) or len(value['skills']) > BINDINGS:
        invalid('selection', 'Expected at most 4096 package bindings.')
    defaults = agents(value.get('default_agents', 'all'))
    bindings, seen = [], set()
    for binding in value['skills']:
        closed(binding, ('source', 'id'), ('version', 'agents', 'when', 'introduced_by'))
        name, identifier = c.skill_id(binding['source']), c.skill_id(binding['id'])
        key = (name, identifier)
        if name not in sources or key in seen:
            invalid('selection', 'Unknown source or duplicate source/package binding.')
        seen.add(key)
        row = dict(source=name, id=identifier)
        if 'agents' in binding:
            row['agents'] = agents(binding['agents'])
        if 'version' in binding:
            row['version'] = selector(binding['version'])
        if 'when' in binding:
            when = binding['when']
            closed(when, (), ('platforms', 'architectures'))
            if not when:
                invalid('selection', 'An explicit when condition cannot be empty.')
            row['when'] = {field: strings(items, 'selection', choices=PLATFORMS if field == 'platforms' else ARCHITECTURES) for field, items in when.items()}
        if 'introduced_by' in binding:
            row['introduced_by'] = strings(binding['introduced_by'], 'selection')
        bindings.append(row)
    return dict(schema_version=2, sources=sources, default_agents=defaults, skills=sorted(bindings, key=coordinate))


def coordinate(row):
    return row['source'] + '/' + row['id']


def selection_digest(value):
    return c.digest(canonical(selection(value)))


def declared_selector(declaration, binding):
    return binding.get('version') or ({'ref': declaration['sources'][binding['source']]['ref']} if 'ref' in declaration['sources'][binding['source']] else None)


def lock(value, declaration=None, *, matching=True):
    canonical(value, 'lock')
    closed(value, ('schema_version', 'selection_digest', 'resolver', 'packages'), family='lock')
    if value['resolver'] != 'mask-lock-v1' or not isinstance(value['selection_digest'], str) or not SHA.fullmatch(value['selection_digest']):
        invalid('lock', 'Invalid lock resolver or selection digest.')
    if not isinstance(value['packages'], list) or len(value['packages']) > BINDINGS:
        invalid('lock', 'Expected at most 4096 resolved packages.')
    seen, rows = set(), []
    for entry in value['packages']:
        closed(entry, ('source', 'id', 'repository', 'path', 'commit', 'git_object_format', 'payload_digest', 'metadata_digest', 'selector'), ('provenance_digest',), 'lock')
        c.skill_id(entry['source'])
        c.skill_id(entry['id'])
        key = coordinate(entry)
        if key in seen:
            invalid('lock', 'Duplicate resolved binding.')
        seen.add(key)
        repository(entry['repository'], 'lock')
        path(entry['path'])
        selector({'commit': entry['commit']}, 'lock')
        if entry['git_object_format'] not in ('sha1', 'sha256') or len(entry['commit']) != {'sha1': 40, 'sha256': 64}[entry['git_object_format']]:
            invalid('lock', 'Object format and full commit length disagree.')
        chosen = selector(entry['selector'], 'lock')
        if 'commit' in chosen and chosen['commit'] != entry['commit']:
            invalid('lock', 'Exact commit selector cannot resolve to another commit.')
        for field in ('payload_digest', 'metadata_digest', 'provenance_digest'):
            if field in entry and (not isinstance(entry[field], str) or not SHA.fullmatch(entry[field])):
                invalid('lock', 'Invalid content digest.')
        rows.append(copy.deepcopy(entry))
    result = dict(value, packages=sorted(rows, key=coordinate))
    if declaration is not None:
        declaration = selection(declaration)
        expected = {coordinate(row): row for row in declaration['skills']}
        if matching and (seen != expected.keys() or value['selection_digest'] != selection_digest(declaration)):
            c.fail('lock.stale', 'Lock does not match the normalized selection; run mask lock explicitly.', 4)
        for row in rows:
            binding = expected.get(coordinate(row))
            if binding is None:
                if matching:
                    invalid('lock', 'Resolution is not selected.')
                continue
            chosen = declared_selector(declaration, binding)
            if row['repository'] != declaration['sources'][row['source']]['repository'] or chosen is not None and chosen != row['selector']:
                c.fail('lock.stale', 'Resolved identity or selector differs from the declaration; explicitly refresh the changed binding.', 4)
    return result


def metadata(raw):
    if raw is None:
        return None
    if len(raw) > METADATA_BYTES:
        c.fail('metadata.limit', 'Package metadata exceeds 1 MiB.', 4)
    value = parse(raw, 'metadata')
    closed(value, ('schema_version',), ('agents', 'platforms', 'architectures', 'requirements'), 'metadata')
    result = dict(schema_version=1)
    for field in ('agents', 'platforms', 'architectures'):
        if field in value:
            choices = PLATFORMS if field == 'platforms' else ARCHITECTURES if field == 'architectures' else None
            result[field] = 'generic' if value[field] == 'generic' else strings(value[field], 'metadata', choices=choices)
            if field == 'agents' and isinstance(result[field], list):
                for name in result[field]:
                    c.skill_id(name)
    if 'requirements' in value:
        result['requirements'] = strings(value['requirements'], 'metadata', empty=True)
    return result


def payload_digests(payload):
    files = {entry.path: entry.data for entry in payload.files}
    result = dict(payload_digest=payload.digest, metadata_digest=c.digest(canonical(metadata(files.get('mask-skill.json')), 'metadata')))
    if '.mask-provenance.json' in files:
        result['provenance_digest'] = c.digest(files['.mask-provenance.json'])
    return result


def approved(declaration, config):
    entries = {}
    for name, expected in declaration['sources'].items():
        entry = s.selected(config, name)
        if entry['repository'] != expected['repository'] or entry['packages'] != expected['packages']:
            c.fail('source.identity_mismatch', 'Selection repository or package layout does not match the machine approval.', 4, source=name)
        entries[name] = entry
    return entries


def cached(home, name, entry):
    root = s.cached(home, name, entry)
    if root is None:
        c.fail('lock.resolution_required', 'Approved source has no cache; explicitly fetch it before locking.', 4, source=name)
    return root


def verify_commit(root, row):
    observed = c.git(root, 'rev-parse', '--verify', row['commit'] + '^{commit}', optional=True)
    if observed != row['commit']:
        c.fail('lock.resolution_required', 'Exact locked commit is unavailable; fetch that commit explicitly without substituting another revision.', 4, commit=row['commit'])
    if c.git(root, 'rev-parse', '--show-object-format') != row['git_object_format']:
        invalid('lock', 'Cache object format differs from the lock.')


def frozen_payload(root, row):
    verify_commit(root, row)
    return p.validate(root, row['commit'], row['path'], row['id'])


def verify_resolution(home, name, entry, row):
    root = cached(home, name, entry)
    verify_commit(root, row)
    found = [item for item in s.discover(root, name, entry, row['commit'], identifier=row['id']) if item['id'] == row['id']]
    if len(found) != 1 or found[0]['path'] != row['path']:
        c.fail('lock.path_mismatch', 'Locked package path differs from the exact commit source index/layout.', 4)
    payload = p.validate(root, row['commit'], row['path'], row['id'])
    actual = payload_digests(payload)
    if actual != {key: row[key] for key in ('payload_digest', 'metadata_digest', 'provenance_digest') if key in row}:
        c.fail('lock.digest_mismatch', 'Exact cached payload, metadata or provenance differs from the lock.', 4, skill=coordinate(row))
    return payload


def machine_selector(root, entry):
    requested = entry['ref']
    if OID.fullmatch(requested):
        return {'commit': requested}
    refs = s.cached_refs(root, entry) or {}
    candidates = [name for name in refs if name == requested or name in ('refs/heads/' + requested, 'refs/tags/' + requested)]
    if len(candidates) != 1:
        c.fail('lock.resolution_required', 'Machine ref must resolve to one cached fully qualified branch or tag; declare an explicit ref.', 4)
    return {'ref': ref(candidates[0], 'lock')}


def resolve_binding(home, declaration, binding, entry):
    root = cached(home, binding['source'], entry)
    chosen = declared_selector(declaration, binding) or machine_selector(root, entry)
    commit = chosen.get('commit')
    if commit is None:
        refs = s.cached_refs(root, entry) or {}
        if chosen['ref'] not in refs:
            c.fail('lock.resolution_required', 'Selected ref has no cached advertisement; fetch explicitly first.', 4, ref=chosen['ref'])
        commit = refs[chosen['ref']]
    observed = c.git(root, 'rev-parse', '--verify', commit + '^{commit}', optional=True)
    if observed is None or 'commit' in chosen and observed != commit:
        c.fail('lock.resolution_required', 'Selected Git object cannot resolve to the required commit in the approved cache; explicitly inspect/fetch that selector first.', 4, object=commit, selector=chosen)
    commit = observed
    found = [item for item in s.discover(root, binding['source'], entry, commit, identifier=binding['id']) if item['id'] == binding['id']]
    if len(found) != 1:
        c.fail('skill.unknown', 'Selected package must have exactly one safe path at the chosen commit.', 4, skill=coordinate(binding))
    row = {key: found[0][key] for key in ('source', 'id', 'repository', 'path', 'commit')}
    row.update(selector=chosen, git_object_format=c.git(root, 'rev-parse', '--show-object-format'))
    row.update(payload_digests(frozen_payload(root, row)))
    return row


def resolve_candidate(declaration, config, home, previous=None, *, refresh=False, skills=(), allow_ref_rebind=False):
    declaration = selection(declaration)
    entries = approved(declaration, config)
    old = lock(previous) if previous is not None else None
    bindings = {coordinate(row): row for row in declaration['skills']}
    selected = set(skills)
    if len(selected) != len(skills) or selected - bindings.keys() or selected and not refresh or allow_ref_rebind and not refresh:
        c.fail('invocation.invalid', '--skill selects unique declared SOURCE/ID bindings and requires --refresh; --allow-ref-rebind also requires --refresh.', 2)
    previous_rows = {coordinate(row): row for row in old['packages']} if old else {}
    rows = []
    for key, binding in bindings.items():
        prior = previous_rows.get(key)
        entry = entries[binding['source']]
        update = refresh and (not selected or key in selected)
        if prior is not None and not update:
            chosen = declared_selector(declaration, binding)
            if prior['repository'] != entry['repository'] or chosen is not None and chosen != prior['selector']:
                c.fail('lock.stale', 'Changed binding requires an explicit selected --refresh.', 4, skill=key)
            verify_resolution(home, binding['source'], entry, prior)
            rows.append(prior)
            continue
        row = resolve_binding(home, declaration, binding, entry)
        if prior is not None and prior['repository'] == row['repository'] and prior['selector'] == row['selector'] and prior['commit'] != row['commit']:
            chosen = row['selector']
            root = cached(home, binding['source'], entry)
            rewritten = 'ref' in chosen and (chosen['ref'].startswith('refs/tags/') or c.git(root, 'merge-base', '--is-ancestor', prior['commit'], row['commit'], optional=True) is None)
            if rewritten and not allow_ref_rebind:
                c.fail('lock.ref_rebound', 'Cached tag moved or branch is not proven fast-forward; review and pass --allow-ref-rebind explicitly.', 4, skill=key, before=prior['commit'], after=row['commit'])
        rows.append(row)
    return lock(dict(schema_version=1, resolver='mask-lock-v1', selection_digest=selection_digest(declaration), packages=rows), declaration)


def read_model(pathname, family, *, missing=False):
    c.parents_safe(Path(pathname.anchor), pathname)
    if c.kind(pathname) == 'missing' and missing:
        return None, None
    if c.kind(pathname) == 'missing':
        c.fail(family + '.missing', 'Required ' + family + ' file is missing.', 4, path=str(pathname))
    if c.kind(pathname) != 'file':
        invalid(family, 'Control files must be regular unlinked files.')
    raw = regular_bytes(pathname, MODEL_BYTES)
    return parse(raw, family), raw


def lock_path(root, scope='project', home=None):
    return Path(home) / 'user.lock.json' if scope == 'user' else Path(root) / '.mask.lock.json'


def read_exact_lock(root, scope='project', home=None, config=None, *, verify=True):
    declaration = selection(read_model(c.declaration_path(root, scope, home), 'selection')[0])
    resolved = lock(read_model(lock_path(root, scope, home), 'lock')[0], declaration)
    if verify and config is None:
        if home is None:
            c.fail('config.missing', 'Verified lock reads require approved machine configuration and cache home.', 4)
        config = c.config(c.read_json(Path(home) / 'config.json'))
    if config is not None:
        entries = approved(declaration, config)
        if verify:
            for row in resolved['packages']:
                verify_resolution(home, row['source'], entries[row['source']], row)
    return declaration, resolved


def guard_legacy(root, scope='project', home=None):
    """Validate v2 lock before entering version-dispatched consumer operations."""
    value, _ = read_model(c.declaration_path(root, scope, home), 'manifest', missing=True)
    if isinstance(value, dict) and value.get('schema_version') == 2:
        declaration = selection(value)
        lock(read_model(lock_path(root, scope, home), 'lock')[0], declaration)


def dispatch(args, output, home):
    scope = 'user' if getattr(args, 'user', False) else 'project'
    root = home if scope == 'user' else c.project_root(getattr(args, 'project', None))
    declaration_path = c.declaration_path(root, scope, home)
    target = lock_path(root, scope, home)
    declaration_value, declaration_raw = read_model(declaration_path, 'selection')
    declaration = selection(declaration_value)
    original, before = read_model(target, 'lock', missing=True)
    config_raw = c.read_text(home / 'config.json')
    config = c.config(c.parse_json(config_raw))
    identities = dict(root=c.identity(root), home=c.identity(home))
    proposal = resolve_candidate(declaration, config, home, original, refresh=getattr(args, 'refresh', False), skills=getattr(args, 'skill', ()), allow_ref_rebind=getattr(args, 'allow_ref_rebind', False))
    serialized = c.text_json(proposal)
    if len(serialized.encode('utf-8')) > MODEL_BYTES:
        c.fail('lock.limit', 'Serialized lock exceeds the 4 MiB control-file limit.', 4)
    changed = original is None or lock(original) != proposal
    state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
    record = state.get('user') if scope == 'user' else state['projects'].get(str(root))
    if changed and record is not None and record.get('mode') == 'pinned':
        c.fail('lock.active', 'Use the journaled pinned update flow to change an active consumer lock.', 4)
    plan_hash = c.digest(dict(command='lock', declaration=c.digest(declaration_raw), before=c.digest(before) if before is not None else None, after=proposal, config=c.digest(config_raw.encode('utf-8')), path=str(target), identities=identities))
    output['data'] = dict(scope=scope, lock_path=str(target), lock=proposal, plan_hash=plan_hash, network='none', portable=all(not entry['repository'].startswith('file:') for entry in declaration['sources'].values()), targeting='not_evaluated', deployment='not_requested')
    output['would_change'] = changed
    if getattr(args, 'expect_plan_hash', plan_hash) != plan_hash:
        c.fail('plan.stale', 'Lock candidate or observed inputs changed since preview.', 4)
    if changed:
        output['actions'] = [dict(kind='lock.write', path=str(target), status='planned')]
        if not output['dry_run']:
            if c.identity(root) != identities['root'] or c.identity(home) != identities['home']:
                c.fail('plan.stale', 'Project or machine home identity changed before publication.', 4)
            if regular_bytes(declaration_path, MODEL_BYTES) != declaration_raw or c.read_text(home / 'config.json') != config_raw:
                c.fail('plan.stale', 'Selection or source approval changed before publication.', 4)
            c.atomic_text(target, serialized, before.decode('utf-8') if before is not None else None)
            output.update(changed=True, transaction='committed')


def guard_command(args, home):
    """Central guard for public legacy consumer operations, before side effects."""
    command = args.command
    scoped = command.startswith(('project.', 'user.', 'integration.')) or command in {'ensure', 'plan', 'apply', 'doctor', 'inventory', 'skill.where-used', 'link.adopt', 'update'}
    if not scoped or command in {'project.list', 'integration.revoke', 'integration.status'}:
        return
    state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
    roots = []
    if command.startswith('user.') or getattr(args, 'user', False):
        roots.append((home, 'user'))
    elif command in {'update', 'skill.where-used'} or getattr(args, 'all', False) or command in {'doctor', 'inventory'} and not getattr(args, 'project', None):
        roots.extend((Path(root), c.consumer_scope(state, root)) for root in c.consumer_records(state))
    else:
        requested = getattr(args, 'project', getattr(args, 'path', None))
        try:
            roots.append((c.project_root(requested), 'project'))
        except c.MaskError as error:
            if error.code not in {'project.not_found', 'manifest.missing'}:
                raise
        if command == 'ensure' and getattr(args, 'event', 'manual') == 'startup':
            roots.append((home, 'user'))
        if command == 'ensure' and getattr(args, 'event', '').startswith('post-'):
            roots.extend((Path(root), 'project') for root in state['projects'])
    for root, scope in roots:
        if root.is_dir():
            guard_legacy(root, scope, home)
            value = c.read_json(c.declaration_path(root, scope, home), 'manifest', default={})
            if value.get('schema_version') == 2 and command in {'update', 'project.set', 'project.require', 'project.unrequire', 'project.set-targets', 'user.set', 'user.require', 'user.unrequire', 'user.set-targets'}:
                c.fail('selection.command_unsupported', 'Legacy consumer mutation requires an explicit pinned-aware operation.', 4)
