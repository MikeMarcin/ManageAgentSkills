---
schema: "implement-rfc.card.v1"
id: "MASK-0089"
title: "Run genuinely required setup with exact consent and recovery"
status: "Done"
rfcs: ["RFC-MASK-0019"]
depends_on: ["MASK-0085", "MASK-0088"]
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": false, "packet_key": "approved-staged-setup"}
acceptance: [{"criterion":"RFC-MASK-0019-AC04","outcome":"pass","revision":"824b0c29515f6e048a8b2b87adca5e386858a97f","evidence":{"kind":"command","detail":"python3 -B -m unittest tests.test_setup (macOS, subprocess CLI on disposable fixture source/consumer): terminal yes on a pty shows the exact disclosure and runs/validates/publishes/rechecks in one invocation; no/EOF/interrupt run nothing (sentinel absent); --json/--check/--dry-run/--yes/--event/redirected streams never run package code even with --allow-setup; only --expect-plan-hash plus exact SOURCE/ID:ACTION grants; malformed/foreign grants refused"}},{"criterion":"RFC-MASK-0019-AC05","outcome":"pass","revision":"824b0c29515f6e048a8b2b87adca5e386858a97f","evidence":{"kind":"command","detail":"Same run: frozen snapshot digest compared at copy time; changed entrypoint/helper after prompt -> plan.stale, nothing ran; timeout stops the owned process tree (spawned child killed), output overflow and unsuccessful exit are bounded setup.failed; extra/symlink/traversing/unsupported/renamed/missing outputs -> setup.outputs_invalid, nothing published; crash after launch -> recover --complete refuses setup.unverified, --rollback discards, no rerun; crash during publication completes/rolls back from the journal without rerunning; tampered transaction id -> recovery.conflict with MASK_HOME intact; post-run input change or parent replacement -> setup.failed with unknown side effects (critical-review fixes)"}}]
---

# MASK-0089: Run genuinely required setup with exact consent and recovery

Governing RFC: [RFC-MASK-0019](../../rfcs/RFC-MASK-0019-complete-workflow-readiness.md). Live IDs confirmed by the committed pack reservation `6d80121`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-ux-readiness.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-ux-readiness/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-ux-readiness/ACCEPTANCE.md).

## Objective and owned paths

Bounded setup service over mask_process.py, shared proposal/authority/journal seams, role staging validation and timeout/crash tests. No general shell hook framework.

## Bounded work

Implement the fixed Python preparation interface with frozen package/context inputs, exact named action authority and staged role outputs. A human yes covers the disclosed bounded sequence. Package validators are not executed implicitly. Use existing process-tree control, stream bounds and typed operation recovery; do not duplicate the renderer or let it own final paths.

## Acceptance

Yes runs then verifies; no/EOF/check/dry-run/JSON-without-approval runs nothing. Changed imported code or inputs invalidates consent. Timeout/cancellation/crash retains truthful stage/pending status and never automatically reexecutes uncertain code. Malformed/extra/stale stage outputs cannot reach host discovery paths. No claim of a security sandbox is made.

Criterion coverage: RFC-MASK-0019-AC04, RFC-MASK-0019-AC05.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary. Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation, and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Done September 9, 2026 inside integrated outcome M7 (dispatch D8, mandate
revision 2). Candidate `7793469` (rfc-worker, claude-fable-5-1, effort high;
the worker hit its host turn limit after landing the code, so the integrator
consumed the working tree directly) adds `mask_setup.py`: setup actions become
frozen proposals (package bytes, descriptor, declared inputs, interpreter) whose
fingerprints bind the `ensure` plan hash; consent is `package.setup` through
`mask_consent` (terminal yes, or `--expect-plan-hash` plus exact `--allow-setup
SOURCE/ID:ACTION`; `--yes`, `--json`, `--check`, `--dry-run`, events and
redirected streams never run package code); execution uses
`mask_core.contained_run` (the Git process-tree runner generalized) on a
task-private package snapshot with `--repo-root/--output-root/--request-file`;
only `STAGE/AGENT/NAME.ext` regular files are admitted; the portable lock and
roles publish through the typed journal (`pending.setup` phases `launched` ->
`staged`); a launched-but-unverified journal refuses `recover --complete`
(`setup.unverified`) and is never rerun. Critical review (rfc-critical-reviewer,
claude-fable-5-1, effort xhigh, read-only at `7793469`) found two blocking
defects fixed in `824b0c29515f6e048a8b2b87adca5e386858a97f`: a tampered journal transaction id (`..`) let stage
cleanup delete MASK_HOME, and post-launch failures (script edits a declared
input; script replaces `.claude/agents` with a file) were reported as "nothing
ran" or crashed with exit 10. Hardening from the same review: shipped bytecode
never enters the frozen snapshot (`PYTHONPYCACHEPREFIX` is task-private) and the
staged-role size bound precedes the read. Verified: `python3 -B -m unittest
tests.test_setup tests.test_workflow_roles tests.test_consent tests.test_ensure
tests.test_recovery tests.test_human_output` (69 tests, OK, macOS) at `824b0c29515f6e048a8b2b87adca5e386858a97f`;
full discovery at `7793469` (334 tests, 1 failure = the known pre-existing
`tests.test_user_scope.test_scope_selection_and_parser`). Limitations recorded:
`ensure --check --expect-plan-hash WRONG` returns ok (the guard is not applied
in check mode) while `--dry-run` with a wrong hash is `plan.stale`; a stage
directory can leak if journal validation fails before `pending.json` is written;
the lock's parent directory is not listed in `pending['directories']`; the
pinned payload-view path reports `blocked` (no local package directory) and was
reviewed by reading only; no Windows Job containment or native lane was
exercised for setup (open for MASK-0092); capability advertisement and the
install/update/doctor/launch final status wait for MASK-0090.
