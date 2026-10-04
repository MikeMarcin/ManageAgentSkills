---
schema: "implement-rfc.card.v1"
id: "MASK-0133"
title: "mask update gets past a dirty program checkout, and Git Bash finds mask on Windows"
status: "Ready"
rfcs: []
depends_on: []
platforms: ["windows", "macos", "linux"]
metadata: {}
acceptance: []
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
