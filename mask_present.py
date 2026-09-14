"""Human presentation for MASK results (RFC-MASK-0018, contract section 5).

Every registered command renders the same structured result object that
``--json`` emits; nothing here decides, mutates or re-derives engine facts.
``RENDERERS`` is the coverage table: a command without an explicit entry is a
defect that ``tests.test_human_output`` rejects, not a case for dumping JSON.
Success text goes to stdout, errors to stderr, plain ASCII, no decoration.
"""
from __future__ import annotations

import re
import shlex

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
            warned = [row for row in data['shadowing'] if not row.get('same_target')]
            lines.append(f"  shadowing: {len(data['shadowing'])} scope overlap(s)"
                         + ('; see warnings' if warned else '; every overlap resolves to one target'))
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


def render_migrate(data, output):
    """doctor --migrate: the conversion preview or its applied result."""
    migration = data.get('migration') or {}
    tap = migration.get('proposed_tap') or {}
    lines = [f"doctor --migrate: {clean(migration.get('machine'))} to taps ({outcome(output)})",
             f"  tap: {clean(tap.get('alias'))} {clean(tap.get('repository'))}"]
    for row in migration.get('changes', []) or []:
        lines.append(f"  legacy {clean(row.get('scope'))}: {clean(row.get('root'))}")
    acquisition = migration.get('acquisition') or {}
    if acquisition:
        lines.append(f"  cache: {clean(acquisition.get('commit'))} from {clean(acquisition.get('source'))}")
    lines.extend(actions(output))
    if output['dry_run'] and data.get('plan_hash'):
        lines.append(f"  apply this preview with 'mask doctor --migrate --expect-plan-hash {clean(data['plan_hash'])}'")
    return lines


def render_doctor(data, output):
    if 'config_after' in (data.get('migration') or {}):
        return render_migrate(data, output)
    lines = [f"doctor: {'healthy' if data.get('healthy') else 'problems found'}"]
    for issue in data.get('issues', []) or []:
        lines.append(f"  issue: {clean(issue.get('message') if isinstance(issue, dict) else issue)}")
    lines.extend(fields(data, [('symlinks', 'symlink_capability'), ('host loading', 'host_load')]))
    for blocker in data.get('blockers', []) or []:
        lines.append(f"  blocked: {clean(blocker.get('message'))}")
    lines.extend(workflow_lines(data, verb='would be deployed by'))
    migration = data.get('migration') or {}
    if migration.get('required'):
        lines.append(f"  migration: required ({clean(migration.get('machine'))})")
        tap = migration.get('proposed_tap') or {}
        if tap:
            lines.append(f"  proposed tap: {clean(tap.get('alias'))} {clean(tap.get('repository'))}")
        for blocker in migration.get('blockers', []) or []:
            lines.append(f"  migration blocked: {clean(blocker.get('message'))}")
        for row in migration.get('consumers', []) or []:
            state = 'migratable' if row.get('migratable') else 'blocked'
            lines.append(f"  legacy {clean(row.get('scope'))}: {clean(row.get('root'))} ({state})")
        lines.append("  preview the conversion with 'mask doctor --migrate --dry-run'")
    if output['would_change']:
        lines.append("  links or roles differ from the declaration; run 'mask apply' or 'mask ensure' to reconcile")
    return lines


def render_ensure(data, output):
    if data.get('repair'):
        return repair_lines(data, output) + backup_lines(data)
    lines = [f"ensure: readiness {clean(data.get('readiness'))}" + (f" ({outcome(output)})" if output['dry_run'] or output['changed'] else '')]
    for item in data.get('scope_readiness', []) or []:
        lines.append(f"  {clean(item.get('root'))}: {clean(item.get('readiness'))}")
    lines.extend(fields(data, [('event', 'event'), ('network', 'network'), ('host loading', 'host_load'), ('approval', 'approval')]))
    for blocker in data.get('blockers', []) or []:
        lines.append(f"  blocked: {clean(blocker.get('message'))}")
    lines.extend(workflow_lines(data))
    lines.extend(setup_lines(data))
    lines.extend(actions(output))
    if data.get('readiness') == 'approval_required':
        lines.append("  approve the consumer with 'mask integration approve --project ROOT' before automatic readiness")
    confirmation = data.get('confirmation')
    if confirmation and confirmation.get('granted_by'):
        lines.append(f"  one-time readiness granted by {clean(confirmation['granted_by'])}; automatic readiness still needs 'mask integration approve'")
    elif confirmation:
        lines.append("  would ask for one-time readiness consent; automatic readiness still needs 'mask integration approve'")
    return lines + plan_guard(data, output)


def workflow_lines(data, verb='will be deployed from'):
    """Declared native roles and consumer inputs per consumer: what matches, what is preserved, what will be deployed."""
    lines = []
    for entry in data.get('workflow_readiness', []) or []:
        declared = [skill for skill in entry.get('skills', []) or [] if skill.get('workflow') == 'declared']
        if declared:
            lines.append(f"  {clean(entry.get('scope', 'project'))}: {clean(entry.get('root'))}")
        for skill in declared:
            pending_roles = any(row.get('state') not in ('ok', 'not_applicable') for row in skill.get('roles') or [])
            status = 'needs deployment' if skill.get('complete') and pending_roles else 'ready' if skill.get('complete') else 'needs attention'
            lines.append(f"    {clean(skill.get('skill'))}: {status} (host loading: not verified)")
            for row in skill.get('retired_files', []):
                if row['state'] != 'absent':
                    note = {'present': 'retired; use ensure --repair to back up and remove', 'remove_planned': 'will back up and remove',
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
                lines.append(f"      {clean(note)}")
                for row in roles:
                    lines.append(f"        {clean(row.get('path') or str(row.get('agent')) + '/' + str(row.get('name')))}")
    return lines


SETUP_NOTES = {
    'consent_required': "needs your yes in a terminal, or --expect-plan-hash HASH with --allow-setup {subject} from automation",
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
    for row in setup.get('actions', []) or []:
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
                               ('remote', 'remote_freshness'), ('fetch required', 'requires_fetch'), ('next invocation required', 'next_invocation_required'), ('network', 'network')]))
    if isinstance(data.get('scope'), str):
        lines.append(f"  scope: {clean(data['scope'])}")
    lines.extend(fetch_lines(data))
    for row in data.get('consumers') or []:
        note = f" ({clean(row['error'].get('code'))})" if row.get('error') else ''
        if row.get('requires_fetch'):
            note += '; the cache lacks this selection, so run update without --dry-run, --offline or --expect-plan-hash to fetch it'
        lines.append(f"  {clean(row.get('scope'))} {clean(row.get('root'))}: {clean(row.get('status'))}{note}")
        lines.extend(f"    {clean(item.get('coordinate'))}: {clean((item.get('before_commit') or 'none')[:12])} -> {clean((item.get('after_commit') or 'none')[:12])}"
                     for item in row.get('changes') or [])
    lines.extend(workflow_lines(data))
    return lines + change()(data, output)[1:] if 'projects' in data else lines + actions(output) + plan_guard(data, output)


def fetch_lines(data):
    effects = data.get('fetch_effects')
    lines = [f"  fetch: {'fetched' if effects.get('fetched') else 'attempted, nothing new' if effects.get('attempted') else 'not attempted (cached candidate used)'}"] if effects else []
    for name, row in (data.get('fetches') or {}).items():
        if not row.get('attempted'):
            outcome_text = 'not attempted (cached content used)'
        elif not row.get('ok'):
            outcome_text = f"failed ({clean((row.get('error') or {}).get('code'))})"
        else:
            outcome_text = 'fetched, configured ref moved' if row.get('remote_refs_changed') else 'fetched, configured ref unchanged'
        lines.append(f"  fetch {clean(name)}: {outcome_text}")
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
    lines.extend(workflow_lines(data))
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


PRESERVED = {'not_started': 'no deployment changes were applied', 'not_needed': 'no deployment changes were needed', 'rolled_back': 'the started change was rolled back',
             'committed': 'deployment changes were saved (this is not a Git commit)', 'partial': 'effects are partial; run mask recover --inspect'}


def render_confirmation(proposal, output):
    """The proposal a human answers or automation reviews: scope, planned actions, and the authority it does not grant."""
    lines = [f"{output['command'].replace('.', ' ')}: confirmation needed ({clean(proposal.get('reason'))})"]
    if proposal.get('kind') == 'package.setup':
        return '\n'.join(lines + setup_proposal_lines(proposal)) + '\n'
    for root in proposal.get('scope', []):
        lines.append(f"  scope: {clean(root)}")
    lines.extend(actions(dict(actions=proposal.get('actions', []))))
    lines.append('  grants: this invocation only; no package scripts, new sources, overwrites or persistent approval')
    return '\n'.join(lines) + '\n'


def render_error(output):
    """Text for stderr on a handled failure: what failed, what is preserved, what to do."""
    error = output['error']
    data = output.get('data', {})
    message = error['message']
    if error['code'] == 'workflow.incomplete' and data.get('workflow_readiness'):
        count = sum(not entry.get('complete') for entry in data['workflow_readiness'])
        message = f'Skill setup is incomplete in {count} scope(s). Existing files were preserved.'
    lines = [f"error: {clean(message)}", f"  code: {clean(error['code'])}"]
    if data.get('repair'):
        lines.extend(repair_lines(data, output)[1:])
    for key, value in (error.get('details') or {}).items():
        if key == 'workflow' and data.get('workflow_readiness'):
            continue
        lines.append(f"  {clean(key).replace('_', ' ')}: {clean(value)}")
    if output.get('data', {}).get('confirmation') and error['code'].startswith('confirmation.'):
        lines.extend(render_confirmation(output['data']['confirmation'], output).rstrip('\n').split('\n')[1:])
    lines.extend(workflow_lines(data, verb='can be deployed by ensure from'))
    lines.extend(setup_lines(data))
    lines.extend(backup_lines(data))
    setup = data.get('setup') or {}
    if setup.get('confirmation') and any(row.get('state') == 'consent_required' for row in setup.get('actions', [])):
        lines.extend(setup_proposal_lines(setup['confirmation']))
    if setup.get('confirmation') and output['dry_run'] and data.get('plan_hash'):
        lines.append(f"  plan hash: {data['plan_hash']}")
    lines.extend(fetch_lines(output.get('data', {})))  # Cache effects before a decline are not activated content.
    if output.get('changed'):
        lines.extend(actions(output))  # A committed link/role transaction is reported even when readiness stayed incomplete.
    lines.append(f"  state: {PRESERVED.get(output['transaction'], output['transaction'])}")
    for step in error.get('remediation', []):
        if error['code'] == 'workflow.incomplete' and data.get('workflow_readiness'):
            continue
        lines.append(f"  next: {clean(step.get('message'))}")
    if error['code'] == 'workflow.incomplete' and data.get('workflow_readiness'):
        lines.extend(workflow_next_steps(data))
    return '\n'.join(lines + warnings(output)) + '\n'


def workflow_next_steps(data):
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
            lines.append('    Repeating setup or adding --yes will not overwrite them. See docs/guides/recovery.md.')
            selection = '--user' if entry.get('scope') == 'user' else '--project ' + shlex.quote(str(entry.get('root')))
            lines.append(f'    Or run mask ensure {clean(selection)} --repair to back up and replace them automatically.')
        else:
            selection = '--user' if entry.get('scope') == 'user' else '--project ' + shlex.quote(str(entry.get('root')))
            lines.append(f"  next: Resolve any missing inputs above, then run mask ensure {clean(selection)}")
            lines.append('    Answer the setup question in a terminal if prompted; update never runs setup.')
    return lines


def backup_lines(data):
    groups = {}
    for row in data.get('backups') or []:
        groups.setdefault((row.get('directory') or row['path'], row.get('state', 'unknown')), 0)
        groups[(row.get('directory') or row['path'], row.get('state', 'unknown'))] += 1
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
                lines.append('    Run mask recover --inspect before retrying.')
    if not output['dry_run']:
        roles = sum(row.get('kind') == 'native_role.write' and row.get('status') == 'applied' for row in output.get('actions') or [])
        links = sum(row.get('kind') == 'link.create' and row.get('status') == 'applied' for row in output.get('actions') or [])
        if roles or links:
            lines.append(f'  Applied: {roles} role file(s), {links} skill link(s).')
        lines.append('  Host loading has not been verified; restart active agents to load changed roles.')
    return lines


EVERYDAY = [
    ('skill list', 'Browse available skills'),
    ('install ID...', 'Add skills to this project and create their links'),
    ('remove ID...', 'Remove selections and their managed links'),
    ('list', 'Show this project\'s selected skills and link status'),
    ('ensure', 'Reconcile this project; offer required setup'),
    ('update', 'Update the shared source and ALL its registered consumers'),
    ('doctor --check', 'Check health without changing files'),
    ('self update', 'Update the MASK program itself'),
]


def compact_help(version, groups):
    lines = [f'mask {version} - Manage Agent Skills', 'usage: mask COMMAND [OPTIONS]',
             'Link shared skills into Claude Code and Codex projects.', '',
             'Start here:', '  mask tap add agentskills https://github.com/MikeMarcin/AgentSkills.git   # approve a skill source once',
             '  mask skill list                         # find a skill ID',
             '  mask install implement-rfc              # add it to the current project',
             '  mask ensure                             # finish any required setup',
             '  mask ensure --all --repair              # fix all registered scopes; back up replaced roles', '', 'Everyday commands:']
    pad = max(len(usage) for usage, _ in EVERYDAY)
    lines.extend(f'  {usage.ljust(pad)}  {text}' for usage, text in EVERYDAY)
    lines += ['', 'Choose where:',
              '  install / remove / list / ensure use the current project by default.',
              '  Add --project DIR for another project or --user for personal skills.',
              '  Bare update changes the shared source for every registered consumer.',
              '  update --project DIR / --user selects independently pinned skills.', '',
              'Preview and diagnose:',
              '  mask ensure --dry-run          Preview this project without running setup',
              '  mask doctor --all --check      Check all registered scopes',
              '  mask inventory --all           List skills across registered scopes',
              '  mask update --help             Understand update scope before fetching', '',
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
    'init': ('Create an empty machine tap catalog. mask tap add creates it automatically when it is missing.', 'mask init\nmask init --target codex --git-timeout 60'),
    'install': ('Add skills and deploy their links. Uses the current project unless --project or --user is supplied. Other selections are kept.', 'mask install implement-rfc\nmask install wizard --user\nmask install wizard --project /path/to/project --dry-run'),
    'remove': ('Remove selected skills and their managed links. Other selections and modified files are kept.', 'mask remove wizard\nmask remove wizard --user'),
    'list': ('Show selected skills and their status in the current project, another project, or your personal scope.', 'mask list\nmask list --user'),
    'ensure': ('Reconcile a project or personal scope and check its required inputs and native agent roles. Only manual ensure can offer package setup. Normal ensure preserves unmanaged or modified files. --repair (--yolo) explicitly authorizes setup and backs up then replaces conflicting role files without prompts. --yes alone does not authorize setup.', 'mask ensure --all --repair            # repair all registered scopes, with backups\nmask ensure --all --repair --dry-run  # preview only\nmask ensure\nmask ensure --project /path/to/project --dry-run\nmask ensure --user\n\nIf existing role files block setup, restore their matching lock from version\ncontrol or review and back up the files before deciding what to replace.\nRepeating normal ensure will not overwrite them. Use --repair for automatic\nbackup and replacement. See docs/guides/recovery.md.\n\nAutomatic startup and --check require prior integration approval.\nFor automation: preview with --dry-run --json, then pass that plan hash with\n--expect-plan-hash HASH --allow-setup SOURCE/ID:ACTION on ensure.'),
    'update': ('With no scope options, fetch and update the shared source for ALL registered consumers that use it, regardless of your current directory. With --project, --user or --all, update independently pinned selections. A shared source cannot be updated for just one project. This command never runs package setup.', 'mask update --dry-run              # preview cached shared-source changes\nmask update                        # fetch and update shared consumers\nmask update --project .            # update this pinned project\nmask update --user                 # update personal pinned selections\nmask update --project . --skill ID # update one pinned selection\n\nIf required setup is missing after update, run ensure for the named consumer.\nUse mask self update to update the MASK program.'),
    'doctor': ('Inspect health, missing files and drift without changing files. --check returns exit 7 when problems are found. On a machine or consumer that still uses a live checkout, doctor reports what migration to taps would convert; --migrate converts it through one recoverable transaction.', 'mask doctor --project . --check\nmask doctor --all --check\nmask doctor --migrate --dry-run\nmask doctor --migrate --expect-plan-hash HASH'),
    'inventory': ('Inspect skill selections, source versions and per-agent links across registered scopes.', 'mask inventory --project .\nmask inventory --all'),
    'plan': ('Preview deployment changes for registered scopes without applying them.', 'mask plan --project .\nmask plan --all'),
    'apply': ('Reconcile managed links for the selected registered scopes. Does not run package setup.', 'mask apply --project . --dry-run\nmask apply --project .'),
    'recover': ('Inspect or finish an interrupted MASK deployment transaction.', 'mask recover --inspect\nmask recover --complete\nmask recover --rollback'),
    'skill.list': ('List the skills available from your configured source.', 'mask skill list'),
    'skill.show': ('Describe an available skill, optionally including its instructions.', 'mask skill show implement-rfc\nmask skill show implement-rfc --content'),
    'self.install': ('Create a MASK launcher in an existing bin directory.', 'mask self install --bin-dir /path/to/bin'),
    'self.update': ('Update the MASK program checkout using its configured Git remote.', 'mask self update --dry-run\nmask self update'),
    'self.status': ('Show the MASK program, interpreter and installed launchers.', 'mask self status'),
    'project.init': ('Create a project skill declaration without installing skills. For the everyday install task, use mask install ID.', 'mask project init --project .'),
    'project.show': ('Show a project\'s declared skill selections and targets.', 'mask project show --project .'),
    'project.set': ('Replace the project\'s entire skill selection. Use install or project require to add skills without removing others.', 'mask project set --skill wizard --skill implement-rfc --dry-run'),
    'project.require': ('Add skills to the project declaration. Use --apply to deploy the selection too.', 'mask project require wizard --apply'),
    'project.unrequire': ('Remove skills from the declaration. Use --apply to reconcile their links too.', 'mask project unrequire wizard --apply'),
    'project.register': ('Register this physical project so MASK can manage its links.', 'mask project register /path/to/project'),
    'project.unregister': ('Stop managing this project. Preserve the declaration and any changed files.', 'mask project unregister /path/to/project --dry-run'),
    'project.list': ('List the physical projects registered on this machine.', 'mask project list'),
    'skill.where-used': ('Find registered consumers that select a skill.', 'mask skill where-used implement-rfc'),
    'skill.validate': ('Validate passive skill package content without running package code.', 'mask skill validate implement-rfc\nmask skill validate --all'),
    'integration.approve': ('Grant persistent automatic-readiness authority to an explicitly selected project or boundary.', 'mask integration approve --project /path/to/project --dry-run'),
    'integration.inspect': ('Inspect project readiness authority and installed integrations.', 'mask integration inspect --project .'),
    'source.status': ('Show the configured shared source checkout and its Git state.', 'mask source status'),
    'source.list': ('List configured source aliases.', 'mask source list'),
    'source.show': ('Show one configured source and its available packages.', 'mask source show NAME'),
    'source.fetch': ('Fetch source content without activating updates in consumers.', 'mask source fetch'),
    'lock': ('Resolve selected requirements to exact versions without deploying them.', 'mask lock --project . --dry-run'),
    'migrate': ('Preview or perform an explicit conversion from shared live selections to independent version pins.', 'mask migrate --to-pinned --project . --dry-run'),
    'capabilities': ('Describe supported commands, schemas and feature boundaries for automation.', None),
    'config.show': ('Show local MASK configuration.', None),
    'config.set': ('Change local default agent targets or Git timeout.', None),
    'compatibility.override': ('Record an explicit exception to advertised compatibility, with a reason.', None),
    'compatibility.clear': ('Remove a recorded compatibility exception.', None),
    'integration.enable': ('Install a selected Git or agent startup integration.', None),
    'integration.disable': ('Remove an owned startup integration, preserving unexpected edits.', None),
    'integration.revoke': ('Remove persistent readiness authority for the selected boundary.', None),
    'launch': ('Check readiness, then launch the selected agent with arguments after --.', None),
    'link.adopt': ('Record ownership of an existing link only when its source matches the explicit expectation.', None),
    'project.set-agents': ('Choose which agents receive one pinned skill in this project.', None),
    'project.set-targets': ('Replace the project\'s agent targets, or restore inherited defaults.', None),
    'selection-policy.set': ('Set machine-level agent selection policy.', None),
    'selection-policy.clear': ('Clear machine-level agent selection policy.', None),
    'skill.import': ('Import skill content from a Git source using an explicit mode and destination.', None),
    'skill.provenance': ('Show the recorded origin and adaptations of a skill.', None),
    'skill.record-adaptation': ('Record an explanation for a local skill adaptation.', None),
    'source.dev-link': ('Switch a pinned skill to a local authoring checkout, or return it to pinned deployment.', None),
    'source.inspect': ('Inspect a prospective Git source without selecting it for deployment.', None),
    'source.migrate': ('Register the existing shared source under a source alias.', None),
    'source.publish': ('Inspect selected source changes; commit or push only when explicitly requested by the corresponding flags.', None),
    'tap.add': ('Register a named Git source for skill discovery.', None),
    'tap.remove': ('Remove a named source registration.', None),
    'user.init': ('Create the personal skill declaration without deploying skills.', None),
    'user.show': ('Show your personal skill declaration.', None),
    'user.set': ('Replace your entire personal skill selection. Use install --user to add skills without removing others.', None),
    'user.require': ('Add skills to your personal declaration; --apply also deploys them.', None),
    'user.unrequire': ('Remove skills from your personal declaration; --apply also reconciles links.', None),
    'user.register': ('Register the personal home in which MASK will manage skill links.', None),
    'user.unregister': ('Stop managing personal links, preserving the declaration and changed files.', None),
    'user.set-agents': ('Choose which agents receive one pinned personal skill.', None),
    'user.set-targets': ('Replace personal agent targets, or restore inherited defaults.', None),
    'workspace.forget': ('Forget an absent workspace only when its recorded identity matches.', None),
}

OPTION_HELP = {
    'json': 'Emit a structured result for scripts; never prompt',
    'debug': 'Include diagnostic details', 'help': 'Show this help', 'version': 'Show MASK version',
    'home': 'MASK state directory (not the project or personal home)',
    'source': 'Local AgentSkills checkout directory', 'project': 'Select a project directory',
    'remote': 'Git remote to use for source updates', 'branch': 'Git branch to use for source updates',
    'user': 'Select your personal skills instead of a project', 'all': 'Select all registered scopes',
    'ids': 'Skill IDs to add or remove', 'id': 'Skill ID',
    'dry-run': 'Preview local/cached changes without applying, fetching or running setup',
    'yes': 'Accept ordinary confirmation; does not authorize package setup or overwrites',
    'expect-plan-hash': 'Require the exact plan hash from a reviewed preview (automation)',
    'check': 'Report readiness without making changes', 'offline': 'Use local/cached content; do not fetch',
    'allow-setup': 'Authorize the named SOURCE/ID:ACTION with --expect-plan-hash; repeatable',
    'repair': 'Repair without prompts: authorize declared setup and back up then replace conflicting role files (--yolo is an alias)',
    'event': 'Invocation context: manual (default), startup, post-checkout, post-merge, post-rewrite or post-commit',
    'agent': 'Agent name (claude or codex)', 'skill': 'Skill ID; repeat for multiple skills',
    'limit': 'Maximum rows to return', 'offset': 'Number of rows to skip',
    'include-unmanaged': 'Also inspect entries MASK does not own',
    'content': 'Include SKILL.md content', 'inspect': 'Report the pending transaction without changing it',
    'complete': 'Complete the pending transaction', 'rollback': 'Roll back the pending transaction',
    'bin-dir': 'Existing directory in which to create the launcher',
    'allow-ref-rebind': 'Explicitly allow a locked Git reference to resolve to a different commit',
    'apply': 'Also deploy the resulting selection', 'clear': 'Explicitly select no skills',
    'target': 'Agent target; repeat for multiple targets', 'targets': 'Agent targets to select',
    'agents': 'Agents to select for this skill', 'inherit': 'Use the configured default selection',
    'path': 'Filesystem path', 'url': 'Git repository URL', 'name': 'Source alias',
    'ref': 'Git branch, tag or commit', 'into': 'Destination skill ID',
    'mode': 'Import mode', 'note': 'Explanation to record with the adaptation',
    'scope': 'Filter by project or personal scope', 'git-timeout': 'Git command timeout in seconds',
    'keep-links': 'Leave links in place and abandon MASK ownership',
    'user-home': 'Personal home directory in which to deploy links',
    'repository': 'Git repository approval boundary', 'under': 'Directory approval boundary',
    'linked-worktrees': 'Include linked worktrees in this approval',
    'inactive-branches': 'Allow readiness on inactive branches',
    'allow-locked-fetch': 'Allow fetching a named locked source; repeatable',
    'git': 'Select Git hook integration', 'host_args': 'Arguments passed to the selected agent after --',
    'expect-identity': 'Require the recorded workspace identity before forgetting it',
    'expect-source': 'Require this exact source when adopting the link',
    'locked': 'Fetch sources needed by locked selections',
    'paths': 'Source paths to include; repeatable', 'commit': 'Explicitly commit the selected source changes',
    'push': 'Explicitly push the source changes', 'message': 'Commit message',
    'authoring-root': 'Local checkout to use while editing this skill',
    'to-pinned': 'Select independent pinned deployment', 'alias': 'Tap alias for the migrated live checkout (doctor --migrate)',
    'migrate': 'Convert a live-checkout machine or consumer to taps through one recoverable transaction',
    'packages': 'Package directory inside the source', 'checkout': 'Local source checkout',
    'refresh': 'Refresh existing version resolutions', 'reason': 'Explanation for this compatibility override',
    'platform': 'Override the advertised platform restriction', 'architecture': 'Override the advertised architecture restriction',
}
