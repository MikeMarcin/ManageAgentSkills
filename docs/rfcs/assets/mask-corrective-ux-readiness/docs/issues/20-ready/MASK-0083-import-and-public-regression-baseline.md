---
schema: "implement-rfc.card.v1"
id: "MASK-0083"
title: "Import and capture the actual broken public journeys"
status: "Ready"
rfcs: ["RFC-MASK-0018", "RFC-MASK-0019"]
depends_on: []
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": true, "packet_key": "import-and-public-regression-baseline"}
---

# MASK-0083: Import and capture the actual broken public journeys

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
