---
id: "RFC-MASK-0010"
title: "Portable personal selections, reusable bundles and profile composition"
status: "Proposed"
owner: "MikeMarcin"
created: "2026-09-05"
---

# RFC-MASK-0010: Portable personal selections, reusable bundles and profile composition

**Delivery stage:** C — portable composition. **Packet status:** proposed implementation contract; no implementation or acceptance is claimed.

**Predecessors:** RFC-MASK-0008, RFC-MASK-0009.

The new behavior below explicitly extends the historical v1 scope. Preserve settled RFCs 0001–0005; update current architecture/user documentation only when the relevant implementation ships. See [source reconciliation](../design/SOURCE-RECONCILIATION.md), [shared contracts](../design/CONTRACTS.md), and [references](../design/REFERENCES.md).

## Decision

Make “recreate my skills on another machine” a portable declaration-and-lock operation. Do not synchronize `MASK_HOME`, ownership records, absolute source paths, home-directory identities, pending recovery, launcher paths or credentials.

Add named bundles as selection conveniences. The first version expands a bundle into explicit bindings and exact locks; it does not introduce live package dependencies, installation hooks, or an automatically changing membership graph.

## Portable profile format

A profile is ordinary versioned data in a repository or exported directory:

```text
profiles/personal/selection.json
profiles/personal/selection.lock.json
profiles/personal/README.md             # optional human explanation
```

The selection and lock use the same schemas as a project. Bundle origins and source coordinates are portable. Machine endpoints, local approved-root policy, stored home identities and secrets are not. Content artifacts are optional separately addressed attachments, not paths into the producer's filesystem.

```text
mask user export --output DIRECTORY [--effective] [--freeze-agents]
mask user import DIRECTORY [--replace] [--apply]
mask profile inspect LOCATION
mask profile subscribe LOCATION --user
mask profile unsubscribe PROFILE --user
mask bundle list [--source SOURCE]
mask bundle show SOURCE/NAME
mask bundle apply SOURCE/NAME [--project PATH | --user] [--replace]
mask bundle refresh SOURCE/NAME [--project PATH | --user]
```

All mutations support dry-run/guards; export writes only an explicit output destination and refuses unrelated existing files. Default import is an incremental merge. `--replace` deliberately replaces only the selected local declaration contribution, not all subscribed profiles or unrelated unmanaged skills. Plain exports default to the local contribution; `--effective` produces a self-contained flattened view and labels the loss of live subscription semantics. Do not clone profile internal machine state.

## All-agent defaults and portability

The user selected an all-supported default. Export preserves `agents: "all"` by default and states that the adapter set can differ by machine/version. `--freeze-agents` concretizes the currently resolved agents for exact deployment-target reproduction; it does not change package locks. Content reproducibility and identical host coverage are different claims.

V1 inherited machine defaults are concretized during migration/export unless the owner explicitly chooses all. A platform-conditional skill preserves its `when` condition so import on another OS is explainable. A source's SSH authentication alias remains local; the portable repository identity is credential-free.

## Bundles

Bundle definitions belong in a versioned source index or a portable profile repository. Each named bundle is an ordered-for-display, set-for-semantics collection of source-qualified skill bindings and optional target/condition suggestions. Bundle source commit and definition digest are recorded at expansion. A bundle update is explicit and diffable; existing membership does not change because the source's main branch moved.

Flat bundles only: no recursive includes, dependency solver, post-install commands, or hidden source enrollment. If a bundle references an unapproved source, report the prerequisite before any consumer edit. Expansion must yield a collision-free candidate selection before commit/apply. A changed definition invalidates its plan hash.

Apply defaults to set union and does not overwrite a manual per-skill target override. A conflict returns the competing origins for an explicit choice. `--replace` means exact resulting local selection, with its removals shown. Record `introduced_by` for explanation, not as a license to delete a shared skill later.

There is deliberately no naive `bundle remove` that removes every member. A skill may be independently selected or present in several bundles. Initial removal is explicit unrequire, or an exact-set refresh preview that shows which bindings disappear. A future live-bundle contribution model would need ownership semantics; do not smuggle it into origin annotations.

## Subscriptions and local contributions

A subscription binds an approved profile identity/revision to one local consumer. The local base selection stays separately editable. Resolve each contribution to its exact lock; merge identical bindings and preserve all origin references. Conflict rules are RFC-MASK-0009. The subscription file is machine policy, not a mechanism for a downloaded profile to approve itself or create arbitrary projects.

Profile updates are explicit locally or driven by the optional approved fleet policy in RFC-MASK-0013. Unsubscribing removes that contribution and reconciles only now-unrequired unchanged owned links. If a local binding still requires the skill, it remains. Offline evaluation uses the last approved profile revision and reports its freshness; it must not imply live fleet convergence.

## Installation and new-machine bootstrap

A new machine installs the known MASK program and enrolls source/profile trust once. Import resolves local source transports, obtains exact locked artifacts under explicit network policy, registers the selected existing home and applies through the normal journal. Return a short prerequisite report if the interpreter, symlink privilege, authentication or exact artifact is missing. Do not create secret-bearing setup scripts.

The code path should support one durable command for import-and-apply; the agent should not need to manually edit JSON, relocate symlinks, copy plan hashes through several turns, or hand-merge internal registries. A dry run remains available for meaningful review. Unavailable native machines do not become a mandatory user checkpoint for all other work.

## Acceptance boundary

Use two independent temporary machine roots with different local source and home paths. Verify the same exported profile produces identical package digests, independently correct links, and appropriate target/platform reports. The actual canonical AgentSkills contents are a separate handoff; test fixtures do not prove those workflows are portable.

## Acceptance criteria

- **RFC-MASK-0010-AC01** — Export/import round-trips selections and exact content locks between different machine/home/source paths without including credentials, registry identities, journals or launchers.
- **RFC-MASK-0010-AC02** — Incremental and replace modes preserve their declared ownership scopes; exported all-agent behavior and optional frozen-agent behavior are explicit and tested.
- **RFC-MASK-0010-AC03** — Bundle expansion/refresh is deterministic, source-revision bound and stale-plan guarded; overlapping bundles/manual selections do not cause accidental removals.
- **RFC-MASK-0010-AC04** — Profile subscription/removal preserves local contributions and reports version/target conflicts, unapproved sources, unavailable artifacts and offline freshness honestly.
- **RFC-MASK-0010-AC05** — One public import-and-apply path bootstraps selected personal scope through normal validation/recovery, with native Windows/macOS focused tests and no internal-state editing.
