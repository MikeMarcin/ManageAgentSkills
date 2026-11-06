---
schema: "implement-rfc.card.v1"
id: "MASK-0151"
title: "Report already-current fleet project scopes without a Git upgrade"
status: "In Progress"
rfcs: ["RFC-MASK-0025"]
depends_on: ["MASK-0149"]
---

# MASK-0151: Report already-current fleet project scopes without a Git upgrade

Follow-up to [MASK-0149](../60-done/MASK-0149-fleet-command-maintenance.md)
under [RFC-MASK-0025](../../rfcs/RFC-MASK-0025-fleet-command-maintenance.md).
Source baseline `95b5b8a87f8367e8811356dcf65f95a858b0576f`.

The fleet dry run checks canonical Git eligibility before finding out whether
each otherwise blocked project needs a lock update.

- AC1. Report an independently resolved, already-current project scope as
  complete without a request to apply, repair or commit it.
- AC2. Keep scopes that need changes subject to the existing blockers and
  preserve ordinary canonical fast-forward and cherry-pick behavior. Signed
  scope inspection and source authorization still apply.

Verify through the public command with disposable repositories and signed
subprocess delivery.
