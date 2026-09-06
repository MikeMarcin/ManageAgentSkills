---
schema: "implement-rfc.card.v1"
id: "MASK-0035"
title: "Build isolated raw-byte artifacts and exact hydration"
status: "Backlog"
rfcs: ["RFC-MASK-0008"]
depends_on: ["MASK-0034", "MASK-0033"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "artifact-store", "stage": "B — reproducible content", "provisional_id": true}
---

# MASK-0035: Build isolated raw-byte artifacts and exact hydration

Governing RFC: [RFC-MASK-0008](../../rfcs/RFC-MASK-0008-pinned-artifacts-and-recovery.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Compute canonical payload manifests including supporting bytes/logical modes; stage and atomically publish digest directories without hardlinking authoring files. Validate preexisting artifacts and corruption. Hydrate only exact approved locked objects, including controller-forwarded packages later. Leave retention conservative and report cache effects separately.

Own only: `mask_store.py (new)`, `mask_git.py`, `tests/test_artifacts.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0008-AC01: Two worktrees simultaneously use distinct immutable versions of one skill, and source authoring/ref movement changes neither deployment until an explicit selected update.
- RFC-MASK-0008-AC02: Locks reproduce raw package bytes across fixture machines; digest, package path, source identity, executable mode, malformed lock and moved-ref errors fail closed.
- RFC-MASK-0008-AC03: Ensure restores available exact artifacts, optionally hydrates only approved locked content, never resolves latest or rewrites lockfiles, and reports unavailable exact commits honestly.
- RFC-MASK-0008-AC07: Cache preparation, retention, dev-link exceptions and scoped publishing cannot silently alter other consumers, delete authoring history or claim atomicity across readers/devices.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_artifacts
- Compare fixture raw bytes across independent roots and simulated platform mode mappings.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
