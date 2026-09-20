---
schema: "implement-rfc.card.v1"
id: "MASK-0123"
title: "Show useful human diagnostics for unknown commands"
status: "Ready"
rfcs: []
depends_on: []
priority: "P2"
metadata: {"milestone_plan":{"id":"command-diagnostics","path":"docs/rfcs/plans/command-diagnostics/milestone-plan.json"}}
---

# MASK-0123: Show useful human diagnostics for unknown commands

Owner requests a concise usage guide and plain unknown-command error, like the
provided brew example, instead of argparse's full command-choice dump and technical
result fields. Continue directly. Baseline: `43c984c764e9427060e0d60767bde73da254924a`.

- AC1: Unknown commands show short useful examples and help discovery, plus one
  plain error. No raw command-choice dump, code/state/next field block, or reliance
  on typo correction. Nested command errors give relevant group guidance.
- AC2: Preserve exit class 2, stderr human diagnostics, explicit JSON protocol and
  operand separation. Other usage errors are concise without hiding operational
  failure evidence. Control characters remain sanitized and pipes remain plain.
- AC3: Focused public CLI checks and visual inspection demonstrate the output and
  JSON behavior. Document the result and commit only task-owned paths.

Source and fixture scope only. Preserve the unrelated `.mask.lock.json` edit.
No live upgrade, publication or delegation.
