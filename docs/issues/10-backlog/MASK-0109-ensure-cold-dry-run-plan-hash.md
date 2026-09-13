---
schema: "implement-rfc.card.v1"
id: "MASK-0109"
title: "Bind the same plan hash for a pinned ensure preview on a cold store as for the applying run"
status: "Backlog"
rfcs: []
depends_on: ["MASK-0100"]
priority: "P2"
metadata: {"origin":"RFC-MASK-0020 d2 follow-up candidate filed under mandate r2 (2026-09-13)","follow_up_of":"MASK-0099"}
---

# MASK-0109: Bind the same plan hash for a pinned ensure preview on a cold store as for the applying run

## Evidence

[MASK-0099 execution record](../60-done/MASK-0099-machine-v3-and-tap-bootstrap.md#contract-notes-and-follow-up-candidates): an `ensure --dry-run` of a pinned consumer whose store is not yet materialized gives a plan hash different from the run that applies.

## Bounded work

Make the reviewed plan hash independent of whether locked artifacts are already materialized, without letting a preview fetch or materialize anything, and without weakening the guard against a real change between preview and apply.

## Acceptance

On a pinned consumer with a cold store, `ensure --dry-run` followed by `ensure --expect-plan-hash H` applies without `plan.stale`. A changed declaration, lock or policy between the two still refuses `plan.stale`. The preview performs no fetch and no materialization.
