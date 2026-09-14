---
schema: "implement-rfc.card.v1"
id: "MASK-0108"
title: "Refuse a wrong-branch authoring checkout with one typed code whether or not it has an origin"
status: "Done"
rfcs: []
depends_on: ["MASK-0100"]
priority: "P2"
metadata: {"origin":"RFC-MASK-0020 d2 follow-up candidate filed under mandate r2 (2026-09-13)","follow_up_of":"MASK-0099"}
acceptance: [{"criterion":"A wrong-branch authoring checkout with an origin and one without produce the same code and exit, and write nothing","outcome":"pass","revision":"2848f6d","evidence":{"kind":"command","detail":"python -B -m unittest -v tests.test_authoring_branch_refusal: 7 tests OK (tap add --checkout, skill import destination, skill record-adaptation, source publish, source dev-link; each with and without an origin; fixture tree and checkout Git facts compared after every refusal). Windows 11, Python 3.14.6, Git 2.55.0.windows.3. Logs: d7 session scratchpad d7-w2/candidate-new-2.log and d7-suite/out/test_authoring_branch_refusal.1.log (8ea0fe5). Negative control on git archive 1afd8b1: 29 subtest failures (d7-w2/base-negative-control-2.log)."}},{"criterion":"A detached checkout and a missing origin keep their documented codes","outcome":"pass","revision":"2848f6d","evidence":{"kind":"command","detail":"Same module: a detached HEAD refuses source.detached (exit 4, details.configured_branch) with and without an origin; a lost origin keeps the path identity and source.identity_mismatch; the positive control on the configured branch succeeds."}},{"criterion":"Bounded work: every authoring-checkout observation uses the same refusal and the CLI contract names it","outcome":"pass","revision":"2848f6d","evidence":{"kind":"observation","detail":"mask_sources.authoring_branch is called by tap add --checkout, source publish and mask_provenance.authoring_checkout (import destination, record-adaptation, dev-link destination); import observes the destination before its fetch. docs/architecture/cli-contract.md 'Taps, payloads and caches' and the import-destination paragraph; python scripts/verify_documentation.py --root . reports 0 structural violations."}},{"criterion":"No regression","outcome":"pass","revision":"8ea0fe5","evidence":{"kind":"command","detail":"Guarded per-module suite on a disposable clone at 8ea0fe595489fe702a51b446f7ed1c6ec106de8f (every tests/test_*.py as its own python -B -m unittest -v process, private MASK_HOME/USERPROFILE/HOME, 3 workers): 52/52 modules, 460 tests, 17 skipped, 0 failures, 0 errors, no reruns, 3313.5 s; clone HEAD and status unchanged; owner ~/.mask, AgentSkills and this repository's declaration files unchanged. Windows 11 only; not the literal single-process run. Summary: d7 session scratchpad d7-suite/out/summary.json."}}]
---

# MASK-0108: Refuse a wrong-branch authoring checkout with one typed code whether or not it has an origin

## Evidence

[MASK-0099 execution record](MASK-0099-machine-v3-and-tap-bootstrap.md#contract-notes-and-follow-up-candidates): a wrong-branch authoring checkout reports `source.identity_mismatch` when it has an origin and `source.detached` when it has none.

## Bounded work

Make every authoring-checkout observation — `tap add --checkout`, `source publish`, `source dev-link` and import destinations — report a branch other than the configured one with the same typed refusal, independent of whether an origin exists. Keep a detached HEAD distinct only where the current contract names it. Update the CLI contract where it names these codes.

## Acceptance

Through the public CLI with disposable checkouts, a wrong-branch checkout with an origin and one without produce the same code and exit, and write nothing. A detached checkout and a missing origin keep their documented codes.

## Execution record

Dispatch `d7` of run `mask-rfc0020-2026-09-12-a`, producer `rfc-integrator-d7`, mandate revision `4`. Claimed at `72f13e2`; implemented at `2848f6d` (W2, `rfc-worker`, in a separate worktree, cherry-picked onto main).

- **Behavior:** these commands now check the configured branch first:
  - `tap add --checkout` and `source publish`;
  - `source dev-link` destinations, `skill import` destinations and `skill record-adaptation`.
  - Another branch refuses `source.identity_mismatch` (exit 4, with `details.branch` and `details.configured_branch`), and a detached HEAD refuses `source.detached`. Both apply with or without an origin.
  - A checkout with no origin is still identified by its own path.
  - Import observes the destination before its fetch, so its refusals write nothing.
- **Checks:** Windows 11 Home 10.0.26200, Python 3.14.6, Git 2.55.0.windows.3.
  - `tests.test_authoring_branch_refusal` passes 7 tests. The negative control on an archive of `1afd8b1` fails 29 subtests.
  - 17 existing modules that assert these codes pass.
  - The guarded per-module suite at `8ea0fe5` passes 52/52 modules (460 tests, 17 skipped). The structure gate reports 0 violations.
- **Behavior changes to note:** `tap add --checkout` now also refuses a tap whose `--ref` is not the checkout's branch, and `skill import --dry-run` on a cold cache refuses a bad destination before it reports `resolution_required`.
- **Review:** no independent review. The `rfc-reviewer-critical` attempt d7-R3 failed before producing output with HTTP 429 on `claude-fable-5-1`, and no alternate route is authorized (owner question Q6).
- **Limitations:** macOS was not exercised. The run was not the literal single-process suite. A tag with the same name as the branch makes `symbolic-ref --short` return `heads/<name>`, so such a checkout is refused. This edge is shared with `self update` and was not changed.
