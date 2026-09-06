"""Validated local data and filesystem primitives for MASK."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import signal
import subprocess
import tempfile
import threading
import time

ADAPTERS = {'claude': '.claude/skills', 'codex': '.agents/skills'}
ID_RE = re.compile(r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
RESERVED = {'synced', 'con', 'prn', 'aux', 'nul', 'clock$', *(f'{p}{n}' for p in ('com', 'lpt') for n in range(1, 10))}


class MaskError(Exception):
    def __init__(self, code, message, exit_code=3, *, details=None, retryable=False):
        super().__init__(message)
        self.code, self.exit_code = code, exit_code
        self.details, self.retryable = details or {}, retryable

    def as_dict(self):
        return dict(code=self.code, message=str(self), retryable=self.retryable, details=self.details,
                    remediation=[dict(kind='inspect', message='Inspect the reported inputs and retry only after resolving the condition.')])


def fail(code, message, exit_code=3, **details):
    raise MaskError(code, message, exit_code, details=details)


def text_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n'


def digest(value):
    raw = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode('utf-8')
    return 'sha256:' + hashlib.sha256(raw).hexdigest()


def parse_json(text, family='config'):
    def pairs(items):
        answer = {}
        for key, value in items:
            if key in answer:
                fail(family + '.invalid', 'Duplicate JSON key.', key=key)
            answer[key] = value
        return answer
    def constant(_):
        fail(family + '.invalid', 'Non-finite JSON numbers are unsupported.')
    try:
        return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, UnicodeError):
        fail(family + '.invalid', 'Invalid UTF-8 JSON.')


def fields(value, required, optional=(), family='config', *, versions=(1,)):
    if not isinstance(value, dict) or not set(required) <= value.keys() or value.keys() - set(required) - set(optional):
        fail(family + '.invalid', 'Unexpected or missing fields.')
    if 'schema_version' in required and (type(value['schema_version']) is not int or value['schema_version'] not in versions):
        fail(family + '.unsupported_version', 'Unsupported schema version.', supported=list(versions))


def skill_id(value):
    if not isinstance(value, str) or not 1 <= len(value) <= 64 or not ID_RE.fullmatch(value) or value in RESERVED:
        fail('skill.invalid', 'Unsafe or reserved skill ID.', skill=value)
    return value


def string_set(value, family, *, targets=False):
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        fail(family + '.invalid', 'Expected an array of strings.')
    if len(set(value)) != len(value):
        fail(family + '.invalid', 'Duplicate set entries.')
    if targets:
        if not value or set(value) - ADAPTERS.keys():
            fail(family + '.invalid', 'Targets must be a nonempty subset of claude and codex.')
    else:
        for item in value:
            skill_id(item)
    return sorted(value)


def manifest(value):
    fields(value, ('schema_version', 'skills'), ('targets',), 'manifest')
    normalized = dict(schema_version=1, skills=string_set(value['skills'], 'manifest'))
    if 'targets' in value:
        normalized['targets'] = string_set(value['targets'], 'manifest', targets=True)
    return normalized


def reparse(info):
    return bool(getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0))


def kind(path):
    try:
        info = path.lstat()
    except FileNotFoundError:
        return 'missing'
    if stat.S_ISLNK(info.st_mode):
        return 'symlink'
    if reparse(info):
        return 'reparse'
    if stat.S_ISREG(info.st_mode):
        return 'file'
    if stat.S_ISDIR(info.st_mode):
        return 'directory'
    return 'special'


def parents_safe(root, path):
    if not path.is_relative_to(root):
        fail('target.parent_link', 'Destination escapes its managed root.', 4, path=str(path))
    current = root
    for part in path.relative_to(root).parts[:-1]:
        current /= part
        observed = kind(current)
        if observed not in ('missing', 'directory'):
            fail('target.parent_link', 'A destination parent is linked or is not a real directory.', 4, path=str(current))


def read_text(path, family='config', missing=False):
    parents_safe(Path(path.anchor), path)
    observed = kind(path)
    if observed == 'missing' and missing:
        return None
    if observed == 'missing':
        fail(family + '.missing', 'Required file is missing.', path=str(path))
    if observed != 'file':
        fail(family + '.invalid', 'Expected a regular unlinked file.', path=str(path))
    try:
        with path.open(encoding='utf-8', newline='') as handle:
            return handle.read()
    except UnicodeError:
        fail(family + '.invalid', 'Expected UTF-8 text.', path=str(path))


def read_json(path, family='config', default=None):
    text = read_text(path, family, missing=default is not None)
    return default if text is None else parse_json(text, family)


def atomic_text(path, content, before):
    parents_safe(Path(path.anchor), path)
    actual = read_text(path, missing=True)
    if actual != before:
        fail('state.drift', 'File changed since preflight.', 4, path=str(path))
    if actual == content:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile('w', encoding='utf-8', newline='\n', dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())
    try:
        parents_safe(Path(path.anchor), path)
        if read_text(path, missing=True) != before:
            fail('state.drift', 'File changed before replacement.', 4, path=str(path))
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return True


@contextmanager
def writer_lock(home):
    parents_safe(Path(home.anchor), home / 'operation.lock')
    home.mkdir(parents=True, exist_ok=True)
    path = home / 'operation.lock'
    if kind(path) not in ('missing', 'file'):
        fail('config.invalid', 'The writer lock must be a regular file.')
    handle = path.open('a+b')
    locked = False
    try:
        if os.name == 'nt':
            import msvcrt
            if path.stat().st_size == 0:
                handle.write(b'\0'); handle.flush()
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError:
                fail('lock.busy', 'Another MASK writer holds the lock.', 6)
        else:
            import fcntl
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                fail('lock.busy', 'Another MASK writer holds the lock.', 6)
        locked = True
        yield
    finally:
        if locked:
            if os.name == 'nt':
                handle.seek(0); msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle, fcntl.LOCK_UN)
        handle.close()


HOOK_EVENTS = ('applypatch-msg', 'pre-applypatch', 'post-applypatch', 'pre-commit', 'pre-merge-commit',
               'prepare-commit-msg', 'commit-msg', 'post-commit', 'pre-rebase', 'post-checkout', 'post-merge',
               'pre-push', 'pre-receive', 'update', 'proc-receive', 'post-receive', 'post-update',
               'reference-transaction', 'push-to-checkout', 'pre-auto-gc', 'post-rewrite', 'sendemail-validate',
               'fsmonitor-watchman', 'p4-changelist', 'p4-prepare-changelist', 'p4-post-changelist',
               'p4-pre-submit', 'post-index-change')


def git(root, *args, timeout=30, optional=False, binary=False, mutating=False, inspect_hooks=False,
        max_output=16 * 1024 * 1024, monitor=None):
    selectors = {'GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE', 'GIT_COMMON_DIR', 'GIT_OBJECT_DIRECTORY',
                 'GIT_ALTERNATE_OBJECT_DIRECTORIES', 'GIT_NAMESPACE', 'GIT_CONFIG_PARAMETERS', 'GIT_CONFIG_COUNT',
                 'GIT_CEILING_DIRECTORIES', 'GIT_DISCOVERY_ACROSS_FILESYSTEM'}
    environment = {key: value for key, value in os.environ.items() if key not in selectors and not key.startswith(('GIT_CONFIG_KEY_', 'GIT_CONFIG_VALUE_'))}
    environment.update(GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0', GIT_MERGE_AUTOEDIT='no', GCM_INTERACTIVE='never',
                       GIT_ASKPASS=os.devnull, SSH_ASKPASS=os.devnull, MASK_INTERNAL_GIT='1',
                       GIT_NO_REPLACE_OBJECTS='1', GIT_NO_LAZY_FETCH='1')
    if not environment.get('GIT_SSH') and not environment.get('GIT_SSH_COMMAND'):
        environment['GIT_SSH_COMMAND'] = 'ssh -o BatchMode=yes'
    options = dict(start_new_session=True) if os.name != 'nt' else dict(creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
    if inspect_hooks and (not args or args[0] not in ('config', 'rev-parse')):
        fail('internal.invariant', 'Hook-path inspection is restricted to observational Git commands.', 10)
    hook_options = [] if inspect_hooks else ['-c', 'core.hooksPath=' + os.devnull]
    # Older Git ignores these settings; capable Git disables every known event.
    # An environment token alone cannot suppress third-party configured hooks.
    if not inspect_hooks:
        for event in HOOK_EVENTS:
            hook_options.extend(('-c', f'hook.{event}.enabled=false'))
    command = ['git', *hook_options, '-C', str(root), *args]
    job = None
    if os.name == 'nt':
        from mask_process import WindowsJob, CREATE_SUSPENDED
        try:
            job = WindowsJob()
        except OSError:
            fail('git.containment_unavailable', 'Windows Job Object containment is unavailable; Git was not started.', 4)
        options['creationflags'] |= CREATE_SUSPENDED
    try:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment, **options)
    except BaseException:
        if job is not None:
            job.close()
        raise
    if job is not None:
        try:
            job.start(process.pid)
        except (OSError, KeyboardInterrupt) as error:
            try:
                job.close()
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=10)
            except (OSError, subprocess.TimeoutExpired):
                fail('recovery.required', 'Git containment setup failed and process termination could not be confirmed.', 8, indeterminate=True)
            finally:
                process.stdout.close()
                process.stderr.close()
            if isinstance(error, KeyboardInterrupt):
                raise
            fail('git.containment_unavailable', 'Git could not join and resume in its Windows Job Object; the suspended process was terminated.', 4)
    # Drain both pipes concurrently into bounded buffers. communicate() allocates
    # the complete output before its caller can inspect a size limit.
    buffers = [bytearray(), bytearray()]
    exceeded = threading.Event()
    read_failed = threading.Event()
    def drain(stream, buffer, limit):
        try:
            while True:
                chunk = stream.read1(min(65536, max(1, limit - len(buffer) + 1)))
                if not chunk:
                    break
                if len(buffer) + len(chunk) > limit:
                    exceeded.set()
                    break
                buffer.extend(chunk)
        except Exception:
            read_failed.set()
        finally:
            try:
                stream.close()
            except Exception:
                read_failed.set()
    readers = [threading.Thread(target=drain, args=(stream, buffer, limit), daemon=True)
               for stream, buffer, limit in ((process.stdout, buffers[0], max_output),
                                              (process.stderr, buffers[1], 65536))]
    for reader in readers:
        reader.start()
    try:
        deadline = time.monotonic() + timeout
        while True:
            if read_failed.is_set():
                fail('git.output_failed', 'Git output could not be read completely.', 5)
            if exceeded.is_set():
                fail('git.output_limit', 'Git exceeded its bounded output allowance.', 5)
            if monitor is not None:
                monitor()
            if process.poll() is not None and not any(reader.is_alive() for reader in readers):
                break
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(command, timeout)
            exceeded.wait(0.01)
        if read_failed.is_set():
            fail('git.output_failed', 'Git output could not be read completely.', 5)
        if exceeded.is_set():
            fail('git.output_limit', 'Git exceeded its bounded output allowance.', 5)
        if job is not None:
            try:
                job.stop()
            except OSError:
                fail('recovery.required', 'Windows Git job cleanup could not be confirmed.', 8, indeterminate=True)
        stdout, stderr = map(bytes, buffers)
    except (subprocess.TimeoutExpired, KeyboardInterrupt, MaskError) as error:
        confirmed = False
        try:
            if os.name == 'nt':
                job.stop()
                confirmed = True
            else:
                process.poll()  # Reap an exited leader before signaling its group.
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except PermissionError:
                    # macOS can report EPERM for a group with a zombie leader.
                    # Reap it, then signal again so live descendants still must
                    # be terminated (or the group proven absent).
                    process.wait(timeout=0.1)
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                except ProcessLookupError:
                    pass  # The entire process group already exited.
                confirmed = True
            process.wait(timeout=10)
            for reader in readers:
                reader.join(timeout=10)
            confirmed = confirmed and not any(reader.is_alive() for reader in readers)
        except (OSError, subprocess.TimeoutExpired):
            confirmed = False
        if not confirmed:
            fail('recovery.required', 'Git process-tree termination could not be confirmed; inspect before retrying.', 8, indeterminate=True)
        if isinstance(error, (KeyboardInterrupt, MaskError)):
            raise
        fail('git.timeout', 'Git exceeded its timeout; its process tree was terminated and reaped.', 5)
    finally:
        if job is not None:
            job.close()
    if process.returncode and not optional:
        lower = stderr.lower()
        auth = any(token in lower for token in (b'authentication failed', b'could not read username', b'permission denied (publickey)'))
        fail('git.auth_required' if auth else 'git.failed', 'Noninteractive Git authentication failed.' if auth else 'Git operation failed.', 5, operation=args[0] if args else '')
    if process.returncode:
        return None
    return stdout if binary else stdout.decode('utf-8', errors='replace').strip()


def checkout(root):
    if not root.is_dir() or kind(root) != 'directory':
        fail('source.missing', 'Source checkout is unavailable.', root=str(root))
    top = git(root, 'rev-parse', '--show-toplevel', optional=True)
    if top is None or Path(top).resolve() != root:
        fail('source.identity_mismatch', 'Source must be an ordinary Git checkout root.', 4)
    return root


def config(value):
    required = ('schema_version', 'source', 'default_targets', 'git_timeout_seconds')
    if isinstance(value, dict) and value.get('schema_version') == 2:
        required += ('sources', 'legacy_source')
    fields(value, required, versions=(1, 2))
    source = value['source']
    fields(source, ('root', 'remote', 'branch'))
    if not isinstance(source['root'], str) or not Path(source['root']).is_absolute():
        fail('config.invalid', 'Source root must be an absolute path.')
    for key in ('remote', 'branch'):
        item = source[key]
        if not isinstance(item, str) or not item or item.startswith('-') or any(c.isspace() for c in item) or any(c in item for c in ':\\~^?*[\x00') or '..' in item or '@{' in item:
            fail('config.invalid', 'Unsafe remote or branch name.', field=key)
    targets = string_set(value['default_targets'], 'config', targets=True)
    timeout = value['git_timeout_seconds']
    if type(timeout) is not int or not 1 <= timeout <= 600:
        fail('config.invalid', 'Git timeout must be an integer from 1 through 600.')
    if value['schema_version'] == 2:
        from mask_sources import validate_config
        validate_config(value)
    return dict(value, default_targets=targets)


def identity(root):
    info = root.stat()
    return dict(device=info.st_dev, inode=info.st_ino)


def metadata(text, expected_id):
    lines = text.splitlines()
    if not lines or lines[0] != '---' or '---' not in lines[1:]:
        fail('skill.invalid', 'SKILL.md needs frontmatter.', skill=expected_id)
    header = lines[1:lines.index('---', 1)]
    values = {}
    for line in header:
        match = re.match(r'^(name|description):\s*(.*)$', line)
        if not match:
            continue
        key, value = match.groups()
        if key in values:
            fail('skill.invalid', 'Duplicate frontmatter field.', field=key)
        if not value or value[0] in '|>!&*[{':
            fail('skill.metadata_unsupported', 'MASK supports single-line plain or quoted name/description scalars.')
        if value.startswith('"'):
            try:
                value = json.loads(value)
            except ValueError:
                fail('skill.metadata_unsupported', 'Unsupported quoted frontmatter scalar.')
        elif value.startswith("'"):
            if not value.endswith("'") or len(value) < 2:
                fail('skill.metadata_unsupported', 'Unclosed quoted scalar.')
            value = value[1:-1].replace("''", "'")
        elif ': ' in value or ' #' in value:
            fail('skill.metadata_unsupported', 'Ambiguous plain frontmatter scalar; quote it.')
        if not isinstance(value, str) or not value.strip():
            fail('skill.invalid', 'Frontmatter values must be nonempty strings.')
        values[key] = value
    if values.get('name') != expected_id or not values.get('description'):
        fail('skill.invalid', 'Frontmatter name must match ID and description must be present.', skill=expected_id)
    return values


def package(source, identifier, content=False):
    skill_id(identifier)
    if kind(source) != 'directory':
        fail('source.missing', 'Source checkout is unavailable or linked.')
    base = source / 'skills'
    root = base / identifier
    for path in (base, root):
        if kind(path) == 'missing':
            fail('skill.unknown', 'Skill is not available in the configured source.', skill=identifier)
        if kind(path) != 'directory':
            fail('skill.path_escape', 'Source packages require real directories.', path=str(path))
    names = [entry.name.casefold() for entry in base.iterdir()]
    if len(names) != len(set(names)):
        fail('skill.invalid', 'Case-colliding skill IDs.')
    staged = git(source, 'ls-files', '--stage', '--', 'skills/' + identifier, optional=True)
    if staged and any(line.startswith('160000 ') for line in staged.splitlines()):
        fail('skill.path_escape', 'Submodules are unsupported in skill packages.')
    files = {}
    def walk(directory):
        folded = set()
        for entry in sorted(directory.iterdir()):
            if entry.name.casefold() in folded:
                fail('skill.invalid', 'Case-colliding source entries.', path=str(entry))
            folded.add(entry.name.casefold())
            observed = kind(entry)
            if observed == 'directory':
                walk(entry)
            elif observed == 'file':
                files[entry.relative_to(root).as_posix()] = entry.read_bytes()
            else:
                fail('skill.path_escape', 'Source package contains a link or special entry.', path=str(entry))
    walk(root)
    if 'SKILL.md' not in files:
        fail('skill.invalid', 'SKILL.md is missing.', skill=identifier)
    try:
        text = files['SKILL.md'].decode('utf-8')
    except UnicodeError:
        fail('skill.invalid', 'SKILL.md must be UTF-8.')
    facts = metadata(text, identifier)
    answer = dict(id=identifier, asset_path=str(root), description=facts['description'], valid=True,
                  scope='mask-package-v1', issues=[], fingerprint=digest({name: digest(data) for name, data in files.items()}))
    if content:
        answer['content'] = text
    return answer


def catalog(source):
    base = source / 'skills'
    if kind(base) != 'directory':
        fail('source.missing', 'Source must contain a real skills directory.')
    entries, folded = [], set()
    for path in sorted(base.iterdir()):
        if path.name.casefold() in folded:
            fail('skill.invalid', 'Case-colliding skill IDs.')
        folded.add(path.name.casefold())
        try:
            entries.append(package(source, path.name))
        except MaskError as error:
            entries.append(dict(id=path.name, asset_path=str(path), valid=False, description=None,
                                scope='mask-package-v1', issues=[error.as_dict()]))
    return entries


def empty_state():
    return dict(schema_version=1, generation=0, projects={}, launchers={})


def state(value):
    fields(value, ('schema_version', 'generation', 'projects', 'launchers'), ('user',), family='state', versions=(1, 2))
    if (value['schema_version'] == 1 and 'user' in value) or (value['schema_version'] == 2 and 'user' not in value):
        fail('state.invalid', 'User records require state version 2.')
    user = value.get('user')
    if user is not None and (not isinstance(user, dict) or not isinstance(user.get('root'), str)):
        fail('state.invalid', 'Invalid user record.')
    if type(value['generation']) is not int or value['generation'] < 0 or not isinstance(value['projects'], dict) or not isinstance(value['launchers'], dict):
        fail('state.invalid', 'Invalid generation or registry maps.')
    for key, record in value['launchers'].items():
        fields(record, ('program_root', 'interpreter', 'content_digest'), family='state')
        if not isinstance(key, str) or not Path(key).is_absolute() or Path(key).name not in ('mask', 'mask.cmd') or any(not isinstance(record[item], str) or not Path(record[item]).is_absolute() for item in ('program_root', 'interpreter')) or not isinstance(record['content_digest'], str) or not re.fullmatch('sha256:[0-9a-f]{64}', record['content_digest']):
            fail('state.invalid', 'Invalid launcher ownership.')
    if user and user['root'] in value['projects']:
        fail('state.invalid', 'User and project roots overlap.')
    for key, record in consumer_records(value).items():
        fields(record, ('root', 'root_identity', 'last_manifest', 'last_manifest_digest', 'last_source_revision', 'links'), family='state')
        if not isinstance(key, str) or not Path(key).is_absolute() or key != record['root'] or os.path.normpath(key) != key:
            fail('state.invalid', 'Noncanonical registry root.')
        fields(record['root_identity'], ('device', 'inode'), family='state')
        if any(type(v) is not int for v in record['root_identity'].values()):
            fail('state.invalid', 'Invalid root identity.')
        previous_manifest = manifest(record['last_manifest'])
        if not isinstance(record['last_manifest_digest'], str) or record['last_manifest_digest'] != digest(previous_manifest):
            fail('state.invalid', 'Invalid cached manifest digest.')
        revision = record['last_source_revision']
        if revision is not None and (not isinstance(revision, str) or not re.fullmatch(r'[0-9a-f]{40,64}', revision)):
            fail('state.invalid', 'Invalid recorded source revision.')
        if not isinstance(record['links'], dict):
            fail('state.invalid', 'Invalid ownership map.')
        for relative, link in record['links'].items():
            fields(link, ('skill', 'target', 'link_text'), family='state')
            skill_id(link['skill'])
            if not isinstance(link['target'], str) or link['target'] not in ADAPTERS or relative != f"{ADAPTERS[link['target']]}/{link['skill']}" or not isinstance(link['link_text'], str) or not link['link_text']:
                fail('state.invalid', 'Unsafe ownership path or link record.')
    return value


def consumer_records(value):
    """A root is unique across scopes; the user record remains explicit on disk."""
    records = dict(value['projects'])
    if value.get('user') is not None:
        records[value['user']['root']] = value['user']
    return records


def consumer_scope(value, root):
    user = value.get('user')
    return 'user' if user and user['root'] == str(root) else 'project'


def set_consumer(value, root, record, scope):
    if scope == 'user':
        value.update(schema_version=2, user=record)
    elif record is None:
        value['projects'].pop(str(root), None)
    else:
        value['projects'][str(root)] = record


def declaration_path(root, scope='project', home=None):
    if scope == 'user':
        if home is None:
            fail('internal.invariant', 'User declarations require the selected MASK home.', 10)
        return Path(home) / 'user.json'
    return Path(root) / '.mask.json'


def consumer_manifest(root, scope='project', home=None):
    return manifest(read_json(declaration_path(root, scope, home), 'manifest'))


def registration_safe(root, source, home, value, scope):
    if str(root) in consumer_records(value) and consumer_scope(value, root) != scope:
        fail('target.overlap', 'The root is already registered in another scope.', 4, root=str(root))
    for adapter in ADAPTERS.values():
        destination = root / adapter
        if source.is_relative_to(destination) or (home is not None and home.is_relative_to(destination)) or destination.is_relative_to(source / 'skills') or root == home:
            fail('config.invalid', 'Managed source, state and destination locations overlap.')
        parents_safe(root, destination / 'mask-registration-check')
        for known in consumer_records(value):
            if known == str(root):
                continue
            for other_adapter in ADAPTERS.values():
                other = Path(known) / other_adapter
                if destination.is_relative_to(other) or other.is_relative_to(destination):
                    fail('target.overlap', 'Registered consumer destinations overlap.', 4, path=str(destination), other=str(other))


def project_root(selection=None, *, initializing=False, cwd=None):
    if selection is not None:
        root = Path(selection).expanduser().resolve()
        if not root.is_dir():
            fail('project.not_found', 'Project directory does not exist.', root=str(root))
        return root
    cwd = Path(cwd or Path.cwd()).resolve()
    top = git(cwd, 'rev-parse', '--show-toplevel', optional=True)
    if top is None:
        fail('project.not_found', 'Outside Git, select an explicit --project root.')
    boundary = Path(top).resolve()
    if initializing:
        return boundary
    current = cwd
    while current.is_relative_to(boundary):
        if kind(current / '.mask.json') != 'missing':
            return current
        if current == boundary:
            break
        current = current.parent
    fail('manifest.missing', 'No declaration found within the current Git worktree.')


def project_manifest(root):
    return manifest(read_json(root / '.mask.json', 'manifest'))


def registry_record(root, declaration, source):
    return dict(root=str(root), root_identity=identity(root), last_manifest=declaration,
                last_manifest_digest=digest(declaration), last_source_revision=git(source, 'rev-parse', 'HEAD', optional=True), links={})


def registered_root(root, record, scope='project'):
    if not root.is_dir():
        fail(scope + '.unavailable', 'Registered consumer is unavailable.', 4, root=str(root))
    if root.resolve() != root or identity(root) != record['root_identity']:
        fail(scope + '.identity_changed', 'Registered directory identity changed.', 4, root=str(root))


def save_state(home, before, after):
    if before == after:
        return False
    after['generation'] = before['generation'] + 1
    state(after)
    return atomic_text(home / 'state.json', text_json(after), read_text(home / 'state.json', 'state', missing=True))
