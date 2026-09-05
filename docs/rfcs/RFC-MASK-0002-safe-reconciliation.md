---
id: RFC-MASK-0002
title: Ownership-safe planning, symlink deployment and recovery
status: Proposed
owner: MikeMarcin
created: 2026-09-05
---

# RFC-MASK-0002: Ownership-safe planning, symlink deployment and recovery


## Summary

Reconcile project declarations into directory symlinks without overwriting user content. Separate pure planning from effects. Serialize MASK writers on one machine, preflight the whole selected operation, and retain minimal recoverable intent when a crash interrupts multiple filesystem writes.

## Scope

Own the planner, filesystem adapter, ownership state, local operation lock, `pending.json`, `plan`, `apply`, `link adopt`, `recover` and observational `doctor`, with focused filesystem/CLI tests. No file synchronization, copy deployment, junction creation, remote state or background service.

## Authority model

MASK may create needed **real** `.claude/skills` and `.agents/skills` directories and individual symlinks for declared skills; it may atomically rewrite its own validated configuration/state/manifest files through the commands that own them. It may unlink a managed **leaf symlink** only when its current identity/type/link value passes the ownership precondition.

It must never recursively delete a path, replace an agent skills root, follow a linked destination parent, delete a real target directory, clean parent directories, or edit the pointed-to skill content during reconciliation. The application contains no `shutil.rmtree` deployment/cleanup path. Repository source edits and Git fast-forward checkout are separate explicit authorities, not an exception allowing destination deletion.

Machine state records `relative_path`, `skill`, `target`, and the exact `readlink` value observed at creation/adoption. Paths are recomputed from validated skill IDs and the adapter table; serialized paths are checked against those recomputed values. A poisoned state entry like `../../Documents` is never used as a removal instruction. Root aliases are canonicalized at registration; every path component **beneath** a managed root is inspected without following symlinks/reparse points. An already linked `.claude` or `.agents` directory is refused in v1, with an explanation rather than an overwrite.

## Target truth table

| Current leaf | Ownership record | Action |
|---|---|---|
| Missing | None | Create |
| Missing | Valid prior record | Recreate if still desired; otherwise drop stale record |
| Symlink with exact expected source | Matching record | No-op |
| Broken symlink with unchanged recorded link text | Matching record | Repair only after source/desired-path validation; no blind deletion |
| Symlink with a different link value than its record | Any | Refuse `target.drift`; preserve it |
| Correct-looking symlink | None | Refuse `target.unmanaged_link`; optional explicit adoption below |
| Real file/directory, junction or special entry | Any | Refuse `target.collision`; state does not override disk |
| Unchanged owned symlink no longer desired | Matching record | Unlink leaf and remove record |

When removing a requirement, source existence is not required to remove an unchanged owned dangling link. A missing desired source **does** block new deployment. Opaque unknown content is never treated as an obsolete skill.

## Planner

`mask plan --project PATH` or `--all` computes deterministic sorted actions from the source, prospective/current manifests, effective targets, registry and observed filesystem. Missing/unavailable registered projects are blockers, not silently skipped. `--all` preflights all selected projects before the first managed mutation; targeted apply does not inspect unrelated projects. An empty registry returns a no-op warning.

A plan contains create/remove/record/manifest actions, no-op reasons, all blockers, `would_change`, and a `plan_hash`. Hash inputs include tool protocol/adapter identity, relevant machine config, state generation and ownership records, consumer roots/identity, normalized manifests, source commit plus hashes of **all selected skill files** (not HEAD alone), target types/raw link text, and intended changes. Include the bytes of supporting scripts/references so dirty changes invalidate a prior preview. Exclude timestamps and diagnostic formatting. Hash regular entries without following source links.

`apply --expect-plan-hash HASH` recomputes under the writer lock immediately before effects; mismatch is `plan.stale` with zero managed changes. Prospective manifest commands with `--apply` use the same planner and accept the same guard. This is optimistic concurrency for cooperative agents, not a cryptographic approval or protection from a hostile process.

## Writer serialization and files

Use one persistent `MASK_HOME/operation.lock` and OS advisory locking: `fcntl` on POSIX, `msvcrt` byte-range locking on Windows. Hold it through preflight, journal, effects and state commit; OS release after process death avoids stale PID lock deletion. Keep metadata informational only. Do not unlink the lock path as “recovery,” and never bypass a busy lock. All MASK mutators using a shared MASK_HOME take the same lock.

Read commands and dry runs do not create lock/journal/state directories. Read a generation before/after inspection and report/retry a bounded unstable snapshot rather than pretending a mixed view is authoritative. Initialization creates the known lock file as an explicit mutation. `MASK_HOME` must be a local filesystem location; concurrent independent MASK_HOME registries managing one project are unsupported and must collide rather than steal each other's links.

Configuration/state/manifest rewrites use a sibling temporary regular file, flush/fsync where supported, and `os.replace`. Check parent/leaf preconditions and old-content digest immediately before replacing. This protects against ordinary truncation and stale writers, but does not make several files one durable transaction or guarantee every filesystem's power-loss behavior.

## Minimal journal, not a second database

Keep at most one `pending.json` for the active mutation. It records transaction ID, phase, selected projects, before/after manifest bytes where relevant, state generation, and exact planned leaf link values. It contains no full source checkout, arbitrary scripts or unrelated file backups.

Write intent before the first link/manifest mutation. After successful effects, replace state and clear the journal. A crash or failure can therefore leave an operation in a recognizable before/after state. All later mutators refuse `recovery.required` until recovery; inspection remains available.

`mask recover --inspect --json` is observational. `mask recover --complete --json` and `--rollback` are explicit mutators; only one mode is accepted. Both validate every journal path and current value against recorded before/after states, refuse unexpected objects, and never infer blanket ownership. A current path matching neither state is a collision that the agent must report. Recovery intent authorizes only the specific journaled change, not arbitrary current contents.

Rollback removes only newly created unchanged symlinks, recreates only unchanged prior owned links in still-empty destinations, and restores manifest/state bytes only when their current bytes match the operation's expected post-state. Leave empty directories created by the operation rather than pruning them; report that residual effect. Never overwrite edits made after the failed operation. No automatic destructive recovery on startup.

For a Git update, the journal also records source-before/source-after commits. Recovery does not reset the source checkout. If source advanced, returning all old link records is not a whole-operation rollback; report source advancement and perform safe completion or a partial outcome. RFC-MASK-0003 defines this boundary.

## Runtime failures and honest outcomes

Recheck leaf and destination-parent conditions at each effect. On an expected I/O error, attempt only the narrow rollback that remains safe. Report each action's actual state and one of `not_started`, `not_needed`, `committed`, `rolled_back`, `partial`. Persistent empty created directories and changed Git state keep `changed=true` even when core link effects were rolled back. Never claim all-or-nothing across projects; a late OS failure may leave earlier projects changed.

The default operation stops on the first runtime failure after full preflight. It returns nonzero and leaves enough state/journal for the next agent to inspect. `--all` does not return success with a failed/unavailable project hidden in warnings.

The journal/ownership records are trusted local program state, but parsing still rejects invalid schemas and paths. This is not a hardened adversarial filesystem sandbox. Full race freedom against malicious same-user parent swapping would require stronger OS-specific handles and a different scope. Tests cover detectable cooperative races and fail-closed behavior; documentation must not overclaim stronger protection.

## Explicit adoption

One narrow command solves bootstrap or lost-record ownership without a generic force flag:

```text
mask link adopt --project PATH --skill implement-rfc --target codex --expect-source ABSOLUTE_PATH
```

The project must be registered, the skill declared, the leaf an actual directory symlink, its current raw/normalized destination the expected configured source, and all parent/source validations must pass. Adoption writes ownership state only. It cannot adopt real directories, arbitrary links, another source, a skill not in the declaration, or all unknown paths recursively. It supports JSON, dry-run and stale-plan checking. A mismatched ownership record is not “fixed” by adoption.

## Observational diagnostics

`doctor` checks configuration, source, registry, selected links, pending recovery and Git ignore status. It does not create a scratch symlink merely to claim read-only status; Windows creation capability may be `unknown` until an actual apply or isolated test. `--check` returns a dedicated nonzero drift/failure class, while `plan` can successfully describe actionable drift. Source dirty is a warning for local apply but a blocker for update. Report deployment as `filesystem_present`; host loading/enabling remains `not_verified` unless a separately recorded runtime check exists. No `doctor --fix`.

## Native verification

Use temporary fixtures and actual filesystem objects, not only mocks. Verify Windows symlink privilege refusal, directory symlink type, junction refusal and path normalization; verify macOS symlinks, case behavior and spaced paths. A skipped native test is not a passing platform claim. Linux fixture tests provide additional evidence but cannot satisfy native Windows/macOS cards. No user directory is a disposable test target.


## Acceptance criteria

- **RFC-MASK-0002-AC01** — Planner/apply preserve unmanaged files, real directories, unknown/wrong symlinks and junctions byte-for-byte; stale state never authorizes deleting replacement content.
- **RFC-MASK-0002-AC02** — Valid per-skill links converge idempotently; removal affects only unchanged owned leaf links; source/destination escape and case-collision checks fail closed.
- **RFC-MASK-0002-AC03** — All selected projects and prospective manifests preflight before effects; stale plan hashes, supporting-file edits and unavailable projects cause zero managed changes.
- **RFC-MASK-0002-AC04** — Writer locking, atomic JSON replacement and the minimal pending journal support explicit inspect/complete/rollback; injected mid-operation failure and process restart yield truthful outcomes without recursive deletion.
- **RFC-MASK-0002-AC05** — Explicit link adoption changes only ownership state for exact validated current links; doctor/dry-run do not mutate configuration, links, journals or Git state.
- **RFC-MASK-0002-AC06** — Native Windows and macOS focused symlink/ownership checks have passing direct evidence, or their cards remain open and the corresponding support claim is withheld.
