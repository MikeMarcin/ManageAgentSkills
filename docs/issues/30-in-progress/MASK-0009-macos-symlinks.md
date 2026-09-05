---
id: MASK-0009
title: Verify native macOS symlink safety
status: In Progress
rfc: RFC-MASK-0002
depends_on: ["MASK-0007"]
platform: macos
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

Not started. Record actual commands, outcomes and commits here. Read the live board before claiming. Never stage unrelated paths.
