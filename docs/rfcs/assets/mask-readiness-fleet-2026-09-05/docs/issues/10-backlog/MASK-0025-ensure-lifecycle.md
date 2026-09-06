---
schema: "implement-rfc.card.v1"
id: "MASK-0025"
title: "Implement branch inactivity and bounded readiness recovery"
status: "Backlog"
rfcs: ["RFC-MASK-0006"]
depends_on: ["MASK-0024"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "ensure-lifecycle", "stage": "A — first usable milestone", "provisional_id": true}
---

# MASK-0025: Implement branch inactivity and bounded readiness recovery

Governing RFC: [RFC-MASK-0006](../../rfcs/RFC-MASK-0006-automatic-workspace-readiness.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Add journal v3 readiness control-file expectations and safe inactive-branch deactivation without creating a manifest. Distinguish branch absence from local deletion, sparse/conflicted input and changed worktree identity. Add explicit verified worktree retirement; do not prune unavailable roots. Revalidate current branch/control files during recovery. Add busy/deadline behavior without lock takeover.

Own only: `mask_ensure.py`, `mask_fs.py`, `schemas/pending-v3.schema.json (new)`, `tests/test_workspace_lifecycle.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0006-AC03: Untrusted roots, collisions, replaced parents, busy locks and pending recovery cannot be converted to success or silently repaired; hooks never claim to roll back completed Git actions.
- RFC-MASK-0006-AC04: Inactive-branch handling distinguishes verified branch absence from deleted, sparse, unreadable or conflicted input; interrupted readiness refuses completion after its control files change.
- RFC-MASK-0006-AC07: Native Windows and macOS readiness/launcher paths receive focused direct checks; worktree removal and unavailable-root handling preserve ownership and are independently tested.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_workspace_lifecycle tests.test_recovery

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
