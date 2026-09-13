---
id: "RFC-MASK-0020"
title: "Personal-scope workflow readiness for external implement-rfc state"
status: "Implementing"
---

# RFC-MASK-0020: Personal-scope workflow readiness

Accepted run `personal-mode-20260913`, mandate revision 1. AgentSkills [RFC-ASK-0013](https://github.com/MikeMarcin/AgentSkills/blob/main/docs/rfcs/RFC-ASK-0013-personal-implement-rfc-storage.md) owns the canonical skill and external tracker behavior. [MASK-0099](../issues/30-in-progress/MASK-0099-close-personal-workflow-readiness.md) records the baseline, actual handoff and current status. Existing RFC-MASK-0019 work is retained.

## Decision

Extend the generic workflow descriptor/readiness contract with scope-specific requirements. Project scope retains consumer inputs and roles. Personal scope prepares canonical shared roles without treating the user's home as a Git consumer or writing target-project configuration. Personal preflight checks role files and the selected source/tracker binding, with installed-file state distinct from observed host loading. Preserve collisions, exact setup authorization, existing route checks, managed ownership and current project behavior. Do not grant this checkout persistent integration approval or alter existing consumers.

## Acceptance criteria

- **RFC-MASK-0020-AC01 — Scope-specific descriptor.** The passive contract expresses different project and personal prerequisites without a hard-coded implement-rfc exception; invalid or ambiguous descriptors refuse.
- **RFC-MASK-0020-AC02 — Personal readiness.** Personal roles are prepared from the canonical source without home-as-project assumptions; preflight checks roles and source/tracker binding and reports missing/stale conditions truthfully.
- **RFC-MASK-0020-AC03 — Existing safeguards.** Project readiness, collision protection, exact setup authorization, route checks, no script execution during passive checks and managed-file ownership remain intact.
- **RFC-MASK-0020-AC04 — Integrated qualification.** Disposable public CLI scenarios exercise both scopes and actual cross-repository handoff revisions; native loading remains separately evidenced or open.

No push, persistent permission/credential grant or unrelated consumer migration is authorized.
