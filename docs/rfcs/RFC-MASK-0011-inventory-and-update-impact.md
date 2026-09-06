---
id: "RFC-MASK-0011"
title: "Where-used inventory, update diffs and deployment impact reports"
status: "Implementing"
owner: "MikeMarcin"
created: "2026-09-05"
---

# RFC-MASK-0011: Where-used inventory, update diffs and deployment impact reports

**Delivery stage:** C — explainability. **Packet status:** proposed implementation contract; no implementation or acceptance is claimed.

**Predecessors:** RFC-MASK-0008, RFC-MASK-0009, RFC-MASK-0010.

The new behavior below explicitly extends the historical v1 scope. Preserve settled RFCs 0001–0005; update current architecture/user documentation only when the relevant implementation ships. See [source reconciliation](../design/SOURCE-RECONCILIATION.md), [shared contracts](../design/CONTRACTS.md), and [references](../design/REFERENCES.md).

## Decision

Make the deployment understandable from the skill's point of view: where is this exact skill used, why is it selected, which content is active, and what will a proposed change affect? Build on planner observations instead of a second inventory database.

The first inventory view can be delivered against legacy deployments as soon as readiness lands. Full lock/source/profile/fleet fields follow their capabilities; unavailable fields are explicitly unknown, not made-up values. The complete acceptance boundary for this RFC includes pinned and layered selections.

## Public interface

```text
mask skill where-used SOURCE/ID [--agent AGENT] [--scope user|project] [--fleet]
mask inventory [--project PATH | --user | --all] [--include-unmanaged]
mask update report [--project PATH | --user | --all] [--skill SOURCE/ID ...]
mask diff SOURCE/ID --from RESOLUTION --to RESOLUTION [--patch]
mask report OPERATION_ID [--format text|json|html]
```

Reports are observational unless an explicit output file is selected. `--fleet` reads recorded fleet receipts unless a separate live-refresh option is requested and advertised as network-capable. Normal where-used does not SSH to every machine, search every filesystem, or fetch upstream refs. Results identify their selection boundary and completeness.

## Inventory model

Each row identifies repository/source alias, package path/id, artifact digest/revision, consumer root or stable device-local alias, scope, agent, desired and actual state, declaration/profile/bundle origin, compatibility decision, and last receipt/observation basis. One skill in user scope and three worktrees is four consumers, not four copies of its bytes. Same names from different sources stay distinct.

Show `declared_not_deployed`, `managed_converged`, `managed_drifted`, `unmanaged_present`, `unavailable_consumer`, `inapplicable`, `legacy_unpinned`, and `host_load_unknown` separately. Inspect unmanaged neighbors only in selected supported discovery directories; never recursively traverse linked neighbors or treat inventory as adoption authority. Cached manifests of unavailable consumers are diagnostic only.

The inverse view uses the existing registration/declaration/ownership model. It does not need a resident indexer or database. Optional fleet receipts extend scope with explicitly dated remote observations; they do not transform local inspection into current remote truth.

## Diff and impact

Compare exact old/new package manifests and bytes, including SKILL.md, supporting scripts, references, assets, machine-readable compatibility and provenance. Summarize added/removed/modified files; show binary-size/hash changes without dumping binary content. Text patches are opt-in and size-bounded. Disable external Git diff/textconv/filter commands and terminal escape sequences; output is untrusted content to be displayed, never instructions to execute.

For every content change, derive affected consumers and effective agent deployments even if link membership is unchanged. Pinned updates identify only consumers whose planned lock/artifact changes; consumers pinned to old versions are explicitly unaffected. Legacy live-source updates warn that all linked consumers observe shared content changes and running agents may cache instructions.

Distinguish selection change, content change, target/applicability change, provenance-only change and host discovery refresh requirement. A metadata restriction that makes a previously deployed agent incompatible must appear before activation. A source ref advance that resolves to identical selected payload bytes can be reported as provenance/ref movement without pretending the code changed.

Use the same exact candidate/plan object for preview and execution. Candidate identity and relevant content/consumer observations contribute to the plan hash; report formatting, report file path, wall-clock time and pagination do not. Generating a report is not approval, and a report cannot silently refetch a moving candidate.

## Human and agent UX

Default output is compact: changed skills, affected consumers, blockers, skipped/not-applicable targets, and next safe action. Provide structured pagination for large inventories and explicit `--all` for broad scope. Do not put the entire SKILL.md catalog into an agent's context. Human text and JSON share one result model.

A local HTML report is optional but useful for fleet rollout. It has no remote fonts/scripts, analytics, external resources or active shell links. Escape all package-controlled text and URLs. Redact credentials and sensitive local path details by policy; show source links only when explicitly requested for the audience. The report is a view of the durable operation/receipt, not another mutable status ledger.

## Performance and testing

Instrument representative cold/warm selected-scope queries, file counts and bytes read before adding caching. Unrelated repositories and skill payloads should not be read for a narrow where-used query. Read-only operations must not churn generation, fetch refs, alter links or create lock files. Test query results against actual fixtures with duplicate names, multiple scopes, pinned revisions, stale remote receipts and modified unmanaged content.

## Acceptance criteria

- **RFC-MASK-0011-AC01** — Where-used accurately joins source-qualified skill identities to each project/personal consumer, agent, origin and artifact, without conflating duplicate names or inferring unknown host loading.
- **RFC-MASK-0011-AC02** — Update reports include supporting-file/binary/metadata/provenance changes and affected consumers even when membership is unchanged, while distinguishing unaffected pinned consumers from legacy shared-source impact.
- **RFC-MASK-0011-AC03** — Reports and application use the same frozen candidate/plan; source/ref/control-file movement stales a guarded plan, while formatting changes do not.
- **RFC-MASK-0011-AC04** — Inspection preserves state and unmanaged content, scopes filesystem/network work explicitly, and labels unavailable consumers and stale fleet receipts.
- **RFC-MASK-0011-AC05** — Compact text/JSON and optional offline HTML safely display untrusted skill content with escaping/redaction; focused query workloads record actual bounded work.

## Live authorization

Accepted for implementation by the owner’s 2026-09-05 import-and-implement request. Follow the live card dependencies; native and external acceptance remain open until directly exercised.
