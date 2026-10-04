---
schema: "implement-rfc.card.v1"
id: "MASK-0137"
title: "The full test suite runs in minutes, not a quarter of an hour"
status: "Backlog"
rfcs: []
depends_on: ["MASK-0135"]
platforms: ["win", "mac", "linux"]
metadata: {}
---

# MASK-0137: The full test suite runs in minutes, not a quarter of an hour

Owner request, 2026-10-03: 18 minutes is far too long for what MASK does.

## What happened

After MASK-0134 the full Windows run still took 1,101 s for 578 tests on 20
workers. Most tests drive the real CLI as a fresh Python process (`call`,
`machine`, `raw`). Each CLI call imports MASK and runs dozens of contained Git
processes. An `install` is budgeted at 100 of them
(`SpawnBudgetTests.test_one_install_stays_within_its_git_process_budget`).
Every test also builds its own tap, upstream and project repositories from
scratch in `setUp`. Fifteen classes each take over 200 s.

## Acceptance

- AC1: A measured profile of the suite on this host names where the time goes:
  Git processes per CLI call, CLI calls per test, Python start and import, and
  fixture setup. It also lists the twenty most expensive tests.
- AC2: Reductions chosen from that profile, with each change justified by it.
  Candidates include:
  - removing repeated Git questions in the product, where the profile shows
    them (as MASK-0134 did for blob reads);
  - building fixture repositories once per process and copying them per test;
  - calling the CLI in-process where a test does not depend on a fresh
    process;
  - merging tests that repeat the same expensive setup to check neighbouring
    claims.

  No test loses a claim it checks. A test that moves from a subprocess to an
  in-process call keeps at least one subprocess-level test of the same
  behaviour.
- AC3: The full `python -B scripts/run_tests.py` wall time on this Windows
  host is reported before and after. The target is under 5 minutes. If the
  target is missed, the closeout records what is left and why. The set of
  failing tests does not grow.

Scope: tests, test support, and product hot paths that the profile names, plus
this card's bookkeeping. Process containment, journaling and readiness
semantics stay as they are.
