"""Observational reconciliation plans and bounded, owned filesystem effects."""
from __future__ import annotations

import copy
import os
from pathlib import Path

import mask_core as c


def link_value(path):
    observed = c.kind(path)
    return dict(type=observed, link_text=os.readlink(path) if observed == 'symlink' else None)


def normalized_link(path, raw):
    return Path(os.path.abspath(path.parent / raw))


def plan(config, state, roots, *, proposals=None, register=(), unregister=(), keep_links=False, candidate=None, operation='apply'):
    proposals = proposals or {}
    source = Path(config['source']['root'])
    after = copy.deepcopy(state)
    links, files, actions, blockers, observations, packages = [], [], [], [], [], {}
    revision = candidate['revision'] if candidate else c.git(source, 'rev-parse', 'HEAD', optional=True)
    dirty = bool(c.git(source, 'status', '--porcelain', '--untracked-files=all', optional=True)) if source.is_dir() else False
    for root in sorted(roots, key=str):
        key = str(root)
        record = state['projects'].get(key)
        try:
            if record is None and key not in register:
                c.fail('project.not_registered', 'Project is not registered.', 4, root=key)
            if key in unregister and keep_links:
                after['projects'].pop(key, None)
                actions.extend(dict(kind='link.abandon', status='planned', path=str(root / rel)) for rel in record['links'])
                observations.append(dict(root=key, abandoned=record))
                continue
            if record:
                c.registered_root(root, record)
            elif not root.is_dir():
                c.fail('project.unavailable', 'Project is unavailable.', 4, root=key)
            before_text = c.read_text(root / '.mask.json', 'manifest')
            current = c.manifest(c.parse_json(before_text, 'manifest'))
            desired = c.manifest(proposals.get(key, current))
            old_links = record['links'] if record else {}
            expected = {}
            if key not in unregister:
                for identifier in desired['skills']:
                    if identifier not in packages:
                        packages[identifier] = candidate['packages'][identifier] if candidate else c.package(source, identifier)
                    for target in desired.get('targets', config['default_targets']):
                        relative = f'{c.ADAPTERS[target]}/{identifier}'
                        expected[relative] = dict(skill=identifier, target=target, link_text=str(source / 'skills' / identifier))
            next_record = copy.deepcopy(record) if record else c.registry_record(root, desired, source)
            next_record['links'] = {}
            leaves = []
            for relative in sorted(set(old_links) | set(expected)):
                leaf = root / relative
                c.parents_safe(root, leaf)
                actual = link_value(leaf)
                leaves.append(dict(relative=relative, **actual))
                old = old_links.get(relative)
                wanted = expected.get(relative)
                if actual['type'] not in ('missing', 'symlink'):
                    c.fail('target.collision', 'A real or special entry occupies the target.', 4, path=str(leaf), existing_type=actual['type'])
                if old and normalized_link(leaf, old['link_text']) != source / 'skills' / old['skill']:
                    c.fail('state.invalid', 'Ownership value does not name the configured source.', path=str(leaf))
                if actual['type'] == 'symlink':
                    if old is None:
                        c.fail('target.unmanaged_link', 'A symlink has no ownership record; inspect explicit adoption.', 4, path=str(leaf))
                    if actual['link_text'] != old['link_text']:
                        c.fail('target.drift', 'Owned link changed since it was recorded.', 4, path=str(leaf))
                before = actual['link_text'] if actual['type'] == 'symlink' else None
                if wanted:
                    after_raw = old['link_text'] if old else wanted['link_text']
                    next_record['links'][relative] = dict(wanted, link_text=after_raw)
                else:
                    after_raw = None
                if before != after_raw:
                    entry = dict(root=key, relative=relative, skill=(wanted or old)['skill'], target=(wanted or old)['target'], before=before, after=after_raw)
                    links.append(entry)
                    actions.append(dict(kind='link.create' if after_raw else 'link.remove', status='planned', path=str(leaf), skill=entry['skill'], target=entry['target'], source=after_raw))
            observations.append(dict(root=key, identity=c.identity(root), manifest=desired, manifest_bytes=c.digest(before_text.encode()), leaves=leaves))
            if key in unregister:
                after['projects'].pop(key, None)
            else:
                next_record.update(last_manifest=desired, last_manifest_digest=c.digest(desired), last_source_revision=revision)
                after['projects'][key] = next_record
            if desired != current:
                files.append(dict(root=key, before=before_text, after=c.text_json(desired)))
                actions.append(dict(kind='manifest.write', status='planned', path=str(root / '.mask.json')))
        except c.MaskError as error:
            blockers.append(error.as_dict())
    if after != state:
        actions.append(dict(kind='state.record', status='planned'))
        after['generation'] = state['generation'] + 1
    source_data = dict(root=str(source), revision=revision, dirty=dirty,
                       fingerprint=c.digest({key: value['fingerprint'] for key, value in sorted(packages.items())}))
    payload = dict(protocol=1, adapters=c.ADAPTERS, operation=operation, config=config, generation=state['generation'],
                   state=state, observations=observations, source=source_data, links=links, manifests=files,
                   register=sorted(register), unregister=sorted(unregister), keep_links=keep_links)
    if candidate:
        payload['transition'] = candidate.get('transition')
    return dict(applicable=not blockers, blockers=blockers, plan_hash=c.digest(payload), source=source_data,
                projects=observations, actions=actions, would_change=bool(actions),
                intent=dict(operation=operation, selected=[str(root) for root in roots], links=links, manifests=files,
                            before_state=state, after_state=after, config=config))


def public_plan(planned, output):
    output['data'] = {key: value for key, value in planned.items() if key not in ('intent', 'actions', 'would_change')}
    output['actions'] = planned['actions']
    output['would_change'] = planned['would_change']
    if planned['source']['dirty']:
        output['warnings'].append(dict(code='source.dirty', message='Local authoring changes are included in the source fingerprint.'))
    if not planned['projects'] and not planned['blockers']:
        output['warnings'].append(dict(code='project.empty_registry', message='No registered projects selected.'))


def ensure_applicable(planned, expected=None):
    if expected is not None and expected != planned['plan_hash']:
        c.fail('plan.stale', 'Plan inputs changed; inspect and preview again.', 4)
    if planned['blockers']:
        first = planned['blockers'][0]
        raise c.MaskError(first['code'], first['message'], 4, details=first['details'])
