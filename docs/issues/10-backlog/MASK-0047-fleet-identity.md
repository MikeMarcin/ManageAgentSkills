---
schema: "implement-rfc.card.v1"
id: "MASK-0047"
title: "Implement local device enrollment and authorization records"
status: "Backlog"
rfcs: ["RFC-MASK-0012"]
depends_on: ["MASK-0069", "MASK-0070"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "fleet-identity", "stage": "D — enrolled fleet foundation", "provisional_id": false}
---

# MASK-0047: Implement local device enrollment and authorization records

Governing RFC: [RFC-MASK-0012](../../rfcs/RFC-MASK-0012-fleet-enrollment-and-transport.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Extend the shared command registrar/capability generator for the new nested fleet command paths without breaking existing leaf commands or argument/JSON behavior. Define device/controller IDs, local root mappings, allowed sources/actions, pinned host/signing identities and protocol negotiation. Use synthetic keys by default. Add explicit enroll/revoke/probe commands and establish initial epoch/high-water trust; no private key replication or host-key bypass.

Own only: `mask_fleet.py (new)`, `mask_identity.py (new)`, `tests/test_fleet_identity.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0012-AC01: Enrollment binds stable device/controller identities, permitted scopes/sources and host transport identity, and rejects changed/revoked/unknown peers without changing user SSH security settings.
- RFC-MASK-0012-AC06: Controller/device signing and receipt validation use the established provider with separate namespaces and no unsigned silent fallback for unattended requests.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_fleet_identity
- Temporary OpenSSH signing provider checks with synthetic keys.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
