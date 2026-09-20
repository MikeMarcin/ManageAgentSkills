---
schema: "implement-rfc.card.v1"
id: "MASK-0119"
title: "Inspect approved development links without reconciliation"
status: "Ready"
rfcs: ["RFC-MASK-0023"]
depends_on: ["MASK-0116"]
---

# MASK-0119: Development readiness check

Support the owner's local simple-milestone default deployment in AgentSkills
ASK-0088. `ensure --check` currently rejects an explicit managed development link
before inspecting selected requirements, even though the operation is read-only.

## Acceptance

- **AC1:** Read-only readiness can inspect approved development links and reports
  `ready_dev_link` separately from pinned readiness, in project and personal scope.
- **AC2:** Missing inputs, role requirements, unapproved roots and link drift still
  fail. Inspection performs no setup or state writes. Mutating reconciliation still
  refuses a development override.
- **AC3:** Public CLI fixtures and focused readiness regressions pass.

No source fetching, permission changes, publication or unrelated consumer changes.
