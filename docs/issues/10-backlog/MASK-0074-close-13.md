---
schema: "implement-rfc.card.v1"
id: "MASK-0074"
title: "Verify and close RFC-MASK-0013"
status: "Backlog"
rfcs: ["RFC-MASK-0013"]
depends_on: ["MASK-0051", "MASK-0052", "MASK-0053", "MASK-0054", "MASK-0055"]
closeout_for: ["RFC-MASK-0013"]
metadata: {"packet":"mask-readiness-fleet-2026-09-05","packet_key":"close-13","stage":"D — personal fleet workflow","provisional_id":false,"closeout":true,"milestone_plan":{"id":"fleet-skill-rollouts","path":"docs/rfcs/plans/fleet-skill-rollouts/milestone-plan.json"}}
---

# MASK-0074: Verify and close RFC-MASK-0013

Governing RFC: [RFC-MASK-0013](../../rfcs/RFC-MASK-0013-fleet-rollouts-and-continuous-sync.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Reconcile every acceptance criterion against direct evidence at the stated boundary. Capture the real pre-implementation RFC_BASE_SHA and actual implementation/handoff commits. Reuse unchanged focused results; run a broader integration/review only where combined risk warrants it. Keep unavailable native, host, real-device or upstream handoff rows open. Do not claim packet validation as product acceptance.

Own only: `docs/rfcs/RFC-MASK-0013-fleet-rollouts-and-continuous-sync.md`, `the corresponding live closeout card`, `current affected public contract docs`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0013-AC01: A single name-or-GitHub-URL fleet install request composes copy/tap resolution, exact locking, authorized source/control publication, deployment and a per-device report without manual internal-state edits.
- RFC-MASK-0013-AC02: Frozen device/scope sets, local contribution preservation and source/package identity prevent unexpected project edits, hidden source enrollment or skill-name ambiguity.
- RFC-MASK-0013-AC03: Signed monotonic desired revisions and compare-and-swap publication handle two controllers, duplicate deliveries, replay, rollback-as-new-intent and revoked peers without silent last-writer overwrite.
- RFC-MASK-0013-AC04: Offline, unknown, incompatible, recovery-required, canceled and superseded devices are reported distinctly; incomplete rollouts never claim installed everywhere or reuse stale receipts.
- RFC-MASK-0013-AC05: An opt-in runner catches up to the latest approved state with bounded polling/backoff, preserves scheduler ownership, never upgrades upstream/programs implicitly, and resumes after interruptions.
- RFC-MASK-0013-AC06: Actual two-machine macOS/native-Windows rollout and offline catch-up evidence is recorded, or that acceptance stays open with the exact environmental limitation.
- RFC-MASK-0013-AC07: Failure between import/publication/remote apply/receipt steps is resumable and truthful, and reports preserve the difference between filesystem verification and host discovery.

Proposed direct checks (not executed by this packet):

- python -B scripts/verify_documentation.py --root .
- Only missing or invalidated direct acceptance checks for this RFC.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Durable closeout anchor

RFC_BASE_SHA: 9dc90df45febf2a6e048ace60a4ac959807aaaf6

Surviving pre-implementation anchor after the prepublication rewrite: 4c401c5b3a03c11bc6a67af9a004708b97898ef3. The original RFC_BASE_SHA is retained above.

Planned cards: MASK-0051, MASK-0052, MASK-0053, MASK-0054, MASK-0055.

Cross-repository handoff: unrecorded; attach only an actual upstream ID/revision when required.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0013-AC01 | Native tap name and GitHub tree-URL curated copy with signed exact receipts | Pass | `d1d87be` |
| RFC-MASK-0013-AC02 | Frozen target proof, project mapping fixture, native local pins and unchanged authoring index | Pass | `c7680f8` |
| RFC-MASK-0013-AC03 | Disposable Git CAS, signed replay and exact rollback via public command | Pass | `c7680f8` |
| RFC-MASK-0013-AC04 | Native independent collision/offline results and supersession, fixture cancel/lost-ack/recovery | Pass | `d1d87be` |
| RFC-MASK-0013-AC05 | Foreground native pull and injected scheduler ownership/backoff passed. Native scheduler registration, invocation and removal need explicit authorization | Open | `c7680f8` |
| RFC-MASK-0013-AC06 | Actual distinct native macOS and Windows over pinned SSH, two offline revisions and exact newest catch-up | Pass | `d1d87be` |
| RFC-MASK-0013-AC07 | Deterministic source-only resume, signed reply loss recovery and separate host-load status | Pass | `2895f43` |

Closeout review runtime: implementer self-review. Native scheduler qualification remains open. See the [native rollout report](../../development/fleet-native-acceptance.md#two-device-rollout-and-catch-up).
