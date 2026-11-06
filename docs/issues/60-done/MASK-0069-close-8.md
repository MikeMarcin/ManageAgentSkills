---
schema: "implement-rfc.card.v1"
id: "MASK-0069"
title: "Verify and close RFC-MASK-0008"
status: "Done"
rfcs: ["RFC-MASK-0008"]
depends_on: ["MASK-0034", "MASK-0035", "MASK-0036", "MASK-0037"]
closeout_for: ["RFC-MASK-0008"]
metadata: {"packet":"mask-readiness-fleet-2026-09-05","packet_key":"close-8","stage":"B — reproducible content","provisional_id":false,"closeout":true,"milestone_plan":{"id":"pin-target-prerequisites","path":"docs/rfcs/plans/pin-target-prerequisites/milestone-plan.json"}}
acceptance: [{"criterion":"RFC-MASK-0008-AC01","outcome":"pass","revision":"74f341a36791887f747373a0db37addd03b9c47e","evidence":{"kind":"observation","detail":"Native two-worktree exact artifact test and public macOS CLI authoring, fetch and selected upgrade preserving personal lock, link and bytes. See targeting-acceptance.md for native Windows 7b6c6db and current macOS evidence."}},{"criterion":"RFC-MASK-0008-AC02","outcome":"pass","revision":"74f341a36791887f747373a0db37addd03b9c47e","evidence":{"kind":"observation","detail":"Native lock and artifact suites verify raw Git bytes, logical modes, exact paths and identity, malformed lock and moved-ref refusals. See targeting-acceptance.md for native Windows 7b6c6db and current macOS evidence."}},{"criterion":"RFC-MASK-0008-AC03","outcome":"pass","revision":"74f341a36791887f747373a0db37addd03b9c47e","evidence":{"kind":"observation","detail":"Native pinned recovery and artifact exact hydration cases verify approved fetch, offline restore, unavailable exact commits and preserved controls. See targeting-acceptance.md for native Windows 7b6c6db and current macOS evidence."}},{"criterion":"RFC-MASK-0008-AC04","outcome":"pass","revision":"74f341a36791887f747373a0db37addd03b9c47e","evidence":{"kind":"observation","detail":"Native pinned link/adoption/retarget and collision tests; historical owned legacy link retargeting evidenced by MASK-0037 and MASK-0104. See targeting-acceptance.md for native Windows 7b6c6db and current macOS evidence."}},{"criterion":"RFC-MASK-0008-AC05","outcome":"pass","revision":"74f341a36791887f747373a0db37addd03b9c47e","evidence":{"kind":"observation","detail":"Native interruption, exact rollback and concurrent-input guards. Public forward commit recovery and protected-input refusal; historical migration config rollback evidenced by MASK-0037 and MASK-0104. See targeting-acceptance.md for native Windows 7b6c6db and current macOS evidence."}},{"criterion":"RFC-MASK-0008-AC06","outcome":"pass","revision":"35048af","evidence":{"kind":"observation","detail":"Historical project/personal migration, dirty/unborn/pending refusal, old-program guard and direct Python fallback in MASK-0037; successor in MASK-0104. Owner retired pre-tap migration in 7ccf671."}},{"criterion":"RFC-MASK-0008-AC07","outcome":"pass","revision":"74f341a36791887f747373a0db37addd03b9c47e","evidence":{"kind":"observation","detail":"Native pinned update, artifact and scoped authoring tests verify isolated preparation, retention, development return and publication authority, with only disposable local bare remotes. See targeting-acceptance.md for native Windows 7b6c6db and current macOS evidence."}}]
---

# MASK-0069: Verify and close RFC-MASK-0008

Governing RFC: [RFC-MASK-0008](../../rfcs/RFC-MASK-0008-pinned-artifacts-and-recovery.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Reconcile every acceptance criterion against direct evidence at the stated boundary. Capture the real pre-implementation RFC_BASE_SHA and actual implementation/handoff commits. Reuse unchanged focused results; run a broader integration/review only where combined risk warrants it. Keep unavailable native, host, real-device or upstream handoff rows open. Do not claim packet validation as product acceptance.

Own only: `docs/rfcs/RFC-MASK-0008-pinned-artifacts-and-recovery.md`, `the corresponding live closeout card`, `current affected public contract docs`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0008-AC01: Two worktrees simultaneously use distinct immutable versions of one skill, and source authoring/ref movement changes neither deployment until an explicit selected update.
- RFC-MASK-0008-AC02: Locks reproduce raw package bytes across fixture machines; digest, package path, source identity, executable mode, malformed lock and moved-ref errors fail closed.
- RFC-MASK-0008-AC03: Ensure restores available exact artifacts, optionally hydrates only approved locked content, never resolves latest or rewrites lockfiles, and reports unavailable exact commits honestly.
- RFC-MASK-0008-AC04: Planner/executor/adoption/recovery correctly retarget an unchanged owned legacy or old-artifact link to a new artifact and preserve collisions, rather than retaining the old target.
- RFC-MASK-0008-AC05: Interruptions before/after lock, link and state effects preserve bounded v3 recovery; configuration/state migrations preserve exact legacy rollback bytes and reject concurrent edits.
- RFC-MASK-0008-AC06: Explicit migration covers project and personal consumers, dirty/unborn sources, old pending journals, schema-incompatible old programs, and direct-entrypoint escape paths.
- RFC-MASK-0008-AC07: Cache preparation, retention, dev-link exceptions and scoped publishing cannot silently alter other consumers, delete authoring history or claim atomicity across readers/devices.

Proposed direct checks (not executed by this packet):

- python -B scripts/verify_documentation.py --root .
- Only missing or invalidated direct acceptance checks for this RFC.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Durable closeout anchor

RFC_BASE_SHA: 9dc90df45febf2a6e048ace60a4ac959807aaaf6

The prepublication rewrite removed that historical object from the live
history. The scoped final comparison uses `794cc2a`, the surviving
pre-implementation parent of the live pack import `90a4f33`.

Planned cards: MASK-0034, MASK-0035, MASK-0036, MASK-0037.

Cross-repository handoff: unrecorded; attach only an actual upstream ID/revision when required.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0008-AC01 | Pinned recovery two-worktree test plus the public scoped-upgrade fixture. Authoring and ref movement preserve other locks, links and bytes. | Pass | `74f341a`, Windows `7b6c6db` |
| RFC-MASK-0008-AC02 | Lock and artifact suites compare canonical bytes across fixture machines and verify typed refusals for digests, paths, source identity, malformed locks, logical modes and moved refs. | Pass | `74f341a`, Windows `7b6c6db` |
| RFC-MASK-0008-AC03 | Pinned recovery and artifact exact hydration cases exercise offline restore, approved locked fetch and missing-commit refusal with unchanged controls. | Pass | `74f341a`, Windows `7b6c6db` |
| RFC-MASK-0008-AC04 | Pinned recovery and link producer tests exercise adoption, retargeting and collision preservation. Historical legacy retargeting is recorded in [MASK-0037](MASK-0037-pin-migration.md) and [MASK-0104](MASK-0104-doctor-migration.md). | Pass, with historical migration evidence | `74f341a`, Windows `7b6c6db`, historical `35048af` and `2dad1b0` |
| RFC-MASK-0008-AC05 | Typed journal crash, rollback, tampering and concurrent-edit checks, plus the public forward-commit positive and protected-input negative recovery probe. Historical exact configuration rollback is recorded in MASK-0037 and MASK-0104. | Pass, with historical migration evidence | `74f341a`, Windows `7b6c6db`, historical `35048af` and `2dad1b0` |
| RFC-MASK-0008-AC06 | MASK-0037 records project/user migration and dirty, unborn, pending and previous-program cases. MASK-0104 records successor doctor recovery and typed refusals. The owner retired pre-tap migration at `7ccf671`. | Pass for historical supported migration | Historical `35048af`, `2dad1b0` and `a2d7ee4` |
| RFC-MASK-0008-AC07 | Artifact preparation/retention and scoped pinned-update/dev-link/publishing suites verify preserved other consumers and authoring bytes, separate publication authority and honest uncertain push outcomes using fixture repositories. | Pass | `74f341a`, Windows `7b6c6db` |

Closeout review runtime: implementer reconciliation only. Historical
independent review and corrections are recorded on MASK-0036 and MASK-0037.

## Implementation progress

MASK-0034 model/resolver source: `c5a359f` (Done card records focused checks and corrections). MASK-0035 store/exact-hydration source: `d17a607` (Done card records 17 passing focused methods plus affected/new checks). These supply bounded lock/raw-artifact evidence, not full RFC acceptance. MASK-0036 now owns activation/recovery and unlocked readiness preparation; MASK-0037 owns selected migration/update/dev-link/publishing. Native pinned-engine/targeting checks remain planned at the coherent milestone; do not repeat unchanged RFC-0007 source/import native results.

MASK-0036 source `53522576740ecbd3cd237742a3d777592e056cb3` adds the artifact engine and typed recovery; its Done card records the focused results and corrected independent-review findings. Native lock/store checks are now recorded on MASK-0034/0035, including fixture-only correction6d36d6f. Remaining next slice: MASK-0037 explicit legacy/config migration, selected pinned update, dev-link and scoped publication; then combine only changed/new native engine/migration/targeting checks. Full AC rows above remain open until these paths are complete.

MASK-0037 source `7bbe2dbb4749ee3f69351b5c069b1b0ee28dae86` implements explicit migration/update/dev-link/publication. Its Done card records local direct checks, historical-program refusal/direct fallback, and corrected one-pass migration review findings. Next: RFC-0009 targeting/adapter integration, then MASK-0040 native engine/migration/targeting checks and combined RFC-0008/0009 closeout. Do not infer native engine acceptance from unchanged native lock/store results.

## Execution record

The combined native evidence in [MASK-0040](MASK-0040-target-native.md)
and the [verification note](../../development/targeting-acceptance.md)
supersedes the pending references above. The current product uses taps and
the public `upgrade` command for selected pinned updates. The historical
pre-tap migration evidence remains attached to the original criteria.
