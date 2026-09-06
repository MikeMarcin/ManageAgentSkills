---
schema: "implement-rfc.card.v1"
id: "MASK-0042"
title: "Implement flat named bundle expansion and guarded refresh"
status: "Backlog"
rfcs: ["RFC-MASK-0010"]
depends_on: ["MASK-0041"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "bundles", "stage": "C — portable composition", "provisional_id": true}
---

# MASK-0042: Implement flat named bundle expansion and guarded refresh

Governing RFC: [RFC-MASK-0010](../../rfcs/RFC-MASK-0010-portable-selections-and-bundles.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Expand source-revision-bound bundles to explicit binding sets. Preserve manual target intent and overlapping membership, report conflicts, require source approval, stale changed definitions, and avoid naive bundle deletion/dependency execution.

Own only: `mask_profiles.py`, `mask_sources.py`, `tests/test_bundles.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0010-AC02: Incremental and replace modes preserve their declared ownership scopes; exported all-agent behavior and optional frozen-agent behavior are explicit and tested.
- RFC-MASK-0010-AC03: Bundle expansion/refresh is deterministic, source-revision bound and stale-plan guarded; overlapping bundles/manual selections do not cause accidental removals.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_bundles tests.test_profiles

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
