---
id: MASK-0005
title: Implement ownership-aware pure reconciliation plans
status: In Progress
rfc: RFC-MASK-0002
depends_on: ["MASK-0004"]
---

# MASK-0005: Implement ownership-aware pure reconciliation plans

## Objective and owned paths

Own planner, source/target containment, identity/fingerprint and `tests/test_reconcile_plan.py`.

## Bounded work

Implement target truth table, multi-project/prospective preflight, deterministic actions and source-content-aware plan hashes. No filesystem effects in planning.

## Acceptance

Unmanaged objects/linked parents/unsafe state/unavailable roots become blockers. Supporting file edits stale a plan; no preview creates locks/state or contacts the network.

## Focused verification

`python -m unittest tests.test_reconcile_plan` and subprocess dry-run sentinel checks.

## Run record

Not started. Record actual commands, outcomes and commits here. Read the live board before claiming. Never stage unrelated paths.
