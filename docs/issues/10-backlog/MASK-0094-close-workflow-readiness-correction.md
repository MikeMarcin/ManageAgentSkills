---
schema: "implement-rfc.card.v1"
id: "MASK-0094"
title: "Verify and close complete workflow readiness"
status: "Backlog"
rfcs: ["RFC-MASK-0019"]
depends_on: ["MASK-0092"]
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": false, "packet_key": "close-workflow-readiness-correction"}
closeout_for: ["RFC-MASK-0019"]
---

# MASK-0094: Verify and close complete workflow readiness

Governing RFC: [RFC-MASK-0019](../../rfcs/RFC-MASK-0019-complete-workflow-readiness.md). Live IDs confirmed by the committed pack reservation `6d80121`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-ux-readiness.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-ux-readiness/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-ux-readiness/ACCEPTANCE.md).

## Objective and owned paths

This RFC, its closeout, current affected docs and exact upstream/native evidence references only.

## Bounded work

Reconcile all RFC-MASK-0019 criteria, including the real AgentSkills handoff and the public fresh-consumer/missing-role cases. Confirm no setup/recovery path silently executes unapproved code, retries uncertain actions, rewrites tracked files, or claims loaded roles from configuration alone.

## Acceptance

Every criterion has direct actual evidence and an implementation revision; every linked required card is Done. A fixture package, source-only validator or successful symlink operation cannot substitute for the real workflow journey. Unavailable upstream/native acceptance remains open.

Criterion coverage: RFC-MASK-0019-AC01, RFC-MASK-0019-AC02, RFC-MASK-0019-AC03, RFC-MASK-0019-AC04, RFC-MASK-0019-AC05, RFC-MASK-0019-AC06, RFC-MASK-0019-AC07, RFC-MASK-0019-AC08.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary. Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation, and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Not started. Claim the live remapped card before edits. No code implementation,
native result, host loading, user approval, or quota improvement is asserted.

## Durable closeout anchor

RFC_BASE_SHA: 6d80121b1c870f1be7864e8bc9db2b02a0e41c2d

Planned cards: MASK-0083, MASK-0088, MASK-0089, MASK-0090, MASK-0092.

| Acceptance | Direct check / observation | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0019-AC01 | `python3 -B -m unittest tests.test_workflow_roles tests.test_public_baseline` (macOS, subprocess CLI, synthetic static/generated packages, disposable consumers): with correct links and `rfc-integrator` absent, `ensure --check` is nonzero and names the role (exit 7 `readiness.drift` when the package can supply it, exit 4 `workflow.incomplete` when only preserved/unlocked roles remain); `ensure` never reports `ready_legacy_unpinned` while a declared role or required input is missing/modified; plain skills report `workflow: not_declared`; unavailable payload bytes report `unexamined`, never complete (MASK-0088). `tests.test_readiness_entrypoints` (macOS, subprocess CLI): `install` with a generated role and no lock -> exit 4 `workflow.incomplete` with the link committed; `doctor` lists a deleted role as missing and `--check` exits 7; `launch --agent codex|claude` with correct links and `setup_required` integrator exits 4 and never invokes the fake host; legacy `update` plans a role added upstream from the candidate; `capabilities` advertises `workflow_readiness_v1` (MASK-0090) | Pass for the MASK side; real AgentSkills package not exercised | `bc90418cc4f97f3e62c1eeef80815fe769ccef44`, `3bbac77` |
| RFC-MASK-0019-AC02 | Same run: static package assets deploy as exact bytes with no generator, script or prompt; a fresh Git clone with tracked correct role files (no lock, no local renderer manifest) passes as `repository-owned` with tracked bytes/index unchanged; the generated variant passes only through a coherent `native-roles.lock.json` (descriptor digest, input digests, output hashes) and no `__pycache__` or script execution occurs (MASK-0088) | Pass at card boundary; real AgentSkills package not exercised | `bc90418cc4f97f3e62c1eeef80815fe769ccef44` |
| RFC-MASK-0019-AC03 | Same run: destinations come from `mask_adapters.role_relative` (`.codex/agents/<name>.toml`, `.claude/agents/<name>.md`), written through `pending.native_roles` (v3 journal, rollback/complete, `recovery.conflict` on a replaced file); modified/unknown files, linked parents (`target.parent_link`), a collision between two skills and repository-owned files are preserved and reported; valid checked-in files are neither adopted (no ownership record) nor deleted on `unrequire`; unchanged managed outputs are retired, an edited one is released with `native_role.released` (MASK-0088) | Pass at card boundary; explicit manual overwrite approval for tracked edits deferred to MASK-0089/0090 | `bc90418cc4f97f3e62c1eeef80815fe769ccef44` |
| RFC-MASK-0019-AC04 | `python3 -B -m unittest tests.test_setup` (macOS, POSIX pty and pipes, disposable fixture source/consumer): terminal yes shows the exact disclosure (source, fingerprint, interpreter, script, target, not sandboxed) and runs, validates, publishes and rechecks in one invocation; no/EOF/interrupt run nothing; `--json`/`--check`/`--dry-run`/`--yes`/`--event`/redirected streams never run package code even with `--allow-setup`; only `--expect-plan-hash` plus exact `--allow-setup SOURCE/ID:ACTION` grants; malformed/foreign grants refused (MASK-0089) | Pass for the synthetic generated package; Windows console lane open | `824b0c29515f6e048a8b2b87adca5e386858a97f` |
| RFC-MASK-0019-AC05 | Same run: task-private frozen snapshot digested at copy time; changed entrypoint/helper after consent -> `plan.stale`, nothing ran; timeout stops the owned process tree (spawned child killed), overflow/unsuccessful exit bounded `setup.failed`; extra/symlink/traversing/unsupported/renamed/missing outputs `setup.outputs_invalid`, nothing published; crash after launch -> `recover --complete` refuses `setup.unverified`, `--rollback` discards, no rerun; crash during publication completes/rolls back from the journal; tampered transaction id -> `recovery.conflict`; post-run input change or parent replacement -> `setup.failed` with unknown side effects. Critical review (rfc-critical-reviewer, claude-fable-5-1, effort xhigh) at `7793469` found the last two, fixed in `824b0c2` (MASK-0089) | Pass for the synthetic package; Windows Job containment for setup not exercised | `824b0c29515f6e048a8b2b87adca5e386858a97f` |
| RFC-MASK-0019-AC06 | Same run: requirements follow each binding's effective agents (`targets: [codex]` -> Claude roles `not_applicable`, no `.claude` directory) and physical scope; missing `rfc-integrator` is explicit; a role whose native `name` differs from the declared role (`rfc-critical-integrator`) is refused as `workflow.role_invalid`; the configured route (`model`, effort fields) is reported per role separately from `host_load: not_verified` (MASK-0088). `tests.test_readiness_entrypoints`: `update` evaluates roles from the frozen candidate (role added upstream planned as `native_role.write` with its configured route and `host_load: not_verified`; renamed role retires the unchanged managed file and preserves the edited one); consent for a generated role binds the exact package/descriptor/inputs/interpreter (MASK-0089/0090) | Pass for the MASK side; consumer profile/override semantics need the real package (MASK-0092) | `bc90418cc4f97f3e62c1eeef80815fe769ccef44`, `824b0c2`, `3bbac77` |
| RFC-MASK-0019-AC07 | Baseline uses the synthetic static package only; real package and native lanes not exercised (MASK-0083) | Not run | Not recorded |
| RFC-MASK-0019-AC08 | Docs describe static/checked-in, lock and approved-setup paths (`docs/guides/readiness-and-integrations.md`, README); unchanged reruns are script-free no-ops (`tests.test_setup`: second `ensure` runs nothing); `capabilities.workflow` advertises the contract. Upstream AgentSkills handoff: none exists at AgentSkills `2e45a4e` (no descriptor, preflight or staging entrypoint); recorded on MASK-0090 without an invented ASK ID | Open: upstream handoff not recorded | `824b0c2`, `3bbac77` |

Closeout review runtime: Not recorded. Required native/upstream boundaries remain
open until their actual evidence is linked. Do not invent a PASS to close the board.

## Current continuation

M0-M6 invariants and decisions live on [MASK-0093](../60-done/MASK-0093-close-human-cli-correction.md); this record carries the remaining outcomes.

Integrated outcome M7 (MASK-0089 + MASK-0090, dispatch D8, mandate revision 2) reached its boundary at `3bbac77`: a declared generated role can be produced by consented, frozen, journaled package setup from `ensure`, and no public task (`ensure`, `install`, `remove`, `update`, `doctor --check`, `launch`) reports complete success or starts a host while a declared role or input is unmet. MASK-0089 is Done (`824b0c2`); MASK-0090's MASK side is complete at `3bbac77` but the card is Blocked (`agentskills-handoff`) because no upstream AgentSkills handoff exists. Invariants for later cards: `mask_ensure.final_status` is the only place a task decides `workflow.incomplete` (renderers only print `data.workflow`/`workflow_readiness`); setup consent (`package.setup`) is asked only by manual `ensure`, never by install/update/launch, and never while the writer lock is held; `mask_setup.publish` holds the writer lock through execution and publication, journals `pending.setup` (`launched` -> `staged`, UUID transaction id, stage under `MASK_HOME/staging/<id>`) and a launched-but-unverified journal is refused by `recover --complete` and discarded by `--rollback`, never replayed; `mask_core.contained_run` is the shared owned-process-tree runner for Git and setup; the update planner must receive the frozen candidate bytes (`PackageView(files=...)`) so roles follow the selected candidate; bytecode never enters the setup snapshot. Known limitations: `ensure --check --expect-plan-hash WRONG` returns ok while `--dry-run` with a wrong hash is `plan.stale`; a stage directory can leak if journal validation fails before `pending.json` is written; the lock's parent directory is not listed in `pending['directories']`; the pinned payload-view path reports setup `blocked`; `list`/`inventory` stay `unexamined`.

Next outcome M8 (MASK-0092 + MASK-0094: real-package qualification in two disposable consumer contexts on macOS and Windows, then the RFC-MASK-0019 closeout) cannot start: MASK-0092 depends on MASK-0090, which waits on the upstream handoff (authorizing AgentSkills work is a user decision outside this pack). Independent MASK-only work that remains eligible without it: the Windows lane for `tests.test_setup`/`tests.test_readiness_entrypoints` (ExampleWinHost, disposable clone) and the `ensure --check` guard consistency; both are bounded follow-ups, not M8.

Integrated outcome M7b (dispatch D9, mandate revision 2; follow-ups to MASK-0089/MASK-0090, not M8): the setup and readiness-entrypoint behavior accepted on macOS is exercised natively on Windows, and `ensure` applies its `--expect-plan-hash` guard consistently. Exit criteria: (1) `ensure --check --expect-plan-hash WRONG` refuses with `plan.stale` exactly like `--dry-run`, with a subprocess test; (2) a failed setup journal validation leaves no stage directory under `MASK_HOME/staging`; (3) `tests.test_setup` and `tests.test_readiness_entrypoints` run with Windows Python from a disposable clone on the ExampleWinHost station (`example-win-host`, registered checkout untouched, user profile untouched), with the exact OS, interpreter, revision and per-test outcome recorded in `docs/development/readiness-acceptance.md` and the RFC-MASK-0019-AC07 row updated to the actual native result; any Windows-only failure receives a focused fix and rerun or stays recorded as open. The lock parent directory omission from `pending['directories']` stays a recorded limitation. Nothing in M8, MASK-0092 or the AgentSkills repository is touched.
