---
schema: "implement-rfc.card.v1"
id: "MASK-0136"
title: "The full test suite passes on Windows"
status: "Ready"
rfcs: []
depends_on: []
platforms: ["win"]
metadata: {}
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
