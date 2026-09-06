---
schema: "implement-rfc.card.v1"
id: "MASK-0038"
title: "Implement per-binding agent choices and compatibility metadata"
status: "Backlog"
rfcs: ["RFC-MASK-0009"]
depends_on: ["MASK-0036"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "target-model", "stage": "B — selection semantics", "provisional_id": true}
---

# MASK-0038: Implement per-binding agent choices and compatibility metadata

Governing RFC: [RFC-MASK-0009](../../rfcs/RFC-MASK-0009-scope-agent-targeting-and-compatibility.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Implement all/explicit agent semantics independently per consumer, machine-readable generic/specific/unspecified metadata and when filters. Explicit incompatible intent blocks; implicit all-agent restrictions report exclusions. Preserve v1 effective targets at migration and avoid installation-detection-based default changes.

Own only: `mask_selection.py (new)`, `mask_core.py`, `mask.py`, `tests/test_targeting.py (new)`, `tests/test_compatibility.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0009-AC01: The same skill has independently configurable personal and project agent sets, with new selections defaulting to all supported/enabled agents and no executable-detection side effects.
- RFC-MASK-0009-AC02: V1 migration preserves explicit and inherited target behavior; per-skill edits/locks/plans remain guarded and no-op stable.
- RFC-MASK-0009-AC03: Generic, absent and agent/platform-specific metadata produce distinct truthful reports; explicit incompatibilities block, and conditional/inapplicable bindings are not called installed.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_targeting tests.test_compatibility tests.test_user_scope

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
