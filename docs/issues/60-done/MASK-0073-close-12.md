---
schema: "implement-rfc.card.v1"
id: "MASK-0073"
title: "Verify and close RFC-MASK-0012"
status: "Done"
rfcs: ["RFC-MASK-0012"]
depends_on: ["MASK-0047", "MASK-0048", "MASK-0049", "MASK-0050"]
closeout_for: ["RFC-MASK-0012"]
metadata: {"packet":"mask-readiness-fleet-2026-09-05","packet_key":"close-12","stage":"D — enrolled fleet foundation","provisional_id":false,"closeout":true,"milestone_plan":{"id":"fleet-enrolled-transport","path":"docs/rfcs/plans/fleet-enrolled-transport/milestone-plan.json"}}
acceptance: [{"criterion":"RFC-MASK-0012-AC01","outcome":"pass","revision":"a46dd0d3ccab7920d5fdd77d71917d79c0514960","evidence":{"kind":"artifact","detail":"Actual native signed enrollment and strict SSH host/login refusal, plus local identity and authority fixtures.","path":"docs/development/fleet-native-acceptance.md"}},{"criterion":"RFC-MASK-0012-AC02","outcome":"pass","revision":"a46dd0d3ccab7920d5fdd77d71917d79c0514960","evidence":{"kind":"artifact","detail":"Closed framed protocol tests and actual fixed native launcher checks with invalid frames and preserved exit status.","path":"docs/development/fleet-native-acceptance.md"}},{"criterion":"RFC-MASK-0012-AC03","outcome":"pass","revision":"a46dd0d3ccab7920d5fdd77d71917d79c0514960","evidence":{"kind":"artifact","detail":"The ordinary local journal performed a scoped repair. Timeout, lost response, same-ID replay, sequence guard and partial recovery remained independently observable.","path":"docs/development/fleet-native-acceptance.md"}},{"criterion":"RFC-MASK-0012-AC04","outcome":"pass","revision":"a46dd0d3ccab7920d5fdd77d71917d79c0514960","evidence":{"kind":"artifact","detail":"Exact acquisition and signed forwarding fixture tests passed on both OSes with integrity, path, selection and authorization refusals.","path":"docs/development/fleet-native-acceptance.md"}},{"criterion":"RFC-MASK-0012-AC05","outcome":"pass","revision":"a46dd0d3ccab7920d5fdd77d71917d79c0514960","evidence":{"kind":"artifact","detail":"Actual native Windows SSH with Windows shell boundary checks and unprivileged macOS loopback SSH, separately from subprocess and fake Git transport fixtures.","path":"docs/development/fleet-native-acceptance.md"}},{"criterion":"RFC-MASK-0012-AC06","outcome":"pass","revision":"a46dd0d3ccab7920d5fdd77d71917d79c0514960","evidence":{"kind":"artifact","detail":"Actual OpenSSH provider, independent namespaces, matched device and request IDs and operation receipts with semantic binding.","path":"docs/development/fleet-native-acceptance.md"}}]
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

Surviving pre-implementation baseline: c0ff45c882efd52b744fa3fb4e9c0d6d22d79eed. The original imported anchor above predates the privacy rewrite.

Planned cards: MASK-0047, MASK-0048, MASK-0049, MASK-0050.

Cross-repository handoff: none required for the enrolled transport foundation.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0012-AC01 | Reviewed enrollment over actual native SSH bound signing identities, host key, endpoint and explicit authority. Host-key change, unavailable login and revocation refused. | Pass | a46dd0d3ccab7920d5fdd77d71917d79c0514960 |
| RFC-MASK-0012-AC02 | Public stdio subprocess and native fixed launchers rejected duplicate keys, oversized and malformed frames, shell/path inputs and unauthorized actions. Native malformed input kept stdout empty and preserved exit 4. | Pass | a46dd0d3ccab7920d5fdd77d71917d79c0514960 |
| RFC-MASK-0012-AC03 | Public apply repaired a real fixture link using the ordinary local journal. Same ID and digest replayed the durable result. Actual lost SSH reply was queryable, and injected partial local work required ordinary recovery. | Pass | a46dd0d3ccab7920d5fdd77d71917d79c0514960 |
| RFC-MASK-0012-AC04 | Native macOS and Windows fixture suites retrieved exact locked Git bytes and separately delivered selected signed package bytes. Disabled forwarding, unrelated coordinates, bad paths and bad digests refused. | Pass | a46dd0d3ccab7920d5fdd77d71917d79c0514960 |
| RFC-MASK-0012-AC05 | Native macOS loopback sshd and existing native Windows OpenSSH both passed. The Windows command was also exercised with cmd.exe and PowerShell. See the linked native record. | Pass | a46dd0d3ccab7920d5fdd77d71917d79c0514960 |
| RFC-MASK-0012-AC06 | Distinct OpenSSH intent and receipt namespaces bound canonical bytes to the correct peers and request. Changed keys, digest, revision and removed scope were refused. | Pass | a46dd0d3ccab7920d5fdd77d71917d79c0514960 |

Closeout review runtime: Codex gpt-6.1-sol xhigh implementer self-review.

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


## Integration and continuation

The [native verification record](../../development/fleet-native-acceptance.md)
contains the two actual SSH runs and the separate native fixture results.
The RPC and ordinary pinned recovery pass ran 22 cases at
`741df64`. The final semantic receipt and scope checks ran 17 cases at
`a46dd0d`. The fan-out and terminal refusal test at `1bc98d6` preserved separate outcomes
for both peers. At final product revision `67fea18`, all 18 fleet, CLI protocol
and launcher inventory checks passed, together with the 14 focused help,
renderer and transport checks. Each controller
probe and exact retrieval was bounded. Network waits released the device's
ordinary deployment writer lock. The final native macOS SSH run at
`67fea18` confirmed the enrolled Python directory was absent from the actual
remote PATH. A final strict SSH probe found zero remaining Stage D temporary
roots on the Windows host.

The closeout compares the scoped change to the surviving baseline above.
The signed transport foundation now satisfies the prerequisite for
MASK-0051 under RFC-MASK-0013. The next milestone owns new desired profile
delivery, production enrollment and the multi-device rollout and offline
catch-up acceptance.
