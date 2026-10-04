---
schema: "implement-rfc.card.v1"
id: "MASK-0134"
title: "mask upgrade stops paying for a system-wide thread walk and a process per package file on Windows"
status: "In Progress"
rfcs: []
depends_on: []
platforms: ["win", "mac", "linux"]
metadata: {}
---

# MASK-0134: mask upgrade stops paying for a system-wide thread walk and a process per package file on Windows

Owner request, 2026-10-03, from the Windows BetterPullReview lane.

## What happened

`mask upgrade --all --commit` from PowerShell sat on `Fetching tap agentskills...`
for about 60 seconds, then on `Preparing locked skill content` and `Applying
skill links and version locks` for another 40. The network was not the cause:
`ls-remote` answered in about 1 s over both HTTPS and SSH, and an up-to-date
fetch transferred in 0.3 s.

A profiled `mask upgrade --all --dry-run --json` (no network) from PowerShell
on this host took 71 s before `Checking selected installations`. It spent that
time in 600 Git processes. Two multipliers explain it:

1. Each `c.git` call cost about 108 ms against 28 ms for a bare
   `subprocess.run`. `WindowsJob.start` resumes the suspended child by taking a
   `CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD)` of every thread on the machine
   (7,453 here) and walking it through ctypes to find the child's one thread.
   That walk alone costs 68 ms per spawn, and it grows with whatever else the
   machine runs. `CreateProcess` already returned the thread id; `Popen`
   discards it.
2. `mask_packages.validate` asks Git two questions per package file:
   `cat-file -s` and then `cat-file blob`. implement-rfc has 167 files, so one
   validation is about 334 processes. 438 `cat-file` calls took 51 of the 71 s.

The progress label made it look like a slow fetch: after the fetch, `dispatch`
resolves every consumer from the cache while `Fetching tap NAME` is still the
current phase.

## Acceptance

- AC1: A contained Windows spawn resumes its primary thread without a
  system-wide snapshot. `contained_run` keeps the primary thread id that
  `CreateProcess` returns for the spawn on the calling thread. `WindowsJob.start`
  assigns the process to the job first, as today. It then opens that thread,
  checks with `GetProcessIdOfThread` that the thread belongs to the process, and
  requires `ResumeThread` to report a prior suspend count of 1. Any mismatch
  is `git.containment_unavailable` and the suspended process is terminated,
  as today. The Toolhelp walk remains only for when no thread id was captured.
  Non-Windows behaviour is unchanged.
- AC2: One package validation runs a fixed number of Git processes, however
  many files it has. Sizes come from one `git cat-file --batch-check` and
  contents from one `git cat-file --batch`, both fed object ids on stdin.
  Per-file, cumulative and file-count limits are still checked before any
  content is read. Every batch header must name the requested object, type
  `blob` and the size already checked, or validation fails with
  `skill.object_invalid`. Answers fill the existing per-invocation frozen
  cache, so a later `git_frozen` question about the same blob spawns nothing.
  No filters, textconv or replace objects apply.
- AC3: After its tap fetches, `upgrade` shows its own phase while it resolves
  the selected consumers, so the fetch label stops when the fetch does.
- AC4: Evidence and checks. A spawn-budget test shows that validating a package
  with many files costs the same number of Git processes as validating one with
  few. A Windows test shows a contained spawn never takes a thread snapshot when
  the id was captured, and that a wrong or missing thread still refuses. The
  existing limit-before-read test also covers the batch read. On this host, a
  profiled `mask upgrade --all --dry-run --json` from PowerShell reports the
  before and after wall time and process count, and `c.git` overhead over a bare
  spawn is measured again. The focused suites and `python scripts/verify_documentation.py
  --root .` pass, and the full `scripts/run_tests.py` shows no failure that the
  pre-change HEAD does not also show.

Scope: `mask_process.py`, `mask_core.py`, `mask_packages.py`,
`mask_update.py`, `tests/test_subprocess_policy.py`,
`tests/test_import_safety.py`, and this card's bookkeeping. No change to what
is fetched, validated, locked or linked, and no change to the process
containment contract. The tap cache keeps only loose objects because fetches
disable auto-maintenance, and the fetch monitor rescans them every 50 ms. That
is real but small here (0.2 s per scan) and stays out of scope.
