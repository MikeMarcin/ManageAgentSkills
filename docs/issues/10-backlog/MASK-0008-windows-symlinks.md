---
id: MASK-0008
title: Verify native Windows symlink safety
status: Backlog
rfc: RFC-MASK-0002
depends_on: ["MASK-0007"]
platform: windows
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

Not started. Record actual commands, outcomes and commits here. Read the live board before claiming. Never stage unrelated paths.
