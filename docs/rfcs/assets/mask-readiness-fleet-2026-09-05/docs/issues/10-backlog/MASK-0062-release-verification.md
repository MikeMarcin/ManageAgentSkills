---
schema: "implement-rfc.card.v1"
id: "MASK-0062"
title: "Prepare optional reproducible release and signature verification"
status: "Backlog"
rfcs: ["RFC-MASK-0016"]
depends_on: ["MASK-0061"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "release-verification", "stage": "E — stretch public assurance", "provisional_id": true}
---

# MASK-0062: Prepare optional reproducible release and signature verification

Governing RFC: [RFC-MASK-0016](../../rfcs/RFC-MASK-0016-public-trust-and-supply-chain-hardening.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

After a real owner distribution/license decision, select established signing/attestation tooling, pin CI dependencies and define independent trust bootstrap. Create synthetic release fixtures and reproducible verification instructions without uploading a public release or changing visibility.

Own only: `release tooling (new, scoped)`, `docs/security/release-verification.md (new)`, `tests/test_release_verification.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0016-AC02: Core boundary tests and provider/dependency inventory are reused in a compact trust report that labels dirty/unsigned/unverified conditions truthfully.
- RFC-MASK-0016-AC03: A proposed public release has an explicitly authorized distribution/license decision, independently bootstrapped artifact verification and reproducible verification instructions; no publication is assumed.

Proposed direct checks (not executed by this packet):

- Verify a synthetic artifact and signature, modified artifact refusal and explicit trust-root selection.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
