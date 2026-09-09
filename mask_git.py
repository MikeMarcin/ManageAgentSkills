"""Explicit fetch and frozen-candidate updates; no implicit Git reset or push."""
from __future__ import annotations

import copy
from pathlib import Path
import re

import mask_core as c
import mask_fs as fs
import mask_sources as sources


def status(root, remote='origin', branch='main', timeout=30):
    c.checkout(root)
    head = c.git(root, 'rev-parse', 'HEAD', optional=True, timeout=timeout)
    current_branch = c.git(root, 'symbolic-ref', '--short', 'HEAD', optional=True, timeout=timeout)
    dirty = bool(c.git(root, 'status', '--porcelain', '--untracked-files=all', timeout=timeout))
    candidate = c.git(root, 'rev-parse', '--verify', f'refs/remotes/{remote}/{branch}^{{commit}}', optional=True, timeout=timeout)
    relation = 'unknown'
    if head and candidate:
        if head == candidate:
            relation = 'equal'
        elif c.git(root, 'merge-base', '--is-ancestor', head, candidate, optional=True, timeout=timeout) is not None:
            relation = 'behind'
        elif c.git(root, 'merge-base', '--is-ancestor', candidate, head, optional=True, timeout=timeout) is not None:
            relation = 'ahead'
        else:
            relation = 'diverged'
    return dict(root=str(root), revision=head, branch=current_branch, configured_branch=branch, remote=remote,
                candidate=candidate, dirty=dirty, relation=relation, remote_freshness='last_fetched', unborn=head is None)


def checkout_preconditions(root, remote, branch, expected_name, timeout=30, *, clean=True, approved_repository=None):
    observed = status(root, remote, branch, timeout)
    if observed['branch'] is None:
        c.fail('source.detached', 'Checkout is detached.', 4)
    if observed['branch'] != branch or observed['revision'] is None:
        c.fail('source.identity_mismatch', 'Checkout is not on the configured branch with a commit.', 4)
    origin = c.git(root, 'remote', 'get-url', remote, optional=True, timeout=timeout)
    if origin is None:
        c.fail('source.remote_unknown', 'Configured remote is missing.', 4)
    if approved_repository is not None:
        if sources.repository(origin) != approved_repository:
            c.fail('source.identity_mismatch', 'Configured remote differs from its approved repository.', 4)
        sources.endpoint(root, origin, approved_repository)
    else:
        # Legacy v1 configuration has no approved URI. Migration is explicit.
        name = origin.replace('\\', '/').rstrip('/').removesuffix('.git').rsplit('/', 1)[-1].rsplit(':', 1)[-1]
        if name != expected_name:
            c.fail('source.identity_mismatch', 'Configured remote does not name the expected repository.', 4, expected_repository=expected_name)
    if clean and observed['dirty']:
        c.fail('source.dirty', 'Commit or preserve authoring changes before updating.', 4)
    for marker in ('MERGE_HEAD', 'CHERRY_PICK_HEAD', 'REVERT_HEAD', 'rebase-merge', 'rebase-apply'):
        location = c.git(root, 'rev-parse', '--git-path', marker, timeout=timeout)
        path = Path(location)
        if not path.is_absolute():
            path = root / path
        if path.exists():
            c.fail('source.dirty', 'An in-progress Git operation blocks updating.', 4)
    if c.git(root, 'config', '--bool', '--get', 'core.sparseCheckout', optional=True, timeout=timeout) == 'true':
        c.fail('source.candidate_invalid', 'Sparse checkouts are unsupported.', 4)
    entries = c.git(root, 'ls-files', '--stage', timeout=timeout)
    if any(line.startswith('160000 ') for line in entries.splitlines()):
        c.fail('source.candidate_invalid', 'Submodule checkouts are unsupported.', 4)
    return observed


def fetch(root, remote, branch, timeout, output):
    transport = c.git(root, 'remote', 'get-url', remote, timeout=timeout)
    options = sources.network_options(root, transport)
    before = c.git(root, 'rev-parse', '--verify', f'refs/remotes/{remote}/{branch}', optional=True, timeout=timeout)
    output['data']['fetch_effects'] = dict(attempted=True, fetched=False, remote_refs_changed=False)
    try:
        c.git(root, *options, 'fetch', '--no-tags', '--no-recurse-submodules', remote, f'+refs/heads/{branch}:refs/remotes/{remote}/{branch}', timeout=timeout, mutating=True)
        output['data']['fetch_effects']['fetched'] = True
    finally:
        after = c.git(root, 'rev-parse', '--verify', f'refs/remotes/{remote}/{branch}', optional=True, timeout=timeout)
        output['data']['fetch_effects'].update(remote_refs_changed=before != after, before=before, after=after)


def tree(root, revision, path='', recursive=False, *, max_output=16 * 1024 * 1024,
         exact=None, include_trees=False):
    args = ['ls-tree', '-z']
    if recursive:
        args.append('-r')
    if include_trees:
        args.append('-t')
    args.append(revision + (':' + path if path else ''))
    if exact is not None:
        args = ['--literal-pathspecs', *args, '--', exact]
    raw = c.git(root, *args, binary=True, max_output=max_output)
    rows = []
    for item in raw.split(b'\0'):
        if not item:
            continue
        try:
            header, name = item.split(b'\t', 1)
            mode, kind, oid = header.decode('ascii').split()
            name = name.decode('utf-8')
        except (ValueError, UnicodeError):
            c.fail('source.candidate_invalid', 'Candidate has unsupported tree names.', 4)
        rows.append((mode, kind, oid, name))
    return rows


def candidate_packages(root, revision, identifiers):
    available = {}
    folded = set()
    try:
        for mode, kind, oid, name in tree(root, revision, 'skills'):
            c.skill_id(name)
            if name.casefold() in folded or mode != '040000' or kind != 'tree':
                c.fail('source.candidate_invalid', 'Candidate package roots must be distinct real trees.', 4)
            folded.add(name.casefold())
            available[name] = oid
        packages = {}
        for identifier in sorted(identifiers):
            if identifier not in available:
                c.fail('source.candidate_invalid', 'Candidate removes a requested skill.', 4, skill=identifier)
            files, paths = {}, {}
            for mode, kind, oid, name in tree(root, revision, 'skills/' + identifier, True):
                if mode not in ('100644', '100755') or kind != 'blob' :
                    c.fail('source.candidate_invalid', 'Candidate contains linked, special or case-colliding entries.', 4, skill=identifier)
                parts = name.split('/')
                for index in range(1, len(parts) + 1):
                    partial = '/'.join(parts[:index])
                    value = (partial, index == len(parts))
                    if partial.casefold() in paths and paths[partial.casefold()] != value:
                        c.fail('source.candidate_invalid', 'Candidate contains case or file/directory conflicts.', 4)
                    paths[partial.casefold()] = value
                if any(part in ('', '.', '..') for part in name.split('/')) or '\\' in name:
                    c.fail('source.candidate_invalid', 'Unsafe candidate path.', 4)
                files[name] = c.git(root, 'cat-file', 'blob', oid, binary=True)
            if 'SKILL.md' not in files:
                c.fail('source.candidate_invalid', 'Candidate package has no SKILL.md.', 4)
            facts = c.metadata(files['SKILL.md'].decode('utf-8'), identifier)
            packages[identifier] = dict(id=identifier, description=facts['description'], fingerprint=c.digest({name: c.digest(value) for name, value in files.items()}))
        return packages
    except (c.MaskError, UnicodeError) as error:
        if isinstance(error, c.MaskError) and error.code == 'source.candidate_invalid':
            raise
        c.fail('source.candidate_invalid', 'Candidate skill tree or metadata is invalid.', 4)


def validate_git_intent(entry, config, program_root):
    c.fields(entry, ('scope', 'root', 'before', 'candidate'), family='recovery')
    expected = Path(config['source']['root']) if entry['scope'] == 'source' else program_root if entry['scope'] == 'program' else None
    if expected is None or entry['root'] != str(expected) or any(not isinstance(entry[key], str) or not re.fullmatch('[0-9a-f]{40,64}', entry[key]) for key in ('before', 'candidate')):
        c.fail('recovery.conflict', 'Invalid pending Git transition.', 8)


def advance(root, candidate, pending, home, output, timeout):
    before = copy.deepcopy(pending)
    pending['phase'] = 'git_started'
    c.atomic_text(home / 'pending.json', c.text_json(pending), c.text_json(before))
    try:
        c.git(root, 'merge', '--ff-only', '--no-edit', candidate, timeout=timeout, mutating=True)
        if c.git(root, 'rev-parse', 'HEAD', timeout=timeout) != candidate:
            c.fail('git.failed', 'Checkout did not reach the frozen candidate.', 5)
        before = copy.deepcopy(pending)
        pending['phase'] = 'git_advanced'
        c.atomic_text(home / 'pending.json', c.text_json(pending), c.text_json(before))
        fs.checkpoint('git')
    except (Exception, KeyboardInterrupt):
        output.update(changed=True, transaction='partial')
        c.fail('recovery.required', 'Checkout may have changed; pending intent retained without resetting Git.', 8)


def explicit_selection(args, state, legacy):
    """Legacy roots the user named with --project/--user, or None for the shared operation itself."""
    if not (getattr(args, 'project', None) or getattr(args, 'user', False)) or getattr(args, 'all', False):
        return None
    import mask
    return [root for root in mask.selected_roots(args, state) if root in legacy]


def update(config, state, home, output, args):
    """One normal update: acquire, freeze, disclose impact, obtain any expanded-scope consent, activate, verify.

    A dry run, --offline, --expect-plan-hash and a consented rerun never fetch: they bind
    the candidate already in the cache so that the applied content is the reviewed one.
    """
    import mask_consent as consent
    guard = getattr(args, 'expect_plan_hash', None)
    source = config['source']
    root, remote, branch = Path(source['root']), source['remote'], source['branch']
    timeout = config['git_timeout_seconds']
    observed = checkout_preconditions(root, remote, branch, 'AgentSkills', timeout, approved_repository=sources.approved_legacy(config))
    records = c.consumer_records(state)
    from mask_pinned import is_pinned
    roots = [Path(key) for key in sorted(records) if not is_pinned(records[key])]
    selected = explicit_selection(args, state, roots)
    # Refuse unavailable/invalid declarations before any network operation.
    identifiers = set()
    for project in roots:
        c.registered_root(project, records[str(project)], c.consumer_scope(state, project))
        identifiers.update(c.consumer_manifest(project, c.consumer_scope(state, project), home)['skills'])
    local = fs.plan(config, state, roots, operation='update', home=home)
    for blocker in local['blockers']:
        if blocker['code'] != 'skill.unknown':
            raise c.MaskError(blocker['code'], blocker['message'], 4, details=blocker['details'])
    acquire = not output['dry_run'] and not getattr(args, 'offline', False) and guard is None and getattr(args, 'consented', None) is None
    if acquire:
        fetch(root, remote, branch, timeout, output)
    fetched = output['data'].get('fetch_effects', dict(attempted=False, fetched=False))
    observed = checkout_preconditions(root, remote, branch, 'AgentSkills', timeout, approved_repository=sources.approved_legacy(config))
    if observed['candidate'] is None:
        c.fail('source.remote_unknown', 'Fetch the configured source branch before previewing an update.', 4)
    if observed['relation'] in ('ahead', 'diverged'):
        c.fail('source.' + observed['relation'], 'Source cannot fast-forward; no automatic merge, reset or push is allowed.', 4)
    candidate = observed['candidate']
    packages = candidate_packages(root, candidate, identifiers)
    transition = dict(scope='source', root=str(root), before=observed['revision'], candidate=candidate)
    view = dict(revision=candidate, packages=packages, transition=transition)
    planned = fs.plan(config, state, roots, candidate=view, operation='update', home=home)
    advanced = candidate != observed['revision']
    if advanced:
        planned['would_change'] = True
        planned['actions'].insert(0, dict(kind='source.advance', status='planned', before=observed['revision'], after=candidate))
    fs.public_plan(planned, output)
    output['data'].update(source_before=observed['revision'], source_after=observed['revision'], remote_freshness='last_fetched', requires_fetch=not acquire, fetch_effects=fetched,
                          scope=dict(kind='shared_source', selected=[str(item) for item in (roots if selected is None else selected)], affected=[str(item) for item in roots],
                                     pinned_unaffected=[key for key in sorted(records) if is_pinned(records[key])]))
    fs.ensure_applicable(planned, guard)
    if selected is not None and len(selected) < len(roots) and planned['would_change']:
        # A shared checkout cannot be isolated to the named scope: disclose every affected legacy scope and ask for that wider effect.
        proposal = consent.request('scope.expand', 'update.shared_source', output['data']['scope']['affected'], planned['actions'], planned['plan_hash'],
                                   f"This update also changes {len(roots) - len(selected)} other legacy scope(s) sharing the source; apply it to all {len(roots)}?")
        if output['dry_run']:
            output['data']['confirmation'] = proposal
        else:
            consent.require(args, output, proposal)
    if output['dry_run'] or not planned['would_change']:
        return
    rechecked = checkout_preconditions(root, remote, branch, 'AgentSkills', timeout, approved_repository=sources.approved_legacy(config))
    if rechecked['revision'] != observed['revision'] or fs.plan(config, state, roots, candidate=view, operation='update', home=home)['plan_hash'] != planned['plan_hash']:
        c.fail('plan.stale', 'Source or consumer observations changed before checkout.', 4)
    pending = fs.make_pending(planned, home)
    pending['git'] = transition
    fs.validate_pending(pending, home)
    c.atomic_text(home / 'pending.json', c.text_json(pending), None)
    if advanced:
        advance(root, candidate, pending, home, output, timeout)
        output['data']['source_after'] = candidate
    try:
        for identifier in identifiers:
            c.package(root, identifier)
    except c.MaskError:
        output.update(changed=advanced, transaction='partial')
        c.fail('recovery.required', 'Checked-out skill contents failed validation; inspect pending update.', 8)
    fs.execute(planned, home, output, pending=pending)
    output['changed'] = output['changed'] or advanced


def recover_git(pending, home, output, mode):
    entry = pending['git']
    root = Path(entry['root'])
    config = pending['config']
    remote = config['source']['remote'] if entry['scope'] == 'source' else 'origin'
    branch = config['source']['branch'] if entry['scope'] == 'source' else 'main'
    expected_name = 'AgentSkills' if entry['scope'] == 'source' else 'ManageAgentSkills'
    observed = checkout_preconditions(root, remote, branch, expected_name, (config or {}).get('git_timeout_seconds', 30), approved_repository=sources.approved_legacy(config) if entry['scope'] == 'source' else None)
    if observed['revision'] not in (entry['before'], entry['candidate']):
        c.fail('recovery.conflict', 'Checkout changed outside the recorded transition.', 8)
    if mode == 'rollback':
        if observed['revision'] != entry['before']:
            output.update(changed=True, transaction='partial')
            c.fail('recovery.conflict', 'The source advanced; rollback never resets Git. Complete recovery against the new revision.', 8)
        return
    if entry['scope'] == 'source':
        identifiers = {identifier for key in pending['selected'] for identifier in c.consumer_records(pending['after_state']).get(key, {}).get('last_manifest', {}).get('skills', [])}
        candidate_packages(root, entry['candidate'], identifiers)
    else:
        from mask_install import validate_program
        validate_program(root, entry['candidate'])
    if observed['revision'] == entry['before'] and entry['candidate'] != entry['before']:
        if c.git(root, 'merge-base', '--is-ancestor', entry['before'], entry['candidate'], optional=True) is None:
            c.fail('recovery.conflict', 'Recorded candidate is no longer a fast-forward.', 8)
        if not output['dry_run']:
            advance(root, entry['candidate'], pending, home, output, (config or {}).get('git_timeout_seconds', 30))
