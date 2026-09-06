---
schema: "implement-rfc.card.v1"
id: "MASK-0046"
title: "Add compact text JSON and offline HTML report renderers"
status: "Backlog"
rfcs: ["RFC-MASK-0011"]
depends_on: ["MASK-0045"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "report-render", "stage": "C — explainability", "provisional_id": true}
---

# MASK-0046: Add compact text JSON and offline HTML report renderers

Governing RFC: [RFC-MASK-0011](../../rfcs/RFC-MASK-0011-inventory-and-update-impact.md). IDs are packet-local until the main integrator imports/reserves them.

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
