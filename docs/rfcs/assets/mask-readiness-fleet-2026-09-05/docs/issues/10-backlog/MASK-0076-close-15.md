---
schema: "implement-rfc.card.v1"
id: "MASK-0076"
title: "Verify and close RFC-MASK-0015"
status: "Backlog"
rfcs: ["RFC-MASK-0015"]
depends_on: ["MASK-0058", "MASK-0059", "MASK-0060"]
closeout_for: ["RFC-MASK-0015"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "close-15", "stage": "E — optional credential extension", "provisional_id": true, "closeout": true}
---

# MASK-0076: Verify and close RFC-MASK-0015

Governing RFC: [RFC-MASK-0015](../../rfcs/RFC-MASK-0015-credential-providers-and-vault.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Reconcile every acceptance criterion against direct evidence at the stated boundary. Capture the real pre-implementation RFC_BASE_SHA and actual implementation/handoff commits. Reuse unchanged focused results; run a broader integration/review only where combined risk warrants it. Keep unavailable native, host, real-device or upstream handoff rows open. Do not claim packet validation as product acceptance.

Own only: `docs/rfcs/RFC-MASK-0015-credential-providers-and-vault.md`, `the corresponding live closeout card`, `current affected public contract docs`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0015-AC01: Credential handles remain separate from values, and existing Git/SSH providers keep working without migration or a mandatory shared vault.
- RFC-MASK-0015-AC02: An optional sealed provider uses a pinned established encryption/signature implementation and enforces explicit recipient/purpose grants without plaintext in portable data or tool responses.
- RFC-MASK-0015-AC03: Locked/unavailable providers, rotation, revoked/offline recipients and recovery-key loss produce accurate outcomes rather than silent fallback or premature completion.
- RFC-MASK-0015-AC04: Synthetic-secret leakage checks and actual selected native provider tests support the advertised exposure boundary; production credential changes are not part of fixture acceptance.

Proposed direct checks (not executed by this packet):

- python -B scripts/verify_documentation.py --root .
- Only missing or invalidated direct acceptance checks for this RFC.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Durable closeout anchor

RFC_BASE_SHA: UNRECORDED — capture actual live pre-implementation commit before source changes.

Planned cards: MASK-0058, MASK-0059, MASK-0060.

Cross-repository handoff: unrecorded; attach only an actual upstream ID/revision when required.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0015-AC01 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0015-AC02 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0015-AC03 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0015-AC04 | Not recorded | Not run | Unrecorded |

Closeout review runtime: not run. A skipped required native/host/device check leaves the criterion open.
