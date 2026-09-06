---
schema: "implement-rfc.card.v1"
id: "MASK-0063"
title: "Document and test signer rotation and future update-channel boundaries"
status: "Backlog"
rfcs: ["RFC-MASK-0016"]
depends_on: ["MASK-0062"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "trust-rotation", "stage": "E — stretch public assurance", "provisional_id": false}
---

# MASK-0063: Document and test signer rotation and future update-channel boundaries

Governing RFC: [RFC-MASK-0016](../../rfcs/RFC-MASK-0016-public-trust-and-supply-chain-hardening.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Test selected signer rotation/revocation. Evaluate mature TUF integration for any future automatic program channel, while leaving current program updates explicit. Record compromised-signer and malicious-approved-skill limits; no custom pseudo-TUF implementation.

Own only: `docs/security/key-lifecycle.md (new)`, `tests/test_release_verification.py`, `docs/security/update-channel-evaluation.md (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0016-AC01: Threat/effect documentation distinguishes integrity, authorization, deployment, host loading and content safety, with explicit non-goals and no universal safety claim.
- RFC-MASK-0016-AC04: Key rotation/revocation and update-channel rollback/freeze considerations are documented/tested at the selected provider boundary, without adding an unrequested automatic program updater.

Proposed direct checks (not executed by this packet):

- Run selected provider rotation/revocation fixtures; record evaluation conclusions separately from implemented behavior.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
