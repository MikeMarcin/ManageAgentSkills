---
schema: "implement-rfc.card.v1"
id: "MASK-0135"
title: "scripts/run_tests.py schedules tests, not classes, so one long class stops setting the wall time"
status: "Ready"
rfcs: []
depends_on: []
platforms: ["win", "mac", "linux"]
metadata: {}
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
