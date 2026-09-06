---
schema: "implement-rfc.card.v1"
id: "MASK-0023"
title: "Reconcile live sources and import the staged RFC pack"
status: "Done"
rfcs: ["RFC-MASK-0017"]
depends_on: []
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "import", "stage": "A–D — integration and owner workflow", "provisional_id": false}
acceptance: [{"criterion":"RFC-MASK-0017-AC01","outcome":"pass","revision":"499a1f5a20cc9fae8134586d36e2fa33f5fdb114","evidence":{"kind":"observation","detail":"Reservation committed at 9dc90df before import b185a15; IDs map identically, original pack retained, 12 closeouts have immutable baseline, historical RFC/card bytes preserved. Structure gate: 17 RFCs, 80 cards; 0 violations."}}]
---

# MASK-0023: Reconcile live sources and import the staged RFC pack

Governing RFC: [RFC-MASK-0017](../../rfcs/RFC-MASK-0017-integration-and-personal-dogfood.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Inspect live Git root, board/counter/history and canonical implement-rfc context. Reserve actual IDs on main with the existing allocator and commit its receipt before use. Remap every packet reference, merge index rows, record LIVE_IMPORT, and capture real pre-implementation baselines on closeouts. Preserve settled records and private repositories. Do not install hooks, enroll devices or migrate unrelated consumers during import.

Own only: `docs/rfcs/README.md`, `docs/issues/NEXT_ID`, `docs/issues/_reservations/*`, `docs/design/*`, `live imported RFCs/cards`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0017-AC01: Live import preserves historical RFCs/cards/counters, uses real reservations and baseline commits, and imports one closeout per RFC with no fabricated evidence.

Proposed direct checks (not executed by this packet):

- python -B scripts/verify_documentation.py --root .
- Review actual reservation/LIVE_IMPORT mapping and preserved historical IDs.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
