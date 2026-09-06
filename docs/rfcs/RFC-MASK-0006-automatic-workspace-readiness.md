---
id: "RFC-MASK-0006"
title: "Automatic workspace readiness for clone, worktree, branch and agent startup"
status: "Accepted"
owner: "MikeMarcin"
created: "2026-09-05"
---

# RFC-MASK-0006: Automatic workspace readiness for clone, worktree, branch and agent startup

**Delivery stage:** A — first usable milestone. **Packet status:** proposed implementation contract; no implementation or acceptance is claimed.

**Predecessors:** none in this pack; builds on the supplied v0.2.0 baseline.

The new behavior below explicitly extends the historical v1 scope. Preserve settled RFCs 0001–0005; update current architecture/user documentation only when the relevant implementation ships. See [source reconciliation](../design/SOURCE-RECONCILIATION.md), [shared contracts](../design/CONTRACTS.md), and [references](../design/REFERENCES.md).

## Decision and user outcome

On a configured machine, an approved repository should not need repeated registration, manual plan-hash copying, or an LLM-driven installation ceremony after ordinary development operations. Add `mask ensure`: discover the selected worktree, authorize the scope, register when needed, and reconcile the live requirements through the existing planner/executor. Git and agent integrations call the same operation.

Ship this first against the existing local-source mode. Do not wait for the fleet service, source federation, locks, or optional security reporting. Existing `project register . --apply` demonstrates that registration/reconciliation can already share an operation; do not shell out to a chain of public commands and claim that chain is one transaction. [M1: mask.py:project_dispatch; mask_fs.py:plan/execute]

## Public interface

```text
mask ensure [--project PATH] [--event EVENT] [--check] [--offline] [--json]
mask integration inspect [--project PATH] [--json]
mask integration enable [--git] [--agent claude|codex] [--project PATH] [--json]
mask integration disable [--git] [--agent claude|codex] [--project PATH] [--json]
mask integration approve --project PATH [--linked-worktrees] [--json]
mask integration approve --repository REPOSITORY --under ROOT [--json]
mask integration revoke --project PATH [--json]
mask workspace forget PATH --expect-identity ID [--json]
mask launch --agent claude|codex [--project PATH] -- HOST_ARGUMENTS...
```

Mutating forms support dry-run and guards where they compute managed edits. `ensure --check` is observational and exits nonzero if readiness is blocked or drifted. Ordinary `ensure` does not require a caller-supplied plan hash: it computes and rechecks its own operation under the existing writer lock. It never reports an observational plan as applied.

Integration installation is separate from repository approval. Approval records are machine-local, bound to physical roots or an explicit repository identity plus clone-root boundary. Approving linked worktrees authorizes independent registration within that common Git repository, not arbitrary sibling projects. A remote URL alone is not ownership proof. Existing explicit registrations remain usable; adopting automatic policy is deliberate, not inferred from an untrusted `.mask.json`.

For non-Git directories, explicit `--project` plus root approval is required. Discovery stops at the nearest worktree boundary and never follows parent manifests across that boundary. Nested projects are reconciled when directly selected or already registered; a global Git event does not recursively crawl a monorepo looking for declarations.

## Git integration and capability detection

Prefer additive named hooks where the installed Git supports them. Git's current primary documentation describes named configuration hooks, coexistence with traditional hooks, and event-level disable switches; availability must be probed, not inferred from an executable name. [E1, E2]

Use separate owned hook names for `post-checkout`, `post-merge`, `post-rewrite`, and a bounded `post-commit` recheck. Pass a fixed event argument from a machine-owned launcher; Git supplies event-specific positional arguments/stdin. Never interpolate branch names, repository text, or hook stdin into a shell expression. The post-commit path covers a manually completed merge or committed declaration change; no-op work remains bounded.

For older Git, install only into a verified unoccupied per-repository hook entry or provide an explicit integration entry for the existing hook manager. A template adapter may cover future clones only when it preserves the selected template and the effective hook path. Do not silently take over `core.hooksPath`, replace a hook script, rewrite a user's hook manager, or claim a committed hook file alone covers clone. Agent startup remains the mandatory fallback for unsupported Git integration.

A one-time user-level named-hook installation can observe new clones under approved boundaries. With older Git, report exactly whether clone-time coverage, existing-worktree coverage, and startup coverage exist. Events after checkout do not undo Git's work when readiness fails. Print a concise warning that names the completed Git operation and the blocked MASK state; do not say the checkout failed to occur. [E1]

MASK's own Git helper must suppress both traditional and named/configured hooks. The existing `core.hooksPath` override alone is insufficient for named hooks. Use capability-aware event-level disabling for each relevant Git operation, including reference transactions, and an internal reentrancy token. Test with configured marker hooks and directory marker hooks. An environment token alone is not an authority boundary. [M1: mask_core.py:git; E2]

## Agent startup and discovery

Install thin adapters outside the skill payload being bootstrapped, pinned to the selected interpreter and program launcher. Bootstrap cannot depend on loading `manage-agent-skills` first. Host configuration edits preserve unrelated entries and use exact owned-entry identities/hashes for uninstall or replacement.

Claude's documented startup output can request `reloadSkills`; its SessionStart event cannot itself enforce blocking. Codex has documented hook trust and startup integration. Record the supported host/version and the adapter's actual gate/reload capabilities; do not copy Claude output fields into Codex. Do not bypass a host's hook trust prompt or modify host trust databases. [E3, E4]

The adapter checks project readiness and, when personal scope is already registered, the applicable personal readiness. It never creates personal selections because an untrusted project requested them. Keep the two scopes independently reported; a cross-scope startup operation preflights its selected consumers before effects. A no-project session can still check approved personal scope.

Use a supported pre-prompt gate when available for a strict blocked-workflow policy. Otherwise expose a visible warning and offer `mask launch` as a deterministic prelaunch gate. That command ensures first, then invokes an already configured host executable with an argv array and inherited ordinary host authorization; it is not a replacement agent runtime. No host executable, subscription, or native adapter test is fabricated.

Codex application worktree setup can invoke the same installed command as an additional supported integration. It must coexist with existing setup scripts rather than replacing them. [E5]

## Lifecycle state machine

| Observation | Result and allowed effect |
|---|---|
| Approved, valid manifest, all prerequisites available | Register/reconcile; return `ready` or `ready_legacy_unpinned` |
| No approval | `approval_required`; no registration, link creation, or fetch |
| Invalid/conflicted/unreadable manifest or lock | `blocked`; preserve previous deployment |
| Known owned destination changed or unmanaged collision | `blocked`; preserve the object |
| Pending journal | `recovery_required`; never choose recovery automatically |
| Busy writer | Bounded wait within the hook deadline; then `busy`, no forced takeover |
| Startup with missing ordinary manifest | `manifest_missing`, unless the proven inactive-branch case below applies |
| Explicitly selected project no longer exists | `unavailable`; no inferred deletion |

A confirmed branch that never declared MASK can be `inactive_on_branch` under the repository's opt-in policy. Confirm: the approved worktree identity is unchanged; the current HEAD and index omit the declaration; the previous managed declaration was tracked; no sparse-checkout, merge/rebase/conflicted index, or ambiguous local deletion explains the absence. For a startup without a usable transition record, use the same conservative Git evidence or block. Remove only unchanged owned links, keep registration and integration, and create no empty manifest. Switching back restores the branch's declared skills. A plain missing file never means an empty selection.

Persist only the policy and operation state necessary to explain/recover these effects; do not add a second authoritative project registry. An inactive branch can be derived from current verified Git evidence and the existing registration. Journal v3 adds validated control-file expectations (including expected absence) and the readiness/deactivation operation kinds; it may carry v1/v2 registry states before later pinned-state migration. Recovery validates branch/control-file expectations and does not complete stale effects after a subsequent branch switch.

For worktree removal, accept explicit verified host removal notification or `workspace forget` with expected registration identity. If the path still exists, perform normal unregister rules rather than abandon files. If removal is established and no pending operation references it, retire the local registration without touching an unrelated path. Missing mounts and inaccessible machines are not proof of removal. Ordinary Git has no universal worktree-removal event to assume.

## Readiness, pins and network boundary

Initially ensure reads only the configured local source. RFC-MASK-0008 later supplies locked artifacts. Its rule is stronger than a blanket prohibition on network: restoring **an already approved exact lock** can hydrate missing bytes under one-time `allow_locked_fetch` policy; resolving newer upstream revisions cannot. Default hook policy is cache-only until locked-fetch authority is enabled. `--offline` always wins. A first clone lacking locked bytes reports the exact missing artifacts and a single supported hydration action, not an LLM scavenger hunt.

Ready means the desired filesystem deployment exists. Report `host_load` separately as `reload_requested`, `verified`, `not_verified`, or `restart_required`; do not imply removal erases instructions from an ongoing conversation.

## Performance and implementation seam

Build `mask_ensure.py` for orchestration and `mask_integration.py` for owned hook/config adapters. Reuse `mask_fs.plan/execute`; extend their input observations instead of introducing a shell link installer. No global `doctor --all`, network freshness check, full home scan, or broad catalog scan on startup. Hash selected payloads once per operation; measure before adding a cache. No-change ensure preserves registry generations and file bytes. Diagnostics/log writes, when requested, are bounded and explicitly excluded from the managed-deployment no-op claim.

Integration enable/disable must itself be recoverable: allowlisted destination roles, before/after entry values, exact ownership checks, no whole-config replacement. Record each changed persistent integration file in the operation outcome. Program upgrades keep the stable launcher path; missing launcher/interpreter is an actionable bootstrap failure.

## Acceptance criteria

- **RFC-MASK-0006-AC01** — Actual clone, worktree add, branch switch, merge and manual-merge completion fixtures invoke integration and converge without a user executing apply; unsupported Git integration reports its coverage accurately.
- **RFC-MASK-0006-AC02** — Ensure combines authorization, registration and selected-scope reconciliation through the existing safety engine; unchanged runs preserve managed bytes/generation and perform no unrelated scans.
- **RFC-MASK-0006-AC03** — Untrusted roots, collisions, replaced parents, busy locks and pending recovery cannot be converted to success or silently repaired; hooks never claim to roll back completed Git actions.
- **RFC-MASK-0006-AC04** — Inactive-branch handling distinguishes verified branch absence from deleted, sparse, unreadable or conflicted input; interrupted readiness refuses completion after its control files change.
- **RFC-MASK-0006-AC05** — Owned hook installation/removal preserves unrelated hooks/settings, suppresses configured and directory hooks for MASK internal Git commands, and prevents recursion.
- **RFC-MASK-0006-AC06** — Native Claude and Codex startup/worktree scenarios record actual versions and first-prompt discovery or an explicit fallback limitation; a warning-only adapter is not called a strict gate.
- **RFC-MASK-0006-AC07** — Native Windows and macOS readiness/launcher paths receive focused direct checks; worktree removal and unavailable-root handling preserve ownership and are independently tested.

## Live authorization

Accepted for implementation by the owner’s 2026-09-05 import-and-implement request. Follow the live card dependencies; native and external acceptance remain open until directly exercised.
