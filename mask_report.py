"""Read-only legacy inventory from declarations, ownership and selected leaves."""
from __future__ import annotations

from pathlib import Path

import mask_core as c
import mask_fs as fs


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
        if '/' not in args.id or args.id.count('/') != 1:
            c.fail('invocation.invalid', 'Use the source-qualified legacy/ID form.', 2)
        alias, identifier = args.id.split('/')
        c.skill_id(identifier)
        if alias != 'legacy':
            c.fail('source.unknown', 'Only the configured legacy source is currently supported.', 4)
        if getattr(args, 'scope', None) not in (None, 'project', 'user') or getattr(args, 'agent', None) not in (None, *c.ADAPTERS):
            c.fail('invocation.invalid', 'Choose a supported scope and agent.', 2)
    if inverse or getattr(args, 'all', False):
        roots = sorted(records)
    elif getattr(args, 'user', False):
        if not state.get('user'):
            c.fail('user.not_registered', 'User scope is not registered.', 4)
        roots = [state['user']['root']]
    else:
        selection = getattr(args, 'project', None)
        root = Path(selection).expanduser().resolve() if selection else c.project_root()
        if str(root) not in records:
            c.fail('project.not_registered', 'Inventory requires a registered consumer.', 4)
        roots = [str(root)]
    rows, consumers, observations = [], [], []
    counts = dict(declarations_read=0, declaration_bytes_read=0, payload_files_read=0, directories_enumerated=0, leaves_inspected=0)
    source = c.legacy_source(config)
    for key in roots:
        scope = c.consumer_scope(state, key)
        if getattr(args, 'scope', None) not in (None, scope):
            continue
        root, record = Path(key), records[key]
        if record.get('mode') in ('pinned', 'dev-link'):
            consumers.append(dict(root=key, scope=scope, available=root.is_dir(), declaration_basis='cached_pinned_selection', error=dict(code='inventory.pinned_unsupported', message='Pinned inventory detail awaits the reporting implementation.'), mode=record['mode'], reproducible=record['mode']=='pinned', fleet_eligible=record['mode']=='pinned'))
            continue
        if source is None:
            # A legacy record on a tap catalog machine has no live checkout to compare its links with.
            consumers.append(dict(root=key, scope=scope, available=root.is_dir(), declaration_basis='cached_declaration',
                                  error=c.MaskError('migration.required', 'Legacy consumer ownership has no live checkout on a tap catalog machine; migrate it first.', 4, details=dict(root=key)).as_dict()))
            continue
        declaration = record['last_manifest']
        basis, consumer_error = 'live_declaration', None
        available = True
        try:
            c.registered_root(root, record, scope)
        except c.MaskError as error:
            available, consumer_error, basis = False, error.as_dict(), 'cached_declaration'
        if available:
            path = c.declaration_path(root, scope, home)
            try:
                raw = c.read_text(path, 'manifest')
                counts['declarations_read'] += 1
                counts['declaration_bytes_read'] += len(raw.encode('utf-8'))
                declaration = c.manifest(c.parse_json(raw, 'manifest'))
                observations.append((path, raw))
            except c.MaskError as error:
                consumer_error, basis = error.as_dict(), 'cached_declaration'
        consumers.append(dict(root=key, scope=scope, available=available, declaration_basis=basis, error=consumer_error))
        desired = {f'{c.ADAPTERS[agent]}/{skill}': (skill, agent)
                   for skill in declaration['skills'] for agent in declaration.get('targets', config['default_targets'])}
        leaves = dict(desired)
        for relative, owned in record['links'].items():
            leaves[relative] = (owned['skill'], owned['target'])
        if getattr(args, 'include_unmanaged', False) and available:
            for agent, relative in c.ADAPTERS.items():
                directory = root / relative
                try:
                    c.parents_safe(root, directory / 'mask-inventory-check')
                    if c.kind(directory) == 'directory':
                        counts['directories_enumerated'] += 1
                        for leaf in directory.iterdir():
                            leaves.setdefault(f'{relative}/{leaf.name}', (leaf.name, agent))
                except c.MaskError as error:
                    consumers[-1].setdefault('discovery_errors', []).append(error.as_dict())
        for relative, (skill, agent) in sorted(leaves.items()):
            if identifier is not None and skill != identifier or getattr(args, 'agent', None) not in (None, agent):
                continue
            owned = record['links'].get(relative)
            wanted = relative in desired and basis == 'live_declaration'
            actual, error = dict(type='unknown', link_text=None), None
            if available:
                try:
                    leaf = root / relative
                    c.parents_safe(root, leaf)
                    actual = fs.link_value(leaf)
                    counts['leaves_inspected'] += 1
                except c.MaskError as caught:
                    error = caught.as_dict()
            if not available:
                status = 'unavailable_consumer'
            elif error or consumer_error:
                status = 'blocked'
            elif owned:
                matches = (actual['type'] == 'symlink' and actual['link_text'] == owned['link_text']
                           and fs.normalized_link(root / relative, owned['link_text']) == source / 'skills' / skill
                           and c.kind(source / 'skills' / skill) == 'directory')
                status = 'managed_converged' if matches and wanted else 'managed_drifted'
            elif actual['type'] != 'missing':
                status = 'unmanaged_present'
            else:
                status = 'declared_not_deployed'
            rows.append(dict(skill='legacy/' + skill if wanted or owned else None, name=skill,
                             source=dict(alias='legacy', root=str(source), repository=None) if wanted or owned else None,
                             package_path='skills/' + skill if wanted or owned else None,
                             artifact=None, recorded_source_revision=record['last_source_revision'] if owned else None,
                             content_mode='legacy_unpinned' if wanted or owned else 'unknown',
                             root=key, scope=scope, agent=agent, declared=wanted,
                             declaration_basis=basis, origin='local_declaration' if wanted else 'ownership' if owned else 'unmanaged',
                             owned=owned is not None, path=str(root / relative), actual=actual, status=status,
                             compatibility='unspecified', host_load='not_verified', error=error))
    for path, raw in observations:
        if c.read_text(path, 'manifest') != raw:
            c.fail('state.drift', 'A declaration changed during inventory; retry.', 4)
        counts['declaration_bytes_read'] += len(raw.encode('utf-8'))
    output['data'] = dict(rows=rows[offset:offset + limit], total_rows=len(rows),
                          next_offset=offset + limit if offset + limit < len(rows) else None,
                          consumers=consumers, source_mode='legacy', network='none',
                          scope='registered_local_consumers' if inverse or getattr(args, 'all', False) else 'selected_consumer',
                          complete=all(item['error'] is None and not item.get('discovery_errors') for item in consumers),
                          work=counts, limitations=['Legacy live-source content is not pinned.',
                                                  'Artifact, profile, fleet receipt and actual host-loading data are unavailable.'])
