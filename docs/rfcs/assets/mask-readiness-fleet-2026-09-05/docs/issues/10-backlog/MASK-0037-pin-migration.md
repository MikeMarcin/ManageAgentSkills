---
schema: "implement-rfc.card.v1"
id: "MASK-0037"
title: "Add explicit legacy migration and pinned update operations"
status: "Backlog"
rfcs: ["RFC-MASK-0008"]
depends_on: ["MASK-0036"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "pin-migration", "stage": "B — reproducible content", "provisional_id": true}
---

# MASK-0037: Add explicit legacy migration and pinned update operations

Governing RFC: [RFC-MASK-0008](../../rfcs/RFC-MASK-0008-pinned-artifacts-and-recovery.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Preserve dirty/unborn sources and old recovery. Implement reviewed program upgrade then explicit selected-scope migration, dev-link escape hatch, targeted pinned update and legacy all-source behavior. Source publication uses isolated worktree/exact paths under explicit authority. No hidden schema migration or reset.

Own only: `mask.py`, `mask_resolve.py`, `mask_install.py`, `mask_git.py`, `tests/test_pin_migration.py (new)`, `tests/test_pinned_update.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0008-AC05: Interruptions before/after lock, link and state effects preserve bounded v3 recovery; configuration/state migrations preserve exact legacy rollback bytes and reject concurrent edits.
- RFC-MASK-0008-AC06: Explicit migration covers project and personal consumers, dirty/unborn sources, old pending journals, schema-incompatible old programs, and direct-entrypoint escape paths.
- RFC-MASK-0008-AC07: Cache preparation, retention, dev-link exceptions and scoped publishing cannot silently alter other consumers, delete authoring history or claim atomicity across readers/devices.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_pin_migration tests.test_pinned_update tests.test_launcher

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
