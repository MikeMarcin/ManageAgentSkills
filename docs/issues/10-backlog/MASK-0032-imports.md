---
schema: "implement-rfc.card.v1"
id: "MASK-0032"
title: "Add curated copy imports with verifiable provenance"
status: "Backlog"
rfcs: ["RFC-MASK-0007"]
depends_on: ["MASK-0031"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "imports", "stage": "B — source foundation", "provisional_id": false}
---

# MASK-0032: Add curated copy imports with verifiable provenance

Governing RFC: [RFC-MASK-0007](../../rfcs/RFC-MASK-0007-sources-imports-and-provenance.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Prepare exact packages outside discovery, preserve notices and upstream coordinate/commit/digests, then write only selected new curated paths. Refuse unknown existing content. Record adaptation without guessing unknown history. Return changed paths without default commit/push; define the scoped publication seam for later fleet use.

Own only: `mask_sources.py`, `mask_provenance.py (new)`, `tests/test_imports.py (new)`, `tests/test_provenance.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0007-AC03: Copy import preserves byte provenance and notices, refuses existing unrelated destinations, records local adaptations, and performs no commit/push unless separately authorized.
- RFC-MASK-0007-AC06: Public CLI/capabilities describe resolution, catalog-only addition, mutation/network boundaries and provenance verification levels with deterministic errors.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_imports tests.test_provenance

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
