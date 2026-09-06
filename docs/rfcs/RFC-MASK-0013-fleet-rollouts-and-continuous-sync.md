---
id: "RFC-MASK-0013"
title: "Declarative fleet rollouts, optional continuous convergence and completion reports"
status: "Accepted"
owner: "MikeMarcin"
created: "2026-09-05"
---

# RFC-MASK-0013: Declarative fleet rollouts, optional continuous convergence and completion reports

**Delivery stage:** D — personal fleet workflow. **Packet status:** proposed implementation contract; no implementation or acceptance is claimed.

**Predecessors:** RFC-MASK-0010, RFC-MASK-0011, RFC-MASK-0012.

The new behavior below explicitly extends the historical v1 scope. Preserve settled RFCs 0001–0005; update current architecture/user documentation only when the relevant implementation ships. See [source reconciliation](../design/SOURCE-RECONCILIATION.md), [shared contracts](../design/CONTRACTS.md), and [references](../design/REFERENCES.md).

## User story and decision

The owner says to Claude or Codex: “Install this skill on all my machines,” supplying a unique configured name or a GitHub skill URL. The tool resolves it, imports a curated copy or registers a tap under the chosen policy, fixes an exact artifact resolution, updates authorized desired selections, contacts online devices, and returns a useful per-device report. Offline devices remain pending, not silently successful.

The same workflow supports an already enrolled pull runner for machines that become reachable later. This explicitly expands the earlier no-fleet/no-daemon scope; ordinary local use still installs no background process. Continuous convergence follows **approved desired revisions**, not arbitrary upstream latest.

## High-level operation

```text
mask fleet install INPUT --all-devices --scope user [--mode copy|tap]
mask fleet install INPUT --device NAME ... --project-alias ALIAS [--mode copy|tap]
mask fleet remove SOURCE/ID --all-devices --scope user
mask fleet update SOURCE/ID --all-devices --scope user
mask fleet sync [--device NAME | --all]
mask fleet operation show OPERATION_ID
mask fleet operation wait OPERATION_ID --timeout SECONDS
mask fleet operation cancel OPERATION_ID
mask fleet runner enable [--interval SECONDS]
mask fleet runner disable
mask fleet runner status
```

All high-level mutators expose one preview/guardable plan and default human report; JSON is the agent API. `INPUT` name resolution is restricted to configured taps; URL parsing is RFC-MASK-0007. Ambiguous names or multi-skill repositories return bounded choices before selecting anything. An omitted import mode uses an owner-configured default and shows it in the plan; without such a default the request needs that one decision. Do not pick a destructive or more public mode silently.

A request for “all my machines” means the frozen set of currently enrolled, non-revoked devices included by the selected group policy. New devices are not silently added to an in-flight operation. A future subscription policy can apply the resulting profile to new enrollees as a separate desired revision.

Scope user does not mean “edit every project.” A project rollout uses preauthorized project aliases mapped independently on each machine; it does not guess absolute paths or clone arbitrary projects. Missing project mappings remain blocked. Local user selections and project requirements stay independent.

## Durable desired state

Use a private Git repository as the initial optional control store. It contains portable profile declarations/locks, source identities, signed desired-state objects, operation membership, and signed device receipts. Local device endpoints, credentials, physical ownership/state and pending filesystem journals remain local. Git is transport/history, not the authenticity proof.

A single active control history serializes desired revisions. Each signed revision includes fleet epoch, monotonically increasing sequence, parent intent digest, operation ID, frozen device/scope set, resolved artifact/selection digests, permitted compatibility skips, authorization expiry for new application, and approved source-publication effects. Authenticate using enrolled controller keys. A stale/replayed epoch/sequence, unknown signer or invalid chain is rejected; read-only repo hosting cannot silently inject a deployment.

Any local Claude/Codex driver with delegated controller authority may propose a change. Publish using compare-and-swap/fast-forward against the expected control revision. Concurrent proposals never overwrite one another; re-read and recompute a disjoint additive request if policy permits, otherwise return a conflict. Do not automate arbitrary Git conflict resolution or reset the control repo. A rollback is a new signed desired revision referencing old pinned bytes, not history rewriting.

Devices receive read-only credentials for the desired-state repository by default. For online RPC, the controller records their signed receipts. A pull runner publishes receipts to a separate receipt repository or an explicitly ref-restricted endpoint, never by granting it write access to controller intent. A single physical repository is permitted only when its actual host ACLs prove the required ref separation; do not assume an ordinary GitHub repository token is branch-scoped. Validate device signatures and intent binding even in a private repository. Receipt deletion/reordering can reduce availability and yields unknown/stale status, not forged completion. A durable local operation record distinguishes publication from deployment.

## Install pipeline and authority

1. Resolve the input against cached/explicitly fetched source data. Choose copy/tap mode from explicit input or policy; freeze package coordinate and commit.
2. Validate package kind/structure and compatibility. Prepare the artifact and provenance outside discovery. Diff current intended bindings.
3. Expand the requested device set and scope. Query online capabilities; use clearly dated cached enrollment data for offline devices, never invented readiness.
4. Compose desired profile changes while preserving local/fleet contribution ownership. Preflight possible conflicts. Freeze exact content and target intent for every selected device.
5. Under existing delegated authority, commit/publish the selected profile/control changes. A curated copy may require a separate source publish; only its explicit package/provenance paths may be committed/pushed. Show and report these external writes. No public visibility or credential grant is implied.
6. Dispatch prepare/apply to online devices. Each device hydrates exact bytes, checks its local conditions, applies through MASK, verifies final links/artifacts and publishes a signed receipt.
7. Produce the operation report immediately with all known outcomes. `wait` may synchronously poll for a bounded interval; a timeout returns pending/unknown states and a resumable operation ID.

If a caller has not delegated the needed publish/enroll/source authority, stop at that boundary with a precise proposed grant; do not demand recurring confirmation for mechanics already authorized. “Install this skill” is not authority to publish a private repository, add an SSH key to every machine, or rotate credentials.

## Delivery state and truthfulness

| Device state | Meaning |
|---|---|
| `queued_offline` | Intent durably published; no device acceptance yet |
| `preparing` | Exact content validated/hydrating; deployment not complete |
| `applied_verified` | Device verified expected filesystem links and artifact digests at the recorded desired revision |
| `not_applicable` | Explicit platform/target condition or approved compatibility skip; not an installation |
| `blocked` | Collision, missing mapping, policy, version, credential or compatibility prerequisite |
| `recovery_required` | Device has unresolved local partial mutation |
| `unknown` | Connection/receipt loss prevents a reliable current outcome |
| `superseded` | A later desired revision replaces this request before convergence |
| `canceled` | Future delivery withdrawn; already applied effects are separately recorded |

An accepted request is not a completed rollout. `fleet install` returns `ok=false` with exit 9 when selected devices remain incomplete, while recording any successful local control publication and per-device results. Exit 8 is reserved for actual partial/indeterminate local mutation requiring recovery. A read-only `operation show` can return `ok=true` while `data.complete=false`; its meaning is successful observation, not success of the rollout.

`complete=true` requires a matching receipt for every selected applicable device and explicit accounted-for non-applicable entries. `installed_everywhere=true` is stricter: every selected device actually installed, without skips. A stale receipt from an earlier intent cannot satisfy the new operation. `host_load` remains independent; fresh filesystem state cannot prove active conversations discarded old instructions.

## Optional continuous delivery

Start with `sync` and foreground/on-demand RPC. Add an opt-in per-user scheduled runner that fetches the approved control revision, verifies signatures/monotonicity, reconciles only its delegated scopes, and publishes receipts. Prefer bounded scheduled invocations over a custom always-running network server. Native scheduler adapters can target launchd and Windows Task Scheduler after exact ownership/native tests; no elevation is assumed. A Linux adapter remains best-effort until proven.

Suggested default polling is five minutes with bounded jitter and exponential failure backoff; this is a proposed configurable policy, not an observed performance claim. One catch-up runs on an enabled startup/wake path. No local write lock is held during network transfer. A runner does not update the MASK program, enroll sources, expand trust, change an exact lock to latest, or resolve recovery on its own.

Published removal supersedes a queued earlier install; a waking device applies the latest authorized effective desired state and records old requests as superseded rather than replaying every historical mutation. Cancel stops future dispatch; uninstalling already deployed content requires a new desired-state change. Revocation prevents future authorized work but cannot erase keys/content from an unreachable stolen device.

## Report and real demonstration

The report shows input/mode, source and imported revision, selected device count, exact package digest, per-device effective agents/scope, changed/unchanged/skipped bindings, pending/blocker reasons, host-load status, timestamps and operation ID. The example report is illustrative, never proof of completed installation.

Required dogfood: at least two genuinely distinct enrolled machines, including the owner's supported macOS and native Windows paths, plus an offline/catch-up scenario. Enroll only with explicit authority. Device simulation proves protocol and reconciliation logic but cannot close the real multi-machine acceptance row. No special LLM subscription or agent running on every target is needed.

## Acceptance criteria

- **RFC-MASK-0013-AC01** — A single name-or-GitHub-URL fleet install request composes copy/tap resolution, exact locking, authorized source/control publication, deployment and a per-device report without manual internal-state edits.
- **RFC-MASK-0013-AC02** — Frozen device/scope sets, local contribution preservation and source/package identity prevent unexpected project edits, hidden source enrollment or skill-name ambiguity.
- **RFC-MASK-0013-AC03** — Signed monotonic desired revisions and compare-and-swap publication handle two controllers, duplicate deliveries, replay, rollback-as-new-intent and revoked peers without silent last-writer overwrite.
- **RFC-MASK-0013-AC04** — Offline, unknown, incompatible, recovery-required, canceled and superseded devices are reported distinctly; incomplete rollouts never claim installed everywhere or reuse stale receipts.
- **RFC-MASK-0013-AC05** — An opt-in runner catches up to the latest approved state with bounded polling/backoff, preserves scheduler ownership, never upgrades upstream/programs implicitly, and resumes after interruptions.
- **RFC-MASK-0013-AC06** — Actual two-machine macOS/native-Windows rollout and offline catch-up evidence is recorded, or that acceptance stays open with the exact environmental limitation.
- **RFC-MASK-0013-AC07** — Failure between import/publication/remote apply/receipt steps is resumable and truthful, and reports preserve the difference between filesystem verification and host discovery.

## Live authorization

Accepted for implementation by the owner’s 2026-09-05 import-and-implement request. Follow the live card dependencies; native and external acceptance remain open until directly exercised.
