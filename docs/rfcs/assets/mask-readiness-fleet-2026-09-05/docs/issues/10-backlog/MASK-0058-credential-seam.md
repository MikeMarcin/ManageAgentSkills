---
schema: "implement-rfc.card.v1"
id: "MASK-0058"
title: "Implement credential handle providers without exporting values"
status: "Backlog"
rfcs: ["RFC-MASK-0015"]
depends_on: ["MASK-0073"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "credential-seam", "stage": "E — optional credential extension", "provisional_id": true}
---

# MASK-0058: Implement credential handle providers without exporting values

Governing RFC: [RFC-MASK-0015](../../rfcs/RFC-MASK-0015-credential-providers-and-vault.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Add named handles, probe/use-for-fixed-operation interface and native provider capability reports. Keep existing Git/SSH auth unchanged and avoid a generic secret getter. Portable data can describe requirements but not execute providers or select secret output paths.

Own only: `optional/credentials/* (new)`, `tests/test_credential_providers.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0015-AC01: Credential handles remain separate from values, and existing Git/SSH providers keep working without migration or a mandatory shared vault.
- RFC-MASK-0015-AC04: Synthetic-secret leakage checks and actual selected native provider tests support the advertised exposure boundary; production credential changes are not part of fixture acceptance.

Proposed direct checks (not executed by this packet):

- Run synthetic-secret provider and redaction tests, with actual native provider checks only where implemented.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
