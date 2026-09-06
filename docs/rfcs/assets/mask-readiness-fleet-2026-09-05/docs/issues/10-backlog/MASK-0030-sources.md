---
schema: "implement-rfc.card.v1"
id: "MASK-0030"
title: "Implement approved source identities and multi-source catalog"
status: "Backlog"
rfcs: ["RFC-MASK-0007"]
depends_on: ["MASK-0067"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "sources", "stage": "B — source foundation", "provisional_id": true}
---

# MASK-0030: Implement approved source identities and multi-source catalog

Governing RFC: [RFC-MASK-0007](../../rfcs/RFC-MASK-0007-sources-imports-and-provenance.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Separate portable repository identity from machine transport/cache paths. Replace basename-only matching. Preserve legacy configuration through explicit migration. Add tap list/add/remove and exact qualified lookups; refuse ambiguous identities and referenced-source removal. Catalog registration is not deployment.

Own only: `mask_sources.py (new)`, `mask_core.py`, `mask_git.py`, `schemas/machine-v2.schema.json (new)`, `tests/test_sources.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0007-AC01: Two private/public-style local bare remotes expose independent taps and nested/root packages; name ambiguity, path/ref ambiguity and conflicting aliases are actionable rather than silently selected.
- RFC-MASK-0007-AC02: Source identity checks bind the approved repository and transport policy, not just the basename; credential-bearing/unsupported URLs and unapproved redirects refuse without leaking secrets.
- RFC-MASK-0007-AC05: Source lifecycle and legacy-config migration preserve current ownership and old declarations; removing a referenced source refuses and reads/dry-runs remain observational.
- RFC-MASK-0007-AC06: Public CLI/capabilities describe resolution, catalog-only addition, mutation/network boundaries and provenance verification levels with deterministic errors.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_sources tests.test_git_update tests.test_cli_protocol

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
