---
schema: "implement-rfc.card.v1"
id: "MASK-0133"
title: "mask update gets past a dirty program checkout, and Git Bash finds mask on Windows"
status: "Done"
rfcs: []
depends_on: []
platforms: ["windows", "macos", "linux"]
metadata: {}
acceptance: [{"criterion": "AC1", "outcome": "pass", "revision": "d61d4d953246d449e56fc22f796d4d501dfe2f7b", "evidence": {"kind": "command", "detail": "python -B -m unittest tests.test_launcher (Windows 11, Python 3.14, local bare remotes in temp roots): test_dirty_checkout_fast_forwards_when_the_update_touches_none_of_it. A modified, an untracked and a staged path the update does not touch survive merge --ff-only (staging kept) and appear in program.preserved; merge-fails and crash-at-git faults on the dirty checkout recover with --rollback and --complete; overlapping dirt refuses --complete with source.dirty and blocking_paths; rollback still clears. Ahead/diverged/detached/identity/in-progress holds unchanged (same checkout_preconditions checks)."}}, {"criterion": "AC2", "outcome": "pass", "revision": "d61d4d953246d449e56fc22f796d4d501dfe2f7b", "evidence": {"kind": "command", "detail": "python -B -m unittest tests.test_launcher (Windows 11, Python 3.14, local bare remotes in temp roots): test_overlapping_changes_hold_the_program_and_name_the_way_out (held, source.dirty, sorted blocking_paths, preserved, tap still fetched, exit 0; human output names five paths, then 'and 2 more', and suggests mask update --stash, all lines 80 columns or fewer) and test_file_where_the_update_has_a_directory_blocks."}}, {"criterion": "AC3", "outcome": "pass", "revision": "d61d4d953246d449e56fc22f796d4d501dfe2f7b", "evidence": {"kind": "command", "detail": "python -B -m unittest tests.test_launcher (Windows 11, Python 3.14, local bare remotes in temp roots): test_stash_moves_only_the_blocking_paths_and_never_applies_them (--dry-run --stash names paths, touches nothing; --stash stashes only blocking paths incl. untracked, message mask update <before>..<candidate> <UTC>, commit/message/inspect reported in JSON and human output, stash never popped, non-blocking dirt kept; no overlap does nothing extra; upgrade --stash exits 2) and test_failure_after_the_stash_keeps_it_journaled_and_recovery_reports_it (merge failure after stash leaves HEAD at before with stash commit in pending.json; recover/--rollback report it; crash at the stash checkpoint completes forward and reports it)."}}, {"criterion": "AC4", "outcome": "pass", "revision": "d61d4d953246d449e56fc22f796d4d501dfe2f7b", "evidence": {"kind": "observation", "detail": "Tests: test_launcher_style_follows_its_name and test_windows_writes_a_git_bash_launcher_beside_mask_cmd (unrelated mask kept and reported as launcher.collision, rerun adds the sh launcher, LF, no backslashes, digested state records, Git Bash runs it by bare name, edited sh launcher kept by uninstall, both removed otherwise). Live on this host: python mask.py self install --bin-dir C:/Users/mikem/AppData/Local/Programs/MASK --json applied launcher.install for mask.cmd and mask (exit 0). From Git Bash (/usr/bin/bash): command -v mask = /c/Users/mikem/AppData/Local/Programs/MASK/mask; mask --help exit 0; mask update --dry-run --json exit 0, ok true, program held source.ahead (expected: local commits not pushed)."}}, {"criterion": "AC5", "outcome": "pass", "revision": "d61d4d953246d449e56fc22f796d4d501dfe2f7b", "evidence": {"kind": "command", "detail": "Help text for update, --stash and self install in mask_present.py; README, installation, sources-and-updates, recovery guides and cli-contract updated. Tests placed in tests/test_launcher.py, the current owner of the update journal and launcher tests, because tests.test_refresh_v2 already fails on Windows at the baseline (spaced interpreter re-exec). Focused run of launcher/installer/human_output/cli_protocol/cli_v2/update/recovery/consent/readme_journeys/host_integration/task_commands/public_baseline: the only failures (public_baseline x3 classes, readme_journeys.ReadmeText, cli_v2.CleanupV2) fail identically on a git archive of the pre-change HEAD. verify_documentation: 0 violations; git diff --check clean."}}]
---

# MASK-0133: mask update gets past a dirty program checkout, and Git Bash finds mask on Windows

Owner request, 2026-10-03, from the Windows BetterPullReview lane.

## What happened

1. In Claude Code, `! mask update` ran in Git Bash and failed with
   `mask: command not found`. The Windows install writes only
   `%LOCALAPPDATA%\Programs\MASK\mask.cmd`, and Git Bash won't run a `.cmd`
   by its bare name. From PowerShell the same command worked.
2. From PowerShell, `mask update` printed
   `MASK was not updated: this checkout has uncommitted changes.` The program
   checkout was 50 commits behind `origin/main`. Its only dirt was
   `.mask.lock.json`, which `mask upgrade` had rewritten: the MASK checkout is
   itself a registered consumer. The incoming commits also changed that file,
   so nothing short of a manual `git stash` (done by hand on 2026-10-03)
   moved the program forward. Every refusal looks the same, and none
   of them says which path is in the way or what to run.

The repository rule stays: no force overwrite and no implicit reset. The way
out preserves every byte and says where it went.

## Acceptance

- AC1: A dirty checkout whose changes do not touch the update still
  fast-forwards. `mask update` advances when no modified, staged or untracked
  path appears in `git diff --name-only --no-renames HEAD <candidate>`. Git's
  own `merge --ff-only` keeps those changes. The result lists them under
  `program.preserved`. An interrupted fast-forward of such a checkout recovers
  through `recover` in both directions: the dirt check that `recover_git` uses
  tolerates the same non-overlapping changes. Every other hold (ahead,
  diverged, detached, identity, a Git operation in progress) is unchanged.
- AC2: An overlap names its paths and the way out. When local changes do
  touch the update, the program stays `held` with code `source.dirty`. The
  result carries `program.blocking_paths` (sorted, repository-relative). Human
  output names up to five of them and suggests `mask update --stash`. Taps are
  still fetched.
- AC3: `mask update --stash` moves only the blocking paths aside. It runs
  `git stash push --include-untracked -m "mask update <before>..<candidate>
  <UTC time>" -- <blocking paths>`, then fast-forwards. It never pops or
  applies the stash. The result and human output give the stash's commit id
  and message, plus `git stash show -p <id>` to inspect it. Non-blocking
  changes stay in the working tree, as in AC1. With no overlap, `--stash` does
  nothing extra. `--dry-run --stash` reports the paths it would stash and
  touches nothing. A failure after the stash but before the advance leaves the
  checkout at `before` with the stash recorded in the pending intent, and
  recovery reports it. `--stash` is accepted only by `update`.
- AC4: On Windows, Git Bash finds a working `mask`. Next to `mask.cmd`,
  `mask self install` writes an extensionless POSIX launcher `mask`: LF line
  endings, `#!/bin/sh`, `MASK owned launcher v1`, and interpreter and entry
  paths in forward-slash form. Each launcher is owned, digested, journaled,
  collision-checked (an unrelated or edited `mask` is kept and reported) and
  removed by `mask self uninstall` exactly as `mask.cmd` is today. Rerunning
  `mask self install` adds the missing sh launcher to an existing install.
  Non-Windows behaviour is unchanged. Evidence: on this Windows host, `mask
  --help` and `mask update --dry-run --json` succeed from Git Bash
  (`/usr/bin/bash`) through the reinstalled launcher.
- AC5: Docs and checks. Update the `update` help text in `mask_present.py`,
  `docs/guides/installation.md`, `docs/guides/sources-and-updates.md`,
  `docs/guides/recovery.md` and README where they describe the held states or
  the Windows launcher. Add focused tests to `tests/test_launcher.py`,
  `tests/test_installer.py` and `tests/test_refresh_v2.py` (or their current
  owners) for AC1 to AC4, using temporary fixture roots and local bare
  remotes. The focused suites and `python scripts/verify_documentation.py
  --root .` pass.

Scope: `mask_update.py`, `mask_install.py`, `mask_git.py`, `mask_cli.py`,
`mask_present.py`, the named tests and guides, and this card's bookkeeping. No
change to how `upgrade` writes consumer locks. Whether the program checkout
should commit its own `.mask.lock.json` after an upgrade is MASK-0130's
territory and stays out of scope. No publication and no push.

The stash `stash@{0}` "stale .mask.lock.json held by mask update
(implement-rfc 827aa3b), 2026-10-03" in the owner's Windows program checkout
is the owner's data. Leave it alone.

## Closeout

Implemented at `d61d4d9`. Tests for AC1 to AC4 live in `tests/test_launcher.py`.
Recovery `--rollback` never moves the checkout, so it tolerates any local changes;
`--complete` refuses only overlapping ones. The owner's `stash@{0}` was not touched.
