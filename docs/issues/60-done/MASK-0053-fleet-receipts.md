---
schema: "implement-rfc.card.v1"
id: "MASK-0053"
title: "Track per-device completion failure and supersession"
status: "Done"
rfcs: ["RFC-MASK-0013"]
depends_on: ["MASK-0052"]
metadata: {"packet":"mask-readiness-fleet-2026-09-05","packet_key":"fleet-receipts","stage":"D — personal fleet workflow","provisional_id":false,"milestone_plan":{"id":"fleet-skill-rollouts","path":"docs/rfcs/plans/fleet-skill-rollouts/milestone-plan.json"}}
acceptance: [{"criterion":"RFC-MASK-0013-AC03","outcome":"pass","revision":"c7680f8f1b1c1a2c774f8b1baac40fe8bee519fc","evidence":{"kind":"command","detail":"tests.test_fleet_control, tests.test_fleet_rpc and tests.test_fleet_receipts exercised competing same-parent publication, signed replay refusal, duplicate apply, recorded revocation, cancel and public rollback as a new higher sequence."}},{"criterion":"RFC-MASK-0013-AC04","outcome":"pass","revision":"c7680f8f1b1c1a2c774f8b1baac40fe8bee519fc","evidence":{"kind":"command","detail":"Public wait/cancel/status and injected lost receipt exercised queued, unknown, canceled and superseded results. Native candidate d1d87be preserved independent outcomes through offline updates, a controlled collision and latest-only catch-up."}},{"criterion":"RFC-MASK-0013-AC07","outcome":"pass","revision":"c7680f8f1b1c1a2c774f8b1baac40fe8bee519fc","evidence":{"kind":"command","detail":"A real device subprocess applied before the injected transport reply loss. The controller stayed unknown until an exact signed query resolved it, refused a tampered receipt, and rendered host load separately. The native rollout record contains the signed desired and receipt IDs."}}]
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
