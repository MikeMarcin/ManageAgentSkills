---
schema: "implement-rfc.card.v1"
id: "MASK-0136"
title: "The full test suite passes on Windows"
status: "Done"
rfcs: []
depends_on: []
platforms: ["win"]
metadata: {}
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"7b6c6dbfa164fe6e01f5ca0f7b350b710b92cf30","evidence":{"kind":"observation","detail":"Each listed failure diagnosed at runtime on Windows 11 / Python 3.14 / Git 2.55 and recorded in the closeout: three product defects (cleanup placeholder repository without a drive, Windows execv re-exec quoting and held lifecycle.lock, RUNTIME_MODULES missing two modules) fixed in the product with the failing tests as regression checks, plus a new RUNTIME_MODULES guard test; the rest are test defects fixed without weakening assertions (UTF-8 JSON reads, LF authoring writes, read-only removal, bytes stdin, native fixture paths, complete program fixture, real package changes, current README replay). No platform skips were added."}},{"criterion":"AC2","outcome":"pass","revision":"7b6c6dbfa164fe6e01f5ca0f7b350b710b92cf30","evidence":{"kind":"command","detail":"Clean worktree at 7b6c6db: python -B scripts/run_tests.py -> 581 tests in 113 classes, 40 skipped, 0 failed, wall 830 s. Focused: tests.test_cli_v2.CleanupV2, tests.test_refresh_v2, tests.test_launcher guard, tests.test_readme_journeys (ReadmeText and ReadmeRecipes.test_everyday_commands) pass. POSIX paths: execv branch and cleanup placeholder (Path(abspath('/mask-cleanup')).resolve().as_uri() == 'file:///mask-cleanup') are unchanged in behaviour."}},{"criterion":"AC3","outcome":"pass","revision":"7b6c6dbfa164fe6e01f5ca0f7b350b710b92cf30","evidence":{"kind":"observation","detail":"Not reproduced: passed alone on both trees, 10/10 at 5-way concurrency, and in three later full runs (1079 s, 782 s, 830 s). Diagnosis path left: docs/guides/development.md documents GIT_TRACE2_EVENT; verified that c.git on a failing fetch reports only git.failed while the trace file records Git's error message ('Could not read from remote repository')."}}]
---

# MASK-0136: The full test suite passes on Windows

Owner request, 2026-10-03: failing MASK tests on Windows get fixed.

## What happened

On Windows 11 with Python 3.14 and Git 2.55 (`core.autocrlf=true` globally),
`python -B scripts/run_tests.py` fails these tests at the pre-MASK-0134 HEAD
`aa38f33`. They fail the same way after MASK-0134, except where noted.

| Test | Symptom |
|---|---|
| `test_artifacts.ArtifactTests.test_cache_types_unknown_contents_and_concurrent_atomic_churn` | `PermissionError` [WinError 5] / `FileExistsError` [WinError 183] in the store's `__pycache__`; `Artifacts require unlinked regular files and real directories.` |
| `test_bundles.BundleTests.test_bundle_uninstall_uses_frozen_receipt_without_catalogue_or_network` | `PermissionError` [WinError 5] on a loose object under `machine/sources/*.git/objects` |
| `test_cli_v2.CleanupV2.test_cleanup_references_unknown_content_and_stale_review` | expected cleanup references list is empty |
| `test_readme_journeys.ReadmeText.test_replayed_text_is_the_readme_text` | replayed README sections differ from the README |
| `test_recovery_entrypoint.RecoveryEntrypoint` (3 tests) | `KeyError` on `str(self.project)` in `pending['after_state']['projects']` |
| `test_refresh_v2.RefreshV2.test_freshness_no_update_offline_and_reviewed_application` | `upgrade` returns `internal.invariant` |
| `test_refresh_v2.RefreshV2.test_program_update_reexecutes_before_install` | re-exec of the interpreter splits `C:\Program Files\...` at the space |
| `test_terminal_progress.TerminalPresentation.test_review_groups_links_but_keeps_setup_and_exact_replacements` | `'2 skill links'` missing from the review text |
| `test_upgrade_commit.UpgradeCommit.test_full_partially_staged_controls_and_new_version_exclude_other_files` | LF expected, CRLF read back. It timed out at 60 s at the baseline, but fails the same way there when run alone |
| `test_upgrade_commit.UpgradeCommit.test_unmerged_index_refuses_and_preserves_index` | `TypeError: 'NoneType' object is not subscriptable` |
| `test_workflow_profiles.WorkflowProfileTests.test_development_checks_are_observational_in_both_scopes` | `source.line_endings_converted` under `core.autocrlf=true` |

One failure was seen only once, under full 20-worker load after MASK-0134:
`BundleTests.test_aggregate_upgrade_recovery_uses_frozen_membership_and_package_rows`
got `git.failed` (operation `-c`) from `tap fetch`. It passed alone on both
trees and 10 times out of 10 at 5-way concurrency. MASK hides Git's stderr, so
the cause is unknown.

## Acceptance

- AC1: Each listed failure is diagnosed as a product defect or a test defect,
  with the reason recorded in the closeout. A product defect is fixed in the
  product, with the test kept as the regression check. A test defect is fixed
  without weakening what the test checks. A platform-only skip needs the
  owner's agreement.
- AC2: The full `python -B scripts/run_tests.py` passes on this Windows host,
  run in a clean worktree. Focused suites for any changed product module pass,
  and non-Windows behaviour is unchanged.
- AC3: The load-only `tap fetch` failure is either reproduced and fixed, or
  left with a way to diagnose it next time (for example, Git's redacted stderr
  in the test failure output). Which one happened is recorded.

Scope: the failing tests, the product modules their diagnosis names, and this
card's bookkeeping. MASK-0135 and MASK-0137 own runner speed and test cost.

## Closeout

Implemented at `7b6c6db`. In a clean worktree at that commit on this Windows
host, `python -B scripts/run_tests.py` ran 581 tests in 113 classes: 0 failed,
40 skipped, 830 s.

Product defects, fixed in the product:

- `mask cleanup` checked every store artifact against `file:///mask-cleanup`.
  That URL has no drive on Windows, so validation refused every artifact,
  cleanup preserved them all and never collected anything (`CleanupV2`).
- After a program update, `os.execv` re-ran MASK. On Windows it does not quote
  arguments, so `C:\Program Files` split at the space. It also keeps
  `lifecycle.lock` held, because the process is not replaced (`RefreshV2`).
  `mask.main` now runs the updated program after the stack has unwound and
  exits with its status. POSIX keeps `execv`.
- `update`'s `RUNTIME_MODULES` lacked `mask_bundles.py` and
  `mask_upgrade_commit.py`. A new test keeps the list equal to the program's
  modules.

Test defects, fixed without weakening any check:

- MASK's JSON was read as cp1252, which mangled the `ü` path key
  (`RecoveryEntrypoint`). All 50 `json.loads(...read_text())` reads now use
  UTF-8.
- Authoring files were written CRLF over LF commits
  (`WorkflowProfileTests`, `UpgradeCommit` partially-staged).
- Read-only Git objects and hard-linked store files were deleted without making
  them writable first (`ArtifactTests`, `BundleTests` uninstall).
- `update-index` input went through a text stdin, which turned `\n` into `\r\n`
  (`UpgradeCommit` unmerged).
- POSIX literal paths were matched against native roots
  (`TerminalPresentation`).
- The program fixture copied a stale module list. The refresh test published
  empty commits, which MASK-0125's stable locks keep at the old commit
  (`RefreshV2`).
- `ReadmeText` was stale against the README.

At the owner's request, the README's Everyday commands are ordered by task and
use a `TAP/BUNDLE` placeholder. The replay runs every row, including the bundle
commands and `upgrade --commit`.

The one-off `tap fetch` `git.failed` under load did not recur, in isolation, at
5-way concurrency or in any later full run. MASK withholds Git's stderr by
design, so credentials never reach a result. `docs/guides/development.md` now
explains how to get Git's message for the next occurrence with
`GIT_TRACE2_EVENT`; this was verified through `c.git`.
