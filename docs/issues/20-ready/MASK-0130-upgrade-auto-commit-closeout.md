---
schema: "implement-rfc.card.v1"
id: "MASK-0130"
title: "Close out optional upgrade commits"
status: "Ready"
rfcs: ["RFC-MASK-0024"]
depends_on: ["MASK-0129"]
closeout_for: ["RFC-MASK-0024"]
metadata: {"milestone_plan":{"id":"upgrade-auto-commit","path":"docs/rfcs/plans/upgrade-auto-commit/milestone-plan.json"}}
---

# Close out optional upgrade commits

## Scope and acceptance

Cover all acceptance in [RFC-MASK-0024](../../rfcs/RFC-MASK-0024-upgrade-auto-commit.md).
The planned implementation card is MASK-0129.

## Verification and execution record
Authorized live adoption records RFC_BASE_SHA and implementation revisions.
RFC_BASE_SHA: `c8201e2eeef5d7d06b3d6526e63669570182fdbc`.
Mandate: `upgrade-auto-commit`, revision 2. Owner: `/root/upgrade_commit`.
Planned cards: MASK-0129, MASK-0130. Actual evidence follows.


| Criterion | Planned check | Outcome | Implementation revision |
|---|---|---|---|
| AC01 | Public CLI flag/default/scope/setup-consent fixtures | Pass | `4ef044c1639d7ac106e1e86c65801592aee2c89b` |
| AC02 | Exact commit tree and staged/unstaged/untracked/no-op fixtures | Pass | `4ef044c1639d7ac106e1e86c65801592aee2c89b` |
| AC03 | Read-only preview, hash binding and changed-observation fixtures | Pass | `4ef044c1639d7ac106e1e86c65801592aee2c89b` |
| AC04 | Git eligibility, aggregate blocking and linked-worktree fixtures | Pass | `4ef044c1639d7ac106e1e86c65801592aee2c89b` |
| AC05 | Readiness failure, Git failure/race/timeout and retry fixtures | Pass | `4ef044c1639d7ac106e1e86c65801592aee2c89b` |
| AC06 | Aggregate partial results and human/JSON contract fixtures | Pass | `4ef044c1639d7ac106e1e86c65801592aee2c89b` |
| AC07 | Focused regression suites and reconciled public documentation | Pass | `4ef044c1639d7ac106e1e86c65801592aee2c89b` |

Draft structural validation belongs in [DRAFT_CHECKS.md](../../rfcs/assets/upgrade-auto-commit/DRAFT_CHECKS.md), not in
this acceptance table. Implementation determines actual checks and evidence.

## Current checkpoint

Mandate `upgrade-auto-commit` revision 2; milestone `usable-upgrade-commits`; owner
`/root/upgrade_commit`. D4–D7 were confirmed by the human's “confirm go ahead”.
D2–D3 remain settled. Implementation: `4ef044c1639d7ac106e1e86c65801592aee2c89b` on main.
Owned source paths and exact source digests are recorded in
[verification evidence](../../development/upgrade-auto-commit-verification.json).
The source commit contains 13 explicit feature/docs paths and excludes live controls.

Guarded integration: 126 tests across 14 classes, 1 Windows-only Job Object
prerequisite skip on macOS, zero failed classes, wall 196s. Self-review identified
a nonregular-control classification correction; the final affected rerun passes all
24 feature/setup tests in 126.770s with no skips. The earlier 13-test failure was
the corrected human dry-run disclosure. Guard receipts preserve both repositories'
controls and this checkout's .gitignore. Fixture roots are empty. Documentation
validation: 24 RFCs, 130 cards, zero structural violations; whitespace check passes.

AC01–AC07 pass against the recorded source candidate. Acceptance adds no required
human, independent or native-platform gate. No native Windows or serving-runtime
claim is made. The cooperative guard cannot establish transient or undeclared-file
protection. Source/card evidence, not draft structural checks, establishes acceptance.

No repository writers or task commands remain active. No review server or protected
review candidate exists. No push, publication, live migration or AgentSkills source
change occurred. Preexisting live controls and unrelated .gitignore remain dirty
and excluded. Next: finish MASK-0129, claim/finish MASK-0130, reconcile RFC/index,
renew the plan binding for execution-record formatting and close the milestone.
