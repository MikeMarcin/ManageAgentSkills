#!/usr/bin/env python3
"""MASK — Manage Agent SKills. Python 3.11+, standard library and Git."""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import sys
import shutil
import subprocess
import textwrap

VERSION = '0.2.0'
PROTOCOL_VERSION = 1
import mask_adapters as adapters

ADAPTERS = adapters.paths()
PROGRAM_ROOT = Path(__file__).resolve().parent


import mask_consent as consent
import mask_core as core
import mask_fs as fs
import mask_install as install_ops
import mask_ensure as ensure_ops
import mask_integration as integration_ops
import mask_report as report_ops
import mask_present as present
import mask_sources as sources_ops
import mask_workflow as workflow
from mask_core import MaskError

class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise MaskError('invocation.invalid', message, 2)


def result(command='', dry_run=False):
    return dict(schema_version=1, tool='mask', tool_version=VERSION, command=command,
                ok=True, dry_run=dry_run, changed=False, would_change=False,
                transaction='not_needed', data={}, actions=[], warnings=[], error=None)


# One registration table drives argparse and public capability descriptors.
COMMANDS = {
    'capabilities': (False, False, []),
    'init': (True, False, [('target', 'repeat'), ('git-timeout', 'int')]),
    'config.show': (False, False, []),
    'config.set': (True, False, [('target', 'repeat'), ('git-timeout', 'int')]),
    'skill.list': (False, False, []),
    'skill.show': (False, False, [('id', 'pos'), ('content', 'flag')]),
    'skill.where-used': (False, False, [('id', 'pos'), ('agent', 'value'), ('scope', 'value'), ('limit', 'int'), ('offset', 'int')]),
    'inventory': (False, False, [('project', 'value'), ('user', 'flag'), ('all', 'flag'), ('include-unmanaged', 'flag'), ('limit', 'int'), ('offset', 'int')]),
    'install': (True, True, [('ids', 'many'), ('project', 'value'), ('user', 'flag'), ('agent', 'repeat'), ('offline', 'flag')]),
    'remove': (True, False, [('ids', 'many'), ('project', 'value'), ('user', 'flag')]),
    'list': (False, False, [('project', 'value'), ('user', 'flag')]),
    'skill.validate': (False, False, [('id', 'optional'), ('all', 'flag')]),
    'skill.import': (True, True, [('url', 'pos'), ('mode', 'required'), ('into', 'required'), ('ref', 'value'), ('path', 'value')]),
    'skill.provenance': (False, False, [('id', 'pos')]),
    'skill.record-adaptation': (True, False, [('id', 'pos'), ('note', 'required')]),
    'project.init': (True, False, [('project', 'value')]),
    'project.show': (False, False, [('project', 'value')]),
    'project.set': (True, False, [('project', 'value'), ('skill', 'repeat'), ('clear', 'flag'), ('apply', 'flag')]),
    'project.require': (True, False, [('project', 'value'), ('ids', 'many'), ('apply', 'flag')]),
    'project.unrequire': (True, False, [('project', 'value'), ('ids', 'many'), ('apply', 'flag')]),
    'project.set-agents': (True, False, [('project', 'value'), ('id', 'pos'), ('agents', 'some'), ('all', 'flag'), ('inherit', 'flag'), ('apply', 'flag')]),
    'selection-policy.set': (True, False, [('agent', 'repeat')]),
    'selection-policy.clear': (True, False, []),
    'compatibility.override': (True, False, [('id', 'pos'), ('project', 'value'), ('user', 'flag'), ('reason', 'required'), ('agent', 'repeat'), ('platform', 'flag'), ('architecture', 'flag')]),
    'compatibility.clear': (True, False, [('id', 'pos'), ('project', 'value'), ('user', 'flag')]),
    'project.set-targets': (True, False, [('project', 'value'), ('targets', 'some'), ('inherit', 'flag'), ('apply', 'flag')]),
    'project.register': (True, False, [('project', 'value'), ('path', 'optional'), ('apply', 'flag')]),
    'project.unregister': (True, False, [('project', 'value'), ('path', 'optional'), ('keep-links', 'flag')]),
    'project.list': (False, False, []),
    'plan': (False, False, [('project', 'value'), ('user', 'flag'), ('all', 'flag')]),
    'apply': (True, False, [('project', 'value'), ('user', 'flag'), ('all', 'flag')]),
    'ensure': (True, True, [('project', 'value'), ('user', 'flag'), ('all', 'flag'), ('event', 'value'), ('check', 'flag'), ('offline', 'flag'), ('allow-setup', 'repeat'), ('repair', 'flag')]),
    'integration.approve': (True, False, [('project', 'value'), ('repository', 'value'), ('under', 'value'), ('linked-worktrees', 'flag'), ('inactive-branches', 'flag'), ('allow-locked-fetch', 'repeat')]),
    'integration.revoke': (True, False, [('project', 'value'), ('repository', 'value'), ('under', 'value')]),
    'integration.inspect': (False, False, [('project', 'value'), ('agent', 'value')]),
    'integration.enable': (True, False, [('project', 'value'), ('git', 'flag'), ('agent', 'value')]),
    'integration.disable': (True, False, [('project', 'value'), ('git', 'flag'), ('agent', 'value')]),
    'launch': (True, True, [('project', 'value'), ('agent', 'required'), ('host_args', 'remainder')]),
    'workspace.forget': (True, False, [('path', 'pos'), ('expect-identity', 'required')]),
    'link.adopt': (True, False, [('project', 'value'), ('user', 'flag'), ('skill', 'required'), ('target', 'required'), ('expect-source', 'required')]),
    'recover': (True, False, [('inspect', 'flag'), ('complete', 'flag'), ('rollback', 'flag')]),
    # Observational unless --migrate, which converts a live-checkout machine or consumer through one journal.
    'doctor': (True, False, [('project', 'value'), ('user', 'flag'), ('all', 'flag'), ('check', 'flag'), ('migrate', 'flag'), ('alias', 'value'), ('offline', 'flag')]),
    'source.fetch': (True, True, [('name', 'optional'), ('locked', 'flag'), ('project', 'value'), ('user', 'flag'), ('offline', 'flag')]),
    'source.list': (False, False, []),
    'source.show': (False, False, [('name', 'pos')]),
    'source.inspect': (True, True, [('url', 'pos'), ('ref', 'value'), ('path', 'value')]),
    'source.publish': (True, True, [('name', 'pos'), ('paths', 'repeat'), ('commit', 'flag'), ('push', 'flag'), ('message', 'value')]),
    'source.dev-link': (True, False, [('id', 'pos'), ('project', 'value'), ('user', 'flag'), ('authoring-root', 'value'), ('to-pinned', 'flag')]),
    'tap.add': (True, False, [('name', 'pos'), ('url', 'pos'), ('ref', 'value'), ('packages', 'value'), ('checkout', 'value'), ('autocrlf', 'flag')]),
    'tap.remove': (True, False, [('name', 'pos')]),
    'lock': (True, False, [('project', 'value'), ('user', 'flag'), ('refresh', 'flag'), ('skill', 'repeat'), ('allow-ref-rebind', 'flag')]),
    # brew/apt vocabulary: update refreshes what is available (this program and the taps); upgrade moves consumers to it.
    'update': (True, True, []),
    'upgrade': (True, True, [('project', 'value'), ('user', 'flag'), ('all', 'flag'), ('skill', 'repeat'), ('allow-ref-rebind', 'flag'), ('offline', 'flag')]),
    'self.status': (False, False, []),
    'self.install': (True, False, [('bin-dir', 'required')]),
}
for action in ('init', 'show', 'set', 'require', 'unrequire', 'set-targets', 'set-agents', 'register', 'unregister'):
    mutates, network, arguments = COMMANDS['project.' + action]
    user_arguments = [(name, shape) for name, shape in arguments if name not in ('project', 'path')]
    if action == 'register':
        user_arguments.append(('user-home', 'value'))
    COMMANDS['user.' + action] = (mutates, network, user_arguments)
GUARDED = {'apply', 'link.adopt', 'upgrade', 'project.set', 'project.require', 'project.unrequire', 'project.set-targets', 'project.register', 'project.unregister'}
GUARDED.update(name.replace('project.', 'user.') for name in tuple(GUARDED) if name.startswith('project.'))
GUARDED.update({'integration.approve', 'integration.revoke'})
GUARDED.update({'integration.enable', 'integration.disable'})
GUARDED.update({'tap.add', 'tap.remove'})
GUARDED.update({'skill.import', 'skill.record-adaptation', 'lock', 'source.dev-link', 'source.publish'})
GUARDED.update({'project.set-agents', 'user.set-agents', 'selection-policy.set', 'selection-policy.clear', 'compatibility.override', 'compatibility.clear'})
GUARDED.add('ensure')
GUARDED.update({'install', 'remove'})
GUARDED.add('doctor')  # --expect-plan-hash binds a reviewed doctor --migrate preview.
IMPLEMENTED = set(COMMANDS)
COMMON = [('json', 'flag'), ('debug', 'flag'), ('help', 'flag'), ('version', 'flag'), ('home', 'value')]


def argument(parser, name, shape):
    kwargs = {'default': argparse.SUPPRESS}
    if name in present.OPTION_HELP:
        kwargs['help'] = present.OPTION_HELP[name]
    positional = shape in {'pos', 'optional', 'many', 'some', 'remainder'}
    if shape == 'remainder':
        kwargs['nargs'] = argparse.REMAINDER
    if shape == 'flag':
        kwargs['action'] = 'store_true'
    elif shape == 'repeat':
        kwargs['action'] = 'append'
    elif shape == 'int':
        kwargs['type'] = int
    elif shape == 'required':
        kwargs['required'] = True
    elif shape in {'optional', 'many', 'some'}:
        kwargs['nargs'] = {'optional': '?', 'many': '+', 'some': '*'}[shape]
    options = [name] if positional else ['--' + name]
    if name == 'repair':
        options.append('--yolo')
    parser.add_argument(*options, **kwargs)


def make_parser():
    root = Parser(prog='mask', add_help=False, description=__doc__, allow_abbrev=False)
    for name, shape in COMMON:
        argument(root, name, shape)
    sub = root.add_subparsers(dest='group', parser_class=Parser)
    groups, leaves = {}, {}
    for command, (mutates, network, arguments) in COMMANDS.items():
        parts = command.split('.')
        if len(parts) == 2:
            if parts[0] not in groups:
                group = sub.add_parser(parts[0], add_help=False, allow_abbrev=False)
                for name, shape in COMMON:
                    argument(group, name, shape)
                groups[parts[0]] = group.add_subparsers(dest='subcommand', parser_class=Parser)
            parent = groups[parts[0]]
        else:
            parent = sub
        description, examples = present.COMMAND_HELP.get(command, (None, None))
        parser = parent.add_parser(parts[-1], add_help=False, allow_abbrev=False,
                                   description=textwrap.fill(description, width=78, break_on_hyphens=False) if description else None,
                                   epilog='Examples:\n  ' + examples.replace('\n', '\n  ') if examples else None,
                                   formatter_class=argparse.RawDescriptionHelpFormatter)
        for name, shape in COMMON + arguments:
            argument(parser, name, shape)
        if command == 'skill.validate':
            parser._option_string_actions['--all'].help = 'Validate every available skill'
        if command in ('project.set-agents', 'user.set-agents'):
            parser._option_string_actions['--all'].help = 'Select all supported agents for this skill'
        if mutates:
            argument(parser, 'dry-run', 'flag')
            argument(parser, 'yes', 'flag')
        if command in GUARDED:
            argument(parser, 'expect-plan-hash', 'value')
        parser.set_defaults(command=command)
        leaves[command] = parser
    return root, leaves


def capabilities(leaves):
    descriptors = []
    for command, (mutates, network, _) in COMMANDS.items():
        arguments = []
        for action in leaves[command]._actions:
            arguments.append(dict(name=action.dest, flags=action.option_strings,
                                  type='integer' if action.type is int else 'boolean' if isinstance(action, argparse._StoreTrueAction) else 'string',
                                  required=action.required, repeatable=isinstance(action, argparse._AppendAction) or action.nargs in ('+', '*'),
                                  nargs=action.nargs, conflicts=CONFLICTS.get(command, {}).get(action.dest, [])))
        descriptors.append(dict(name=command, implemented=command in IMPLEMENTED, arguments=arguments,
                                effect='managed_mutation' if mutates else 'observational', network=network,
                                dry_run=mutates, plan_guard=command in GUARDED, exit_classes=[0, 2, 3, 4, 5, 6, 7, 8, 10, 130]))
    return dict(commands=descriptors, schemas=dict(result=1, project=2, user=2, lock=1, machine=3, state=3, pending=3),
                readable_versions=dict(project=[1, 2], user=[1, 2], lock=[1], machine=[1, 2, 3], state=[1, 2, 3], pending=[1, 2, 3]), scopes=['project', 'user'],
                deployment_model='taps', migration='doctor', line_endings=dict(default='exact', values=['exact', 'autocrlf'], opt_in='tap add --autocrlf'), pinned_deployment=True, per_binding_targeting=True, adapter_contracts=adapters.capabilities(), targets=ADAPTERS, python_minimum='3.11', program_root=str(PROGRAM_ROOT),
                workflow=dict(readiness='workflow_readiness_v1', scope_contracts=['project', 'user'], setup_request_scope=True, native_roles=True, staged_setup=True, repair_with_backups=True, paths=workflow.paths(), retired_paths=True, compatible_locks=True, entrypoints=['ensure', 'install', 'remove', 'upgrade', 'doctor', 'launch'], host_load='not_verified'))


CONFLICTS = {
    'project.set': {'skill': ['clear'], 'clear': ['skill']},
    'project.set-targets': {'targets': ['inherit'], 'inherit': ['targets']},
    'project.register': {'path': ['project'], 'project': ['path']},
    'project.unregister': {'path': ['project'], 'project': ['path']},
    'skill.validate': {'id': ['all'], 'all': ['id']},
    'recover': {'inspect': ['complete', 'rollback'], 'complete': ['inspect', 'rollback'], 'rollback': ['inspect', 'complete']},
    'plan': {'project': ['all'], 'all': ['project']},
    'apply': {'project': ['all'], 'all': ['project']},
    'doctor': {'project': ['all'], 'all': ['project']},
}
for action in ('set', 'set-targets'):
    CONFLICTS['user.' + action] = CONFLICTS['project.' + action]
for command in ('plan', 'apply', 'doctor', 'inventory', 'upgrade', 'ensure'):
    CONFLICTS[command] = {key: [other for other in ('project', 'user', 'all') if other != key] for key in ('project', 'user', 'all')}
CONFLICTS['doctor'].update(check=['migrate'], migrate=['check'])
CONFLICTS['link.adopt'] = {'project': ['user'], 'user': ['project']}
for command in ('install', 'remove', 'list'):
    CONFLICTS[command] = {'project': ['user'], 'user': ['project']}
CONFLICTS['source.dev-link'] = {'project': ['user'], 'user': ['project'], 'authoring_root': ['to_pinned'], 'to_pinned': ['authoring_root']}
CONFLICTS['project.set-agents'] = {key: [other for other in ('agents', 'all', 'inherit') if other != key] for key in ('agents', 'all', 'inherit')}
CONFLICTS['user.set-agents'] = CONFLICTS['project.set-agents']
for command in ('compatibility.override', 'compatibility.clear'):
    CONFLICTS[command] = {'project': ['user'], 'user': ['project']}
CONFLICTS['lock'] = {'project': ['user'], 'user': ['project']}
CONFLICTS['source.fetch'] = {'name': ['locked'], 'locked': ['name'], 'project': ['user'], 'user': ['project']}


def validate_arguments(args):
    command = args.command
    if command == 'ensure' and getattr(args, 'repair', False) and getattr(args, 'event', 'manual') != 'manual':
        raise MaskError('invocation.invalid', '--repair is a manual command and cannot be used by startup hooks.', 2)
    for key, conflicts in CONFLICTS.get(command, {}).items():
        if getattr(args, key, None) and any(getattr(args, other, None) for other in conflicts):
            raise MaskError('invocation.invalid', f'{key} conflicts with {", ".join(conflicts)}', 2)
    required_sets = {'project.set-agents': ('agents', 'all', 'inherit'), 'user.set-agents': ('agents', 'all', 'inherit'),
                     'selection-policy.set': ('agent',), 'compatibility.override': ('project', 'user'), 'compatibility.clear': ('project', 'user'),
                     'project.set': ('skill', 'clear'), 'project.set-targets': ('targets', 'inherit'),
                     'user.set': ('skill', 'clear'), 'user.set-targets': ('targets', 'inherit'), 'link.adopt': ('project', 'user'),
                     'config.set': ('target', 'git_timeout'), 'skill.validate': ('id', 'all'),
                     'recover': ('inspect', 'complete', 'rollback')}
    if command == 'doctor' and not getattr(args, 'migrate', False) and any(getattr(args, key, None) for key in ('alias', 'offline', 'dry_run', 'yes', 'expect_plan_hash')):
        raise MaskError('invocation.invalid', '--alias, --offline, --dry-run, --yes and --expect-plan-hash apply only to doctor --migrate.', 2)
    if command == 'compatibility.override' and not any(getattr(args, key, None) for key in ('agent', 'platform', 'architecture')):
        raise MaskError('invocation.invalid', 'An explicit compatibility dimension is required.', 2)
    if command in required_sets and not any(getattr(args, key, None) for key in required_sets[command]):
        raise MaskError('invocation.invalid', 'An explicit operand or mode is required.', 2)
    if any(not consent.GRANT_RE.fullmatch(entry) for entry in getattr(args, 'allow_setup', None) or []):
        raise MaskError('invocation.invalid', 'Each --allow-setup entry names one exact SOURCE/ID:ACTION; nothing else grants setup.', 2)


def machine_home(args):
    return Path(getattr(args, 'home', os.environ.get('MASK_HOME', str(Path.home() / '.mask')))).expanduser().resolve()


def machine_config(home):
    return core.config(core.read_json(home / 'config.json'))


def selected_roots(args, state, *, all_default=False):
    if getattr(args, 'user', False):
        if not state.get('user'):
            core.fail('user.not_registered', 'User scope is not registered.', 4)
        return [Path(state['user']['root'])]
    if getattr(args, 'all', False) or all_default and not getattr(args, 'project', None):
        return [Path(key) for key in sorted(core.consumer_records(state))]
    root = core.project_root(getattr(args, 'project', None))
    for known in state['projects']:
        if Path(known).is_dir() and os.path.samefile(root, known):
            root = Path(known)
            break
    if str(root) not in state['projects']:
        core.fail('project.not_registered', 'Project is not registered.', 4, root=str(root))
    return [root]


# Commands that stay available on a v1/v2 (live-checkout) machine so it can be inspected, recovered and migrated.
MIGRATION_EXEMPT = {'capabilities', 'config.show', 'doctor', 'recover'}


def migration_gate(command, home):
    """Refuse every other command on a v1/v2 machine before any effect; a missing configuration is not gated."""
    if command in MIGRATION_EXEMPT or command.startswith('self.') or command == 'update':
        return  # update still advances the program on a v1/v2 machine; it skips the taps such a machine does not have.
    try:
        value = core.read_json(home / 'config.json', default={})
    except MaskError:
        return  # An unreadable configuration is reported by the command that reads it.
    core.refuse_legacy_config(value)


def diagnostics(args, output, home):
    import mask_legacy
    config = core.config(core.read_json(home / 'config.json'), legacy=True)
    state = core.state(core.read_json(home / 'state.json', 'state', default=core.empty_state()))
    migration, migration_warnings = mask_legacy.inspect(home, config, state, project=getattr(args, 'project', None), user=getattr(args, 'user', False))
    pending = [MaskError('recovery.required', 'A pending operation requires inspection.', 8).as_dict()] if core.kind(home / 'pending.json') != 'missing' else []
    symlinks = 'unknown' if os.name == 'nt' else 'available'
    consumer_issue = MaskError('migration.required', 'A consumer still uses the retired live-checkout model; preview its conversion with mask doctor --migrate --dry-run.', 4,
                               details=dict(roots=[row['root'] for row in migration['consumers']], remediation=core.MIGRATION_REMEDIATION)).as_dict()
    try:
        core.refuse_legacy_config(config)
        roots = selected_roots(args, state, all_default=True)
    except MaskError as error:
        if error.code == 'migration.required':
            # Reported only: nothing is planned on a live-checkout machine, so no checkout link is derived or observed.
            issues = [error.as_dict(), *pending]
        elif error.code in ('project.not_registered', 'user.not_registered') and migration['consumers']:
            # An unregistered v1 declaration is reported for migration instead of refused as unregistered.
            issues = [consumer_issue, *pending]
        else:
            raise
        output['data'].update(healthy=False, issues=issues, migration=migration, filesystem_present=False, host_load='not_verified', symlink_capability=symlinks)
        output['warnings'].extend(migration_warnings)
        if getattr(args, 'check', False):
            core.fail('state.drift', 'Doctor found actionable drift or health failures.', 7)
        return
    planned = fs.plan(config, state, roots, home=home)
    fs.public_plan(planned, output)
    issues = list(planned['blockers']) + pending
    try:
        fs.pinned.verify_artifacts(planned['intent']['after_state'], [str(root) for root in roots], home)
    except MaskError as error:
        issues.append(error.as_dict())
    drift = bool(planned['would_change'])
    # Declared prerequisites are observed with the links (RFC-MASK-0019 AC01); no package code runs and nothing is deployed here.
    output['data']['workflow'] = ensure_ops.scope_workflows(planned)
    unmet = ensure_ops.observe(planned)
    if unmet:
        issues.append(MaskError('workflow.incomplete', 'Declared native roles or consumer inputs are not satisfied.', 7, details=dict(workflow=unmet)).as_dict())
    for root in roots:
        if not root.is_dir() or core.consumer_scope(state, root) == 'user':
            continue
        for relative in state['projects'][str(root)]['links']:
            tracked = core.git(root, 'ls-files', '--error-unmatch', '--', relative, optional=True) is not None
            ignored = core.git(root, 'check-ignore', '--quiet', '--no-index', '--', relative, optional=True) is not None
            if tracked or not ignored:
                output['warnings'].append(dict(code='project.link_ignore', message='Managed link is tracked or not ignored by Git.', details=dict(path=str(root / relative), tracked=tracked, ignored=ignored)))
    if migration['required'] and not any(item['code'] == 'migration.required' for item in issues):
        issues.append(consumer_issue)
    output['warnings'].extend(migration_warnings)
    output['data'].update(healthy=not issues and not drift, issues=issues, filesystem_present=not issues and not drift, migration=migration,
                          host_load='not_verified', symlink_capability='unknown' if os.name == 'nt' else 'available')
    if getattr(args, 'check', False) and (issues or drift):
        core.fail('state.drift', 'Doctor found actionable drift or health failures.', 7, **(dict(workflow=unmet) if unmet else {}))


def reconciliation(args, output, home):
    config = machine_config(home)
    state = core.state(core.read_json(home / 'state.json', 'state', default=core.empty_state()))
    roots = selected_roots(args, state)
    planned = fs.plan(config, state, roots, home=home)
    fs.public_plan(planned, output)
    if args.command == 'apply':
        fs.ensure_applicable(planned, getattr(args, 'expect_plan_hash', None))
        if not output['dry_run']:
            fs.execute(planned, home, output)


def project_dispatch(args, output, home):
    scope = 'user' if args.command.startswith('user.') else 'project'
    command = args.command.replace('user.', 'project.')
    state = core.state(core.read_json(home / 'state.json', 'state', default=core.empty_state()))
    config_raw = core.read_json(home / 'config.json', default={})
    config = core.config(config_raw) if config_raw else None
    if command == 'project.list':
        output['data'] = dict(projects=[dict(record, available=Path(root).is_dir()) for root, record in sorted(state['projects'].items())])
        return
    selection = getattr(args, 'project', getattr(args, 'path', None))
    if scope == 'user':
        record = state.get('user')
        root = Path(record['root']) if record else Path.home().resolve()
        if hasattr(args, 'user_home'):
            selected = Path(args.user_home).expanduser().resolve()
            if record and selected != root:
                core.fail('user.already_registered', 'Unregister the existing user home before selecting another.', 4)
            root = selected
        if command == 'project.register' and not root.is_dir():
            core.fail('user.not_found', 'User home must be an existing directory.', 4, root=str(root))
    elif command == 'project.unregister' and getattr(args, 'keep_links', False) and selection is not None:
        root = Path(selection).expanduser().resolve()
    else:
        root = core.project_root(selection, initializing=command == 'project.init')
    path = core.declaration_path(root, scope, home)
    key = str(root)
    for known, existing_record in (state['projects'].items() if scope == 'project' else []):
        if root.is_dir() and Path(known).is_dir() and core.identity(root) == existing_record['root_identity'] and os.path.samefile(root, known):
            root, key = Path(known), known
            path = root / '.mask.json'
            break
    record = state.get('user') if scope == 'user' else state['projects'].get(key)
    if command == 'project.init':
        if core.kind(path) != 'missing':
            declaration = core.selection_manifest(core.read_json(path, 'manifest'))
            output['data'] = dict(root=key, manifest=declaration)
            return
        # A new consumer is a v2 selection with its empty lock, as install creates one; no machine configuration is written.
        import mask_resolve
        import mask_task
        fresh = mask_task.fresh_declaration(config)
        created = {path: fresh}
        lock_path = mask_resolve.lock_path(root, scope, home)
        if core.kind(lock_path) == 'missing':
            created[lock_path] = dict(schema_version=1, resolver='mask-lock-v1', selection_digest=mask_resolve.selection_digest(fresh), packages=[])
        output['data'] = dict(root=key, manifest=created[path])
        output['would_change'] = True
        if not output['dry_run']:
            for control, value in created.items():
                core.atomic_text(control, core.text_json(value), None)
            output.update(changed=True, transaction='committed')
        return
    if command == 'project.unregister':
        if record is None:
            output['data'] = dict(root=key, registered=False)
            return
        keep = getattr(args, 'keep_links', False)
        if scope == 'user' or record['links'] and not keep:
            planned = fs.plan(config, state, [root], unregister=[key], keep_links=keep, operation=args.command, home=home)
            fs.public_plan(planned, output)
            fs.ensure_applicable(planned, getattr(args, 'expect_plan_hash', None))
            if not output['dry_run']:
                fs.execute(planned, home, output)
            return
        if not keep:
            core.registered_root(root, record)
        after = copy.deepcopy(state)
        del after['projects'][key]
        output['data'] = dict(root=key, registered=False, abandoned_paths=[str(root / rel) for rel in record['links']] if keep else [])
        output['would_change'] = True
        output['data']['plan_hash'] = core.digest(dict(command=command, root=key, state=state, after=after, config=config))
        if getattr(args, 'expect_plan_hash', output['data']['plan_hash']) != output['data']['plan_hash']:
            core.fail('plan.stale', 'Registry operation changed since preview.', 4)
        if not output['dry_run']:
            core.save_state(home, state, after)
            output.update(changed=True, transaction='committed')
        return
    declaration_text = core.read_text(path, 'manifest')
    declaration = core.selection_manifest(core.parse_json(declaration_text, 'manifest'))
    if declaration['schema_version'] == 1:
        core.migration_required('A v1 declaration must be migrated to a v2 declaration before this command.', path=str(path))
    if record:
        core.registered_root(root, record, scope)
    import mask_pinned
    mode = (record or {}).get('mode', 'pinned')
    output['data'] = dict(root=key, scope=scope, manifest_path=str(path), manifest=declaration, registered=record is not None,
                          configured_targets=None, effective_targets=None, mode=mode, reproducible=mode != 'dev-link',
                          fleet_eligible=mode != 'dev-link', requested_targets=mask_pinned.simple_targets(declaration))
    if command == 'project.show':
        output['data']['ownership'] = record['links'] if record else {}
        if config:
            inspection = fs.plan(config, state, [root], register=[] if record else [key], home=home, user_root=root if scope == 'user' else None)
            output['data']['source'] = inspection['source']
            output['data']['expected_links'] = core.consumer_records(inspection['intent']['after_state']).get(key, {}).get('links', {})
            observations = inspection['users'] if scope == 'user' else inspection['projects']
            output['data']['actual_links'] = observations[0]['leaves'] if observations else []
            output['data']['blockers'] = inspection['blockers']
            output['data']['outcomes'] = inspection['outcomes']
            output['data']['shadowing'] = inspection['shadowing']
            output['warnings'].extend(fs.shadow_warnings(inspection['shadowing']))
            output['data']['effective_targets'] = sorted({row['agent'] for row in inspection['outcomes'] if row['status'] in ('selected', 'deployed', 'overridden')})
        output['data']['host_load'] = 'not_verified'
        return
    if config is None:
        core.fail('config.missing', 'Add a skill source before this operation.')
    apply = getattr(args, 'apply', False)
    if command == 'project.register':
        if record and not apply:
            return
        core.registration_safe(root, home, state, scope)
        planned = fs.plan(config, state, [root], register=[key], operation=args.command, home=home,
                          user_root=root if scope == 'user' else None, register_only=not apply)
        fs.public_plan(planned, output)
        fs.ensure_applicable(planned, getattr(args, 'expect_plan_hash', None))
        if not output['dry_run']:
            fs.execute(planned, home, output)
        return
    if apply and record is None:
        core.fail(scope + '.not_registered', '--apply requires a registered consumer.', 4)
    # set, require and unrequire only ever edited v1 string selections, which are retired; install and remove edit v2 declarations.
    # The consumer guard (mask_resolve.guard_command) normally refuses first with this same refusal.
    import mask_resolve
    mask_resolve.refuse_selection_setter(args)


def local_dispatch(args, output, leaves):
    command = args.command
    home = machine_home(args)
    if command == 'capabilities':
        output['data'] = capabilities(leaves)
        return
    import mask_resolve
    if command == 'lock':
        return mask_resolve.dispatch(args, output, home)
    if command == 'source.fetch' and getattr(args, 'locked', False):
        import mask_store
        return mask_store.dispatch(args, output, home)
    if command == 'source.fetch' and any(getattr(args, flag, False) for flag in ('project', 'user', 'offline')):
        core.fail('invocation.invalid', 'Scope/offline options require source fetch --locked.', 2)
    if command == 'source.fetch' and not getattr(args, 'name', None):
        import mask_update
        return mask_update.fetch_all(args, output, home)
    mask_resolve.guard_command(args, home)
    if command in ('inventory', 'skill.where-used'):
        return report_ops.dispatch(args, output, home)
    if command == 'list':
        import mask_task
        return mask_task.dispatch(args, output, home)
    if command in ('skill.import', 'skill.provenance', 'skill.record-adaptation'):
        import mask_provenance
        return mask_provenance.dispatch(args, output, home)
    if command == 'source.publish':
        return sources_ops.publication(args, output, home)
    if command == 'source.inspect':
        return sources_ops.inspect(args, output, home)
    if command in ('source.list', 'source.show', 'source.fetch', 'tap.add', 'tap.remove'):
        return sources_ops.dispatch(args, output, home)
    if command in ('integration.enable', 'integration.disable'):
        return integration_ops.dispatch(args, output, home)
    if command in ('ensure', 'workspace.forget') or command.startswith('integration.'):
        return ensure_ops.dispatch(args, output, home)
    if command == 'init':
        # An empty v3 tap catalog; taps are approved separately with tap add, which also bootstraps a missing machine.
        proposal = core.empty_config(getattr(args, 'target', None), getattr(args, 'git_timeout', 30))
        core.state(core.read_json(home / 'state.json', 'state', default=core.empty_state()))
        existing = core.read_json(home / 'config.json', default={})
        if existing:
            current = core.config(existing)
            explicit = [key for key, option in (('default_targets', 'target'), ('git_timeout_seconds', 'git_timeout')) if hasattr(args, option)]
            if any(current[key] != proposal[key] for key in explicit):
                core.fail('config.already_initialized', 'Machine already has a different configuration.', 4, schema_version=current['schema_version'])
            proposal = current
        output['data'] = dict(config=proposal, program_root=str(PROGRAM_ROOT))
        if not existing:
            output['would_change'] = True
            output['actions'] = [dict(kind='config.create', status='planned')]
            if not output['dry_run']:
                core.atomic_text(home / 'config.json', core.text_json(proposal), None)
                if core.kind(home / 'state.json') == 'missing':
                    core.atomic_text(home / 'state.json', core.text_json(core.empty_state()), None)
                output.update(changed=True, transaction='committed')
        return
    if command.startswith('self.'):
        return install_ops.dispatch(args, output, home, PROGRAM_ROOT)
    if command == 'update':
        import mask_update
        return mask_update.refresh(args, output, home, PROGRAM_ROOT)
    if command == 'recover':
        mode = 'inspect' if getattr(args, 'inspect', False) else 'complete' if getattr(args, 'complete', False) else 'rollback'
        pending = core.read_json(home / 'pending.json', 'recovery', default={})
        if str(pending.get('operation', '')).startswith('integration.'):
            return integration_ops.recover(home, output, mode)
        return fs.recover(home, output, mode)
    if command == 'doctor':
        return diagnostics(args, output, home)
    if command == 'link.adopt':
        config = machine_config(home)
        state = core.state(core.read_json(home / 'state.json', 'state', default=core.empty_state()))
        return fs.adopt(config, state, selected_roots(args, state)[0], args.skill, args.target, args.expect_source, output, home, getattr(args, 'expect_plan_hash', None))
    if command in ('plan', 'apply'):
        return reconciliation(args, output, home)
    if command.startswith(('project.', 'user.')):
        return project_dispatch(args, output, home)
    if command in ('skill.list', 'skill.show', 'skill.validate'):
        return sources_ops.query(args, output, home)
    if command == 'config.show':
        config = core.config(core.read_json(home / 'config.json'), legacy=True)
        output['data'] = dict(config=config, program_root=str(PROGRAM_ROOT), home=str(home), migration_required=config['schema_version'] != 3)
        return
    if command != 'config.set':
        core.fail('config.command_unavailable', 'This command is not implemented in this version.')
    config = machine_config(home)
    proposal = dict(config)
    if hasattr(args, 'target'):
        proposal['default_targets'] = args.target
    if hasattr(args, 'git_timeout'):
        proposal['git_timeout_seconds'] = args.git_timeout
    proposal = core.config(proposal)
    output['data'] = dict(config=proposal)
    output['would_change'] = proposal != config
    if proposal != config and not output['dry_run']:
        core.atomic_text(home / 'config.json', core.text_json(proposal), core.read_text(home / 'config.json'))
        output.update(changed=True, transaction='committed')


def locked_dispatch(args, output, leaves, home, preparation):
    with core.writer_lock(home):
        if args.command != 'recover' and core.kind(home / 'pending.json') != 'missing':
            core.fail('recovery.required', 'Inspect and recover the pending operation first.', 8)
        import mask_pinned
        mask_pinned.recheck_preparation(preparation, home)
        try:
            local_dispatch(args, output, leaves)
        finally:
            if preparation is not None:
                output['data']['preparation'] = preparation['effects']
                output['data']['network'] = 'locked_fetch' if any(item['effects'].get('network_attempted') for item in preparation['effects']) else 'none'


def dispatch_impl(args, output, leaves):
    home = machine_home(args)
    migration_gate(args.command, home)
    if args.command == 'launch':
        if args.agent not in ADAPTERS:
            core.fail('invocation.invalid', 'Choose a supported agent.', 2)
        executable = shutil.which(args.agent)
        if executable is None or os.name == 'nt' and Path(executable).suffix.lower() in ('.cmd', '.bat'):
            core.fail('host.unavailable', 'Configure a directly executable host on PATH before launch.', 4)
        ensure_args = argparse.Namespace(**vars(args))
        ensure_args.command, ensure_args.event = 'ensure', 'startup'
        dispatch(ensure_args, output, leaves)
        if output['dry_run']:
            return
        operands = getattr(args, 'host_args', [])
        if operands and operands[0] == '--':
            operands = operands[1:]
        run = subprocess.run([executable, *operands], cwd=getattr(args, 'project', None),
                             capture_output=getattr(args, 'json', False), text=True)
        output['data']['host'] = dict(agent=args.agent, exit_code=run.returncode, executable=executable)
        if getattr(args, 'json', False):
            output['data']['host'].update(stdout=run.stdout, stderr=run.stderr)
        if run.returncode:
            core.fail('host.failed', 'The host exited unsuccessfully after readiness.', 5, exit_code=run.returncode)
        return
    if args.command not in IMPLEMENTED:
        core.fail('config.command_unavailable', 'This command is not implemented in this version.')
    if args.command == 'doctor' and getattr(args, 'migrate', False):
        import mask_migrate
        return mask_migrate.dispatch(args, output, home)
    # Plain doctor stays observational: it takes no writer lock and a pending journal is reported, not refused.
    mutates = COMMANDS[args.command][0] and args.command != 'doctor' and not output['dry_run'] and not (args.command == 'recover' and getattr(args, 'inspect', False)) and not (args.command == 'ensure' and getattr(args, 'check', False))
    if args.command == 'ensure' and getattr(args, 'repair', False) and getattr(args, 'all', False):
        if getattr(args, 'event', 'manual') != 'manual':
            core.fail('invocation.invalid', '--repair is a manual command and cannot be used by startup hooks.', 2)
        from mask_repair import ensure_all
        return ensure_all(args, output, home, lambda selected, child, _: dispatch(selected, child, leaves))
    if args.command == 'source.fetch' and getattr(args, 'locked', False):
        if core.kind(home / 'pending.json') != 'missing':
            core.fail('recovery.required', 'Recover pending consumer effects before exact preparation.', 8)
        return local_dispatch(args, output, leaves)
    import mask_pinned
    import mask_selection
    import mask_task
    if mask_selection.dispatch(args, output, home) or mask_task.dispatch(args, output, home):
        return
    if args.command == 'upgrade':
        import mask_update
        return mask_update.dispatch(args, output, home)
    if args.command == 'source.dev-link':
        return mask_pinned.dev_dispatch(args, output, home)
    preparation = mask_pinned.prepare_dispatch(args, output, home) if mutates else None
    if mutates:
        while True:
            try:
                locked_dispatch(args, output, leaves, home, preparation)
                break
            except consent.ConsentRequired as pending:
                # The writer lock is released here; a human answers, then the exact proposal is rechecked under the lock.
                kind = pending.request['kind']
                consented, declined = getattr(args, 'consented', None) or {}, getattr(args, 'declined', None) or set()
                if kind in consented or kind in declined:
                    core.fail('internal.invariant', 'An answered consent kind was asked again.', 10, kind=kind)
                if consent.ask(pending.request, present.render_confirmation(pending.request, output)):
                    args.consented = {**consented, kind: pending.request['plan_hash']}
                elif kind in consent.CONTINUES_ON_DECLINE:
                    args.declined = declined | {kind}
                else:
                    core.fail('confirmation.declined', 'Declined; nothing was applied.', 4, reason=pending.request['reason'])
                output.clear()
                output.update(result(args.command, getattr(args, 'dry_run', False)))
    else:
        observed = args.command not in ('capabilities',)
        before = [core.read_text(home / name, 'state', missing=True) for name in ('config.json', 'state.json', 'pending.json', 'user.json', 'integration.json', 'integrations.json', 'selection-policy.json')] if observed else []
        local_dispatch(args, output, leaves)
        after = [core.read_text(home / name, 'state', missing=True) for name in ('config.json', 'state.json', 'pending.json', 'user.json', 'integration.json', 'integrations.json', 'selection-policy.json')] if observed else []
        if before != after:
            core.fail('state.drift', 'Machine state changed during inspection; retry the observational command.', 4)
    if output['dry_run'] and output['would_change']:
        output['transaction'] = 'not_started'
    for action in output['actions']:
        if output['changed']:
            action['status'] = 'applied'


def dispatch(args, output, leaves):
    import mask_pinned
    completed = False
    try:
        dispatch_impl(args, output, leaves)
        completed = True
    finally:
        mask_pinned.merge_preparation(output, completed=completed)


def help_text(parser, leaves, words):
    """Compact everyday help for the root, the subcommand list for a group, argparse detail for a leaf."""
    groups = sorted({name.split('.')[0] for name in COMMANDS if '.' in name})
    selected = '.'.join(words[:2])
    if selected in leaves:
        return leaves[selected].format_help()
    if words and words[0] in groups:
        members = [name.split('.')[1] for name in COMMANDS if name.startswith(words[0] + '.')]
        lines = [f"usage: mask {words[0]} SUBCOMMAND [OPTIONS]", 'subcommands:']
        for member in members:
            description = present.COMMAND_HELP.get(f'{words[0]}.{member}', ('', ''))[0]
            lines.append(f'  {member:16} {description}'.rstrip())
        lines.append(f"Run 'mask {words[0]} SUBCOMMAND --help' for arguments and examples.")
        return '\n'.join(lines) + '\n'
    if words and words[0] in leaves:
        return leaves[words[0]].format_help()
    return present.compact_help(VERSION, groups)


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):  # Human text and JSON are UTF-8 on every OS, piped or not.
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    argv = list(sys.argv[1:] if argv is None else argv)
    core.FROZEN.clear()  # Object-addressed Git answers are reused within one invocation only.
    before_separator = argv[:argv.index('--')] if '--' in argv else argv
    machine = '--json' in before_separator
    output = result()
    exit_code = 0
    try:
        parser, leaves = make_parser()
        if '--help' in before_separator or '--version' in before_separator or not [item for item in before_separator if item not in ('--json', '--debug')]:
            output['command'] = 'version' if '--version' in before_separator else 'help'
            output['data'] = {'version': VERSION}
            if output['command'] == 'help':
                words = [item for item in before_separator if not item.startswith('-')]
                output['data']['help'] = help_text(parser, leaves, words)
        else:
            args = parser.parse_args(argv)
            if not hasattr(args, 'command'):
                members = [name.split('.')[1] for name in COMMANDS if name.startswith(f"{getattr(args, 'group', '')}.")]
                raise MaskError('invocation.invalid', f"'mask {args.group}' needs one of these subcommands: {', '.join(members)}." if members else 'A complete command is required.', 2)
            output = result(args.command, getattr(args, 'dry_run', False))
            validate_arguments(args)
            dispatch(args, output, leaves)
    except MaskError as error:
        output.update(ok=False, error=error.as_dict())
        if output['transaction'] == 'not_needed':
            output['transaction'] = 'not_started'
        exit_code = error.exit_code
    except KeyboardInterrupt:
        error = MaskError('invocation.interrupted', 'Interrupted by user.', 130)
        output.update(ok=False, error=error.as_dict())
        if output['transaction'] == 'not_needed':
            output['transaction'] = 'not_started'
        exit_code = 130
    except OSError:
        error = MaskError('filesystem.failed', 'A filesystem operation failed.', 5)
        output.update(ok=False, error=error.as_dict())
        if output['transaction'] == 'not_needed':
            output['transaction'] = 'not_started'
        exit_code = 5
    except Exception:
        error = MaskError('internal.invariant', 'An internal invariant failed.', 10)
        output.update(ok=False, error=error.as_dict())
        if output['transaction'] == 'not_needed':
            output['transaction'] = 'not_started'
        exit_code = 10
    if machine:
        print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    elif output['error']:
        sys.stderr.write(present.render_error(output))
    else:
        sys.stdout.write(present.render(output))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
