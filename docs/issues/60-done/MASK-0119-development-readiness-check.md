---
schema: "implement-rfc.card.v1"
id: "MASK-0119"
title: "Inspect approved development links without reconciliation"
status: "Done"
rfcs: ["RFC-MASK-0023"]
depends_on: ["MASK-0116"]
acceptance: [{"criterion":"AC1-AC3: read-only project/personal development readiness with existing guards","outcome":"pass","revision":"5c5c176baf659eedd56e13491f3e3ab5b49e8e81","evidence":{"kind":"command","detail":"32 tests passed: python3 -B -m unittest tests.test_workflow_profiles tests.test_ensure tests.test_workflow_scopes tests.test_pinned_update. AgentSkills public installed-link test passes in two disposable consumers. No setup or state writes during checks; mutating ensure still refuses dev links."}}]
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
