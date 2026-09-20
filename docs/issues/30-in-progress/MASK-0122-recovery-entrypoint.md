---
schema: "implement-rfc.card.v1"
id: "MASK-0122"
title: "Guide pending-operation recovery through repair"
status: "In Progress"
rfcs: []
depends_on: []
priority: "P1"
metadata: {"milestone_plan":{"id":"recovery-entrypoint","path":"docs/rfcs/plans/recovery-entrypoint/milestone-plan.json"}}
---

# MASK-0122: Guide pending-operation recovery through repair

Owner reports update blocked by pending recovery and bare recover rejecting the
invocation; recover was absent from the agreed command buckets. Continue directly.
Baseline: `e7017d0c3501d2ff8edbe3e0c5a981b1a4b4c09f`.

- AC1: Bare recover is observational inspection with a useful diagnosis and next
  steps. Repair guides recovery of an interrupted task using the same reviewed
  task/hash pattern. Normal blocked mutations point to repair. Help and buckets
  explain recovery as maintenance rather than an undisclosed ordinary prerequisite.
- AC2: Frozen native-role publication can recover after unrelated commits or after
  committing unchanged declaration/lock bytes. This narrow case still checks
  exact declarations/locks, identities, authority, artifacts, setup inputs,
  destination bytes and registry state. Broader journals retain their guards.
- AC3: Public fixtures cover complete/rollback/no-rerun, preview and approval,
  terminal review, edits/collisions/input changes and conservative refusal.
- AC4: Diagnose and restore the user's existing blocked operation through the
  supported CLI after safe preview if its original approved effects remain valid.
  Preserve concurrent work; no manually edited journal, unrequested upgrades,
  package reruns, push or publication. Record actual outcome and any remaining gap.

Direct primary execution; no delegation. Prior source-only boundary applies to
previous work; this corrective request includes resolving the reported live block.
