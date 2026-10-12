---
schema: implement-rfc.card.v1
id: MASK-0138
title: Report an ahead-only program checkout as current during update
status: "In Progress"
rfcs: []
depends_on: []
---

# Report an ahead-only program checkout as current during update

Owner request (2026-10-11): fix `mask update` reporting “MASK was not updated:
this checkout is ahead of its remote” while tap fetching succeeds.

An ahead-only checkout already contains every fetched upstream commit. Treat
ordinary `update` as current, preserving its local commits and working tree,
and explain that there is no newer upstream MASK to apply. This amends the
historical ahead hold for ordinary update, not divergence or self-update's
strict refusal contract. Never reset, rebase, merge divergent history or push.

Scope: program update classification/output, focused local-bare-remote CLI
checks and update guide. Baseline: 5f4eef5 (actual preimplementation HEAD).
Direct primary execution; no agents. No live network or consumer mutation.

Acceptance:
- AC1: Ahead-only update exits successfully with program status current and
  relation ahead, actual before/after revision and fetched candidate disclosed.
  HEAD, commits, dirt, index and MASK persistent state are preserved; taps still
  fetch. Dry-run does not fetch or write and names last-fetched evidence.
- AC2: Human output says no newer upstream MASK is available and local commits
  are kept, without an alarming not-updated message or a missing revision.
- AC3: Divergence, detach, wrong identity and in-progress Git operations retain
  their holds; behind still follows existing reviewed fast-forward behavior.
  Strict self update retains its refusal. Focused CLI fixtures and documentation
  gate pass.
