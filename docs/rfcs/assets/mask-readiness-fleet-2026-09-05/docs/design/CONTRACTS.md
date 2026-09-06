# Shared architecture and wire contracts

These are proposed contracts for the new RFCs, not shipped schemas. The fixture JSON schemas under `contracts/` cover the portable examples; runtime state/journal implementations remain implementation work. Integrators may adjust provisional version numbers after inspecting live history, but cannot change semantics silently.

## 1. Vocabulary and system boundary

| Term | Meaning |
|---|---|
| Agent | Host adapter such as claude or codex |
| Platform | windows, macos or linux; architecture is a separate selector |
| Consumer | One physical project/worktree or the registered personal home |
| Scope | user or project; never an agent name |
| Source / tap | Approved repository identity and package layout |
| Copy import | Curated source payload copied from a frozen upstream revision, with provenance |
| Binding | A source-qualified skill requirement for one consumer contribution |
| Selector | Commit or ref requested when creating/updating a resolution |
| Lock / resolution | Exact repository commit, package path and content digest |
| Artifact | Isolated locally materialized content identified by a digest |
| Profile | Portable selection plus lock, optionally contributing to a local consumer |
| Bundle | Named set expanded into explicit bindings at a recorded source revision |
| Intent | Signed desired-state change with frozen scope/device/content identities |
| Receipt | Device-signed observation of applying/verifying an exact intent |
| Readiness | Current declared filesystem deployment is present; not proof of host loading |

```text
name / Git URL / curated source
        -> approved source resolver + copy/tap choice
        -> exact lock + validated immutable artifacts
        -> consumer selection / profile contributions
        -> one local planner, ownership validator and executor
        -> per-skill links for each selected scope/agent

fleet controller -> signed intent -> enrolled device's same local engine
                                  <- signed receipt <- verified filesystem
```

No consumer directory is replaced wholesale. No package code runs during import/deployment. No separate agent-specific installer writes into MASK-owned destinations. A per-device machine state is never shared through the control repository.

## 2. Portable selection v2

Closed shape:

```text
schema_version: 2
sources: map of source alias -> { repository, ref?, packages? }
default_agents?: "all" | nonempty agent array  # default all
skills: unique binding array
binding: { source, id, version?, agents?, when?, introduced_by? }
version: { commit } | { ref }                 # mutually exclusive
when: { platforms?, architectures? }        # nonempty arrays when supplied
introduced_by: provenance-only string array  # never removal authority
```

Source aliases and skill IDs follow safe ASCII token conventions. Unique binding key is `(source, id)` within one contribution. Same host invocation name from different sources is allowed only when effective scope/agent destinations are disjoint. Source indexes map IDs to exact paths; path is frozen in the lock and cannot be reinterpreted by a later index update.

`default_agents`/binding `agents` are positive selections. “All” is not an autodetection query. Explicit lists must be supported by the deployed adapter contract. Portable metadata may name an unknown future agent as a publisher restriction, but an explicit consumer request for an unsupported adapter is a typed unsupported request, never silently skipped.

When `when` is false, the binding is intentionally not applicable on that device. Otherwise explicit platform incompatibility blocks; implicit/all agents may be filtered by declared agent compatibility. A fleet policy can explicitly approve platform skips in its plan. Receipts record skip reasons and never call a skip an installation. Unknown compatibility stays unspecified and permissive for legacy imports, not certified generic.

Use common canonical serialization for hashes: reject duplicate keys, floats/nonfinite values, unknown closed fields and invalid schemas; normalize semantic sets in a documented order; UTF-8 JSON with sorted keys, compact separators and no ASCII escaping; append no newline to hashed bytes. This is MASK's explicit serialization, not a claim of RFC8785 conformance. Sequence integers are bounded to JSON-interoperable nonnegative safe integers. Display output may use indentation and a trailing newline.

## 3. Lock v1

Closed portable fields:

```text
schema_version: 1
selection_digest: sha256
resolver: "mask-lock-v1"
packages: unique resolved binding array
resolved binding: {
  source, id, repository, path,
  commit, git_object_format,
  payload_digest, metadata_digest, provenance_digest?, selector
}
```

`selector` records the commit/ref used when resolving; commits remain exact. Hash the normalized full selection (including source/default/when/target intent) so any relevant declaration edit requires a coherent lock update. Origin-only edit may retain all package resolutions while updating the declaration digest; it need not fetch.

All selected bindings receive resolutions, including currently inapplicable ones, so the same portable profile has exact content identities on other devices. A device need not download an inapplicable package to claim a correctly recorded skip, but it cannot claim its bytes are installed. A source not available to the exporting machine cannot receive a guessed resolution.

`metadata_digest` hashes compatibility/package metadata; metadata may be absent, in which case its canonical explicit absence has a defined digest. Provenance optional absence remains distinguishable from known imported origin. `payload_digest` covers every deployed regular payload entry and logical executable mode. A lock never contains a target filesystem path or a credential.

Package artifact identity is a SHA-256 digest over a sorted manifest of `{path, mode, size, sha256}` entries. `mode` is logical Git `100644`/`100755`; string paths are UTF-8 portable normalized spelling. This retains executable intent even where the OS lacks POSIX mode bits. Reject path aliases/case/Unicode-normalization collisions instead of normalizing two names into one.

## 4. Metadata v1 and source indexes

`mask-skill.json` is optional, closed, passive JSON: schema_version, agents, platforms, architectures, requirements. Fields use `generic` or nonempty arrays; missing file means unspecified. Requirements are bounded human-readable strings, never executable commands or provider addresses. Raw free-text SKILL.md compatibility remains human metadata.

`mask-source.json` is optional source-owned JSON: schema_version, packages map `{id: path}`, bundles map `{name: {description?, skills: [binding...]}}`. Cross-source bundle references identify portable source requirements and require explicit local source approval. The source index cannot set machine trust, install hooks, private credential names, endpoints, or arbitrary output paths.

Do not expand arbitrary YAML support or rewrite imported package text just to populate metadata. Unsupported syntax must produce a precise limitation. Substantial adaptation/copying preserves relevant licensing notices; MASK does not infer a license grant from an absent LICENSE file.

## 5. Local machine and persistence evolution

| Contract | Snapshot | Proposed new boundary |
|---|---|---|
| CLI result | v1 | Remains v1 envelope; additive data/actions and exit 9 for incomplete fleet mutation |
| Project/user selection | v1 strings + whole targets | v2 source-qualified bindings; explicit migration |
| Machine config | v1 single root | v2 approved source bindings; legacy source alias retained |
| Ownership state | v1/v2 | v3 resolved artifact identity + preserved legacy records |
| Pending journal | v1/v2 | v3 bounded typed control-file/ownership intent |
| Resolution lock | absent | v1 |
| Integration policy | absent | v1 local authority/config-entry ownership |
| Fleet protocol/intent/receipt | absent | independent v1 contracts |

Readiness can ship journal v3 while still writing legacy state v2. It does not require content-store migration. Later v3 state is an explicit selected-scope migration. Each reader dispatches by serialized version; never reinterpret old bytes with a new parser. Old pending journals are recovered first. Tool upgrade and persisted-state migration are separate visible operations.

Persisted local approval/config objects belong to the machine, not portable manifests. Journal v3 paths are validated by typed role and selected physical root. Before/after declaration/lock bytes and expected absence are recorded; only recognized mutation kinds can change them. Config updates/hook entries use a separate bounded role allowlist and exact existing-entry identity checks; arbitrary JSON-provided filesystem targets are never accepted.

When activation changes the artifact, desired raw link text comes from the **new** resolution; current raw link text must match old ownership before replacement. Recovery pins old/new artifacts and control-file observations. If a branch moves between a crash and recovery, changed live control files block stale completion. Unchanged registry paths do not imply unchanged worktree identity.

Artifact preparation may retain safe cache/staging effects after a failed operation. Report those effects explicitly; never call a full-system snapshot byte-identical if cache artifacts were created. Read-only commands/dry-runs do not prepare caches. No-op deployment does not update timestamps/generations just because a hook fired.

## 6. Publication and external effects

Default source import writes selected curated paths only and returns them. Fleet copy mode that needs remote availability can use a scoped isolated-worktree publication operation under an explicit owner policy. Exact paths, expected parent revision, source identity and new commit are recorded. Existing unrelated staged edits are not swept into the commit. Source publication and control publication cannot be made one atomic cross-repository transaction; a failure leaves each completed phase visible and resumable.

Devices use read-only desired-state access; receipt publication uses the controller or a separate receipt store/ref-restricted endpoint. Do not assume branch-scoped authorization exists on every Git host.

The control repository may be a private Git host chosen by the owner. No GitHub-specific hosted workflow, cloud subscription, daemon or account provisioning is required. A tap's private authentication remains device-local unless explicitly approved artifact forwarding is used. An exact commit unavailable upstream is not replaced by current main.

## 7. Fleet wire and authorization

RPC `mask.rpc.v1` uses length-prefixed UTF-8 JSON messages, e.g. a 4-byte unsigned network-order byte length followed by the JSON payload. Reject lengths above the configured bound before allocation, duplicate fields and unexpected frame counts. Initial proposed control-frame cap: 1 MiB; content transfer uses separate bounded binary chunks with total/package limits. These are tunable implementation defaults to measure, not performance evidence.

Sign the canonical intent **payload bytes**, excluding transport framing and detached signature fields. Use established OpenSSH file signatures with distinct intent/receipt/vault namespaces (for example `mask-intent@mask.invalid` for fixtures); pin actual deployed namespace identifiers in the protocol. Verify authorized signer, payload digest, intended device/group, epoch/sequence/parent, source/scope permission and validity before acting. The examples intentionally contain no valid signature and cannot authorize a mutation.

Enrollment establishes current fleet epoch and minimum accepted sequence through a trusted controller exchange. A fresh device must not trust “the first old signed revision the repository returned” as current. Persist a high-water mark and compare-and-swap generation. Offline devices can keep already-installed approved bytes while their control view is stale, but must not claim current convergence or accept an expired fresh mutation. Controller signatures do not prove freshness against a server indefinitely hiding newer revisions; report last contact and expiry, and do not overclaim freeze resistance.

Receipts bind device ID/key, intent/operation digests, effective scope/agent bindings, exact package digests, actual status and observation time. The receiver persists idempotency identity in the journal/committed operation record before acknowledging. Lost transport means unknown outcome until query. A signature is not remote OS attestation or host UI evidence.

### Initial resource policy

Proposed conservative defaults: 1 MiB per control frame, 256 MiB per selected package, 64 MiB per regular file, 10,000 files and depth 32 per package, bounded binary transfer chunks, and 64 KiB of redacted diagnostic output. Large manifests transfer in bounded chunks rather than bypassing the frame cap. An explicit approved machine policy may raise limits; downloaded package text cannot. Enforce bounds before allocation/materialization where possible and test cumulative limits, not only individual files. These are initial tunable policies, not measured capacity/performance claims.

## 8. Result and status policy

Keep existing `ok`, `changed`, `would_change`, `transaction`, `actions`, `error` semantics for the local command. Add explicit `data.complete`, `data.installed_everywhere`, `data.device_results`, `data.operation_id` and `data.report` for fleet operations.

Exit 9 is `fleet.incomplete`: some requested device results remain pending/blocked/unknown or policy-authorized partial application exists, but it does not itself mean local filesystem recovery is needed. Exit 8 remains actual local partial/indeterminate mutation/recovery. Remote recovery-required is visible in the corresponding device row and aggregate incomplete result; an unaffected controller need not invent a local pending journal.

An observational status query may succeed while the operation is incomplete. Initial install/apply requests requiring all-device convergence cannot return success merely because they published intent. `complete=true` accounts for every selected device; `installed_everywhere=true` excludes compatibility skips. Later superseded receipts do not satisfy earlier exact content requests.

## 9. Scope ownership and portability

Effective selection is a composition of local declaration and approved subscribed-profile contributions. Preserve provenance per contribution. Equal coordinate+digest bindings merge positive agent edges by union; a missing edge in one contribution is not a deny. Conflicting versions or an explicit local permission restriction require policy. A fleet receipt verifies that its requested contribution and deployment edges exist; unrelated extra local skills/edges do not invalidate that receipt, but a local override preventing a requested edge does. Fleet removal withdraws its own contribution and cannot remove a local independent choice. When a local override prevents exact fleet intent, report deviation/blocked, not applied_verified.

Neither target selection nor version isolation gives strong session isolation. Running agents may retain instructions or reopen changed links. A per-session immutable snapshot/lease could be designed later; do not advertise it in this pack. Retain needed prior artifacts conservatively until explicit cleanup policy exists.

Automatic ensure refuses changes to tracked generated destinations and warns about unignored managed link paths. It never rewrites tracked .gitignore from a Git hook. An explicit integration/setup plan may maintain exact per-entry ignore rules after checking existing content; shared Git worktree exclude files require shared-scope disclosure and cannot hide unrelated real skills. Do not introduce a new bootstrap surprise while solving readiness.
