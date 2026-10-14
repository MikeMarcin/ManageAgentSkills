---
schema: "implement-rfc.card.v1"
id: "MASK-0141"
title: "Sanitize remaining mutable source-preview path metadata"
status: "Done"
rfcs: []
depends_on: []
metadata: {"mandate":"public-prep-final-reconciliation-v1","baseline":"4ba72a7235d8a94d0d8cb386a672a51e671702bc","milestone_plan":{"id":"public-source-finalization","path":"docs/rfcs/plans/public-source-finalization/milestone-plan.json"}}
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"7a97e948ac21ce4141f6850e8eebc921d2c37652","evidence":{"kind":"artifact","path":"docs/development/public-source-finalization.md","detail":"MASK-0133 comparison confirms only its Windows/Git Bash user prefixes changed to EXAMPLE in /acceptance/3/evidence/detail; other fields/body retained and privacy projection note appended."}},{"criterion":"AC2","outcome":"pass","revision":"7a97e948ac21ce4141f6850e8eebc921d2c37652","evidence":{"kind":"artifact","path":"docs/development/public-source-finalization.md","detail":"Docs24RFCs/142cards zero; exact7a97e94 credential scans zero; current path scan classifies only three immutable provenance locations in two files. No production/workflow/license change."}},{"criterion":"AC3","outcome":"pass","revision":"7a97e948ac21ce4141f6850e8eebc921d2c37652","evidence":{"kind":"artifact","path":"docs/development/public-source-finalization.md","detail":"Explicit source paths committed; latest origin reconciled; ordinary source push and exact7a97e94 remote identity confirmed. All test/scan commands complete; final board/push and M3 handoff precede writer release."}}]
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
