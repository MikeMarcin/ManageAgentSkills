---
schema: "implement-rfc.card.v1"
id: "MASK-0050"
title: "Verify native remote invocation and enrollment boundaries"
status: "Backlog"
rfcs: ["RFC-MASK-0012"]
depends_on: ["MASK-0049"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "fleet-native", "stage": "D — enrolled fleet foundation", "provisional_id": true}
---

# MASK-0050: Verify native remote invocation and enrollment boundaries

Governing RFC: [RFC-MASK-0012](../../rfcs/RFC-MASK-0012-fleet-enrollment-and-transport.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

With explicit enrollment authority, check actual native Windows and macOS fixed launchers, spaces/Unicode, host key refusal, noninteractive auth, disconnect status and signed receipts. Keep fixture simulation separate from real transport evidence. No workstation aliases from old conversations are presumed authorized.

Own only: `tests/test_fleet_transport.py`, `docs/development/fleet-native-acceptance.md (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0012-AC01: Enrollment binds stable device/controller identities, permitted scopes/sources and host transport identity, and rejects changed/revoked/unknown peers without changing user SSH security settings.
- RFC-MASK-0012-AC04: Exact package transfer validates paths/digests and never forwards credentials or unrelated private content; unavailable authentication remains a prerequisite.
- RFC-MASK-0012-AC05: Native Windows/macOS transport and launcher checks record actual host/runtime results, while fixture-only tests remain labelled as such.
- RFC-MASK-0012-AC06: Controller/device signing and receipt validation use the established provider with separate namespaces and no unsigned silent fallback for unattended requests.

Proposed direct checks (not executed by this packet):

- Record actual distinct native host environments and focused commands/results; missing devices leave this card open.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
