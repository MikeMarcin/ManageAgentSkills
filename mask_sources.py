"""Approved repository identities and catalog-only source bindings."""
from __future__ import annotations

import copy
from pathlib import Path
import re
from urllib.parse import quote, unquote, urlsplit, urlunsplit
from urllib.request import url2pathname

import mask_core as c


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


def fetch(home, name, entry, timeout, output):
    root = cache_root(home, name, entry)
    endpoint(home, entry['transport'], entry['repository'])
    if cached(home, name, entry) is None:
        root.parent.mkdir(parents=True, exist_ok=True)
        root.mkdir()  # An existing unrelated object is never adopted.
        output['data']['cache_effects'] = dict(path=str(root), created=True)
        c.git(root, '-c', 'init.templateDir=', 'init', '--bare', mutating=True)
        c.atomic_text(root / 'mask-source.json', c.text_json(dict(schema_version=1, repository=entry['repository'], identity=c.identity(root))), None)
    endpoint(root, entry['transport'], entry['repository'])
    before = c.git(root, 'rev-parse', '--verify', 'refs/mask/selected^{commit}', optional=True)
    protocol = urlsplit(entry['repository']).scheme
    options = network_options(root, entry['transport']) + ['-c', 'protocol.allow=never', '-c', 'protocol.' + protocol + '.allow=always']
    output['data']['fetch_effects'] = dict(attempted=True, before=before, after=before)
    try:
        c.git(root, *options, 'fetch', '--no-tags', '--no-recurse-submodules', entry['transport'],
              '+' + entry['ref'] + ':refs/mask/selected', timeout=timeout, mutating=True)
    finally:
        after = c.git(root, 'rev-parse', '--verify', 'refs/mask/selected^{commit}', optional=True)
        output['data']['fetch_effects'].update(after=after, remote_refs_changed=before != after)


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
