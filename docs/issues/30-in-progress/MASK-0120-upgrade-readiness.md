---
schema: "implement-rfc.card.v1"
id: "MASK-0120"
title: "Make upgrade reconcile registered consumers through workflow setup"
status: "In Progress"
rfcs: []
depends_on: []
priority: "P1"
metadata: {"milestone_plan":{"id":"upgrade-readiness","path":"docs/rfcs/plans/upgrade-readiness/milestone-plan.json"}}
---

# MASK-0120: Make upgrade reconcile registered consumers through workflow setup

## Mandate and boundary

Owner request, 2026-09-20: work directly; `upgrade` should be sufficient to make
existing registered projects and personal skills functional. `ensure` remains
useful for a new worktree or reconciling pinned versions without upgrading.
This amends the setup-only-on-ensure behavior recorded by RFC-MASK-0019; it does
not close that RFC's outstanding real-package/native acceptance.

Baseline: `0b2e41fcabe629a8916bc3820b3394f8240e255a`.
Owned surface: upgrade orchestration, shared setup/repair validation where needed,
CLI options and presentation, public CLI tests and current documentation.
No live consumer migration, source push, automatic approval or host-load claim.

## Acceptance

- AC1: Scoped and default all-registered upgrade reconciles links, static roles
  and consented generated roles in one invocation, including unchanged versions;
  a second unchanged invocation runs no setup.
- AC2: Preview binds candidate setup identities and writes/fetches/runs nothing;
  named setup with its hash succeeds, changed inputs refuse, terminal yes/no is
  honored, and JSON/redirected/--yes invocations never run unauthorized setup.
- AC3: Modified/unmanaged content remains protected by default. Explicit
  `upgrade --repair` uses the existing backup and staged repair semantics;
  failed setup never reports success and retains truthful committed link effects.
- AC4: Scope selection, pins, offline behavior and failed-tap isolation remain
  intact; help and README explain upgrade versus ensure and the setup path.

## Execution

Direct strategy, no delegation. The host has no scoped delegation-disable
setting exposed; no agent or external model calls are used. Direct preflight
reports `integration.approval_required` for this checkout. That is an automatic
readiness policy prerequisite, not a missing engineering role; this task changes
source and tests disposable consumers and does not grant live readiness approval.
The pre-existing `.mask.lock.json` edit is unrelated and preserved.
