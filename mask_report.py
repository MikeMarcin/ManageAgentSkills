"""Observational inventory over pinned consumer records, locks and owned links (RFC-MASK-0011, MASK-0102).

Reads only the selected consumers' declarations, locks and state records, one level of
discovery leaves, and the locked store metadata a compatibility decision needs. There is
no network, writer lock, fetch, store materialization or control-file write.
"""
from __future__ import annotations

from pathlib import Path

import mask_adapters as adapters
import mask_core as c
import mask_fs as fs
import mask_resolve as r
import mask_selection as selection
import mask_store as store

EXCLUDED = ('not_applicable', 'excluded_by_metadata')
ARTIFACT = ('payload_digest', 'metadata_digest', 'commit', 'selector')


def observed(path, family, counter, counts, observations):
    """Read one control file; its exact bytes are rechecked for drift after the report."""
    value, raw = r.read_model(path, family)
    counts[counter + 's_read'] += 1
    counts[counter + '_bytes_read'] += len(raw)
    observations.append((path, raw, counter))
    return value


def stored_metadata(home, row, counts):
    """Locked absence needs no read; present metadata must match its locked digest in the store copy."""
    if row['metadata_digest'] == c.digest(b'null'):
        return None
    raw = r.regular_bytes(store.location(home, row['payload_digest'], row['id'])[1] / 'mask-skill.json', r.METADATA_BYTES)
    counts['payload_files_read'] += 1
    value = r.metadata(raw)
    if c.digest(r.canonical(value, 'metadata')) != row['metadata_digest']:
        c.fail('metadata.unavailable', 'Stored metadata differs from its locked digest.', 4)
    return value


def decisions(home, declaration, resolved, record, scope, policy, counts, identifier=None):
    """Selection outcome status by (coordinate, agent); empty when any needed metadata is unobservable.

    A where-used query evaluates only bindings that share its ID: an invocation-name conflict is the
    only outcome that spans coordinates, so unrelated payload metadata is never read.
    """
    if identifier is not None:
        declaration = dict(declaration, skills=[binding for binding in declaration['skills'] if binding['id'] == identifier])
        resolved = dict(resolved, selection_digest=r.selection_digest(declaration),
                        packages=[row for row in resolved['packages'] if row['id'] == identifier])
    facts, locked = selection.device(), {r.coordinate(row): row for row in resolved['packages']}
    try:
        metadata = {}
        for key in selection.applicable_coordinates(declaration, facts):
            if key in record.get('dev_links', {}):
                return {}  # Working authoring bytes have no locked metadata to observe.
            metadata[key] = stored_metadata(home, locked[key], counts)
        evaluated = selection.evaluate([dict(origin='local', declaration=declaration, lock=resolved)], metadata, facts=facts,
                                       enabled_agents=policy['enabled_agents'], scope=scope, root=record['root'],
                                       identity=record['root_identity'], overrides=policy['overrides'])
    except c.MaskError:
        return {}
    return {(outcome['coordinate'], outcome['agent']): outcome['status'] for outcome in evaluated['outcomes']}


def link_target(link, home):
    """An owned link's recorded destination: the authoring package of a dev link, otherwise its store payload."""
    if 'dev' in link:
        return Path(link['dev']['root']) / link['dev']['path']
    return store.location(home, link['resolution']['payload_digest'], link['skill'])[1]


def dispatch(args, output, home):
    limit, offset = getattr(args, 'limit', 100), getattr(args, 'offset', 0)
    if not 1 <= limit <= 1000 or offset < 0:
        c.fail('invocation.invalid', 'Use limit 1–1000 and a nonnegative offset.', 2)
    config = c.config(c.read_json(home / 'config.json'))
    state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
    records = c.consumer_records(state)
    inverse = args.command == 'skill.where-used'
    identifier = None
    if inverse:
        if args.id.count('/') != 1:
            c.fail('invocation.invalid', 'Use the source-qualified SOURCE/ID form.', 2)
        alias, identifier = args.id.split('/')
        c.skill_id(identifier)
        if alias not in config['sources']:
            c.fail('source.unknown', 'Source alias is not approved.', 4, source=alias)
        if getattr(args, 'scope', None) not in (None, 'project', 'user') or getattr(args, 'agent', None) not in (None, *c.ADAPTERS):
            c.fail('invocation.invalid', 'Choose a supported scope and agent.', 2)
    if inverse or getattr(args, 'all', False):
        roots = sorted(records)
    elif getattr(args, 'user', False):
        if not state.get('user'):
            c.fail('user.not_registered', 'User scope is not registered.', 4)
        roots = [state['user']['root']]
    else:
        requested = getattr(args, 'project', None)
        root = Path(requested).expanduser().resolve() if requested else c.project_root()
        if str(root) not in records:
            c.fail('project.not_registered', 'Inventory requires a registered consumer.', 4)
        roots = [str(root)]
    try:
        policy = selection.read_policy(home)[0]
    except c.MaskError:
        policy = None  # An unreadable local policy leaves every compatibility decision unspecified.
    rows, consumers, observations = [], [], []
    counts = dict(declarations_read=0, declaration_bytes_read=0, locks_read=0, lock_bytes_read=0,
                  payload_files_read=0, directories_enumerated=0, leaves_inspected=0)
    for key in roots:
        scope = c.consumer_scope(state, key)
        if getattr(args, 'scope', None) not in (None, scope):
            continue
        root, record = Path(key), records[key]
        consumer = dict(root=key, scope=scope, available=True, declaration_basis='live_declaration', error=None,
                        mode=record['mode'], reproducible=record['mode'] == 'pinned')
        consumers.append(consumer)
        declaration, resolved = r.selection(record['last_manifest']), r.lock(record['last_lock'])
        try:
            c.registered_root(root, record, scope)
        except c.MaskError as error:
            consumer.update(available=False, error=error.as_dict())
        else:
            try:
                current = r.selection(observed(c.declaration_path(root, scope, home), 'manifest', 'declaration', counts, observations))
                declaration, resolved = current, r.lock(observed(r.lock_path(root, scope, home), 'lock', 'lock', counts, observations), current)
            except c.MaskError as error:
                consumer['error'] = error.as_dict()
        if consumer['error'] is not None:
            # Diagnostic only: the cached pinned selection is not a claim about the current declaration.
            consumer['declaration_basis'] = 'cached_pinned_selection'
        entries = {}
        held = {r.coordinate(binding) for binding in declaration['skills'] if binding.get('pinned')}
        for binding in declaration['skills']:
            agents = binding.get('agents', declaration['default_agents'])
            for agent in sorted(c.ADAPTERS) if agents == 'all' else agents:
                entries[adapters.relative(agent, scope, binding['id']), r.coordinate(binding)] = (agent, 'local_declaration')
        for relative, link in record['links'].items():
            entries.setdefault((relative, r.coordinate(link['resolution'])), (link['target'], 'ownership'))
        if getattr(args, 'include_unmanaged', False) and consumer['available']:
            for agent, parent in adapters.paths(scope).items():
                directory = root / parent
                try:
                    c.parents_safe(root, directory / 'mask-inventory-check')
                    if c.kind(directory) == 'directory':
                        counts['directories_enumerated'] += 1
                        known = {relative for relative, _ in entries}
                        for leaf in directory.iterdir():
                            if f'{parent}/{leaf.name}' not in known:
                                entries[f'{parent}/{leaf.name}', None] = (agent, 'unmanaged')
                except c.MaskError as error:
                    consumer.setdefault('discovery_errors', []).append(error.as_dict())
        live = consumer['declaration_basis'] == 'live_declaration' and policy is not None
        decided = decisions(home, declaration, resolved, record, scope, policy, counts, identifier) if live else {}
        locked, devs = {r.coordinate(row): row for row in resolved['packages']}, record.get('dev_links', {})
        for (relative, coordinate), (agent, origin) in sorted(entries.items(), key=lambda item: (item[0][0], item[0][1] or '')):
            if inverse and coordinate != args.id or getattr(args, 'agent', None) not in (None, agent):
                continue
            link = record['links'].get(relative)
            owned = link if link is not None and r.coordinate(link['resolution']) == coordinate else None
            row = locked.get(coordinate) or (owned or {}).get('resolution')
            decision = decided.get((coordinate, agent), decided.get((coordinate, None)))
            actual, error, target = dict(type='unknown', link_text=None), None, None
            if consumer['available']:
                try:
                    c.parents_safe(root, root / relative)
                    actual = fs.link_value(root / relative)
                    counts['leaves_inspected'] += 1
                    if owned:
                        target = link_target(owned, home)
                except c.MaskError as caught:
                    error = caught.as_dict()
            if not consumer['available']:
                status = 'unavailable_consumer'
            elif error or consumer['error'] or decision == 'blocked':
                status = 'blocked'
            elif owned:
                matches = (origin == 'local_declaration' and decision not in EXCLUDED and owned['resolution'] == row
                           and actual['type'] == 'symlink' and actual['link_text'] == owned['link_text']
                           and fs.normalized_link(root / relative, owned['link_text']) == target and c.kind(target) == 'directory')
                status = 'managed_converged' if matches else 'managed_drifted'
            elif origin == 'unmanaged' or actual['type'] != 'missing' and relative not in record['links']:
                status = 'unmanaged_present'
            elif decision in EXCLUDED:
                status = 'inapplicable'
            else:
                status = 'declared_not_deployed'
            rows.append(dict(skill=coordinate, name=relative.rsplit('/', 1)[1], pinned=coordinate in held,
                             source=dict(alias=row['source'], repository=row['repository']) if row else None,
                             package_path=row['path'] if row else None,
                             artifact={field: row[field] for field in ARTIFACT} if row else None,
                             recorded_source_revision=None,
                             content_mode='unknown' if coordinate is None else 'dev_link' if coordinate in devs else 'pinned',
                             root=key, scope=scope, agent=agent, declared=origin == 'local_declaration',
                             declaration_basis=consumer['declaration_basis'], origin=origin, owned=owned is not None,
                             path=str(root / relative), actual=actual, status=status,
                             compatibility=decision or 'unspecified', host_load='not_verified', error=error))
    for path, raw, counter in observations:
        try:
            unchanged = r.regular_bytes(path, r.MODEL_BYTES) == raw
        except (c.MaskError, OSError):
            unchanged = False
        if not unchanged:
            c.fail('state.drift', 'A declaration or lock changed during inventory; retry.', 4)
        counts[counter + '_bytes_read'] += len(raw)
    output['data'] = dict(rows=rows[offset:offset + limit], total_rows=len(rows),
                          next_offset=offset + limit if offset + limit < len(rows) else None,
                          consumers=consumers, source_mode='tap', network='none',
                          scope='registered_local_consumers' if inverse or getattr(args, 'all', False) else 'selected_consumer',
                          complete=all(item['error'] is None and not item.get('discovery_errors') for item in consumers),
                          work=counts, limitations=['Compatibility is unspecified for development links and wherever locked store metadata is not observable.',
                                                  'Profile, fleet receipt and actual host-loading data are unavailable.'])


PATCH_BYTES = 64 * 1024
PATCH_FILE_BYTES = 16 * 1024


def text_lines(data):
    """Return bounded passive UTF-8 lines, or None for binary data."""
    import unicodedata
    try:
        value = data.decode('utf-8')
    except UnicodeDecodeError:
        return None
    if '\x00' in value:
        return None
    return ''.join(ch if ch in '\t\n\r' or unicodedata.category(ch) not in ('Cc', 'Cf') else '?' for ch in value).splitlines()


def package_diff(before, after, *, patch=False):
    import difflib
    old = {file.path: file for file in before.files} if before else {}
    new = {file.path: file for file in after.files} if after else {}
    files, patches = [], []
    budget, truncated = PATCH_BYTES, False
    for path in sorted(old.keys() | new.keys()):
        left, right = old.get(path), new.get(path)
        if left == right:
            continue
        summaries = {}
        lines = []
        for side, file in (('before', left), ('after', right)):
            summaries[side] = dict(size=len(file.data), sha256=c.digest(file.data), mode=file.mode) if file else None
            lines.append(text_lines(file.data) if file else [])
        binary = any(value is None for value in lines)
        files.append(dict(path=path, change='added' if left is None else 'removed' if right is None else 'modified',
                          binary=binary, **summaries))
        if not patch or binary:
            continue
        if budget == 0 or any(item and len(item.data) > PATCH_FILE_BYTES for item in (left, right)) or any(len(value) > 1000 for value in lines):
            truncated = True
            continue
        label = ''.join(ch if ch.isprintable() else '?' for ch in path)
        diff = '\n'.join(difflib.unified_diff(*lines, fromfile='a/' + label, tofile='b/' + label, lineterm=''))
        size = len(diff.encode('utf-8')) + 1
        if size > budget:
            truncated = True
            continue
        if diff:
            patches.append(diff)
            budget -= size
    result = dict(files=files)
    if patch:
        result.update(patch='\n'.join(patches), patch_truncated=truncated)
    return result


def exact_payload(home, row, config, views):
    key = r.payload_key(row)
    if key not in views:
        root, _ = store.location(home, row['payload_digest'], row['id'])
        if c.kind(root) != 'missing':
            views[key] = store.verify(home, row, as_payload=True)
        else:
            import mask_sources as sources
            views[key] = r.verify_resolution(home, row['source'], sources.selected(config, row['source']), row)
    return views[key]


def impact_kind(old, new, files):
    if old is None or new is None:
        return 'selection'
    paths = {item['path'] for item in files}
    if not paths and old == new:
        return 'identical'
    if not paths or paths == {'.mask-provenance.json'}:
        return 'provenance'
    return 'metadata' if paths == {'mask-skill.json'} else 'content'


def update_impact(home, config, consumers, planned, locks, views, refs):
    """Explain candidate resolutions and observed links without replanning or fetching."""
    before = c.consumer_records(planned['intent']['before_state'])
    after = c.consumer_records(planned['intent']['after_state'])
    comparisons, deployments = {}, []
    for item in consumers:
        key = str(item['root'])
        scope = item['scope']
        current, desired = before[key], after[key]
        if current.get('mode') == 'dev-link':
            deployments.append(dict(root=key, scope=scope, status='development_link',
                                    warning='Edits to the shared authoring checkout are visible through its links. Running agents may cache instructions.'))
            continue
        previous = item.get('previous_lock')
        proposed = locks.get(key)
        if previous is None or proposed is None:
            deployments.append(dict(root=key, scope=scope, status=item['row']['status'], error=item['row']['error']))
            continue
        old_rows = {r.coordinate(row): row for row in previous['packages']}
        new_rows = {r.coordinate(row): row for row in proposed['packages']}
        held = {r.coordinate(row) for row in item['declaration']['skills'] if row.get('pinned') or 'commit' in row.get('version', {})}
        selected = set(item['skills']) or old_rows.keys() | new_rows.keys()
        for coordinate in sorted(selected):
            old, new = old_rows.get(coordinate), new_rows.get(coordinate)
            old_agents = sorted({link['target'] for link in current['links'].values() if r.coordinate(link['resolution']) == coordinate})
            new_agents = sorted({link['target'] for link in desired['links'].values() if r.coordinate(link['resolution']) == coordinate})
            content_changed = (old or {}).get('payload_digest') != (new or {}).get('payload_digest')
            kind = None
            if old != new:
                pair = tuple(r.payload_key(row) if row else '' for row in (old, new))
                if pair not in comparisons:
                    try:
                        compared = package_diff(*(exact_payload(home, row, config, views) if row else None for row in (old, new)))
                        compared['kind'] = impact_kind(old, new, compared['files'])
                    except c.MaskError as error:
                        compared = dict(kind='unavailable', files=[], error=error.as_dict())
                    comparisons[pair] = dict(id=c.digest(list(pair)), skill=coordinate,
                                             before_commit=old['commit'] if old else None, after_commit=new['commit'] if new else None,
                                             **compared)
                change = comparisons[pair]['id']
                kind = comparisons[pair]['kind']
                status = 'blocked' if planned['blockers'] else 'affected'
            else:
                change = None
                status = 'pinned_unaffected' if coordinate in held else 'unchanged'
                if old_agents != new_agents:
                    status = 'affected'
                elif old and old['selector'].get('ref', '').startswith('refs/heads/') and (old['source'], old['selector']['ref']) in refs and refs[old['source'], old['selector']['ref']] != old['commit'] and status == 'unchanged':
                    status = 'ref_advanced_identical_payload'
            deployments.append(dict(root=key, scope=scope, skill=coordinate, status=status, comparison=change,
                                    before_agents=old_agents, after_agents=new_agents, targets_changed=old_agents != new_agents,
                                    host_refresh_required=status == 'affected' and (old_agents != new_agents or content_changed and bool(new_agents) and kind != 'provenance'),
                                    host_load='not_verified'))
        for name, receipt in current.get('profiles', {}).items():
            for row in receipt['lock']['packages']:
                coordinate = r.coordinate(row)
                if item['skills'] and coordinate not in item['skills']:
                    continue
                agents = sorted({link['target'] for link in current['links'].values() if r.payload_key(link['resolution']) == r.payload_key(row)})
                deployments.append(dict(root=key, scope=scope, skill=coordinate, status='profile_frozen_unaffected',
                                        profile=name, profile_revision=receipt['revision'], before_agents=agents, after_agents=agents,
                                        targets_changed=False, host_refresh_required=False, host_load='not_verified'))
    return dict(comparisons=list(comparisons.values()), deployments=deployments)


def compare_commits(args, output, home):
    import mask_sources as sources
    coordinate = r.qualified(args.id, 'diff')
    name, identifier = coordinate.split('/')
    config = c.config(c.read_json(home / 'config.json'))
    entry = sources.selected(config, name)
    resolved = []
    for commit in (getattr(args, 'from'), args.to):
        if not r.OID.fullmatch(commit):
            c.fail('invocation.invalid', 'Compare two full lowercase commit IDs from a lock or update report.', 2)
        declaration = dict(schema_version=2, sources={name: dict(repository=entry['repository'], packages=entry['packages'])}, skills=[])
        binding = dict(source=name, id=identifier, version=dict(commit=commit))
        views = {}
        try:
            row = r.resolve_binding(home, declaration, binding, entry, views)
        except c.MaskError as error:
            if error.code != 'lock.resolution_required':
                raise
            state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
            recorded = {}
            for record in c.consumer_records(state).values():
                for lock in [record['last_lock'], *(item['lock'] for item in record.get('profiles', {}).values())]:
                    for candidate in lock['packages']:
                        if r.coordinate(candidate) == coordinate and candidate['commit'] == commit and sources.same(candidate['repository'], entry['repository']):
                            key = (candidate['path'], candidate['payload_digest'], candidate['metadata_digest'], candidate.get('provenance_digest'))
                            recorded[key] = candidate
            if len(recorded) != 1:
                raise
            row = next(iter(recorded.values()))
        resolved.append((row, exact_payload(home, row, config, views)))
    old, new = resolved
    result = package_diff(old[1], new[1], patch=getattr(args, 'patch', False))
    output['data'] = dict(skill=coordinate, before=old[0], after=new[0], network='none',
                          kind=impact_kind(old[0], new[0], result['files']), **result)


def inspect_exact(args, output, home):
    if args.command == 'diff':
        return compare_commits(args, output, home)
    import argparse
    import mask_update
    upgrade = argparse.Namespace(**vars(args))
    upgrade.command = upgrade.public_command = 'upgrade'
    # The identical upgrade engine and approval namespace generate the executable hash.
    output['dry_run'] = True
    mask_update.dispatch(upgrade, output, home, impact=True)
