---
schema: "implement-rfc.card.v1"
id: "MASK-0044"
title: "Expose skill-centric where-used and actual deployment inventory"
status: "Done"
rfcs: ["RFC-MASK-0011"]
depends_on: ["MASK-0024"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "inventory", "stage": "C — explainability", "provisional_id": false}
acceptance: [{"criterion":"RFC-MASK-0011-AC01","outcome":"pass","revision":"79c3d611709cf719bb30169adafdd73fdd5646d3","evidence":{"kind":"command","detail":"python3 -B -m unittest tests.test_inventory tests.test_manifest_registry tests.test_launcher: 14 tests passed. Direct CLI fixtures cover desired/owned/drifted rows, scope/agent filtering, pagination, unavailable cached selections, shallow unmanaged inspection, linked-parent refusal, and absent source targets. A narrow query inspected one leaf and one declaration with zero payload reads or Git scans. Full multi-source/pinned/profile/fleet fields remain explicitly unavailable until predecessor features ship."}},{"criterion":"RFC-MASK-0011-AC04","outcome":"pass","revision":"79c3d611709cf719bb30169adafdd73fdd5646d3","evidence":{"kind":"command","detail":"python3 -B -m unittest tests.test_inventory tests.test_manifest_registry tests.test_launcher: 14 tests passed. Direct CLI fixtures cover desired/owned/drifted rows, scope/agent filtering, pagination, unavailable cached selections, shallow unmanaged inspection, linked-parent refusal, and absent source targets. A narrow query inspected one leaf and one declaration with zero payload reads or Git scans. Full multi-source/pinned/profile/fleet fields remain explicitly unavailable until predecessor features ship."}},{"criterion":"RFC-MASK-0011-AC05","outcome":"pass","revision":"79c3d611709cf719bb30169adafdd73fdd5646d3","evidence":{"kind":"command","detail":"python3 -B -m unittest tests.test_inventory tests.test_manifest_registry tests.test_launcher: 14 tests passed. Direct CLI fixtures cover desired/owned/drifted rows, scope/agent filtering, pagination, unavailable cached selections, shallow unmanaged inspection, linked-parent refusal, and absent source targets. A narrow query inspected one leaf and one declaration with zero payload reads or Git scans. Full multi-source/pinned/profile/fleet fields remain explicitly unavailable until predecessor features ship."}}]
---

# MASK-0044: Expose skill-centric where-used and actual deployment inventory

Governing RFC: [RFC-MASK-0011](../../rfcs/RFC-MASK-0011-inventory-and-update-impact.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Start with the legacy registry and evolve additively to source-qualified/pinned/profile fields. Join desired/current/owned/inapplicable states without a second database or blind home scan. Unavailable consumer caches remain diagnostic; unmanaged inventory grants no authority.

Own only: `mask_report.py (new)`, `mask.py`, `tests/test_inventory.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0011-AC01: Where-used accurately joins source-qualified skill identities to each project/personal consumer, agent, origin and artifact, without conflating duplicate names or inferring unknown host loading.
- RFC-MASK-0011-AC04: Inspection preserves state and unmanaged content, scopes filesystem/network work explicitly, and labels unavailable consumers and stale fleet receipts.
- RFC-MASK-0011-AC05: Compact text/JSON and optional offline HTML safely display untrusted skill content with escaping/redaction; focused query workloads record actual bounded work.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_inventory tests.test_manifest_registry

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
