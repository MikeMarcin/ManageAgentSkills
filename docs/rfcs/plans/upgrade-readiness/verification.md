# MASK 0.3 lifecycle verification

Selected work: MASK-0120, direct execution in the existing main checkout.
Baseline: `0b2e41fcabe629a8916bc3820b3394f8240e255a`.
The accepted surface and pin amendment supersede the original AC1–AC4 command
spellings, separate grants and all-registered default. Their ownership, recovery,
offline and failure-reporting obligations remain covered.

## Acceptance evidence

| Criterion | Observed result |
|---|---|
| AC5 | Shipped subprocess tests isolate current checkout, personal and all-registered targets; outside-checkout calls require a selector; contradictory selectors refuse. |
| AC6 | Register prepares a linked worktree at its existing locked commit; install/uninstall preserve incremental membership; unregister retains declarations; tap/untap, search and workflow-aware info work through the public CLI. |
| AC7 | Missing consent and terminal decline preserve consumer files. One approval covers setup plus exact regular-role backup/replacements. Changed review inputs refuse before publication. Cache acquisition and blocked-tap effects survive refusal reporting. |
| AC8 | Disposable program clones prove the 24-hour refresh window, explicit machine-home propagation, no-update/offline/reviewed-plan boundaries and re-execution into new program code before installation. Retired names refuse; capabilities and results use protocol v2; startup uses integration run. |
| AC9 | Cleanup removes verified unused artifacts, untapped caches and disposable backups; it preserves unknown files, referenced versions and active lock files. Stale reviews refuse. Lifecycle locking spans preparation; read-only verification preserves unexpected bytecode. |
| AC10 | README recipes replay through a disposable installed launcher. Help describes scopes and reviews. Real macOS launcher and host --version checks pass; host loading is not inferred. Shared callers have the source handoff below. |
| AC11 | Pin/unpin support SKILL or all skills in the chosen checkout, with explicit personal scope. Upgrade advances unheld skills and retains held commits while rebuilding missing generated roles. Unpin does not immediately upgrade. Listings expose version holds. |

Private journal/readiness regressions retain their test-only operation harness.
It is not installed and provides no public aliases. New lifecycle acceptance uses
the actual mask.py entrypoint. Recovery tests verify that interrupted setup is
never rerun, publication rollback preserves already committed link effects, and
invalid or changed outputs remain protected. The simplification pass removed
redundant candidate planning outside terminal review and separated task metadata
from plan replacement so refused tasks retain truthful acquisition reports.

## Test records

Local detailed logs and cooperative guard receipts are retained under
`.mask/sessions/upgrade-readiness/` (ignored runtime evidence):

- `qualification-v2.log` / `.json`: 58 tests, one native Windows skip; all selected
  checks passed and all 14 watched live files were unchanged.
- `qualification-final-v2.log` / `.json`: 24 checks after lifecycle corrections;
  all passed and the same watched files remained unchanged.
- `regression-rerun-v2.log`: 100 tests across 26 classes; four outdated fixture
  expectations in three classes were corrected. `last-fixture-fixes-v2.log`
  passes their three setup/scope cases; `refusal-effects-v2.log` passes the revised
  multi-scope refusal case and the public install refusal case.
- `corrected-v2.log`, `focused-fixes-v2.log`, `edge-fixes-v2.log`,
  `remaining-regressions-v2.log` retain intermediate failures. Their fixes were
  rerun in the guarded courses, regression batch and narrow logs above.
- `presentation-final-v2.log`: six passing renderer and human-diagnostic checks.
  `pin-list-final-v2.log`: seven passing pin-list, human-output and README checks.
- The initial `full-v2.log` ran 455 tests with 69 failure reports, 17 errors and four
  skips during migration. It is retained as failure evidence, not called a passing
  suite. Relevant failure groups were corrected and rerun as described above;
  unaffected passing engine checks were reused.
- `status-profiles-fixed-v2.log`: six passing public status/profile checks, including
  project and personal development links. Status uses an observational plan and
  reports development readiness without claiming a locked deployment.
- Documentation structure validation: 23 RFCs, 120 cards, zero violations.
  `git diff --check` passes.

The guard checks only the declared live files at course boundaries. It is a
cooperative comparison, not a sandbox or proof about every file or transient edit.
Fixtures use private MASK_HOME/personal roots, temporary consumers and local bare
remotes. No source publication, installed-skill migration or live readiness grant
was performed. The pre-existing MASK lock edits in both repositories remain
unrelated and preserved.

## AgentSkills source handoff

AgentSkills commit `f55aef4` updates canonical management instructions, negotiates
status versus the earlier ensure via advertised capabilities in workflow preflight,
and directs native-role drift back to repair. Its 12 preflight tests and 23 renderer
tests pass (`upstream-mask-v2.log`, `upstream-render-v2-fixed.log`). Both edited
packages pass passive author-byte validation and project/personal descriptor
validation (`upstream-payload-v2.log`). No installed payload is claimed updated.

## Native and review limits

No subagents or independent reviewer were used under the requested direct strategy.
This is primary engineering acceptance, not independent review. Native macOS
symlink, launcher and bounded host version observations are covered. The configured
Windows station `example-win-host` failed DNS resolution during the authorized
read-only SSH probe. Native Windows acceptance was not repeated and no Windows
success or real host skill-loading claim is made. Existing broader RFC native
acceptance obligations remain open; this card does not close those RFCs.
