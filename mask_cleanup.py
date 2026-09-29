"""Explicit, reference-aware garbage collection of verified MASK-owned data."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import stat

import mask_consent as consent
import mask_core as c
import mask_resolve as r
import mask_store as store


def tree(path):
    """A bounded no-follow snapshot; hard links and special entries are never disposable."""
    files, directories, size = {}, {}, 0
    pending = [path]
    while pending:
        node = pending.pop()
        c.parents_safe(Path(path.anchor), node)
        kind = c.kind(node)
        relative = node.relative_to(path).as_posix()
        if kind == 'directory':
            directories[relative] = c.identity(node)
            pending.extend(sorted(node.iterdir()))
        elif kind == 'file' and node.lstat().st_nlink == 1:
            observed = node.stat()
            size += observed.st_size
            if size > 2 * 1024**3:
                c.fail('cleanup.limit', 'Candidate exceeds the bounded cleanup inventory.', 4)
            digest = hashlib.sha256()
            with node.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(chunk)
            files[relative] = dict(identity=c.identity(node), size=observed.st_size, sha256='sha256:' + digest.hexdigest())
        else:
            c.fail('cleanup.preserved', 'Linked, special or unknown content is preserved.', 4, path=str(node))
        if len(files) + len(directories) > 100000:
            c.fail('cleanup.limit', 'Candidate contains too many entries.', 4)
    return dict(files=files, directories=directories, bytes=size)


def artifact(path):
    value = store.manifest(c.read_json(path / 'manifest.json', 'artifact'))
    if not path.name.startswith('.mask-stage-') and path.name != value['payload_digest'][7:]:
        c.fail('artifact.invalid', 'Artifact directory does not match its manifest.', 4)
    row = dict(source='cleanup', id=value['id'], repository='file:///mask-cleanup', path='.',
               commit='0' * 40, git_object_format='sha1', selector=dict(commit='0' * 40),
               **{key: value[key] for key in ('payload_digest','metadata_digest','provenance_digest') if key in value})
    store.verify_tree(path, row)
    return value['payload_digest']


def backup(path, snapshot):
    if not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', path.name):
        c.fail('cleanup.preserved', 'Unknown backup name.', 4)
    value = c.read_json(path / 'manifest.json', 'backup')
    c.fields(value, ('files',), family='backup', versions=())
    if not isinstance(value['files'], list) or not value['files']:
        c.fail('cleanup.preserved', 'Unknown backup manifest.', 4)
    expected = {'manifest.json'}
    directories = {'.'}
    for row in value['files']:
        c.fields(row, ('original', 'backup', 'sha256'), family='backup', versions=())
        original, destination = Path(row['original']), Path(row['backup'])
        if not original.is_absolute() or not destination.is_relative_to(path):
            c.fail('cleanup.preserved', 'Backup paths do not belong to this transaction.', 4)
        relative = destination.relative_to(path).as_posix()
        if relative in expected or snapshot['files'].get(relative, {}).get('sha256') != row['sha256']:
            c.fail('cleanup.preserved', 'Backup content changed; preserve it.', 4)
        expected.add(relative)
        directories.update(parent.as_posix() for parent in Path(relative).parents)
    if set(snapshot['files']) != expected or set(snapshot['directories']) != directories:
        c.fail('cleanup.preserved', 'Backup contains unknown content.', 4)


def plan(home):
    if c.kind(home / 'pending.json') != 'missing':
        c.fail('recovery.required', 'Recover pending work before cleanup; all recovery data is preserved.', 8)
    state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
    config = c.config(c.read_json(home / 'config.json'))
    referenced, sources, controls = set(), set(), {}
    roots = []
    for key, record in c.consumer_records(state).items():
        root = Path(key)
        scope = c.consumer_scope(state, root)
        c.registered_root(root, record, scope)
        roots.append(root)
        for lock in (record.get('last_lock'), c.read_json(r.lock_path(root, scope, home), 'lock', default={})):
            if lock:
                for row in r.lock(lock)['packages']:
                    referenced.add(row['payload_digest'])
                    sources.add(row['source'])
        for control in (c.declaration_path(root, scope, home), r.lock_path(root, scope, home)):
            controls[str(control)] = c.read_text(control, missing=True)
    # Personal declarations remain useful even after unregistering them.
    for row in c.read_json(home / 'user.lock.json', 'lock', default={}).get('packages', []):
        referenced.add(row['payload_digest'])
        sources.add(row['source'])
    candidates, preserved = [], []
    def consider(path, kind, verify):
        try:
            snapshot = tree(path)
            verify(path, snapshot)
            candidates.append(dict(path=str(path), kind=kind, bytes=snapshot['bytes'], snapshot=snapshot))
        except (c.MaskError, OSError, ValueError, KeyError, TypeError) as error:
            preserved.append(dict(path=str(path), reason=str(error)))
    base = home / 'store/v1'
    if c.kind(base) == 'directory':
        for path in sorted(base.iterdir()):
            if 'sha256:' + path.name in referenced:
                continue
            if re.fullmatch(r'[0-9a-f]{64}', path.name) or path.name.startswith('.mask-stage-'):
                def verify(path, snapshot):
                    if artifact(path) in referenced and not path.name.startswith('.mask-stage-'):
                        c.fail('cleanup.preserved', 'Referenced artifact.', 4)
                consider(path, 'artifact', verify)
            else:
                preserved.append(dict(path=str(path), reason='Unknown store entry.'))
    base = home / 'backups'
    if c.kind(base) == 'directory':
        for path in sorted(base.iterdir()):
            consider(path, 'backup', backup)
    base = home / 'sources'
    if c.kind(base) == 'directory':
        retained = {Path(entry['cache']) for entry in config['sources'].values()}
        for path in sorted(base.iterdir()):
            if path in retained:
                continue
            def verify_cache(path, snapshot):
                import mask_sources
                marker = c.read_json(path / 'mask-source.json', 'source')
                match = re.fullmatch(r'(.+)-[0-9a-f]{16}\.git', path.name)
                if set(marker) != {'schema_version','repository','identity'} or marker['schema_version'] != 1 or marker['identity'] != c.identity(path) or not isinstance(marker['repository'], str) or not match:
                    c.fail('cleanup.preserved', 'Source ownership is unknown.', 4)
                alias = match[1]
                mask_sources.alias(alias)
                if path != mask_sources.cache_path(home, alias, marker['repository']) or alias in sources:
                    c.fail('cleanup.preserved', 'Source cache identity is unknown or still referenced.', 4)
                mask_sources.repository(marker['repository'])
                mask_sources.cached_refs(path, marker)
                known_file = re.compile(r'(?:HEAD|config|description|packed-refs|mask-source\.json|mask-refs\.json|mask-transport\.json|FETCH_HEAD|shallow|info/(?:exclude|refs)|hooks/[a-z-]+\.sample|objects/(?:[0-9a-f]{2}/[0-9a-f]{38,62}|pack/pack-[0-9a-f]{40,64}\.(?:pack|idx|rev|bitmap)|info/(?:packs|commit-graph))|refs/.+)')
                directories = {'.', 'objects', 'objects/pack', 'objects/info', 'refs', 'refs/heads', 'refs/tags', 'hooks', 'info'}
                for relative in snapshot['files']:
                    directories.update(parent.as_posix() for parent in Path(relative).parents)
                if any(not known_file.fullmatch(relative) for relative in snapshot['files']) or set(snapshot['directories']) - directories:
                    c.fail('cleanup.preserved', 'Source cache contains unknown files.', 4)
                if c.git(path, 'rev-parse', '--is-bare-repository') != 'true':
                    c.fail('cleanup.preserved', 'Not an owned bare cache.', 4)
            consider(path, 'source-cache', verify_cache)
    if c.kind(home / 'staging') == 'directory':
        preserved.extend(dict(path=str(path), reason='No surviving setup ownership journal; preserve unknown staging.') for path in sorted((home / 'staging').iterdir()))
    # Generated retired files have an explicit package declaration and a complete
    # replacement. Current .mask.lock.json and native-role locks never qualify.
    if roots:
        import mask_fs
        planned = mask_fs.plan(config, state, roots, home=home, retire_files=True)
        if planned['blockers']:
            preserved.extend(dict(path=item.get('details', {}).get('root', ''), reason=item['message']) for item in planned['blockers'])
        for entry in planned['intent'].get('retired_files', []):
            path = Path(entry['root']) / entry['relative']
            consider(path, 'retired-file', lambda path, snapshot: None)
    return dict(candidates=candidates, preserved=preserved, plan_hash=c.digest(dict(state=state, config=config, controls=controls, candidates=candidates)),
                reclaimable_bytes=sum(row['bytes'] for row in candidates))


def remove(row, removed):
    path, expected = Path(row['path']), row['snapshot']
    if tree(path) != expected:
        c.fail('plan.stale', 'Cleanup candidate changed; review again.', 4, path=str(path))
    # Unlink only the exact inventoried entries. Unknown entries prevent rmdir;
    # no recursive deletion ever follows a substituted link.
    for relative, observed in expected['files'].items():
        leaf = path if relative == '.' else path / relative
        c.parents_safe(Path(path.anchor), leaf)
        if c.kind(leaf) != 'file' or c.identity(leaf) != observed['identity'] or c.digest(leaf.read_bytes()) != observed['sha256']:
            c.fail('plan.stale', 'Cleanup file changed; remaining content was preserved.', 4, path=str(leaf))
        if os.name == 'nt':
            leaf.chmod(leaf.stat().st_mode | stat.S_IWRITE)
        leaf.unlink()
        removed['files'] += 1
    for relative, identity in sorted(expected['directories'].items(), key=lambda item: len(Path(item[0]).parts), reverse=True):
        directory = path if relative == '.' else path / relative
        c.parents_safe(Path(path.anchor), directory)
        if c.kind(directory) != 'directory' or c.identity(directory) != identity:
            c.fail('plan.stale', 'Cleanup directory changed.', 4, path=str(directory))
        directory.rmdir()
        removed['directories'] += 1


def dispatch(args, output, home):
    candidate = plan(home)
    output['data'] = {key: value for key, value in candidate.items() if key != 'candidates'}
    output['data']['candidates'] = [{key: value for key, value in row.items() if key != 'snapshot'} for row in candidate['candidates']]
    output['actions'] = [dict(kind='cleanup.remove', status='planned', path=row['path'], bytes=row['bytes']) for row in candidate['candidates']]
    output['would_change'] = bool(candidate['candidates'])
    expected = getattr(args, 'expect_plan_hash', None)
    if expected is not None and expected != candidate['plan_hash']:
        c.fail('plan.stale', 'Cleanup references or candidates changed; review again.', 4)
    proposal = dict(kind='task', reason='cleanup.delete', scope=[str(home)], actions=output['actions'], plan_hash=candidate['plan_hash'], question='Delete these unused files and backups?', granted_by=None)
    output['data']['review'] = proposal
    if output['dry_run'] or not candidate['candidates']:
        return
    if expected is None:
        if not consent.interactive(args):
            c.fail('confirmation.required', 'Preview cleanup with --dry-run, then use --approve-plan HASH.', 4)
        import mask_present
        if not consent.ask(proposal, mask_present.render_confirmation(proposal, output)):
            c.fail('confirmation.declined', 'Cleanup declined; nothing was deleted.', 4)
    with c.writer_lock(home):
        if plan(home)['plan_hash'] != candidate['plan_hash']:
            c.fail('plan.stale', 'Cleanup references changed during review; nothing was deleted.', 4)
        for row, action in zip(candidate['candidates'], output['actions']):
            removed = dict(files=0, directories=0)
            try:
                remove(row, removed)
            except BaseException:
                output['changed'] |= any(removed.values())
                output['transaction'] = 'partial' if output['changed'] else 'not_started'
                action.update(status='partial' if any(removed.values()) else 'refused', removed=removed)
                raise
            action['status'] = 'applied'
            output.update(changed=True, transaction='committed')
