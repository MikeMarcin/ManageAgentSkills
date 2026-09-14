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
import mask_pinned as pinned
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
        if not pinned.is_pinned(record):
            try:
                c.migration_required('Legacy consumer ownership has no live checkout on a tap catalog machine; migrate it first.', root=key)
            except c.MaskError as error:
                consumers.append(dict(root=key, scope=scope, available=root.is_dir(), declaration_basis='cached_declaration', error=error.as_dict()))
            continue
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
            rows.append(dict(skill=coordinate, name=relative.rsplit('/', 1)[1],
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
