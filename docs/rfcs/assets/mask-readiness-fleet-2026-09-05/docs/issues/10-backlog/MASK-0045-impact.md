---
schema: "implement-rfc.card.v1"
id: "MASK-0045"
title: "Explain exact content diffs and selected consumer impact"
status: "Backlog"
rfcs: ["RFC-MASK-0011"]
depends_on: ["MASK-0044", "MASK-0069", "MASK-0070", "MASK-0071"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "impact", "stage": "C — explainability", "provisional_id": true}
---

# MASK-0045: Explain exact content diffs and selected consumer impact

Governing RFC: [RFC-MASK-0011](../../rfcs/RFC-MASK-0011-inventory-and-update-impact.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Compare all raw package files and metadata, including binary summaries and origin changes. Derive impacted/unaffected consumers from the same frozen candidate as apply; retain legacy shared-source warning. Disable external diff/textconv; guard candidate changes independently of rendering.

Own only: `mask_report.py`, `mask_resolve.py`, `tests/test_update_impact.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0011-AC02: Update reports include supporting-file/binary/metadata/provenance changes and affected consumers even when membership is unchanged, while distinguishing unaffected pinned consumers from legacy shared-source impact.
- RFC-MASK-0011-AC03: Reports and application use the same frozen candidate/plan; source/ref/control-file movement stales a guarded plan, while formatting changes do not.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_update_impact tests.test_pinned_update

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
