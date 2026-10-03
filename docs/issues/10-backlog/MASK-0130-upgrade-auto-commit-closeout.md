---
schema: "implement-rfc.card.v1"
id: "MASK-0130"
title: "Close out optional upgrade commits"
status: "Backlog"
rfcs: ["RFC-MASK-0024"]
depends_on: ["MASK-0129"]
closeout_for: ["RFC-MASK-0024"]
metadata: {"milestone_plan":{"id":"upgrade-auto-commit","path":"docs/rfcs/plans/upgrade-auto-commit/milestone-plan.json"}}
---

# Close out optional upgrade commits

## Scope and acceptance

Cover all acceptance in [RFC-MASK-0024](../../rfcs/RFC-MASK-0024-upgrade-auto-commit.md).
The planned implementation card is [MASK-0129](../20-ready/MASK-0129-upgrade-auto-commit.md).
Authorized live adoption records RFC_BASE_SHA and implementation revisions.
RFC_BASE_SHA: `c8201e2eeef5d7d06b3d6526e63669570182fdbc`.
Mandate: `upgrade-auto-commit`, revision 2. Owner: `/root/upgrade_commit`.
Planned cards: MASK-0129, MASK-0130. No acceptance evidence yet.


| Criterion | Planned check | Outcome | Implementation revision |
|---|---|---|---|
| AC01 | Public CLI flag/default/scope/setup-consent fixtures | Not run | Pending |
| AC02 | Exact commit tree and staged/unstaged/untracked/no-op fixtures | Not run | Pending |
| AC03 | Read-only preview, hash binding and changed-observation fixtures | Not run | Pending |
| AC04 | Git eligibility, aggregate blocking and linked-worktree fixtures | Not run | Pending |
| AC05 | Readiness failure, Git failure/race/timeout and retry fixtures | Not run | Pending |
| AC06 | Aggregate partial results and human/JSON contract fixtures | Not run | Pending |
| AC07 | Focused regression suites and reconciled public documentation | Not run | Pending |

Draft structural validation belongs in [DRAFT_CHECKS.md](../DRAFT_CHECKS.md), not in
this acceptance table. Implementation determines actual checks and evidence.

## Current checkpoint

Confirmed D4–D7; adoption and plan binding precede source implementation.
Candidate baseline and protected unrelated files are recorded above. No commands
remain running. Next: bind, claim MASK-0129, implement AC01–AC07 in fixture roots.
