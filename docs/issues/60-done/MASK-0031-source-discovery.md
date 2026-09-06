---
schema: "implement-rfc.card.v1"
id: "MASK-0031"
title: "Resolve skill URLs and bounded indexed/nested packages"
status: "Done"
rfcs: ["RFC-MASK-0007"]
depends_on: ["MASK-0030"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "source-discovery", "stage": "B — source foundation", "provisional_id": false}
acceptance: [{"criterion":"MASK-0031/discovery","outcome":"pass","revision":"d45a8811860b6d03ced50d912a472dcd66df38e3","evidence":{"kind":"observation","detail":"Public subprocess root, flat and indexed nested sources, exact paths, duplicate names and overlaps passed. No deployment performed."}},{"criterion":"MASK-0031/resolution","outcome":"pass","revision":"d45a8811860b6d03ced50d912a472dcd66df38e3","evidence":{"kind":"observation","detail":"Frozen SHA-1/SHA-256 object identities, historical refs, unavailable exact commit refusal, slash-ref and branch/tag ambiguity, and offline previews passed."}},{"criterion":"MASK-0031/authority","outcome":"pass","revision":"d45a8811860b6d03ced50d912a472dcd66df38e3","evidence":{"kind":"observation","detail":"Only configured sources are inspected; index authority injection refuses. Existing redirect and SSH regression tests pass."}},{"criterion":"MASK-0031/public-contract","outcome":"pass","revision":"d45a8811860b6d03ced50d912a472dcd66df38e3","evidence":{"kind":"observation","detail":"Capabilities and CLI expose explicit inspect network/dry-run boundaries, qualified selection, resolution_required and metadata_only status."}}]
---

# MASK-0031: Resolve skill URLs and bounded indexed/nested packages

Governing RFC: [RFC-MASK-0007](../../rfcs/RFC-MASK-0007-sources-imports-and-provenance.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

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

Implemented at `d45a8811860b6d03ced50d912a472dcd66df38e3`.

- `python3 -B -m unittest tests.test_source_discovery tests.test_sources tests.test_cli_protocol`: 19 passed on macOS in 20.695s. Public subprocess fixtures cover independent root/nested taps, duplicate qualified names, cached previews, exact historical commits, unreachable commits, unapproved sources, passive index boundaries, and branch/tag ambiguity. GitHub URL splitting is checked against locally fetched refs without an external GitHub connection.
- Final SHA-256 and alias selection addition: `python3 -B -m unittest tests.test_source_discovery.DiscoveryTests.test_sha256_objects_and_explicit_catalog_alias`: one passed in 1.069s.
- `git diff --check`: passed. Native Windows is not yet asserted for this slice. All temporary fixture roots were cleaned by the test harness.

Inspection reports `metadata_only`; full payload validation, import safety and
pre-allocation resource limits remain on MASK-0033. Copy/provenance remains on
MASK-0032. This card is not RFC-0007 closeout. Configured catalog cursors remain
unchanged when inspecting another frozen ref.

## Bounded implementation plan

Continue the owner-authorized dependency path to RFCs 0012/0013. Resolve approved
source URLs and frozen cached Git objects, add root/flat/indexed nested package
coordinates and typed name/ref/path ambiguity. Network inspection is explicit;
read-only commands and dry-run never fetch. Extend ownership to `mask.py`
registrar/dispatch, shipped source-index schema and current public docs.
Package extraction/import and the full adversarial resource policy remain on
MASK-0032/0033. Preserve old v1 CLI behavior; multi-source queries use explicit
approved config v2 and report missing cached resolution.
