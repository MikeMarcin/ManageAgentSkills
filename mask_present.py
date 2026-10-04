"""Human presentation for MASK results (RFC-MASK-0018, contract section 5).

Every registered command renders the same structured result object that
``--json`` emits; nothing here decides, mutates or re-derives engine facts.
``RENDERERS`` is the coverage table: a command without an explicit entry is a
defect that ``tests.test_human_output`` rejects, not a case for dumping JSON.
Success text goes to stdout, errors to stderr; terminal color is applied only at emission.
"""
from __future__ import annotations

import os
import re
import shlex
import textwrap

CONTROL = re.compile(r'[\x00-\x08\x0b-\x1f\x7f-\x9f]')


def clean(value):
    """Render one value as sanitized text; untrusted control characters never pass through."""
    if value is None:
        return '-'
    if isinstance(value, bool):
        return 'yes' if value else 'no'
    if isinstance(value, (list, tuple)):
        return ', '.join(clean(item) for item in value) if value else '-'
    if isinstance(value, dict):
        return ', '.join(f'{clean(key)}={clean(item)}' for key, item in value.items()) if value else '-'
    text = CONTROL.sub('?', str(value)).replace('\n', ' ')
    # A value that is a path under the home directory reads as ~/...; sentences and copy-paste commands are left alone.
    home = os.path.expanduser('~')
    if text == home:
        text = '~'
    elif len(home) > 1 and text.startswith(home + os.sep):
        text = '~' + text[len(home):]
    return text


# A renderer marks one trusted word for color as SO tone GS word SI. clean() turns those control characters in any
# value into '?', so only renderer code can produce a mark; paint() colors marks on a terminal and strips them elsewhere.
MARK = re.compile('\x0e([a-z]+)\x1d([^\x0e\x0f]*)\x0f')
INLINE = {'ok': '32', 'warn': '33', 'dim': '2'}


def mark(text, tone):
    return f'\x0e{tone}\x1d{text}\x0f'


def scrub(line):
    """Replace stray control characters in a rendered line; a well-formed mark survives with its word scrubbed too."""
    parts, last = [], 0
    for match in MARK.finditer(line):
        parts += [CONTROL.sub('?', line[last:match.start()]), mark(CONTROL.sub('?', match.group(2)), match.group(1))]
        last = match.end()
    return ''.join(parts) + CONTROL.sub('?', line[last:])


def paint(text, stream, *, tone='success'):
    """Decorate trusted structure after values are sanitized; pipes stay byte-for-byte plain."""
    if not stream.isatty() or 'NO_COLOR' in os.environ or os.environ.get('TERM') == 'dumb':
        return MARK.sub(lambda match: match.group(2), text)
    text = MARK.sub(lambda match: f'\x1b[{INLINE.get(match.group(1), "1")}m{match.group(2)}\x1b[0m', text)
    lines = text.splitlines(keepends=True)
    if not lines:
        return text
    color = {'success': '1;32', 'error': '1;31', 'review': '1;36', 'progress': '2'}.get(tone, '1')
    index = 0
    if tone == 'error':
        index = next((i for i, line in enumerate(lines) if line.lower().startswith('error:')), 0)
    lines[index] = f'\x1b[{color}m' + lines[index].rstrip('\n') + '\x1b[0m' + ('\n' if lines[index].endswith('\n') else '')
    return ''.join(lines)


def short(commit):
    return clean(commit[:7]) if isinstance(commit, str) and commit else '-'


def pairs(rows):
    """Aligned ``label  value`` lines; a row whose value is None or empty is left out."""
    rows = [(label, clean(value)) for label, value in rows if value not in (None, '', [], {})]
    width = max((len(label) for label, _ in rows), default=0)
    return [f'  {label.ljust(width)}  {value}' for label, value in rows]


def note(data):
    """The one honest caveat every readiness report carries, said once and plainly."""
    return ['  Whether a running agent has loaded these skills is not something MASK can check.'] if data.get('host_load') == 'not_verified' else []


ACTION_VERBS = {'link.create': 'create link', 'link.remove': 'remove link', 'link.replace': 'replace link', 'link.adopt': 'adopt link', 'link.abandon': 'release link',
                'native_role.write': 'write role', 'retired_file.remove': 'remove retired file', 'declaration.write': 'write', 'declaration.create': 'create',
                'lock.write': 'write', 'native_role_lock.write': 'write', 'launcher.install': 'install launcher', 'setup.run': 'run setup', 'config.create': 'create configuration',
                'config.migrate': 'convert configuration', 'launcher.remove': 'remove launcher', 'source.catalog': 'update tap catalog', 'integration.record': 'record integration', 'skill.import': 'import skill'}


def action_lines(output, roots=()):
    """Every planned or applied action, one short line each: a verb and the path relative to its consumer. --json keeps the store targets."""
    lines, bases = [], sorted((str(root) for root in roots), key=len, reverse=True)
    for action in output.get('actions', []):
        if action.get('kind') == 'state.record':
            continue
        target = str(action.get('path') or action.get('root') or '')
        for base in bases:
            if target.startswith(base + os.sep):
                target = target[len(base) + 1:]
                break
        status = action.get('status', 'planned')
        mark = {'planned': '', 'applied': ''}.get(status, f' [{clean(status)}]')
        lines.append(f"  {ACTION_VERBS.get(action.get('kind'), clean(action.get('kind'))):<12} {clean(target)}{mark}".rstrip())
    return lines


def table(rows, columns):
    """Padded ASCII columns. Cells are never clipped, so narrow terminals wrap without losing facts."""
    cells = [[clean(row.get(key)) for _, key in columns] for row in rows]
    widths = [max(len(label), *(len(row[index]) for row in cells)) if cells else len(label) for index, (label, _) in enumerate(columns)]
    lines = ['  ' + '  '.join(label.ljust(widths[index]) for index, (label, _) in enumerate(columns)).rstrip()]
    for row in cells:
        lines.append('  ' + '  '.join(cell.ljust(widths[index]) for index, cell in enumerate(row)).rstrip())
    return lines


def fields(data, spec):
    """Labelled key/value lines for the keys in ``spec`` that the result carries."""
    return [f'  {label}: {clean(data[key])}' for label, key in spec if key in data]


def outcome(output):
    if output['dry_run']:
        return 'changes planned (dry run: nothing applied)' if output['would_change'] else 'nothing to change (dry run)'
    if output['changed']:
        return 'done' if output['transaction'] == 'committed' else f"changed ({output['transaction']})"
    if output['would_change']:
        return 'changes proposed, nothing applied'
    return '' if output['transaction'] == 'not_needed' and 'plan_hash' not in output['data'] else 'nothing to change'


def headline(output, title=None):
    name, result = (title or output['command']).replace('.', ' '), outcome(output)
    return name[0].upper() + name[1:] + (': ' + result if result else '')


def actions(output):
    lines = []
    for action in output.get('actions', []):
        what = clean(action.get('kind'))
        target = action.get('path') or action.get('root') or ''
        extra = ' -> ' + clean(action['source']) if action.get('source') else ''
        lines.append(f"  {action.get('status', 'planned')}: {what} {clean(target)}{extra}".rstrip())
    return lines


ACTION_NOUNS = {'link.create': ('link', 'created'), 'link.remove': ('link', 'removed'), 'link.replace': ('link', 'replaced'),
                'native_role.write': ('role file', 'written'), 'retired_file.remove': ('retired file', 'removed')}
QUIET_ACTIONS = ('state.record', 'declaration.write', 'declaration.create', 'lock.write', 'native_role_lock.write')  # Bookkeeping, not news.


def plural(count, noun):
    return f"{count} {noun[:-1] + 'ies' if count != 1 and noun.endswith('y') else noun + ('' if count == 1 else 's')}"


def joined(items):
    items = [clean(item) for item in items]
    return ', '.join(items[:-1]) + (' and ' if len(items) > 1 else '') + items[-1] if items else '-'


def action_summary(output):
    """One line of counts in place of one line per action; ``plan``, ``apply`` and ``--json`` keep every path."""
    counts = {}
    for action in output.get('actions', []):
        if action.get('kind') not in QUIET_ACTIONS:
            status = 'unknown' if action.get('effects') == 'unknown' else action.get('status', 'planned')
            key = (status, action.get('kind'))
            counts[key] = counts.get(key, 0) + 1
    parts = []
    for (status, kind), count in counts.items():
        noun, verb = ACTION_NOUNS.get(kind, (clean(kind), 'done'))
        parts.append(f"{plural(count, noun)} " + ('with unconfirmed changes' if status == 'unknown' else
                     verb if status == 'applied' else 'to be ' + verb if status == 'planned' else verb + ' (' + clean(status) + ')'))
    return ['  ' + ', '.join(parts) + '.'] if parts else []


def place(data):
    return 'your personal skills' if data.get('scope') == 'user' else clean(data.get('root'))


def plan_guard(data, output):
    lines = []
    if output['would_change'] and not output['changed'] and data.get('plan_hash'):
        lines.append(f"  Apply exactly this with --approve-plan {data['plan_hash']}")
    return lines


# --- layouts -----------------------------------------------------------------

def summary(title=None, spec=()):
    def render(data, output):
        lines = [headline(output, title)] + fields(data, spec)
        return lines + actions(output) + plan_guard(data, output)
    return render


def change(title=None, spec=()):
    """Reconciliation-shaped results: a sentence for the outcome, then each action as a verb and a relative path."""
    def render(data, output):
        roots = [entry.get('root') for key in ('projects', 'users') for entry in data.get(key, []) or []]
        where = clean(roots[0]) if len(roots) == 1 else plural(len(roots), 'scope') if roots else None
        count = sum(action.get('kind') != 'state.record' for action in output.get('actions', []))
        name = (title or output['command']).replace('.', ' ')
        if data.get('blockers'):
            head = f"{name.capitalize()}: blocked" + (f' in {where}' if where else '') + '.'
        elif not count and not output['would_change'] and not output['changed']:
            head = f"Nothing to change: {where} already matches its declaration." if where else f'{name.capitalize()}: nothing to change.'
        elif output['changed']:
            head = f"Applied {plural(count, 'change')}" + (f' to {where}' if where else '') + ('.' if output['transaction'] == 'committed' else f" ({output['transaction']}).")
        else:
            head = f"{plural(count, 'change')} planned" + (f' for {where}' if where else '') + (' (dry run: nothing applied).' if output['dry_run'] else '; nothing applied yet.')
        lines = [head[0].upper() + head[1:]] + fields(data, [item for item in spec if item[1] not in ('root', 'scope', 'network', 'registered', 'mode')])
        if len(roots) > 1:
            lines.extend(f'  {clean(root)}' for root in roots)
        for blocker in data.get('blockers', []) or []:
            lines.append(f"  blocked: {clean(blocker.get('message'))} ({clean(blocker.get('code'))})")
        differing = [row for row in data.get('shadowing') or [] if not row.get('same_target')]
        if differing:
            lines.append(f"  shadowing: {plural(len(differing), 'scope overlap')} resolving to different targets; see warnings")
        lines.extend(action_lines(output, roots))
        return lines + plan_guard(data, output)
    return render


def render_help(data, output):
    return data['help'].rstrip('\n').split('\n')


def render_version(data, output):
    return [f"mask {data['version']}"]


def render_capabilities(data, output):
    commands = data.get('commands', [])
    lines = [f"mask {output['tool_version']} capabilities: {len(commands)} commands, protocol result schema {(data.get('schemas') or {}).get('result', 1)}",
             f"  program: {clean(data.get('program_root'))}", f"  python: {clean(data.get('python_minimum'))}+",
             f"  targets: {clean(data.get('targets'))}", f"  scopes: {clean(data.get('scopes'))}"]
    workflow = data.get('workflow') or {}
    if workflow:
        lines.append(f"  workflow: {clean(workflow.get('readiness'))} on {clean(workflow.get('entrypoints'))}; native roles {'typed' if workflow.get('native_roles') else 'unsupported'}; staged setup {'by approval' if workflow.get('staged_setup') else 'unsupported'}; host loading {clean(workflow.get('host_load'))}")
    rows = [dict(name=item['name'], effect='mutates' if item['effect'] == 'managed_mutation' else 'observes',
                 network='network' if item['network'] else '-', guard='plan hash' if item['plan_guard'] else '-') for item in commands]
    lines.extend(table(rows, [('COMMAND', 'name'), ('EFFECT', 'effect'), ('NETWORK', 'network'), ('GUARD', 'guard')]))
    lines.append("  run 'mask COMMAND --help' for arguments; add --json for the machine protocol")
    return lines


STATUS_WORDS = dict(managed_converged='ok', managed_drifted='drifted', declared_not_deployed='missing', unmanaged_present='unmanaged',
                    blocked='blocked', unavailable_consumer='unavailable')


def render_inventory(data, output):
    rows, agents = {}, []
    links, consumers, total = data.get('rows', []), data.get('consumers', []), data.get('total_rows', 0)
    for row in links:
        key = (row['root'], row['scope'], row.get('skill') or row['name'], row.get('content_mode'))
        entry = rows.setdefault(key, dict(skill=row.get('skill') or row['name'], source=(row.get('source') or {}).get('alias') or '-',
                                          content=row.get('content_mode'), pinned=row.get('pinned', False), states={}, notes=[]))
        agent = row['agent']
        if agent not in agents:
            agents.append(agent)
        state = STATUS_WORDS.get(row['status'], row['status'])
        if row.get('error'):
            state += f" ({clean(row['error'].get('code'))})"
        entry['states'][agent] = state
        if not row.get('declared') and row.get('owned'):
            entry['notes'].append('owned but no longer declared')
        if row.get('pinned') and 'version held' not in entry['notes']:
            entry['notes'].append('version held')
    lines = [f"Inventory: {plural(len(rows), 'skill')}, {plural(len(links), 'link')}" + ('' if len(links) == total else f' shown of {total}')]
    if not links and not consumers:
        lines.append('  No registered project or personal scope is selected.')
    for consumer in consumers:
        line = f"  {clean(consumer['root'])}" + (' (personal)' if consumer['scope'] == 'user' else '')
        extras = ([] if consumer.get('available') else ['unavailable']) + ([consumer['mode']] if consumer.get('mode') not in (None, 'pinned') else []) + \
            ([clean(consumer['declaration_basis']).replace('_', ' ')] if consumer.get('declaration_basis') not in (None, 'live_declaration') else [])
        lines.append(line + (': ' + ', '.join(extras) if extras else ''))
        if consumer.get('error'):
            lines.append(f"    problem: {clean(consumer['error'].get('message'))} ({clean(consumer['error'].get('code'))})")
        for problem in consumer.get('discovery_errors', []):
            lines.append(f"    discovery: {clean(problem.get('message'))}")
    if rows:
        columns = [('SKILL', 'skill'), ('CONTENT', 'content')] + [(agent.upper(), agent) for agent in sorted(agents)] + ([('NOTES', 'notes')] if any(entry['notes'] for entry in rows.values()) else [])
        table_rows = [dict(skill=entry['skill'], source=entry['source'], content=entry['content'], notes=entry['notes'] or None,
                           **{agent: entry['states'].get(agent, 'not observed') for agent in agents}) for entry in rows.values()]
        lines += ['', *table(table_rows, columns), '']
    elif consumers:
        lines.append('  No skills are declared or deployed there.')
    if data.get('next_offset') is not None:
        lines.append(f"  More rows follow this page; continue with --offset {data['next_offset']}")
    if not data.get('complete', True):
        lines.append('  Incomplete: at least one scope could not be fully observed.')
    for limitation in data.get('limitations', []):
        lines.append(f'  note: {clean(limitation)}')
    return lines


def render_where_used(data, output):
    shown, total = len(data.get('rows', [])), data.get('total_rows', 0)
    lines = [f"Where used: {plural(shown, 'link')}" + ('' if shown == total else f' shown of {total}')]
    lines.extend(table(data.get('rows', []), [('SKILL', 'name'), ('SCOPE', 'scope'), ('AGENT', 'agent'), ('STATE', 'status'), ('PATH', 'path')]))
    if data.get('next_offset') is not None:
        lines.append(f"  More rows follow this page; continue with --offset {data['next_offset']}")
    return lines


def render_catalog(data, output):
    skills = data.get('skills', [])
    lines = [f"{plural(len(skills), 'skill')} in your fetched taps"]
    if data.get('resolution_required'):
        lines.append(f"  Not fetched yet: {clean(data.get('unresolved_sources'))}. Run 'mask update' first.")
    if skills:
        rows = [dict(id=item.get('id') or item.get('name'), valid='ok' if item.get('valid', True) else 'invalid',
                     source=item.get('source') or item.get('scope') or '-', description=item.get('description')) for item in skills]
        lines.extend(table(rows, [('SKILL', 'id'), ('STATE', 'valid'), ('SOURCE', 'source'), ('DESCRIPTION', 'description')]))
        for item in skills:
            for issue in item.get('issues', []) or []:
                lines.append(f"  {clean(item.get('id'))}: {clean(issue.get('message'))}")
    elif not data.get('resolution_required'):
        lines.append("  None found. Approve a tap with 'mask tap NAME URL', then run 'mask update'.")
    return lines


def render_skill(data, output):
    lines = [f"skill {clean(data.get('id'))}: {'valid' if data.get('valid', True) else 'invalid'}"]
    lines.extend(fields(data, [('description', 'description'), ('path', 'asset_path'), ('digest', 'digest'), ('scope', 'scope')]))
    if output['command'] == 'info':
        lines.extend(fields(data, [('source', 'source'), ('commit', 'commit')]))
        for scope, contract in data.get('workflow', {}).items():
            lines.append(f"  {scope} workflow: {len(contract['roles'])} native roles; {len(contract['setup'])} setup actions")
            lines.extend(f"    setup: {clean(name)} ({clean(action.get('entrypoint'))})" for name, action in contract['setup'].items())
            lines.extend(f"    input: {clean(row['path'])}" for row in contract['inputs'] if row['required'])
    for issue in data.get('issues', []) or []:
        lines.append(f"  issue: {clean(issue.get('message'))}")
    if data.get('content'):
        lines.append('  --- SKILL.md ---')
        lines.extend(CONTROL.sub('?', str(data['content'])).rstrip('\n').split('\n'))
    return lines


def render_projects(data, output):
    projects = data.get('projects', [])
    lines = [f"{plural(len(projects), 'registered project')}"]
    if not projects:
        lines.append("  None yet. 'mask install ID' in a project registers it.")
    for record in projects:
        extras = ([] if record.get('available') else ['unavailable']) + ([clean(record['mode'])] if record.get('mode') != 'pinned' else [])
        lines.append(f"  {clean(record.get('root'))}  {plural(len(record.get('links', {})), 'link')}" + (f" ({', '.join(extras)})" if extras else ''))
    return lines


def render_show(data, output):
    scope = data.get('scope', 'project')
    lines = [f"{'Personal skills' if scope == 'user' else 'Project'} {clean(data.get('root'))}" + ('' if data.get('registered') else ' (not registered)')]
    manifest = data.get('manifest') or {}
    skills = manifest.get('skills')
    if isinstance(skills, list):
        skills = [item['source'] + '/' + item['id'] if isinstance(item, dict) and 'source' in item and 'id' in item else item for item in skills]
    requested, effective = data.get('requested_targets'), data.get('effective_targets')
    lines.extend(pairs([('declaration', data.get('manifest_path')), ('skills', skills if skills is None else (skills or 'none')),
                        ('agents', effective if effective is not None else manifest.get('targets')),
                        ('requested agents', requested if requested != effective else None),
                        ('mode', data.get('mode') if data.get('mode') != 'pinned' else None),
                        ('owned links', len(data['ownership']) if 'ownership' in data else None)]))
    for blocker in data.get('blockers', []) or []:
        lines.append(f"  blocked: {clean(blocker.get('message'))}")
    differing = [row for row in data.get('shadowing') or [] if not row.get('same_target')]
    if differing:
        lines.append(f"  shadowing: {plural(len(differing), 'scope overlap')} resolving to different targets")
    return lines + plan_guard(data, output)


def render_doctor(data, output):
    if 'identity_canonicalization' in data and 'config' in data:  # doctor --migrate (RFC-MASK-0022)
        rows = data['identity_canonicalization']
        if not rows:
            return ['Every tap already uses its transport-neutral identity. Nothing to do.']
        lines = [f"Would update {plural(len(rows), 'tap')} to its transport-neutral identity (dry run: nothing written)." if output['dry_run'] else
                 f"Updated {plural(len(rows), 'tap')} to its transport-neutral identity." if output['changed'] else f"{plural(len(rows), 'tap')} to update; nothing written."]
        for row in rows:
            lines += [f"  {clean(row.get('source'))}  {clean(row.get('after'))}", f"    was {clean(row.get('before'))}; still reached over {clean(row.get('transport'))}"]
        return lines + ['  Only the machine catalog changes: no project file, link or cache is touched.'] + plan_guard(data, output)
    if output['command'] == 'status':
        lines = ['Status: ready.' if data.get('healthy') else 'Status: problems found.']
        lines.extend(f"  {clean(row['scope'])}: {clean(row['root'])}" for row in data.get('scopes', []))
    else:
        lines = ['Everything MASK manages looks healthy.' if data.get('healthy') else 'Doctor found problems.']
    for issue in data.get('issues', []) or []:
        lines.append(f"  problem: {clean(issue.get('message') if isinstance(issue, dict) else issue)}")
    if data.get('symlink_capability') not in (None, 'available'):
        lines.append(f"  symlinks: {clean(data['symlink_capability'])}")
    extra = (data.get('forge_hosts') or {}).get('machine')
    if extra:
        lines.append(f'  extra forge hosts on this machine: {clean(extra)}')
    for blocker in data.get('blockers', []) or []:
        lines.append(f"  blocked: {clean(blocker.get('message'))}")
    lines.extend(workflow_lines(data, verb='would be deployed by'))
    if output['would_change']:
        lines.append("  Links or roles differ from the declaration; 'mask repair' reconciles them.")
    return lines + note(data)


READINESS_WORDS = dict(ready_pinned='ready', ready_dev_link='ready (development link, not pinned)', inactive_on_branch='inactive on this branch',
                       would_reconcile='changes needed', workflow_incomplete='setup incomplete', approval_required='approval required',
                       confirmation_required='confirmation required', drifted='drifted', blocked='blocked')


def render_ensure(data, output):
    if data.get('repair'):
        return repair_lines(data, output) + backup_lines(data)
    scopes = data.get('scope_readiness', []) or []
    word = READINESS_WORDS.get(data.get('readiness'), clean(data.get('readiness')))
    if len(scopes) == 1:
        head = f"{READINESS_WORDS.get(scopes[0].get('readiness'), clean(scopes[0].get('readiness')))}: {clean(scopes[0].get('root'))}"
    else:
        head = f"{word}: {plural(len(scopes), 'scope')}" if scopes else f'Readiness: {word}'
    if output['dry_run']:
        head += ' (dry run: changes needed, nothing applied)' if output['would_change'] else ' (dry run: no changes needed)'
    elif output['changed']:
        head += ' (fixed just now)' if output['transaction'] == 'committed' else f" ({output['transaction']})"
    lines = [head[0].upper() + head[1:]]
    if len(scopes) > 1:
        lines.extend(f"  {clean(item.get('root'))}: {READINESS_WORDS.get(item.get('readiness'), clean(item.get('readiness')))}" for item in scopes)
    if data.get('event') not in (None, 'manual'):
        lines.append(f"  event: {clean(data['event'])}")
    if data.get('network') not in (None, 'none'):
        lines.append(f"  network: {clean(data['network'])}")
    for blocker in data.get('blockers', []) or []:
        lines.append(f"  blocked: {clean(blocker.get('message'))}")
    # A quiet "ready" is enough until this invocation changed something or ran setup; then the per-skill verdict is the news.
    lines.extend(workflow_lines(data, quiet_ready=not (output['changed'] or (data.get('setup') or {}).get('actions'))))
    lines.extend(setup_lines(data))
    lines.extend(action_summary(output))
    if data.get('approval') == 'not_approved' and data.get('readiness') != 'approval_required':
        lines.append("  Automatic startup checks: not approved ('mask integration approve' enables them).")
    if data.get('readiness') == 'approval_required':
        lines.append("  approve the consumer with 'mask integration approve --project ROOT' before automatic readiness")
    confirmation = data.get('confirmation')
    if confirmation and confirmation.get('granted_by'):
        lines.append(f"  one-time readiness granted by {clean(confirmation['granted_by'])}; automatic readiness still needs 'mask integration approve'")
    elif confirmation:
        lines.append("  would ask for one-time readiness consent; automatic readiness still needs 'mask integration approve'")
    if output['changed']:
        lines.append('  Restart running agents to load the change.')
    return lines + plan_guard(data, output)


def workflow_lines(data, verb='will be deployed from', quiet_ready=False):
    """Declared native roles and consumer inputs per consumer: what matches, what is preserved, what will be deployed.

    ``quiet_ready`` leaves out skills that are complete with nothing pending, for results where only news belongs.
    """
    if data.get('workflow_readiness_observation') == 'before_setup':
        return []  # Completed/partial setup below is newer than this snapshot.
    lines = []
    for entry in data.get('workflow_readiness', []) or []:
        declared = [skill for skill in entry.get('skills', []) or [] if skill.get('workflow') == 'declared'
                    and not (quiet_ready and skill.get('complete') and all(row.get('state') in ('ok', 'not_applicable') for row in skill.get('roles') or [])
                             and all(row['state'] == 'absent' for row in skill.get('retired_files', [])))]
        if declared:
            lines.append(f"  {clean(entry.get('scope', 'project'))}: {clean(entry.get('root'))}")
        for skill in declared:
            pending_roles = any(row.get('state') not in ('ok', 'not_applicable') for row in skill.get('roles') or [])
            status = 'needs deployment' if skill.get('complete') and pending_roles else 'ready' if skill.get('complete') else 'needs attention'
            lines.append(f"    {clean(skill.get('skill'))}: {status}")
            for row in skill.get('retired_files', []):
                if row['state'] != 'absent':
                    note = {'present': 'retired; preview cleanup to remove safely', 'remove_planned': 'will back up and remove',
                            'in_use': 'fallback lock preserved until a canonical lock is published', 'unsafe': 'unsafe retired entry; preserved',
                            'active_input': 'still declared as a consumer input; preserved'}.get(row['state'], row['state'])
                    lines.append(f"      {clean(row['path'])}: {note}")
            for row in skill.get('inputs', []) or []:
                if row.get('state') not in ('ok', 'absent'):
                    lines.append(f"      input {clean(row.get('path'))}: {clean(row.get('state'))}")
            groups = {}
            for row in skill.get('roles', []) or []:
                state = row.get('state')
                if state in ('ok', 'not_applicable'):
                    continue
                note = {'missing': f'{verb} the package', 'stale': f'managed copy {verb} the package'}.get(state) or row.get('detail') or 'preserved'
                label = {'setup_required': 'setup needed', 'modified': 'existing files differ', 'collision': 'destination conflict'}.get(state, state)
                if state == 'setup_required' and row.get('observed_sha256') and row.get('ownership') != 'package-managed':
                    label = 'existing files need review'
                if data.get('repair') and state in ('setup_required', 'modified', 'stale'):
                    label = 'will regenerate' if row.get('producer') == 'setup' else 'will replace'
                    note = 'Repair will back up existing role files before replacing them.'
                groups.setdefault((label, note), []).append(row)
            for (label, note), roles in groups.items():
                lines.append(f"      {len(roles)} role file(s): {clean(label)}")
                # Missing generated output needs one diagnosis; conflicts still name every file.
                if all(row.get('state') == 'setup_required' and not row.get('observed_sha256') for row in roles):
                    continue
                lines.append(f"      {clean(note)}")
                lines.extend(f"        {clean(row.get('path') or str(row.get('agent')) + '/' + str(row.get('name')))}" for row in roles)
    return lines


SETUP_NOTES = {
    'consent_required': 'needs approval of this task; preview it, then use --approve-plan HASH',
    'not_run': 'check, dry-run and event invocations never run package code',
    'declined': 'nothing ran',
    'granted': 'approved; not run',
    'published': 'ran, validated and published',
    'partial': 'ran; some outputs were preserved instead of published',
    'blocked': 'cannot run',
}


def setup_lines(data):
    """Declared setup actions: what would run, under which authority, and what happened (never a copy/paste command)."""
    lines = []
    setup = data.get('setup') or {}
    rows = setup.get('actions', []) or []
    if len(rows) > 1:
        lines.append('  Setup results:')
        for row in rows:
            state = {'published': 'done', 'granted': 'not started', 'consent_required': 'needs approval',
                     'partial': 'recovery needed'}.get(row.get('state'), row.get('state'))
            lines.append(f"    {clean(row.get('root'))}  {clean(row.get('subject'))}  {clean(state)}")
            if row.get('state') in ('blocked', 'failed', 'stale', 'partial') and row.get('detail'):
                lines.append(f"      {clean(row['detail'])}")
        return lines
    for row in rows:
        subject = clean(row.get('subject') or f"{row.get('coordinate')}:{row.get('action')}")
        note = SETUP_NOTES.get(row.get('state'), '').format(subject=subject)
        detail = row.get('detail') if row.get('state') not in SETUP_NOTES or row.get('state') in ('blocked', 'partial') else None
        lines.append(f"  setup {subject} in {clean(row.get('root'))}: {clean(row.get('state'))}" + (f"; {note}" if note else ''))
        if detail:
            lines.append(f"    {clean(detail)}")
        if row.get('granted_by'):
            lines[-1] += f" [granted by {clean(row['granted_by'])}]"
    return lines


def setup_proposal_lines(proposal):
    """The exact disclosure a human answers (contract section 5): skill, source, script, interpreter, targets, no sandbox."""
    lines = []
    for action in proposal.get('actions', []) or []:
        lines.append(f"  {clean(action.get('skill'))} needs consumer-specific native role setup.")
        lines.append(f"  Source: {clean(action.get('coordinate'))} (content fingerprint {clean(action.get('fingerprint'))})")
        lines.append(f"  Run: Python {clean(action.get('path'))}")
        lines.append(f"  Interpreter: {clean(action.get('interpreter'))}")
        lines.append(f"  Project: {clean(action.get('root'))}")
        roles = action.get('native_roles') or []
        lines.append(f"  Generate {len(roles)} role file(s):")
        lines.extend(f"    {clean(role)}" for role in roles)
    lines.append('  This runs package code with your user permissions; it is not sandboxed.')
    return lines


def render_recover(data, output):
    if not data.get('pending'):
        return ['recover: nothing pending']
    pending = data['pending']
    if pending.get('setup'):
        setup = pending['setup']
        root, skill = clean(setup['root']), clean(setup['skill'])
        recovered = output['changed'] and output['transaction'] in ('committed', 'rolled_back')
        if recovered:
            verb = 'Completed' if output['transaction'] == 'committed' else 'Rolled back'
            return [f'{verb} interrupted setup: {skill}', f'  Location: {root}',
                    '  No setup scripts were rerun.', '  Run mask repair again to check readiness, or retry your previous command.']
        staged = setup['phase'] == 'staged'
        lines = [f'Interrupted setup: {skill}', f'  Location: {root}',
                 f"  {len(pending.get('native_roles', []))} role files were validated before publication stopped." if staged else
                 '  Setup outputs were not validated; this attempt must be rolled back.',
                 '  Package script side effects are unknown and are not rolled back.']
        if data.get('recovery'):
            lines += ['  Repair will ' + ('finish the recorded publication' if staged else 'roll back this attempt') + '; no setup script will run.']
            if output['dry_run']:
                lines += plan_guard(data, output)
        else:
            lines += ['  Next: mask repair', '  Advanced: mask recover --complete --dry-run' if staged else '  Advanced: mask recover --rollback --dry-run']
        return lines
    lines = [f"recover: pending {clean(pending.get('operation') or pending.get('kind'))} ({clean(data.get('recovery_mode', 'inspect'))})"]
    lines.extend(fields(pending, [('generation', 'generation'), ('phase', 'phase'), ('scope', 'scope')]))
    if data.get('setup'):
        lines.append(f"  setup {clean(data['setup'].get('skill'))}: phase {clean(data['setup'].get('phase'))}; package script side effects are {clean(data['setup'].get('script_effects'))} and are not rolled back")
    lines.extend(actions(output))
    if data.get('retained_directories'):
        lines.append(f"  retained directories: {clean(data['retained_directories'])}")
    if output['changed']:
        lines.append(f"  transaction: {output['transaction']}")
    return lines


def render_self_status(data, output):
    launchers = data.get('launchers') or {}
    return [f"mask {output['tool_version']}"] + pairs([('program', data.get('program_root')), ('python', data.get('interpreter')), ('on PATH', data.get('path_command') or 'no'),
                                                        ('launchers', list(launchers) if isinstance(launchers, dict) and launchers else None)])


def render_uninstall(data, output):
    removed, kept = data.get('removed') or [], data.get('kept') or []
    lines = [(f"Would remove {plural(len(removed), 'launcher')} (dry run: nothing removed)." if output['dry_run'] else f"Removed {plural(len(removed), 'launcher')}.") if removed
             else 'No MASK launcher is recorded on this machine.']
    lines.extend(f'  - {clean(path)}' for path in removed)
    lines.extend(f"  kept {clean(item.get('path'))}: {clean(item.get('reason'))}" for item in kept)
    linked = data.get('linked_consumers') or []
    lines += ['', 'MASK never deletes folders for you. To finish by hand:']
    if linked:
        lines.append(f"  {plural(len(linked), 'project')} still link skills from MASK's store; first run 'mask project unregister PATH' (or 'mask user unregister') for each:")
        lines.extend(f'      {clean(path)}' for path in linked)
    lines.append(f"  rm -rf {shlex.quote(str(data.get('home')))}          # taps, store and state")
    lines.append(f"  rm -rf {shlex.quote(str(data.get('program_root')))}  # the program")
    return lines


def render_config(data, output):
    config = data.get('config') or {}
    if output['command'] == 'config.show':
        head = 'MASK configuration'
    else:
        head = 'Would change the configuration (dry run: nothing written).' if output['dry_run'] and output['would_change'] else \
            'Configuration updated.' if output['changed'] else 'Configuration already says that. Nothing to do.'
    lines = [head] + pairs([('taps', sorted(config.get('sources') or {}) or ('none' if 'sources' in config else None)),
                            ('default agents', config.get('default_targets')), ('git timeout', f"{config['git_timeout_seconds']} s" if 'git_timeout_seconds' in config else None),
                            ('extra forge hosts', config.get('forge_hosts')), ('machine state', data.get('home')), ('program', data.get('program_root'))])
    return lines


def tap_line(name, entry, width=0):
    return f"  {clean(name).ljust(width)}  {clean(entry.get('repository'))}  (follows {clean(entry.get('ref', 'main'))})"


def render_sources(data, output):
    command, name = output['command'], data.get('source')
    catalog = data.get('sources')
    if command == 'source.list' and isinstance(catalog, dict):
        width = max((len(item) for item in catalog), default=0)
        return [plural(len(catalog), 'approved tap')] + ([tap_line(item, entry, width) for item, entry in catalog.items()] or ["  None yet. Approve one with 'mask tap NAME URL'."])
    if command == 'source.repair-cache':
        return [headline(output)] + pairs([('retained cache', data.get('cache_retained')),
                ('next', 'mask tap fetch ' + clean(data.get('source')))]) + plan_guard(data, output)
    if command == 'source.show':
        binding = data.get('binding') or {}
        how = clean(data.get('transport')) + {'pinned': ' (pinned)', 'origin': " (follows the project's origin)", 'hint': ' (worked last time)', 'gh': ' (gh git_protocol)',
                                                'catalog': '', 'probe': ' (found by trying)'}.get(data.get('chosen_by'), '')
        return [f'Tap {clean(name)}'] + pairs([('repository', binding.get('repository')), ('follows', binding.get('ref')), ('packages', binding.get('packages') if binding.get('packages') != 'skills' else None),
                                               ('reached over', how), ('authoring checkout', binding.get('authoring')), ('line endings', data.get('line_endings') if data.get('line_endings') != 'exact' else None),
                                               ('fetched', short(data.get('cached_revision')) if data.get('cached_revision') else "not yet; run 'mask update'")])
    if command in ('tap.add', 'tap.remove', 'tap.transport'):
        verb = {'tap.add': ('Would approve the', 'Approved the', 'Already approved: the'), 'tap.remove': ('Would remove the', 'Removed the', 'Already absent: the'),
                'tap.transport': ('Would change how this machine reaches the', 'Changed how this machine reaches the', 'No change to how this machine reaches the')}[command]
        head = f"{verb[0] if output['dry_run'] and output['would_change'] else verb[1] if output['changed'] else verb[2]} tap {clean(data.get('tap') or name or '')}".rstrip()
        lines = [head + (' (dry run: nothing written).' if output['dry_run'] and output['would_change'] else '.')]
        lines.extend(pairs([('transport', data.get('transport')), ('policy', data.get('transport_policy')), ('line endings', data.get('line_endings') if data.get('line_endings') not in (None, 'exact') else None),
                            ('cache kept at', data.get('cache_retained'))]))
        if command == 'tap.add' and output['would_change']:
            lines.append("  Nothing is fetched yet; 'mask install ID' or 'mask update' fetches it.")
        return lines + plan_guard(data, output)
    lines = [headline(output, command.replace('.', ' '))]
    lines.extend(fields(data, [('source', 'source'), ('repository', 'repository'), ('ref', 'ref'), ('line endings', 'line_endings'), ('commit', 'commit'),
                               ('phase', 'phase'), ('created commit', 'created_commit'), ('created ref', 'created_ref'), ('pushed', 'pushed')]))
    if 'skills' in data and isinstance(data['skills'], list):
        lines.extend(render_catalog(data, output)[1:])
    return lines + action_lines(output) + plan_guard(data, output)


def consumer_count(rows):
    projects = sum(row.get('scope') != 'user' for row in rows)
    parts = ([plural(projects, 'project')] if projects else []) + (['personal skills'] if projects != len(rows) else [])
    return ' and '.join(parts) or 'no consumers'


def commit_lines(data):
    lines = []
    for row in data.get('commits') or []:
        label = clean(row['root']) + (' (personal)' if row['scope'] == 'user' else '')
        detail = clean(row['status']) + (f" {short(row['commit'])}" if row.get('commit') else '')
        lines.append(f'  Git commit: {label}: {detail}')
        if row['status'] == 'planned':
            lines.append('    paths: ' + ', '.join(row['paths']) + '; message: ' + clean(row['message']))
            if row['included_existing_changes']:
                lines.append('    includes existing changes: ' + ', '.join(row['included_existing_changes']))
        if row.get('error'):
            lines.append('    ' + clean(row['error']['message']) + ' (' + clean(row['error']['code']) + ')')
    return lines


def render_upgrade(data, output):
    """upgrade: fetch results, then the outcome, consumers and follow-ups that carry news."""
    rows = data.get('consumers') or []
    moved = sum(len(row.get('changes') or []) for row in rows)
    touched = consumer_count([row for row in rows if row.get('changes')])
    if output['dry_run']:
        head = f"Would upgrade {plural(moved, 'skill')} in {touched} (dry run: nothing fetched or applied)." if moved else \
            'Would reconcile links and workflow setup; no skill versions would change (dry run).' if output['would_change'] else 'Nothing to upgrade (dry run: cached taps only).'
    elif output['changed']:
        recorded = sum(bool(row.get('commit')) for row in data.get('commits') or [])
        head = f"Upgraded {plural(moved, 'skill')} in {touched}." if moved else \
            f"Recorded {plural(recorded, 'Git commit')}; no skill versions changed." if recorded and output['transaction'] == 'not_needed' else \
            'Reconciled links and workflow setup; no skill versions changed.'
        if output['transaction'] not in ('committed', 'not_needed'):
            head += f" Transaction: {output['transaction']}."
    elif output['would_change']:
        head = 'Upgrade proposed; nothing applied.'
    else:
        head = f'Already up to date ({consumer_count(rows)}).' if rows else 'Nothing to upgrade.'
    taps = fetch_lines(data)
    lines = (taps + [''] if taps else []) + [head]
    width = max((len(clean(item.get('coordinate'))) for row in rows for item in row.get('changes') or []), default=0)
    for row in rows:
        if not row.get('changes') and row.get('status') in ('unchanged', 'updated'):
            continue
        label = clean(row.get('root')) + (' (personal)' if row.get('scope') == 'user' else '')
        if row.get('status') not in ('unchanged', 'updated'):
            error = row.get('error') or {}
            label += f": {clean(row.get('status'))}" + (f" - {clean(error.get('message'))} ({clean(error.get('code'))})" if error else '')
        lines += ['', f'  {label}']
        if row.get('requires_fetch'):
            lines.append("    not in the cache yet; run 'mask upgrade' without --dry-run, --offline or --approve-plan to fetch it")
        lines.extend(f"    {clean(item.get('coordinate')).ljust(width)}  {clean((item.get('before_commit') or 'new')[:7])} -> {clean((item.get('after_commit') or 'removed')[:7])}"
                     for item in row.get('changes') or [])
    notes = []
    for blocker in data.get('blockers', []) or []:
        notes.append(f"  blocked: {clean(blocker.get('message'))} ({clean(blocker.get('code'))})")
    differing = [row for row in data.get('shadowing') or [] if not row.get('same_target')]
    if differing:  # Overlaps that resolve to one target are not news; --json still lists them.
        notes.append(f"  shadowing: {plural(len(differing), 'scope overlap')} resolving to different targets; see warnings")
    notes.extend(workflow_lines(data, quiet_ready=True))
    notes.extend(setup_lines(data))
    notes.extend(backup_lines(data))
    notes.extend(commit_lines(data))
    if output['changed'] and (moved or output['actions']):
        notes.append('  Restart running agents to load the new versions.')
    return lines + ([''] + notes if notes else []) + plan_guard(data, output)


CHANGE_TONE = {'comment': 'ok', 'additive': 'ok', 'breaking': 'warn'}


def schema_rows(migration, indent='    ', width=80):
    """One aligned row per changed schema: file, class word (colored on a terminal), and a summary cut to the width."""
    rows = migration.get('schemas') or []
    name_width = max((len(clean(row.get('file'))) for row in rows), default=0)
    lines = []
    for row in rows:
        change = clean(row.get('change'))
        room = max(width - len(indent) - name_width - 3 - 8 - 3, 12)
        summary = clean(row.get('summary'))
        summary = summary if len(summary) <= room else summary[:room - 3].rstrip() + '...'
        lines.append(f"{indent}{clean(row.get('file')):<{name_width}}   {mark(f'{change:<8}', CHANGE_TONE.get(change, 'warn'))}   {summary}")
    return lines


def commit_span(migration):
    commits = migration.get('commits')
    span = f"{short(migration.get('before'))} -> {short(migration.get('candidate'))}"
    return span + (f" ({plural(commits, 'commit')})" if isinstance(commits, int) else '')


def protocol_text(migration):
    protocol = migration.get('protocol') or {}
    if protocol.get('before') == protocol.get('after'):
        return f"v{clean(protocol.get('before'))}, unchanged"
    return mark(f"v{clean(protocol.get('before'))} -> v{clean(protocol.get('after'))}, a new protocol", 'warn')


def shell_path(path):
    text = clean(path)
    if text.startswith('~/'):
        return '~/' + shlex.quote(text[2:])
    return shlex.quote(text)


def tap_outcome(data):
    rows = (data.get('fetches') or {}).items()
    if not rows:
        return []
    failed = [f"tap {clean(name)} could not be fetched ({clean((row.get('error') or {}).get('code'))})" for name, row in rows if row.get('ok') is False]
    return [line[0].upper() + line[1:] + '.' for line in failed] or ['Taps were fetched.']


def migration_review(proposal, output):
    """The question a human answers before MASK moves to a program whose contracts changed."""
    migration = proposal.get('migration') or {}
    schemas = migration.get('schemas') or []
    root = (proposal.get('scope') or ['-'])[0]
    lines = [f"MASK {commit_span(migration)}", '',
             '  This update changes the files MASK uses to describe your setup.', '',
             f"  Protocol   {protocol_text(migration)}",
             f"  Schemas    {plural(len(schemas), 'changed file') if schemas else 'unchanged'}"]
    lines.extend(schema_rows(migration))
    lines.append('')
    lines.append('  ' + (mark('Some existing files may no longer validate with this version.', 'warn') if migration.get('breaking')
                         else 'Your existing projects and taps stay valid with this version.'))
    lines.append(f"  What's new: git -C {shell_path(root)} log --oneline {short(migration.get('before'))}..{short(migration.get('candidate'))}")
    taps = tap_outcome(output.get('data') or {})
    if taps:
        lines.extend([''] + ['  ' + line for line in taps])
    return '\n'.join(lines) + '\n\n'


def migration_error(output):
    """update refused or declined a program contract migration: what changes, what happened, and the two ways forward."""
    error, data = output['error'], output.get('data') or {}
    migration = (data.get('program') or {}).get('program_migration') or (data.get('confirmation') or {}).get('migration') or {}
    schemas = migration.get('schemas') or []
    if error['code'] == 'confirmation.declined':
        lines = ['error: You declined, so MASK was not updated.', f"  code: {clean(error['code'])}"]
        lines.extend(fetch_lines(data))
        lines.append("  next: Run 'mask update' again when you want this version.")
        return '\n'.join(lines + warnings(output)) + '\n'
    what = plural(len(schemas), 'schema') if schemas else 'its protocol'
    lines = [f"error: MASK update needs your approval: it changes {what}.", f"  code: {clean(error['code'])}",
             f"  from: {commit_span(migration)}"]
    protocol = migration.get('protocol') or {}
    if protocol.get('before') != protocol.get('after'):
        lines.append(f"  protocol: {protocol_text(migration)}")
    if schemas:
        lines.append('  schemas:')
        lines.extend(schema_rows(migration))
    if migration.get('breaking'):
        lines.append('  ' + mark('Some existing files may no longer validate with this version.', 'warn'))
    taps = [line[0].lower() + line[1:].rstrip('.') for line in tap_outcome(data)]
    lines.append('  state: MASK was not moved' + (f"; {'; '.join(taps)}" if taps else ''))
    lines.append("  next: Run 'mask update' in a terminal to review and confirm it, or approve")
    lines.append("        exactly this change with 'mask update --approve-plan HASH'.")
    if migration.get('plan_hash'):
        lines.append(f"  hash: {clean(migration['plan_hash'])}")
    return '\n'.join(lines + warnings(output)) + '\n'


def render_refresh(data, output):
    """update: what became available. The program first, then each tap, then the one next step if there is one."""
    program = data.get('program') or {}
    before, after = clean((program.get('program_before') or '-')[:7]), clean((program.get('program_after') or '-')[:7])
    lines = [{'updated': f'MASK updated: {before} -> {after}. The new version runs from the next command.',
              'behind': 'A newer MASK is available (dry run: not fetched or applied).',
              'current': f"MASK is up to date ({before})." + (' Dry run: the remote was not contacted.' if output['dry_run'] else ''),
              'held': f"MASK was not updated: {clean(program.get('reason'))}.",
              'failed': f"MASK could not be updated: {clean(program.get('reason'))} ({clean(program.get('code'))})."}.get(program.get('status'), headline(output, 'update'))]
    migration = program.get('program_migration')
    if migration and program.get('status') in ('updated', 'behind'):
        protocol = migration.get('protocol') or {}
        if protocol.get('before') != protocol.get('after'):
            lines.append(f"  Protocol   {protocol_text(migration)}")
        if migration.get('schemas'):
            lines.append(f"  Schemas    {plural(len(migration['schemas']), 'changed file')}")
            lines.extend(schema_rows(migration))
        if program.get('status') == 'behind' and migration.get('requires_consent'):
            lines.append("  'mask update' will show this change and ask before applying it.")
    taps = fetch_lines(data)
    lines.extend(taps or ["  No taps are approved yet; add one with 'mask tap NAME URL'."])
    if any(row.get('remote_refs_changed') for row in (data.get('fetches') or {}).values()):
        lines.append("  Run 'mask upgrade' for this checkout, or 'mask upgrade --all' for every registered checkout and personal skills.")
    return lines


def render_fetch(data, output):
    """source fetch: one line per tap; a named tap also says which commit it is now at."""
    if data.get('source') and 'fetch_effects' in data:
        effects, name = data['fetch_effects'], clean(data['source'])
        if not effects.get('attempted'):
            return [f"Did not fetch {name} (dry run). It is at {short(data.get('cached_revision'))}." if data.get('cached_revision') else f'Did not fetch {name} (dry run). It has never been fetched.']
        return [f"Fetched {name}: {'new commits' if effects.get('remote_refs_changed') else 'nothing new'} (now at {short(effects.get('after'))})."]
    if 'fetches' not in data:
        got = sum(1 for item in data.get('acquisitions') or [] if item.get('acquired'))
        made = sum(1 for item in data.get('artifacts') or [] if item.get('created'))
        lines = [f"Prepared the locked skills: {plural(got, 'commit')} fetched, {plural(made, 'store copy')} created." if got or made else 'The locked skills are already prepared.']
        return lines + action_lines(output) + plan_guard(data, output)
    taps = fetch_lines(data)
    return ['Would fetch your taps (dry run: nothing contacted).' if output['dry_run'] else 'Fetched your taps.'] + (taps or ["  No taps are approved yet; add one with 'mask tap NAME URL'."])


def fetch_lines(data):
    effects = data.get('fetch_effects')
    lines = [f"  fetch: {'fetched' if effects.get('fetched') else 'attempted, nothing new' if effects.get('attempted') else 'not attempted (cached candidate used)'}"] if effects else []
    for name, row in (data.get('fetches') or {}).items():
        if not row.get('attempted'):
            outcome_text = 'used the cached copy (not fetched)'
        elif not row.get('ok'):
            outcome_text = f"fetch failed ({clean((row.get('error') or {}).get('code'))})"
        else:
            outcome_text = 'fetched new commits' if row.get('remote_refs_changed') else 'fetched, nothing new'
        if row.get('chosen_by') and row.get('tried'):  # Only a fallback is news: the first choice working is the normal case.
            tried = ', '.join(f"{clean(item.get('transport'))} ({clean(item.get('code'))})" for item in row['tried'])
            outcome_text += f"; reached over {clean(row.get('transport'))} after {tried} did not answer"
        lines.append(f"  tap {clean(name)}: {outcome_text}")
    return lines


def render_launch(data, output):
    host = data.get('host') or {}
    lines = [f"launch: {clean(host.get('agent'))} exited {clean(host.get('exit_code'))}" if host else headline(output, 'launch')]
    lines.extend(fields(data, [('readiness', 'readiness'), ('executable', 'executable')]))
    return lines


def render_lock(data, output):
    lines = [headline(output, output['command'])]
    lines.extend(fields(data, [('scope', 'scope'), ('lock', 'lock_path'), ('portable', 'portable'), ('network', 'network'), ('deployment', 'deployment')]))
    lock = data.get('lock') or {}
    for name, entry in (lock.get('skills') or lock.get('bindings') or {}).items() if isinstance(lock.get('skills') or lock.get('bindings'), dict) else ():
        lines.append(f"  {clean(name)}: {clean(entry.get('commit') or entry.get('revision'))}")
    return lines + actions(output) + plan_guard(data, output)


def render_integration(data, output):
    command = output['command'].split('.')[-1]
    if command == 'inspect':
        head = f"Automatic readiness for {clean(data.get('root'))}: {'approved' if data.get('approved') else 'not approved'}"
    else:
        done = {'approve': 'Approved automatic readiness', 'revoke': 'Revoked automatic readiness', 'enable': 'Enabled the integration', 'disable': 'Disabled the integration'}.get(command, command)
        head = (f'Would have: {done.lower()}' if output['dry_run'] else done if output['changed'] else f'Nothing to do: {done.lower()} already holds') + (f" for {clean(data.get('root'))}" if data.get('root') else '') + '.'
    lines = [head]
    coverage = data.get('coverage') if isinstance(data.get('coverage'), dict) else {}
    lines.extend(pairs([(str(key).replace('_', ' '), value) for key, value in coverage.items() if key != 'limitation' and value not in (False, None, [], '')]))
    if coverage.get('limitation'):
        lines.append(f"  note: {clean(coverage['limitation'])}")
    for path in data.get('files', []) or []:
        lines.append(f"  file: {clean(path)}")
    if data.get('worktree_setup_command'):
        lines.append(f"  worktree setup: {clean(data['worktree_setup_command'])}")
    return lines + action_lines(output, [data.get('root')] if data.get('root') else ()) + note(data) + plan_guard(data, output)


def render_provenance(data, output):
    lines = [headline(output, output['command'].replace('.', ' '))]
    lines.extend(fields(data, [('operation', 'operation'), ('destination', 'destination'), ('origin', 'origin'), ('url', 'url'), ('ref', 'ref'), ('commit', 'commit'),
                               ('imported', 'imported_at'), ('adaptations', 'adaptations'), ('changed paths', 'changed_paths')]))
    return lines + actions(output) + plan_guard(data, output)


SCOPE_SPEC = [('root', 'root'), ('scope', 'scope'), ('declaration', 'manifest_path'), ('registered', 'registered'), ('mode', 'mode'), ('network', 'network')]
manifest_change = change(spec=SCOPE_SPEC)


def render_manifest(data, output):
    lines = manifest_change(data, output)
    manifest = data.get('manifest') or {}
    if manifest.get('skills') is not None and 'projects' not in data:
        lines.insert(1, f"  skills: {clean(manifest['skills'])}")
    if data.get('preparation'):
        lines.append(f"  prepared: {len(data['preparation'])} pinned scope(s)")
    return lines


TASK_SPEC = [('scope', 'scope'), ('root', 'root'), ('declaration', 'declaration_path'), ('mode', 'mode'), ('network', 'network')]


def render_task(data, output):
    """install/remove: the outcome in one sentence, the skills it touched, then only what needs a human's attention."""
    install = output['command'] == 'install'
    moved = data.get('added' if install else 'removed') or []
    verb, link = ('install', 'into') if install else ('uninstall', 'from')
    if not moved:
        head = (f"Already installed in {place(data)}: " if install else f"Not installed in {place(data)}: ") + joined(data.get('already') or [])
        head += '. Nothing to do.' if not output['would_change'] and not output['changed'] else '.'
    elif output['dry_run']:
        head = f"Would {verb} {plural(len(moved), 'skill')} {link} {place(data)} (dry run: nothing applied)."
    elif output['changed']:
        head = f"{verb.capitalize().rstrip('e')}ed {plural(len(moved), 'skill')} {link} {place(data)}."
    else:
        head = f"Proposed: {verb} {plural(len(moved), 'skill')} {link} {place(data)}; nothing applied."
    lines = [head] + [f"  {'+' if install else '-'} {clean(item)}" for item in moved]
    if moved and data.get('already'):
        lines.append(f"  {'already installed' if install else 'not installed'}: {joined(data['already'])}")
    if install and moved and data.get('agents'):
        lines.append(f"  for: {joined(data['agents'])}")
    created = ([f"created {clean(data.get('declaration_path'))}"] if data.get('declaration_created') else []) + \
        ([] if data.get('registered', True) else ['registered this ' + ('home' if data.get('scope') == 'user' else 'project')])
    if created and (output['changed'] or output['dry_run']):
        lines.append('  ' + ('Also ' if output['changed'] else 'Would also have ') + joined(created) + '.')
    lines.extend(action_summary(output))
    if not install and 'skills' in data and moved:
        lines.append(f"  still installed: {joined(data['skills']) if data['skills'] else 'nothing'}")
    for blocker in data.get('blockers', []) or []:
        lines.append(f"  blocked: {clean(blocker.get('message'))} ({clean(blocker.get('code'))})")
    lines.extend(workflow_lines(data, quiet_ready=True))
    if output['changed']:
        lines.append('  Restart running agents to load the change.')
    return lines + plan_guard(data, output)


def render_list(data, output):
    """One row per selected skill with a column per agent; footer counts and honest limitations."""
    lines = [f"{'Personal' if data.get('scope') == 'user' else 'Project'} skills in {clean(data.get('root'))}"]
    if not data.get('declared'):
        lines.append("  None yet. Add one with 'mask install ID'; browse with 'mask search'.")
        return lines
    agents = data.get('agents', [])
    rows = [dict(skill=entry['skill'], version=entry.get('commit', '-')[:7] if entry.get('commit') else '-', held='yes' if entry.get('pinned') else '-', **{agent: entry['states'].get(agent, 'unknown') for agent in agents}) for entry in data.get('skills', [])]
    lines.append('')
    if rows:
        lines.extend(table(rows, [('SKILL', 'skill'), ('VERSION', 'version'), ('HELD', 'held')] + [(agent.upper(), agent) for agent in agents]))
    else:
        lines.append('  no skills selected')
    links = data.get('links') or {}
    linked, expected = links.get('linked', 0), links.get('expected', 0)
    lines += ['', f"  {plural(len(rows), 'skill')}, " + ('no links expected here.' if not expected else f'all {clean(expected)} links in place.' if linked == expected else f"{clean(linked)} of {clean(expected)} links in place; run 'mask repair' to fix.")]
    if not data.get('registered'):
        lines.append("  Not registered, so nothing is deployed; 'mask register' prepares the selection.")
    for limitation in data.get('limitations', []):
        lines.append(f'  note: {clean(limitation)}')
    return lines


def render_forget(data, output):
    return [headline(output, 'workspace forget')] + fields(data, [('root', 'root'), ('abandoned paths', 'abandoned_paths')]) + actions(output) + plan_guard(data, output)


def render_lifecycle(data, output):
    if data.get('recovery'):
        return render_recover(data, output)
    return [headline(output, output['command'])] + actions(output) + workflow_lines(data, quiet_ready=True) + plan_guard(data, output)


def render_bundles(data, output):
    if 'bundles' in data:
        lines = ['Available bundles']
        for row in data['bundles']:
            lines.append(f"  {clean(row['coordinate'])}: {clean(row['description'])} ({len(row['bindings'])} skills)")
        for row in data.get('unavailable', []):
            lines.append(f"  {clean(row['source'])}: fetch this approved tap to inspect its bundles")
        return lines
    row = data.get('bundle', {})
    lines = [f"Bundle {clean(row.get('coordinate'))}"]
    if row.get('commit'):
        lines.extend([f"  revision: {clean(row['commit'])}", f"  definition: {clean(row['definition_digest'])}"])
    if 'after' in data:
        action = output['command'].split('.')[-1]
        completed = dict(install='Installed', uninstall='Uninstalled', upgrade='Upgraded')[action]
        verb = 'Would ' + action if output['dry_run'] and output['would_change'] else completed if output['changed'] else 'Unchanged'
        lines[0] = f"{verb} bundle {clean(row.get('coordinate'))} in {place(data)}"
        lines.extend('  + ' + clean(key) for key in data.get('added', []))
        lines.extend('  - ' + clean(key) for key in data.get('removed', []))
        lines.extend('  preserved ' + clean(item['skill']) + ': ' + clean(item['reason']) for item in data.get('preserved', []))
        lines.extend('  version ' + clean(item['coordinate']) + ': ' + clean(item.get('before_commit')) + ' -> ' + clean(item.get('after_commit')) for item in data.get('versions', []))
        lines.extend(action_summary(output))
        lines.extend(workflow_lines(data, quiet_ready=True))
        lines.extend(plan_guard(data, output))
    else:
        lines.extend('  ' + clean(binding['source'] + '/' + binding['id']) for binding in row.get('bindings', []))
    return lines


def render_all_list(data, output):
    return render_inventory(data, output) if 'consumers' in data or 'deployments' in data else render_list(data, output)


RENDERERS = {
    'bundle.list': render_bundles, 'bundle.show': render_bundles, 'bundle.install': render_bundles, 'bundle.uninstall': render_bundles, 'bundle.upgrade': render_bundles,
    'tap': render_sources, 'untap': render_sources, 'search': render_catalog, 'info': render_skill,
    'uninstall': render_task, 'register': render_lifecycle, 'unregister': render_forget,
    'repair': render_lifecycle, 'status': render_doctor, 'pin': render_lifecycle, 'unpin': render_lifecycle,
    'cleanup': render_lifecycle, 'integration.run': render_ensure,
    'tap.fetch': render_fetch, 'tap.show': render_sources, 'tap.inspect': render_sources,
    'tap.repair-cache': render_sources, 'tap.publish': render_sources, 'tap.migrate': render_doctor,
    'skill.dev-link': render_manifest,

    'help': render_help, 'version': render_version, 'capabilities': render_capabilities,
    'init': render_config, 'config.show': render_config, 'config.set': render_config,
    'skill.list': render_catalog, 'skill.validate': lambda data, output: render_catalog(data, output) if 'skills' in data else render_skill(data, output),
    'skill.show': render_skill, 'skill.where-used': render_where_used, 'inventory': render_inventory,
    'install': render_task, 'remove': render_task, 'list': render_all_list,
    'skill.import': render_provenance, 'skill.provenance': render_provenance, 'skill.record-adaptation': render_provenance,
    'project.init': summary('project init', SCOPE_SPEC), 'project.show': render_show, 'project.set-agents': render_manifest, 'project.set-targets': render_manifest,
    'project.register': render_manifest, 'project.unregister': render_forget, 'project.list': render_projects,
    'user.init': summary('user init', SCOPE_SPEC), 'user.show': render_show, 'user.set-agents': render_manifest, 'user.set-targets': render_manifest, 'user.register': render_manifest, 'user.unregister': render_forget,
    'selection-policy.set': change('selection policy', [('policy', 'selection_policy'), ('affected scopes', 'affected_scopes')]),
    'selection-policy.clear': change('selection policy', [('policy', 'selection_policy'), ('affected scopes', 'affected_scopes')]),
    'compatibility.override': change('compatibility override', SCOPE_SPEC), 'compatibility.clear': change('compatibility clear', SCOPE_SPEC),
    'plan': change('plan'), 'apply': change('apply'), 'ensure': render_ensure, 'doctor': render_doctor, 'recover': render_recover,
    'integration.approve': render_integration, 'integration.revoke': render_integration, 'integration.inspect': render_integration,
    'integration.enable': render_integration, 'integration.disable': render_integration, 'launch': render_launch,
    'workspace.forget': render_forget, 'link.adopt': summary('link adopt', [('root', 'root'), ('scope', 'scope'), ('path', 'path'), ('link', 'link_text')]),
    'source.fetch': render_fetch, 'source.list': render_sources, 'source.show': render_sources, 'source.inspect': render_sources, 'source.repair-cache': render_sources,
    'source.publish': render_sources, 'source.dev-link': render_manifest, 'tap.add': render_sources, 'tap.remove': render_sources, 'tap.transport': render_sources,
    'lock': render_lock, 'update': render_refresh, 'upgrade': render_upgrade,
    'self.status': render_self_status, 'self.uninstall': render_uninstall, 'self.install': summary('self install', [('launcher', 'launcher'), ('interpreter', 'interpreter'), ('on PATH', 'on_path')]),
}


def warnings(output):
    """One line per distinct message; repeats of a message list their paths beneath it instead of repeating the sentence."""
    groups = {}
    for warning in output.get('warnings', []):
        detail = warning.get('details') or {key: value for key, value in warning.items() if key not in ('code', 'message')}
        detail = {key: value for key, value in detail.items() if not isinstance(value, (dict, list))} if isinstance(detail, dict) else detail
        groups.setdefault(clean(warning.get('message')), []).append(detail)
    lines = []
    ignorable = [item.get('details') or item for item in output.get('warnings', []) if item.get('code') == 'project.link_ignore']
    if ignorable:
        # Managed links live two levels down (.claude/skills/ID), so the folder to ignore is relative to the project that holds it.
        folders = {}
        for item in ignorable:
            parts = str(item.get('path') or '').replace('\\', '/').split('/')
            if len(parts) > 3:
                folders.setdefault('/'.join(parts[:-3]), set()).add('/'.join(parts[-3:-1]) + '/')
        groups.pop('Managed link is tracked or not ignored by Git.', None)
        for root, names in sorted(folders.items()):
            lines.append(f"warning: {clean(root)} would commit MASK's links. Add to its .gitignore:  {'  '.join(sorted(names))}")
    for message, details in groups.items():
        if len(details) == 1:
            lines.append(f'warning: {message}' + (f' [{clean(details[0])}]' if details[0] else ''))
            continue
        lines.append(f'warning: {message} ({len(details)} times)')
        lines.extend(f"  {clean(detail.get('path') or detail.get('root') or detail) if isinstance(detail, dict) else clean(detail)}" for detail in details if detail)
    return lines


def render(output):
    """Text for stdout on a handled success; always ends with one newline."""
    renderer = RENDERERS.get(output['command'])
    if renderer is None:
        raise KeyError(f"no human renderer registered for {output['command']}")
    data = output['data']
    lines = renderer(data, output)
    if output['dry_run'] and output['would_change'] and (data.get('review') or {}).get('kind') == 'task':
        # Keep the command's outcome sentence, then the same review shown at the prompt.
        lines = lines[:1] + [''] + task_review(data['review'], output).splitlines()[2:] + plan_guard(data, output)
    lines += warnings(output)
    return '\n'.join(scrub(line) for line in lines) + '\n'


PRESERVED = {'not_started': 'no deployment changes were applied', 'not_needed': 'no deployment changes were needed', 'rolled_back': 'the started change was rolled back',
             'committed': 'deployment changes were saved (this is not a Git commit)', 'partial': 'effects are partial; run mask recover --inspect'}


def render_confirmation(proposal, output):
    """The proposal a human answers or automation reviews: scope, planned actions, and the authority it does not grant."""
    if proposal.get('kind') == 'task':
        return task_review(proposal, output)
    if proposal.get('kind') == 'program.migration':
        return migration_review(proposal, output)
    lines = [f"{output['command'].replace('.', ' ')}: confirmation needed ({clean(proposal.get('reason'))})"]
    if proposal.get('kind') == 'package.setup':
        return '\n'.join(lines + setup_proposal_lines(proposal)) + '\n'
    for root in proposal.get('scope', []):
        lines.append(f"  scope: {clean(root)}")
    lines.extend(actions(dict(actions=proposal.get('actions', []))))
    lines.append('  grants: only the exact actions shown, including any listed setup, replacements or deletions; no persistent approval' if proposal.get('kind') == 'task' else '  grants: this invocation only; no package scripts, new sources, overwrites or persistent approval')
    return '\n'.join(lines) + '\n'


def task_review(proposal, output):
    """Group ordinary bookkeeping; keep significant code and replacement choices explicit."""
    roots = proposal.get('scope', [])
    rows = {root: dict(root=root, links=0, controls=0, setup=[]) for root in roots}
    shared, exact = {}, []
    for action in proposal.get('actions', []):
        kind = action.get('kind')
        if kind == 'setup.run':
            key = (action.get('coordinate'), action.get('path'), str(action.get('interpreter')),
                   action.get('fingerprint'), tuple(action.get('native_roles') or []))
            shared.setdefault(key, dict(action=action, roots=[]))['roots'].append(action.get('root'))
            if action.get('root') in rows:
                rows[action['root']]['setup'].append(action.get('skill'))
            continue
        if kind == 'state.record':
            continue
        path = str(action.get('path') or action.get('root') or '')
        root = next((root for root in sorted(roots, key=len, reverse=True) if path == root or path.startswith(root + os.sep)), None)
        if kind in ('link.create', 'link.replace', 'link.remove') and root:
            rows[root]['links'] += 1
        elif kind in QUIET_ACTIONS:
            if root:
                rows[root]['controls'] += 1
        else:
            exact.append(action)
    lines = [f"{output['command'].replace('.', ' ').capitalize()}: review {plural(len(roots), 'location')}", '']
    bundle = output['data'].get('bundle_changes')
    if bundle:
        lines.append(f"  Bundle {clean(bundle['coordinate'])} at {clean(bundle['commit'])}")
        lines.append(f"  Definition: {clean(bundle['definition_digest'])}")
        lines.extend('    + ' + clean(key) for key in bundle['added'])
        lines.extend('    - ' + clean(key) for key in bundle['removed'])
        for item in bundle['changed']:
            lines.append(f"    change {clean(item['skill'])}: {clean(item['before'])} -> {clean(item['after'])}")
        lines.extend('    preserve ' + clean(item['skill']) + ': ' + clean(item['reason']) for item in bundle['preserved'])
        lines.extend('    version ' + clean(item['coordinate']) + ': ' + clean(item.get('before_commit')) + ' -> ' + clean(item.get('after_commit')) for item in bundle.get('versions', []))
        lines.append('')
    for update in output['data'].get('bundle_updates', []):
        lines.append('  Bundles in ' + clean(update['root']))
        lines.extend('    ' + clean(item['coordinate']) + ' at ' + clean(item['commit']) + ' (' + clean(item['definition_digest']) + ')' for item in update['definitions'])
        lines.extend('    + ' + clean(key) for key in update['added'])
        lines.extend('    - ' + clean(key) for key in update['removed'])
        lines.extend('    preserve ' + clean(item['skill']) + ': ' + clean(item['reason']) for item in update['preserved'])
        lines.extend('    version ' + clean(item['coordinate']) + ': ' + clean(item.get('before_commit')) + ' -> ' + clean(item.get('after_commit')) for item in update['versions'])
        lines.append('')
    for root, row in rows.items():
        parts = []
        if row['links']:
            parts.append(plural(row['links'], 'skill link'))
        if row['controls']:
            parts.append('save locked versions')
        if row['setup']:
            parts.append('setup ' + joined(row['setup']))
        lines.append(f"  {clean(root)}  {'; '.join(parts) or 'check readiness'}")
    lines.extend(commit_lines(output['data']))
    # One code disclosure can cover several consumers of the same frozen payload.
    for item in shared.values():
        action = item['action']
        script = str(action.get('path', ''))
        coordinate = action.get('coordinate') or action.get('skill')
        marker = '/payload/' + str(action.get('skill')) + '/'
        portable = script.replace('\\', '/')
        script = portable.split(marker, 1)[-1] if marker in portable else script
        lines += ['', f"  Run setup: {clean(coordinate)} ({clean(action.get('fingerprint'))})", f"    {clean(script)} (Python: {clean(action.get('interpreter'))})"]
        lines += textwrap.wrap('In: ' + joined(item['roots']), width=96, initial_indent='    ', subsequent_indent='      ', break_long_words=False, break_on_hyphens=False)
        lines += textwrap.wrap(f"Generate {plural(len(action.get('native_roles') or []), 'role')}: " + joined(action.get('native_roles') or []), width=96,
                               initial_indent='    ', subsequent_indent='      ', break_long_words=False, break_on_hyphens=False)
    if exact:
        lines += ['', '  File changes:']
        for action in exact:
            verb = 'back up and replace' if action.get('kind') == 'file.backup_replace' else ACTION_VERBS.get(action.get('kind'), action.get('kind'))
            lines.append(f"    {clean(verb)} {clean(action.get('path') or action.get('root'))}")
    if shared:
        lines.append('  Setup runs package code with your user permissions.')
    lines += ['', '  Approval applies only to this task.']
    return '\n'.join(lines) + '\n'


def render_invocation(error, command):
    """Usage mistakes need commands and help, not transaction diagnostics."""
    details = error.get('details') or {}
    command_path = clean(details.get('command_path') or ('mask ' + command.replace('.', ' ')).rstrip())
    lines = []
    if details.get('subcommands'):
        lines = ['Commands:'] + [f'  {command_path} {clean(name)}' for name in details['subcommands']]
    elif 'unknown_command' in details:
        lines = [
            'Example usage:',
            '  mask search TEXT',
            '  mask info SKILL',
            '  mask install SKILL',
            '  mask uninstall SKILL',
            '  mask list',
            '  mask update',
            '  mask upgrade',
            '  mask upgrade --all',
            '',
            'Troubleshooting:',
            '  mask status',
            '  mask repair',
        ]
    if lines:
        lines += ['', 'Further help:', f'  {command_path} --help']
        if command_path == 'mask':
            lines.append('  mask COMMAND --help')
        lines.append('')
    lines.append(f"Error: {clean(error['message'])}")
    if len(lines) == 1:
        lines.append(f'Run {command_path} --help for usage.')
    return '\n'.join(lines) + '\n'


def render_error(output):
    """Text for stderr on a handled failure: what failed, what is preserved, what to do."""
    error = output['error']
    data = output.get('data', {})
    if error['code'] == 'invocation.invalid' and not (data or output.get('changed') or output.get('actions') or output.get('warnings')):
        return render_invocation(error, output['command'])
    if output.get('command') == 'update' and error['code'] in ('confirmation.required', 'confirmation.declined') and (data.get('program') or {}).get('status') == 'review':
        return migration_error(output)
    message = error['message']
    if error['code'] == 'workflow.incomplete' and data.get('workflow_readiness'):
        count = sum(not entry.get('complete') for entry in data['workflow_readiness'])
        message = f'Skill setup is incomplete in {count} scope(s). Existing files were preserved.'
    lines = [f"error: {clean(message)}", f"  code: {clean(error['code'])}"]
    if data.get('repair'):
        lines.extend(repair_lines(data, output)[1:])
    if (data.get('pending') or {}).get('setup'):
        lines.extend('  ' + line for line in render_recover(data, output))
    for key, value in (error.get('details') or {}).items():
        if key == 'workflow' and data.get('workflow_readiness'):
            continue
        if key in ('cause', 'rollback') and isinstance(value, dict):
            lines.append(f"  {'cause' if key == 'cause' else 'rollback stopped'}: {clean(value.get('message'))} ({clean(value.get('code'))})")
            lines.extend(f"    {clean(k).replace('_', ' ')}: {clean(v)}" for k, v in (value.get('details') or {}).items())
            continue
        lines.append(f"  {clean(key).replace('_', ' ')}: {clean(value)}")
    if output.get('data', {}).get('confirmation') and error['code'].startswith('confirmation.'):
        lines.extend(render_confirmation(output['data']['confirmation'], output).rstrip('\n').split('\n')[1:])
    lines.extend(workflow_lines(data, verb='can be restored from'))
    lines.extend(setup_lines(data))
    lines.extend(backup_lines(data))
    setup = data.get('setup') or {}
    if setup.get('confirmation') and any(row.get('state') == 'consent_required' for row in setup.get('actions', [])):
        lines.extend(setup_proposal_lines(setup['confirmation']))
    if setup.get('confirmation') and output['dry_run'] and data.get('plan_hash'):
        lines.append(f"  plan hash: {data['plan_hash']}")
    lines.extend(fetch_lines(output.get('data', {})))  # Cache effects before a decline are not activated content.
    lines.extend(commit_lines(data))
    if output.get('changed') and output['transaction'] != 'not_started':
        lines.extend(action_summary(output))  # A committed link/role transaction is reported even when readiness stayed incomplete.
    retained = data.get('retained_preparation')
    if retained:
        lines.append(f"  retained preparation: {len(retained['artifacts'])} store artifact(s) and {len(retained['acquisitions'])} cache acquisition(s) "
                     'kept under MASK_HOME; they are not deployment changes')
    lines.append(f"  state: {PRESERVED.get(output['transaction'], output['transaction'])}")
    for step in error.get('remediation', []):
        if error['code'] == 'workflow.incomplete' and data.get('workflow_readiness'):
            continue
        lines.append(f"  next: {clean(step.get('message'))}")
    if error['code'] == 'workflow.incomplete' and data.get('workflow_readiness'):
        lines.extend(workflow_next_steps(data, command=output['command']))
    return '\n'.join(lines + warnings(output)) + '\n'


def workflow_next_steps(data, *, command='ensure'):
    command = 'upgrade' if command == 'upgrade' else 'repair'
    lines = []
    for entry in data.get('workflow_readiness') or []:
        if entry.get('complete'):
            continue
        roles = [row for skill in entry.get('skills') or [] for row in skill.get('roles') or []]
        preserved = any(row.get('state') in ('modified', 'collision') or
                        (row.get('state') == 'setup_required' and row.get('observed_sha256') and row.get('ownership') != 'package-managed')
                        for row in roles)
        if preserved:
            lines.append(f"  next for {clean(entry.get('root'))}: Review the preserved files above.")
            lines.append('    Restore the matching native-roles.lock.json and role files from version control if available.')
            lines.append('    Otherwise compare and back up the files before deciding which to keep or replace.')
            lines.append('    See docs/guides/recovery.md for the reviewed replacement procedure.')
            selection = '--user' if entry.get('scope') == 'user' else '--project ' + shlex.quote(str(entry.get('root')))
            lines.append(f'    Preview mask {command} {clean(selection)} --dry-run, then approve the shown backups and replacements.')
        else:
            selection = '--user' if entry.get('scope') == 'user' else '--project ' + shlex.quote(str(entry.get('root')))
            lines.append(f"  next: Resolve any missing inputs above, then run mask {command} {clean(selection)}")
            lines.append('    Answer the setup question in a terminal if prompted.')
    return lines


def backup_lines(data):
    groups = {}
    for row in data.get('backups') or []:
        groups.setdefault((row.get('directory') or row['path'], row.get('state', 'unknown')), 0)
        groups[(row.get('directory') or row['path'], row.get('state', 'unknown'))] += 1
    if len(groups) > 1 and len({(os.path.dirname(path), state) for path, state in groups}) == 1:
        directory, state = next(iter(groups))
        return [f'  Backups {clean(state)}: {plural(sum(groups.values()), "file")} in {plural(len(groups), "set")} under {clean(os.path.dirname(directory))}.']
    return [f'  backups {clean(state)}: {count} file(s) in {clean(directory)}' for (directory, state), count in groups.items()]


def repair_lines(data, output):
    rows = data.get('repair_results') or [dict(root=row.get('root'), ok=row.get('workflow') in ('complete', 'not_declared'),
                                            changed=output['changed']) for row in data.get('scope_readiness') or []]
    ready = sum(row.get('ok', False) for row in rows)
    title = 'repair preview; nothing applied' if output['dry_run'] else f'{ready} of {len(rows)} scopes ready'
    lines = [f'ensure: {title}']
    for row in rows:
        status = 'ready' if row.get('ok') else 'needs attention'
        if output['dry_run']:
            status = 'changes planned' if not row.get('ok') or output['would_change'] else 'no changes needed'
        lines.append(f"  {status}: {clean(row.get('root'))}")
        error = row.get('error') or {}
        if error and error.get('code') != 'workflow.incomplete':
            lines.append(f"    {clean(error.get('message'))}")
            for key in ('path', 'root'):
                if (error.get('details') or {}).get(key):
                    lines.append(f"    {clean(error['details'][key])}")
            if error.get('code') in ('recovery.required', 'state.pending'):
                lines.append('    Run mask repair to review the interrupted operation before retrying.')
    if not output['dry_run']:
        roles = sum(row.get('kind') == 'native_role.write' and row.get('status') == 'applied' for row in output.get('actions') or [])
        links = sum(row.get('kind') == 'link.create' and row.get('status') == 'applied' for row in output.get('actions') or [])
        if roles or links:
            lines.append(f'  Applied: {roles} role file(s), {links} skill link(s).')
        lines.append('  Host loading has not been verified; restart active agents to load changed roles.')
    return lines


EVERYDAY = [
    ('skill list', 'Browse the skills in your fetched taps'),
    ('install ID...', 'Add skills to this project and link their pinned payloads'),
    ('remove ID...', 'Remove selections and their managed links'),
    ('list', 'Show this project\'s selected skills and link status'),
    ('ensure', 'Reconcile this project; offer required setup'),
    ('update', 'Update MASK itself and fetch your taps; changes no project'),
    ('upgrade', 'Move ALL registered projects and personal skills to the newest versions'),
    ('doctor --check', 'Check health without changing files'),
]


def compact_help(version, groups):
    lines = [f'mask {version} - Manage Agent Skills', 'usage: mask COMMAND [OPTIONS]',
             'Deploy pinned skills from approved Git taps into Claude Code and Codex.', '',
             'Start here:', '  mask tap add agentskills https://github.com/MikeMarcin/AgentSkills.git   # approve a tap; sets up this machine',
             '  mask tap fetch                       # fetch approved taps so you can browse them',
             '  mask search                         # find a skill ID',
             '  mask install implement-rfc              # pin it and link it into the current project',
             '  mask repair                             # finish any required setup',
             '  mask repair --all --repair              # fix all registered scopes; back up replaced roles', '', 'Everyday commands:']
    pad = max(len(usage) for usage, _ in EVERYDAY)
    lines.extend(f'  {usage.ljust(pad)}  {text}' for usage, text in EVERYDAY)
    lines += ['', 'Choose where:',
              '  install / remove / list / ensure use the current project by default.',
              '  Add --project DIR for another project or --user for personal skills.',
              '  Bare upgrade fetches each referenced tap once and upgrades every registered consumer.',
              '  upgrade --project DIR, --user or --skill SOURCE/ID narrows what it upgrades.', '',
              'Preview and diagnose:',
              '  mask repair --dry-run            Preview this project without running setup',
              '  mask status --all --check        Check all registered scopes',
              '  mask inventory --all             List skills across registered scopes',
              '  mask upgrade --help              Understand upgrade scope before fetching',
              '',
              'Options:', '  --dry-run   Preview changes without applying or fetching (mutating commands)',
              '  --yes       Accept ordinary confirmation; never authorizes package setup',
              '  --json      Emit structured output for scripts; never prompt',
              '  --home DIR  Use a different MASK state directory',
              '  --debug     Include diagnostic details', '  --version   Print the version',
              '  --help      Show command help and examples', '',
              f"Advanced command groups: {', '.join(groups)}",
              "Run 'mask COMMAND --help' or 'mask GROUP --help' to learn more."]
    return '\n'.join(lines) + '\n'


# Parser-owned help uses these descriptions without changing the command grammar.
COMMAND_HELP = {
    'init': ('Optionally create an empty machine configuration (a tap catalog) and state. mask tap add creates both when they are missing, so one tap add bootstraps a machine.', 'mask init\nmask init --target codex --git-timeout 60'),
    'install': ('Add skills and link them. Uses the current project unless --project or --user is supplied. Other selections are kept. A bare ID is looked up in every approved tap; name SOURCE/ID when more than one tap offers it. A tap that is not fetched yet is fetched on demand, never with --offline or --dry-run. The declaration, its lock of exact commits, the registration and links to the payloads in the MASK store are written in one recoverable transaction.', 'mask install implement-rfc\nmask install wizard --user\nmask install agentskills/wizard --project /path/to/project --dry-run'),
    'remove': ('Remove selected skills and their managed links. Other selections and modified files are kept.', 'mask remove wizard\nmask remove wizard --user'),
    'list': ('Show selected skills and their status in the current project, another project, or your personal scope.', 'mask list\nmask list --user'),
    'ensure': ('Reconcile a project or personal scope and check its required inputs and native agent roles. Use ensure for a fresh clone/worktree or to restore pinned versions without upgrading. Manual ensure and upgrade can offer package setup. Normal ensure preserves unmanaged or modified files. --repair (--yolo) explicitly authorizes setup and backs up then replaces conflicting role files without prompts. --yes alone does not authorize setup.', 'mask repair --all --repair            # repair all registered scopes, with backups\nmask repair --all --repair --dry-run  # preview only\nmask repair\nmask repair --project /path/to/project --dry-run\nmask repair --user\n\nIf existing role files block setup, restore their matching lock from version\ncontrol or review and back up the files before deciding what to replace.\nRepeating normal ensure will not overwrite them. Use --repair for automatic\nbackup and replacement. See docs/guides/recovery.md.\n\nAutomatic startup and --check require prior integration approval.\nFor automation: preview with --dry-run --json, then pass that plan hash with\n--approve-plan HASH --allow-setup SOURCE/ID:ACTION on ensure.'),
    'update': ('Refresh what is available, as brew update and apt update do: fast-forward the MASK program from its Git remote, then fetch every approved tap into its MASK-owned cache. No declaration, lock, link or consumer changes; run mask upgrade to move projects to what was fetched. A program checkout that is ahead of its remote, diverged, detached or has uncommitted changes is left alone and reported, and the taps are still fetched. A newer MASK that changes its protocol or schemas is shown first and needs a yes in a terminal, or --approve-plan HASH from a script; comment-only schema edits apply without asking. --dry-run contacts nothing. An updated program takes effect on the next command.', 'mask update                      # update MASK and fetch taps\nmask update --approve-plan HASH  # apply one reviewed contract change\nmask upgrade --dry-run           # see what the fetched taps would change\nmask upgrade                     # move every registered project and your personal skills'),
    'upgrade': ('Move pinned skills to the newest versions their selectors allow. With no scope options, upgrade ALL registered consumers (every registered project and your personal scope), regardless of your current directory; --project, --user, --all and --skill SOURCE/ID narrow it. Each referenced tap is fetched once, except under --dry-run, --offline or --approve-plan, which use cached content only. Every selected consumer is re-resolved against its selectors, and all lock and link changes apply in one recoverable transaction. A tap that fails to fetch blocks only the consumers that use it: the others still apply and the command exits 4 with upgrade.incomplete. A moved tag or a branch that is not a fast-forward refuses unless --allow-ref-rebind. After applying versions and links, reconcile workflow prerequisites even if versions were already current. Necessary generated roles use the same consented staged setup as ensure. A terminal asks before running package code; automation uses the preview hash and --allow-setup SOURCE/ID:ACTION. --repair explicitly authorizes setup and backs up then replaces conflicting native role files. --yes alone never authorizes setup. Missing inputs or declined/failed setup remain nonzero.', 'mask upgrade --dry-run              # preview from cached taps; never fetches\nmask upgrade                        # fetch taps; upgrade every registered consumer\nmask upgrade --project .            # upgrade only this project\nmask upgrade --user                 # upgrade only your personal skills\nmask upgrade --skill agentskills/implement-rfc  # upgrade one selection wherever declared\n\nTo review fresh content before applying it, run mask update, then\nmask upgrade --dry-run, then mask upgrade --approve-plan HASH.\nFor unattended setup, include --allow-setup SOURCE/ID:ACTION with the preview hash.\nUse mask upgrade --repair for explicit setup and role replacement with backups.\nUse ensure for a fresh clone/worktree or to restore pinned versions without upgrading.\nUse mask update to update the MASK program.'),
    'doctor': ('Inspect health, missing files and drift without changing files. --check exits 7 when problems are found. When the tap catalog still records an older spelling of a tap identity, doctor says so, and doctor --migrate rewrites just those catalog entries in one atomic write; no project file, state record or cache changes.', 'mask status --project . --check\nmask status --all --check\nmask status --migrate --dry-run\nmask status --migrate'),
    'inventory': ('Inspect skill selections, source versions and per-agent links across registered scopes.', 'mask inventory --project .\nmask inventory --all'),
    'plan': ('Preview deployment changes for registered scopes without applying them.', 'mask plan --project .\nmask plan --all'),
    'apply': ('Reconcile managed links for the selected registered scopes. Does not run package setup.', 'mask apply --project . --dry-run\nmask apply --project .'),
    'recover': ('Inspect or finish an interrupted MASK deployment transaction.', 'mask recover --inspect\nmask recover --complete\nmask recover --rollback'),
    'skill.list': ('List the skills in the fetched caches of your approved taps. A tap that is not fetched yet is named instead; run mask tap fetch first.', 'mask search'),
    'skill.show': ('Describe a skill from a fetched tap, optionally including its instructions. Name SOURCE/ID when more than one tap offers it.', 'mask info implement-rfc\nmask info implement-rfc --content'),
    'self.install': ('Create a MASK launcher in an existing bin directory.', 'mask self install --bin-dir /path/to/bin'),
    'self.status': ('Show the MASK program, interpreter and installed launchers.', 'mask self status'),
    'self.uninstall': ('Remove the mask launchers this program wrote. A launcher edited since MASK wrote it is kept. MASK never deletes folders, so the command ends by listing what is left (the projects that still link skills, the machine state and the program clone) with the commands that remove them.', 'mask self uninstall --dry-run\nmask self uninstall'),
    'project.init': ('Create a project skill declaration without installing skills. For the everyday install task, use mask install ID.', 'mask project init --project .'),
    'project.show': ('Show a project\'s declared skill selections and targets.', 'mask project show --project .'),
    'project.register': ('Register this physical project so MASK can manage its links.', 'mask project register /path/to/project'),
    'project.unregister': ('Stop managing this project. Preserve the declaration and any changed files.', 'mask project unregister /path/to/project --dry-run'),
    'project.list': ('List the physical projects registered on this machine.', 'mask project list'),
    'skill.where-used': ('Find registered consumers that select a skill.', 'mask skill where-used implement-rfc'),
    'skill.validate': ('Validate passive skill package content from fetched taps without running package code.', 'mask skill validate implement-rfc\nmask skill validate --all'),
    'integration.approve': ('Grant persistent automatic-readiness authority to an explicitly selected project or boundary.', 'mask integration approve --project /path/to/project --dry-run'),
    'integration.inspect': ('Inspect project readiness authority and installed integrations.', 'mask integration inspect --project .'),
    'source.list': ('List approved taps.', 'mask source list'),
    'source.show': ('Show one approved tap: its identity, the transport this machine uses to reach it and why (pinned, the project origin, a transport that worked before, gh, the typed URL or a probe), its line-ending policy and cached revision.', 'mask source show NAME'),
    'source.repair-cache': ('Retain a recognized tap cache at a sibling path without trusting its old ownership or objects. Preview and apply with the plan hash; the next source fetch rebuilds it. No consumer or catalog changes, deletion, or network access.', 'mask source repair-cache agentskills --dry-run\nmask source repair-cache agentskills --approve-plan HASH\nmask tap fetch agentskills'),
    'source.fetch': ('Fetch approved taps into their MASK-owned caches without changing any consumer. With no NAME, fetch every approved tap; NAME fetches one tap. --locked prepares only the exact commits and store payloads that a project or personal lock names (from the cache only with --offline). Run upgrade to deploy fetched content.', 'mask tap fetch\nmask tap fetch agentskills\nmask tap fetch --locked --project .'),
    'lock': ('Resolve selected requirements to exact versions without deploying them.', 'mask lock --project . --dry-run'),
    'capabilities': ('Describe supported commands, schemas and feature boundaries for automation.', None),
    'config.show': ('Show the machine configuration and its approved taps.', None),
    'config.set': ('Change local default agent targets, the Git timeout, or the extra hosts on which this machine treats HTTPS and SSH URLs as one tap identity. github.com, gitlab.com, bitbucket.org and codeberg.org are always such hosts; add a self-hosted forge only when both URLs really reach the same repositories.', 'mask config set --forge-host git.example.com\nmask config set --clear-forge-hosts'),
    'compatibility.override': ('Record an explicit exception to advertised compatibility, with a reason.', None),
    'compatibility.clear': ('Remove a recorded compatibility exception.', None),
    'integration.enable': ('Install a selected Git or agent startup integration.', None),
    'integration.disable': ('Remove an owned startup integration, preserving unexpected edits.', None),
    'integration.revoke': ('Remove persistent readiness authority for the selected boundary.', None),
    'launch': ('Check readiness, then launch the selected agent with arguments after --.', None),
    'link.adopt': ('Record ownership of an existing link only when its source matches the explicit expectation.', None),
    'project.set-targets': ('Replace the project\'s agent targets, or restore inherited defaults.', None),
    'user.set-targets': ('Replace personal agent targets, or restore inherited defaults.', None),
    'project.set-agents': ('Choose which agents receive one pinned skill in this project.', None),
    'selection-policy.set': ('Set machine-level agent selection policy.', None),
    'selection-policy.clear': ('Clear machine-level agent selection policy.', None),
    'skill.import': ('Import skill content from a Git source using an explicit mode and destination.', None),
    'skill.provenance': ('Show the recorded origin and adaptations of a skill.', None),
    'skill.record-adaptation': ('Record an explanation for a local skill adaptation.', None),
    'source.dev-link': ('Switch a pinned skill to a local authoring checkout, or return it to pinned deployment.', None),
    'source.inspect': ('Inspect an approved tap, named by alias or repository URL, at a ref or path and list its packages without selecting them for deployment.', None),
    'source.publish': ('Inspect selected source changes; commit or push only when explicitly requested by the corresponding flags.', None),
    'tap.add': ('Approve a Git repository as a named tap. On github.com, gitlab.com, bitbucket.org and codeberg.org an HTTPS URL and an SSH URL name the same tap, and the URL you type only suggests how to reach it; --pin-transport makes this machine always use exactly that URL (see mask tap transport --help). Only the catalog is written and nothing is fetched; install, update, upgrade or source fetch '
                'later fetches the tap into a MASK-owned cache. On a machine without configuration this also creates the machine configuration '
                'and state. --checkout binds an authoring checkout whose origin matches the tap; source publish, source dev-link and skill import '
                'use it, install, update, list and ensure never read it, and it is never a link target. A tap keeps exact bytes: MASK never converts line endings '
                'of its packages unless --autocrlf opts this tap in to Git core.autocrlf=true conversion at registration.',
                'mask tap add agentskills https://github.com/MikeMarcin/AgentSkills.git\n'
                'mask tap add agentskills https://github.com/MikeMarcin/AgentSkills.git --checkout /path/to/AgentSkills'),
    'tap.transport': ('Choose how this machine reaches an approved tap, without changing which repository is trusted. A tap identity is transport-neutral on github.com, gitlab.com, bitbucket.org, codeberg.org and any host added with mask config set --forge-host: HTTPS and SSH URLs name the same tap, so one committed project file suits machines that authenticate either way. By default the transport is derived per fetch: the project checkout origin scheme on the same host, then the transport that last worked, then gh git_protocol, then the other scheme, moving on only when one cannot authenticate or connect, and never prompting. Give a URL to pin that transport so no other is tried; --derive returns to convention. A URL naming another repository refuses source.identity_mismatch. Only the machine catalog changes; nothing about transport is ever written to a project file.', 'mask tap transport agentskills git@github.com:MikeMarcin/AgentSkills.git   # always use SSH here\nmask tap transport agentskills --derive                                      # follow convention again\nmask source show agentskills                                                 # see the transport in use and why'),
    'tap.remove': ('Remove an approved tap from the catalog. It refuses while a consumer still uses the tap; the cache is retained.', None),
    'user.init': ('Create the personal skill declaration without deploying skills.', None),
    'user.show': ('Show your personal skill declaration.', None),
    'user.register': ('Register the personal home in which MASK will manage skill links.', None),
    'user.unregister': ('Stop managing personal links, preserving the declaration and changed files.', None),
    'user.set-agents': ('Choose which agents receive one pinned personal skill.', None),
    'workspace.forget': ('Forget an absent workspace only when its recorded identity matches.', None),
}
OPTION_HELP = {
    'bundle': 'Source-qualified bundle name: SOURCE/NAME',
    'source': 'Filter bundles to one approved source alias',
    'replace': 'Replace only this named local bundle contribution; review exclusive removals',
    'workflow-profile': 'Check a declared role subset: SKILL=PROFILE (status --check)',
    'approve-plan': 'Approve the exact reviewed task, including its disclosed setup and replacements',
    'no-update': 'Skip the preliminary program and catalog update; task-specific fetching remains allowed',
    'query': 'Text to find in skill names and descriptions',
    'json': 'Emit a structured result for scripts; never prompt',
    'debug': 'Include diagnostic details', 'help': 'Show this help', 'version': 'Show MASK version',
    'home': 'MASK state directory (not the project or personal home)',
    'project': 'Select a project directory',
    'user': 'Select your personal skills instead of a project', 'all': 'Select all registered scopes',
    'ids': 'Skill IDs to add or remove', 'id': 'Skill ID',
    'dry-run': 'Preview local/cached changes without applying, fetching or running setup',
    'yes': 'Accept ordinary confirmation; does not authorize package setup or overwrites',
    'expect-plan-hash': 'Require the exact plan hash from a reviewed preview (automation)',
    'check': 'Report readiness without making changes', 'offline': 'Use local/cached content; do not fetch',
    'allow-setup': 'Authorize the named SOURCE/ID:ACTION with --approve-plan; repeatable',
    'repair': 'Repair without prompts: authorize declared setup and back up then replace conflicting role files (--yolo is an alias)',
    'event': 'Invocation context: manual (default), startup, post-checkout, post-merge, post-rewrite or post-commit',
    'agent': 'Agent name (claude or codex)', 'skill': 'Skill ID; repeat for multiple skills',
    'limit': 'Maximum rows to return', 'offset': 'Number of rows to skip',
    'include-unmanaged': 'Also inspect entries MASK does not own',
    'content': 'Include SKILL.md content', 'inspect': 'Report the pending transaction without changing it',
    'complete': 'Complete the pending transaction', 'rollback': 'Roll back the pending transaction',
    'bin-dir': 'Existing directory in which to create the launcher',
    'allow-ref-rebind': 'Allow a moved tag or a branch that is not a fast-forward to replace a locked commit',
    'apply': 'Also deploy the resulting selection',
    'target': 'Agent target; repeat for multiple targets', 'targets': 'Agent targets to select',
    'agents': 'Agents to select for this skill', 'inherit': 'Use the configured default selection',
    'path': 'Filesystem path', 'url': 'Git repository URL', 'name': 'Tap name',
    'ref': 'Git branch, tag or commit', 'into': 'Destination skill ID',
    'mode': 'Import mode', 'note': 'Explanation to record with the adaptation',
    'scope': 'Filter by project or personal scope', 'git-timeout': 'Git command timeout in seconds',
    'keep-links': 'Leave links in place and abandon MASK ownership',
    'user-home': 'Personal home directory in which to deploy links',
    'repository': 'Git repository approval boundary', 'under': 'Directory approval boundary',
    'linked-worktrees': 'Include linked worktrees in this approval',
    'inactive-branches': 'Allow readiness on inactive branches',
    'allow-locked-fetch': 'Allow fetching a named locked source; repeatable',
    'git': 'Select Git hook integration',
    'forge-host': 'Also treat HTTPS and SSH URLs on this host as one tap identity; repeatable, replaces the list',
    'clear-forge-hosts': 'Remove every extra forge host from this machine', 'host_args': 'Arguments passed to the selected agent after --',
    'expect-identity': 'Require the recorded workspace identity before forgetting it',
    'expect-source': 'Require this exact source when adopting the link',
    'locked': "Prepare only the exact commits and store payloads the selected consumer's lock names",
    'paths': 'Source paths to include; repeatable', 'commit': 'Explicitly commit the selected source changes',
    'push': 'Explicitly push the source changes', 'message': 'Commit message',
    'authoring-root': 'Local checkout to use while editing this skill',
    'to-pinned': 'Return the skill from its authoring checkout to its pinned store payload',
    'migrate': 'Rewrite older tap identity spellings in the machine catalog, in one atomic write',
    'packages': 'Package directory inside the tap repository (default: skills)',
    'checkout': 'Authoring checkout for source publish and source dev-link; never a link target',
    'autocrlf': 'Opt this tap in to Git core.autocrlf=true line-ending conversion (default: exact bytes)',
    'pin-transport': 'Always reach this tap exactly as the URL says, instead of deriving HTTPS or SSH per fetch',
    'derive': 'Stop pinning: derive the transport by convention again',
    'refresh': 'Refresh existing version resolutions', 'reason': 'Explanation for this compatibility override',
    'platform': 'Override the advertised platform restriction', 'architecture': 'Override the advertised architecture restriction',
}
