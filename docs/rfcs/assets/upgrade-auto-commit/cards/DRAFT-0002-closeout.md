---
schema: "implement-rfc.card.v1"
id: "DRAFT-0002"
title: "Close out optional upgrade commits"
status: "Backlog"
rfcs: ["RFC-DRAFT-0001"]
depends_on: ["DRAFT-0001"]
closeout_for: ["RFC-DRAFT-0001"]
---

# Close out optional upgrade commits

## Scope and acceptance

Cover all acceptance in [RFC-DRAFT-0001](../RFC-DRAFT-0001-upgrade-auto-commit.md).
The planned implementation card is [DRAFT-0001](DRAFT-0001-upgrade-auto-commit.md).
Authorized live adoption records RFC_BASE_SHA and implementation revisions.
No baseline or acceptance evidence exists in this proposed card.

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
