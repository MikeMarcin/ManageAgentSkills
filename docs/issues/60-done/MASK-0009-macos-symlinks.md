---
schema: "implement-rfc.card.v1"
id: "MASK-0009"
title: "Verify native macOS symlink safety"
status: "Done"
rfcs: ["RFC-MASK-0002"]
depends_on: ["MASK-0007"]
metadata: {"platform":"macos"}
---

# MASK-0009: Verify native macOS symlink safety

## Objective and owned paths

Own native macOS test adjustments and this card.

## Bounded work

Exercise actual symlinks, alias/case handling, root normalization, paths containing spaces and safe interruption/recovery on a native Mac. Never use real personal skills as disposable fixtures.

## Acceptance

Native evidence supports macOS; Linux simulation is not substituted. Record filesystem assumptions and any unavailable lane.

## Focused verification

Native macOS: selected `tests.test_reconcile_plan`, `tests.test_reconcile_apply`, `tests.test_recovery` cases.

## Run record

Native macOS 26.6.2 build 25G83, Python 3.14.7: focused planner/apply/recovery suite PASS (19 tests, 2 Windows-only skips); final affected protocol-inclusive rerun 23 tests PASS, 2 Windows-only skips. Actual directory symlinks, case-insensitive APFS aliases, Unicode/spaced roots, replaced parents and crash recovery exercised. Local disposable fixtures cleaned automatically. Commit: this Done move.
