---
schema: "implement-rfc.card.v1"
id: "MASK-0024"
title: "Add one authorized ensure path over the existing reconciler"
status: "Backlog"
rfcs: ["RFC-MASK-0006"]
depends_on: ["MASK-0023"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "ensure-core", "stage": "A — first usable milestone", "provisional_id": true}
---

# MASK-0024: Add one authorized ensure path over the existing reconciler

Governing RFC: [RFC-MASK-0006](../../rfcs/RFC-MASK-0006-automatic-workspace-readiness.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Implement nearest-worktree selection, local approval policy and idempotent register-plus-reconcile. Keep normal operation legacy-source compatible and narrowly scoped. Preserve stale-plan, busy-lock, collision and pending-recovery behavior. Add compact ready/blocked output and a true observational --check path; normal ensure must not need an agent to copy a hash between commands.

Own only: `mask.py`, `mask_ensure.py (new)`, `mask_core.py`, `mask_fs.py`, `tests/test_ensure.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0006-AC02: Ensure combines authorization, registration and selected-scope reconciliation through the existing safety engine; unchanged runs preserve managed bytes/generation and perform no unrelated scans.
- RFC-MASK-0006-AC03: Untrusted roots, collisions, replaced parents, busy locks and pending recovery cannot be converted to success or silently repaired; hooks never claim to roll back completed Git actions.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_ensure tests.test_reconcile_plan tests.test_cli_protocol

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
