---
schema: "implement-rfc.card.v1"
id: "MASK-0031"
title: "Resolve skill URLs and bounded indexed/nested packages"
status: "Backlog"
rfcs: ["RFC-MASK-0007"]
depends_on: ["MASK-0030"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "source-discovery", "stage": "B — source foundation", "provisional_id": true}
---

# MASK-0031: Resolve skill URLs and bounded indexed/nested packages

Governing RFC: [RFC-MASK-0007](../../rfcs/RFC-MASK-0007-sources-imports-and-provenance.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Resolve repository/tree/blob URLs, slash-containing refs and package subpaths using frozen object identity. Support existing flat, root single-skill and indexed nested layouts without installing every match. Return bounded ambiguous candidates. Keep source metadata non-authoritative for trust.

Own only: `mask_sources.py`, `mask_git.py`, `tests/test_source_discovery.py (new)`, `contracts/source-index schema implementation`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0007-AC01: Two private/public-style local bare remotes expose independent taps and nested/root packages; name ambiguity, path/ref ambiguity and conflicting aliases are actionable rather than silently selected.
- RFC-MASK-0007-AC02: Source identity checks bind the approved repository and transport policy, not just the basename; credential-bearing/unsupported URLs and unapproved redirects refuse without leaking secrets.
- RFC-MASK-0007-AC06: Public CLI/capabilities describe resolution, catalog-only addition, mutation/network boundaries and provenance verification levels with deterministic errors.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_source_discovery
- Local bare fixtures cover ambiguous ref/path, duplicate names, unapproved source and unreachable exact object.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
