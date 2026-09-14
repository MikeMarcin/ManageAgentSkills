"""Read-only detection of retired live-checkout inputs for doctor migration (RFC-MASK-0020 AC04; contracts/MIGRATION.md).

This module reads what the live-checkout program left behind: a v1 or v2 machine configuration, mode-less
consumer records and v1 declarations. It never writes, fetches, checks out, stashes or resets; the legacy
checkout is observed with read-only Git commands. ``doctor`` reports :func:`inspect`. ``doctor --migrate``
plans from the same observations and the shared mapping :func:`migrated_declaration`, and the planner stays
authoritative: a consumer row is ``migratable`` when nothing observed here blocks it.
"""
from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import unquote, urlsplit

import mask_core as c
import mask_fs as fs
import mask_pinned as pinned
import mask_resolve as r
import mask_sources as sources

MACHINES = {1: 'legacy_v1', 2: 'legacy_v2', 3: 'current'}
UNFINISHED = ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply')


def machine(config):
    return MACHINES[config['schema_version']]


def is_legacy(record):
    """A registered consumer the live-checkout program recorded: it has no deployment mode."""
    return record is not None and not pinned.is_pinned(record)


def issue(code, message, exit_code=4, **details):
    return c.MaskError(code, message, exit_code, details=details)


def block(blockers, failures, error):
    """Report a blocker and keep its typed error, so a refusal raised from it keeps the error's own exit code."""
    blockers.append(error.as_dict())
    failures.append(error)


def dirty_reason(root):
    """Why the checkout is not a clean committed baseline, or None: edits, untracked files, hidden index flags, sparse or unfinished work."""
    if c.git(root, 'config', '--bool', '--get', 'core.sparseCheckout', optional=True) == 'true':
        return 'sparse_checkout'
    flags = c.git(root, 'ls-files', '-v', '-z', binary=True).split(b'\0')
    if any(item and (item[:1] == b'S' or item[:1].islower()) for item in flags):
        return 'index_flags'
    for marker in UNFINISHED:
        if c.kind(Path(c.git(root, 'rev-parse', '--path-format=absolute', '--git-path', marker))) != 'missing':
            return 'unfinished_operation'
    if c.git(root, 'status', '--porcelain=v1', '--untracked-files=all'):
        return 'worktree_changes'
    return None


def clone(config):
    """Observe the legacy checkout without changing it.

    ``error`` is the typed error (a MaskError) that prevents deriving anything from it, such as a missing or
    non-root checkout. ``published`` is True when HEAD is an ancestor of ``refs/remotes/<remote>/<branch>``,
    False when not, 'unknown' without that ref; ``diverged`` when each holds commits the other lacks.
    """
    source = config['source']
    root = Path(source['root'])
    value = dict(root=str(root), head=None, branch=None, dirty=None, unborn=None, published='unknown',
                 remote_url=None, dirty_reason=None, error=None, diverged=False)
    try:
        c.parents_safe(Path(root.anchor), root)
        top = c.git(root, 'rev-parse', '--show-toplevel', optional=True) if c.kind(root) == 'directory' else None
        if top is None or Path(top).resolve() != root:
            c.fail('source.missing', 'The legacy checkout is missing or is not a Git checkout root.', 3, root=str(root))
        value['head'] = c.git(root, 'rev-parse', '--verify', '--quiet', 'HEAD^{commit}', optional=True)
        value['unborn'] = value['head'] is None
        value['branch'] = c.git(root, 'symbolic-ref', '--quiet', '--short', 'HEAD', optional=True)
        value['dirty_reason'] = dirty_reason(root)
        value['dirty'] = value['dirty_reason'] is not None
        value['remote_url'] = c.git(root, 'remote', 'get-url', source['remote'], optional=True)
        tracking = c.git(root, 'rev-parse', '--verify', '--quiet', f"refs/remotes/{source['remote']}/{source['branch']}^{{commit}}", optional=True)
        if value['head'] and tracking:
            value['published'] = c.git(root, 'merge-base', '--is-ancestor', value['head'], tracking, optional=True) is not None
            # Diverged: HEAD and the remote-tracking branch each hold commits the other lacks (HEAD strictly ahead is only unpublished).
            value['diverged'] = not value['published'] and c.git(root, 'merge-base', '--is-ancestor', tracking, value['head'], optional=True) is None
    except c.MaskError as error:
        value['error'] = error
    return value


def public_clone(observed):
    return {key: observed[key] for key in ('root', 'head', 'branch', 'dirty', 'unborn', 'published')}


def derived_alias(config, remote_url, requested=None):
    """--alias, else the v2 legacy alias, else the remote basename when it is a valid alias (AgentSkills -> agentskills), else legacy."""
    if requested is not None:
        return sources.alias(requested)
    if config['schema_version'] == 2:
        return config['legacy_source']
    if remote_url:
        try:
            name = unquote(urlsplit(sources.repository(remote_url)).path).rstrip('/').rsplit('/', 1)[-1]
            name = (name[:-4] if name.lower().endswith('.git') else name).lower()
            return sources.alias(name)
        except c.MaskError:
            pass
    return 'legacy'


def proposed_tap(config, home, alias, observed):
    """The approved tap binding the legacy checkout becomes; raises the typed refusal that prevents deriving it.

    A v1 checkout's repository is its configured remote, or its own path as a local ``file`` identity. A v2
    machine keeps its legacy binding; another alias renames it, and an alias that already names a different
    approved tap refuses ``source.alias_conflict``.
    """
    root = observed['root']
    identity = sources.repository(observed['remote_url'] or root)
    if config['schema_version'] == 2:
        legacy = config['sources'][config['legacy_source']]
        if identity != legacy['repository']:
            c.fail('source.identity_mismatch', "The checkout's remote no longer matches the approved legacy source identity.", 4,
                   source=config['legacy_source'], observed=identity, approved=legacy['repository'])
        entry = legacy
        if alias != config['legacy_source']:
            entry = sources.binding(home, alias, legacy['transport'], legacy['ref'], legacy['packages'], legacy['authoring'])
            existing = config['sources'].get(alias)
            if existing is not None and existing != entry:
                c.fail('source.alias_conflict', 'The chosen alias already names a different approved tap.', 4, source=alias)
    else:
        entry = sources.binding(home, alias, observed['remote_url'] or root, config['source']['branch'], 'skills', authoring=root)
    # Git URL rewriting (insteadOf) must not turn the transport into another repository.
    sources.endpoint(Path(root), entry['transport'], entry['repository'])
    return dict(alias=alias, **entry)


def legacy_target(clone_root, skill):
    """The directory a live-checkout link named: ``<clone>/skills/<id>``."""
    return Path(clone_root) / 'skills' / skill


def declaration_version(path):
    try:
        value = c.read_json(path, 'manifest', default={})
    except c.MaskError:
        return None
    version = value.get('schema_version') if isinstance(value, dict) else None
    return version if type(version) is int else None


def selected_consumers(home, state, *, project=None, user=False):
    """(root, scope, record) rows to report: every registered legacy consumer, or the explicitly selected scope.

    An explicit --project or --user also reports an unregistered v1 declaration there.
    """
    if user:
        record = state.get('user')
        if record is not None:
            return [(Path(record['root']), 'user', record)] if is_legacy(record) else []
        return [(Path.home().resolve(), 'user', None)] if declaration_version(home / 'user.json') == 1 else []
    if project is not None:
        root = c.project_root(project)
        for known, record in state['projects'].items():
            if Path(known).is_dir() and os.path.samefile(root, known):
                return [(Path(known), 'project', record)] if is_legacy(record) else []
        return [(root, 'project', None)] if declaration_version(root / '.mask.json') == 1 else []
    return [(Path(key), c.consumer_scope(state, key), record) for key, record in sorted(c.consumer_records(state).items()) if is_legacy(record)]


def link_rows(root, record, clone_root, failures):
    """Per recorded link: ok, drift (link text or target differs from the record and checkout), missing or collision."""
    rows, blockers = [], []
    for relative, link in sorted(record['links'].items()):
        leaf = Path(root) / relative
        row = dict(relative=relative, skill=link['skill'], agent=link['target'], link_text=link['link_text'], state='ok')
        try:
            c.parents_safe(Path(root), leaf)
            kind = c.kind(leaf)
        except c.MaskError as error:
            row['state'] = 'collision'
            block(blockers, failures, error)
            rows.append(row)
            continue
        if kind == 'missing':
            row['state'] = 'missing'
        elif kind != 'symlink':
            row['state'] = 'collision'
            block(blockers, failures, issue('target.collision', 'A real or special entry occupies an owned link path.', path=str(leaf), existing_type=kind))
        else:
            text = os.readlink(leaf)
            expected = legacy_target(clone_root, link['skill']) if clone_root is not None else None
            if text != link['link_text'] or expected is not None and fs.normalized_link(leaf, text) != expected:
                row['state'] = 'drift'
                block(blockers, failures, issue('target.drift', 'Owned link changed since it was recorded or no longer names the legacy checkout.', path=str(leaf),
                                                expected=str(expected) if expected is not None else None))
        rows.append(row)
    return rows, blockers


def consumer_row(home, root, scope, record, clone_root, available, failures):
    row = dict(root=str(root), scope=scope, registered=record is not None, declaration_version=None,
               mode='legacy' if record is not None else None, skills=[], links=[])
    blockers = []
    if record is not None:
        try:
            c.registered_root(root, record, scope)
        except c.MaskError as error:
            block(blockers, failures, error)
    if not blockers:
        try:
            declaration = c.selection_manifest(c.read_json(c.declaration_path(root, scope, home), 'manifest'))
            row['declaration_version'] = declaration['schema_version']
            row['skills'] = declaration['skills'] if declaration['schema_version'] == 1 else [r.coordinate(binding) for binding in declaration['skills']]
        except c.MaskError as error:
            block(blockers, failures, error)
        if record is not None and row['declaration_version'] == 2:
            # Its lock may name other taps or commits the checkout lacks, which a clone-only migration cannot prove.
            block(blockers, failures, issue('migration.declaration_unsupported', 'A legacy consumer already declares a v2 selection; release its ownership with unregister --keep-links, then migrate.',
                                            root=str(root), declaration_version=2, remediation=['mask', scope, 'unregister', '--keep-links']))
        if record is not None:
            row['links'], found = link_rows(root, record, clone_root, failures)
            blockers.extend(found)
    if available is not None and row['declaration_version'] == 1:
        for identifier in row['skills']:
            if identifier not in available:
                block(blockers, failures, issue('skill.unknown', 'A declared skill is absent from the legacy checkout at HEAD.', skill=identifier, root=str(root)))
    row.update(migratable=not blockers, blockers=blockers)
    return row


def inspect(home, config, state, *, project=None, user=False, failures=None):
    """``data.migration`` and its warnings for doctor; also the machine observations ``doctor --migrate`` plans from.

    On a v1/v2 machine a condition of the checkout blocks migration only while a registered legacy consumer
    would lock its HEAD; with no such consumer, dirty or unborn checkouts are warnings (configuration only).
    ``failures`` receives the typed errors behind every blocker, machine blockers first and then each row's,
    in report order.
    """
    failures = [] if failures is None else failures
    warnings, blockers = [], []
    legacy_machine = config['schema_version'] in (1, 2)
    observed = tap = available = None
    if legacy_machine:
        observed = clone(config)
        if observed['error'] is not None:
            block(blockers, failures, observed['error'])
        else:
            try:
                tap = proposed_tap(config, home, derived_alias(config, observed['remote_url']), observed)
            except c.MaskError as error:
                block(blockers, failures, error)
            locking = any(is_legacy(record) for record in c.consumer_records(state).values())
            if observed['branch'] != config['source']['branch']:
                block(blockers, failures, issue('source.identity_mismatch', 'The legacy checkout is detached or on a branch other than the configured one.',
                                                branch=observed['branch'], expected=config['source']['branch']))
            if observed['diverged']:
                block(blockers, failures, issue('source.identity_mismatch', 'The legacy checkout and its remote-tracking branch each hold commits the other lacks.',
                                                reason='diverged', head=observed['head'], branch=observed['branch']))
            for condition, code, message in ((observed['unborn'], 'migration.unborn', 'The legacy checkout has no commit on HEAD.'),
                                             (observed['dirty'], 'source.dirty', 'The legacy checkout has uncommitted, untracked, hidden or unfinished work.')):
                if condition:
                    found = issue(code, message, root=observed['root'], reason=observed['dirty_reason'] if code == 'source.dirty' else None)
                    if locking:
                        block(blockers, failures, found)
                    else:
                        warnings.append(dict(code=found.code, message=str(found) + ' No consumer locks its HEAD, so only the configuration migrates.', details=found.details))
            if tap is not None and observed['remote_url'] is None:
                warnings.append(dict(code='migration.local_only_source', message='The checkout has no remote; the tap is a machine-local file identity.', details=dict(repository=tap['repository'])))
            if tap is not None and locking and observed['published'] is False:
                warnings.append(dict(code='migration.unpublished_commit', message='Migrated locks would name a HEAD that is not on the remote-tracking branch.', details=dict(head=observed['head'])))
            if tap is not None and observed['head']:
                try:
                    available = {item['id'] for item in sources.discover(Path(observed['root']), tap['alias'], tap, observed['head'])}
                except c.MaskError as error:
                    block(blockers, failures, error)
    rows = [consumer_row(home, root, scope, record, observed['root'] if observed else None, available, failures)
            for root, scope, record in selected_consumers(home, state, project=project, user=user)]
    report = dict(required=legacy_machine or bool(rows), machine=machine(config), proposed_tap=tap,
                  clone=public_clone(observed) if observed else None, consumers=rows, blockers=blockers,
                  migratable=not blockers and all(row['migratable'] for row in rows))
    return report, warnings


def migrated_declaration(legacy, alias, entry, default_targets, *, ref=None):
    """The v2 declaration a v1 declaration becomes: each skill bound to one tap alias, with the same agents.

    Machine migration passes ``ref='refs/heads/<branch>'`` (MIGRATION.md mapping); a straggler conversion on a
    v3 machine omits it, as install does.
    """
    legacy = c.manifest(legacy)
    binding = dict(repository=entry['repository'], packages=entry['packages'])
    if ref is not None:
        binding['ref'] = ref
    return r.selection(dict(schema_version=2, sources={alias: binding}, default_agents=legacy.get('targets', sorted(default_targets)),
                            skills=[dict(source=alias, id=identifier) for identifier in legacy['skills']]))
