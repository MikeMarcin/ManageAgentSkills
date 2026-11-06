"""Prepare an exact curated Git commit without modifying the authoring checkout."""
from __future__ import annotations

import mask_control as control
import mask_core as c
import mask_packages as packages
import mask_provenance as provenance
import mask_resolve as resolve
import mask_sources as sources


def prepare(home, config, upstream, destination, scratch):
    if not destination or destination == upstream['source']:
        c.fail('fleet.copy_destination_required', 'Use --into with a separate approved curated tap.', 4)
    entry = sources.selected(config, destination)
    if sources.same(entry['repository'], upstream['repository']):
        c.fail('fleet.copy_destination_required', 'The curated tap must name a separate repository.', 4)
    root, target, observed = provenance.destination(config, destination, upstream['id'], new=True)
    parent, path = observed['head'], observed['path']
    branch = 'refs/heads/' + sources.authoring_branch(root, entry['ref'])
    resolve.ref(branch, 'fleet')
    mapping = sources.exact_entry(root, parent, 'mask-source.json')
    index = sources.source_index(root, {'mask-source.json': mapping} if mapping else {})
    if index is not None and index['packages'].get(upstream['id']) != path or index is None and path != (
            entry['packages'] + '/' if entry['packages'] != '.' else '') + upstream['id']:
        c.fail('source.publish_index_required', 'The selected curated destination requires its committed package mapping.', 4)
    if sources.exact_entry(root, parent, 'SKILL.md') is not None or any(
            sources.exact_entry(root, parent, '/'.join(path.split('/')[:depth]) + '/SKILL.md')
            for depth in range(1, len(path.split('/')))):
        c.fail('source.path_ambiguous', 'The curated destination would nest inside an existing package.', 4)
    tree = sources.tree_entries(root, parent)
    if any(part.casefold() == path.casefold() or part.casefold().startswith(path.casefold() + '/') for part in tree):
        c.fail('import.collision', 'The committed curated destination is occupied.', 4)
    source = sources.selected(config, upstream['source'])
    cache = sources.cached(home, upstream['source'], source)
    payload = resolve.verify_resolution(home, upstream['source'], source, upstream)
    if any(item.path.split('/')[0].casefold() in (provenance.RECORD, provenance.NOTICES) for item in payload.files):
        c.fail('import.provenance_collision', 'Upstream payload occupies a reserved import path.', 4)
    notices, mappings = provenance.notice_files(cache, payload)
    files = list(payload.files) + notices
    record = provenance.record_for(payload, upstream, destination, observed, files, mappings)
    raw = c.text_json(record).encode()
    if len(raw) > provenance.RECORD_BYTES:
        c.fail('provenance.limit', 'Curated provenance exceeds its byte limit.', 4)
    files.append(packages.PayloadFile(provenance.RECORD, '100644', raw))
    provenance.bounded_manifest(files)
    object_format = 'sha256' if len(parent) == 64 else 'sha1'
    c.git(scratch, '-c', 'init.templateDir=', 'init', '--bare', '--object-format=' + object_format, mutating=True)
    c.git(scratch, '-c', 'protocol.allow=never', '-c', 'protocol.file.allow=always', 'fetch',
          '--no-tags', '--no-recurse-submodules', '--depth=1', root.as_uri(), parent, mutating=True)
    if c.git(scratch, 'rev-parse', 'FETCH_HEAD^{commit}') != parent:
        c.fail('fleet.copy_parent_changed', 'Curated authoring parent changed while constructing the exact commit.', 4)
    c.git(scratch, 'read-tree', parent, mutating=True)
    for item in sorted(files, key=lambda item: item.path):
        oid = c.git(scratch, 'hash-object', '-w', '--stdin', input=item.data, mutating=True)
        c.git(scratch, 'update-index', '--add', '--cacheinfo', item.mode, oid, path + '/' + item.path, mutating=True)
    tree_oid = c.git(scratch, 'write-tree', mutating=True)
    timestamp = int(c.git(scratch, 'show', '-s', '--format=%ct', parent))
    author = f'MASK fleet <mask@mask.invalid> {timestamp} +0000'
    commit_data = (f'tree {tree_oid}\nparent {parent}\nauthor {author}\ncommitter {author}\n'
                   f'\nImport exact MASK skill {upstream["id"]}\n').encode()
    commit = c.git(scratch, 'hash-object', '-w', '-t', 'commit', '--stdin', input=commit_data, mutating=True)
    row = dict(source=destination, id=upstream['id'], repository=sources.repository(entry['repository']),
               path=path, commit=commit, git_object_format=object_format, selector={'ref': branch})
    row.update(resolve.payload_digests(resolve.frozen_payload(scratch, row)))
    effect = dict(source=destination, repository=row['repository'], ref=branch, parent=parent, commit=commit, path=path)
    endpoint = dict(repository=control.endpoint(entry['transport']))
    tip = remote_tip(scratch, endpoint, effect)
    if tip not in (parent, commit):
        c.fail('fleet.copy_parent_changed', 'Curated branch differs from the approved authoring parent and exact prepared commit.', 4)
    return row, effect, endpoint, observed


def remote_tip(scratch, endpoint, effect):
    raw = control.network(scratch, endpoint, 'ls-remote', '--refs', endpoint['repository'], effect['ref'], max_output=1024)
    commit, separator, ref = raw.partition('\t')
    return commit if separator and ref == effect['ref'] else None


def publish(config, scratch, row, effect, endpoint, observed):
    _, _, latest = provenance.destination(config, effect['source'], row['id'], new=True)
    if latest != observed:
        c.fail('plan.stale', 'Curated checkout, destination or index changed during preparation.', 4)
    tip = remote_tip(scratch, endpoint, effect)
    if tip == effect['commit']:
        return 'already_published'
    if tip != effect['parent']:
        c.fail('fleet.copy_parent_changed', 'Curated branch advanced before publication.', 4)
    try:
        control.network(scratch, endpoint, 'push', '--porcelain', '--no-follow-tags',
                        '--force-with-lease=' + effect['ref'] + ':' + effect['parent'], endpoint['repository'],
                        effect['commit'] + ':' + effect['ref'], mutating=True)
    except c.MaskError:
        if remote_tip(scratch, endpoint, effect) != effect['commit']:
            c.fail('fleet.copy_publication_unknown', 'The exact curated commit is not confirmed at the approved ref. Re-preview before retrying.', 4)
    return 'published'
