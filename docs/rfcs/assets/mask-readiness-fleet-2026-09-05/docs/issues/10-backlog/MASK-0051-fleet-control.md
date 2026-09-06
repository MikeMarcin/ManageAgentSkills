---
schema: "implement-rfc.card.v1"
id: "MASK-0051"
title: "Implement signed desired state and conflict-safe control publication"
status: "Backlog"
rfcs: ["RFC-MASK-0013"]
depends_on: ["MASK-0071", "MASK-0073"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "fleet-control", "stage": "D — personal fleet workflow", "provisional_id": true}
---

# MASK-0051: Implement signed desired state and conflict-safe control publication

Governing RFC: [RFC-MASK-0013](../../rfcs/RFC-MASK-0013-fleet-rollouts-and-continuous-sync.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Persist portable profiles/locks and signed sequence/epoch/parent intent objects in an approved private Git store. Use compare-and-swap/ff publication, separate device receipt authority and explicit publish grants. Handle competing controllers, replay, old epochs and missing control freshness without last-writer overwrite.

Own only: `mask_control.py (new)`, `mask_fleet.py`, `tests/test_fleet_control.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0013-AC02: Frozen device/scope sets, local contribution preservation and source/package identity prevent unexpected project edits, hidden source enrollment or skill-name ambiguity.
- RFC-MASK-0013-AC03: Signed monotonic desired revisions and compare-and-swap publication handle two controllers, duplicate deliveries, replay, rollback-as-new-intent and revoked peers without silent last-writer overwrite.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_fleet_control tests.test_fleet_identity

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
