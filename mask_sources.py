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
# A tap keeps exact bytes unless it opted in to Git's core.autocrlf=true conversion at tap add (MASK-0109).
LINE_ENDINGS = ('exact', 'autocrlf')
TRANSPORT_POLICIES = ('derived', 'pinned')  # RFC-MASK-0022: derived follows convention; pinned uses the recorded transport only.


def line_endings(entry):
    """The tap's line-ending policy; an entry written before the policy existed keeps exact bytes."""
    return entry.get('line_endings', 'exact')


def transport_policy(entry):
    """``pinned`` uses the recorded transport only; ``derived``, also the reading of an entry from before RFC-MASK-0022, follows convention."""
    return entry.get('transport_policy', 'derived')


def same_binding(left, right):
    """Whether two catalog entries approve the same thing; how this machine reaches the tap is not part of that."""
    return same(left['repository'], right['repository']) and line_endings(left) == line_endings(right) and \
        all(left[key] == right[key] for key in ('ref', 'packages', 'authoring'))


def checkout_conversion(root):
    """The authoring checkout's effective core.autocrlf when Git would convert line endings there; observational."""
    value = c.git(root, 'config', '--get', 'core.autocrlf', optional=True)
    return value if value is not None and value.lower() in ('true', 'input', 'yes', 'on', '1') else None


def authoring_branch(root, ref):
    """The configured branch an authoring checkout must be on; it refuses the same way with or without an origin (MASK-0110)."""
    branch = ref.removeprefix('refs/heads/')
    current = c.git(root, 'symbolic-ref', '--short', 'HEAD', optional=True)
    if current is None:
        c.fail('source.detached', 'Authoring checkout is detached; check out its configured branch.', 4, configured_branch=branch)
    if current != branch:
        c.fail('source.identity_mismatch', 'Authoring checkout is not on its configured branch.', 4, branch=current, configured_branch=branch)
    return branch


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


# RFC-MASK-0022: hosts where HTTPS and SSH front one repository namespace and one permission model.
FORGE_HOSTS = frozenset(('github.com', 'gitlab.com', 'bitbucket.org', 'codeberg.org'))
# The built-in set plus this machine's own ``forge_hosts``. Only a validated machine configuration extends it;
# a project file never can. mask.main() resets it, so one invocation never inherits another machine's opt-in.
ACTIVE_FORGES = set(FORGE_HOSTS)


def forge_hosts(value):
    if not isinstance(value, list) or len(value) > 64 or len(set(value)) != len(value) or \
            any(not isinstance(host, str) or not re.fullmatch(r'[a-z0-9]([a-z0-9.-]{0,251}[a-z0-9])?', host) for host in value):
        c.fail('config.invalid', 'forge_hosts is a list of at most 64 unique lowercase hostnames.')
    return value


def forge_path(spelled):
    """``(host, path)`` when a strict spelling names a forge repository in a transport-neutral shape, else None.

    HTTPS without user info, ``ssh://git@`` with an absolute path, and ``ssh://git@H/~/P``, which is how MASK spelled
    the scp form ``git@H:P`` before this RFC and which no forge serves as a real home-relative path. A non-default
    port or any other SSH user stays strict.
    """
    parsed = urlsplit(spelled)
    if parsed.scheme not in ('https', 'ssh') or parsed.hostname not in ACTIVE_FORGES or parsed.port is not None:
        return None
    if parsed.username != ('git' if parsed.scheme == 'ssh' else None):
        return None
    path = parsed.path[2:] if parsed.scheme == 'ssh' and parsed.path.startswith('/~/') else parsed.path
    path = path.removesuffix('.git')
    return (parsed.hostname, path) if len(path) > 1 else None


def repository(value):
    """A tap's transport-neutral identity (RFC-MASK-0022): forge spellings fold to ``https://H/P.git``; every other host stays strict."""
    spelled = spelling(value)
    forge = forge_path(spelled)
    return spelled if forge is None else 'https://' + forge[0] + forge[1] + '.git'


def same(left, right):
    """Whether two recorded or typed repository spellings name one identity. Every identity comparison goes through here."""
    return repository(left) == repository(right)


def scp(identity):
    """The SSH transport of a forge identity, as Git's scp form; never the ``/~/`` URI, which forges refuse."""
    forge = forge_path(identity)
    return None if forge is None else 'git@' + forge[0] + ':' + forge[1].lstrip('/') + '.git'


def equivalents(identity):
    """Every strict spelling an older program could have recorded for one identity; just itself off the forge hosts."""
    forge = forge_path(repository(identity))
    if forge is None:
        return [identity]
    host, path = forge
    return [prefix + path + suffix for prefix in ('https://' + host, 'ssh://git@' + host, 'ssh://git@' + host + '/~') for suffix in ('.git', '')]


def canonical_entry(entry):
    """A catalog entry as RFC-MASK-0022 writes it: canonical identity, a transport Git can use, an explicit policy.

    The cache stays where it is: it is this identity's cache under an older key, and cache_root accepts that key.
    """
    identity = repository(entry['repository'])
    transport = entry['transport']
    if forge_path(identity) is not None and scheme(transport) == 'ssh':
        transport = scp(identity)  # Never the /~/ URI an older catalog derived from the scp form.
    return dict(entry, repository=identity, transport=transport, transport_policy=transport_policy(entry))


def noncanonical(config):
    """Tap aliases whose catalog entry still carries a pre-RFC-MASK-0022 spelling."""
    return sorted(name for name, entry in config.get('sources', {}).items() if canonical_entry(entry) != dict(entry, transport_policy=transport_policy(entry)))


def canonicalize(args, output, home):
    """``doctor --migrate`` on a tap machine with no scope: rewrite the catalog's identities in one atomic, previewable write.

    Nothing else changes. Project files are never rewritten for a spelling, the state records mirror those files, and
    the caches are reused in place. A single atomic replace leaves the old bytes or the new ones, so no journal is needed.
    """
    original = c.read_text(home / 'config.json')
    config = c.config(c.parse_json(original))
    names = noncanonical(config)
    proposal = c.config(dict(config, sources={name: canonical_entry(entry) if name in names else entry for name, entry in config['sources'].items()}))
    plan_hash = c.digest(dict(before=config, after=proposal))
    rows = [dict(source=name, code='migration.identity_canonicalization', before=config['sources'][name]['repository'], after=proposal['sources'][name]['repository'],
                 transport=proposal['sources'][name]['transport'], cache_reused=config['sources'][name]['cache']) for name in names]
    output['data'] = dict(identity_canonicalization=rows, config=proposal, plan_hash=plan_hash, network='none')
    output['would_change'] = bool(names)
    if getattr(args, 'expect_plan_hash', plan_hash) != plan_hash:
        c.fail('plan.stale', 'The machine catalog changed; review a new preview.', 4)
    if not names or output['dry_run']:
        return
    output['actions'] = [dict(kind='config.migrate', status='planned', path=str(home / 'config.json'))]
    with c.writer_lock(home):
        if c.kind(home / 'pending.json') != 'missing':
            c.fail('recovery.required', 'Recover the pending operation before migrating.', 8)
        c.atomic_text(home / 'config.json', c.text_json(proposal), original)
    output['actions'][0]['status'] = 'applied'
    output.update(changed=True, transaction='committed')


def spelling(value):
    """Normalize one transport spelling without equating HTTPS and SSH authority; what files recorded before RFC-MASK-0022."""
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
    legacy = value['schema_version'] == 2
    # This machine's own opt-in extends forge equivalence before any of its identities is compared (RFC-MASK-0022).
    ACTIVE_FORGES.clear()
    ACTIVE_FORGES.update(FORGE_HOSTS, forge_hosts(value.get('forge_hosts', [])))
    if not isinstance(value['sources'], dict) or not (1 if legacy else 0) <= len(value['sources']) <= 256:
        c.fail('config.invalid', 'Expected a bounded approved source catalog.')
    if legacy:
        alias(value['legacy_source'])
        if value['legacy_source'] not in value['sources']:
            c.fail('config.invalid', 'The legacy source binding is missing.')
    for name, entry in value['sources'].items():
        alias(name)
        c.fields(entry, ('repository', 'transport', 'cache', 'ref', 'packages', 'authoring'), () if legacy else ('line_endings', 'transport_policy'), family='source')
        if entry.get('transport_policy', 'derived') not in TRANSPORT_POLICIES:
            c.fail('config.invalid', 'A tap transport policy is derived or pinned.')
        if line_endings(entry) not in LINE_ENDINGS:
            c.fail('config.invalid', 'A tap line-ending policy is exact or autocrlf.')
        # A catalog written before RFC-MASK-0022 keeps its strict spelling until doctor --migrate converts it; both are one identity.
        if entry['repository'] not in (repository(entry['repository']), spelling(entry['repository'])) or not same(entry['transport'], entry['repository']):
            c.fail('source.identity_mismatch', 'Source transport does not match its approved identity.', 4)
        selector(entry['ref'])
        package_path(entry['packages'])
        if not isinstance(entry['cache'], str) or not Path(entry['cache']).is_absolute():
            c.fail('config.invalid', 'Source cache must be an absolute machine-local path.')
        if entry['authoring'] is not None and (not isinstance(entry['authoring'], str) or not Path(entry['authoring']).is_absolute()):
            c.fail('config.invalid', 'Authoring checkout must be an absolute machine-local path.')
    if legacy and value['sources'][value['legacy_source']]['authoring'] != value['source']['root']:
        c.fail('config.invalid', 'Legacy source migration must preserve its authoring root.')


def cache_path(home, name, identity):
    return home / 'sources' / (name + '-' + c.digest(identity)[7:23] + '.git')


def binding(home, name, transport, ref='main', packages='skills', authoring=None, policy='exact', pinned=False):
    alias(name)
    identity = repository(transport)
    if policy not in LINE_ENDINGS:
        c.fail('invocation.invalid', 'A tap line-ending policy is exact or autocrlf.', 2)
    # Store only validated credential-free text; actual credentials stay with Git.
    transport = str(Path(transport).resolve()) if Path(transport).is_absolute() else transport
    # A forge SSH transport is kept in Git's scp form: the /~/ URI a strict spelling produces is one no forge serves.
    if forge_path(identity) is not None and not transport.startswith('https://'):
        transport = scp(identity)
    return dict(repository=identity, transport=transport, cache=str(cache_path(home, name, identity)),
                ref=selector(ref), packages=package_path(packages), authoring=authoring, line_endings=policy,
                transport_policy='pinned' if pinned else 'derived')


def selected(config, name):
    alias(name)
    catalog = config.get('sources', {})
    if name not in catalog:
        c.fail('source.unknown', 'Source alias is not approved.', 4, source=name)
    return catalog[name]


def endpoint(root, transport, identity):
    expanded = c.git(root, 'ls-remote', '--get-url', transport)
    if not same(expanded, identity):
        c.fail('source.identity_mismatch', 'Git rewrites the transport to an unapproved repository.', 4)


def scheme(transport):
    """``https``, ``ssh`` or ``file`` for a transport in any accepted spelling, including Git's scp form."""
    return urlsplit(spelling(transport)).scheme


def hint_path(root):
    return root / 'mask-transport.json'


def transport_hint(home, name, entry):
    """The transport that last reached a derived tap, kept beside its cache; the catalog's transport until a fetch succeeds.

    It is not rewritten into config.json: fetches run inside journaled operations that bind the configuration's bytes.
    """
    root = cached(home, name, entry)
    value = c.read_json(hint_path(root), 'source', default={}) if root is not None else {}
    if value:
        c.fields(value, ('schema_version', 'transport', 'chosen_by'), family='source')
        if isinstance(value['transport'], str) and same(value['transport'], entry['repository']):
            return value['transport'], value['chosen_by']
    return entry['transport'], 'catalog'


def gh_protocol(host):
    """``gh config get git_protocol -h HOST`` when gh is installed; read-only, and no gh failure is ever fatal."""
    import shutil
    if shutil.which('gh') is None:
        return None
    try:
        code, stdout, _ = c.contained_run(['gh', 'config', 'get', 'git_protocol', '-h', host], dict(os.environ, GH_PROMPT_DISABLED='1', NO_COLOR='1'),
                                          timeout=5, max_output=256, family='gh', name='gh')
    except (c.MaskError, OSError):
        return None
    answer = stdout.decode('utf-8', errors='replace').strip().lower()
    return answer if code == 0 and answer in ('https', 'ssh') else None


def origin_scheme(consumer, host):
    """The scheme of a consumer checkout's ``origin`` when it is on the tap's host: that machine demonstrably authenticates that way."""
    if consumer is None:
        return None
    origin = c.git(consumer, 'remote', 'get-url', 'origin', optional=True)
    try:
        spelled = urlsplit(spelling(origin)) if origin else None
    except c.MaskError:
        return None
    return spelled.scheme if spelled is not None and spelled.scheme in ('https', 'ssh') and spelled.hostname == host else None


def transports(home, name, entry, consumer=None):
    """Ordered ``(transport, chosen_by)`` for one fetch (RFC-MASK-0022): a pin alone; else origin, hint, gh, then the other scheme.

    Every candidate is a spelling of the tap's own identity, so transport selection can never reach another repository.
    """
    forge = forge_path(repository(entry['repository']))
    if transport_policy(entry) == 'pinned':
        return [(entry['transport'], 'pinned')]
    if forge is None:
        return [(entry['transport'], 'catalog')]  # Off the forge hosts HTTPS and SSH are different identities: nothing to derive.
    reach = {'https': repository(entry['repository']), 'ssh': scp(repository(entry['repository']))}
    hinted, source = transport_hint(home, name, entry)
    if scheme(hinted) == 'ssh':
        hinted = reach['ssh']  # Never the /~/ URI an older catalog recorded: no forge serves it.
    # A transport that a fetch proved outranks gh's stated preference; the URL typed at tap add, never yet proven, does not.
    proven = source != 'catalog'
    order = [(origin_scheme(consumer, forge[0]), 'origin'), (scheme(hinted) if proven else None, 'hint'), (gh_protocol(forge[0]), 'gh'),
             (None if proven else scheme(hinted), 'catalog'), ('https', 'probe'), ('ssh', 'probe')]
    result = []
    for chosen, step in order:
        if chosen in reach and chosen not in [scheme(item[0]) for item in result]:
            # The hint keeps its recorded spelling (for example https without .git); a derived scheme uses the canonical one.
            result.append((hinted if scheme(hinted) == chosen else reach[chosen], step))
    return result


UNREACHED = ('git.auth_required', 'git.failed', 'git.timeout')  # Authentication or reachability: the only failures that try the next transport.


def negotiate(home, name, entry, timeout, output, consumer=None):
    """Reach a tap without prompting: the first candidate transport that answers ``ls-remote``.

    Returns the entry carrying the chosen transport, plus its advertisement. A rewritten endpoint, a redirect policy
    or a malformed advertisement refuses at once; only an authentication or reachability failure moves on.
    """
    context = cached(home, name, entry) or home
    attempted = []
    for transport, step in transports(home, name, entry, consumer):
        chosen = dict(entry, transport=transport)
        try:
            refs, options = remote_refs(context, chosen, timeout, output)
        except c.MaskError as error:
            if error.code not in UNREACHED:
                raise
            attempted.append(dict(transport=transport, chosen_by=step, code=error.code))
            failure = error
            continue
        output['data'].setdefault('transports', {})[name] = dict(transport=transport, transport_policy=transport_policy(entry), chosen_by=step, tried=attempted)
        return chosen, refs, options
    if len(attempted) == 1:
        raise failure  # One way to reach the tap: its own error says most.
    c.fail('git.auth_required', 'No transport reached the tap without prompting; configure HTTPS credentials or an SSH key, or pin one with mask tap transport.', 5,
           source=name, tried=attempted)


def remember(home, name, entry, report):
    """Record the transport that worked as the next fetch's hint; a pinned tap has nothing to remember."""
    root = cached(home, name, entry)
    if root is None or transport_policy(entry) == 'pinned' or report is None:
        return
    text = c.text_json(dict(schema_version=1, transport=report['transport'], chosen_by=report['chosen_by']))
    before = c.read_text(hint_path(root), missing=True)
    if before != text:
        c.atomic_text(hint_path(root), text, before)


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
    # Keyed by the canonical identity; a catalog from before RFC-MASK-0022 keeps the key of its recorded spelling until doctor --migrate.
    allowed = {cache_path(home, name, identity) for identity in [entry['repository'], *equivalents(entry['repository'])]}
    expected = Path(entry['cache'])
    if expected not in allowed:
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
    if set(marker) != {'schema_version', 'repository', 'identity'} or marker['schema_version'] != 1 or marker['identity'] != c.identity(root) \
            or not isinstance(marker['repository'], str) or not same(marker['repository'], entry['repository']):
        c.fail('source.cache_invalid', 'Source cache ownership changed.', 4)
    if c.git(root, 'rev-parse', '--is-bare-repository') != 'true':
        c.fail('source.cache_invalid', 'Expected an owned bare source cache.', 4)
    return root


def remote_refs(root, entry, timeout, output):
    endpoint(root, entry['transport'], entry['repository'])
    options = network_options(root, entry['transport'])
    protocol = scheme(entry['transport'])  # The transport in use; a forge identity is spelled https however it is reached.
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
    if not isinstance(value['repository'], str) or not same(value['repository'], entry['repository']) or not isinstance(value['refs'], dict) or len(value['refs']) > 4096:
        c.fail('source.cache_invalid', 'Invalid cached ref advertisement.', 4)
    for ref, oid in value['refs'].items():
        selector(ref)
        if not isinstance(oid, str) or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', oid):
            c.fail('source.cache_invalid', 'Invalid cached ref identity.', 4)
    return value['refs']


def fetch(home, name, entry, timeout, output, *, ref=None, advertised=None, extra=(), consumer=None):
    """Fetch one selector; ``extra`` object IDs join the same Git invocation and are retained under refs/mask/frozen."""
    root = cache_root(home, name, entry)
    existing = cached(home, name, entry)
    # ``advertised`` is negotiate()'s result; its entry carries the transport that answered.
    entry, refs, options = advertised or negotiate(home, name, entry, timeout, output, consumer)
    endpoint(home, entry['transport'], entry['repository'])
    requested = entry['ref'] if ref is None else ref
    oid = resolve_ref(refs, requested)
    extra = sorted(set(extra))
    if any(not isinstance(item, str) or len(item) != len(oid) or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', item) for item in extra):
        c.fail('source.ref_invalid', 'Additional acquisitions require full object IDs in the source object format.', 4)
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
              '+' + oid + ':' + staged, *(f'+{item}:{staged}-{index}' for index, item in enumerate(extra)),
              timeout=timeout, mutating=True, monitor=resource_check)
        resource_check(force=True)
        resolved = c.git(root, 'rev-parse', '--verify', staged + '^{commit}')
        c.git(root, 'update-ref', destination, resolved, before or '0' * len(resolved), mutating=True)
        c.git(root, 'update-ref', '-d', staged, oid, mutating=True)
        for index, item in enumerate(extra):
            freeze(root, item, f'{staged}-{index}')
        path = root / 'mask-refs.json'
        c.atomic_text(path, c.text_json(dict(schema_version=1, repository=entry['repository'], refs=refs)), c.read_text(path, missing=True))
        remember(home, name, entry, output['data'].get('transports', {}).get(name))
    finally:
        after = c.git(root, 'rev-parse', '--verify', destination + '^{commit}', optional=True)
        output['data']['fetch_effects'].update(after=after, remote_refs_changed=before != after)
    return root, after


def freeze(root, oid, staged):
    """Retain one fetched object: refs/mask/frozen/OID names its peeled commit, as source inspect records it."""
    commit = c.git(root, 'rev-parse', '--verify', staged + '^{commit}')
    frozen = 'refs/mask/frozen/' + oid
    previous = c.git(root, 'rev-parse', '--verify', frozen, optional=True)
    if previous not in (None, commit):
        c.fail('source.cache_invalid', 'An exact cache ref has an unexpected value.', 4)
    if previous is None:
        c.git(root, 'update-ref', frozen, commit, '0' * len(commit), mutating=True)
    c.git(root, 'update-ref', '-d', staged, oid, mutating=True)


def references(home, config, state, name):
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
    original = c.read_text(home / 'config.json', missing=args.command == 'tap.add')
    # The first tap bootstraps a machine: it creates the v3 catalog (and empty state) in the same guarded write.
    bootstrap = original is None
    config = c.empty_config() if bootstrap else c.config(c.parse_json(original))
    name = getattr(args, 'name', None)
    proposal = copy.deepcopy(config)
    output['data'] = dict(catalog_only=True, **(dict(tap=name) if name else {}))
    if args.command == 'source.list':
        output['data']['sources'] = config['sources']
        return
    elif args.command == 'tap.add':
        policy = 'autocrlf' if getattr(args, 'autocrlf', False) else 'exact'
        entry = binding(home, name, args.url, getattr(args, 'ref', 'main'), getattr(args, 'packages', 'skills'), getattr(args, 'checkout', None), policy,
                        pinned=getattr(args, 'pin_transport', False))
        output['data']['line_endings'] = policy
        if entry['authoring'] is not None:
            root = Path(entry['authoring']).expanduser().resolve()
            c.checkout(root)
            authoring_branch(root, entry['ref'])
            remote = c.git(root, 'remote', 'get-url', 'origin', optional=True) or str(root)
            if not same(remote, entry['repository']):
                c.fail('source.identity_mismatch', 'Authoring checkout does not match the source identity.', 4)
            entry['authoring'] = str(root)
            converting = checkout_conversion(root) if policy == 'exact' else None
            if converting is not None:
                output['warnings'].append(dict(code='source.line_endings_conversion', path=str(root), autocrlf=converting,
                    message='This tap keeps exact bytes, but Git converts line endings in this checkout (core.autocrlf=' + converting + '). '
                            'Publishing and new development links refuse converted files; set core.autocrlf false in the checkout, or register the tap with --autocrlf.'))
        existing = config['sources'].get(name)
        if existing is not None and not same_binding(existing, entry):
            c.fail('source.alias_conflict', 'Source alias already has a different approved binding.', 4)
        # An identical binding written before the policy existed is kept byte-for-byte.
        proposal['sources'][name] = existing if existing is not None else entry
    elif args.command == 'tap.transport':
        # How this machine reaches a tap (RFC-MASK-0022). Only the catalog changes, and never which repository is trusted.
        existing = selected(config, name)
        url, derive = getattr(args, 'url', None), getattr(args, 'derive', False)
        if (url is None) == (not derive):
            c.fail('invocation.invalid', 'Give the transport URL to pin, or --derive to follow convention again.', 2)
        if derive:
            proposal['sources'][name] = dict(existing, transport_policy='derived')
        else:
            if not same(url, existing['repository']):
                c.fail('source.identity_mismatch', 'That URL names a different repository than the approved tap; nothing changed.', 4, source=name)
            pinned = binding(home, name, url, existing['ref'], existing['packages'], existing['authoring'], line_endings(existing), pinned=True)
            proposal['sources'][name] = dict(existing, transport=pinned['transport'], transport_policy='pinned')
        output['data'].update(source=name, transport=proposal['sources'][name]['transport'], transport_policy=proposal['sources'][name]['transport_policy'])
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
        hinted, chosen_by = transport_hint(home, name, entry)
        pinned = transport_policy(entry) == 'pinned'
        output['data'].update(transport=entry['transport'] if pinned else hinted, transport_policy=transport_policy(entry), chosen_by='pinned' if pinned else chosen_by)
        output['data'].update(source=name, binding=entry, line_endings=line_endings(entry), cached_revision=c.git(root, 'rev-parse', '--verify', 'refs/mask/selected^{commit}', optional=True) if root else None)
        output['data']['resolution_required'] = root is None or output['data']['cached_revision'] is None
        if args.command == 'source.fetch':
            output['data']['fetch_effects'] = dict(attempted=False)
        if args.command == 'source.fetch' and not output['dry_run']:
            fetch(home, name, entry, config['git_timeout_seconds'], output)
            output['data']['cached_revision'] = output['data']['fetch_effects']['after']
            output['data']['resolution_required'] = output['data']['cached_revision'] is None
        return
    proposal = c.config(proposal)
    plan_hash = c.digest(dict(before=None if bootstrap else config, after=proposal))
    if getattr(args, 'expect_plan_hash', plan_hash) != plan_hash:
        c.fail('plan.stale', 'Source configuration changed; review a new preview.', 4)
    output['data'].update(config=proposal, plan_hash=plan_hash)
    output['would_change'] = bootstrap or proposal != config
    if output['would_change']:
        output['actions'] = ([dict(kind='config.create', status='planned')] if bootstrap else []) + [dict(kind='source.catalog', status='planned')]
        if not output['dry_run']:
            if bootstrap:
                c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
            c.atomic_text(home / 'config.json', c.text_json(proposal), original)
            if bootstrap and c.kind(home / 'state.json') == 'missing':
                c.atomic_text(home / 'state.json', c.text_json(c.empty_state()), None)
            output.update(changed=True, transaction='committed')


def object_blob(root, oid, limit=1024 * 1024):
    try:  # One bounded read: the output allowance is the size gate, so an oversized blob is never buffered.
        return c.git_frozen(root, 'cat-file', 'blob', oid, binary=True, max_output=limit)
    except c.MaskError as error:
        if error.code != 'git.output_limit':
            raise
        c.fail('source.limit', 'Selected metadata exceeds its byte limit.', 4)


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
        match = re.search(r'^name:[ \t]*([^\r\n]*)\r?$', text.split('---', 2)[1] if text.startswith('---') and text.count('---') >= 2 else '', re.M)
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
    return validate_index(value)


def validate_index(value):
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
    candidates = [(name, entry, None, None) for name, entry in config.get('sources', {}).items() if repository(entry['repository']) == normalized]
    parsed = urlsplit(url)
    parts = unquote(parsed.path).strip('/').split('/')
    if parsed.scheme.lower() == 'https' and parsed.hostname == 'github.com' and len(parts) >= 2:
        base = 'https://github.com/' + '/'.join(parts[:2]).removesuffix('.git')
        tail = '/'.join(parts[3:]) if len(parts) >= 4 and parts[2] in ('tree', 'blob') else None
        if len(parts) == 2 or tail:
            candidates = [(name, entry, tail, parts[2] if tail else None) for name, entry in config.get('sources', {}).items()
                          if repository(entry['repository']) == repository(base)]
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
    name, entry, tail, kind = locate_url(config, args.url)
    root = cached(home, name, entry)
    output['data'] = dict(source=name, repository=entry['repository'], resolution_required=True, catalog_only=True)
    advertised = None
    if output['dry_run']:
        refs = cached_refs(root, entry) if root else None
        if refs is None:
            return
    else:
        advertised = negotiate(home, name, entry, config['git_timeout_seconds'], output)
        refs = advertised[1]
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


def acquire_exact(home, name, entry, commit, timeout, effects, consumer=None):
    """Acquire only a full commit; never resolve refs or move selected. A derived tap with two ways in is probed once for the one that answers."""
    if not isinstance(commit, str) or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', commit):
        c.fail('source.ref_invalid', 'Exact acquisition requires a full commit.', 4)
    root = cached(home, name, entry)
    if root and c.git(root, 'rev-parse', '--verify', commit + '^{commit}', optional=True) == commit:
        return root
    root = root or cache_root(home, name, entry)
    ways = transports(home, name, entry, consumer)
    scratch = dict(data={})
    entry = negotiate(home, name, entry, timeout, scratch, consumer)[0] if len(ways) > 1 else dict(entry, transport=ways[0][0])
    effects['transport'] = scratch['data'].get('transports', {}).get(name) or dict(transport=entry['transport'], transport_policy=transport_policy(entry), chosen_by=ways[0][1], tried=[])
    endpoint(home, entry['transport'], entry['repository'])
    options = network_options(root if root.exists() else home, entry['transport'])
    protocol = scheme(entry['transport'])  # The transport in use; a forge identity is spelled https however it is reached.
    options += ['-c', 'protocol.allow=never', '-c', 'protocol.' + protocol + '.allow=always']
    effects.update(path=str(root), commit=commit, network_attempted=False, retained_objects_possible=False)
    if c.kind(root) == 'missing':
        c.parents_safe(home, root)
        root.parent.mkdir(parents=True, exist_ok=True)
        root.mkdir()
        effects['cache_created'] = True
        c.git(root, '-c', 'init.templateDir=', 'init', '--bare', '--object-format=' + ('sha256' if len(commit) == 64 else 'sha1'), mutating=True)
        c.atomic_text(root / 'mask-source.json', c.text_json(dict(schema_version=1, repository=entry['repository'], identity=c.identity(root))), None)
    cached(home, name, entry)
    if c.git(root, 'rev-parse', '--show-object-format') != ('sha256' if len(commit) == 64 else 'sha1'):
        c.fail('source.object_format', 'Locked commit and approved cache object format differ.', 4)
    identity = c.identity(root)
    baseline, last = cache_bytes(root), 0
    def monitor(force=False):
        nonlocal last
        now = time.monotonic()
        if not force and now - last < 0.05:
            return
        last = now
        size = cache_bytes(root)
        if size > CACHE_BYTES or size - baseline > FETCH_BYTES:
            c.fail('source.fetch_limit', 'Exact acquisition exceeds storage policy; acquired objects are retained.', 4)
    staged = 'refs/mask/acquiring/' + uuid.uuid4().hex
    effects.update(staging_ref=staged, resource_policy=dict(fetch_growth_bytes=FETCH_BYTES, cache_bytes=CACHE_BYTES, storage_poll_seconds=0.05, hard_wire_byte_limit=False))
    monitor(True)
    endpoint(root, entry['transport'], entry['repository'])
    effects.update(network_attempted=True, retained_objects_possible=True)
    try:
        c.git(root, *options, '-c', 'fetch.unpackLimit=0', '-c', 'gc.auto=0', 'fetch',
              '--no-tags', '--no-recurse-submodules', '--no-write-fetch-head', '--no-auto-maintenance',
              entry['transport'], '+' + commit + ':' + staged, timeout=timeout, mutating=True, monitor=monitor)
    except c.MaskError as error:
        if error.code == 'git.failed':
            c.fail('artifact.unavailable', 'Approved remote did not provide the exact locked commit; no substitute was selected.', 4, commit=commit)
        raise
    monitor(True)
    if c.identity(root) != identity or c.git(root, 'rev-parse', '--verify', staged + '^{commit}', optional=True) != commit:
        c.fail('source.cache_invalid', 'Exact acquisition identity changed.', 4)
    # Retain the exact object under its own immutable name, never a moving selector.
    frozen = 'refs/mask/frozen/' + commit
    previous = c.git(root, 'rev-parse', '--verify', frozen, optional=True)
    if previous not in (None, commit):
        c.fail('source.cache_invalid', 'An exact cache ref has an unexpected value.', 4)
    if previous is None:
        c.git(root, 'update-ref', frozen, commit, '0' * len(commit), mutating=True)
    c.git(root, 'update-ref', '-d', staged, commit, mutating=True)
    effects['staging_ref'] = None
    effects['acquired'] = True
    return root


def publication(args, output, home):
    """Publish exact passive package paths from an isolated, unfiltered index."""
    import tempfile
    import mask_provenance as provenance
    import mask_packages as packages
    config = c.config(c.read_json(home / 'config.json'))
    entry = selected(config, args.name)
    paths = getattr(args, 'paths', [])
    if not paths or len(paths) > 64 or len(set(paths)) != len(paths):
        c.fail('invocation.invalid', 'Publishing requires 1–64 unique --paths package roots.', 2)
    if getattr(args, 'push', False) and not getattr(args, 'commit', False):
        c.fail('invocation.invalid', '--push requires separately explicit --commit.', 2)
    if entry['authoring'] is None:
        c.fail('source.authoring_required', 'Publishing requires an approved authoring checkout.', 4)
    root = Path(entry['authoring'])
    c.checkout(root)
    authoring_branch(root, entry['ref'])
    head = c.git(root, 'rev-parse', '--verify', 'HEAD^{commit}')
    committed_record = exact_entry(root, head, 'mask-source.json')
    committed_index = source_index(root, {'mask-source.json': committed_record} if committed_record else {})
    raw_index = provenance.regular_bytes(root / 'mask-source.json', 1024 * 1024) if c.kind(root / 'mask-source.json') != 'missing' else None
    mapping = validate_index(c.parse_json(raw_index, 'source'))['packages'] if raw_index is not None else {}
    if raw_index is None:
        for path in paths:
            if path.startswith(entry['packages'] + '/') and path.count('/') == entry['packages'].count('/') + 1:
                mapping.setdefault(path.rsplit('/', 1)[-1], path)
    selected_ids = []
    for path in paths:
        package_path(path)
        matches = [identifier for identifier, chosen in mapping.items() if chosen == path]
        if path == '.' or len(matches) != 1:
            c.fail('source.publish_path', 'Publish an exact non-root package path in the approved layout/index.', 4, path=path)
        if (raw_index is not None and committed_index is None or committed_index is not None and committed_index['packages'].get(matches[0]) != path):
            c.fail('source.publish_index_required', 'Commit the selected source-index mapping explicitly before package publication; unrelated index edits are never swept into this commit.', 4, path=path)
        selected_ids.append(matches[0])
    if any(a.startswith(b + '/') or b.startswith(a + '/') for i, a in enumerate(paths) for b in paths[i + 1: ]):
        c.fail('source.publish_path', 'Publication package roots overlap.', 4)
    config_raw = c.read_text(home / 'config.json')
    policy = line_endings(entry)
    observations = []
    payloads = []
    committed = []
    for identifier, path in zip(selected_ids, paths):
        actual, target, observation = provenance.destination(config, args.name, identifier)
        if actual != root or observation['path'] != path or observation['head'] != head:
            c.fail('source.changed', 'Publication source selection changed.', 4)
        staged = c.git(root, '--literal-pathspecs', 'diff', '--cached', '--name-only', '-z', '--', path, binary=True)
        if staged:
            c.fail('source.publish_overlap', 'Selected package has staged changes; preserve/commit those explicitly first.', 4, path=path)
        old = {}
        if exact_entry(root, head, path) is not None:
            old = {item.path: item for item in packages.validate(root, head, path, identifier).files}
        # The tap's line-ending policy decides the published bytes; an exact tap refuses Git-converted copies.
        payload = provenance.authoring_payload(root, target, identifier, commit=head, path=path, committed=old, policy=policy, source=args.name)
        observations.append(observation)
        payloads.append(payload)
        committed.append(old)
    snapshot = dict(config=config_raw, identity=c.identity(root), head=head, index=c.digest(c.git(root, 'ls-files', '--stage', '-z', binary=True)), source_index=c.digest(raw_index), observations=observations, payloads=[payload.summary() for payload in payloads])
    message = getattr(args, 'message', 'Publish selected MASK packages')
    if not isinstance(message, str) or not 1 <= len(message) <= 4096 or '\x00' in message:
        c.fail('invocation.invalid', 'Commit message must be bounded nonempty text.', 2)
    branch = entry['ref'] if entry['ref'].startswith('refs/heads/') else 'refs/heads/' + entry['ref']
    from mask_resolve import ref
    ref(branch, 'source')
    plan_hash = c.digest(dict(snapshot=snapshot, paths=sorted(paths), message=message, commit=getattr(args, 'commit', False), push=getattr(args, 'push', False)))
    output['data'] = dict(source=args.name, paths=paths, parent_commit=head, plan_hash=plan_hash, created_commit=None, created_ref=None, pushed=False, push_outcome='not_attempted', phase='planned', retained_objects_possible=False, authoring_head=head, authoring_index_changed=False, authoring_checkout_updated=False, network='none', line_endings=policy)
    output['would_change'] = any(exact_entry(root, head, payload.path) is None or packages.validate(root, head, payload.path, payload.id).digest != payload.digest for payload in payloads)
    if getattr(args, 'expect_plan_hash', plan_hash) != plan_hash:
        c.fail('plan.stale', 'Publication inputs changed; preview again.', 4)
    if output['dry_run'] or not getattr(args, 'commit', False) or not output['would_change']:
        return
    def recheck():
        if c.read_text(home / 'config.json') != snapshot['config'] or c.identity(root) != snapshot['identity'] or c.git(root, 'rev-parse', 'HEAD') != head or c.digest(c.git(root, 'ls-files', '--stage', '-z', binary=True)) != snapshot['index']:
            c.fail('plan.stale', 'Publication source/config/index changed.', 4)
        for payload, observation, old in zip(payloads, observations, committed):
            actual, target, now = provenance.destination(config, args.name, payload.id)
            if now != observation or provenance.authoring_payload(root, target, payload.id, commit=head, path=payload.path, committed=old, policy=policy, source=args.name).digest != payload.digest:
                c.fail('plan.stale', 'Publication package changed.', 4)
    recheck()
    with tempfile.TemporaryDirectory(prefix='mask-publish-') as temporary:
        isolated = Path(temporary) / 'worktree'
        added = False
        try:
            c.git(root, 'worktree', 'add', '--detach', '--no-checkout', str(isolated), head, mutating=True)
            added = True
            output['data'].update(phase='isolated_index', temporary_worktree_created=True, temporary_worktree_removed=False)
            c.git(isolated, 'read-tree', head, mutating=True)
            for payload in payloads:
                tracked = c.git(isolated, '--literal-pathspecs', 'ls-files', '-z', '--', payload.path, binary=True)
                for raw in tracked.split(b'\0'):
                    if raw:
                        c.git(isolated, 'update-index', '--force-remove', '--', raw.decode('utf-8'), mutating=True)
                for item in payload.files:
                    path = isolated / payload.path / item.path
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_bytes(item.data)
                    output['data'].update(phase='objects', retained_objects_possible=True)
                    output.update(changed=True, transaction='partial')
                    oid = c.git(isolated, 'hash-object', '-w', '--no-filters', '--', str(path), mutating=True)
                    c.git(isolated, 'update-index', '--add', '--cacheinfo', item.mode, oid, payload.path + '/' + item.path, mutating=True)
            tree = c.git(isolated, 'write-tree', mutating=True)
            recheck()
            commit = c.git(isolated, '-c', 'commit.gpgsign=false', 'commit-tree', tree, '-p', head, '-m', message, mutating=True)
            output['data'].update(created_commit=commit, phase='commit_created')
            published = 'refs/mask/published/' + commit
            c.git(root, 'update-ref', published, commit, '0' * len(commit), mutating=True)
            output['data']['created_ref'] = published
            if getattr(args, 'push', False):
                recheck()
                endpoint(root, entry['transport'], entry['repository'])
                output['data']['network'] = 'query'
                refs, _ = remote_refs(root, entry, config['git_timeout_seconds'], output)
                if refs.get(branch) != head:
                    c.fail('source.publish_rebound', 'Remote branch no longer equals the reviewed parent; retained publication commit was not pushed.', 4)
                output['data'].update(network='push', push_attempted=True, pushed=None, push_outcome='unknown', phase='push_attempted')
                c.git(root, *network_options(root, entry['transport']), '-c', 'push.gpgSign=false', '-c', 'push.followTags=false', 'push', '--no-verify', '--porcelain', entry['transport'], commit + ':' + branch, mutating=True, timeout=config['git_timeout_seconds'])
                output['data'].update(pushed=True, push_outcome='confirmed')
            output['data']['phase'] = 'complete'
            output['transaction'] = 'committed'
        finally:
            if added:
                c.git(root, 'worktree', 'remove', '--force', str(isolated), mutating=True)
                output['data']['temporary_worktree_removed'] = True
