---
schema: "implement-rfc.card.v1"
id: "MASK-0043"
title: "Compose subscribed profile and local selection contributions"
status: "Backlog"
rfcs: ["RFC-MASK-0010"]
depends_on: ["MASK-0042"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "subscriptions", "stage": "C — portable composition", "provisional_id": true}
---

# MASK-0043: Compose subscribed profile and local selection contributions

Governing RFC: [RFC-MASK-0010](../../rfcs/RFC-MASK-0010-portable-selections-and-bundles.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Add explicit local subscriptions with independent local selection ownership. Merge equal exact bindings, refuse unapproved conflicts, preserve local requirements on unsubscribe, and expose offline revision freshness. Include native personal import-and-apply evidence, not just portable JSON equality.

Own only: `mask_profiles.py`, `mask_selection.py`, `mask_fs.py`, `tests/test_profile_contributions.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0010-AC01: Export/import round-trips selections and exact content locks between different machine/home/source paths without including credentials, registry identities, journals or launchers.
- RFC-MASK-0010-AC04: Profile subscription/removal preserves local contributions and reports version/target conflicts, unapproved sources, unavailable artifacts and offline freshness honestly.
- RFC-MASK-0010-AC05: One public import-and-apply path bootstraps selected personal scope through normal validation/recovery, with native Windows/macOS focused tests and no internal-state editing.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_profile_contributions tests.test_profiles
- Run focused native personal export/import checks.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
