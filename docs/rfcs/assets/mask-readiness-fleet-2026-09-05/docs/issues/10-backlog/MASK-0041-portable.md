---
schema: "implement-rfc.card.v1"
id: "MASK-0041"
title: "Implement portable personal profile export and import"
status: "Backlog"
rfcs: ["RFC-MASK-0010"]
depends_on: ["MASK-0069", "MASK-0070"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "portable", "stage": "C — portable composition", "provisional_id": true}
---

# MASK-0041: Implement portable personal profile export and import

Governing RFC: [RFC-MASK-0010](../../rfcs/RFC-MASK-0010-portable-selections-and-bundles.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Export local or explicit effective selections plus exact locks with no local registry/secrets. Preserve all-agent defaults and optional freeze-agents. Import via incremental or explicit replacement semantics and one validated apply path; test two machines with different paths.

Own only: `mask_profiles.py (new)`, `mask.py`, `tests/test_profiles.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0010-AC01: Export/import round-trips selections and exact content locks between different machine/home/source paths without including credentials, registry identities, journals or launchers.
- RFC-MASK-0010-AC02: Incremental and replace modes preserve their declared ownership scopes; exported all-agent behavior and optional frozen-agent behavior are explicit and tested.
- RFC-MASK-0010-AC05: One public import-and-apply path bootstraps selected personal scope through normal validation/recovery, with native Windows/macOS focused tests and no internal-state editing.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_profiles tests.test_user_scope

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
