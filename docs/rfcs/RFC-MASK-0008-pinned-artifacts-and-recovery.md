---
id: "RFC-MASK-0008"
title: "True version pinning, immutable deployment artifacts and recoverable migration"
status: "Accepted"
owner: "MikeMarcin"
created: "2026-09-05"
---

# RFC-MASK-0008: True version pinning, immutable deployment artifacts and recoverable migration

**Delivery stage:** B — reproducible content. **Packet status:** proposed implementation contract; no implementation or acceptance is claimed.

**Predecessors:** RFC-MASK-0007.

The new behavior below explicitly extends the historical v1 scope. Preserve settled RFCs 0001–0005; update current architecture/user documentation only when the relevant implementation ships. See [source reconciliation](../design/SOURCE-RECONCILIATION.md), [shared contracts](../design/CONTRACTS.md), and [references](../design/REFERENCES.md).

## Decision

A project or personal selection resolves to exact package bytes, not to a moving shared checkout. Store those bytes in a local content-addressed artifact store; deployment links target a versioned artifact. Several worktrees may simultaneously deploy different revisions of the same skill. Authoring a source checkout does not mutate pinned consumers.

A lockfile without isolated content does not satisfy this RFC. The legacy live-checkout mode remains available only as an explicit compatibility/authoring mode and is reported as `unpinned`; fleet and reproducibility claims require pinned mode.

## Declaration and lock

Selection schema v2 is shared by project and user declarations; its authoritative shape is in the shared contracts and examples. It records source identities, selected source-qualified package IDs, optional per-package commit/ref selectors, target policies and selection provenance. Per-skill targeting is implemented by RFC-MASK-0009 before that combined milestone is advertised.

Project lock: `<project>/.mask.lock.json`. Personal lock: `MASK_HOME/user.lock.json`. Portable exported profiles contain both the declaration and its lock. A lock includes the canonical declaration digest, source identity and exact package path, full Git commit and object format, selected payload/tree digest, original package name, relevant compatibility/provenance metadata digests, and resolver schema/version. No absolute machine paths, secrets, mutable `latest` values, or installation timestamps belong in the content resolution.

A source ref is an **update selector**. A lock is the **active resolution**. Changing a ref upstream never changes an existing lock. Pinned commit requirements remain fixed until explicitly changed. Semver dependency solving and skill-to-skill dependencies are outside this pack; tags/branches resolve to full commits through ordinary Git. Moved tags/ref rewrites are surfaced as non-fast-forward/rebound selectors and require explicit approval, not an automatic upgrade.

```text
mask lock [--project PATH | --user] [--refresh] [--skill SOURCE/ID ...]
mask source fetch --locked [--project PATH | --user]
mask update [--project PATH | --user | --all] [--skill SOURCE/ID ...]
mask source publish SOURCE [--paths PACKAGE_PATH ...] [--json]
mask migrate --to-pinned [--project PATH | --user | --all]
mask source dev-link SOURCE/ID --project PATH --authoring-root PATH
```

Lock creation/refresh is an explicit declaration-resolution mutation. It uses cached refs unless an explicitly network-capable flow has fetched first. `update` may fetch with permission, freezes a candidate, reports a diff, then changes the selected lock/deployment through the guarded engine. `update --dry-run` remains network-free. `ensure` never rewrites a lock or changes a selector. With an existing stale/mismatched lock, it blocks; with no lock in a v2 declaration, it reports `lock.missing`.

The published capability registry distinguishes possible network use from policy/operand conditions. Legacy unqualified `update` retains all-consumer shared-checkout behavior while any selected legacy mode is used. A targeted update cannot claim to isolate a legacy shared source; either migrate first or expand the operation explicitly. Pinned targeted updates affect only selected consumers.

## Artifact construction

Use canonical raw Git blob bytes and logical Git executable modes, not a filtered checkout or OS newline conventions. Define the payload digest over a sorted list of relative path, logical file type/mode, byte length and SHA-256 content digest. Directory paths are derived. Include all selected supporting files and package metadata; reject casefold and normalization collisions before writing. Digest algorithm/schema form part of the artifact identifier.

Suggested layout: `MASK_HOME/store/v1/<payload-digest>/payload/<skill-id>/...`, with a sibling validated artifact manifest. The exact path is runtime-derived from validated identifiers. Do not trust arbitrary absolute destinations in a lock or journal. Sharing identical immutable payloads is allowed; mutable authoring files are never hardlinked into the store.

Build under a unique owned staging root, validate, flush files where supported, then publish by an atomic directory rename within the store volume. Never replace an existing digest directory with different bytes. An existing matching artifact is reused; a corrupted one blocks dependent deployment and can be repaired only by an explicit verified operation after checking active references. Read-only permissions are an accident-prevention aid, not a hostile same-user boundary.

Native Windows modes differ; retain logical modes in the manifest and compare raw file contents without inventing POSIX permission evidence. No file execution, `pip`, `npm`, LFS smudge, submodule fetch, archive extraction helper or Git checkout hook is invoked by artifact materialization. Selected package validation remains bounded.

## Hydration and offline operation

A committed declaration plus lock is sufficient to identify exact required content. On a new machine, an approved source transport can retrieve the locked commit and verify the payload digest. Do not resolve a branch to a newer revision to satisfy a missing commit. Some remotes will not serve an unreachable commit; return `artifact.unavailable` and use the retained copy/artifact-transfer path, not a substitute.

Fresh clone/worktree readiness may hydrate absent locked artifacts if `allow_locked_fetch` is enabled for that approved source/scope. Cache-only mode and `--offline` never network. This is restoration, not upstream update. Each report names hydrated bytes and whether network was used. A clean warm ensure verifies the selected artifact/leaf conditions only; reuse hashes within one operation but do not replace integrity checking with a timestamp assertion.

## Reconciliation and recovery changes

State schema v3 extends ownership with validated source/package/artifact identity and deployment mode. Journal v3 represents bounded typed file roles: project declaration, project lock, user declaration, user lock, selected machine migration fields, and owned deployment links. Paths are reconstructed from trusted roots and role enums. It is not an arbitrary file-write list.

Fix an important existing assumption: the current planner retains `old['link_text']` whenever an old record exists. Pinned upgrades must compute the **desired new artifact target**, while checking the actual old raw target before replacement. Recovery must validate both old and new resolved artifacts; it cannot compare both against one configured `source/skills/<id>` path. `link adopt`, doctor, unregister and recovery all require this generalization. [M1: mask_fs.py:plan/validate_pending/adopt]

Build/fetch artifacts before link activation and outside long-held machine mutation locks. Reacquire the existing writer lock and revalidate declaration/lock bytes, generations, destination identities and artifact digests before the journaled transition. Failed preparation may retain owned cache objects and must report them, but makes no consumer changes. A late link/lock write failure is a truthful partial/recoverable operation.

A selected consumer's lock and links converge through one journaled operation; this is not an atomic all-file switch for an already-running reader. Multiple consumers/machines are not a distributed transaction. Rollback restores unchanged owned previous links and control-file bytes; it never resets an authoring Git checkout. Pending journals and rollback baselines retain references to their artifacts.

Legacy state/journals v1/v2 remain readable and recoverable. An old pending operation must be recovered before migration. Migration records exact before state/config/declaration/lock bytes and source fingerprints; it never invents pins for dirty/uncommitted source content. Dirty authoring work must be preserved and either committed explicitly, retained as explicit dev-link mode, or deliberately imported as a separately identified local artifact that cannot claim upstream commit reproducibility.

The current self updater refuses schema changes by byte comparison. Do not bypass that check or migrate during a hook. Install/update the program through an explicit reviewed revision, then run the supported migration, leaving a direct Python fallback and retained legacy snapshots. Older executables refuse state v3. [M1: mask_install.py:validate_program]

## Authoring, retention and source publishing

Normal shared-skill editing belongs in the source checkout. A `dev-link` is a scope-local explicit exception, marked dirty/unpinned and forbidden in fleet intents; returning to pinned mode is a guarded resolution/deployment operation. No automatic writeback follows a symlink edit.

Source publishing is new bounded authority: use an isolated worktree and explicit package/provenance paths; refuse overlapping edits; optional commit/push authority is separately approved and reported. Updating a source does not update consumers until their locks change.

Automatic garbage collection is not required. Retain artifacts referenced by any live lock, unavailable registered consumer, pending journal, rollback baseline, or durable fleet delivery. An explicit future GC can list candidates; this pack does not add recursive deletion to deploy/unregister. A removed remote does not invalidate already retained pinned bytes.

## Acceptance criteria

- **RFC-MASK-0008-AC01** — Two worktrees simultaneously use distinct immutable versions of one skill, and source authoring/ref movement changes neither deployment until an explicit selected update.
- **RFC-MASK-0008-AC02** — Locks reproduce raw package bytes across fixture machines; digest, package path, source identity, executable mode, malformed lock and moved-ref errors fail closed.
- **RFC-MASK-0008-AC03** — Ensure restores available exact artifacts, optionally hydrates only approved locked content, never resolves latest or rewrites lockfiles, and reports unavailable exact commits honestly.
- **RFC-MASK-0008-AC04** — Planner/executor/adoption/recovery correctly retarget an unchanged owned legacy or old-artifact link to a new artifact and preserve collisions, rather than retaining the old target.
- **RFC-MASK-0008-AC05** — Interruptions before/after lock, link and state effects preserve bounded v3 recovery; configuration/state migrations preserve exact legacy rollback bytes and reject concurrent edits.
- **RFC-MASK-0008-AC06** — Explicit migration covers project and personal consumers, dirty/unborn sources, old pending journals, schema-incompatible old programs, and direct-entrypoint escape paths.
- **RFC-MASK-0008-AC07** — Cache preparation, retention, dev-link exceptions and scoped publishing cannot silently alter other consumers, delete authoring history or claim atomicity across readers/devices.

## Live authorization

Accepted for implementation by the owner’s 2026-09-05 import-and-implement request. Follow the live card dependencies; native and external acceptance remain open until directly exercised.
