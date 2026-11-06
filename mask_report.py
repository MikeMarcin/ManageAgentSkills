"""Observational inventory over pinned consumer records, locks and owned links (RFC-MASK-0011, MASK-0102).

Reads only the selected consumers' declarations, locks and state records, one level of
discovery leaves, and the locked store metadata a compatibility decision needs. There is
no network, writer lock, fetch, store materialization or control-file write.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

import mask_adapters as adapters
import mask_core as c
import mask_fs as fs
import mask_resolve as r
import mask_selection as selection
import mask_sources as sources
import mask_store as store

EXCLUDED = ('not_applicable', 'excluded_by_metadata')
ARTIFACT = ('payload_digest', 'metadata_digest', 'provenance_digest', 'commit', 'selector')


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
    counts['payload_bytes_read'] += len(raw)
    value = r.metadata(raw)
    if c.digest(r.canonical(value, 'metadata')) != row['metadata_digest']:
        c.fail('metadata.unavailable', 'Stored metadata differs from its locked digest.', 4)
    return value


def decisions(home, contributions, record, scope, policy, counts, identifier=None):
    """Read metadata only for the queried skill and potential invocation-name conflicts."""
    if identifier is not None:
        narrowed = []
        for layer in contributions:
            declaration = {key: value for key, value in layer['declaration'].items() if key != 'bundle_state'}
            declaration['skills'] = [binding for binding in declaration['skills'] if binding['id'] == identifier]
            locked = dict(layer['lock'], selection_digest=r.selection_digest(declaration),
                          packages=[row for row in layer['lock']['packages'] if row['id'] == identifier])
            narrowed.append(dict(layer, declaration=declaration, lock=locked))
        contributions = narrowed
    facts, metadata = selection.device(), {}
    try:
        for layer in contributions:
            applicable = set(selection.applicable_coordinates(layer['declaration'], facts))
            for row in layer['lock']['packages']:
                coordinate = r.coordinate(row)
                if coordinate not in applicable:
                    continue
                if coordinate in record.get('dev_links', {}):
                    return {}, {}
                key = r.payload_key(row)
                if key not in metadata:
                    metadata[key] = stored_metadata(home, row, counts)
        evaluated = selection.evaluate(contributions, metadata, facts=facts,
                                       enabled_agents=policy['enabled_agents'], scope=scope, root=record['root'],
                                       identity=record['root_identity'], overrides=policy['overrides'])
    except c.MaskError:
        return {}, {}
    precedence = ('not_applicable', 'excluded_by_metadata', 'selected', 'overridden', 'blocked')
    statuses = {}
    for row in evaluated['outcomes']:
        key = row['coordinate'], row['agent']
        if key not in statuses or precedence.index(row['status']) > precedence.index(statuses[key]):
            statuses[key] = row['status']
    desired = {(row['coordinate'], row['agent']): row['resolution'] for row in evaluated['deployable']}
    return statuses, desired


def declaration_origins(declaration, origin, coordinate):
    ledger = declaration.get('bundle_state')
    if ledger is None:
        return [origin]
    result = [origin] if coordinate in ledger['manual'] or origin != 'local' else []
    for name, receipt in ledger['bundles'].items():
        if any(r.coordinate(binding) == coordinate for binding in receipt['bindings']):
            result.append(('' if origin == 'local' else origin + '/') + 'bundle:' + name)
    return result


def link_target(link, home):
    """An owned link's recorded destination: the authoring package of a dev link, otherwise its store payload."""
    if 'dev' in link:
        return Path(link['dev']['root']) / link['dev']['path']
    return store.location(home, link['resolution']['payload_digest'], link['skill'])[1]


def dispatch(args, output, home):
    limit, offset = pagination(args)
    config = c.config(c.read_json(home / 'config.json'))
    state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
    records = c.consumer_records(state)
    inverse = args.command == 'skill.where-used'
    if getattr(args, 'fleet_observations', None) and not getattr(args, 'fleet', False):
        c.fail('invocation.invalid', 'Use --fleet with --fleet-observations FILE.', 2)
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
                  payload_files_read=0, payload_bytes_read=0, git_scans=0, directories_enumerated=0, leaves_inspected=0)
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
        from mask_profiles import freshness, layers
        profiles = record.get('profiles', {})
        if profiles:
            consumer['profiles'] = freshness(profiles)
        contributions = layers(declaration, resolved, profiles)
        entries, origins, locked, held = {}, {}, {}, set()
        for layer in contributions:
            selected = layer['declaration']
            for row in layer['lock']['packages']:
                locked.setdefault(r.coordinate(row), row)
            for binding in selected['skills']:
                coordinate = r.coordinate(binding)
                if identifier is not None and identifier != binding['id']:
                    continue
                if binding.get('pinned'):
                    held.add(coordinate)
                agents = binding.get('agents', selected['default_agents'])
                for agent in sorted(c.ADAPTERS) if agents == 'all' else agents:
                    edge = adapters.relative(agent, scope, binding['id']), coordinate
                    entries.setdefault(edge, (agent, 'local_declaration' if layer['origin'] == 'local' else 'profile'))
                    origins.setdefault(edge, set()).update(declaration_origins(selected, layer['origin'], coordinate))
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
        decided, desired = decisions(home, contributions, record, scope, policy, counts, identifier) if live else ({}, {})
        devs = record.get('dev_links', {})
        for (relative, coordinate), (agent, origin) in sorted(entries.items(), key=lambda item: (item[0][0], item[0][1] or '')):
            if inverse and coordinate != args.id or getattr(args, 'agent', None) not in (None, agent):
                continue
            link = record['links'].get(relative)
            owned = link if link is not None and r.coordinate(link['resolution']) == coordinate else None
            declared = origin in ('local_declaration', 'profile')
            row = desired.get((coordinate, agent)) or ((owned or {}).get('resolution') if not declared else None) or locked.get(coordinate)
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
                matches = (declared and decision not in EXCLUDED and owned['resolution'] == row
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
                             artifact={field: row[field] for field in ARTIFACT if field in row} if row else None,
                             recorded_source_revision=None,
                             content_mode='unknown' if coordinate is None else 'dev_link' if coordinate in devs else 'pinned',
                             root=key, scope=scope, agent=agent, declared=declared,
                             origins=sorted(origins.get((relative, coordinate), ())),
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
                                                  'Host loading is unverified. Link observations do not rescan package bytes.'])
    if getattr(args, 'fleet', False):
        fleet = recorded_fleet(args, home, config['sources'][alias]['repository'], limit, offset)
        output['data']['fleet'] = fleet
        output['data']['complete'] &= fleet['complete']


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
    if args.command == 'report':
        return inspect_receipt(args, output, home)
    import argparse
    import mask_update
    limit, offset = pagination(args)
    upgrade = argparse.Namespace(**vars(args))
    upgrade.command = upgrade.public_command = 'upgrade'
    # The identical upgrade engine and approval namespace generate the executable hash.
    output['dry_run'] = True
    mask_update.dispatch(upgrade, output, home, impact=True)
    data = output['data']
    if getattr(args, 'output', None):
        receipt = receipt_for(data)
        data['receipt'] = publish_report(args.output, c.text_json(receipt))
        data['operation_id'] = receipt['operation_id']
        output.update(changed=True, would_change=True, dry_run=False, transaction='committed')
    data['impact'] = page_impact(data.get('impact', dict(deployments=[], comparisons=[])), limit, offset)


def recorded_fleet(args, home, repository, limit, offset):
    """Read a projection of recorded receipts, with no signature or liveness claim."""
    explicit = getattr(args, 'fleet_observations', None)
    path = Path(explicit).expanduser().absolute() if explicit else home / 'fleet' / 'inventory-observations.json'
    document, raw = r.read_model(path, 'fleet_observations', missing=explicit is None)
    if document is None:
        return dict(status='unavailable', complete=False, rows=[], total_rows=0, next_offset=None, bytes_read=0,
                    basis='No recorded fleet inventory projection is available.')
    c.fields(document, ('schema_version', 'desired_revision', 'observations'), family='fleet_observations', versions=(1,))
    revision, observations = document['desired_revision'], document['observations']
    if not isinstance(revision, str) or not r.SHA.fullmatch(revision) or not isinstance(observations, list) or len(observations) > r.BINDINGS:
        c.fail('fleet_observations.invalid', 'Expected a bounded dated observation snapshot and exact desired revision.', 4)
    rows = []
    for row in observations:
        c.fields(row, ('device', 'observed_at', 'desired_revision', 'scope', 'agent', 'skill', 'repository', 'payload_digest', 'outcome'),
                 family='fleet_observations')
        c.skill_id(row['device'])
        r.qualified(row['skill'], 'fleet_observations')
        r.repository(row['repository'], 'fleet_observations')
        date = row['observed_at']
        try:
            if not isinstance(date, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', date):
                raise ValueError()
            datetime.fromisoformat(date)
        except ValueError:
            c.fail('fleet_observations.invalid', 'Observation dates must be UTC timestamps.', 4)
        if (not isinstance(row['desired_revision'], str) or not r.SHA.fullmatch(row['desired_revision'])
                or row['scope'] not in ('project', 'user') or row['agent'] not in (*c.ADAPTERS, None)
                or row['outcome'] not in ('installed', 'not_applicable', 'blocked', 'unknown')
                or row['payload_digest'] is not None and (not isinstance(row['payload_digest'], str) or not r.SHA.fullmatch(row['payload_digest']))):
            c.fail('fleet_observations.invalid', 'Invalid receipt scope, outcome or digest.', 4)
        if row['skill'] == args.id and sources.same(row['repository'], repository) and all(
                getattr(args, key, None) in (None, row[key]) for key in ('agent', 'scope')):
            rows.append(dict(row, status='stale_receipt' if row['desired_revision'] != revision else 'recorded_receipt',
                             host_load='not_verified'))
    rows.sort(key=lambda row: (row['device'], row['scope'], row['agent'] or '', row['observed_at']))
    if r.regular_bytes(path, r.MODEL_BYTES) != raw:
        c.fail('state.drift', 'Fleet observations changed during inspection; retry.', 4)
    return dict(status='recorded', complete=False,
                desired_revision=revision, rows=rows[offset:offset + limit], total_rows=len(rows),
                next_offset=offset + limit if offset + limit < len(rows) else None, bytes_read=2 * len(raw),
                basis='Dated recorded observations. Device coverage, live status and receipt signatures were not verified.')


def pagination(args):
    limit, offset = getattr(args, 'limit', 100), getattr(args, 'offset', 0)
    if not 1 <= limit <= 1000 or offset < 0:
        c.fail('invocation.invalid', 'Use limit 1–1000 and a nonnegative offset.', 2)
    return limit, offset


def page_impact(impact, limit, offset):
    rows = impact['deployments']
    page = rows[offset:offset + limit]
    identifiers = {row.get('comparison') for row in page}
    return dict(deployments=page, comparisons=[row for row in impact['comparisons'] if row['id'] in identifiers],
                total_rows=len(rows), next_offset=offset + limit if offset + limit < len(rows) else None)


def receipt_for(data):
    """Persist a report with numbered consumer labels and no machine paths or URLs."""
    impact = data.get('impact', dict(comparisons=[], deployments=[]))
    aliases, totals = {}, {}
    deployments = []
    for row in impact['deployments']:
        root, scope = row['root'], row['scope']
        if root not in aliases:
            totals[scope] = totals.get(scope, 0) + 1
            aliases[root] = f'{scope}-{totals[scope]}'
        item = {field: row[field] for field in ('scope', 'skill', 'status', 'comparison', 'before_agents', 'after_agents',
                                               'targets_changed', 'host_refresh_required', 'profile', 'profile_revision') if field in row}
        item['consumer'] = aliases[root]
        if row.get('error'):
            item['error_code'] = row['error']['code']
        deployments.append(item)
    comparisons = [{key: value for key, value in row.items() if key != 'error'} for row in impact['comparisons']]
    report = dict(plan_hash=data.get('plan_hash'), comparisons=comparisons, deployments=deployments, host_load='not_verified')
    return dict(schema_version=1, kind='update-impact', operation_id=c.digest(report), report=report)


def publish_report(value, content):
    """Publish a single explicit report atomically without replacing an existing file."""
    import os
    import tempfile
    path = Path(value).expanduser().absolute()
    c.parents_safe(Path(path.anchor), path)
    if c.kind(path.parent) != 'directory':
        c.fail('report.output', 'Select an existing unlinked output parent directory.', 4)
    if len(content.encode('utf-8')) > r.MODEL_BYTES:
        c.fail('report.limit', 'Report output exceeds 4 MiB. Narrow the selected query.', 4)
    parent = c.identity(path.parent)
    with tempfile.TemporaryDirectory(prefix='.mask-report-', dir=path.parent) as stage:
        temporary = Path(stage) / 'report'
        temporary.write_text(content, encoding='utf-8', newline='\n')
        c.parents_safe(Path(path.anchor), path)
        if c.identity(path.parent) != parent:
            c.fail('state.drift', 'The report output parent changed during publication.', 4)
        try:
            os.link(temporary, path)
        except FileExistsError:
            c.fail('report.collision', 'Report destination already exists and was preserved.', 4)
    return str(path)


def validate_receipt(receipt):
    """Validate only the shareable report shape, with no roots, endpoints or free-form payloads."""
    import mask_packages
    c.fields(receipt, ('schema_version', 'kind', 'operation_id', 'report'), family='report', versions=(1,))
    report = receipt['report']
    c.fields(report, ('plan_hash', 'comparisons', 'deployments', 'host_load'), family='report')
    if (receipt['kind'] != 'update-impact' or receipt['operation_id'] != c.digest(report) or report['host_load'] != 'not_verified'
            or not all(isinstance(report[name], list) for name in ('comparisons', 'deployments'))
            or report['plan_hash'] is not None and (not isinstance(report['plan_hash'], str) or not r.SHA.fullmatch(report['plan_hash']))):
        c.fail('report.invalid', 'The report receipt does not match its operation ID or supported result shape.', 4)
    identifiers = set()
    for row in report['comparisons']:
        c.fields(row, ('id', 'skill', 'before_commit', 'after_commit', 'kind', 'files'), family='report')
        r.qualified(row['skill'], 'report')
        if (not isinstance(row['id'], str) or not r.SHA.fullmatch(row['id']) or row['id'] in identifiers
                or row['kind'] not in ('content', 'metadata', 'provenance', 'selection', 'unavailable')
                or not isinstance(row['files'], list)
                or any(row[key] is not None and (not isinstance(row[key], str) or not r.OID.fullmatch(row[key])) for key in ('before_commit', 'after_commit'))):
            c.fail('report.invalid', 'Invalid exact comparison.', 4)
        identifiers.add(row['id'])
        for file in row['files']:
            c.fields(file, ('path', 'change', 'binary', 'before', 'after'), family='report')
            mask_packages.portable_path(file['path'])
            if file['change'] not in ('added', 'removed', 'modified') or type(file['binary']) is not bool:
                c.fail('report.invalid', 'Invalid file comparison.', 4)
            for side in ('before', 'after'):
                entry = file[side]
                if entry is not None:
                    c.fields(entry, ('size', 'sha256', 'mode'), family='report')
                    if (type(entry['size']) is not int or not 0 <= entry['size'] <= mask_packages.FILE_BYTES
                            or not isinstance(entry['sha256'], str) or not r.SHA.fullmatch(entry['sha256'])
                            or entry['mode'] not in ('100644', '100755')):
                        c.fail('report.invalid', 'Invalid file digest or mode.', 4)
    for row in report['deployments']:
        c.fields(row, ('consumer', 'scope', 'status'), ('skill', 'comparison', 'before_agents', 'after_agents', 'targets_changed',
                 'host_refresh_required', 'profile', 'profile_revision', 'error_code'), family='report')
        if (row['scope'] not in ('project', 'user') or not isinstance(row['consumer'], str)
                or not re.fullmatch(row['scope'] + r'-[1-9][0-9]*', row['consumer'])
                or row['status'] not in ('affected', 'pinned_unaffected', 'unchanged', 'ref_advanced_identical_payload',
                                         'profile_frozen_unaffected', 'development_link', 'blocked', 'skipped')
                or row.get('comparison') is not None and (not isinstance(row['comparison'], str) or row['comparison'] not in identifiers)):
            c.fail('report.invalid', 'Invalid deployment report row.', 4)
        if 'skill' in row:
            r.qualified(row['skill'], 'report')
        if 'profile' in row:
            c.skill_id(row['profile'])
        for field in ('before_agents', 'after_agents'):
            if field in row:
                r.strings(row[field], 'report', choices=set(c.ADAPTERS), empty=True)
        for field in ('targets_changed', 'host_refresh_required'):
            if field in row and type(row[field]) is not bool:
                c.fail('report.invalid', 'Invalid report target effect.', 4)
        if 'profile_revision' in row and (not isinstance(row['profile_revision'], str) or not r.SHA.fullmatch(row['profile_revision'])):
            c.fail('report.invalid', 'Invalid recorded profile revision.', 4)
        if 'error_code' in row and (not isinstance(row['error_code'], str) or not re.fullmatch(r'[a-z][a-z0-9_.]{1,80}', row['error_code'])):
            c.fail('report.invalid', 'Invalid report error code.', 4)
    return report


def inspect_receipt(args, output, home):
    value = args.operation
    path = home / 'reports' / (value[7:] + '.json') if r.SHA.fullmatch(value) else Path(value).expanduser().absolute()
    receipt, _ = r.read_model(path, 'report')
    report = validate_receipt(receipt)
    if r.SHA.fullmatch(value) and value != receipt['operation_id']:
        c.fail('report.invalid', 'The stored receipt does not match the requested operation ID.', 4)
    limit, offset = pagination(args)
    view = page_impact(report, limit, offset)
    view.update(operation_id=receipt['operation_id'], plan_hash=report['plan_hash'], host_load='not_verified')
    format_name = getattr(args, 'format', 'text')
    if format_name not in ('text', 'json', 'html'):
        c.fail('invocation.invalid', 'Choose report format text, json or html.', 2)
    output['data'] = dict(view=view, format=format_name, network='none')
    if getattr(args, 'output', None):
        output['data']['output'] = publish_report(args.output, render_receipt(view, format_name))
        output.update(changed=True, would_change=True, transaction='committed')


def report_lines(data):
    """A shared compact view of the typed report."""
    import unicodedata
    import mask_present as present
    def clean(value):
        return ''.join('?' if unicodedata.category(ch) == 'Cf' else ch for ch in present.clean(value))
    rows = data.get('deployments', [])
    total = data.get('total_rows', len(rows))
    lines = [f"Update impact · {len(rows)} of {total} deployment rows"]
    for row in rows:
        lines.append('  ' + ' · '.join(clean(row.get(key)) for key in ('skill', 'status', 'consumer' if 'consumer' in row else 'root')))
        if row.get('targets_changed'):
            lines.append(f"    targets {clean(row.get('before_agents'))} → {clean(row.get('after_agents'))}")
        if row.get('host_refresh_required'):
            lines.append('    Refresh agent discovery for the changed content or targets.')
        if row.get('status') == 'development_link':
            lines.append('    Edits to the shared authoring checkout are visible through its links. Running agents may cache instructions.')
        if row.get('error_code') or row.get('error'):
            lines.append('    ' + clean(row.get('error_code') or row['error']['code']))
    for comparison in data.get('comparisons', []):
        files = comparison.get('files') or []
        if not isinstance(files, list):
            continue
        lines.append(f"  {clean(comparison.get('skill'))} · {clean(comparison.get('kind'))} · {len(files)} changed files")
        for item in files[:5]:
            if isinstance(item, dict):
                lines.append(f"    {clean(item.get('change'))} {clean(item.get('path'))}")
    if data.get('next_offset') is not None:
        lines.append(f"  More deployment rows follow. Continue with --offset {clean(data['next_offset'])}.")
    return lines


def render_receipt(view, format_name):
    import html
    import json
    if format_name == 'json':
        return json.dumps(view, ensure_ascii=True, sort_keys=True, indent=2) + '\n'
    content = '\n'.join(report_lines(view)) + '\n'
    if format_name == 'html':
        return ('<!doctype html>\n<html lang="en"><meta charset="utf-8"><title>MASK update impact</title>\n'
                '<h1>MASK update impact</h1><pre>' + html.escape(content) + '</pre>\n</html>\n')
    return content
