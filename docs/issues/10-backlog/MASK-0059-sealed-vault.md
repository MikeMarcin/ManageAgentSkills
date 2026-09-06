---
schema: "implement-rfc.card.v1"
id: "MASK-0059"
title: "Add opt-in established-provider encrypted vault delivery"
status: "Backlog"
rfcs: ["RFC-MASK-0015"]
depends_on: ["MASK-0058", "MASK-0074"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "sealed-vault", "stage": "E — optional credential extension", "provisional_id": false}
---

# MASK-0059: Add opt-in established-provider encrypted vault delivery

Governing RFC: [RFC-MASK-0015](../../rfcs/RFC-MASK-0015-credential-providers-and-vault.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Use an explicitly pinned established encryption provider and separate signature authority. Bind ciphertext/recipient/purpose digests; retain device-local private keys, explicit unlock policies and safe plaintext exposure boundaries. No handwritten cipher/format or plaintext fallback.

Own only: `optional/credentials/*`, `tests/test_sealed_vault.py (new)`, `optional dependency manifest`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0015-AC02: An optional sealed provider uses a pinned established encryption/signature implementation and enforces explicit recipient/purpose grants without plaintext in portable data or tool responses.
- RFC-MASK-0015-AC04: Synthetic-secret leakage checks and actual selected native provider tests support the advertised exposure boundary; production credential changes are not part of fixture acceptance.

Proposed direct checks (not executed by this packet):

- Run synthetic multi-recipient encryption/decryption, tamper/signature and leak checks with temporary keys.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
