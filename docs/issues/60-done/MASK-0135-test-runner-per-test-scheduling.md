---
schema: "implement-rfc.card.v1"
id: "MASK-0135"
title: "scripts/run_tests.py schedules tests, not classes, so one long class stops setting the wall time"
status: "Done"
rfcs: []
depends_on: []
platforms: ["win", "mac", "linux"]
metadata: {}
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"29b0af156a22cb0ca6dd5a9dd6aaa2c5d934fbb6","evidence":{"kind":"command","detail":"python -B scripts/run_tests.py -k test_terminal_progress -j 4 --slowest 3: 7 tests in 2 classes, one process per test id; the failing test printed under its test id with a 'rerun: python3 -m unittest tests.test_terminal_progress.TerminalPresentation.test_review_groups_links_but_keeps_setup_and_exact_replacements' line; --slowest lists test ids; -k no_such_test prints 'No tests match.' and exits 1. Full runs: 578 tests in 113 classes reported."}},{"criterion":"AC2","outcome":"pass","revision":"29b0af156a22cb0ca6dd5a9dd6aaa2c5d934fbb6","evidence":{"kind":"command","detail":"Clean worktrees, Windows 11, 20 workers, same product code: per-class runner 1079 s (76e00d1), per-test runner 782 s (29b0af1). Failing tests per-test (13) are a subset of per-class (14); the one difference, BundleTests.test_bundle_uninstall_uses_frozen_receipt_without_catalogue_or_network, depended on order and was fixed by MASK-0136. No failure comes from shared-process execution."}},{"criterion":"AC3","outcome":"pass","revision":"29b0af156a22cb0ca6dd5a9dd6aaa2c5d934fbb6","evidence":{"kind":"command","detail":"docs/guides/development.md and docs/architecture/test-boundaries.md describe per-test scheduling; python scripts/verify_documentation.py --root .: 0 structural violations."}}]
---

# MASK-0135: scripts/run_tests.py schedules tests, not classes, so one long class stops setting the wall time

Owner request, 2026-10-03, after MASK-0134.

## What happened

`scripts/run_tests.py` runs each TestCase class in its own process, one per
CPU. On Windows (20 workers), the full run at the MASK-0134 baseline took
2,318 s. That was exactly the time `tests.test_bundles.BundleTests` took to run
its 38 tests one after another; `UpgradeCommit` took 1,959 s. After MASK-0134
the run took 1,101 s, and `BundleTests` was again the whole wall time. Most
workers sit idle for the second half of the run.

No test uses `setUpClass`, `setUpModule` or another class or module fixture.
Every test builds its own temporary fixture in `setUp`. Running each test in
its own process therefore keeps what every test checks and how it is isolated.

## Acceptance

- AC1: The runner schedules one `python -B -m unittest TEST_ID` process per
  test. Tests of the largest classes start first. Failure output, the
  "rerun:" lines and `--slowest N` name test ids. `-k TEXT` selects tests whose
  dotted id contains TEXT, so an existing class or module selection still
  works. A module that fails to import still stops the run with the existing
  message. The summary reports tests, classes, skips and failures.
- AC2: On this Windows host, the full run's wall time is reported before and
  after, on the same tree. The set of failing tests is unchanged, apart from
  failures that come from running tests in a shared process; any such failure
  is named.
- AC3: `docs/guides/development.md` and `docs/architecture/test-boundaries.md`
  describe the per-test scheduling. `python scripts/verify_documentation.py
  --root .` passes.

Scope: `scripts/run_tests.py`, the two docs, and this card's bookkeeping. No
test changes. Making the tests themselves cheaper is MASK-0137.

## Closeout

Implemented at `29b0af1`. On the same product code (`76e00d1` and `29b0af1`
differ only in the runner and its docs), in clean worktrees on this Windows
host with 20 workers: one process per class took 1,079 s, and one process per
test took 782 s. Running each test alone added no failure. One test that failed
in the class run passed alone:
`BundleTests.test_bundle_uninstall_uses_frozen_receipt_without_catalogue_or_network`.
Whether its loose Git objects were still read-only when it ran depended on
order, and MASK-0136 fixed it.

The new floor is the slowest single tests (up to 150 s under 20-way load) and
total CPU work, not class packing. MASK-0137 owns that.
