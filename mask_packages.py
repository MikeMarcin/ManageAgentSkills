"""Passive, bounded payload validation from exact Git objects; never checkout."""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
import unicodedata

import mask_core as c

FILE_BYTES = 64 * 1024 * 1024
PACKAGE_BYTES = 256 * 1024 * 1024
FILE_COUNT = 10000
DEPTH = 32
TREE_BYTES = 16 * 1024 * 1024


def passive_frontmatter(text):
    """Accept a closed passive scalar subset, never ignore unknown YAML syntax."""
    if '!`' in text or '```!' in text:
        c.fail('skill.activation_unsupported', 'Dynamic shell preprocessing in SKILL.md is unsupported for plain skills.', 4)
    lines = text.splitlines()
    if not lines or lines[0] != '---' or '---' not in lines[1:]:
        c.fail('skill.invalid', 'SKILL.md needs frontmatter.', 4)
    seen, nested = set(), None
    active = {'hooks', 'allowed-tools', 'mcp', 'mcpservers', 'mcp-servers', 'plugin', 'plugins'}
    for line in lines[1:lines.index('---', 1)]:
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        match = re.fullmatch(r'(  )?([A-Za-z][A-Za-z0-9_-]*): *(.*)', line)
        if match is None:
            c.fail('skill.metadata_unsupported', 'Plain skills require unquoted frontmatter keys and single-line scalars; flow, aliases and complex YAML are unsupported.', 4)
        indent, key, value = match.groups()
        if indent is None:
            nested = None
            if key.casefold() in active:
                c.fail('skill.activation_unsupported', 'Plain skills cannot grant tools or define hook, MCP or plugin activation.', 4)
            if key not in {'name', 'description', 'license', 'compatibility', 'metadata'}:
                c.fail('skill.metadata_unsupported', 'Unsupported plain-skill frontmatter field.', 4, field=key)
            if key in seen:
                c.fail('skill.invalid', 'Duplicate frontmatter field.', 4, field=key)
            seen.add(key)
            if key == 'metadata':
                if value:
                    c.fail('skill.metadata_unsupported', 'Metadata supports only an indented flat scalar map.', 4)
                nested = set()
                continue
        else:
            if nested is None or key in nested:
                c.fail('skill.metadata_unsupported', 'Only a unique flat metadata map supports indentation.', 4)
            nested.add(key)
        value = value.strip()
        if not value or value[0] in '|>!&*[{':
            c.fail('skill.metadata_unsupported', 'Plain frontmatter values require single-line scalars.', 4)
        if value.startswith('"'):
            try:
                if not isinstance(json.loads(value), str):
                    raise ValueError()
            except ValueError:
                c.fail('skill.metadata_unsupported', 'Unsupported quoted frontmatter scalar.', 4)
        elif value.startswith("'"):
            if re.fullmatch(r"'(?:[^']|'')*'", value) is None:
                c.fail('skill.metadata_unsupported', 'Unsupported quoted frontmatter scalar.', 4)
        elif ': ' in value or ' #' in value:
            c.fail('skill.metadata_unsupported', 'Ambiguous frontmatter scalar; quote it.', 4)


def portable_path(path):
    try:
        size = len(path.encode('utf-8')) if isinstance(path, str) else 0
    except UnicodeError:
        c.fail('skill.path_invalid', 'Package paths require valid Unicode scalars.', 4)
    if not isinstance(path, str) or not path or size > 1024:
        c.fail('skill.path_invalid', 'Package paths require bounded UTF-8 relative names.', 4)
    parts = path.split('/')
    if len(parts) > DEPTH:
        c.fail('skill.limit', 'Package exceeds its path depth limit.', 4)
    for part in parts:
        if (part in ('', '.', '..') or part[-1:] in (' ', '.') or
                any(ord(ch) < 32 or ord(ch) == 127 or ch in '\\:<>"|?*' for ch in part) or
                unicodedata.normalize('NFC', part) != part or
                part.split('.')[0].casefold() in (c.RESERVED - {'synced'}) | {'com¹', 'com²', 'com³', 'lpt¹', 'lpt²', 'lpt³'}):
            c.fail('skill.path_invalid', 'Package has a nonportable path component.', 4)
    return parts


def passive_path(parts):
    # These are package-kind boundaries, not a claim to detect arbitrary malware.
    names = [part.casefold() for part in parts]
    if (any(name in {'.git', '.claude-plugin', '.codex-plugin', '.claude', '.codex', '.agents'} for name in names)
            or names[-1] in {'.mcp.json', 'mcp.json', '.gitmodules'}
            or names[-2:] == ['hooks', 'hooks.json']):
        c.fail('skill.activation_unsupported', 'Plain skills cannot include host activation or Git administration metadata.', 4)


def check_paths(paths, files=None):
    spellings = {}
    files = set(paths if files is None else files)
    for path in paths:
        parts = portable_path(path)
        passive_path(parts)
        for i in range(1, len(parts) + 1):
            prefix = '/'.join(parts[:i])
            key = prefix.casefold()
            previous = spellings.setdefault(key, prefix)
            if previous != prefix or i < len(parts) and prefix in files:
                c.fail('skill.path_ambiguous', 'Package has colliding file or directory components.', 4)


@dataclass(frozen=True)
class PayloadFile:
    path: str
    mode: str
    data: bytes

    def manifest_entry(self):
        return dict(path=self.path, mode=self.mode, size=len(self.data),
                    sha256=c.digest(self.data).removeprefix('sha256:'))


@dataclass(frozen=True)
class Payload:
    commit: str
    path: str
    id: str
    description: str
    files: tuple[PayloadFile, ...]
    digest: str
    total_bytes: int

    def summary(self):
        return dict(validation='payload', valid=True, payload_digest=self.digest,
                    total_bytes=self.total_bytes, file_count=len(self.files),
                    scope='mask-package-v1')

    def manifest(self):
        return [item.manifest_entry() for item in self.files]


def validate(root, commit, path, identifier):
    """Return immutable exact bytes/logical modes suitable for later staging.

    The caller supplies an approved cache and full frozen commit. No files are
    written, no refs resolved implicitly, and no filters or package code run.
    """
    from mask_sources import package_path
    from mask_git import tree
    c.skill_id(identifier)
    package_path(path)
    if not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', commit):
        c.fail('skill.revision_invalid', 'Payload validation requires a full frozen commit.', 4)
    if path != '.':
        portable_path(path)
    rows = tree(root, commit, '' if path == '.' else path, recursive=True,
                include_trees=True, max_output=TREE_BYTES)
    if len(rows) > FILE_COUNT:
        c.fail('skill.limit', 'Package exceeds its file count limit.', 4)
    check_paths([row[3] for row in rows], [row[3] for row in rows if row[1] != 'tree'])
    rows = [row for row in rows if row[:2] != ('040000', 'tree')]
    sizes, total = [], 0
    for mode, kind, oid, name in rows:
        if mode not in ('100644', '100755') or kind != 'blob':
            c.fail('skill.entry_unsupported', 'Packages require regular blobs; links and submodules are unsupported.', 4)
        size = c.git(root, 'cat-file', '-s', oid, max_output=32)
        if not size.isdecimal() or int(size) > FILE_BYTES:
            c.fail('skill.limit', 'Package exceeds its per-file byte limit.', 4)
        total += int(size)
        if total > PACKAGE_BYTES:
            c.fail('skill.limit', 'Package exceeds its cumulative byte limit.', 4)
        sizes.append(int(size))
    files = []
    for (mode, kind, oid, name), size in zip(rows, sizes):
        data = c.git(root, 'cat-file', 'blob', oid, binary=True, max_output=size)
        if len(data) != size:
            c.fail('skill.object_invalid', 'Frozen blob size changed during validation.', 4)
        files.append(PayloadFile(name, mode, data))
    return validate_files(files, identifier, commit=commit, path=path)


def validate_files(files, identifier, *, commit, path):
    """Revalidate raw supplied regular entries; a frozen dataclass grants no trust."""
    c.skill_id(identifier)
    if not isinstance(commit, str) or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', commit):
        c.fail('skill.revision_invalid', 'Payload requires a full frozen commit.', 4)
    if path != '.':
        portable_path(path)
    if not isinstance(files, (tuple, list)) or len(files) > FILE_COUNT:
        c.fail('skill.limit', 'Payload requires a bounded collection of regular files.', 4)
    paths, directories, total = [], set(), 0
    for item in files:
        if not isinstance(item, PayloadFile) or type(item.data) is not bytes or item.mode not in ('100644', '100755'):
            c.fail('skill.entry_unsupported', 'Payload entries require raw bytes and regular logical Git modes.', 4)
        parts = portable_path(item.path)
        paths.append(item.path)
        directories.update('/'.join(parts[:i]) for i in range(1, len(parts)))
        total += len(item.data)
        if len(item.data) > FILE_BYTES or total > PACKAGE_BYTES or len(files) + len(directories) > FILE_COUNT:
            c.fail('skill.limit', 'Payload exceeds file/package bytes or entry count.', 4)
        if item.data.startswith(b'version https://git-lfs.github.com/spec/v1'):
            c.fail('skill.lfs_unsupported', 'Git LFS assets need a separate supported acquisition policy.', 4)
        if parts[-1] == 'SKILL.md':
            try:
                passive_frontmatter(item.data.decode('utf-8'))
            except UnicodeError:
                c.fail('skill.invalid', 'SKILL.md requires UTF-8 text.', 4)
    if len(set(paths)) != len(paths):
        c.fail('skill.path_ambiguous', 'Duplicate payload file path.', 4)
    check_paths(paths)
    skill = next((item for item in files if item.path == 'SKILL.md'), None)
    if skill is None:
        c.fail('skill.invalid', 'Payload requires SKILL.md.', 4)
    facts = c.metadata(skill.data.decode('utf-8'), identifier)
    ordered = tuple(sorted(files, key=lambda item: item.path))
    return Payload(commit, path, identifier, facts['description'], ordered,
                   c.digest([item.manifest_entry() for item in ordered]), total)
