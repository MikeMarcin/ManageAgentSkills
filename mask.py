#!/usr/bin/env python3
"""MASK — Manage Agent SKills. Python 3.11+, standard library and Git."""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import sys

VERSION = '0.1.0'
PROTOCOL_VERSION = 1
ADAPTERS = {'claude': '.claude/skills', 'codex': '.agents/skills'}
PROGRAM_ROOT = Path(__file__).resolve().parent


import mask_core as core
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
    'skill.validate': (False, False, [('id', 'optional'), ('all', 'flag')]),
    'project.init': (True, False, [('project', 'value')]),
    'project.show': (False, False, [('project', 'value')]),
    'project.set': (True, False, [('project', 'value'), ('skill', 'repeat'), ('clear', 'flag'), ('apply', 'flag')]),
    'project.require': (True, False, [('project', 'value'), ('ids', 'many'), ('apply', 'flag')]),
    'project.unrequire': (True, False, [('project', 'value'), ('ids', 'many'), ('apply', 'flag')]),
    'project.set-targets': (True, False, [('project', 'value'), ('targets', 'some'), ('inherit', 'flag'), ('apply', 'flag')]),
    'project.register': (True, False, [('project', 'value'), ('path', 'optional'), ('apply', 'flag')]),
    'project.unregister': (True, False, [('project', 'value'), ('path', 'optional'), ('keep-links', 'flag')]),
    'project.list': (False, False, []),
    'plan': (False, False, [('project', 'value'), ('all', 'flag')]),
    'apply': (True, False, [('project', 'value'), ('all', 'flag')]),
    'link.adopt': (True, False, [('project', 'required'), ('skill', 'required'), ('target', 'required'), ('expect-source', 'required')]),
    'recover': (True, False, [('inspect', 'flag'), ('complete', 'flag'), ('rollback', 'flag')]),
    'doctor': (False, False, [('project', 'value'), ('all', 'flag'), ('check', 'flag')]),
    'source.status': (False, False, []),
    'source.fetch': (True, True, []),
    'update': (True, True, []),
    'self.status': (False, False, []),
    'self.install': (True, False, [('bin-dir', 'required')]),
    'self.update': (True, True, []),
}
GUARDED = {'apply', 'link.adopt', 'update', 'project.set', 'project.require', 'project.unrequire', 'project.set-targets', 'project.register', 'project.unregister'}
IMPLEMENTED = {'capabilities', 'init', 'config.show', 'config.set', 'skill.list', 'skill.show', 'skill.validate', *(name for name in COMMANDS if name.startswith('project.'))}
COMMON = [('json', 'flag'), ('debug', 'flag'), ('help', 'flag'), ('version', 'flag'), ('home', 'value')]


def argument(parser, name, shape):
    kwargs = {'default': argparse.SUPPRESS}
    positional = shape in {'pos', 'optional', 'many', 'some'}
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
    return dict(commands=descriptors, schemas=dict(result=1, project=1, machine=1, state=1),
                targets=ADAPTERS, python_minimum='3.11', program_root=str(PROGRAM_ROOT))


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


def validate_arguments(args):
    command = args.command
    for key, conflicts in CONFLICTS.get(command, {}).items():
        if getattr(args, key, None) and any(getattr(args, other, None) for other in conflicts):
            raise MaskError('invocation.invalid', f'{key} conflicts with {", ".join(conflicts)}', 2)
    required_sets = {'project.set': ('skill', 'clear'), 'project.set-targets': ('targets', 'inherit'),
                     'config.set': ('target', 'git_timeout'), 'skill.validate': ('id', 'all'),
                     'recover': ('inspect', 'complete', 'rollback')}
    if command in required_sets and not any(getattr(args, key, None) for key in required_sets[command]):
        raise MaskError('invocation.invalid', 'An explicit operand or mode is required.', 2)


def machine_home(args):
    return Path(getattr(args, 'home', os.environ.get('MASK_HOME', str(Path.home() / '.mask')))).expanduser().resolve()


def machine_config(home):
    return core.config(core.read_json(home / 'config.json'))


def project_dispatch(args, output, home):
    command = args.command
    state = core.state(core.read_json(home / 'state.json', 'state', default=core.empty_state()))
    config_raw = core.read_json(home / 'config.json', default={})
    config = core.config(config_raw) if config_raw else None
    if command == 'project.list':
        output['data'] = dict(projects=[dict(record, available=Path(root).is_dir()) for root, record in sorted(state['projects'].items())])
        return
    selection = getattr(args, 'project', getattr(args, 'path', None))
    if command == 'project.unregister' and getattr(args, 'keep_links', False) and selection is not None:
        root = Path(selection).expanduser().resolve()
    else:
        root = core.project_root(selection, initializing=command == 'project.init')
    path = root / '.mask.json'
    key = str(root)
    record = state['projects'].get(key)
    if command == 'project.init':
        if core.kind(path) != 'missing':
            declaration = core.project_manifest(root)
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
        if record['links'] and not keep:
            core.fail('config.command_unavailable', 'Owned-link removal requires the reconciliation engine.')
        if not keep:
            core.registered_root(root, record)
        after = copy.deepcopy(state)
        del after['projects'][key]
        output['data'] = dict(root=key, registered=False, abandoned_paths=[str(root / rel) for rel in record['links']] if keep else [])
        output['would_change'] = True
        if not output['dry_run']:
            core.save_state(home, state, after)
            output.update(changed=True, transaction='committed')
        return
    declaration = core.project_manifest(root)
    if record:
        core.registered_root(root, record)
    output['data'] = dict(root=key, manifest=declaration, registered=record is not None,
                          configured_targets=declaration.get('targets'), effective_targets=declaration.get('targets', config['default_targets'] if config else None))
    if command == 'project.show':
        output['data']['source'] = config['source'] if config else None
        output['data']['ownership'] = record['links'] if record else {}
        output['data']['host_load'] = 'not_verified'
        return
    if config is None:
        core.fail('config.missing', 'Initialize the machine source before this operation.')
    source = Path(config['source']['root'])
    if getattr(args, 'apply', False):
        if record is None and command != 'project.register':
            core.fail('project.not_registered', '--apply requires a registered project.', 4)
        core.fail('config.command_unavailable', 'The registered-project reconciler is not implemented yet.')
    if command == 'project.register':
        if record:
            return
        for adapter in ADAPTERS.values():
            destination = root / adapter
            if source.is_relative_to(destination) or home.is_relative_to(destination) or destination.is_relative_to(source / 'skills') or root == home:
                core.fail('config.invalid', 'Managed source, state and destination locations overlap.')
        for identifier in declaration['skills']:
            core.package(source, identifier)
        after = copy.deepcopy(state)
        after['projects'][key] = core.registry_record(root, declaration, source)
        output['data']['registered'] = True
        output['would_change'] = True
        if not output['dry_run']:
            core.save_state(home, state, after)
            output.update(changed=True, transaction='committed')
        return
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
    output['data']['manifest'] = proposal
    output['data']['plan_hash'] = core.digest(dict(command=command, root=key, before=declaration, after=proposal, generation=state['generation'], config=config))
    output['would_change'] = proposal != declaration
    if getattr(args, 'expect_plan_hash', output['data']['plan_hash']) != output['data']['plan_hash']:
        core.fail('plan.stale', 'The prospective manifest changed since preview.', 4)
    if proposal != declaration and not output['dry_run']:
        core.atomic_text(path, core.text_json(proposal), core.read_text(path, 'manifest'))
        output.update(changed=True, transaction='committed')


def local_dispatch(args, output, leaves):
    command = args.command
    home = machine_home(args)
    if command == 'capabilities':
        output['data'] = capabilities(leaves)
        return
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
    if command.startswith('project.'):
        return project_dispatch(args, output, home)
    config = machine_config(home)
    source = Path(config['source']['root'])
    if command == 'config.show':
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


def dispatch(args, output, leaves):
    if args.command not in IMPLEMENTED:
        core.fail('config.command_unavailable', 'This command is not implemented in this version.')
    mutates = COMMANDS[args.command][0] and not output['dry_run']
    home = machine_home(args)
    if mutates:
        with core.writer_lock(home):
            if core.kind(home / 'pending.json') != 'missing':
                core.fail('recovery.required', 'Inspect and recover the pending operation first.', 8)
            local_dispatch(args, output, leaves)
    else:
        local_dispatch(args, output, leaves)
    if output['dry_run'] and output['would_change']:
        output['transaction'] = 'not_started'
    for action in output['actions']:
        if output['changed']:
            action['status'] = 'applied'


def main(argv=None):
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
        output.update(ok=False, error=error.as_dict(), transaction='not_started')
        exit_code = error.exit_code
    except KeyboardInterrupt:
        error = MaskError('invocation.interrupted', 'Interrupted by user.', 130)
        output.update(ok=False, error=error.as_dict(), transaction='not_started')
        exit_code = 130
    except OSError:
        error = MaskError('filesystem.failed', 'A filesystem operation failed.', 5)
        output.update(ok=False, error=error.as_dict(), transaction='not_started')
        exit_code = 5
    except Exception:
        error = MaskError('internal.invariant', 'An internal invariant failed.', 10)
        output.update(ok=False, error=error.as_dict(), transaction='not_started')
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
