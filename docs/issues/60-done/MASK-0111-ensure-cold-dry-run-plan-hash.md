---
schema: "implement-rfc.card.v1"
id: "MASK-0111"
title: "Bind the same plan hash for a pinned ensure preview on a cold store as for the applying run"
status: "Done"
rfcs: []
depends_on: ["MASK-0102"]
priority: "P2"
metadata: {"origin":"RFC-MASK-0021 d2 follow-up candidate filed under mandate r2 (2026-09-13)","follow_up_of":"MASK-0101"}
acceptance: [{"criterion":"On a pinned consumer with a cold store, ensure --dry-run followed by ensure --expect-plan-hash H applies without plan.stale","outcome":"pass","revision":"8ea0fe5","evidence":{"kind":"command","detail":"python -B -m unittest -v tests.test_cold_store_plan_hash: 7 tests OK (approved and unapproved cold previews applied by hash; cold setup package with --allow-setup; previewed role paths equal written roles). Windows 11, Python 3.14.6, Git 2.55.0.windows.3. Logs: d7 session scratchpad d7-w3/logs/c2.log and d7-suite/out/test_cold_store_plan_hash.1.log (8ea0fe5). Negative control on git archive 1afd8b1: 3 failures exactly at plan.stale on the guarded apply (d7-w3/logs/nc2.log)."}},{"criterion":"A changed declaration, lock or policy between the two still refuses plan.stale","outcome":"pass","revision":"8ea0fe5","evidence":{"kind":"command","detail":"Same module: a changed declaration, lock, integration policy and selection policy each refuse plan.stale on the candidate; the same 4 guard tests also pass on base 1afd8b1, showing the guard is unchanged. The plan-hash inputs in mask_fs.plan are unchanged."}},{"criterion":"The preview performs no fetch and no materialization","outcome":"pass","revision":"8ea0fe5","evidence":{"kind":"command","detail":"Same module: Git trace2 counts 0 fetch processes for the preview and the guarded apply; every byte under MASK_HOME is unchanged by the preview and no store directory is created. mask_store.cached_payload reads only an exact cached commit and returns None otherwise."}},{"criterion":"No regression","outcome":"pass","revision":"8ea0fe5","evidence":{"kind":"command","detail":"Guarded per-module suite on a disposable clone at 8ea0fe595489fe702a51b446f7ed1c6ec106de8f: 52/52 modules, 460 tests, 17 skipped, 0 failures, 0 errors, no reruns, 3313.5 s; clone HEAD and status and the owner's live files unchanged. Windows 11 only; not the literal single-process run. Summary: d7 session scratchpad d7-suite/out/summary.json."}}]
---

# MASK-0111: Bind the same plan hash for a pinned ensure preview on a cold store as for the applying run

## Evidence

[MASK-0101 execution record](MASK-0101-machine-v3-and-tap-bootstrap.md#contract-notes-and-follow-up-candidates): an `ensure --dry-run` of a pinned consumer whose store is not yet materialized gives a plan hash different from the run that applies.

## Bounded work

Make the reviewed plan hash independent of whether locked artifacts are already materialized, without letting a preview fetch or materialize anything, and without weakening the guard against a real change between preview and apply.

## Acceptance

On a pinned consumer with a cold store, `ensure --dry-run` followed by `ensure --expect-plan-hash H` applies without `plan.stale`. A changed declaration, lock or policy between the two still refuses `plan.stale`. The preview performs no fetch and no materialization.

## Execution record

Dispatch `d7` of run `mask-rfc0020-2026-09-12-a`, producer `rfc-integrator-d7`, mandate revision `4`. Claimed at `47a5105`. Implemented at `8ea0fe5` together with MASK-0112 (W3, `rfc-worker`, in a separate worktree, then cherry-picked onto main).

- **Cause:** on a cold store, the plan gave each package no view. It therefore left native roles unexamined and omitted their writes and setup identity from the hash. The applying run materializes the package first, so it planned those writes and refused `plan.stale`.
- **Fix:** an absent store artifact is now examined from its exact locked bytes in the approved tap cache (`mask_store.cached_payload`), which never fetches or writes. The view is rooted at the future store path. Setup proposals use the same bytes (`mask_setup.files_snapshot`). The hash inputs are unchanged.
- **Checks:** Windows 11 Home 10.0.26200, Python 3.14.6, Git 2.55.0.windows.3.
  - `tests.test_cold_store_plan_hash` passes 7 tests.
  - The negative control on an archive of `1afd8b1` fails 3 tests, exactly at `plan.stale`. The 4 guard tests pass on both revisions.
  - The guarded per-module suite at `8ea0fe5` passes 52/52 modules (460 tests, 17 skipped). The structure gate reports 0 violations.
- **Behavior to note:**
  - When the cache lacks the locked commit, the preview stays unexamined as before, and the contract says so.
  - On a cold store, `plan`, `doctor`, `list` and `--check` now read the exact cached payload, so a corrupt cached payload shows up as a blocker.
- **Review:** no independent review. The reviewer route (`claude-fable-5-1`) was at its usage limit throughout d7, and no alternate route is authorized (owner question Q6).
- **Limitations:** macOS was not exercised, and the run was not the literal single-process suite.
