---
schema: "implement-rfc.card.v1"
id: "MASK-0054"
title: "Add opt-in native scheduled convergence and offline catch-up"
status: "Ready"
rfcs: ["RFC-MASK-0013"]
depends_on: ["MASK-0053"]
metadata: {"packet":"mask-readiness-fleet-2026-09-05","packet_key":"fleet-runner","stage":"D — personal fleet workflow","provisional_id":false,"milestone_plan":{"id":"fleet-skill-rollouts","path":"docs/rfcs/plans/fleet-skill-rollouts/milestone-plan.json"}}
---

# MASK-0054: Add opt-in native scheduled convergence and offline catch-up

Governing RFC: [RFC-MASK-0013](../../rfcs/RFC-MASK-0013-fleet-rollouts-and-continuous-sync.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Implement foreground sync first, then owned per-user scheduler entries for proven native OSs. Verify latest approved intent, bounded jitter/backoff, no long network-held writer lock, recovery refusal and no upstream/program refresh. Catch up latest state rather than replaying superseded historical mutations.

Own only: `mask_runner.py (new)`, `mask_integration.py`, `tests/test_fleet_runner.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0013-AC03: Signed monotonic desired revisions and compare-and-swap publication handle two controllers, duplicate deliveries, replay, rollback-as-new-intent and revoked peers without silent last-writer overwrite.
- RFC-MASK-0013-AC04: Offline, unknown, incompatible, recovery-required, canceled and superseded devices are reported distinctly; incomplete rollouts never claim installed everywhere or reuse stale receipts.
- RFC-MASK-0013-AC05: An opt-in runner catches up to the latest approved state with bounded polling/backoff, preserves scheduler ownership, never upgrades upstream/programs implicitly, and resumes after interruptions.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_fleet_runner tests.test_fleet_control
- Native scheduled-task ownership/disable checks must name the OS actually exercised.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Foreground pull and scheduler adapters are implemented in
`d1d87be996cd240d3cd23e11a82468b0a9b56adb`. The scheduler ownership recheck is
in `c7680f8f1b1c1a2c774f8b1baac40fe8bee519fc`.

`tests.test_fleet_runner` passed on macOS and on native Windows through the
exact disposable Windows archive. Foreground pull selected only the latest
approved content, left an unapproved newer upstream version unapplied and
published the signed receipt to a separate bare Git repository. Injected
scheduler checks exercised ownership, disable and bounded retry. Controller
push and native offline catch-up are recorded in the
[native rollout report](../../development/fleet-native-acceptance.md#two-device-rollout-and-catch-up).

AC05 remains open for an actual current-user launchd and Windows Task Scheduler
registration, invocation and removal. Existing native authority covers
disposable checkout fixtures and excludes host scheduler changes. The private
rollout checkpoint records a scoped temporary procedure for later authorization.
