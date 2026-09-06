---
schema: "implement-rfc.card.v1"
id: "MASK-0048"
title: "Implement bounded remote protocol and idempotent local dispatch"
status: "Backlog"
rfcs: ["RFC-MASK-0012"]
depends_on: ["MASK-0047"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "fleet-rpc", "stage": "D — enrolled fleet foundation", "provisional_id": true}
---

# MASK-0048: Implement bounded remote protocol and idempotent local dispatch

Governing RFC: [RFC-MASK-0012](../../rfcs/RFC-MASK-0012-fleet-enrollment-and-transport.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Use framed typed actions to invoke the local engine only. Validate intended device, signer, action scope, lengths and schemas. Persist operation IDs/digests transactionally and recover receipt publication after apply. Disconnects remain queryable unknown outcomes; no generic exec endpoint.

Own only: `mask_rpc.py (new)`, `mask_fleet.py`, `mask_fs.py`, `tests/test_fleet_rpc.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0012-AC02: Bounded framed RPC accepts only the fixed action schema; malformed messages, shell metacharacters, wrong device IDs and arbitrary paths cannot invoke generic remote execution.
- RFC-MASK-0012-AC03: Each remote mutation uses the ordinary local planner/lock/journal; duplicate operation IDs, changed payloads, disconnects and timeouts produce queryable truthful outcomes.
- RFC-MASK-0012-AC06: Controller/device signing and receipt validation use the established provider with separate namespaces and no unsigned silent fallback for unattended requests.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_fleet_rpc tests.test_pinned_recovery

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
