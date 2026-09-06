---
schema: "implement-rfc.card.v1"
id: "MASK-0074"
title: "Verify and close RFC-MASK-0013"
status: "Backlog"
rfcs: ["RFC-MASK-0013"]
depends_on: ["MASK-0051", "MASK-0052", "MASK-0053", "MASK-0054", "MASK-0055"]
closeout_for: ["RFC-MASK-0013"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "close-13", "stage": "D — personal fleet workflow", "provisional_id": true, "closeout": true}
---

# MASK-0074: Verify and close RFC-MASK-0013

Governing RFC: [RFC-MASK-0013](../../rfcs/RFC-MASK-0013-fleet-rollouts-and-continuous-sync.md). IDs are packet-local until the main integrator imports/reserves them.

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

RFC_BASE_SHA: UNRECORDED — capture actual live pre-implementation commit before source changes.

Planned cards: MASK-0051, MASK-0052, MASK-0053, MASK-0054, MASK-0055.

Cross-repository handoff: unrecorded; attach only an actual upstream ID/revision when required.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0013-AC01 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0013-AC02 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0013-AC03 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0013-AC04 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0013-AC05 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0013-AC06 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0013-AC07 | Not recorded | Not run | Unrecorded |

Closeout review runtime: not run. A skipped required native/host/device check leaves the criterion open.
