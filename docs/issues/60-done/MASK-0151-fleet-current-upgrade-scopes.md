---
schema: "implement-rfc.card.v1"
id: "MASK-0151"
title: "Report already-current fleet project scopes without a Git upgrade"
status: "Done"
rfcs: ["RFC-MASK-0025"]
depends_on: ["MASK-0149"]
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"b489654b2858db9d822d328174e481b490df75b9","evidence":{"kind":"observation","detail":"Public fleet upgrade --all and selected-scope previews over signed subprocess RPC report current dirty and divergent scopes as no action. Approved disposable runs preserve branches, controls, staging and a missing link. The divergent scope retains its own pinned lock distinct from the canonical candidate. The selected no-op completes without a device apply request."}},{"criterion":"AC2","outcome":"pass","revision":"b489654b2858db9d822d328174e481b490df75b9","evidence":{"kind":"observation","detail":"The exact regression preserves dirty, divergent, commit-ineligible and signed local-drift blockers for scopes still needing work. The identical controller code at 0d0e885474f961fab4e1be88c2cc60f96fd5a3e2 passed 13 fleet maintenance, signed RPC and tap tests, including same-parent fast-forward and different-parent cherry-pick with unrelated staging preserved."}}]
---

# MASK-0151: Report already-current fleet project scopes without a Git upgrade

Follow-up to [MASK-0149](MASK-0149-fleet-command-maintenance.md)
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
