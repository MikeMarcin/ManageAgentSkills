---
schema: "implement-rfc.card.v1"
id: "MASK-0036"
title: "Retarget owned links and recover lock/artifact transitions"
status: "Backlog"
rfcs: ["RFC-MASK-0008"]
depends_on: ["MASK-0035"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "artifact-reconcile", "stage": "B — reproducible content", "provisional_id": true}
---

# MASK-0036: Retarget owned links and recover lock/artifact transitions

Governing RFC: [RFC-MASK-0008](../../rfcs/RFC-MASK-0008-pinned-artifacts-and-recovery.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Replace the old-target-retention assumption with separately validated old/current/new targets. Derive journal paths from typed roles and old/new artifact records. Integrate lock/declaration/link changes in bounded recovery; preserve old journal readers and no-op semantics. Crash injection covers each meaningful write boundary and subsequent branch movement.

Own only: `mask_fs.py`, `mask_core.py:state`, `schemas/state-v3.schema.json (new)`, `schemas/pending-v3.schema.json`, `tests/test_pinned_recovery.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0008-AC04: Planner/executor/adoption/recovery correctly retarget an unchanged owned legacy or old-artifact link to a new artifact and preserve collisions, rather than retaining the old target.
- RFC-MASK-0008-AC05: Interruptions before/after lock, link and state effects preserve bounded v3 recovery; configuration/state migrations preserve exact legacy rollback bytes and reject concurrent edits.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_pinned_recovery tests.test_reconcile_apply tests.test_recovery

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
