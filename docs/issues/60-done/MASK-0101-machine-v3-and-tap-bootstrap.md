---
schema: "implement-rfc.card.v1"
id: "MASK-0101"
title: "Add config v3, tap-add bootstrap and tap-first fixtures"
status: "Done"
rfcs: ["RFC-MASK-0021"]
depends_on: ["MASK-0100"]
priority: "P1"
metadata: {"packet":"mask-corrective-managed-taps","provisional_id":false,"packet_key":"machine-v3-and-tap-bootstrap","milestone_plan":{"id":"tap-only-deployment","path":"docs/rfcs/plans/tap-only-deployment/milestone-plan.json"}}
acceptance: [{"criterion":"MASK-0101 AC1 (bootstrap:exit:1; RFC-MASK-0021-AC01 fixture evidence): an empty MASK_HOME plus tap add plus install deploys a v2 consumer with a bare cache, store-targeted links and no checkout on disk","outcome":"pass","revision":"94d4f1cd580dc63b7e1ec6c583b8009b96ee2abc","evidence":{"kind":"command","detail":"PYTHONDONTWRITEBYTECODE=1 python -B -m unittest -v tests.test_tap_bootstrap, with MASK_HOME, USERPROFILE and HOME redirected to empty directories (Windows 11 Home 10.0.26200, Python 3.14.6, Git 2.55.0.windows.3): 6 tests OK. B01: tap add on an empty MASK_HOME writes nothing on --dry-run, then creates config v3 with one tap, empty state and no cache. B02/B03: install --project and --user fetch once into one bare cache under MASK_HOME/sources and write v2 declarations and locks at the upstream HEAD. Records are mode pinned, and every recorded and on-disk link resolves under MASK_HOME/store/v1. No SKILL.md exists outside the store; the consumer project is the only Git work tree. Negative controls: the same test file against the pre-implementation product 5969744 failed 5 of 5; a copy that left an author checkout on disk failed at the no-checkout assertion. A guarded CLI smoke observed the same journey."}},{"criterion":"MASK-0101 AC2: init no longer accepts --source","outcome":"pass","revision":"94d4f1cd580dc63b7e1ec6c583b8009b96ee2abc","evidence":{"kind":"command","detail":"tests.test_tap_bootstrap test_init_writes_an_empty_catalog_and_refuses_the_retired_source_option: init --source X, with or without --remote/--branch, exits 2 invocation.invalid and creates no MASK_HOME. init --target codex --git-timeout 60 writes an empty v3 catalog and empty state, and a later install deploys only the codex link. tests.test_cli_protocol: init --source . is a JSON invocation.invalid (4 OK). capabilities lists the init arguments target and git_timeout only."}},{"criterion":"MASK-0101 AC3: tests/support.py and tests/public_support.py no longer call init --source","outcome":"pass","revision":"94d4f1cd580dc63b7e1ec6c583b8009b96ee2abc","evidence":{"kind":"observation","detail":"grep finds only docstring mentions in tests/support.py and tests/public_support.py. Fixture.init and PublicFixture.bootstrap run tap add agentskills <local bare upstream>. Legacy-behavior tests opt in through legacy_init/legacy_bootstrap, which write the schema-true v1 bytes from tests/legacy_support.py. The only remaining init --source invocations under tests/ are refusal checks in tests/test_cli_protocol.py and tests/test_tap_bootstrap.py."}},{"criterion":"MASK-0101 AC4 (bootstrap:exit:2): the full suite passes on the cut-over fixtures while legacy code still exists","outcome":"pass","revision":"94d4f1cd580dc63b7e1ec6c583b8009b96ee2abc","evidence":{"kind":"command","detail":"Windows 11 Home 10.0.26200, Python 3.14.6, Git 2.55.0.windows.3, HEAD 94d4f1c with product, schema, test and README files clean. Every tests.test_* module ran as its own python -B -m unittest -v tests.MODULE process (5 in parallel), with MASK_HOME, USERPROFILE and HOME redirected to empty per-module directories: 44 of 44 modules OK, 391 tests, 19 skipped, 1478 s. The tree hashes of the 95 product, schema, test and README files were identical before and after the run, as was the owner profile snapshot (~/.mask hashes; skill, agent and launcher entries). Legacy engine code is still present; the legacy-behavior tests pass on legacy_init/legacy_bootstrap starting states. The literal single-process command on the same HEAD, python -B -m unittest with MASK_HOME, USERPROFILE and HOME redirected to empty directories, finished exit 0: Ran 391 tests in 6477 s, OK (skipped=19). Tree hashes and the owner profile snapshot were unchanged across that run. macOS was not exercised (RFC-MASK-0021-AC08 closeout)."}},{"criterion":"MASK-0101 bounded work: config v3 accepted beside v1 and v2 without the migration gate; tap add creates config and state when missing; new declarations are v2 on a v3 machine; capabilities publish the new schema and readable versions","outcome":"pass","revision":"94d4f1cd580dc63b7e1ec6c583b8009b96ee2abc","evidence":{"kind":"command","detail":"tests.test_legacy_baseline: 7 OK (LegacyFixtureBytes parses v1/v2 bytes unchanged; LiveCheckoutBaseline still runs the legacy engine). tests.test_tap_bootstrap capabilities test: schemas.machine 3, readable_versions.machine [1, 2, 3], machine-v3 schema in the union. LegacyRecordsOnATapCatalog: legacy records kept by a bootstrapping tap add refuse migration.required for update, update --project, update --user and link adopt; inventory reports a typed per-consumer error; nothing is written. Guarded CLI survey on v3: every tap-model command exits 0, including crash recovery with --rollback and --complete. v1 stragglers refuse migration.required; source migrate, migrate, source status and no-name source fetch refuse source.legacy_absent. project init and user init on v3 write an empty v2 selection plus lock."}},{"criterion":"Carried obligation: replace the LiveCheckoutBaseline tests that call init --source (LegacyFixtureBytes stays)","outcome":"pass","revision":"94d4f1cd580dc63b7e1ec6c583b8009b96ee2abc","evidence":{"kind":"artifact","detail":"tests/test_legacy_baseline.py: LiveCheckoutBaseline starts from write_machine's v1 configuration, which matched init --source output at 82b4200. It still compares what install, source migrate, tap add and migrate --to-pinned write; 7 tests OK. docs/development/tap-cutover-baseline.md records the change."}},{"criterion":"Carried obligation: complete Windows full-suite reference separating the six existing failures from regressions","outcome":"pass","revision":"94d4f1cd580dc63b7e1ec6c583b8009b96ee2abc","evidence":{"kind":"artifact","detail":"docs/development/tap-cutover-baseline.md, section Runs: complete reference at d05bad8 with 43 modules in guarded per-module processes, 381 tests, 19 skipped, owner profile unchanged. It found ten existing failures (the six plus four in modules never observed before) and an import cycle that stopped two modules from loading alone. Each was diagnosed with a negative control and fixed in 01b2ae3."}},{"criterion":"Independent critical review of the candidate adjudicated","outcome":"pass","revision":"94d4f1cd580dc63b7e1ec6c583b8009b96ee2abc","evidence":{"kind":"observation","detail":"rfc-reviewer-critical (claude-fable-5-1, high effort) reviewed 01b2ae3 and found no blocking finding against the acceptance claims. Two changed-surface defects (update silently skipping legacy records on v3; inventory and link adopt exit 10) were fixed in 94d4f1c. Each was covered by a regression test that failed on 01b2ae3 and passes on 94d4f1c. Non-blocking notes are recorded in the card's Execution record."}}]
---

# MASK-0101: Add config v3, tap-add bootstrap and tap-first fixtures

Governing RFC: [RFC-MASK-0021](../../rfcs/RFC-MASK-0021-tap-only-deployment.md). Live IDs reconciled after rebase; the reservation is `f81155a`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-managed-taps.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-managed-taps/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-managed-taps/ACCEPTANCE.md).

## Objective and owned paths

`mask_core.py` (`config`), `mask_sources.py` (`validate_config`, `selected`, `dispatch`), `mask.py` (`init`, `capabilities`), `schemas/machine-v3.schema.json`, `schemas/machine.schema.json`, `mask_task.py` (`fresh_declaration`), `tests/support.py`, `tests/public_support.py`, `tests/test_sources.py`, `tests/test_cli_protocol.py` and the tests those fixtures feed.

## Bounded work

Accept machine config v3 beside v1 and v2 without the migration gate yet. Make `init` write an empty v3 catalog without `--source`, and make `tap add` create config and state when they are missing. New declarations become v2 on a v3 machine. Cut both test fixture bases over to a local bare repository added as a `file` tap followed by `install`; keep every existing test green while legacy code still exists. Publish the new schema and readable versions through `capabilities`.

## Acceptance

An empty `MASK_HOME` plus `tap add` plus `install` deploys a v2 consumer with a bare cache and store-targeted links and no checkout on disk. `init` no longer accepts `--source`. `tests/support.py` and `tests/public_support.py` no longer call `init --source`. The full suite passes on the cut-over fixtures.

Criterion coverage: RFC-MASK-0021-AC01, RFC-MASK-0021-AC05.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary (subprocess argv, exit code, JSON stdout, stderr,
filesystem and Git effects). Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Not started. Claim the live remapped card before edits. No code implementation,
native result, host loading, user approval or migration of a real machine is
asserted by this card's existence.

## Execution record

Dispatch `d2` of run `mask-rfc0020-2026-09-12-a`, milestone `bootstrap`. Claim `5969744`. Implementation is `01b2ae3640e22a463d42355800cbac6159e67802`, followed by the review fix `94d4f1c`. The heading above ends the bound Acceptance text, so this record does not change the milestone binding.

Host: Windows 11 Home 10.0.26200, Python 3.14.6, Git 2.55.0.windows.3. Every run redirected `MASK_HOME`, `USERPROFILE` and `HOME` to empty directories. The owner's profile snapshot was identical before and after each suite run. macOS was not exercised.

### Acceptance evidence

- **Tap-first bootstrap:** `python -B -m unittest -v tests.test_tap_bootstrap` passes 5 tests.
  - `tap add` on an empty `MASK_HOME` writes nothing with `--dry-run`. Without it, it creates config v3 with one tap and an empty state, and fetches nothing.
  - `install` into a project and `--user` fetch once into one bare cache. They write v2 declarations and locks at the upstream HEAD and record `mode: pinned`. Every recorded and on-disk link resolves under `MASK_HOME/store/v1`.
  - No `SKILL.md` exists outside the store, and the consumer project is the only Git work tree.
  - Negative controls: the same test file against the pre-implementation product failed 5 of 5. A copy that left an author checkout on disk failed at the no-checkout assertion.
- **`init --source` is gone:** it exits 2 `invocation.invalid` and creates nothing. `init --target codex --git-timeout 60` writes an empty v3 catalog, and a later `install` deploys only the codex link.
- **Fixture bases:** `tests/support.py` and `tests/public_support.py` bootstrap with `tap add agentskills <local bare upstream>`. Neither calls `init --source`; the only remaining invocations are the refusal checks in `tests/test_cli_protocol.py` and `tests/test_tap_bootstrap.py`. Tests of retired behavior start from the schema-true v1 bytes through `legacy_init` or `legacy_bootstrap`, until MASK-0102, MASK-0103 or MASK-0104 removes that behavior.
- **Full suite:**
  - Before the review, per-module runs on the integrated tree passed all 44 modules. The first run covered 35 modules and 287 tests; the second covered 11 modules and 137 tests, including the two corrected modules.
  - A single-process run on `01b2ae3` was stopped after 75 clean results so the review fix could land. Its later log entries are a teardown artefact, not evidence.
  - **Final per-module run on `94d4f1c`:** every `tests.test_*` module ran in its own guarded process. All 44 modules passed: 391 tests, 19 skipped, 1478 s. The 95 product, schema, test and README file hashes were identical before and after the run, and so was the owner profile snapshot.
  - **Literal single-process `python -B -m unittest` on `94d4f1c`:** exit 0, 391 tests in 6477 s, OK with 19 skipped, under the same profile guard. Tree hashes and the owner profile were unchanged.
- **Bounded work:**
  - Config v3 is accepted beside v1 and v2; `LegacyFixtureBytes` still parses the legacy bytes unchanged.
  - `tap add` creates config and state when they are missing.
  - On v3, `install`, `project init` and `user init` create v2 declarations with locks.
  - `capabilities` publishes `schemas.machine` 3 and `readable_versions.machine` [1, 2, 3].
  - A guarded CLI survey ran every tap-model command on a v3 machine, including crash recovery with `--rollback` and `--complete`. On v3, v1 declarations and legacy records refuse `migration.required`, and `source migrate`, `migrate`, `source status` and no-name `source fetch` refuse `source.legacy_absent`.

### Carried obligations

- `LiveCheckoutBaseline` now starts from the builder's v1 configuration, whose bytes were compared with `init --source` output at `82b4200`. It still compares what the CLI writes after that point; 7 tests pass.
- The complete Windows reference at `d05bad8` is recorded in [tap-cutover-baseline.md](../../development/tap-cutover-baseline.md#runs). It shows 381 tests, ten existing failures, and an import cycle that stops two modules from loading alone. `01b2ae3` fixes all of them:
  - Failures 1, 3 and 4 were a product defect: selection-policy overrides rejected Windows device and inode numbers above 2^53−1.
  - Failures 2, 5, 6 and 7 were test I/O and path defects: locale or CRLF text writes, and a backslash path assertion.
  - Failure 8 was a CRLF skill fixture before publication.
  - Failure 9 was a clone commit without a Git identity under the profile guard.
  - Failure 10 was a tracked role checkout without `-text` under `core.autocrlf`.
  - The `mask_provenance`/`mask_resolve` import cycle was broken with a lazy import.

### Gaps found by the cutover and fixed

- On v3, `project init` and `user init` wrote v1 declarations that the same machine then refused.
- A manual `ensure` on an unapproved pinned consumer refused `integration.approval_required` before reaching the one-time consent that readiness defines. Preparation now applies the readiness rule: events need approval, and manual readiness gets consent.
- `mask_pinned.target` read a missing `source` block instead of refusing with a typed error.

### Independent review

- **Reviewer:** rfc-reviewer-critical reviewed `01b2ae3` against `5969744`. The requested and reported route was `claude-fable-5-1` at high effort, matching the generated role.
- **Named risks:**
  - persistence and compatibility of config v3 and the bootstrap;
  - the readiness authority change;
  - whether AC01 could be falsified;
  - typed refusals on v3;
  - integrity of the converted tests.
- **Verdict:** no blocking finding against the acceptance claims.
- **Two changed-surface defects, fixed in `94d4f1c`:** a v1 machine whose `config.json` is replaced by a bootstrapping `tap add` keeps its legacy records. On that machine:
  - `update` exited 0 with `project.empty_registry` and left even pinned consumers un-updated. It now refuses with `migration.required` naming the legacy roots.
  - `inventory` and `link adopt` exited 10. `inventory` now reports a typed per-consumer `migration.required` with no rows, and `link adopt` refuses with `migration.required`.
  - `tests/test_tap_bootstrap.py` `LegacyRecordsOnATapCatalog` builds that state through the public CLI.
  - Negative controls on `01b2ae3`: the test fails at `update` (exit 0), and a copy without the update assertions fails at `link adopt` (exit 10).
  - Focused runs on the fix passed: `test_tap_bootstrap` 6, `test_legacy_baseline` 7, `test_inventory` 6, `test_recovery` 7, `test_pinned_update` 11.
- **Fixed:** a builder-versus-builder config assertion in `LiveCheckoutBaseline` was removed; the `init --source` byte comparison stays the historical one at `82b4200`.
- **Accepted as non-blocking:**
  - An unapproved manual `ensure` hydrates the store from the local cache, offline, before its consent refusal, so the refusal reports `changed: true, transaction: partial`. No link, registration, policy or project byte changes, and no fetch happens.
  - The invalid-descriptor test in `test_workflow_deployment` now asserts that the pinned `update` fails closed, the lock is unchanged and nothing launches, instead of exercising `--repair`.
  - A crash between the bootstrap's config and state writes leaves config without state. Every reader defaults to an empty state.
  - Evidence from before the review was partly tied to an uncommitted tree. The final runs above record tree hashes.

### Contract notes and follow-up candidates

These are outside this card's acceptance:
- Retained-pack case B04 names `lock.resolution_required`, but an offline bare ID on a cold single tap returns `source.unresolved` naming the tap. The contract table lists both codes for this situation; a qualified coordinate returns `lock.resolution_required`.
- Under `core.autocrlf=true`, `source publish` hashes working bytes without filters, so it republishes LF blobs as CRLF.
- A wrong-branch authoring checkout reports `source.identity_mismatch` when it has an origin, and `source.detached` when it has none.
- An `ensure --dry-run` of a pinned consumer whose store is not yet materialized gives a plan hash different from the run that applies.
- A refused `apply --all` on a cold store reports `changed` with `partial`, because store preparation is retained.
- `project init` with no machine configuration still writes v1.
- Converted tests carry several local helpers (`declare_pinned` variants, `authoring_init`, `push`) that should be consolidated when MASK-0102 ports the legacy tests.

### Limitations

- POSIX-only terminal and launch tests were converted but are skipped on Windows.
- The shared-context end-to-end test runs only when `MASK_SHARED_SKILL` is set.
- `scripts/qualify_real_package.py` still calls `init --source` (MASK-0106).
- README prose beyond its bootstrap line, and the guides, still describe the checkout journey (MASK-0105).
