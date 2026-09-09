---
schema: "implement-rfc.card.v1"
id: "MASK-0083"
title: "Import and capture the actual broken public journeys"
status: "In Progress"
rfcs: ["RFC-MASK-0018", "RFC-MASK-0019"]
depends_on: []
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": false, "packet_key": "import-and-public-regression-baseline"}
---

# MASK-0083: Import and capture the actual broken public journeys

Governing RFCs: [RFC-MASK-0018](../../rfcs/RFC-MASK-0018-task-oriented-cli-and-human-output.md), [RFC-MASK-0019](../../rfcs/RFC-MASK-0019-complete-workflow-readiness.md). Live IDs confirmed by the committed pack reservation `6d80121`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-ux-readiness.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-ux-readiness/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-ux-readiness/ACCEPTANCE.md).

## Objective and owned paths

Intake, the two new RFC families and index additions, new cards, scoped test fixtures and baseline record. Integrator owns allocation/reservations; no unrelated tracker history changes.

## Bounded work

Reconcile live source against supplied snapshots. Establish the current non-JSON result behavior and the new-skill/old-role readiness gap. Record source deltas and real baseline SHAs. Add public regression fixtures before any renderer/setup preconditions are installed; retain failures as baseline evidence, not synthetic product passes.

## Acceptance

One fresh unregistered project, one user scope and one already linked consumer with missing/stale roles exist as test starting states. Only source/launcher prerequisites may be prepared. Record the actual command and failing expectation for each defect. A baseline fixture must not automatically register, approve or render away the behavior being tested.

Criterion coverage: RFC-MASK-0018-AC02, RFC-MASK-0018-AC08, RFC-MASK-0019-AC01, RFC-MASK-0019-AC07.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary. Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation, and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Not started. Claim the live remapped card before edits. No code implementation,
native result, host loading, user approval, or quota improvement is asserted.
