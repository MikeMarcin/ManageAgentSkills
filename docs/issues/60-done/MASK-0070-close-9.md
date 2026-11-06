---
schema: "implement-rfc.card.v1"
id: "MASK-0070"
title: "Verify and close RFC-MASK-0009"
status: "Done"
rfcs: ["RFC-MASK-0009"]
depends_on: ["MASK-0038", "MASK-0039", "MASK-0040"]
closeout_for: ["RFC-MASK-0009"]
metadata: {"packet":"mask-readiness-fleet-2026-09-05","packet_key":"close-9","stage":"B — selection semantics","provisional_id":false,"closeout":true,"milestone_plan":{"id":"pin-target-prerequisites","path":"docs/rfcs/plans/pin-target-prerequisites/milestone-plan.json"}}
acceptance: [{"criterion":"RFC-MASK-0009-AC01","outcome":"pass","revision":"74f341a36791887f747373a0db37addd03b9c47e","evidence":{"kind":"observation","detail":"Native physical project/user link independence and default both supported agents; direct macOS public CLI check preserves scope isolation. See targeting-acceptance.md for native Windows 7b6c6db and current macOS evidence."}},{"criterion":"RFC-MASK-0009-AC02","outcome":"pass","revision":"74f341a36791887f747373a0db37addd03b9c47e","evidence":{"kind":"observation","detail":"Native stable setters preserve lock package rows and refuse stale/colliding changes. Historical target preservation in MASK-0037 before the retirement of pre-tap migration. See targeting-acceptance.md for native Windows 7b6c6db and current macOS evidence."}},{"criterion":"RFC-MASK-0009-AC03","outcome":"pass","revision":"74f341a36791887f747373a0db37addd03b9c47e","evidence":{"kind":"observation","detail":"Native compatibility tests verify assertion levels, explicit blocking and conditional exclusion with truthful outcomes. See targeting-acceptance.md for native Windows 7b6c6db and current macOS evidence."}},{"criterion":"RFC-MASK-0009-AC04","outcome":"pass","revision":"74f341a36791887f747373a0db37addd03b9c47e","evidence":{"kind":"observation","detail":"Native scope shadowing and disjoint-agent/collision cases plus pure contribution merge/conflict guards. See targeting-acceptance.md for native Windows 7b6c6db and current macOS evidence."}},{"criterion":"RFC-MASK-0009-AC05","outcome":"pass","revision":"74f341a36791887f747373a0db37addd03b9c47e","evidence":{"kind":"observation","detail":"Native adapter contract, schema parity and current Claude/Codex scope checks. Earlier launcher/prelaunch evidence retained without a first-prompt claim. See targeting-acceptance.md for native Windows 7b6c6db and current macOS evidence."}}]
---

# MASK-0070: Verify and close RFC-MASK-0009

Governing RFC: [RFC-MASK-0009](../../rfcs/RFC-MASK-0009-scope-agent-targeting-and-compatibility.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Reconcile every acceptance criterion against direct evidence at the stated boundary. Capture the real pre-implementation RFC_BASE_SHA and actual implementation/handoff commits. Reuse unchanged focused results; run a broader integration/review only where combined risk warrants it. Keep unavailable native, host, real-device or upstream handoff rows open. Do not claim packet validation as product acceptance.

Own only: `docs/rfcs/RFC-MASK-0009-scope-agent-targeting-and-compatibility.md`, `the corresponding live closeout card`, `current affected public contract docs`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0009-AC01: The same skill has independently configurable personal and project agent sets, with new selections defaulting to all supported/enabled agents and no executable-detection side effects.
- RFC-MASK-0009-AC02: V1 migration preserves explicit and inherited target behavior; per-skill edits/locks/plans remain guarded and no-op stable.
- RFC-MASK-0009-AC03: Generic, absent and agent/platform-specific metadata produce distinct truthful reports; explicit incompatibilities block, and conditional/inapplicable bindings are not called installed.
- RFC-MASK-0009-AC04: Multi-source name conflicts, conflicting profiles and user/project duplicate names are explained without overwriting content, silently renaming packages or assuming host precedence.
- RFC-MASK-0009-AC05: A single adapter contract drives paths/capabilities/validation, and existing native Claude/Codex scope tests cover the change; additional agents stay unadvertised until independently proven.

Proposed direct checks (not executed by this packet):

- python -B scripts/verify_documentation.py --root .
- Only missing or invalidated direct acceptance checks for this RFC.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Durable closeout anchor

RFC_BASE_SHA: 9dc90df45febf2a6e048ace60a4ac959807aaaf6

The prepublication rewrite removed that historical object from the live
history. The scoped final comparison uses `794cc2a`, the surviving
pre-implementation parent of the live pack import `90a4f33`.

Planned cards: MASK-0038, MASK-0039, MASK-0040.

Cross-repository handoff: unrecorded; attach only an actual upstream ID/revision when required.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0009-AC01 | Public scope fixture and native targeting/user-scope tests verify independent links, default both agents, scope-local choices and no executable detection. | Pass | `74f341a`, Windows `7b6c6db` |
| RFC-MASK-0009-AC02 | Native targeting tests verify unchanged package rows, no-op, collision and stale-plan refusal. [MASK-0037](MASK-0037-pin-migration.md) records historical explicit/inherited target preservation before the owner retired pre-tap migration. | Pass, with historical migration evidence | `74f341a`, Windows `7b6c6db`, historical `35048af` |
| RFC-MASK-0009-AC03 | Native compatibility/targeting cases distinguish absent, generic and specific metadata, explicit blocks, implicit exclusions and conditional skips. | Pass | `74f341a`, Windows `7b6c6db` |
| RFC-MASK-0009-AC04 | Selection-conflict tests exercise contribution union/conflicts, disjoint agent names, multi-source collisions and user/project shadowing without lost content or assumed precedence. | Pass | `74f341a`, Windows `7b6c6db` |
| RFC-MASK-0009-AC05 | Adapter tests verify audited path/capability/schema/package parity and deferred future adapters. Native scope links and existing launcher/prelaunch evidence cover Claude and Codex; first-prompt loading remains unverified. | Pass | `74f341a`, Windows `7b6c6db` |

Closeout review runtime: implementer reconciliation only. Historical
independent review and corrections are recorded on MASK-0038.

## Implementation progress

MASK-0038 source c2fa4962f06349d33169fae478b69b7f758e7bb4 and Done 4291d5d supply local targeting/compatibility evidence, including corrected one-pass policy review and dangling-artifact reporting regressions. MASK-0039 now owns adapter data and contribution conflicts; MASK-0040 owns combined native engine/migration/targeting verification. Full AC rows remain open until this milestone.

## Execution record

[MASK-0040](MASK-0040-target-native.md) completes combined native
targeting. The [verification note](../../development/targeting-acceptance.md)
identifies tested revisions, physical links, guard and compatibility results.
Public portable-profile storage and fleet authorization retain their separate
RFC scope.
