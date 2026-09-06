"""Approved repository identities and catalog-only source bindings."""
from __future__ import annotations

import copy
import os
from pathlib import Path
import re
import time
import uuid
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from urllib.request import url2pathname

import mask_core as c

FETCH_BYTES = 256 * 1024 * 1024
CACHE_BYTES = 1024 * 1024 * 1024


def cache_bytes(root):
    if c.kind(root / 'objects') != 'directory':
        c.fail('source.cache_invalid', 'Cache object storage must be a real directory.', 4)
    total = 0
    for parent, directories, files in os.walk(root / 'objects', followlinks=False):
        for name in directories + files:
            path = Path(parent) / name
            if c.kind(path) not in ('directory', 'file', 'missing'):
                c.fail('source.cache_invalid', 'Cache object storage contains a link or special entry.', 4)
        for name in files:
            try:
                total += (Path(parent) / name).stat().st_size
            except FileNotFoundError:
                pass  # Git may rename its own temporary pack during the scan.
    return total


def alias(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}', value):
        c.fail('source.invalid', 'Source aliases use lowercase ASCII letters, digits and hyphens.')
    return value


def repository(value):
    """Normalize transport spelling without equating HTTPS and SSH authority."""
    if not isinstance(value, str) or not value or value.startswith('-') or any(ch in value for ch in '\0\r\n'):
        c.fail('source.identity_invalid', 'Expected a credential-free repository URI or absolute local path.')
    if Path(value).is_absolute():
        return Path(value).resolve().as_uri()
    if any(ch.isspace() for ch in value):
        c.fail('source.identity_invalid', 'Whitespace is unsupported in repository URLs.')
    # Only the conventional user@host:path form is accepted as scp syntax.
    if re.fullmatch(r'[A-Za-z0-9._-]+@[A-Za-z0-9.-]+:[^:]+', value):
        userhost, path = value.split(':', 1)
        if path.startswith(('~', '-')):
            c.fail('source.identity_invalid', 'Use an explicit SSH URI for tilde paths; option-leading scp paths are unsupported.')
        # Git scp paths are home-relative; URI /paths are absolute.
        value = 'ssh://' + userhost + (path if path.startswith('/') else '/~/' + path)
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        c.fail('source.identity_invalid', 'Invalid repository authority.')
    if parsed.scheme not in ('https', 'ssh', 'file') or parsed.query or parsed.fragment:
        c.fail('source.identity_invalid', 'Only HTTPS, SSH and explicit local file repositories are supported.')
    if parsed.password is not None or parsed.scheme != 'ssh' and parsed.username is not None:
        c.fail('source.identity_invalid', 'Repository URLs must not contain credentials.')
    path = unquote(parsed.path)
    if '%' in path or any(ord(ch) < 32 or ch == '\\' for ch in path) or any(part in ('.', '..') for part in path.split('/')):
        c.fail('source.identity_invalid', 'Unsafe repository path.')
    if parsed.scheme == 'file':
        if parsed.netloc not in ('', 'localhost') or port is not None:
            c.fail('source.identity_invalid', 'File repositories must be local.')
        local = Path(url2pathname(parsed.path))
        if not local.is_absolute():
            c.fail('source.identity_invalid', 'File repositories require an absolute path.')
        return local.resolve().as_uri()
    if not parsed.hostname or not re.fullmatch(r'[A-Za-z0-9.-]+', parsed.hostname):
        c.fail('source.identity_invalid', 'Unsupported repository hostname.')
    user = parsed.username
    if user is not None and not re.fullmatch(r'[A-Za-z0-9._-]+', user):
        c.fail('source.identity_invalid', 'Unsupported SSH username.')
    path = path.rstrip('/')
    if not path or not path.startswith('/') or '//' in path:
        c.fail('source.identity_invalid', 'Repository path must be unambiguous.')
    authority = (user + '@' if user else '') + parsed.hostname.lower()
    if port is not None and port != {'https': 443, 'ssh': 22}[parsed.scheme]:
        authority += ':' + str(port)
    return urlunsplit((parsed.scheme, authority, quote(path, safe='/@-._~'), '', ''))


def selector(value):
    if (not isinstance(value, str) or not 1 <= len(value) <= 256 or value.startswith(('-', '/'))
            or any(ch.isspace() or ch in ':\\~^?*[\0' for ch in value)
            or '..' in value or '@{' in value or value.endswith(('/', '.', '.lock'))):
        c.fail('source.ref_invalid', 'Expected an exact commit or safe Git ref.')
    return value


def package_path(value):
    if not isinstance(value, str) or len(value) > 1024 or '\\' in value or any(ch in value for ch in '\0\r\n'):
        c.fail('source.path_invalid', 'Expected a bounded repository-relative package path.')
    if value == '.':
        return value
    if any(part in ('', '.', '..') for part in value.split('/')) or ':' in value or value.startswith('-'):
        c.fail('source.path_invalid', 'Package paths cannot escape the repository.')
    return value


def validate_config(value):
    if not isinstance(value['sources'], dict) or not 1 <= len(value['sources']) <= 256:
        c.fail('config.invalid', 'Expected a bounded approved source catalog.')
    alias(value['legacy_source'])
    if value['legacy_source'] not in value['sources']:
        c.fail('config.invalid', 'The legacy source binding is missing.')
    for name, entry in value['sources'].items():
        alias(name)
        c.fields(entry, ('repository', 'transport', 'cache', 'ref', 'packages', 'authoring'), family='source')
        if repository(entry['repository']) != entry['repository'] or repository(entry['transport']) != entry['repository']:
            c.fail('source.identity_mismatch', 'Source transport does not match its approved identity.', 4)
        selector(entry['ref'])
        package_path(entry['packages'])
        if not isinstance(entry['cache'], str) or not Path(entry['cache']).is_absolute():
            c.fail('config.invalid', 'Source cache must be an absolute machine-local path.')
        if entry['authoring'] is not None and (not isinstance(entry['authoring'], str) or not Path(entry['authoring']).is_absolute()):
            c.fail('config.invalid', 'Authoring checkout must be an absolute machine-local path.')
    legacy = value['sources'][value['legacy_source']]
    if legacy['authoring'] != value['source']['root']:
        c.fail('config.invalid', 'Legacy source migration must preserve its authoring root.')


def binding(home, name, transport, ref='main', packages='skills', authoring=None):
    alias(name)
    identity = repository(transport)
    # Store only validated credential-free text; actual credentials stay with Git.
    transport = str(Path(transport).resolve()) if Path(transport).is_absolute() else transport
    return dict(repository=identity, transport=transport,
                cache=str(home / 'sources' / (name + '-' + c.digest(identity)[7:23] + '.git')),
                ref=selector(ref), packages=package_path(packages), authoring=authoring)


def selected(config, name):
    if config['schema_version'] != 2:
        c.fail('source.migration_required', 'Preview source migrate before using the multi-source catalog.', 4)
    alias(name)
    if name not in config['sources']:
        c.fail('source.unknown', 'Source alias is not approved.', 4, source=name)
    return config['sources'][name]


def approved_legacy(config):
    if config['schema_version'] == 2:
        return selected(config, config['legacy_source'])['repository']
    return None


def endpoint(root, transport, identity):
    expanded = c.git(root, 'ls-remote', '--get-url', transport)
    if repository(expanded) != identity:
        c.fail('source.identity_mismatch', 'Git rewrites the transport to an unapproved repository.', 4)


def network_options(root, transport):
    options = ['-c', 'http.followRedirects=false']
    if urlsplit(transport).scheme.lower() not in ('http', 'https'):
        return options
    # URL-scoped settings outrank generic command-line settings in Git.
    effective = c.git(root, *options, 'config', '--get-urlmatch', 'http.followRedirects', transport, optional=True)
    if effective is None or effective.lower() not in ('false', '0', 'no', 'off'):
        c.fail('source.redirect_policy', 'Git has an effective URL-specific redirect policy; disable it for this transport.', 4)
    return options


def cache_root(home, name, entry):
    expected = Path(binding(home, name, entry['transport'], entry['ref'], entry['packages'])['cache'])
    if Path(entry['cache']) != expected:
        c.fail('source.cache_invalid', 'Cache location is outside the selected source binding.', 4)
    c.parents_safe(home, expected)
    return expected


def cached(home, name, entry):
    root = cache_root(home, name, entry)
    if c.kind(root) == 'missing':
        return None
    if c.kind(root) != 'directory':
        c.fail('source.cache_invalid', 'Source cache must be an owned directory.', 4)
    if c.kind(root / 'mask-source.json') != 'file':
        c.fail('source.cache_invalid', 'Source cache has no regular ownership marker.', 4)
    marker = c.read_json(root / 'mask-source.json', 'source')
    if marker != dict(schema_version=1, repository=entry['repository'], identity=c.identity(root)):
        c.fail('source.cache_invalid', 'Source cache ownership changed.', 4)
    if c.git(root, 'rev-parse', '--is-bare-repository') != 'true':
        c.fail('source.cache_invalid', 'Expected an owned bare source cache.', 4)
    return root


def remote_refs(root, entry, timeout, output):
    endpoint(root, entry['transport'], entry['repository'])
    options = network_options(root, entry['transport'])
    protocol = urlsplit(entry['repository']).scheme
    options += ['-c', 'protocol.allow=never', '-c', 'protocol.' + protocol + '.allow=always']
    output['data']['resolution_effects'] = dict(network_attempted=True)
    raw = c.git(root, *options, 'ls-remote', entry['transport'], timeout=timeout, max_output=1024 * 1024)
    refs = {}
    if len(raw.encode('utf-8')) > 1024 * 1024:
        c.fail('source.limit', 'Repository advertises too many refs.', 4)
    for line in raw.splitlines():
        parts = line.split('\t')
        if len(parts) != 2:
            c.fail('source.refs_invalid', 'Malformed remote ref advertisement.', 4)
        oid, ref = parts
        if ref.endswith('^{}'):
            continue
        if ref != 'HEAD' and not ref.startswith(('refs/heads/', 'refs/tags/')):
            continue
        if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', oid) or ref in refs:
            c.fail('source.refs_invalid', 'Invalid or duplicate remote ref.', 4)
        refs[selector(ref)] = oid
    if len(refs) > 4096:
        c.fail('source.limit', 'Repository advertises too many refs.', 4)
    return refs, options


def resolve_ref(refs, ref):
    selector(ref)
    if re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', ref):
        return ref
    candidates = [name for name in refs if name == ref or name in ('refs/heads/' + ref, 'refs/tags/' + ref)]
    if len(candidates) > 1:
        c.fail('source.ref_ambiguous', 'Ref names both a branch and a tag; select the full ref.', 4, choices=sorted(candidates))
    if not candidates:
        c.fail('source.ref_unknown', 'Exact ref is unavailable; no fallback to the default branch.', 4, ref=ref)
    return refs[candidates[0]]


def cached_refs(root, entry):
    path = root / 'mask-refs.json'
    value = c.read_json(path, 'source', default={})
    if not value:
        return None
    c.fields(value, ('schema_version', 'repository', 'refs'), family='source')
    if value['repository'] != entry['repository'] or not isinstance(value['refs'], dict) or len(value['refs']) > 4096:
        c.fail('source.cache_invalid', 'Invalid cached ref advertisement.', 4)
    for ref, oid in value['refs'].items():
        selector(ref)
        if not isinstance(oid, str) or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', oid):
            c.fail('source.cache_invalid', 'Invalid cached ref identity.', 4)
    return value['refs']


def fetch(home, name, entry, timeout, output, *, ref=None, advertised=None):
    root = cache_root(home, name, entry)
    endpoint(home, entry['transport'], entry['repository'])
    existing = cached(home, name, entry)
    context = existing or home
    refs, options = advertised or remote_refs(context, entry, timeout, output)
    requested = entry['ref'] if ref is None else ref
    oid = resolve_ref(refs, requested)
    if existing is None:
        root.parent.mkdir(parents=True, exist_ok=True)
        root.mkdir()
        output['data']['cache_effects'] = dict(path=str(root), created=True)
        c.git(root, '-c', 'init.templateDir=', 'init', '--bare', '--object-format=' + ('sha256' if len(oid) == 64 else 'sha1'), mutating=True)
        c.atomic_text(root / 'mask-source.json', c.text_json(dict(schema_version=1, repository=entry['repository'], identity=c.identity(root))), None)
    endpoint(root, entry['transport'], entry['repository'])
    if c.git(root, 'rev-parse', '--show-object-format') != ('sha256' if len(oid) == 64 else 'sha1'):
        c.fail('source.object_format', 'Source object format differs from its existing cache.', 4)
    destination = 'refs/mask/selected' if ref is None else 'refs/mask/frozen/' + oid
    before = c.git(root, 'rev-parse', '--verify', destination + '^{commit}', optional=True)
    output['data']['fetch_effects'] = dict(attempted=True, before=before, after=before)
    baseline = cache_bytes(root)
    last_check = 0
    def resource_check(force=False):
        nonlocal last_check
        now = time.monotonic()
        if not force and now - last_check < 0.05:
            return
        last_check = now
        size = cache_bytes(root)
        if size > CACHE_BYTES or size - baseline > FETCH_BYTES:
            c.fail('source.fetch_limit', 'Fetch exceeds the cache storage policy; acquired objects are retained for inspection.', 4)
    staged = 'refs/mask/acquiring/' + uuid.uuid4().hex
    output['data']['fetch_effects'].update(staging_ref=staged, retained_objects_possible=True,
        resource_policy=dict(fetch_growth_bytes=FETCH_BYTES, cache_bytes=CACHE_BYTES,
                             storage_poll_seconds=0.05, hard_wire_byte_limit=False))
    try:
        resource_check(force=True)
        c.git(root, *options, '-c', 'fetch.unpackLimit=0', '-c', 'gc.auto=0',
              'fetch', '--no-tags', '--no-recurse-submodules', '--no-write-fetch-head',
              '--no-auto-maintenance', entry['transport'],
              '+' + oid + ':' + staged, timeout=timeout, mutating=True, monitor=resource_check)
        resource_check(force=True)
        resolved = c.git(root, 'rev-parse', '--verify', staged + '^{commit}')
        c.git(root, 'update-ref', destination, resolved, before or '0' * len(resolved), mutating=True)
        c.git(root, 'update-ref', '-d', staged, oid, mutating=True)
        path = root / 'mask-refs.json'
        c.atomic_text(path, c.text_json(dict(schema_version=1, repository=entry['repository'], refs=refs)), c.read_text(path, missing=True))
    finally:
        after = c.git(root, 'rev-parse', '--verify', destination + '^{commit}', optional=True)
        output['data']['fetch_effects'].update(after=after, remote_refs_changed=before != after)
    return root, after


def references(home, config, state, name):
    if name == config['legacy_source']:
        return ['legacy source binding']
    result = []
    for key, record in c.consumer_records(state).items():
        root = Path(key)
        if not root.is_dir():
            c.fail('source.references_unavailable', 'Cannot prove a source is unused while a consumer is unavailable.', 4)
        declaration = home / 'user.json' if c.consumer_scope(state, root) == 'user' else root / '.mask.json'
        raw = c.read_json(declaration, 'manifest')
        if name in raw.get('sources', {}) or any(isinstance(item, dict) and item.get('source') == name for item in raw.get('skills', [])):
            result.append(str(declaration))
        lock = declaration.with_name('user.lock.json' if declaration.name == 'user.json' else '.mask.lock.json')
        if c.kind(lock) != 'missing':
            value = c.read_json(lock, 'lock')
            if any(item.get('source') == name for item in value.get('packages', []) if isinstance(item, dict)):
                result.append(str(lock))
    return result


def dispatch(args, output, home):
    original = c.read_text(home / 'config.json')
    config = c.config(c.parse_json(original))
    name = getattr(args, 'name', None)
    proposal = copy.deepcopy(config)
    output['data'] = dict(catalog_only=True)
    if args.command == 'source.migrate':
        name = getattr(args, 'alias', 'legacy')
        alias(name)
        if config['schema_version'] == 1:
            old = config['source']
            root = Path(old['root'])
            c.checkout(root)
            transport = c.git(root, 'remote', 'get-url', old['remote'], optional=True) or str(root)
            entry = binding(home, name, transport, old['branch'], authoring=str(root))
            endpoint(root, transport, entry['repository'])
            proposal.update(schema_version=2, legacy_source=name, sources={name: entry})
        elif config['legacy_source'] != name:
            c.fail('source.alias_conflict', 'Legacy source already migrated under another alias.', 4)
    elif args.command == 'source.list':
        output['data']['sources'] = config.get('sources', {})
        output['data']['migration_required'] = config['schema_version'] == 1
        return
    elif args.command == 'tap.add':
        if config['schema_version'] != 2:
            c.fail('source.migration_required', 'Preview source migrate before adding a tap.', 4)
        entry = binding(home, name, args.url, getattr(args, 'ref', 'main'), getattr(args, 'packages', 'skills'), getattr(args, 'checkout', None))
        if entry['authoring'] is not None:
            root = Path(entry['authoring']).expanduser().resolve()
            c.checkout(root)
            remote = c.git(root, 'remote', 'get-url', 'origin', optional=True) or str(root)
            if repository(remote) != entry['repository']:
                c.fail('source.identity_mismatch', 'Authoring checkout does not match the source identity.', 4)
            entry['authoring'] = str(root)
        existing = config['sources'].get(name)
        if existing is not None and existing != entry:
            c.fail('source.alias_conflict', 'Source alias already has a different approved binding.', 4)
        proposal['sources'][name] = entry
    elif args.command == 'tap.remove':
        selected(config, name)
        state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
        used = references(home, config, state, name)
        if used:
            c.fail('source.referenced', 'Source is still referenced; preview a separate migration/removal first.', 4, references=used)
        del proposal['sources'][name]
        output['data']['cache_retained'] = config['sources'][name]['cache']
    else:
        entry = selected(config, name)
        root = cached(home, name, entry)
        output['data'].update(source=name, binding=entry, cached_revision=c.git(root, 'rev-parse', '--verify', 'refs/mask/selected^{commit}', optional=True) if root else None)
        output['data']['resolution_required'] = root is None or output['data']['cached_revision'] is None
        if args.command == 'source.fetch':
            output['data']['fetch_effects'] = dict(attempted=False)
        if args.command == 'source.fetch' and not output['dry_run']:
            fetch(home, name, entry, config['git_timeout_seconds'], output)
            output['data']['cached_revision'] = output['data']['fetch_effects']['after']
            output['data']['resolution_required'] = output['data']['cached_revision'] is None
        return
    proposal = c.config(proposal)
    plan_hash = c.digest(dict(before=config, after=proposal))
    if getattr(args, 'expect_plan_hash', plan_hash) != plan_hash:
        c.fail('plan.stale', 'Source configuration changed; review a new preview.', 4)
    output['data'].update(config=proposal, plan_hash=plan_hash)
    output['would_change'] = proposal != config
    if output['would_change']:
        output['actions'] = [dict(kind='source.catalog', status='planned')]
        if not output['dry_run']:
            c.atomic_text(home / 'config.json', c.text_json(proposal), original)
            output.update(changed=True, transaction='committed')


def object_blob(root, oid, limit=1024 * 1024):
    size = c.git(root, 'cat-file', '-s', oid, max_output=32)
    if not size.isdecimal() or int(size) > limit:
        c.fail('source.limit', 'Selected metadata exceeds its byte limit.', 4)
    return c.git(root, 'cat-file', 'blob', oid, binary=True, max_output=limit)


def object_text(root, oid):
    try:
        return object_blob(root, oid).decode('utf-8')
    except UnicodeError:
        c.fail('source.metadata_invalid', 'Selected metadata requires UTF-8 text.', 4)


def tree_entries(root, commit, path=''):
    from mask_git import tree
    rows = tree(root, commit, path, recursive=True)
    if len(rows) > 10000:
        c.fail('source.limit', 'Discovery exceeds 10,000 tree entries; use a smaller source layout.', 4)
    result, folded = {}, set()
    import unicodedata
    for mode, kind, oid, path in rows:
        package_path(path)
        if len(path.split('/')) > 32:
            c.fail('source.limit', 'Discovery exceeds depth 32.', 4)
        key = unicodedata.normalize('NFC', path).casefold()
        if path != unicodedata.normalize('NFC', path) or key in folded:
            c.fail('source.path_ambiguous', 'Source tree contains aliased case or Unicode paths.', 4)
        result[path] = (mode, kind, oid)
        folded.add(key)
    return result


def package_metadata(root, record, identifier=None):
    if record[0] not in ('100644', '100755') or record[1] != 'blob':
        c.fail('skill.path_escape', 'SKILL.md must be a regular Git blob.', 4)
    text = object_text(root, record[2])
    if identifier is None:
        # Infer root/nested IDs using the same deliberately small scalar subset.
        match = re.search(r'^name:\s*([^\r\n]*)$', text.split('---', 2)[1] if text.startswith('---') and text.count('---') >= 2 else '', re.M)
        if match is None:
            c.fail('skill.invalid', 'SKILL.md needs a name in frontmatter.')
        identifier = match[1].strip()
        if identifier.startswith('"'):
            identifier = c.parse_json(identifier, 'skill')
        elif identifier.startswith("'") and identifier.endswith("'"):
            identifier = identifier[1:-1].replace("''", "'")
        c.skill_id(identifier)
    return c.metadata(text, identifier), text


def source_index(root, entries):
    entry = entries.get('mask-source.json')
    if entry is None:
        return None
    if entry[0] not in ('100644', '100755') or entry[1] != 'blob':
        c.fail('source.index_invalid', 'Source index must be a regular Git blob.', 4)
    value = c.parse_json(object_text(root, entry[2]), 'source')
    c.fields(value, ('schema_version', 'packages'), ('bundles',), family='source')
    if not isinstance(value['packages'], dict) or len(value['packages']) > 10000:
        c.fail('source.index_invalid', 'Expected a bounded package map.', 4)
    for identifier, path in value['packages'].items():
        c.skill_id(identifier)
        package_path(path)
    bundles = value.get('bundles', {})
    if not isinstance(bundles, dict) or len(bundles) > 1000:
        c.fail('source.index_invalid', 'Expected a bounded bundle map.', 4)
    for name, bundle in bundles.items():
        c.skill_id(name)
        c.fields(bundle, ('skills',), ('description',), family='source')
        if not isinstance(bundle['skills'], list) or len(bundle['skills']) > 1000:
            c.fail('source.index_invalid', 'Bundle entries must be a bounded binding array.', 4)
        if 'description' in bundle and (not isinstance(bundle['description'], str) or len(bundle['description']) > 4096):
            c.fail('source.index_invalid', 'Bundle descriptions must be bounded text.', 4)
        for binding in bundle['skills']:
            c.fields(binding, ('source', 'id'), ('agents', 'version', 'when', 'introduced_by'), family='source')
            alias(binding['source'])
            c.skill_id(binding['id'])
    return value


def exact_entry(root, commit, path):
    from mask_git import tree
    rows = tree(root, commit, exact=path, max_output=4096)
    matches = [row[:3] for row in rows if row[3] == path]
    return matches[0] if len(matches) == 1 else None


def discover(root, name, entry, commit, *, path=None, content=False, identifier=None):
    index_record = exact_entry(root, commit, 'mask-source.json')
    index = source_index(root, {'mask-source.json': index_record} if index_record else {})
    selected_path = package_path(path) if path is not None else None
    candidates = []
    if index is not None:
        paths = [(key, value) for key, value in index['packages'].items() if identifier is None or key == identifier]
        entries = {}
    else:
        selected_root = selected_path if selected_path not in (None, '.') else entry['packages']
        # A root-level skill is still discoverable with the default flat layout.
        root_skill = exact_entry(root, commit, 'SKILL.md')
        selected_tree = exact_entry(root, commit, selected_root) if selected_root != '.' else None
        if selected_root == '.' or selected_tree and selected_tree[:2] == ('040000', 'tree'):
            entries = tree_entries(root, commit, '' if selected_root == '.' else selected_root)
            if selected_root != '.':
                entries = {selected_root + '/' + key: value for key, value in entries.items()}
        else:
            entries = {}
        if root_skill and selected_path is None:
            entries['SKILL.md'] = root_skill
        prefix = '' if entry['packages'] == '.' else entry['packages'] + '/'
        paths = [(None, key.removesuffix('/SKILL.md') if key != 'SKILL.md' else '.')
                 for key in entries if (key == 'SKILL.md' or key.endswith('/SKILL.md'))
                 and (key == 'SKILL.md' or key.startswith(prefix))]
    for identifier, package in paths:
        if selected_path is not None and selected_path != '.' and package != selected_path and not package.startswith(selected_path + '/'):
            continue
        key = 'SKILL.md' if package == '.' else package + '/SKILL.md'
        if index is not None:
            record = exact_entry(root, commit, key)
            if record:
                entries[key] = record
        if key not in entries:
            c.fail('source.index_invalid', 'Indexed package has no SKILL.md at its exact path.', 4, path=package)
        metadata, text = package_metadata(root, entries[key], identifier)
        identifier = metadata['name']
        row = dict(source=name, id=identifier, coordinate=name + '/' + identifier,
                   repository=entry['repository'], path=package, commit=commit,
                   description=metadata['description'], validation='metadata_only')
        if content:
            row['content'] = text
        candidates.append(row)
    paths = sorted(item['path'] for item in candidates)
    if any(a == '.' or b.startswith(a + '/') for i, a in enumerate(paths) for b in paths[i+1:]):
        c.fail('source.path_ambiguous', 'Overlapping package roots need an index selecting one interpretation.', 4, choices=paths)
    ids = [item['id'] for item in candidates]
    if len(set(ids)) != len(ids):
        c.fail('source.name_ambiguous', 'Duplicate package names need an exact source index.', 4, choices=[dict(id=item['id'], path=item['path']) for item in candidates])
    if selected_path is not None and not candidates:
        c.fail('skill.unknown', 'No package matches the selected repository path.', 4, path=selected_path)
    return sorted(candidates, key=lambda item: (item['id'], item['path']))


def locate_url(config, url):
    if url in config.get('sources', {}):
        return url, config['sources'][url], None, None
    normalized = repository(url)
    candidates = [(name, entry, None, None) for name, entry in config.get('sources', {}).items() if entry['repository'] == normalized]
    parsed = urlsplit(url)
    parts = unquote(parsed.path).strip('/').split('/')
    if parsed.scheme.lower() == 'https' and parsed.hostname == 'github.com' and len(parts) >= 2:
        base = 'https://github.com/' + '/'.join(parts[:2]).removesuffix('.git')
        tail = '/'.join(parts[3:]) if len(parts) >= 4 and parts[2] in ('tree', 'blob') else None
        if len(parts) == 2 or tail:
            candidates = [(name, entry, tail, parts[2] if tail else None) for name, entry in config.get('sources', {}).items()
                          if entry['repository'] in (base, base + '.git')]
    if not candidates:
        c.fail('source.unapproved', 'Approve this repository with tap add before inspecting it.', 4)
    if len(candidates) > 1:
        c.fail('source.alias_ambiguous', 'Repository has multiple catalog bindings; use an unambiguous binding.', 4, choices=[item[0] for item in candidates])
    return candidates[0]


def url_selection(tail, kind, refs, requested_ref, requested_path, default_ref):
    if tail is None:
        return requested_ref or default_ref, requested_path
    choices = []
    for i in range(1, len(tail.split('/')) + 1):
        parts = tail.split('/')
        ref, path = '/'.join(parts[:i]), '/'.join(parts[i:]) or '.'
        if requested_ref and ref != requested_ref:
            continue
        if requested_ref or any(key in refs for key in (ref, 'refs/heads/' + ref, 'refs/tags/' + ref)):
            if kind == 'blob':
                if path == 'SKILL.md':
                    path = '.'
                elif path.endswith('/SKILL.md'):
                    path = path.removesuffix('/SKILL.md')
                else:
                    continue
            choices.append(dict(ref=ref, path=path))
    if len(choices) != 1:
        c.fail('source.ref_path_ambiguous' if choices else 'source.ref_unknown',
               'URL ref/path could not be selected uniquely; supply an exact --ref and --path.', 4, choices=choices)
    return choices[0]['ref'], requested_path if requested_path is not None else choices[0]['path']


def inspect(args, output, home):
    config = c.config(c.read_json(home / 'config.json'))
    if config['schema_version'] != 2:
        c.fail('source.migration_required', 'Migrate the source catalog before URL inspection.', 4)
    name, entry, tail, kind = locate_url(config, args.url)
    root = cached(home, name, entry)
    output['data'] = dict(source=name, repository=entry['repository'], resolution_required=True, catalog_only=True)
    advertised = None
    if output['dry_run']:
        refs = cached_refs(root, entry) if root else None
        if refs is None:
            return
    else:
        advertised = remote_refs(root or home, entry, config['git_timeout_seconds'], output)
        refs = advertised[0]
    ref, path = url_selection(tail, kind, refs, getattr(args, 'ref', None), getattr(args, 'path', None), entry['ref'])
    oid = resolve_ref(refs, ref)
    commit = c.git(root, 'rev-parse', '--verify', oid + '^{commit}', optional=True) if root else None
    output['data'].update(ref=ref, path=path, object=oid, commit=commit)
    if not output['dry_run']:
        root, commit = fetch(home, name, entry, config['git_timeout_seconds'], output, ref=ref, advertised=advertised)
    if commit is None:
        return
    output['data'].update(commit=commit, resolution_required=False, skills=discover(root, name, entry, commit, path=path))


def query(args, output, home):
    config = c.config(c.read_json(home / 'config.json'))
    requested = getattr(args, 'id', None)
    names = sorted(config['sources'])
    identifier = None
    if requested and '/' in requested:
        name, identifier = requested.split('/', 1)
        selected(config, name)
        names = [name]
    elif requested:
        identifier = requested
    if identifier is not None:
        c.skill_id(identifier)
    rows, unresolved = [], []
    for name in names:
        entry = selected(config, name)
        root = cached(home, name, entry)
        commit = c.git(root, 'rev-parse', '--verify', 'refs/mask/selected^{commit}', optional=True) if root else None
        if commit is None:
            unresolved.append(name)
        else:
            rows.extend(discover(root, name, entry, commit, content=getattr(args, 'content', False), identifier=identifier))
    output['data'] = dict(skills=rows, resolution_required=bool(unresolved), unresolved_sources=unresolved, validation='metadata_only')
    if identifier is None:
        if args.command == 'skill.validate':
            if unresolved:
                c.fail('source.resolution_required', 'Fetch sources before validating their payloads.', 4, sources=unresolved)
            for row in rows:
                validate_row(home, config, row)
            output['data']['validation'] = 'payload'
        return
    if unresolved:
        c.fail('source.resolution_required', 'Fetch the named sources before establishing a unique package match.', 4, sources=unresolved)
    matches = [item for item in rows if item['id'] == identifier]
    if len(matches) > 1:
        c.fail('source.name_ambiguous', 'Use a source-qualified skill ID.', 4, choices=[item['coordinate'] for item in matches])
    if not matches:
        c.fail('skill.unknown', 'Skill is unavailable in the selected sources.', 4, skill=identifier)
    output['data'] = matches[0]
    if args.command == 'skill.validate':
        validate_row(home, config, output['data'])


def validate_row(home, config, row):
    from mask_packages import validate
    entry = selected(config, row['source'])
    payload = validate(cached(home, row['source'], entry), row['commit'], row['path'], row['id'])
    row.update(payload.summary())
