---
schema: "implement-rfc.card.v1"
id: "MASK-0046"
title: "Add compact text JSON and offline HTML report renderers"
status: "Done"
rfcs: ["RFC-MASK-0011"]
depends_on: ["MASK-0045"]
metadata: {"packet":"mask-readiness-fleet-2026-09-05","packet_key":"report-render","stage":"C — explainability","provisional_id":false,"milestone_plan":{"id":"fleet-portable-composition","path":"docs/rfcs/plans/fleet-portable-composition/milestone-plan.json"}}
acceptance: [{"criterion":"RFC-MASK-0011-AC04","outcome":"pass","revision":"67e0c8451368d4dd4338f8a02a8e643998b952ed","evidence":{"kind":"command","detail":"Public inventory and where-used preserved fixture state and unmanaged files, scoped linked leaves, and did not fetch. An explicit fixture projection retained the UTC date and labeled an older desired revision stale_receipt. Missing fleet projection was unavailable. Stage D owns production of actual signed receipt observations."}},{"criterion":"RFC-MASK-0011-AC05","outcome":"pass","revision":"67e0c8451368d4dd4338f8a02a8e643998b952ed","evidence":{"kind":"command","detail":"Public text and HTML report views, saved JSON, escaped filename, omitted package text and local paths, preserved destination collision and verified the same guard across output and pagination. First and repeated narrow queries each read 738 declaration and 1514 lock bytes, one leaf, zero package files/bytes and zero Git scans."}}]
---

# MASK-0046: Add compact text JSON and offline HTML report renderers

Governing RFC: [RFC-MASK-0011](../../rfcs/RFC-MASK-0011-inventory-and-update-impact.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Produce compact paginated views from one result object, escaping terminal/HTML content and redacting sensitive data. No network assets or unsafe action links. Record selected-query work/bytes and preserve observational no-op state. Add fleet receipt rendering once RFC0013 supplies records.

Own only: `mask_report.py`, `tests/test_report_rendering.py (new)`, `docs/architecture/cli-contract.md`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0011-AC04: Inspection preserves state and unmanaged content, scopes filesystem/network work explicitly, and labels unavailable consumers and stale fleet receipts.
- RFC-MASK-0011-AC05: Compact text/JSON and optional offline HTML safely display untrusted skill content with escaping/redaction; focused query workloads record actual bounded work.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_report_rendering tests.test_inventory

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
