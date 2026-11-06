---
schema: "implement-rfc.card.v1"
id: "MASK-0055"
title: "Demonstrate real two-machine install and offline convergence"
status: "Done"
rfcs: ["RFC-MASK-0013"]
depends_on: ["MASK-0054", "MASK-0050"]
metadata: {"packet":"mask-readiness-fleet-2026-09-05","packet_key":"fleet-dogfood","stage":"D — personal fleet workflow","provisional_id":false,"milestone_plan":{"id":"fleet-skill-rollouts","path":"docs/rfcs/plans/fleet-skill-rollouts/milestone-plan.json"}}
acceptance: [{"criterion":"RFC-MASK-0013-AC01","outcome":"pass","revision":"d1d87be996cd240d3cd23e11a82468b0a9b56adb","evidence":{"kind":"observation","detail":"Actual Mac and Windows public CLI used a cached unique tap name and GitHub-shaped fixture URL. Curated publication isolated the reviewed package paths and preserved unrelated source staging. Both devices returned matching signed receipts."}},{"criterion":"RFC-MASK-0013-AC04","outcome":"pass","revision":"d1d87be996cd240d3cd23e11a82468b0a9b56adb","evidence":{"kind":"observation","detail":"Actual two-device operation recorded Windows as verified and offline macOS as queued. A newer revision superseded the older Mac outcome. The controlled Mac collision remained blocked while Windows verified."}},{"criterion":"RFC-MASK-0013-AC06","outcome":"pass","revision":"d1d87be996cd240d3cd23e11a82468b0a9b56adb","evidence":{"kind":"observation","detail":"Native macOS and Windows fixture devices verified actual pinned SSH rollout, two controller updates, latest-only offline catch-up and exact independent receipts. Actual per-user scheduler convergence subsequently passed under r2."}},{"criterion":"RFC-MASK-0013-AC07","outcome":"pass","revision":"2895f43cc90a896076b913c3104a6f340fa9238d","evidence":{"kind":"observation","detail":"Exact source-only recovery and lost-ack tests, native signed receipts, independent collision reporting and explicit unobserved agent host load."}}]
---

# MASK-0055: Demonstrate real two-machine install and offline convergence

Governing RFC: [RFC-MASK-0013](../../rfcs/RFC-MASK-0013-fleet-rollouts-and-continuous-sync.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

After explicit selection/enrollment, demonstrate one URL copied to a curated source and one tap installed on distinct macOS/native-Windows devices. Include an offline target and later matching receipt, plus one controlled collision. Capture compact actual commands/revisions/outcomes; no test-only simulation can satisfy the real-device criterion.

Own only: `docs/development/fleet-native-acceptance.md`, `tests/test_fleet_install.py`, `docs/architecture/cli-contract.md`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0013-AC01: A single name-or-GitHub-URL fleet install request composes copy/tap resolution, exact locking, authorized source/control publication, deployment and a per-device report without manual internal-state edits.
- RFC-MASK-0013-AC04: Offline, unknown, incompatible, recovery-required, canceled and superseded devices are reported distinctly; incomplete rollouts never claim installed everywhere or reuse stale receipts.
- RFC-MASK-0013-AC06: Actual two-machine macOS/native-Windows rollout and offline catch-up evidence is recorded, or that acceptance stays open with the exact environmental limitation.
- RFC-MASK-0013-AC07: Failure between import/publication/remote apply/receipt steps is resumable and truthful, and reports preserve the difference between filesystem verification and host discovery.

Proposed direct checks (not executed by this packet):

- Record actual multi-device operation IDs, signed receipt revisions, device status and host-loading limitations.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

The [native rollout report](../../development/fleet-native-acceptance.md#two-device-rollout-and-catch-up)
records two-device evidence for `d1d87be996cd240d3cd23e11a82468b0a9b56adb`.
The disposable macOS and native Windows rollout included a tap install, GitHub
tree-URL curated copy, two controller updates while the Mac listener was
offline, matching receipt for the latest approved revision after sync,
withdrawal and an isolated destination collision. The device fixtures were
removed. The
[native scheduler qualification](../../development/fleet-native-acceptance.md#current-user-native-scheduler-qualification)
under MASK-0054 subsequently verified current-user timed convergence on both
platforms.
