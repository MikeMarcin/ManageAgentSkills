---
schema: "implement-rfc.card.v1"
id: "MASK-0086"
title: "Deliver complete project and personal task commands"
status: "Backlog"
rfcs: ["RFC-MASK-0018"]
depends_on: ["MASK-0085"]
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": true, "packet_key": "complete-install-remove-list"}
---

# MASK-0086: Deliver complete project and personal task commands

## Objective and owned paths

mask.py command registration, mask_core/mask_fs/mask_pinned/mask_resolve selection/planning seams as needed, minimal mask_report pinned views, focused public tests.

## Bounded work

Implement install/remove/list as complete services rather than sequential CLI shellouts. Fold missing declaration/registration, scoped membership edit, new-binding resolution, preparation, engine activation and checks into the task. Handle legacy and pinned paths explicitly, retain unrelated exact pins/targets, and preserve checked-in context and other-scope selections. Limit report work to basic accurate list/inventory; do not wait for full impact reporting.

## Acceptance

A fresh project and first personal selection each need one task command after one-time source setup. A v2 add/remove does not hit the legacy selection.command_unsupported branch. Tests exercise source ambiguity, effective per-binding targeting, no-op reinstall, removal with edited files, and other-scope independence through actual subprocesses.

Criterion coverage: RFC-MASK-0018-AC01, RFC-MASK-0018-AC02, RFC-MASK-0018-AC06.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary. Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation, and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Not started. Claim the live remapped card before edits. No code implementation,
native result, host loading, user approval, or quota improvement is asserted.
