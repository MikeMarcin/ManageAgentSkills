---
id: RFC-MASK-0003
title: Explicit source updates, portable launchers and program updates
status: Proposed
owner: MikeMarcin
created: 2026-09-05
---

# RFC-MASK-0003: Explicit source updates, portable launchers and program updates


## Summary

Implement explicit one-way Git updates of the skill source and portable installation of the MASK executable. Skill updates and program updates are distinct because the user selected two repositories. Preserve private authentication in the existing Git environment; add no OAuth flow, account management, push command or automatic synchronization.

## Commands and scopes

```text
mask source status
mask source fetch
mask update [--expect-plan-hash HASH]
mask self status
mask self update
mask self install --bin-dir PATH
```

All support `--json`. The mutating commands support `--dry-run`. `source fetch`, `update` and `self update` are the **only network-capable MASK commands**. Cloning the two initial repositories remains ordinary Git bootstrap performed by the agent, not a new package-manager feature.

`source fetch` refreshes Git objects/remote-tracking refs only, never the deployed checkout or project links. Its response distinguishes `fetched` and remote-ref changes from deployed-content changes. `source status` reports the last fetched state and does not imply live remote freshness.

`update` always selects all registered projects, because their existing symlinks all observe the same source checkout. There is no `update --project` that pretends only one project's content changed. `apply --project` remains local linking only.

## Noninteractive Git adapter

Invoke the machine's existing Git executable with an argv list and `shell=False`, captured stdout/stderr, a configured timeout and closed stdin. Scope every command with `git -C`. Set `GIT_TERMINAL_PROMPT=0`, `GIT_MERGE_AUTOEDIT=no`, and use no interactive askpass path; with standard Git Credential Manager use its documented noninteractive setting. For ordinary SSH, require already-working noninteractive authentication and use BatchMode where a standard SSH invocation can be safely composed. Never replace a user SSH wrapper silently; unknown helper/wrapper behavior is explicitly unsupported and bounded by timeout.

Sanitize inherited repository-selection variables (`GIT_DIR`, `GIT_WORK_TREE`, `GIT_INDEX_FILE` and equivalents) so the caller cannot accidentally select another checkout. Preserve intended authentication mechanisms. Do not print tokens, credential-bearing URLs, full environment variables or unbounded Git output in JSON/debug logs.

Use `GIT_OPTIONAL_LOCKS=0` for observational Git commands. Disable repository hooks for MASK's own merge/update invocation with an explicit safe hooks setting; never change persistent Git configuration to accomplish this. User-configured credential helpers and checkout filters remain a trust boundary: `shell=False` does not prevent Git itself invoking them. Do not describe MASK as a sandbox, credential-isolated tool, or a system that never spawns a helper.

A timeout must not leave a mutating Git process free to continue after MASK reports refusal. Put the child in a process group/session, terminate the created process tree on timeout (POSIX group termination / Windows process-tree mechanism), wait/reap it, and preserve recovery intent. If complete cleanup cannot be confirmed, return an indeterminate/partial failure and require inspection; do not claim the checkout is unchanged. Focused tests use fake blocking child/helper processes, not a live credential challenge.

## Update algorithm

1. Acquire the local writer lock; refuse unresolved `pending.json`.
2. Confirm the configured source is the expected ordinary non-bare checkout on the configured branch. Refuse detached HEAD, active merge/rebase/cherry-pick, untracked or tracked modifications, wrong origin identity and unsupported sparse/submodule state. Source paths must not overlap consumer destination roots or MASK_HOME; registering the AgentSkills repository itself is allowed because `skills/` and generated destination paths are distinct.
3. Read all live registered manifests. An unavailable root or invalid manifest blocks default update. Do not remove unavailable entries or trust stale membership to authorize a potentially breaking source advance.
4. Perform local collision/path preflight before networking when possible. Fetch the explicitly configured remote branch using an explicit refspec; do not fetch every tag or execute credential provisioning.
5. Freeze the fetched candidate commit ID. If equal to HEAD, continue with local reconciliation. If local HEAD is ahead of or diverged from the remote candidate, refuse with an actionable source code; never reset, push, merge automatically, stash or clean.
6. Require current HEAD to be an ancestor of the frozen candidate. Inspect candidate Git tree objects, not the still-old worktree: every selected `skills/<id>/SKILL.md` must exist as a regular blob and its required subtree must pass package/path checks. Reject source symlinks (mode 120000), submodules (160000), unsupported entries, unsafe IDs, case conflicts and a candidate removing/renaming a requested skill. `git cat-file -e` alone is insufficient to establish type/identity.
7. Validate candidate metadata without executing anything from the candidate. Compute the exact planned source transition plus project actions and compare the requested plan hash, if any, **after** candidate resolution. A newly moved remote ref invalidates a prior preview instead of silently changing the approved candidate.
8. Recheck source HEAD/cleanliness, manifests, registry generation and target observations under the lock. Write pending intent. Fast-forward using `git merge --ff-only <frozen-sha>` with the safe subprocess policy.
9. Confirm resulting HEAD and required source contents, then reconcile all registered project links through the existing engine, without a second implementation of ownership logic.
10. Commit state and clear pending intent. Report source-before/source-after, fetch effects, every project outcome, actual persistent changes and any native/runtime limitations.

MASK never invokes `git reset --hard`, `git clean`, `git stash`, `git push`, `git checkout -f` or a conflict resolver. A source repository's explicit fast-forward can legitimately remove its own tracked files; it does not authorize deleting arbitrary consumer content. Files selected by live registered manifests are validated before advancing.

## Dry-run and source consistency

`update --dry-run` performs **no fetch**. It examines the last-fetched configured remote ref, or reports `source.remote_unknown`. Output explicitly says `remote_freshness=last_fetched` and `requires_fetch=true`; it never claims to be a live upstream check. For a fresh review, an agent runs `source fetch`, then `update --dry-run`, then guarded `update`.

One shared checkout means skill edits and a successful source fast-forward become visible to all symlinked consumers immediately; already-running agents may cache content. Do not promise session isolation, atomic bundle activation or version locks. Run updates between active implementation tasks. Local apply can use a dirty source for authoring, records its fingerprint, and warns; remote update refuses dirty source.

Git checkout is not atomic across the skill tree. A late checkout/I/O failure may leave changed content even if HEAD did not advance. Keep the journal, return nonzero and report actual source status. No automatic Git rollback. A source advance followed by a project deployment failure is a partial update: inspect/recover safely, then apply against the new source; never label the source rollback successful because links were restored.

## Portable installation

The canonical direct invocation is `python /absolute/ManageAgentSkills/mask.py ...` using a known Python 3.11+ interpreter. On Windows examples may use `py -3.11` for bootstrap, but installed launchers record the actual interpreter path selected at install; `py -3` alone does not prove a supported version.

`self install --bin-dir PATH` writes a small POSIX launcher or Windows `mask.cmd` pointing to that interpreter and program checkout. Both correctly quote spaced paths, forward argv and preserve exit code. Refuse an existing unrelated launcher; recognize only this installer's marker and recorded prior content for replacement. Do not edit PATH, shell profiles, registry or elevation settings automatically. Return the exact command/path and whether PATH discovery sees it. A single optional manual PATH change is documented; the agent can operate immediately by absolute launcher path.

Use a separate self-install ownership record in MASK_HOME or its existing state namespace. Do not discover/install a PyPI package with the generic name `mask`. No remote shell-pipe bootstrap, downloaded binary, daemon or installer registry is required.

## Program updates

`self update` identifies the checkout containing the currently running `mask.py` and validates its expected ManageAgentSkills origin, branch and clean/fast-forward conditions. It never substitutes AgentSkills as the program checkout. Reuse the Git adapter. Verify the candidate retains the direct entrypoint and supported protocol/schema contract without executing new code as preflight. Unknown incompatible protocol/state migration is a refusal, not an unreviewed migration.

After advancing, finish with the already-loaded implementation, do not load changed code lazily, and return `next_invocation_required=true`. The following separate invocation picks up the update. No re-exec, hidden continuation, auto-install chain or implicit skill update. A launcher continues pointing to the stable checkout path. Dirty program-authoring checkouts block self update but do not block ordinary skill management.

## Verification

Local bare-remote fixtures prove equal, fast-forward, ahead, diverged, detached, dirty, missing-skill candidate, non-regular tree entry, remote movement after preview, checkout failure and post-advance apply failure. Fake Git/SSH helpers prove output separation, noninteractive behavior and timeouts. Native launcher tests cover argument forwarding/exit codes. There is no required live GitHub mutation or mandatory authentication setup during tests.


## Acceptance criteria

- **RFC-MASK-0003-AC01** — Explicit update validates a frozen candidate against every registered live declaration before advancing and then reuses ownership-safe reconciliation; no requested skill can silently vanish.
- **RFC-MASK-0003-AC02** — Dirty/ahead/diverged/detached/unavailable/colliding/invalid candidate conditions return typed nonzero refusals with no consumer mutation; any fetch metadata effects are reported separately.
- **RFC-MASK-0003-AC03** — Dry-run is local and freshness-labeled; refreshed candidate or dirty-support-file changes invalidate a guarded plan rather than being silently applied.
- **RFC-MASK-0003-AC04** — Git subprocess output is bounded/redacted and noninteractive; timeout cleanup is exercised; source-advance/checkout/late-apply failures report partial state and preserve recoverable intent without destructive reset.
- **RFC-MASK-0003-AC05** — Portable launchers invoke the selected supported interpreter, preserve spaced arguments/exit codes, refuse unrelated files and do not alter PATH or privilege settings.
- **RFC-MASK-0003-AC06** — Program/source updates are separate; self update targets only ManageAgentSkills, uses ff-only safety, reports next invocation and neither re-executes nor modifies skill deployments.
