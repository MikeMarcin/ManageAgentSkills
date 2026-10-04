# Compact upgrade output verification

MASK-0138 was implemented directly on main from baseline
`ee8bb172465f6a2b47307e1e0bace4eea7642fc8`. Implementation: `e0079d9fdb3ab7419fd58fd5e3722fda795de21d`; final source
revision: `f0cf20fbdeac364ea4a4becfba897e5d81efd4ad`.

The default review groups versions, bundles, setup and local commits. Full scope,
version identities, script fingerprints and role names remain available through
`d` in the same approval prompt. Viewing details grants no authority. Existing
control edits included in commits, blocked consumers and replacement paths stay
visible in the compact review. Progress overwrites one terminal line and clears
before consent or final results, including with NO_COLOR. Results count unique
skills, completed setup and commits; failures name exceptions and unstarted setup.
A stale setup identifies its consumer without claiming earlier setup never ran.

| Criterion | Evidence | Outcome |
|---|---|---|
| AC1 | Large 15-location presentation fixture; grouped bundle additions; exact replacement disclosure; public details/decline and details/approval terminal journeys | Pass |
| AC2 | Live blocked-setup heartbeat through a public PTY; terminal overwrite/clear simulation; JSON on a PTY; existing pipe/color checks | Pass |
| AC3 | Large 11-of-14 partial-result fixture; public two-consumer upgrade with input mutation after first setup; commit failures with retained commits; grouped overlap warnings | Pass |
| AC4 | Focused lifecycle, commit, consent, bundle and output checks below; documentation gate and whitespace check | Pass |

Focused test runs used `python3 -B scripts/run_tests.py` with explicit selectors:

- Initial lifecycle/commit/consent integration: 66 tests in 9 classes, no failures
  or skips, 63 seconds. Selectors: `tests.test_upgrade_readiness`,
  `tests.test_upgrade_commit`, `tests.test_terminal_progress`,
  `tests.test_cli_v2.SetupV2`, `tests.test_consent`.
- Output/readiness integration: 45 tests in 7 classes, no failures or skips,
  30 seconds. Selectors: `tests.test_compact_upgrade_output`,
  `tests.test_upgrade_readiness`, `tests.test_human_output`,
  `tests.test_terminal_progress`. Four additional bundle selectors in this run
  named a nonexistent class and selected no tests; the final affected run below
  uses the real `BundleTests` class.
- Final affected checks: 17 tests in 5 classes, no failures or skips, 18 seconds.
  Selectors: `tests.test_compact_upgrade_output`,
  `tests.test_terminal_progress.TerminalPresentation`,
  `tests.test_upgrade_readiness.UpgradeReadiness.test_noninteractive_upgrade_requires`,
  `tests.test_upgrade_readiness.UpgradeReadiness.test_terminal_details_are_read_only`,
  `tests.test_upgrade_commit.UpgradeCommit.test_human_output`, and
  `tests.test_bundles.BundleTests` methods beginning with
  `test_overlap_and_bounded_replace`, `test_upgrade_combines`,
  `test_upgrade_all_installed`, `test_unchanged_definition`.

Initial unit checks exposed two assertions for the superseded verbose layout;
updated assertions check compact disclosure and preservation of full details.
The final focused runs pass. A final scope correction preserves the existing
preparation diagnostics for commands other than upgrade; all 15 affected unit
checks pass afterward. Self-review removed an unused argument and shared
setup-state mappings; checked consent, stale-plan preservation and failure counts.

All three fixture runs used the installed qualification guard, local bare taps
and allowed root `/private/tmp/mask-compact-upgrade-output/fixtures`. Guard receipts
in `/tmp/mask-compact-upgrade-output/{guard,final-guard,affected-guard}.json` report
success and unchanged selected live files. Protected live files include both
repositories' declarations/locks; the first two runs also check MASK's workflow
configuration. This cooperative before/after comparison covers selected bytes;
it does not sandbox commands or prove absence of transient or undeclared writes.
All test subprocesses finished and fixture cleanup completed.

The public partial-failure fixture verifies that the first consumer's roles are
published, the second consumer's links remain activated without generated roles,
no pending journal remains, and the human report identifies the stale location.
The terminal details tests verify no links, setup or publications after decline,
one script run after approval, and stale input refusal after viewing details.
JSON stays one result document; no result schema or mutation policy changed.

Documentation validation reports 24 RFCs, 138 cards and zero structural violations.
`git diff --check` passes. Native PTY checks ran on macOS; no Windows run is claimed.
The existing launcher was read and points to this source checkout. No agents were
delegated, settings changed, live upgrades run or source published. Preexisting
`.mask.json` and `.mask.lock.json` changes remain outside task commits.

Current frontier: AC1–AC4 accepted; no engineering work remains. The original
direct checkpoint and completion receipts are retained in
`/tmp/mask-compact-upgrade-output/`. No pending decision, review candidate or task
command remains. Finish commits this evidence together with the Done card.
