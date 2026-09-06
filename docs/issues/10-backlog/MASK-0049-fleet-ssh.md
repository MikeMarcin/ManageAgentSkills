---
schema: "implement-rfc.card.v1"
id: "MASK-0049"
title: "Add fixed-entrypoint SSH and exact artifact transfer"
status: "Backlog"
rfcs: ["RFC-MASK-0012"]
depends_on: ["MASK-0048"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "fleet-ssh", "stage": "D — enrolled fleet foundation", "provisional_id": false}
---

# MASK-0049: Add fixed-entrypoint SSH and exact artifact transfer

Governing RFC: [RFC-MASK-0012](../../rfcs/RFC-MASK-0012-fleet-enrollment-and-transport.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Invoke only an enrolled fixed remote launcher with platform-specific remote-command quoting, bounded timeouts and no agent forwarding. Send payload through stdin frames; transfer selected digest-validated content when device source auth is absent. Preserve remote unknown outcome after transport timeout.

Own only: `mask_transport.py (new)`, `mask_rpc.py`, `tests/test_fleet_transport.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0012-AC02: Bounded framed RPC accepts only the fixed action schema; malformed messages, shell metacharacters, wrong device IDs and arbitrary paths cannot invoke generic remote execution.
- RFC-MASK-0012-AC03: Each remote mutation uses the ordinary local planner/lock/journal; duplicate operation IDs, changed payloads, disconnects and timeouts produce queryable truthful outcomes.
- RFC-MASK-0012-AC04: Exact package transfer validates paths/digests and never forwards credentials or unrelated private content; unavailable authentication remains a prerequisite.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_fleet_transport tests.test_fleet_rpc

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
