---
schema: "implement-rfc.card.v1"
id: "MASK-0141"
title: "Sanitize remaining mutable source-preview path metadata"
status: "Ready"
rfcs: []
depends_on: []
metadata: {"mandate":"public-prep-final-reconciliation-v1","baseline":"4ba72a7235d8a94d0d8cb386a672a51e671702bc","milestone_plan":{"id":"public-source-finalization","path":"docs/rfcs/plans/public-source-finalization/milestone-plan.json"}}
---

# Final path metadata correction

M3's cross-platform path scan found personal Windows launcher paths in the
accepted evidence of MASK-0133. This independent documentation follow-up replaces
only those operational user prefixes and labels the result as sanitized evidence.
The original acceptance outcomes, revisions and native observations keep their
meaning. MASK-0140 retains the unanswered owner license choice.

## Acceptance

- AC1: MASK-0133's accepted evidence uses EXAMPLE user prefixes for both Windows
  and Git Bash launcher paths; all acceptance fields and text otherwise survive.
  The card labels this privacy projection without claiming fresh native evidence.
- AC2: Documentation checks, exact-candidate credential scans and review of current
  path findings pass. Retained immutable packet paths and historical metadata are
  reported separately; no code/tests/workflow inputs or license state change.
- AC3: Explicit-path commits, final fetch/reconciliation and authorized ordinary
  push are completed and bound in the M3 handoff with quiescent commands and the
  original license/native/public-CI limitations.
