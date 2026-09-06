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

VERSION = '0.2.0'
PROTOCOL_VERSION = 1
ADAPTERS = {'claude': '.claude/skills', 'codex': '.agents/skills'}
PROGRAM_ROOT = Path(__file__).resolve().parent


import mask_core as core
import mask_fs as fs
import mask_git as git_ops
import mask_install as install_ops
import mask_ensure as ensure_ops
import mask_integration as integration_ops
import mask_report as report_ops
import mask_sources as sources_ops
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
    'init': (True, False, [('source', 'required'), ('remote', 'value'), ('branch', 'value'), ('target', 'repeat')]),
    'config.show': (False, False, []),
    'config.set': (True, False, [('target', 'repeat'), ('git-timeout', 'int')]),
    'skill.list': (False, False, []),
    'skill.show': (False, False, [('id', 'pos'), ('content', 'flag')]),
    'skill.where-used': (False, False, [('id', 'pos'), ('agent', 'value'), ('scope', 'value'), ('limit', 'int'), ('offset', 'int')]),
    'inventory': (False, False, [('project', 'value'), ('user', 'flag'), ('all', 'flag'), ('include-unmanaged', 'flag'), ('limit', 'int'), ('offset', 'int')]),
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
    'ensure': (True, True, [('project', 'value'), ('event', 'value'), ('check', 'flag'), ('offline', 'flag')]),
    'integration.approve': (True, False, [('project', 'value'), ('repository', 'value'), ('under', 'value'), ('linked-worktrees', 'flag'), ('inactive-branches', 'flag'), ('allow-locked-fetch', 'repeat')]),
    'integration.revoke': (True, False, [('project', 'value'), ('repository', 'value'), ('under', 'value')]),
    'integration.inspect': (False, False, [('project', 'value'), ('agent', 'value')]),
    'integration.enable': (True, False, [('project', 'value'), ('git', 'flag'), ('agent', 'value')]),
    'integration.disable': (True, False, [('project', 'value'), ('git', 'flag'), ('agent', 'value')]),
    'launch': (True, True, [('project', 'value'), ('agent', 'required'), ('host_args', 'remainder')]),
    'workspace.forget': (True, False, [('path', 'pos'), ('expect-identity', 'required')]),
    'link.adopt': (True, False, [('project', 'value'), ('user', 'flag'), ('skill', 'required'), ('target', 'required'), ('expect-source', 'required')]),
    'recover': (True, False, [('inspect', 'flag'), ('complete', 'flag'), ('rollback', 'flag')]),
    'doctor': (False, False, [('project', 'value'), ('user', 'flag'), ('all', 'flag'), ('check', 'flag')]),
    'source.status': (False, False, []),
    'source.fetch': (True, True, [('name', 'optional'), ('locked', 'flag'), ('project', 'value'), ('user', 'flag'), ('offline', 'flag')]),
    'source.list': (False, False, []),
    'source.show': (False, False, [('name', 'pos')]),
    'source.inspect': (True, True, [('url', 'pos'), ('ref', 'value'), ('path', 'value')]),
    'source.publish': (True, True, [('name', 'pos'), ('paths', 'repeat'), ('commit', 'flag'), ('push', 'flag'), ('message', 'value')]),
    'source.dev-link': (True, False, [('id', 'pos'), ('project', 'value'), ('user', 'flag'), ('authoring-root', 'value'), ('to-pinned', 'flag')]),
    'source.migrate': (True, False, [('alias', 'value')]),
    'tap.add': (True, False, [('name', 'pos'), ('url', 'pos'), ('ref', 'value'), ('packages', 'value'), ('checkout', 'value')]),
    'tap.remove': (True, False, [('name', 'pos')]),
    'lock': (True, False, [('project', 'value'), ('user', 'flag'), ('refresh', 'flag'), ('skill', 'repeat'), ('allow-ref-rebind', 'flag')]),
    'update': (True, True, [('project', 'value'), ('user', 'flag'), ('all', 'flag'), ('skill', 'repeat'), ('allow-ref-rebind', 'flag')]),
    'migrate': (True, False, [('to-pinned', 'flag'), ('project', 'value'), ('user', 'flag'), ('all', 'flag')]),
    'self.status': (False, False, []),
    'self.install': (True, False, [('bin-dir', 'required')]),
    'self.update': (True, True, []),
}
for action in ('init', 'show', 'set', 'require', 'unrequire', 'set-targets', 'set-agents', 'register', 'unregister'):
    mutates, network, arguments = COMMANDS['project.' + action]
    user_arguments = [(name, shape) for name, shape in arguments if name not in ('project', 'path')]
    if action == 'register':
        user_arguments.append(('user-home', 'value'))
    COMMANDS['user.' + action] = (mutates, network, user_arguments)
GUARDED = {'apply', 'link.adopt', 'update', 'project.set', 'project.require', 'project.unrequire', 'project.set-targets', 'project.register', 'project.unregister'}
GUARDED.update(name.replace('project.', 'user.') for name in tuple(GUARDED) if name.startswith('project.'))
GUARDED.update({'integration.approve', 'integration.revoke'})
GUARDED.update({'integration.enable', 'integration.disable'})
GUARDED.update({'source.migrate', 'tap.add', 'tap.remove'})
GUARDED.update({'skill.import', 'skill.record-adaptation', 'lock', 'migrate', 'source.dev-link', 'source.publish'})
GUARDED.update({'project.set-agents', 'user.set-agents', 'selection-policy.set', 'selection-policy.clear', 'compatibility.override', 'compatibility.clear'})
IMPLEMENTED = set(COMMANDS)
COMMON = [('json', 'flag'), ('debug', 'flag'), ('help', 'flag'), ('version', 'flag'), ('home', 'value')]


def argument(parser, name, shape):
    kwargs = {'default': argparse.SUPPRESS}
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
    parser.add_argument(name if positional else '--' + name, **kwargs)


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
        parser = parent.add_parser(parts[-1], add_help=False, allow_abbrev=False)
        for name, shape in COMMON + arguments:
            argument(parser, name, shape)
        if mutates:
            argument(parser, 'dry-run', 'flag')
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
    return dict(commands=descriptors, schemas=dict(result=1, project=2, user=2, lock=1, machine=2, state=3, pending=3),
                readable_versions=dict(project=[1, 2], user=[1, 2], lock=[1], machine=[1, 2], state=[1, 2, 3], pending=[1, 2, 3]), scopes=['project', 'user'],
                pinned_deployment=True, per_binding_targeting=True, targets=ADAPTERS, python_minimum='3.11', program_root=str(PROGRAM_ROOT))


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
for command in ('plan', 'apply', 'doctor', 'inventory', 'migrate', 'update'):
    CONFLICTS[command] = {key: [other for other in ('project', 'user', 'all') if other != key] for key in ('project', 'user', 'all')}
CONFLICTS['link.adopt'] = {'project': ['user'], 'user': ['project']}
CONFLICTS['source.dev-link'] = {'project': ['user'], 'user': ['project'], 'authoring_root': ['to_pinned'], 'to_pinned': ['authoring_root']}
CONFLICTS['project.set-agents'] = {key: [other for other in ('agents', 'all', 'inherit') if other != key] for key in ('agents', 'all', 'inherit')}
CONFLICTS['user.set-agents'] = CONFLICTS['project.set-agents']
for command in ('compatibility.override', 'compatibility.clear'):
    CONFLICTS[command] = {'project': ['user'], 'user': ['project']}
CONFLICTS['lock'] = {'project': ['user'], 'user': ['project']}
CONFLICTS['source.fetch'] = {'name': ['locked'], 'locked': ['name'], 'project': ['user'], 'user': ['project']}


def validate_arguments(args):
    command = args.command
    for key, conflicts in CONFLICTS.get(command, {}).items():
        if getattr(args, key, None) and any(getattr(args, other, None) for other in conflicts):
            raise MaskError('invocation.invalid', f'{key} conflicts with {", ".join(conflicts)}', 2)
    required_sets = {'project.set-agents': ('agents', 'all', 'inherit'), 'user.set-agents': ('agents', 'all', 'inherit'),
                     'selection-policy.set': ('agent',), 'compatibility.override': ('project', 'user'), 'compatibility.clear': ('project', 'user'),
                     'project.set': ('skill', 'clear'), 'project.set-targets': ('targets', 'inherit'),
                     'user.set': ('skill', 'clear'), 'user.set-targets': ('targets', 'inherit'), 'link.adopt': ('project', 'user'),
                     'config.set': ('target', 'git_timeout'), 'skill.validate': ('id', 'all'),
                     'recover': ('inspect', 'complete', 'rollback')}
    if command == 'compatibility.override' and not any(getattr(args, key, None) for key in ('agent', 'platform', 'architecture')):
        raise MaskError('invocation.invalid', 'An explicit compatibility dimension is required.', 2)
    if command in required_sets and not any(getattr(args, key, None) for key in required_sets[command]):
        raise MaskError('invocation.invalid', 'An explicit operand or mode is required.', 2)


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


def diagnostics(args, output, home):
    config = machine_config(home)
    state = core.state(core.read_json(home / 'state.json', 'state', default=core.empty_state()))
    roots = selected_roots(args, state, all_default=True)
    planned = fs.plan(config, state, roots, home=home)
    fs.public_plan(planned, output)
    issues = list(planned['blockers'])
    if core.kind(home / 'pending.json') != 'missing':
        issues.append(MaskError('recovery.required', 'A pending operation requires inspection.', 8).as_dict())
    try:
        if any(not fs.pinned.is_pinned(core.consumer_records(state).get(str(root))) for root in roots):
            core.checkout(Path(config['source']['root']))
    except MaskError as error:
        issues.append(error.as_dict())
    try:
        fs.pinned.verify_artifacts(planned['intent']['after_state'], [str(root) for root in roots], home)
    except MaskError as error:
        issues.append(error.as_dict())
    drift = bool(planned['would_change'])
    for root in roots:
        if not root.is_dir() or core.consumer_scope(state, root) == 'user':
            continue
        for relative in state['projects'][str(root)]['links']:
            tracked = core.git(root, 'ls-files', '--error-unmatch', '--', relative, optional=True) is not None
            ignored = core.git(root, 'check-ignore', '--quiet', '--no-index', '--', relative, optional=True) is not None
            if tracked or not ignored:
                output['warnings'].append(dict(code='project.link_ignore', message='Managed link is tracked or not ignored by Git.', details=dict(path=str(root / relative), tracked=tracked, ignored=ignored)))
    output['data'].update(healthy=not issues and not drift, issues=issues, filesystem_present=not issues and not drift,
                          host_load='not_verified', symlink_capability='unknown' if os.name == 'nt' else 'available')
    if getattr(args, 'check', False) and (issues or drift):
        core.fail('state.drift', 'Doctor found actionable drift or health failures.', 7)


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
        output['data'] = dict(root=key, manifest=dict(schema_version=1, skills=[]))
        output['would_change'] = True
        if not output['dry_run']:
            core.atomic_text(path, core.text_json(output['data']['manifest']), None)
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
    if record:
        core.registered_root(root, record, scope)
    output['data'] = dict(root=key, scope=scope, manifest_path=str(path), manifest=declaration, registered=record is not None,
                          configured_targets=declaration.get('targets'), effective_targets=declaration.get('targets', config['default_targets'] if config else None))
    if declaration['schema_version'] == 2:
        import mask_pinned
        output['data'].update(mode=(record or {}).get('mode', 'pinned'), reproducible=(record or {}).get('mode') != 'dev-link', fleet_eligible=(record or {}).get('mode') != 'dev-link', requested_targets=mask_pinned.simple_targets(declaration), effective_targets=None)
    if command == 'project.show':
        output['data']['source'] = config['source'] if config else None
        output['data']['ownership'] = record['links'] if record else {}
        if config:
            inspection = fs.plan(config, state, [root], register=[] if record else [key], home=home, user_root=root if scope == 'user' else None)
            output['data']['source'].update(inspection['source'])
            output['data']['expected_links'] = core.consumer_records(inspection['intent']['after_state']).get(key, {}).get('links', {})
            observations = inspection['users'] if scope == 'user' else inspection['projects']
            output['data']['actual_links'] = observations[0]['leaves'] if observations else []
            output['data']['blockers'] = inspection['blockers']
            output['data']['outcomes'] = inspection['outcomes']
            if declaration['schema_version'] == 2:
                output['data']['effective_targets'] = sorted({row['agent'] for row in inspection['outcomes'] if row['status'] in ('selected', 'deployed', 'overridden')})
        output['data']['host_load'] = 'not_verified'
        return
    if config is None:
        core.fail('config.missing', 'Initialize the machine source before this operation.')
    source = Path(config['source']['root'])
    if getattr(args, 'apply', False):
        if record is None and command != 'project.register':
            core.fail(scope + '.not_registered', '--apply requires a registered consumer.', 4)

    if command == 'project.register':
        if record and not getattr(args, 'apply', False):
            return
        core.registration_safe(root, source, home, state, scope)
        if declaration['schema_version'] == 1:
            for identifier in declaration['skills']:
                core.package(source, identifier)
        if declaration['schema_version'] == 2 or scope == 'user' or getattr(args, 'apply', False):
            planned = fs.plan(config, state, [root], register=[key], operation=args.command, home=home,
                              user_root=root if scope == 'user' else None, register_only=not getattr(args, 'apply', False))
            fs.public_plan(planned, output)
            fs.ensure_applicable(planned, getattr(args, 'expect_plan_hash', None))
            if not output['dry_run']:
                fs.execute(planned, home, output)
            return
        after = copy.deepcopy(state)
        after['projects'][key] = core.registry_record(root, declaration, source)
        output['data']['registered'] = True
        output['would_change'] = True
        output['data']['plan_hash'] = core.digest(dict(command=command, root=key, state=state, after=after, config=config))
        if getattr(args, 'expect_plan_hash', output['data']['plan_hash']) != output['data']['plan_hash']:
            core.fail('plan.stale', 'Registry operation changed since preview.', 4)
        if not output['dry_run']:
            core.save_state(home, state, after)
            output.update(changed=True, transaction='committed')
        return
    if declaration['schema_version'] == 2:
        core.fail('selection.command_unsupported', 'Edit v2 selection intent explicitly; legacy string mutation commands do not apply.', 4)
    proposal = copy.deepcopy(declaration)
    if command == 'project.set':
        proposal['skills'] = getattr(args, 'skill', [])
    elif command in ('project.require', 'project.unrequire'):
        for identifier in args.ids:
            core.skill_id(identifier)
        existing = set(proposal['skills'])
        proposal['skills'] = sorted(existing.union(args.ids) if command.endswith('require') and not command.endswith('unrequire') else existing.difference(args.ids))
    elif command == 'project.set-targets':
        if getattr(args, 'inherit', False):
            proposal.pop('targets', None)
        else:
            proposal['targets'] = args.targets
    proposal = core.manifest(proposal)
    for identifier in proposal['skills']:
        core.package(source, identifier)
    if getattr(args, 'apply', False):
        planned = fs.plan(config, state, [root], proposals={key: proposal}, operation=args.command, home=home)
        fs.public_plan(planned, output)
        fs.ensure_applicable(planned, getattr(args, 'expect_plan_hash', None))
        if not output['dry_run']:
            fs.execute(planned, home, output)
        return
    output['data']['manifest'] = proposal
    output['data']['plan_hash'] = core.digest(dict(command=args.command, root=key, manifest_path=str(path), before=declaration, after=proposal, generation=state['generation'], config=config))
    output['would_change'] = proposal != declaration
    if getattr(args, 'expect_plan_hash', output['data']['plan_hash']) != output['data']['plan_hash']:
        core.fail('plan.stale', 'The prospective manifest changed since preview.', 4)
    if proposal != declaration and not output['dry_run']:
        core.atomic_text(path, core.text_json(proposal), declaration_text)
        output.update(changed=True, transaction='committed')


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
    mask_resolve.guard_command(args, home)
    if command in ('inventory', 'skill.where-used'):
        return report_ops.dispatch(args, output, home)
    if command in ('skill.import', 'skill.provenance', 'skill.record-adaptation'):
        import mask_provenance
        return mask_provenance.dispatch(args, output, home)
    if command == 'source.publish':
        return sources_ops.publication(args, output, home)
    if command == 'source.inspect':
        return sources_ops.inspect(args, output, home)
    if command in ('source.list', 'source.show', 'source.migrate', 'tap.add', 'tap.remove') or command == 'source.fetch' and getattr(args, 'name', None):
        return sources_ops.dispatch(args, output, home)
    if command in ('integration.enable', 'integration.disable'):
        return integration_ops.dispatch(args, output, home)
    if command in ('ensure', 'workspace.forget') or command.startswith('integration.'):
        return ensure_ops.dispatch(args, output, home)
    if command == 'init':
        source = Path(args.source).expanduser().resolve()
        core.checkout(source)
        if source == PROGRAM_ROOT or home.is_relative_to(source / 'skills') or source.is_relative_to(home):
            core.fail('config.invalid', 'Source, program and machine state must have distinct non-overlapping write locations.')
        proposal = core.config(dict(schema_version=1, source=dict(root=str(source), remote=getattr(args, 'remote', 'origin'), branch=getattr(args, 'branch', 'main')),
                                    default_targets=getattr(args, 'target', ['claude', 'codex']), git_timeout_seconds=30))
        if core.git(source, 'check-ref-format', '--branch', proposal['source']['branch'], optional=True) is None or core.git(source, 'check-ref-format', 'refs/remotes/' + proposal['source']['remote'] + '/mask-check', optional=True) is None:
            core.fail('config.invalid', 'Invalid Git remote or branch name.')
        core.state(core.read_json(home / 'state.json', 'state', default=core.empty_state()))
        existing = core.read_json(home / 'config.json', default={})
        if existing and core.config(existing)['schema_version'] == 2:
            proposal.update(schema_version=2, legacy_source=existing['legacy_source'], sources=existing['sources'])
        if existing and core.config(existing) != proposal:
            core.fail('config.already_initialized', 'Machine already has a different configuration.', 4)
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
    config = machine_config(home)
    source = Path(config['source']['root'])
    if config['schema_version'] == 2 and command in ('skill.list', 'skill.show', 'skill.validate'):
        return sources_ops.query(args, output, home)
    if command == 'source.status':
        output['data'] = git_ops.status(source, config['source']['remote'], config['source']['branch'], config['git_timeout_seconds'])
    elif command == 'source.fetch':
        remote, branch = config['source']['remote'], config['source']['branch']
        git_ops.checkout_preconditions(source, remote, branch, 'AgentSkills', config['git_timeout_seconds'], clean=False, approved_repository=sources_ops.approved_legacy(config))
        if not output['dry_run']:
            git_ops.fetch(source, remote, branch, config['git_timeout_seconds'], output)
        else:
            output['data'] = dict(fetch_effects=dict(attempted=False, fetched=False), remote_freshness='last_fetched')
    elif command == 'update':
        state = core.state(core.read_json(home / 'state.json', 'state', default=core.empty_state()))
        return git_ops.update(config, state, home, output, getattr(args, 'expect_plan_hash', None))
    elif command == 'config.show':
        output['data'] = dict(config=config, program_root=str(PROGRAM_ROOT), home=str(home))
    elif command == 'config.set':
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
    elif command == 'skill.list' or command == 'skill.validate' and getattr(args, 'all', False):
        entries = core.catalog(source)
        output['data'] = dict(skills=entries, scope='mask-package-v1')
        if command == 'skill.validate' and any(not item['valid'] for item in entries):
            core.fail('skill.invalid', 'One or more packages failed validation.')
    elif command in ('skill.show', 'skill.validate'):
        output['data'] = core.package(source, args.id, getattr(args, 'content', False))
    else:
        core.fail('config.command_unavailable', 'This command is not implemented in this version.')


def dispatch_impl(args, output, leaves):
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
    mutates = COMMANDS[args.command][0] and not output['dry_run'] and not (args.command == 'recover' and getattr(args, 'inspect', False)) and not (args.command == 'ensure' and getattr(args, 'check', False))
    home = machine_home(args)
    if args.command == 'source.fetch' and getattr(args, 'locked', False):
        if core.kind(home / 'pending.json') != 'missing':
            core.fail('recovery.required', 'Recover pending consumer effects before exact preparation.', 8)
        return local_dispatch(args, output, leaves)
    import mask_pinned
    import mask_selection
    if mask_selection.dispatch(args, output, home):
        return
    if args.command in ('migrate', 'update') and mask_pinned.transition_dispatch(args, output, home):
        return
    if args.command == 'source.dev-link':
        return mask_pinned.dev_dispatch(args, output, home)
    preparation = mask_pinned.prepare_dispatch(args, output, home) if mutates else None
    if mutates:
        with core.writer_lock(home):
            if args.command != 'recover' and core.kind(home / 'pending.json') != 'missing':
                core.fail('recovery.required', 'Inspect and recover the pending operation first.', 8)
            mask_pinned.recheck_preparation(preparation, home)
            try:
                local_dispatch(args, output, leaves)
            finally:
                if preparation is not None:
                    output['data']['preparation'] = preparation['effects']
                    output['data']['network'] = 'locked_fetch' if any(item['effects'].get('network_attempted') for item in preparation['effects']) else 'none'
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


def main(argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    argv = list(sys.argv[1:] if argv is None else argv)
    before_separator = argv[:argv.index('--')] if '--' in argv else argv
    machine = '--json' in before_separator
    output = result()
    exit_code = 0
    try:
        parser, leaves = make_parser()
        if '--help' in before_separator or '--version' in before_separator:
            output['command'] = 'help' if '--help' in before_separator else 'version'
            output['data'] = {'version': VERSION}
            if output['command'] == 'help':
                words = [item for item in before_separator if not item.startswith('-')]
                selected = '.'.join(words[:2])
                output['data']['help'] = leaves.get(selected, leaves.get(words[0] if words else '', parser)).format_help()
        else:
            args = parser.parse_args(argv)
            if not hasattr(args, 'command'):
                raise MaskError('invocation.invalid', 'A complete command is required.', 2)
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
        print(f"{output['error']['code']}: {output['error']['message']}", file=sys.stderr)
    else:
        print(output['data'].get('help', json.dumps(output, ensure_ascii=False, indent=2)))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
