---
schema: "implement-rfc.card.v1"
id: "MASK-0110"
title: "Report a refusal after retained store preparation without claiming a partial consumer transaction"
status: "Done"
rfcs: []
depends_on: ["MASK-0100"]
priority: "P2"
metadata: {"origin":"RFC-MASK-0020 d2 follow-up candidate filed under mandate r2 (2026-09-13)","follow_up_of":"MASK-0099"}
acceptance: [{"criterion":"A refused apply --all on a cold store reports no consumer transaction and discloses the retained preparation","outcome":"pass","revision":"8ea0fe5","evidence":{"kind":"command","detail":"python -B -m unittest -v tests.test_retained_preparation_report: 7 OK, 1 skipped (POSIX pseudoterminal decline); collision and stale-guard refusals of apply --all on a cold store report transaction not_started with data.retained_preparation. Windows 11, Python 3.14.6, Git 2.55.0.windows.3. Logs: d7 session scratchpad d7-w3/logs/r2.log and d7-suite/out/test_retained_preparation_report.1.log (8ea0fe5). Negative control on git archive 1afd8b1: 6 failures, 1 error (d7-w3/logs/nr3.log)."}},{"criterion":"An unapproved manual ensure whose consent is declined reports no consumer transaction and discloses the retained preparation","outcome":"pass","revision":"8ea0fe5","evidence":{"kind":"command","detail":"Same module: the JSON confirmation refusal and a redirected-stdin human ensure without consent report not_started with the disclosure and a human 'retained preparation' line. Limitation: the typed interactive decline test is POSIX-only and was skipped on Windows; mask.py applies merge_preparation once in its top-level dispatch finally, so every refusal shares that reporting boundary."}},{"criterion":"In both cases no link, registration, policy or project byte changes","outcome":"pass","revision":"8ea0fe5","evidence":{"kind":"command","detail":"Same module compares project files, registry, integration and selection policy bytes and link texts before and after each refusal."}},{"criterion":"Commands that did apply consumer effects keep their current reporting","outcome":"pass","revision":"8ea0fe5","evidence":{"kind":"command","detail":"Same module: ensure --yes still reports committed and a warm no-op reports not_needed without the field. mask_pinned.merge_preparation rewrites only not_needed and not_started. tests.test_pinned_recovery keeps its committed, rolled_back and partial assertions; two refusal-before-consumer-effect assertions changed from partial to not_started as intended."}},{"criterion":"Bounded work: apply, ensure, install and update follow the rule and the CLI contract result description is updated","outcome":"pass","revision":"8ea0fe5","evidence":{"kind":"observation","detail":"install and update refusals after preparation are covered through in-process concurrent-writer injection in the same module; docs/architecture/cli-contract.md changed/transaction paragraphs, the Pinned consumers sentence and update step 6; docs/architecture/state-and-recovery.md; python scripts/verify_documentation.py --root . reports 0 structural violations at 8ea0fe5."}},{"criterion":"No regression","outcome":"pass","revision":"8ea0fe5","evidence":{"kind":"command","detail":"Guarded per-module suite on a disposable clone at 8ea0fe595489fe702a51b446f7ed1c6ec106de8f: 52/52 modules, 460 tests, 17 skipped, 0 failures, 0 errors, no reruns, 3313.5 s; clone HEAD and status and the owner's live files unchanged. Windows 11 only; not the literal single-process run. Summary: d7 session scratchpad d7-suite/out/summary.json."}}]
---

# MASK-0110: Report a refusal after retained store preparation without claiming a partial consumer transaction

## Evidence

[MASK-0099 execution record](MASK-0099-machine-v3-and-tap-bootstrap.md#contract-notes-and-follow-up-candidates):
- A refused `apply --all` on a cold store reports `changed` with `transaction: partial`, because store preparation is retained.
- An unapproved manual `ensure` hydrates the store from the local cache before its consent refusal, so the refusal also reports `changed: true, transaction: partial`, although no link, registration, policy or project byte changed.

## Bounded work

When a command refuses before any consumer effect, but MASK-owned store or cache preparation was retained, report the retained preparation separately from the consumer transaction state. Apply the same rule to `apply`, `ensure`, `install` and `update`, and update the CLI contract result description.

## Acceptance

Through the public CLI:
- A refused `apply --all` on a cold store reports no consumer transaction and discloses the retained preparation.
- An unapproved manual `ensure` whose consent is declined reports no consumer transaction and discloses the retained preparation.
- In both cases no link, registration, policy or project byte changes.
- Commands that did apply consumer effects keep their current reporting.

## Execution record

Dispatch `d7` of run `mask-rfc0020-2026-09-12-a`, producer `rfc-integrator-d7`, mandate revision `4`. Claimed at `4e8af51`. Implemented at `8ea0fe5` together with MASK-0109 (W3, `rfc-worker`, in a separate worktree, then cherry-picked onto main).

- **Behavior:**
  - When a command refuses before any consumer effect but MASK kept store or cache preparation, it now reports `transaction: not_started` with an additive `data.retained_preparation` object: `artifacts`, `directories` and `acquisitions`. `changed: true` remains, because the contract counts store artifacts as changes.
  - Human error output adds a "retained preparation" line and no longer lists planned actions that never ran.
  - A completed no-op still reports `committed`. Consumer transactions keep `committed`, `rolled_back` or `partial`.
  - `ensure --all --repair` no longer inherits `committed` from a scope that kept only preparation.
  - The shared rule also applies to `doctor --migrate`.
- **Checks:** Windows 11 Home 10.0.26200, Python 3.14.6, Git 2.55.0.windows.3.
  - `tests.test_retained_preparation_report`: 7 passed, 1 skipped (the POSIX pseudoterminal decline).
  - Negative control on an archive of `1afd8b1`: 6 failures and 1 error.
  - `tests.test_pinned_recovery`: two refusal assertions intentionally changed from `partial` to `not_started`.
  - The guarded per-module suite at `8ea0fe5` passes 52/52 modules (460 tests, 17 skipped). The structure gate reports 0 violations.
- **Review:** no independent review. The reviewer route (`claude-fable-5-1`) was at its usage limit throughout d7, and no alternate route is authorized (owner question Q6).
- **Limitations:**
  - The typed interactive decline is tested only on POSIX. On Windows the decline goes through the same top-level `merge_preparation` boundary.
  - `install` and `update` refusals after preparation are exercised by injecting a concurrent writer in-process.
  - macOS was not exercised, and the run was not the literal single-process suite.
