---
schema: "implement-rfc.card.v1"
id: "MASK-0034"
title: "Implement portable v2 selections and exact resolution locks"
status: "Backlog"
rfcs: ["RFC-MASK-0008"]
depends_on: ["MASK-0068"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "lock-model", "stage": "B — reproducible content", "provisional_id": true}
---

# MASK-0034: Implement portable v2 selections and exact resolution locks

Governing RFC: [RFC-MASK-0008](../../rfcs/RFC-MASK-0008-pinned-artifacts-and-recovery.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Implement closed normalized selection/lock models and a commit/ref resolver with full source/path/object identities. Preserve all selected package resolutions across platforms. Target fields follow RFC0009 and must not be advertised operationally until implemented. Missing/stale locks block v2 ensure; refresh stays explicit and cached-ref dry runs stay offline.

Own only: `mask_resolve.py (new)`, `mask_core.py`, `schemas/project-v2.schema.json (new)`, `schemas/lock-v1.schema.json (new)`, `tests/test_locks.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0008-AC01: Two worktrees simultaneously use distinct immutable versions of one skill, and source authoring/ref movement changes neither deployment until an explicit selected update.
- RFC-MASK-0008-AC02: Locks reproduce raw package bytes across fixture machines; digest, package path, source identity, executable mode, malformed lock and moved-ref errors fail closed.
- RFC-MASK-0008-AC03: Ensure restores available exact artifacts, optionally hydrates only approved locked content, never resolves latest or rewrites lockfiles, and reports unavailable exact commits honestly.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_locks tests.test_cli_protocol

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
