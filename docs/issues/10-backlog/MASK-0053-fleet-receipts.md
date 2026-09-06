---
schema: "implement-rfc.card.v1"
id: "MASK-0053"
title: "Track per-device completion failure and supersession"
status: "Backlog"
rfcs: ["RFC-MASK-0013"]
depends_on: ["MASK-0052"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "fleet-receipts", "stage": "D — personal fleet workflow", "provisional_id": false}
---

# MASK-0053: Track per-device completion failure and supersession

Governing RFC: [RFC-MASK-0013](../../rfcs/RFC-MASK-0013-fleet-rollouts-and-continuous-sync.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Add durable status/wait/report paths and exit9 incomplete semantics. Verify exact matching receipts and retain unknown/offline/recovery/skipped states. Handle apply-before-ack crash, lost controller response, cancel after partial apply and later desired revision supersession. Distinguish complete from installed_everywhere and host load.

Own only: `mask_fleet.py`, `mask_report.py`, `tests/test_fleet_receipts.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0013-AC03: Signed monotonic desired revisions and compare-and-swap publication handle two controllers, duplicate deliveries, replay, rollback-as-new-intent and revoked peers without silent last-writer overwrite.
- RFC-MASK-0013-AC04: Offline, unknown, incompatible, recovery-required, canceled and superseded devices are reported distinctly; incomplete rollouts never claim installed everywhere or reuse stale receipts.
- RFC-MASK-0013-AC07: Failure between import/publication/remote apply/receipt steps is resumable and truthful, and reports preserve the difference between filesystem verification and host discovery.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_fleet_receipts tests.test_report_rendering

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
