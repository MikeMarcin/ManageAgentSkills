---
schema: "implement-rfc.card.v1"
id: "MASK-0078"
title: "Verify and close RFC-MASK-0017"
status: "Backlog"
rfcs: ["RFC-MASK-0017"]
depends_on: ["MASK-0023", "MASK-0064", "MASK-0065", "MASK-0066"]
closeout_for: ["RFC-MASK-0017"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "close-17", "stage": "A–D — integration and owner workflow", "provisional_id": true, "closeout": true}
---

# MASK-0078: Verify and close RFC-MASK-0017

Governing RFC: [RFC-MASK-0017](../../rfcs/RFC-MASK-0017-integration-and-personal-dogfood.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Reconcile every acceptance criterion against direct evidence at the stated boundary. Capture the real pre-implementation RFC_BASE_SHA and actual implementation/handoff commits. Reuse unchanged focused results; run a broader integration/review only where combined risk warrants it. Keep unavailable native, host, real-device or upstream handoff rows open. Do not claim packet validation as product acceptance.

Own only: `docs/rfcs/RFC-MASK-0017-integration-and-personal-dogfood.md`, `the corresponding live closeout card`, `current affected public contract docs`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0017-AC01: Live import preserves historical RFCs/cards/counters, uses real reservations and baseline commits, and imports one closeout per RFC with no fabricated evidence.
- RFC-MASK-0017-AC02: Readiness, multi-source/pinning/targeting, composition/reporting and fleet milestones have focused integrated evidence and current public docs/capabilities that match what shipped.
- RFC-MASK-0017-AC03: Actual canonical AgentSkills management guidance and selected metadata/bundle/provenance handoffs are recorded by upstream revision and verified locally without duplicate tracker ownership.
- RFC-MASK-0017-AC04: Explicit selected-scope migrations preserve declarations, user data, ownership/recovery and source history on native macOS/Windows; unknown/unavailable acceptance stays open.
- RFC-MASK-0017-AC05: The real one-request fleet story demonstrates exact revisions, online/offline reporting and catch-up on distinct devices; optional MCP/vault/public-release work remains separately tracked and does not falsify core status.

Proposed direct checks (not executed by this packet):

- python -B scripts/verify_documentation.py --root .
- Only missing or invalidated direct acceptance checks for this RFC.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Durable closeout anchor

RFC_BASE_SHA: UNRECORDED — capture actual live pre-implementation commit before source changes.

Planned cards: MASK-0023, MASK-0064, MASK-0065, MASK-0066.

Cross-repository handoff: unrecorded; attach only an actual upstream ID/revision when required.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0017-AC01 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0017-AC02 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0017-AC03 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0017-AC04 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0017-AC05 | Not recorded | Not run | Unrecorded |

Closeout review runtime: not run. A skipped required native/host/device check leaves the criterion open.
