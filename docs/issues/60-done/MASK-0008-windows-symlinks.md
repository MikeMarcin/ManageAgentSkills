---
schema: "implement-rfc.card.v1"
id: "MASK-0008"
title: "Verify native Windows symlink safety"
status: "Done"
rfcs: ["RFC-MASK-0002"]
depends_on: ["MASK-0007"]
metadata: {"platform":"windows"}
---

# MASK-0008: Verify native Windows symlink safety

## Objective and owned paths

Own native Windows test adjustments and this card; no global privilege changes.

## Bounded work

On native Windows run the focused path/ownership suite, including directory symlink creation, missing privilege refusal, junction refusal, spaces/Unicode, case aliases and changed-parent refusal. Record the interpreter/OS actually used.

## Acceptance

Native evidence covers the Windows adapter and refusal path. A skipped test or WSL-only run is not a PASS.

## Focused verification

Native Windows: `python -m unittest tests.test_reconcile_plan tests.test_reconcile_apply tests.test_recovery` with only relevant platform cases; reuse unchanged portable results.

## Run record

Native Windows 11 build 26200, Python 3.14: tests.test_reconcile_plan tests.test_reconcile_apply tests.test_recovery — 19 PASS over existing authorized SSH to example-win-host. Covers real directory symlinks, actual junction refusal, case aliases, Unicode/spaces, busy lock and restart recovery. Winerror 1314 refusal is injected on native Windows; privileges were not changed. Fixed extended raw readlink spelling exposed by native run. Temporary test root C:/Users/example/AppData/Local/Temp/mask-native-e_tfvy_0 remains active for final launcher/end-to-end tests; remove at MASK-0016. Commit: this Done move.
