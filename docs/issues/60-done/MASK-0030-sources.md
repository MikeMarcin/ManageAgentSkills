---
schema: "implement-rfc.card.v1"
id: "MASK-0030"
title: "Implement approved source identities and multi-source catalog"
status: "Done"
rfcs: ["RFC-MASK-0007"]
depends_on: ["MASK-0067"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "sources", "stage": "B — source foundation", "provisional_id": false}
acceptance: [{"criterion":"MASK-0030/catalog","outcome":"pass","revision":"e4bd35cd10551b1afba40a13dca3c6d19c5d4f7d","evidence":{"kind":"observation","detail":"Two independent bare sources, guarded catalog-only add/remove, alias conflicts and fetch effects passed via tests.test_sources; package discovery is explicitly deferred to MASK-0031."}},{"criterion":"MASK-0030/authority","outcome":"pass","revision":"e4bd35cd10551b1afba40a13dca3c6d19c5d4f7d","evidence":{"kind":"observation","detail":"URI-bound fetch/update, cache-local rewrite refusal, local HTTPS redirect refusal, and scp versus absolute SSH refusal passed; corrected reviewer findings exercised."}},{"criterion":"MASK-0030/migration","outcome":"pass","revision":"e4bd35cd10551b1afba40a13dca3c6d19c5d4f7d","evidence":{"kind":"observation","detail":"Exact declaration/state/link preservation, noncanonical config CAS, repeated init, explicit pending recovery and migration guards passed."}},{"criterion":"MASK-0030/public-contract","outcome":"pass","revision":"e4bd35cd10551b1afba40a13dca3c6d19c5d4f7d","evidence":{"kind":"observation","detail":"Source CLI and capabilities, readable machine versions, dry-run snapshots, errors, runtime module inventory and updater compatibility passed. Current docs updated to bounded shipped behavior."}}]
---

# MASK-0030: Implement approved source identities and multi-source catalog

Governing RFC: [RFC-MASK-0007](../../rfcs/RFC-MASK-0007-sources-imports-and-provenance.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

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

Implemented at `e4bd35cd10551b1afba40a13dca3c6d19c5d4f7d`.

This card closes only its catalog/migration slice. Exact package lookup,
root/nested discovery and ref/path ambiguity remain on MASK-0031; imports and
resource/package guards remain on MASK-0032/0033. The RFC acceptance rows stay
open until those slices are integrated.

- `python3 -B -m unittest tests.test_sources tests.test_git_update tests.test_launcher`: 20 passed on macOS in 28.535s, including local HTTPS redirect and SSH transport fixtures, noncanonical config migration, recovery, independent bare caches and legacy updater/launcher regression checks.
- `python3 -B -m unittest tests.test_cli_protocol`: four unchanged tests passed within the earlier combined run. Its one then-failing source-cache rewrite check was corrected and covered by the passing focused run above.
- Final scp tilde/option-path refusal: `python3 -B -m unittest tests.test_sources.SourcesTests.test_repository_normalization_keeps_authority_boundaries`: one passed in 0.265s.
- `git diff --check`: passed. Native Windows acceptance is not asserted for this new slice.

Closeout review runtime: independent `rfc-reviewer`, gpt-6-astra/high. Two
reproduced authority defects were corrected: URL-scoped redirect overrides and
scp relative versus SSH absolute repository paths. The passing tests above
exercise both corrections; no second review was run. All tests and reviewer
reproductions used disposable roots and cleaned them after consumption. The
pre-existing untracked `.DS_Store` remains untouched.

## Bounded implementation plan

Owner request prioritizes RFCs 0012/0013 with their dependency closure. This
source-catalog slice preserves the v1 local engine and adds explicit guarded
machine-v2 migration, credential-free repository identities, catalog-only tap
registration/removal and noninteractive managed bare-cache fetch. Package
discovery/import follows on MASK-0031/0032/0033; no deployment is implied by a tap.

Owned-path extension for the public path: `mask.py` registrar/dispatch,
`mask_install.py` runtime inventory, machine schema union and corresponding
launcher fixtures/current CLI contract documentation. Existing state and
declaration bytes remain unchanged during config migration. Use temporary
local bare repositories for direct CLI acceptance.
