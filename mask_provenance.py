"""Explicit copy imports and bounded, independently qualified provenance."""
from __future__ import annotations

import copy
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
import unicodedata

import mask_core as c
import mask_git as g
import mask_packages as p
import mask_sources as s

RECORD = '.mask-provenance.json'
NOTICES = '.mask-notices'
RECORD_BYTES = 1024 * 1024


def regular_bytes(path, limit):
    c.parents_safe(Path(path.anchor), path)
    if c.kind(path) != 'file':
        c.fail('import.entry_invalid', 'Expected a regular unlinked file.', 4)
    before = path.lstat()
    if before.st_size > limit:
        c.fail('skill.limit', 'File exceeds the selected byte limit.', 4)
    descriptor = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_BINARY', 0))
    with os.fdopen(descriptor, 'rb') as handle:
        actual = os.fstat(handle.fileno())
        if not stat.S_ISREG(actual.st_mode) or c.reparse(actual) or (actual.st_dev, actual.st_ino) != (before.st_dev, before.st_ino):
            c.fail('import.entry_invalid', 'File identity changed before reading.', 4)
        data = handle.read(limit + 1)
    if len(data) > limit:
        c.fail('skill.limit', 'File exceeds the selected byte limit.', 4)
    after = path.lstat()
    if any(getattr(before, key) != getattr(after, key) for key in ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')):
        c.fail('import.entry_invalid', 'File changed while it was being read.', 4)
    return data


def source_path(root, entry, identifier, *, existing=False):
    index_path = root / 'mask-source.json'
    raw = regular_bytes(index_path, RECORD_BYTES) if c.kind(index_path) != 'missing' else None
    if raw is not None:
        index = s.validate_index(c.parse_json(raw, 'source'))
        if identifier not in index['packages']:
            c.fail('import.index_required', 'Add the desired package path to the source index before importing.', 4, skill=identifier)
        path = index['packages'][identifier]
        others = [value for key, value in index['packages'].items() if key != identifier]
        if any(path == other or path == '.' or other == '.' or path.startswith(other + '/') or other.startswith(path + '/') for other in others):
            c.fail('source.path_ambiguous', 'Destination index has overlapping package roots.', 4)
    elif existing and c.kind(root / 'SKILL.md') == 'file':
        try:
            text = regular_bytes(root / 'SKILL.md', RECORD_BYTES).decode('utf-8')
        except UnicodeError:
            c.fail('skill.invalid', 'Root SKILL.md requires UTF-8 text.', 4)
        c.metadata(text, identifier)
        path = '.'
    else:
        path = (entry['packages'] + '/' if entry['packages'] != '.' else '') + identifier
    if path != '.':
        p.portable_path(path)
        p.passive_path(path.split('/'))
    return path, c.digest(raw) if raw is not None else None


def authoring_checkout(config, name):
    """A tap's approved authoring checkout and its HEAD; observational.

    The branch comes first, so another branch or a detached HEAD refuses the same way whether or not the checkout has an origin (MASK-0108).
    """
    entry = s.selected(config, name)
    if entry['authoring'] is None:
        c.fail('import.authoring_required', 'The destination source needs an approved authoring checkout.', 4)
    root = Path(entry['authoring'])
    c.parents_safe(Path(root.anchor), root)
    c.checkout(root)
    branch = s.authoring_branch(root, entry['ref'])
    origin = c.git(root, 'remote', 'get-url', 'origin', optional=True)
    if origin is None:
        if s.repository(str(root)) != entry['repository']:
            c.fail('source.identity_mismatch', 'Authoring checkout does not match its approved local identity.', 4)
        head = c.git(root, 'rev-parse', '--verify', 'HEAD^{commit}')
        for marker in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply'):
            marker_path = Path(c.git(root, 'rev-parse', '--path-format=absolute', '--git-path', marker))
            if c.kind(marker_path) != 'missing':
                c.fail('source.dirty', 'An in-progress Git operation blocks imports.', 4)
    else:
        observed = g.checkout_preconditions(root, 'origin', branch, timeout=config['git_timeout_seconds'], clean=False)
        # The authoring checkout's identity is its origin normalized to the approved tap repository.
        if s.repository(origin) != entry['repository']:
            c.fail('source.identity_mismatch', 'Configured remote differs from its approved repository.', 4)
        s.endpoint(root, origin, entry['repository'])
        head = observed['revision']
    return entry, root, head


def destination(config, name, identifier, *, new=False):
    entry, root, head = authoring_checkout(config, name)
    path, index_digest = source_path(root, entry, identifier, existing=not new)
    target = root / path
    c.parents_safe(root, target)
    current = root
    for part in (() if path == '.' else path.split('/')):
        if c.kind(current) == 'directory':
            for count, sibling in enumerate(current.iterdir(), 1):
                if count > p.FILE_COUNT:
                    c.fail('source.limit', 'Destination parent exceeds its bounded entry count.', 4)
                if unicodedata.normalize('NFC', sibling.name).casefold() == part.casefold() and sibling.name != part:
                    c.fail('import.path_ambiguous', 'Destination component aliases an existing case or Unicode spelling.', 4)
        current /= part
    if c.kind(target.parent) != 'directory':
        c.fail('import.parent_required', 'Create the selected real parent directory before importing.', 4, path=str(target.parent))
    if new:
        tracked = c.git(root, '--literal-pathspecs', 'ls-files', '-z', '--', path, binary=True)
        if c.kind(target) != 'missing' or tracked or s.exact_entry(root, head, path) is not None:
            c.fail('import.collision', 'Destination already has tracked, staged or local material; nothing was replaced.', 4, path=path)
        current = target.parent
        while current != root.parent:
            if c.kind(current / 'SKILL.md') != 'missing':
                c.fail('source.path_ambiguous', 'Destination would create a nested package inside an existing skill.', 4)
            current = current.parent
    elif c.kind(target) != 'directory' or c.kind(target / 'SKILL.md') != 'file':
        c.fail('provenance.unavailable', 'Selected authoring package is unavailable.', 4)
    snapshot = dict(root=str(root), root_identity=c.identity(root), head=head, path=path,
                    parent_identity=c.identity(target.parent), source_index=index_digest,
                    git_index=c.digest(c.git(root, 'ls-files', '--stage', '-z', binary=True)))
    return root, target, snapshot


def notice_files(root, payload):
    files, records = [], []
    total = payload.total_bytes
    if payload.path == '.':
        return files, records
    ancestor = PurePosixPath(payload.path).parent
    for level in range(p.DEPTH):
        prefix = '' if str(ancestor) == '.' else str(ancestor)
        for mode, kind, oid, name in g.tree(root, payload.commit, prefix):
            if not re.fullmatch(r'(LICENSE|LICENCE|NOTICE|COPYING)([.-][A-Za-z0-9_.-]+)?', name, re.I):
                continue
            if mode not in ('100644', '100755') or kind != 'blob':
                c.fail('import.notice_unsupported', 'Adjacent notices must be regular Git blobs.', 4)
            if len(files) >= 64:
                c.fail('skill.limit', 'Import exceeds 64 adjacent notices.', 4)
            data = s.object_blob(root, oid, min(RECORD_BYTES, p.PACKAGE_BYTES - total))
            total += len(data)
            if data.startswith(b'version https://git-lfs.github.com/spec/v1'):
                c.fail('skill.lfs_unsupported', 'Adjacent notice is an unsupported LFS pointer.', 4)
            item = p.PayloadFile(f'{NOTICES}/{level}/{name}', mode, data)
            files.append(item)
            records.append(dict(upstream_path=(prefix + '/' if prefix else '') + name,
                                **item.manifest_entry()))
        if str(ancestor) == '.':
            break
        ancestor = ancestor.parent
    return files, records


def bounded_manifest(files):
    files = sorted(files, key=lambda item: item.path)
    paths = [item.path for item in files]
    p.check_paths(paths)
    tree_paths = {prefix for path in paths for prefix in
                  ('/'.join(path.split('/')[:i]) for i in range(1, len(path.split('/')) + 1))}
    if len(tree_paths) > p.FILE_COUNT or sum(len(item.data) for item in files) > p.PACKAGE_BYTES:
        c.fail('skill.limit', 'Curated payload exceeds its cumulative resource limits.', 4)
    if any(len(item.data) > p.FILE_BYTES for item in files):
        c.fail('skill.limit', 'Curated payload exceeds its file limit.', 4)
    return [item.manifest_entry() for item in files]


def record_for(payload, row, name, snapshot, files, notices):
    manifest = bounded_manifest(files)
    return dict(schema_version=1, kind='mask-copy-import-v1',
                upstream=dict(repository=row['repository'], path=payload.path, id=payload.id,
                              commit=payload.commit, payload_digest=payload.digest, files=payload.manifest(), notices=notices),
                curated=dict(source=name, id=payload.id, path=snapshot['path'],
                             authoring_revision_at_import=snapshot['head'],
                             content_digest=c.digest(manifest), files=manifest), adaptations=[])


def prepared_import(args, output, home, config):
    if args.mode != 'copy':
        c.fail('invocation.invalid', 'Only explicit --mode copy is supported.', 2)
    # Observe the destination checkout before the upstream fetch, so its refusals write nothing.
    authoring_checkout(config, args.into)
    s.inspect(args, output, home)
    if output['data']['resolution_required']:
        output['data']['operation'] = 'copy_import'
        return None
    rows = output['data']['skills']
    if len(rows) != 1:
        c.fail('import.selection_required', 'Select exactly one package with --path.', 4,
               choices=[dict(id=row['id'], path=row['path']) for row in rows])
    row = rows[0]
    root, target, snapshot = destination(config, args.into, row['id'], new=True)
    cache = s.cached(home, row['source'], s.selected(config, row['source']))
    payload = p.validate(cache, row['commit'], row['path'], row['id'])
    if any(item.path.split('/')[0].casefold() in (RECORD, NOTICES) for item in payload.files):
        c.fail('import.provenance_collision', 'Upstream payload uses a reserved import-record or notice path.', 4)
    notices, mappings = notice_files(cache, payload)
    files = list(payload.files) + notices
    record = record_for(payload, row, args.into, snapshot, files, mappings)
    record_data = c.text_json(record).encode('utf-8')
    if len(record_data) > RECORD_BYTES:
        c.fail('skill.limit', 'Import provenance exceeds its record byte limit.', 4)
    complete = files + [p.PayloadFile(RECORD, '100644', record_data)]
    artifact_manifest = bounded_manifest(complete)
    plan_hash = c.digest(dict(config=config, destination=snapshot, record=record))
    output['would_change'] = True
    output['data'].update(operation='copy_import', destination=str(target),
        coordinate=args.into + '/' + row['id'], plan_hash=plan_hash,
        upstream_payload_digest=payload.digest, curated_content_digest=record['curated']['content_digest'],
        artifact_payload_digest=c.digest(artifact_manifest), notices=mappings,
        changed_paths=[str(target / item.path) for item in sorted(complete, key=lambda item: item.path)],
        git_commit_created=False, git_push_performed=False, index_changed=False,
        mode_evidence='recorded_logical_modes' if os.name == 'nt' else 'filesystem_executable_bits')
    if getattr(args, 'expect_plan_hash', plan_hash) != plan_hash:
        c.fail('plan.stale', 'Import inputs changed; review a new preview.', 4)
    return root, target, snapshot, complete


def import_skill(args, output, home, config, original):
    prepared = prepared_import(args, output, home, config)
    if prepared is None or output['dry_run']:
        return
    root, target, snapshot, files = prepared
    git_dir = Path(c.git(root, 'rev-parse', '--absolute-git-dir'))
    c.parents_safe(Path(git_dir.anchor), git_dir)
    if c.kind(git_dir) != 'directory':
        c.fail('import.stage_invalid', 'Checkout Git metadata must be a real directory.', 4)
    with tempfile.TemporaryDirectory(prefix='mask-import-', dir=git_dir) as temporary:
        stage = Path(temporary) / 'payload'
        stage.mkdir()
        for item in files:
            path = stage / item.path
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as handle:
                handle.write(item.data)
            if os.name != 'nt':
                path.chmod(0o755 if item.mode == '100755' else 0o644)
        observed = working_manifest(stage, {item.path: item.mode for item in files}, exclude_record=False)
        if observed != [item.manifest_entry() for item in sorted(files, key=lambda item: item.path)]:
            c.fail('import.stage_invalid', 'Prepared payload changed before publication.', 4)
        # Hash the staged payload before the final authorizing-input checks.
        _, live_target, live = destination(config, args.into, output['data']['coordinate'].split('/')[1], new=True)
        if live != snapshot or live_target != target or c.read_text(home / 'config.json') != original:
            c.fail('plan.stale', 'Import preconditions changed during preparation.', 4)
        c.publish_directory(stage, target)
        output.update(changed=True, transaction='committed')
        output['actions'] = [dict(kind='skill.import', path=str(target), status='created')]


def manifest_schema(value):
    if not isinstance(value, list) or len(value) > p.FILE_COUNT:
        c.fail('provenance.invalid', 'Expected a bounded manifest array.', 4)
    paths, total = [], 0
    for item in value:
        c.fields(item, ('path', 'mode', 'size', 'sha256'), family='provenance', versions=None)
        p.portable_path(item['path'])
        if (item['mode'] not in ('100644', '100755') or type(item['size']) is not int or
                not 0 <= item['size'] <= p.FILE_BYTES or not isinstance(item['sha256'], str) or
                not re.fullmatch('[0-9a-f]{64}', item['sha256'])):
            c.fail('provenance.invalid', 'Invalid manifest file record.', 4)
        paths.append(item['path'])
        total += item['size']
    p.check_paths(paths)
    if paths != sorted(set(paths)) or total > p.PACKAGE_BYTES:
        c.fail('provenance.invalid', 'Manifest order, uniqueness or byte bound is invalid.', 4)
    return value


def read_record(target):
    raw = regular_bytes(target / RECORD, RECORD_BYTES)
    return parse_record(raw), raw


def parse_record(raw):
    if len(raw) > RECORD_BYTES:
        c.fail('provenance.limit', 'Provenance record exceeds its byte limit.', 4)
    value = c.parse_json(raw, 'provenance')
    c.fields(value, ('schema_version', 'kind', 'upstream', 'curated', 'adaptations'), family='provenance')
    if value['kind'] != 'mask-copy-import-v1':
        c.fail('provenance.invalid', 'Unsupported provenance record kind.', 4)
    upstream, curated = value['upstream'], value['curated']
    c.fields(upstream, ('repository', 'path', 'id', 'commit', 'payload_digest', 'files', 'notices'), family='provenance', versions=None)
    c.fields(curated, ('source', 'id', 'path', 'authoring_revision_at_import', 'content_digest', 'files'), family='provenance', versions=None)
    if s.repository(upstream['repository']) != upstream['repository']:
        c.fail('provenance.invalid', 'Noncanonical recorded repository.', 4)
    for item in (upstream, curated):
        s.package_path(item['path']); c.skill_id(item['id'])
        manifest_schema(item['files'])
    s.alias(curated['source'])
    for revision in (upstream['commit'], curated['authoring_revision_at_import']):
        if not isinstance(revision, str) or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', revision):
            c.fail('provenance.invalid', 'Expected a full recorded Git revision.', 4)
    if upstream['payload_digest'] != c.digest(upstream['files']) or curated['content_digest'] != c.digest(curated['files']):
        c.fail('provenance.invalid', 'Recorded manifest digest is inconsistent.', 4)
    if any(item['path'] == RECORD for item in curated['files']):
        c.fail('provenance.invalid', 'Curated content manifest must exclude only its self-record.', 4)
    if not isinstance(upstream['notices'], list) or len(upstream['notices']) > 64:
        c.fail('provenance.invalid', 'Expected bounded notice incorporation records.', 4)
    for notice in upstream['notices']:
        c.fields(notice, ('upstream_path', 'path', 'mode', 'size', 'sha256'), family='provenance', versions=None)
        p.portable_path(notice['upstream_path'])
        manifest_schema([{key: value for key, value in notice.items() if key != 'upstream_path'}])
        if not notice['path'].startswith(NOTICES + '/'):
            c.fail('provenance.invalid', 'Notice incorporation has an invalid destination.', 4)
        if notice['size'] > RECORD_BYTES:
            c.fail('provenance.invalid', 'Notice record exceeds its supported byte limit.', 4)
    if any(item['path'].split('/')[0].casefold() in (RECORD, NOTICES) for item in upstream['files']):
        c.fail('provenance.invalid', 'Original upstream manifest uses reserved import paths.', 4)
    combined = sorted(upstream['files'] + [{key: value for key, value in item.items() if key != 'upstream_path'}
                                          for item in upstream['notices']], key=lambda item: item['path'])
    manifest_schema(combined)
    if combined != curated['files']:
        c.fail('provenance.invalid', 'Original curated content must equal the upstream files plus recorded notices.', 4)
    history = value['adaptations']
    if not isinstance(history, list) or len(history) > 100:
        c.fail('provenance.invalid', 'Adaptation history exceeds its supported bound.', 4)
    for item in history:
        c.fields(item, ('note', 'from_content_digest', 'to_content_digest', 'files'), family='provenance', versions=None)
        if not isinstance(item['note'], str) or not 1 <= len(item['note']) <= 4096:
            c.fail('provenance.invalid', 'Adaptation note exceeds its supported bound.', 4)
        manifest_schema(item['files'])
        if item['to_content_digest'] != c.digest(item['files']):
            c.fail('provenance.invalid', 'Adaptation digest is inconsistent.', 4)
    previous = curated['content_digest']
    for item in history:
        if item['from_content_digest'] != previous:
            c.fail('provenance.invalid', 'Adaptation chain is inconsistent.', 4)
        previous = item['to_content_digest']
    return value


def working_payload(target, identifier, *, commit, path, modes=None):
    manifest = working_manifest(target, modes or {}, exclude_record=False)
    files = [p.PayloadFile(item['path'], item['mode'], regular_bytes(target / item['path'], p.FILE_BYTES)) for item in manifest]
    payload = p.validate_files(files, identifier, commit=commit, path=path)
    if payload.manifest() != manifest:
        c.fail('source.changed', 'Authoring package changed during bounded observation.', 4)
    return payload


LINE_ENDING_ATTRIBUTES = ('text', 'eol', 'crlf', 'filter', 'ident', 'working-tree-encoding')
# Control bytes Git's text statistics count as nonprintable (convert.c gather_stats); NUL is checked separately.
NONPRINTABLE = bytes((*range(1, 8), 11, *range(14, 27), *range(28, 32), 127))


def authoring_payload(root, target, identifier, *, commit, path, committed, policy, source=None):
    """Package bytes MASK derives from an authoring checkout under its tap's line-ending policy (MASK-0107).

    ``committed`` maps package-relative paths to the files committed at ``commit``. An exact tap reads raw bytes;
    given ``source``, it refuses files whose bytes differ from their committed copies only in line endings, which
    Git conversion produced, so publication and a new development link never take them for edits. A tap that
    opted in at registration applies Git's core.autocrlf=true check-in conversion instead.
    """
    payload = working_payload(target, identifier, commit=commit, path=path, modes={name: item.mode for name, item in committed.items()})
    if policy == 'autocrlf':
        return p.validate_files(autocrlf_files(root, path, payload.files, committed), identifier, commit=commit, path=path)
    if source is not None:
        converted = [item.path for item in payload.files if item.path in committed and item.data != committed[item.path].data
                     and item.data.replace(b'\r\n', b'\n') == committed[item.path].data.replace(b'\r\n', b'\n')]
        if converted:
            c.fail('source.line_endings_converted', 'This tap keeps exact bytes, but Git converted the line endings of these unedited authoring files. '
                   'Set core.autocrlf false in the checkout, delete these unedited files and check them out again (git checkout -- PATH ...), '
                   'or register the tap with --autocrlf.', 4, source=source, root=str(root),
                   paths=[name if path == '.' else path + '/' + name for name in converted][:64], autocrlf=s.checkout_conversion(root))
    return payload


def autocrlf_files(root, package, files, committed):
    """Refuse attributes whose conversion MASK does not reproduce, then convert each file as core.autocrlf=true would."""
    names = [item.path if package == '.' else package + '/' + item.path for item in files]
    batches, batch, size = [], [], 0
    for name in names:
        if batch and size + len(name) > 8000:
            batches.append(batch)
            batch, size = [], 0
        batch.append(name)
        size += len(name) + 1
    specified = []
    for batch in batches + ([batch] if batch else []):
        fields = c.git(root, 'check-attr', '-z', *LINE_ENDING_ATTRIBUTES, '--', *batch, binary=True).split(b'\0')
        for index in range(0, len(fields) - 2, 3):
            name, attribute, value = (item.decode('utf-8', 'replace') for item in fields[index:index + 3])
            if value != 'unspecified':
                specified.append(dict(path=name, attribute=attribute, value=value))
    if specified:
        c.fail('source.line_endings_unsupported', 'Git attributes select a conversion that an autocrlf tap does not apply; '
               'remove them from these files, or register the tap without --autocrlf.', 4, attributes=specified[:64])
    return [p.PayloadFile(item.path, item.mode, autocrlf(item.data, committed.get(item.path))) for item in files]


def git_binary(data):
    """Git's text statistics call these bytes binary: a lone CR, a NUL, or too many nonprintable bytes (convert.c)."""
    if data.count(b'\r') != data.count(b'\r\n') or b'\0' in data:
        return True
    control = len(data) - len(data.translate(None, NONPRINTABLE))
    printable = len(data) - data.count(b'\r') - data.count(b'\n') - control
    return (printable >> 7) < control - data.endswith(b'\x1a')


def autocrlf(data, committed=None):
    """Git's core.autocrlf=true check-in conversion of one file without attributes (convert.c crlf_to_git, text=auto).

    Nothing changes without CRLF or for binary bytes, and nothing changes when the committed copy is text that
    already holds CRLF (Git's has_crlf_in_index check).
    """
    if b'\r\n' not in data or git_binary(data):
        return data
    if committed is not None and b'\r\n' in committed.data and not git_binary(committed.data):
        return data
    return data.replace(b'\r\n', b'\n')


def working_manifest(target, modes, *, exclude_record=True):
    if c.kind(target) != 'directory':
        c.fail('provenance.unavailable', 'Selected package is not a real directory.', 4)
    files, paths = [], []
    total = (target / RECORD).stat().st_size if exclude_record and c.kind(target / RECORD) == 'file' else 0
    if total > p.PACKAGE_BYTES:
        c.fail('skill.limit', 'Observed package exceeds its byte limits.', 4)
    def walk(directory):
        nonlocal total
        for item in directory.iterdir():
            relative = item.relative_to(target).as_posix()
            paths.append(relative)
            if len(paths) > p.FILE_COUNT:
                c.fail('skill.limit', 'Observed package exceeds its entry limit.', 4)
            p.portable_path(relative)
            kind = c.kind(item)
            if kind == 'directory':
                walk(item)
            elif kind == 'file':
                if exclude_record and relative == RECORD:
                    continue
                size = item.stat().st_size
                if size > p.FILE_BYTES or total + size > p.PACKAGE_BYTES:
                    c.fail('skill.limit', 'Observed package exceeds its byte limits.', 4)
                data = regular_bytes(item, min(p.FILE_BYTES, p.PACKAGE_BYTES - total))
                total += len(data)
                mode = modes.get(relative, '100644') if os.name == 'nt' else ('100755' if item.stat().st_mode & 0o111 else '100644')
                files.append(p.PayloadFile(relative, mode, data))
            else:
                c.fail('skill.entry_unsupported', 'Observed package contains a link or special entry.', 4)
    walk(target)
    p.check_paths(paths, [item.path for item in files] + ([RECORD] if exclude_record else []))
    return bounded_manifest(files)


def observe(config, home, args):
    if '/' not in args.id:
        c.fail('invocation.invalid', 'Provenance requires SOURCE/ID.', 2)
    name, identifier = args.id.split('/', 1)
    c.skill_id(identifier)
    entry = s.selected(config, name)
    authoring = Path(entry['authoring']) if entry['authoring'] else None
    if args.command == 'skill.provenance' and (authoring is None or c.kind(authoring) != 'directory' or
            c.git(authoring, 'symbolic-ref', '--short', 'HEAD', optional=True) != entry['ref'].removeprefix('refs/heads/')):
        return observe_cached(config, home, args), None
    root, target, snapshot = destination(config, name, identifier)
    if c.kind(target / RECORD) == 'missing':
        return dict(coordinate=args.id, observation='authoring', history='absent', verification='unknown', upstream=None), None
    record, raw = read_record(target)
    if record['curated']['source'] != name or record['curated']['id'] != identifier or record['curated']['path'] != snapshot['path']:
        c.fail('provenance.invalid', 'Recorded curated coordinate does not match the selected package.', 4)
    expected = record['adaptations'][-1]['files'] if record['adaptations'] else record['curated']['files']
    current = working_manifest(target, {item['path']: item['mode'] for item in expected})
    data = dict(coordinate=args.id, observation='authoring', history='recorded', record=record,
                record_trust='local_assertions', verification='recorded_only', verified_git_facts=None,
                current_content_digest=c.digest(current), unrecorded_adaptations=current != expected,
                mode_evidence='recorded_logical_modes' if os.name == 'nt' else 'filesystem_executable_bits')
    verify_upstream(config, home, record, data)
    return data, (root, target, snapshot, record, raw, current)


def observe_cached(config, home, args):
    output = {}
    s.query(args, output, home)
    row = output['data']
    cache = s.cached(home, row['source'], s.selected(config, row['source']))
    payload = p.validate(cache, row['commit'], row['path'], row['id'])
    data = dict(coordinate=args.id, observation='frozen_cache', observed_commit=payload.commit,
                observed_package=dict(repository=row['repository'], path=payload.path, payload_digest=payload.digest),
                history='absent', verification='unknown', upstream=None)
    record_file = next((item for item in payload.files if item.path == RECORD), None)
    if record_file is None:
        return data
    record = parse_record(record_file.data)
    current = [item for item in payload.manifest() if item['path'] != RECORD]
    expected = record['adaptations'][-1]['files'] if record['adaptations'] else record['curated']['files']
    data.update(history='recorded', record=record, record_trust='publisher_assertions',
                verification='recorded_only', verified_git_facts=None,
                current_content_digest=c.digest(current), unrecorded_adaptations=current != expected,
                mode_evidence='frozen_git_modes')
    verify_upstream(config, home, record, data)
    return data


def verify_upstream(config, home, record, data):
    upstream = record['upstream']
    for source_name, entry in config['sources'].items():
        if entry['repository'] != upstream['repository']:
            continue
        cache = s.cached(home, source_name, entry)
        if cache is None or c.git(cache, 'cat-file', '-e', upstream['commit'] + '^{commit}', optional=True) is None:
            continue
        payload = p.validate(cache, upstream['commit'], upstream['path'], upstream['id'])
        _, notices = notice_files(cache, payload)
        if payload.manifest() != upstream['files'] or payload.digest != upstream['payload_digest'] or notices != upstream['notices']:
            data['verification'] = 'mismatch'
        else:
            data.update(verification='verified_git_objects', verified_git_facts=dict(
                repository=entry['repository'], commit=payload.commit, path=payload.path,
                payload_digest=payload.digest, notices=notices))
        break


def dispatch(args, output, home):
    original = c.read_text(home / 'config.json')
    config = c.config(c.parse_json(original))
    if args.command == 'skill.import':
        return import_skill(args, output, home, config, original)
    data, observation = observe(config, home, args)
    output['data'] = data
    if args.command == 'skill.provenance':
        return
    if observation is None:
        c.fail('provenance.absent', 'No recorded history exists; MASK will not invent upstream attribution.', 4)
    if data['verification'] == 'mismatch':
        c.fail('provenance.invalid', 'Recorded upstream facts disagree with cached Git objects.', 4)
    if not isinstance(args.note, str) or not 1 <= len(args.note.strip()) <= 4096 or '\0' in args.note:
        c.fail('invocation.invalid', 'Supply a nonempty adaptation note of at most 4096 characters.', 2)
    root, target, snapshot, record, raw, current = observation
    proposal = copy.deepcopy(record)
    previous = record['adaptations'][-1]['to_content_digest'] if record['adaptations'] else record['curated']['content_digest']
    if c.digest(current) != previous:
        if len(record['adaptations']) >= 100:
            c.fail('provenance.limit', 'Adaptation history reached its supported bound.', 4)
        proposal['adaptations'].append(dict(note=args.note.strip(), from_content_digest=previous,
                                           to_content_digest=c.digest(current), files=current))
    content = c.text_json(proposal)
    if len(content.encode('utf-8')) > RECORD_BYTES:
        c.fail('provenance.limit', 'Adaptation record exceeds its byte limit.', 4)
    if sum(item['size'] for item in current) + len(content.encode('utf-8')) > p.PACKAGE_BYTES:
        c.fail('skill.limit', 'Adaptation record would exceed the total package byte limit.', 4)
    plan_hash = c.digest(dict(config=config, snapshot=snapshot, before=c.digest(raw), after=proposal))
    output['data'].update(plan_hash=plan_hash, proposed_record=proposal, changed_paths=[str(target / RECORD)])
    output['would_change'] = proposal != record
    if getattr(args, 'expect_plan_hash', plan_hash) != plan_hash:
        c.fail('plan.stale', 'Adaptation inputs changed; review a new preview.', 4)
    if output['would_change'] and not output['dry_run']:
        _, _, live = destination(config, record['curated']['source'], record['curated']['id'])
        if live != snapshot or c.read_text(home / 'config.json') != original or working_manifest(target, {item['path']: item['mode'] for item in current}) != current:
            c.fail('plan.stale', 'Adaptation preconditions changed before writing the record.', 4)
        c.atomic_text(target / RECORD, content, raw.decode('utf-8'))
        output.update(changed=True, transaction='committed')
