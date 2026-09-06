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

Own only: `mask_fleet.py (new)`, `mask_identity.py (new)`, `tests/test_fleet_identity.py (new)`, shared registrar/dispatch/capability integration in `mask.py`, runtime module inventory in `mask_install.py`/`tests/test_launcher.py`, bounded identity/authority schemas, current README/CLI documentation and affected CLI protocol tests. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0012-AC01: Enrollment binds stable device/controller identities, permitted scopes/sources and host transport identity, and rejects changed/revoked/unknown peers without changing user SSH security settings.
- RFC-MASK-0012-AC06: Controller/device signing and receipt validation use the established provider with separate namespaces and no unsigned silent fallback for unattended requests.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_fleet_identity
- Temporary OpenSSH signing provider checks with synthetic keys.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.

## Planned bounded decisions

Dependencies remain open until MASK-0069/0070 finish; no source work or fleet enrollment is asserted by this plan. RFC_BASE_SHA remains the imported closeout anchor 9dc90df45febf2a6e048ace60a4ac959807aaaf6.

- Keep local device/controller identities, scopes and authorization under fixed MASK_HOME/fleet paths, separately from deployment state. Stable generated IDs, distinct OpenSSH signing identities and explicit local provider references/public fingerprints are not SSH login credentials or portable profile content. Test with synthetic keys in disposable roots; never copy private keys to Git or a device.
- Use the established OpenSSH file-signature provider and separate fixed mask-intent@mask.invalid and mask-receipt@mask.invalid namespaces. Missing capabilities fail with typed prerequisites, never unsigned fallback. Native provider probes already established that verification with an opened payload file as stdin works on Windows, while its pipe variant did not; use bounded file-backed verification without repeating unchanged probes.
- Local scope aliases bind already registered physical consumer roots/identities. Action/source allowances and per-source artifact-forwarding permission are explicit device policy and cannot be inferred from successful SSH or package metadata. Bind controller key, current epoch and minimum accepted sequence through explicit trusted enrollment data. Preserve revocation tombstones and reject unknown/changed identities.
- Replace the depth-two CLI parser construction with a prefix tree while retaining complete dotted command names, existing leaf specs, argv/JSON behavior and generated capability metadata. Local identity/authority operations in this card must be fully usable and truthfully scoped; actual fixed RPC/probing transport is MASK-0048/0049 and must not be advertised as already tested.
- Network/provider preparation happens outside the deployment writer lock. Commit local authority only after exact bytes, identity and generation checks under the existing lock. No SSH config/known-host changes, forwarding, credential grants, installs, firewall or privilege changes. Existing native SSH authority permits later disposable real-host tests, not personal persistent fleet enrollment.
- Full RFC12 acceptance will combine bounded identity/provider tests with RPC/transport and actual native tests. A source-only identity card cannot claim remote fleet deployment.
