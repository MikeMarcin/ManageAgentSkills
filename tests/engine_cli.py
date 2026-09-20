"""Test-only subprocess harness for private journal/reconciliation operations.

The public CLI is mask.py and is covered by test_cli_v2/protocol/readme journeys.
This harness exposes internal operation IDs to construct and inspect intermediate
states for recovery, artifact, integration and ownership regression tests. It is
not a supported CLI, compatibility alias, or deployment entrypoint.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mask
from mask import *
import argparse
import json
import os
import textwrap

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


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):  # Human text and JSON are UTF-8 on every OS, piped or not.
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    argv = list(sys.argv[1:] if argv is None else argv)
    core.FROZEN.clear()  # Object-addressed Git answers are reused within one invocation only.
    sources_ops.ACTIVE_FORGES.clear()
    sources_ops.ACTIVE_FORGES.update(sources_ops.FORGE_HOSTS)  # A machine's forge_hosts opt-in lasts one invocation.
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
            if args.command in ('upgrade', 'doctor') and not any(getattr(args, key, False) for key in ('project', 'user', 'all')):
                args.all = True
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
    except OSError as cause:
        details = {key: value for key, value in dict(errno=cause.errno, filename=cause.filename,
                                                    filename2=cause.filename2).items() if value is not None}
        error = MaskError('filesystem.failed', 'A filesystem operation failed.', 5, details=details)
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
