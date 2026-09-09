"""Human presentation for MASK results (RFC-MASK-0018, contract section 5).

Every registered command renders the same structured result object that
``--json`` emits; nothing here decides, mutates or re-derives engine facts.
``RENDERERS`` is the coverage table: a command without an explicit entry is a
defect that ``tests.test_human_output`` rejects, not a case for dumping JSON.
Success text goes to stdout, errors to stderr, plain ASCII, no decoration.
"""
from __future__ import annotations

import re

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
    return CONTROL.sub('?', str(value)).replace('\n', ' ')


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
        return 'would change (dry run)' if output['would_change'] else 'no change needed (dry run)'
    if output['changed']:
        return 'changed' if output['transaction'] == 'committed' else f"changed ({output['transaction']})"
    if output['would_change']:
        return 'change proposed, nothing applied'
    return 'reported' if output['transaction'] == 'not_needed' and 'plan_hash' not in output['data'] else 'no change needed'


def headline(output, title=None):
    return f"{(title or output['command']).replace('.', ' ')}: {outcome(output)}"


def actions(output):
    lines = []
    for action in output.get('actions', []):
        what = clean(action.get('kind'))
        target = action.get('path') or action.get('root') or ''
        extra = ' -> ' + clean(action['source']) if action.get('source') else ''
        lines.append(f"  {action.get('status', 'planned')}: {what} {clean(target)}{extra}".rstrip())
    return lines


def plan_guard(data, output):
    lines = []
    if output['would_change'] and not output['changed'] and data.get('plan_hash') and not output['dry_run']:
        lines.append(f"  plan hash: {data['plan_hash']}")
    return lines


# --- layouts -----------------------------------------------------------------

def summary(title=None, spec=()):
    def render(data, output):
        lines = [headline(output, title)] + fields(data, spec)
        return lines + actions(output) + plan_guard(data, output)
    return render


def change(title=None, spec=()):
    """Reconciliation-shaped results: scope, blockers, outcomes, planned/executed actions."""
    def render(data, output):
        lines = [headline(output, title)] + fields(data, spec)
        for scope_key in ('projects', 'users'):
            for entry in data.get(scope_key, []) or []:
                lines.append(f"  {scope_key[:-1]}: {clean(entry.get('root'))}")
        for blocker in data.get('blockers', []) or []:
            lines.append(f"  blocked: {clean(blocker.get('message'))} ({clean(blocker.get('code'))})")
        if data.get('shadowing'):
            lines.append(f"  shadowing: {len(data['shadowing'])} scope overlap(s); see warnings")
        lines.extend(actions(output))
        if not output.get('actions') and not data.get('blockers') and ('projects' in data or 'users' in data):
            lines.append('  links already match the declaration')
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
                                          content=row.get('content_mode'), states={}, notes=[]))
        agent = row['agent']
        if agent not in agents:
            agents.append(agent)
        state = STATUS_WORDS.get(row['status'], row['status'])
        if row.get('error'):
            state += f" ({clean(row['error'].get('code'))})"
        entry['states'][agent] = state
        if not row.get('declared') and row.get('owned'):
            entry['notes'].append('owned but no longer declared')
    lines = [f"inventory: {len(rows)} skill row(s), {len(links)} link(s) shown of {total} total"]
    if not links and not consumers:
        lines.append('  no registered consumers selected')
    for consumer in consumers:
        state = 'available' if consumer.get('available') else 'unavailable'
        line = f"  {consumer['scope']} {clean(consumer['root'])}: {state}, {clean(consumer.get('declaration_basis'))}"
        if consumer.get('mode'):
            line += f", mode {consumer['mode']}"
        lines.append(line)
        if consumer.get('error'):
            lines.append(f"    problem: {clean(consumer['error'].get('message'))} ({clean(consumer['error'].get('code'))})")
        for problem in consumer.get('discovery_errors', []):
            lines.append(f"    discovery: {clean(problem.get('message'))}")
    if rows:
        columns = [('SKILL', 'skill'), ('SOURCE', 'source'), ('CONTENT', 'content')] + [(agent.upper(), agent) for agent in agents] + [('NOTES', 'notes')]
        table_rows = [dict(skill=entry['skill'], source=entry['source'], content=entry['content'], notes=entry['notes'] or None,
                           **{agent: entry['states'].get(agent, 'not observed') for agent in agents}) for entry in rows.values()]
        lines.extend(table(table_rows, columns))
    elif consumers:
        lines.append('  no skills declared or deployed for the selected consumer(s)')
    if data.get('next_offset') is not None:
        lines.append(f"  partial page: rows beyond this page were not observed; continue with --offset {data['next_offset']}")
    if not data.get('complete', True):
        lines.append('  incomplete: at least one consumer could not be fully observed')
    for limitation in data.get('limitations', []):
        lines.append(f'  limitation: {clean(limitation)}')
    return lines


def render_where_used(data, output):
    lines = [f"where-used: {len(data.get('rows', []))} of {data.get('total_rows', 0)} link(s)"]
    lines.extend(table(data.get('rows', []), [('SKILL', 'name'), ('SCOPE', 'scope'), ('AGENT', 'agent'), ('STATE', 'status'), ('PATH', 'path')]))
    if data.get('next_offset') is not None:
        lines.append(f"  partial page: continue with --offset {data['next_offset']}")
    return lines


def render_catalog(data, output):
    skills = data.get('skills', [])
    lines = [f"{output['command'].replace('.', ' ')}: {len(skills)} skill(s) in the source catalog"]
    if data.get('resolution_required'):
        lines.append(f"  unresolved sources: {clean(data.get('unresolved_sources'))}; run 'mask source fetch' first")
    if skills:
        rows = [dict(id=item.get('id') or item.get('name'), valid='ok' if item.get('valid', True) else 'invalid',
                     source=item.get('source') or item.get('scope') or '-', description=item.get('description')) for item in skills]
        lines.extend(table(rows, [('SKILL', 'id'), ('STATE', 'valid'), ('SOURCE', 'source'), ('DESCRIPTION', 'description')]))
        for item in skills:
            for issue in item.get('issues', []) or []:
                lines.append(f"  {clean(item.get('id'))}: {clean(issue.get('message'))}")
    elif not data.get('resolution_required'):
        lines.append('  the source has no skills yet')
    return lines


def render_skill(data, output):
    lines = [f"skill {clean(data.get('id'))}: {'valid' if data.get('valid', True) else 'invalid'}"]
    lines.extend(fields(data, [('description', 'description'), ('path', 'asset_path'), ('digest', 'digest'), ('scope', 'scope')]))
    for issue in data.get('issues', []) or []:
        lines.append(f"  issue: {clean(issue.get('message'))}")
    if data.get('content'):
        lines.append('  --- SKILL.md ---')
        lines.extend(CONTROL.sub('?', str(data['content'])).rstrip('\n').split('\n'))
    return lines


def render_projects(data, output):
    projects = data.get('projects', [])
    lines = [f"projects: {len(projects)} registered"]
    if not projects:
        lines.append("  none registered; use 'mask project register PATH'")
    for record in projects:
        state = 'available' if record.get('available') else 'unavailable'
        lines.append(f"  {clean(record.get('root'))}: {state}, mode {clean(record.get('mode', 'legacy'))}, {len(record.get('links', {}))} link(s)")
    return lines


def render_show(data, output):
    scope = data.get('scope', 'project')
    lines = [f"{scope} {clean(data.get('root'))}: {'registered' if data.get('registered') else 'not registered'}"]
    manifest = data.get('manifest') or {}
    lines.extend(fields(data, [('declaration', 'manifest_path'), ('mode', 'mode'), ('requested targets', 'requested_targets'), ('effective targets', 'effective_targets')]))
    if manifest.get('skills') is not None:
        lines.append(f"  skills: {clean(manifest.get('skills'))}")
    if manifest.get('targets') is not None:
        lines.append(f"  targets: {clean(manifest['targets'])}")
    if 'ownership' in data:
        lines.append(f"  owned links: {len(data['ownership'])}")
    for blocker in data.get('blockers', []) or []:
        lines.append(f"  blocked: {clean(blocker.get('message'))}")
    if data.get('shadowing'):
        lines.append(f"  shadowing: {len(data['shadowing'])} overlap(s)")
    return lines + plan_guard(data, output)


def render_doctor(data, output):
    lines = [f"doctor: {'healthy' if data.get('healthy') else 'problems found'}"]
    for issue in data.get('issues', []) or []:
        lines.append(f"  issue: {clean(issue.get('message') if isinstance(issue, dict) else issue)}")
    lines.extend(fields(data, [('symlinks', 'symlink_capability'), ('host loading', 'host_load')]))
    for blocker in data.get('blockers', []) or []:
        lines.append(f"  blocked: {clean(blocker.get('message'))}")
    if output['would_change']:
        lines.append("  links differ from the declaration; run 'mask apply' or 'mask ensure' to reconcile")
    return lines


def render_ensure(data, output):
    lines = [f"ensure: readiness {clean(data.get('readiness'))}" + (f" ({outcome(output)})" if output['dry_run'] or output['changed'] else '')]
    for item in data.get('scope_readiness', []) or []:
        lines.append(f"  {clean(item.get('root'))}: {clean(item.get('readiness'))}")
    lines.extend(fields(data, [('event', 'event'), ('network', 'network'), ('host loading', 'host_load'), ('approval', 'approval')]))
    for blocker in data.get('blockers', []) or []:
        lines.append(f"  blocked: {clean(blocker.get('message'))}")
    lines.extend(actions(output))
    if data.get('readiness') == 'approval_required':
        lines.append("  approve the consumer with 'mask integration approve --project ROOT' before automatic readiness")
    confirmation = data.get('confirmation')
    if confirmation and confirmation.get('granted_by'):
        lines.append(f"  one-time readiness granted by {clean(confirmation['granted_by'])}; automatic readiness still needs 'mask integration approve'")
    elif confirmation:
        lines.append("  would ask for one-time readiness consent; automatic readiness still needs 'mask integration approve'")
    return lines + plan_guard(data, output)


def render_recover(data, output):
    if not data.get('pending'):
        return ['recover: nothing pending']
    pending = data['pending']
    lines = [f"recover: pending {clean(pending.get('operation') or pending.get('kind'))} ({clean(data.get('recovery_mode', 'inspect'))})"]
    lines.extend(fields(pending, [('generation', 'generation'), ('phase', 'phase'), ('scope', 'scope')]))
    lines.extend(actions(output))
    if data.get('retained_directories'):
        lines.append(f"  retained directories: {clean(data['retained_directories'])}")
    if output['changed']:
        lines.append(f"  transaction: {output['transaction']}")
    return lines


def render_self_status(data, output):
    lines = [f"mask {output['tool_version']} at {clean(data.get('program_root'))}", f"  interpreter: {clean(data.get('interpreter'))}",
             f"  launcher on PATH: {clean(data.get('path_command'))}"]
    launchers = data.get('launchers') or {}
    lines.append(f"  recorded launchers: {len(launchers)}")
    for path, record in (launchers.items() if isinstance(launchers, dict) else ()):
        lines.append(f"    {clean(path)}")
    return lines


def render_config(data, output):
    lines = [headline(output, output['command'].replace('.', ' '))]
    config = data.get('config') or {}
    source = config.get('source') or {}
    if source:
        lines.append(f"  source: {clean(source.get('root'))} ({clean(source.get('remote'))}/{clean(source.get('branch'))})")
    for name, entry in (config.get('sources') or {}).items():
        lines.append(f"  source {clean(name)}: {clean(entry.get('repository'))}")
    lines.extend(fields(config, [('default targets', 'default_targets'), ('git timeout (s)', 'git_timeout_seconds')]))
    lines.extend(fields(data, [('machine state', 'home'), ('program', 'program_root')]))
    return lines


def render_sources(data, output):
    lines = [headline(output, output['command'].replace('.', ' '))]
    sources = data.get('sources')
    if isinstance(sources, dict):
        for name, entry in sources.items():
            lines.append(f"  {clean(name)}: {clean(entry.get('repository'))} @ {clean(entry.get('ref', 'default'))}")
        if not sources:
            lines.append('  no named sources configured')
    lines.extend(fields(data, [('source', 'source'), ('repository', 'repository'), ('ref', 'ref'), ('commit', 'commit'), ('cached revision', 'cached_revision'),
                               ('resolution required', 'resolution_required'), ('migration required', 'migration_required'), ('network', 'network'),
                               ('cache retained', 'cache_retained'), ('phase', 'phase'), ('created commit', 'created_commit'), ('created ref', 'created_ref'), ('pushed', 'pushed')]))
    if 'skills' in data and isinstance(data['skills'], list):
        lines.extend(render_catalog(data, output)[1:])
    return lines + actions(output) + plan_guard(data, output)


def render_update(data, output):
    lines = [headline(output, output['command'].replace('.', ' '))]
    lines.extend(fields(data, [('source before', 'source_before'), ('source after', 'source_after'), ('program before', 'program_before'), ('program after', 'program_after'),
                               ('remote', 'remote_freshness'), ('fetch required', 'requires_fetch'), ('next invocation required', 'next_invocation_required'), ('network', 'network'), ('scope', 'scope')]))
    effects = data.get('fetch_effects')
    if effects:
        lines.append(f"  fetch: {'fetched' if effects.get('fetched') else 'attempted, nothing new' if effects.get('attempted') else 'not attempted'}")
    return lines + change()(data, output)[1:] if 'projects' in data else lines + actions(output) + plan_guard(data, output)


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
    lines = [headline(output, output['command'].replace('.', ' '))]
    lines.extend(fields(data, [('root', 'root'), ('approved', 'approved'), ('approval', 'approval'), ('host loading', 'host_load'), ('coverage', 'coverage')]))
    for path in data.get('files', []) or []:
        lines.append(f"  file: {clean(path)}")
    if data.get('worktree_setup_command'):
        lines.append(f"  worktree setup: {clean(data['worktree_setup_command'])}")
    return lines + actions(output) + plan_guard(data, output)


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
    """install/remove: what was requested, what changed, what was already so, then the engine actions."""
    lines = [headline(output, output['command'])] + fields(data, TASK_SPEC)
    if data.get('declaration_created'):
        lines.append('  declaration: created for this scope' if output['changed'] else '  declaration: would be created for this scope')
    if not data.get('registered', True):
        lines.append('  registration: ' + ('recorded in this operation' if output['changed'] else 'part of this operation'))
    for label, key in (('added', 'added'), ('removed', 'removed'), ('already selected' if output['command'] == 'install' else 'not selected', 'already')):
        if data.get(key):
            lines.append(f"  {label}: {clean(data[key])}")
    if data.get('agents'):
        lines.append(f"  agents for new skills: {clean(data['agents'])}")
    if 'skills' in data:
        lines.append(f"  selected now: {clean(data['skills'])}")
    for blocker in data.get('blockers', []) or []:
        lines.append(f"  blocked: {clean(blocker.get('message'))} ({clean(blocker.get('code'))})")
    lines.extend(actions(output))
    if not output.get('actions') and not data.get('blockers'):
        lines.append('  nothing to do: the selection and links already match')
    return lines + plan_guard(data, output)


def render_list(data, output):
    """One row per selected skill with a column per agent; footer counts and honest limitations."""
    scope = clean(data.get('scope'))
    lines = [f"{scope} skills at {clean(data.get('root'))}"]
    if not data.get('declared'):
        lines.append("  no skills are selected here; add one with 'mask install ID'")
        return lines
    source = data.get('source') or {}
    if source.get('mode') == 'legacy':
        lines.append(f"  source: {clean(source.get('alias'))} {clean(source.get('root'))} (live checkout, not version-pinned)")
    else:
        lines.append(f"  sources: {clean(source.get('sources'))} (pinned)")
    if not data.get('registered'):
        lines.append("  not registered: nothing is deployed; 'mask install ID' or 'mask ensure' deploys the selection")
    agents = data.get('agents', [])
    rows = [dict(skill=entry['skill'], version=entry.get('commit', '-')[:12] if entry.get('commit') else '-', **{agent: entry['states'].get(agent, 'unknown') for agent in agents}) for entry in data.get('skills', [])]
    if rows:
        lines.extend(table(rows, [('SKILL', 'skill'), ('PIN', 'version')] + [(agent.upper(), agent) for agent in agents]))
    else:
        lines.append('  no skills selected')
    links = data.get('links') or {}
    lines.append(f"{len(rows)} skill(s); {clean(links.get('linked', 0))} of {clean(links.get('expected', 0))} managed links in place")
    for limitation in data.get('limitations', []):
        lines.append(f'  limitation: {clean(limitation)}')
    return lines


def render_forget(data, output):
    return [headline(output, 'workspace forget')] + fields(data, [('root', 'root'), ('abandoned paths', 'abandoned_paths')]) + actions(output) + plan_guard(data, output)


RENDERERS = {
    'help': render_help, 'version': render_version, 'capabilities': render_capabilities,
    'init': render_config, 'config.show': render_config, 'config.set': render_config,
    'skill.list': render_catalog, 'skill.validate': lambda data, output: render_catalog(data, output) if 'skills' in data else render_skill(data, output),
    'skill.show': render_skill, 'skill.where-used': render_where_used, 'inventory': render_inventory,
    'install': render_task, 'remove': render_task, 'list': render_list,
    'skill.import': render_provenance, 'skill.provenance': render_provenance, 'skill.record-adaptation': render_provenance,
    'project.init': summary('project init', SCOPE_SPEC), 'project.show': render_show, 'project.set': render_manifest,
    'project.require': render_manifest, 'project.unrequire': render_manifest, 'project.set-agents': render_manifest, 'project.set-targets': render_manifest,
    'project.register': render_manifest, 'project.unregister': render_forget, 'project.list': render_projects,
    'user.init': summary('user init', SCOPE_SPEC), 'user.show': render_show, 'user.set': render_manifest, 'user.require': render_manifest,
    'user.unrequire': render_manifest, 'user.set-agents': render_manifest, 'user.set-targets': render_manifest, 'user.register': render_manifest, 'user.unregister': render_forget,
    'selection-policy.set': change('selection policy', [('policy', 'selection_policy'), ('affected scopes', 'affected_scopes')]),
    'selection-policy.clear': change('selection policy', [('policy', 'selection_policy'), ('affected scopes', 'affected_scopes')]),
    'compatibility.override': change('compatibility override', SCOPE_SPEC), 'compatibility.clear': change('compatibility clear', SCOPE_SPEC),
    'plan': change('plan'), 'apply': change('apply'), 'ensure': render_ensure, 'doctor': render_doctor, 'recover': render_recover,
    'integration.approve': render_integration, 'integration.revoke': render_integration, 'integration.inspect': render_integration,
    'integration.enable': render_integration, 'integration.disable': render_integration, 'launch': render_launch,
    'workspace.forget': render_forget, 'link.adopt': summary('link adopt', [('root', 'root'), ('scope', 'scope'), ('path', 'path'), ('link', 'link_text')]),
    'source.status': render_update, 'source.fetch': render_update, 'source.list': render_sources, 'source.show': render_sources, 'source.inspect': render_sources,
    'source.publish': render_sources, 'source.dev-link': render_manifest, 'source.migrate': render_sources, 'tap.add': render_sources, 'tap.remove': render_sources,
    'lock': render_lock, 'update': render_update, 'migrate': render_manifest,
    'self.status': render_self_status, 'self.install': summary('self install', [('launcher', 'launcher'), ('interpreter', 'interpreter'), ('on PATH', 'on_path')]),
    'self.update': render_update,
}


def warnings(output):
    lines = []
    for warning in output.get('warnings', []):
        detail = warning.get('details') or {key: value for key, value in warning.items() if key not in ('code', 'message')}
        detail = {key: value for key, value in detail.items() if not isinstance(value, (dict, list))} if isinstance(detail, dict) else detail
        lines.append(f"warning: {clean(warning.get('message'))}" + (f" [{clean(detail)}]" if detail else ''))
    return lines


def render(output):
    """Text for stdout on a handled success; always ends with one newline."""
    renderer = RENDERERS.get(output['command'])
    if renderer is None:
        raise KeyError(f"no human renderer registered for {output['command']}")
    lines = renderer(output['data'], output) + warnings(output)
    return '\n'.join(CONTROL.sub('?', line) for line in lines) + '\n'


PRESERVED = {'not_started': 'nothing was changed', 'not_needed': 'nothing was changed', 'rolled_back': 'the started change was rolled back',
             'committed': 'the change had already been committed', 'partial': 'effects are partial; run mask recover --inspect'}


def render_confirmation(proposal, output):
    """The proposal a human answers or automation reviews: scope, planned actions, and the authority it does not grant."""
    lines = [f"{output['command'].replace('.', ' ')}: confirmation needed ({clean(proposal.get('reason'))})"]
    for root in proposal.get('scope', []):
        lines.append(f"  scope: {clean(root)}")
    lines.extend(actions(dict(actions=proposal.get('actions', []))))
    lines.append('  grants: this invocation only; no package scripts, new sources, overwrites or persistent approval')
    return '\n'.join(lines) + '\n'


def render_error(output):
    """Text for stderr on a handled failure: what failed, what is preserved, what to do."""
    error = output['error']
    lines = [f"error: {clean(error['message'])}", f"  code: {clean(error['code'])}"]
    for key, value in (error.get('details') or {}).items():
        lines.append(f"  {clean(key).replace('_', ' ')}: {clean(value)}")
    if output.get('data', {}).get('confirmation') and error['code'].startswith('confirmation.'):
        lines.extend(render_confirmation(output['data']['confirmation'], output).rstrip('\n').split('\n')[1:])
    lines.append(f"  state: {PRESERVED.get(output['transaction'], output['transaction'])}")
    for step in error.get('remediation', []):
        lines.append(f"  next: {clean(step.get('message'))}")
    return '\n'.join(lines + warnings(output)) + '\n'


EVERYDAY = [
    ('init --source DIR', 'select the AgentSkills checkout that supplies skills'),
    ('skill list', 'list the skills the source offers'),
    ('install ID...', 'add skills to this project and deploy them (declares/registers as needed)'),
    ('install ID... --user', 'the same for your personal scope'),
    ('remove ID...', 'remove skills from this project and their links'),
    ('list [--project DIR|--user]', 'show the selected skills and per-agent link state'),
    ('inventory [--project DIR|--user|--all]', 'detailed inventory across registered scopes'),
    ('plan / apply', 'preview or reconcile links for registered scopes'),
    ('ensure', 'make a registered project usable, fetching when allowed'),
    ('update', 'fetch the source and reconcile registered scopes'),
    ('doctor --check', 'report health problems and drift (exit 7 when found)'),
]


def compact_help(version, groups):
    lines = [f'mask {version} - Manage Agent SKills', 'usage: mask [--json] [--home DIR] COMMAND [OPTIONS]', '', 'Everyday commands:']
    pad = max(len(usage) for usage, _ in EVERYDAY)
    lines.extend(f'  {usage.ljust(pad)}  {text}' for usage, text in EVERYDAY)
    lines += ['', f"Command groups: {', '.join(groups)}",
              'Options: --json (machine result), --dry-run and --yes (mutating commands), --home DIR, --debug, --version, --help',
              "Run 'mask COMMAND --help' for a command's arguments."]
    return '\n'.join(lines) + '\n'
