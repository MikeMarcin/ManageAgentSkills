---
schema: "implement-rfc.card.v1"
id: "MASK-0073"
title: "Verify and close RFC-MASK-0012"
status: "Backlog"
rfcs: ["RFC-MASK-0012"]
depends_on: ["MASK-0047", "MASK-0048", "MASK-0049", "MASK-0050"]
closeout_for: ["RFC-MASK-0012"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "close-12", "stage": "D — enrolled fleet foundation", "provisional_id": false, "closeout": true}
---

# MASK-0073: Verify and close RFC-MASK-0012

Governing RFC: [RFC-MASK-0012](../../rfcs/RFC-MASK-0012-fleet-enrollment-and-transport.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Reconcile every acceptance criterion against direct evidence at the stated boundary. Capture the real pre-implementation RFC_BASE_SHA and actual implementation/handoff commits. Reuse unchanged focused results; run a broader integration/review only where combined risk warrants it. Keep unavailable native, host, real-device or upstream handoff rows open. Do not claim packet validation as product acceptance.

Own only: `docs/rfcs/RFC-MASK-0012-fleet-enrollment-and-transport.md`, `the corresponding live closeout card`, `current affected public contract docs`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0012-AC01: Enrollment binds stable device/controller identities, permitted scopes/sources and host transport identity, and rejects changed/revoked/unknown peers without changing user SSH security settings.
- RFC-MASK-0012-AC02: Bounded framed RPC accepts only the fixed action schema; malformed messages, shell metacharacters, wrong device IDs and arbitrary paths cannot invoke generic remote execution.
- RFC-MASK-0012-AC03: Each remote mutation uses the ordinary local planner/lock/journal; duplicate operation IDs, changed payloads, disconnects and timeouts produce queryable truthful outcomes.
- RFC-MASK-0012-AC04: Exact package transfer validates paths/digests and never forwards credentials or unrelated private content; unavailable authentication remains a prerequisite.
- RFC-MASK-0012-AC05: Native Windows/macOS transport and launcher checks record actual host/runtime results, while fixture-only tests remain labelled as such.
- RFC-MASK-0012-AC06: Controller/device signing and receipt validation use the established provider with separate namespaces and no unsigned silent fallback for unattended requests.

Proposed direct checks (not executed by this packet):

- python -B scripts/verify_documentation.py --root .
- Only missing or invalidated direct acceptance checks for this RFC.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Durable closeout anchor

RFC_BASE_SHA: 9dc90df45febf2a6e048ace60a4ac959807aaaf6

Planned cards: MASK-0047, MASK-0048, MASK-0049, MASK-0050.

Cross-repository handoff: unrecorded; attach only an actual upstream ID/revision when required.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0012-AC01 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0012-AC02 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0012-AC03 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0012-AC04 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0012-AC05 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0012-AC06 | Not recorded | Not run | Unrecorded |

Closeout review runtime: not run. A skipped required native/host/device check leaves the criterion open.

## Native signing prerequisite observation

While prerequisites were being implemented, disposable ED25519 keys signed and
verified a fixed probe under namespace `mask-intent@mask.invalid` with
`/usr/bin/ssh-keygen` on macOS and
`C:/Windows/System32/OpenSSH/ssh-keygen.exe` on native ExampleWinHost. Both file-input
verification invocations returned exit 0. No actual enrollment is asserted.

Windows verification fed by Python `subprocess.run(input=bytes)` hung beyond
45s. The exact task-owned `ssh-keygen` process was identified and stopped; its
parent removed `C:/Users/example/AppData/Local/Temp/mask-signing-probe-3kliqunv`.
Using an opened payload file for stdin then passed, and removed
`C:/Users/example/AppData/Local/Temp/mask-signing-file-probe-9esxu4pt`. The fleet
provider implementation should use bounded file input and native containment;
this is a prerequisite observation, not evidence for an implemented signing API.
