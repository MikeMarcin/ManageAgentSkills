---
schema: "implement-rfc.card.v1"
id: "MASK-0050"
title: "Verify native remote invocation and enrollment boundaries"
status: "Done"
rfcs: ["RFC-MASK-0012"]
depends_on: ["MASK-0049"]
metadata: {"packet":"mask-readiness-fleet-2026-09-05","packet_key":"fleet-native","stage":"D — enrolled fleet foundation","provisional_id":false,"milestone_plan":{"id":"fleet-enrolled-transport","path":"docs/rfcs/plans/fleet-enrolled-transport/milestone-plan.json"}}
acceptance: [{"criterion":"RFC-MASK-0012-AC01","outcome":"pass","revision":"a46dd0d3ccab7920d5fdd77d71917d79c0514960","evidence":{"kind":"artifact","detail":"Actual strict SSH on native macOS and Windows authenticated explicit signed enrollment, refused a wrong host key and missing noninteractive login, and refused local revocation.","path":"docs/development/fleet-native-acceptance.md"}},{"criterion":"RFC-MASK-0012-AC04","outcome":"pass","revision":"a46dd0d3ccab7920d5fdd77d71917d79c0514960","evidence":{"kind":"artifact","detail":"Exact candidate 12 fixture tests on native Windows and macOS included exact Git and explicitly granted signed forwarding with denial and integrity controls; live SSH fixtures independently verified locked filesystem effects.","path":"docs/development/fleet-native-acceptance.md"}},{"criterion":"RFC-MASK-0012-AC05","outcome":"pass","revision":"a46dd0d3ccab7920d5fdd77d71917d79c0514960","evidence":{"kind":"artifact","detail":"Native high-port loopback macOS SSH and aito-main-win Windows OpenSSH with bash default plus native cmd.exe and PowerShell invocation. Spaced Unicode path, process exit, disconnect status and fixture cleanup recorded.","path":"docs/development/fleet-native-acceptance.md"}},{"criterion":"RFC-MASK-0012-AC06","outcome":"pass","revision":"a46dd0d3ccab7920d5fdd77d71917d79c0514960","evidence":{"kind":"artifact","detail":"Signed capability and recovered durable receipt verified over both actual native SSH links; independent native fixture tests exercised signature refusal.","path":"docs/development/fleet-native-acceptance.md"}}]
---

# MASK-0050: Verify native remote invocation and enrollment boundaries

Governing RFC: [RFC-MASK-0012](../../rfcs/RFC-MASK-0012-fleet-enrollment-and-transport.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

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
