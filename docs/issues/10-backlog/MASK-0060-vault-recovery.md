---
schema: "implement-rfc.card.v1"
id: "MASK-0060"
title: "Verify vault rotation revocation and recovery limitations"
status: "Backlog"
rfcs: ["RFC-MASK-0015"]
depends_on: ["MASK-0059"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "vault-recovery", "stage": "E — optional credential extension", "provisional_id": false}
---

# MASK-0060: Verify vault rotation revocation and recovery limitations

Governing RFC: [RFC-MASK-0015](../../rfcs/RFC-MASK-0015-credential-providers-and-vault.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Exercise offline/revoked recipients, staged rotation, recovery recipient and lost-key refusal. Do not claim removing access erases already copied plaintext. Keep production token revocation separate from fixtures and never retire working credentials on stale receipts.

Own only: `optional/credentials/*`, `tests/test_vault_rotation.py (new)`, `docs/development/vault-acceptance.md (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0015-AC03: Locked/unavailable providers, rotation, revoked/offline recipients and recovery-key loss produce accurate outcomes rather than silent fallback or premature completion.
- RFC-MASK-0015-AC04: Synthetic-secret leakage checks and actual selected native provider tests support the advertised exposure boundary; production credential changes are not part of fixture acceptance.

Proposed direct checks (not executed by this packet):

- Run synthetic rotation/revocation/recovery tests and record actual provider/native boundaries.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
