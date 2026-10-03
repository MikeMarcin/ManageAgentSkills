"""The public v2 command surface. Legacy operation names remain private journal IDs."""
from __future__ import annotations

import argparse
from contextlib import nullcontext
import os
from pathlib import Path
import sys
import time

import mask_core as c

SCOPES = [('project', 'value'), ('user', 'flag'), ('all', 'flag')]
SINGLE = SCOPES[:2]
OFFLINE = [('offline', 'flag')]
REFRESH = OFFLINE + [('no-update', 'flag')]
COMMANDS = {
    'capabilities': (False, False, []),
    'tap': (True, False, [('name', 'optional'), ('url', 'optional'), ('ref', 'value'), ('packages', 'value'), ('checkout', 'value'), ('autocrlf', 'flag'), ('pin-transport', 'flag')]),
    'untap': (True, False, [('name', 'pos')]),
    'update': (True, True, []),
    'cleanup': (True, False, []),
    'search': (False, False, [('query', 'optional')]),
    'info': (False, False, [('id', 'pos'), ('content', 'flag')]),
    'bundle.list': (False, False, [('source', 'value')]),
    'bundle.show': (False, False, [('bundle', 'pos')]),
    'bundle.install': (True, True, [('bundle', 'pos')] + SINGLE + [('replace', 'flag')] + OFFLINE),
    'bundle.uninstall': (True, False, [('bundle', 'pos')] + SINGLE + OFFLINE),
    'bundle.upgrade': (True, True, [('bundle', 'pos')] + SINGLE + [('allow-ref-rebind', 'flag')] + OFFLINE),
    'register': (True, True, [('path', 'optional')] + SINGLE + OFFLINE),
    'unregister': (True, False, [('path', 'optional')] + SINGLE + [('keep-links', 'flag')]),
    'install': (True, True, [('ids', 'many')] + SINGLE + [('agent', 'repeat')] + REFRESH),
    'uninstall': (True, False, [('ids', 'many')] + SINGLE),
    'list': (False, False, SCOPES + [('include-unmanaged', 'flag'), ('limit', 'int'), ('offset', 'int')]),
    'upgrade': (True, True, [('ids', 'some')] + SCOPES + [('allow-ref-rebind', 'flag')] + REFRESH),
    'pin': (True, False, [('id', 'optional')] + SCOPES),
    'unpin': (True, False, [('id', 'optional')] + SCOPES),
    'repair': (True, True, SCOPES + OFFLINE),
    'status': (False, False, SCOPES + [('check', 'flag'), ('workflow-profile', 'repeat')]),
    'integration.run': (True, True, SINGLE + [('event', 'value'), ('check', 'flag'), ('offline', 'flag'), ('workflow-profile', 'repeat')]),
}
# Advanced operations retain their validated engines but live under the right object.
RENAMES = {'uninstall': 'remove', 'status': 'doctor', 'search': 'skill.list', 'info': 'skill.show',
           'untap': 'tap.remove', 'skill.dev-link': 'source.dev-link', 'integration.run': 'ensure',
           'tap.migrate': 'doctor'}
for action in ('fetch', 'show', 'inspect', 'repair-cache', 'publish'):
    RENAMES['tap.' + action] = 'source.' + action
KEEP = ('config.show', 'config.set', 'skill.where-used', 'skill.validate', 'skill.import', 'skill.provenance',
        'skill.record-adaptation', 'project.set-targets', 'project.set-agents', 'user.set-targets', 'user.set-agents',
        'selection-policy.set', 'selection-policy.clear', 'compatibility.override', 'compatibility.clear',
        'integration.approve', 'integration.revoke', 'integration.inspect', 'integration.enable', 'integration.disable',
        'launch', 'workspace.forget', 'link.adopt', 'recover', 'tap.transport', 'lock', 'self.status', 'self.install', 'self.uninstall')

HELP = {
    'tap': ('Advanced tap commands: fetch, show, inspect, transport, repair-cache, migrate and publish. List taps, or approve NAME URL as a shared skill source. The current checkout does not affect taps. A tap keeps exact bytes unless --autocrlf opts in to core.autocrlf=true.', 'mask tap\nmask tap agentskills https://github.com/MikeMarcin/AgentSkills.git'),
    'untap': ('Remove an unused tap. Cached files remain until cleanup.', 'mask untap NAME'),
    'register': ('Register this checkout and prepare its declared skills, preserving locked versions. PATH selects another checkout; --user selects personal skills.', 'mask register\nmask register /path/to/worktree'),
    'unregister': ('Stop managing this checkout and remove unchanged managed deployment. Preserve its declaration and lock.', 'mask unregister\nmask unregister --user'),
    'install': ('Add skills to this checkout and complete their setup. --user selects personal skills. Review any scripts or replacements before consumer files change.', 'mask install implement-rfc\nmask install implement-rfc --user'),
    'uninstall': ('Remove selected skills from this checkout and its managed deployment. Shared cached versions remain until cleanup.', 'mask uninstall implement-rfc\nmask uninstall implement-rfc --user'),
    'list': ('List selected skills and versions in this checkout. --user selects personal skills; --all lists every registered checkout and personal skills.', 'mask list\nmask list --all'),
    'upgrade': ('Upgrade this checkout, including installed bundle definitions, and make its skills ready. --user selects personal skills; --all upgrades every registered checkout plus personal skills. IDs select package versions only, keeping bundle definitions frozen.', 'mask upgrade\nmask upgrade --user\nmask upgrade --all'),
    'repair': ('Restore this checkout to its declared, pinned state, including required setup. Interrupted setup is reviewed first at its recorded location, even in another checkout. --user selects personal skills; --all restores every registered installation.', 'mask repair\nmask repair --all'),
    'recover': ('Inspect an interrupted operation. Bare recover changes nothing. Advanced modes complete validated effects or roll back journaled changes without rerunning package scripts; repair offers guided recovery.', 'mask recover\nmask repair\nmask recover --complete --dry-run\nmask recover --rollback --dry-run'),
    'pin': ('Hold SKILL at its installed version. --all holds every skill in this checkout; --user selects personal skills. Upgrade still completes readiness.', 'mask pin implement-rfc\nmask pin --all --user'),
    'unpin': ('Release a version hold without upgrading immediately. --all releases every skill in this checkout; --user selects personal skills.', 'mask unpin implement-rfc\nmask unpin --all --user'),
    'status': ('Inspect readiness in this checkout without changing files. --user selects personal skills; --all checks every registered installation. --check exits nonzero for problems.', 'mask status\nmask status --all --check'),
    'search': ('Search the fetched catalogs of your shared taps by skill name or description. No query lists all available skills.', 'mask search review'),
    'info': ('Inspect one available skill, its source and declared workflow. This reads the shared tap catalog.', 'mask info implement-rfc\nmask info implement-rfc --content'),
    'bundle.list': ('List flat bundles in fetched approved taps. Unfetched catalogs are reported; browsing never fetches.', 'mask bundle list\nmask bundle list --source agentskills'),
    'bundle.show': ('Show one fetched bundle definition, its exact source revision and digest.', 'mask bundle show agentskills/rfc'),
    'bundle.install': ('Expand a bundle and complete required setup. Existing manual targets, exact locks and other contributions remain. --replace explicitly refreshes only this named local bundle contribution, with exclusive removals shown.', 'mask bundle install agentskills/rfc --dry-run\nmask bundle install agentskills/rfc --approve-plan HASH'),
    'bundle.uninstall': ('Remove only the named frozen local contribution, without fetching a source definition. Preserve manual, overlapping, held and locally modified skills and their exact locks; unchanged exclusive members are removed. An absent contribution is a no-op.', 'mask bundle uninstall agentskills/rfc --dry-run\nmask bundle uninstall agentskills/rfc --approve-plan HASH'),
    'bundle.upgrade': ('Review the latest definition and newer unheld member versions together. Preserve manual/overlapping membership, exact selectors, holds and local edits; incompatible constraints refuse before changes. Live execution fetches approved member taps; previews and approved plans use cached revisions.', 'mask bundle upgrade agentskills/rfc --dry-run\nmask bundle upgrade agentskills/rfc --approve-plan HASH'),
    'cleanup': ('Preview and delete verified unused MASK storage and disposable backups. Referenced content, active locks, recovery data and unknown files are preserved.', 'mask cleanup --dry-run\nmask cleanup --approve-plan HASH'),
    'integration.run': ('Run an approved startup readiness event. This entrypoint never grants consent or runs package setup.', None),
}


def definitions(engine):
    commands = dict(COMMANDS)
    for name in KEEP:
        mutates, network, arguments = engine[name]
        commands[name] = (mutates, network, [(key, shape) for key, shape in arguments if key != 'apply'])
    for public, internal in RENAMES.items():
        if public not in commands:
            commands[public] = engine[internal] if public != 'tap.migrate' else (True, False, [])
    return commands


def guarded(command, engine):
    return command in ('register', 'repair', 'pin', 'unpin', 'cleanup', 'unregister', 'tap', 'bundle.install', 'bundle.uninstall', 'bundle.upgrade') or RENAMES.get(command, command) in engine.GUARDED


def parser(engine, common, parser_type, add_argument, help_entries):
    import mask
    root = parser_type(prog='mask', add_help=False, allow_abbrev=False)
    for name, shape in common:
        add_argument(root, name, shape)
    sub = root.add_subparsers(dest='group', parser_class=parser_type)
    groups, leaves = {}, {}
    for command, (mutates, _, arguments) in definitions(engine).items():
        parts = command.split('.')
        # tap also has a useful bare form; normalize its advanced subcommands before parsing.
        if len(parts) == 2 and parts[0] != 'tap':
            if parts[0] not in groups:
                group = sub.add_parser(parts[0], add_help=False, allow_abbrev=False)
                for name, shape in common:
                    add_argument(group, name, shape)
                groups[parts[0]] = group.add_subparsers(dest='subcommand', parser_class=parser_type)
            parent, name = groups[parts[0]], parts[-1]
        else:
            parent, name = sub, command
        description, examples = HELP.get(command, help_entries.get(RENAMES.get(command, command), (None, None)))
        for old, new in (('mask source dev-link', 'mask skill dev-link'), ('mask source ', 'mask tap '), ('source fetch', 'tap fetch'), ('mask project register', 'mask register'), ('mask user register', 'mask register --user')):
            description = description.replace(old, new) if description else description
            examples = examples.replace(old, new) if examples else examples
        leaf = parent.add_parser(name, add_help=False, allow_abbrev=False, description=description,
                                epilog='Examples:\n  ' + examples.replace('\n', '\n  ') if examples else None,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
        for name, shape in common + arguments:
            add_argument(leaf, name, shape)
        if command in ('pin', 'unpin'):
            next(action for action in leaf._actions if action.dest == 'all').help = 'Select every skill in the chosen checkout or personal scope'
        if mutates:
            add_argument(leaf, 'dry-run', 'flag')
        if guarded(command, mask):
            add_argument(leaf, 'approve-plan', 'value')
        leaf.set_defaults(command=command)
        leaves[command] = leaf
    return root, leaves


def normalize(argv):
    words = list(argv)
    for index, word in enumerate(words):
        if word == '--':
            break
        if word.startswith('tap.'):
            c.fail('invocation.invalid', 'Use mask tap SUBCOMMAND.', 2)
        if word == 'tap' and index + 1 < len(words) and words[index + 1] in ('fetch', 'show', 'inspect', 'repair-cache', 'publish', 'transport', 'migrate'):
            words[index:index + 2] = ['tap.' + words[index + 1]]
            break
    return words


def validate(args):
    if args.command == 'recover' and not any(getattr(args, mode, False) for mode in ('inspect', 'complete', 'rollback')):
        args.inspect = True
    scope = [name for name in ('project', 'user', 'all') if getattr(args, name, False)]
    if args.command in ('pin', 'unpin'):
        scope = [name for name in scope if name != 'all']
        if bool(getattr(args, 'id', None)) == bool(getattr(args, 'all', False)):
            c.fail('invocation.invalid', 'Choose SKILL or --all (all skills in this checkout, or --user).', 2)
    if len(scope) > 1 or getattr(args, 'path', None) and args.command in ('register', 'unregister') and scope:
        c.fail('invocation.invalid', 'Choose one target: this checkout, --project PATH, --user, or --all.', 2)
    if args.command == 'tap' and bool(getattr(args, 'name', None)) != bool(getattr(args, 'url', None)):
        c.fail('invocation.invalid', 'Use mask tap to list sources, or mask tap NAME URL to add one.', 2)
    if args.command in ('register', 'unregister') and getattr(args, 'path', None):
        args.project = args.path
        del args.path
    if hasattr(args, 'approve_plan'):
        if not isinstance(args.approve_plan, str) or not args.approve_plan.startswith('sha256:') or len(args.approve_plan) != 71:
            c.fail('invocation.invalid', '--approve-plan requires the full SHA-256 hash from a preview.', 2)
        args.expect_plan_hash = args.approve_plan
    args.public_command = args.command


def auto_refresh(args, output, home, leaves):
    import mask
    if args.command not in ('install', 'upgrade') or output['dry_run'] or any(getattr(args, key, False) for key in ('no_update', 'offline', 'expect_plan_hash')):
        return
    recorded = c.read_json(home / 'refresh.json', default={})
    last = recorded.get('completed_at', 0)
    if isinstance(last, (int, float)) and 0 <= time.time() - last < 86400:
        return
    refresh_args = argparse.Namespace(command='update', home=str(home), json=getattr(args, 'json', False))
    refresh = mask.result('update')
    try:
        mask.dispatch(refresh_args, refresh, leaves)
    except c.MaskError as error:
        if not any(row.get('ok') is False for row in refresh['data'].get('fetches', {}).values()):
            raise
        # An unrelated unavailable tap must not block the selected checkout. The
        # task's own fetch phase reports failures for its actual consumers.
        refresh['data']['error'] = error.as_dict()
        output['warnings'].append(dict(code='update.incomplete', message='Catalog refresh was incomplete; continuing with the selected task.'))
    else:
        args.catalog_refreshed = True
        c.atomic_text(home / 'refresh.json', c.text_json(dict(completed_at=time.time())), c.read_text(home / 'refresh.json', missing=True))
    output['data']['refresh'] = refresh['data']
    if refresh['data'].get('program', {}).get('status') == 'updated':
        # Do not plan a consumer task in modules loaded before the program update.
        os.execv(sys.executable, [sys.executable, '-B', str(mask.PROGRAM_ROOT / 'mask.py'), *args.invocation_argv, '--no-update'])


def dispatch(args, output, leaves):
    import mask
    import mask_lifecycle
    import mask_store
    validate(args)
    public = args.command
    home = mask.machine_home(args)
    if public in ('install', 'upgrade'):
        state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
        if public == 'upgrade':
            mask.selected_roots(args, state)
        else:
            import mask_task
            mask_task.consumer(args, state, home, creating=True)
    refresh = None
    mutates = definitions(mask.COMMANDS)[public][0] and not output['dry_run']
    if public == 'tap' and not getattr(args, 'name', None):
        mutates = False
    if public == 'integration.run' and getattr(args, 'check', False):
        mutates = False
    if public == 'recover' and getattr(args, 'inspect', False):
        mutates = False
    if public == 'launch':
        mutates = False  # The readiness phase owns this lock; the host must not hold it.
    if public == 'integration.run':
        args.event = getattr(args, 'event', 'startup')
        if args.event == 'manual':
            c.fail('invocation.invalid', 'Use register or repair for a manual readiness task.', 2)
    # This lock spans resolution and preparation as well as activation. Cleanup
    # cannot remove content acquired by an operation that has not registered it yet.
    with (c.writer_lock(home, name='lifecycle.lock') if mutates else nullcontext()), \
            (mask_store.observational() if not mutates or public == 'cleanup' else nullcontext()):
        try:
            auto_refresh(args, output, home, leaves)
            refresh = output['data'].get('refresh')
            if public in ('pin', 'unpin'):
                import mask_pin
                return mask_pin.dispatch(args, output, home)
            if public in ('register', 'repair'):
                if public == 'repair':
                    import mask_repair
                    if mask_repair.resume_pending(args, output, home):
                        return
                return mask_lifecycle.restore(args, output, home, registering=public == 'register')
            if public == 'cleanup':
                import mask_cleanup
                return mask_cleanup.dispatch(args, output, home)
            if public == 'capabilities':
                return capabilities(output, leaves, mask)
            if public.startswith('bundle.'):
                import mask_bundles
                return mask_bundles.dispatch(args, output, home)
            if public == 'list' and getattr(args, 'all', False):
                args.command = 'inventory'
            elif public == 'tap':
                args.command = 'tap.add' if getattr(args, 'name', None) else 'source.list'
            elif public == 'unregister':
                args.command = 'user.unregister' if getattr(args, 'user', False) else 'project.unregister'
            else:
                args.command = RENAMES.get(public, public)
            if public == 'upgrade':
                ids = getattr(args, 'ids', [])
                if ids:
                    state = c.state(c.read_json(home / 'state.json', 'state', default=c.empty_state()))
                    roots = mask.selected_roots(args, state)
                    declared = {row['source'] + '/' + row['id'] for root in roots for row in
                                c.selection_manifest(c.read_json(c.declaration_path(root, c.consumer_scope(state, root), home), 'manifest'))['skills']}
                    chosen = []
                    for name in ids:
                        matches = [key for key in declared if key == name or '/' not in name and key.split('/', 1)[1] == name]
                        if len(matches) != 1:
                            c.fail('skill.ambiguous' if matches else 'skill.unknown', 'Select a unique declared skill; qualify it as TAP/ID.', 4, skill=name, choices=matches)
                        chosen.extend(matches)
                    args.skill = chosen
            if public == 'tap.migrate':
                args.migrate = True
            if public.endswith(('.set-targets', '.set-agents')):
                args.apply = True
            mask.validate_arguments(args)
            mask.dispatch(args, output, leaves)
            if public == 'info':
                import mask_packages
                import mask_workflow
                import mask_sources
                data = output['data']
                config = mask.machine_config(home)
                entry = mask_sources.selected(config, data['source'])
                payload = mask_packages.validate(mask_sources.cached(home, data['source'], entry), data['commit'], data['path'], data['id'])
                view = mask_workflow.PackageView(payload=payload)
                data['workflow'] = {}
                for scope in ('project', 'user'):
                    descriptor = mask_workflow.descriptor(view, data['id'], scope)
                    if descriptor:
                        data['workflow'][scope] = dict(inputs=descriptor['inputs'], roles=list(descriptor['roles'].values()), setup=descriptor['setup'])
            if public == 'search' and getattr(args, 'query', None):
                query = args.query.casefold()
                output['data']['skills'] = [row for row in output['data']['skills'] if query in (row['coordinate'] + ' ' + row.get('description', '')).casefold()]
            if public == 'update' and not output['dry_run']:
                c.atomic_text(home / 'refresh.json', c.text_json(dict(completed_at=time.time())), c.read_text(home / 'refresh.json', missing=True))
        finally:
            if public in ('register', 'repair', 'pin', 'unpin'):
                import mask_pinned
                mask_pinned.merge_preparation(output, completed=sys.exc_info()[0] is None)
            args.command = public
            output['command'] = public
            if refresh:
                output['data']['refresh'] = refresh
            scopes = output['data'].get('workflow_readiness') or output['data'].get('consumers') or []
            output['data']['scopes'] = [dict(root=row['root'], scope=row['scope']) for row in scopes]
            if not scopes and output['data'].get('root'):
                output['data']['scopes'] = [dict(root=output['data']['root'], scope=output['data'].get('scope', 'user' if getattr(args, 'user', False) else 'project'))]


def capabilities(output, leaves, mask):
    descriptors = []
    for name, (mutates, network, _) in definitions(mask.COMMANDS).items():
        arguments = [dict(name=a.dest, flags=a.option_strings, required=a.required,
                          repeatable=isinstance(a, argparse._AppendAction) or a.nargs in ('+', '*'), nargs=a.nargs,
                          type='integer' if a.type is int else 'boolean' if isinstance(a, argparse._StoreTrueAction) else 'string')
                     for a in leaves[name]._actions]
        descriptors.append(dict(name=name, implemented=True, arguments=arguments, effect='managed_mutation' if mutates else 'observational',
                                network=network, dry_run=mutates, plan_guard=guarded(name, mask)))
    output['data'] = dict(commands=descriptors, schemas=dict(result=2, project=2, user=2, lock=1, machine=3, state=3, pending=3),
                         readable_versions=dict(project=[2], user=[2], lock=[1], machine=[3], state=[1,2,3], pending=[1,2,3]),
                         scopes=['project', 'user'], default_scope='current_checkout', aggregate_scope='all_registered',
                         deployment_model='taps', line_endings=dict(default='exact', values=['exact', 'autocrlf'], opt_in='tap --autocrlf'), pinned_deployment=True, per_binding_targeting=True, targets=mask.ADAPTERS,
                         bundles=dict(flat=True, source_index=1, contributions='explicit_local', upgrade='definition_and_unheld_versions', ordinary_upgrade='installed_receipts', uninstall='named_local_contribution', recursive=False),
                         adapter_contracts=mask.adapters.capabilities(), python_minimum='3.11', program_root=str(mask.PROGRAM_ROOT),
                         workflow=dict(readiness='workflow_readiness_v1', requirement_profiles='workflow_requirement_profiles_v1',
                                       profile_selection='status --check --workflow-profile SKILL=PROFILE', scope_contracts=['project','user'],
                                       setup_request_scope=True, native_roles=True, staged_setup=True, repair_with_backups=True,
                                       setup_entrypoints=['register','install','repair','upgrade','bundle.install','bundle.upgrade','bundle.uninstall'], paths=mask.workflow.paths(),
                                       retired_paths=True, compatible_locks=True, entrypoints=['register','install','uninstall','repair','upgrade','status','launch','bundle.install','bundle.upgrade','bundle.uninstall'], host_load='not_verified'))


def help_text(parser, leaves, argv, mask):
    words = [word for word in argv if not word.startswith('-')]
    key = '.'.join(words[:2])
    if key in leaves:
        return leaves[key].format_help().replace('mask tap.', 'mask tap ')
    if words and words[0] in leaves:
        return leaves[words[0]].format_help().replace('mask tap.', 'mask tap ')
    commands = definitions(mask.COMMANDS)
    if words:
        members = [name for name in commands if name.startswith(words[0] + '.')]
        if members:
            return '\n'.join(['Commands:'] + ['  mask ' + name.replace('.', ' ') for name in members]) + '\n'
    return f'''MASK {mask.VERSION} — manage agent skills

Shared resources (independent of your checkout):
  tap / untap             List, add or remove shared skill sources
  update                  Refresh MASK and your tap catalogs
  cleanup                 Delete verified unused storage and backups

Catalog browsing (your shared taps):
  search [QUERY]          Find available skills
  info SKILL              Inspect an available skill and its workflow
  bundle list / show      Inspect flat named bundles in fetched taps
  bundle install         Add a frozen local bundle contribution
  bundle upgrade         Explicitly adopt changed bundle membership
  bundle uninstall       Remove that contribution; preserve other selections

This checkout:
  register [PATH]         Start managing a checkout and make it ready
  unregister [PATH]       Stop managing a checkout; keep its declarations
  install SKILL ...       Add skills and complete their setup
  uninstall SKILL ...     Remove skills from this checkout
  list                    Show selected skills and versions
  pin / unpin SKILL       Hold or release an installed version
                          --all selects every skill in this checkout (or --user)
  upgrade [SKILL ...]     Upgrade this checkout and make it ready
  repair                  Recover interrupted setup, or restore pinned readiness
  status                  Explain readiness and problems (also bare mask)

Interrupted setup: repair first reviews recovery at its recorded location.

Targets:
  --user                  Personal skills instead of this checkout
  --all                   Every registered checkout plus personal skills
                          Available on upgrade, repair, status and list

Review:
  --dry-run               Preview without fetching, writing or running setup
  --approve-plan HASH     Apply the exact reviewed task without prompting
  --json                  Structured output; never prompts

Run 'mask COMMAND --help' for details. Advanced groups: config, skill, project,
user, integration, selection-policy, compatibility, self.
Advanced recovery: recover (inspect), recover --complete, recover --rollback.
'''
