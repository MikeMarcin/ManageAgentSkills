---
schema: implement-rfc.card.v1
id: MASK-0138
title: Report an ahead-only program checkout as current during update
status: "Done"
rfcs: []
depends_on: []
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"88a4753","evidence":{"kind":"command","detail":"Native Windows focused public CLI fixture test_ahead_only_update_is_current_preserves_work_and_fetches_taps passes using local bare remotes. Ahead update is current, names actual before/after/candidate, fetches tap updates, and preserves local commit, dirty bytes, staging, state and absence of recovery journal. Dry-run preserves the checkout and contacts no remote."}},{"criterion":"AC2","outcome":"pass","revision":"88a4753","evidence":{"kind":"command","detail":"Fixture human rendering and actual python -B mask.py update --dry-run print no newer upstream version and local commits are kept, with actual revision and last-fetched/no-network disclosure. Latest origin/main fetched on Windows: original local upgrade commit changes only .mask.json and .mask.lock.json; remote has no missing commits. Newer local implement-rfc selections are retained."}},{"criterion":"AC3","outcome":"pass","revision":"88a4753","evidence":{"kind":"command","detail":"Six focused launcher tests pass: new ahead-only and diverged cases, existing comment-only update, dirty nonoverlap fast-forward/recovery, overlapping dirty hold and failed program merge/recovery. Preconditions still run before ahead classification. Documentation gate: 24 RFCs/138 cards, zero violations; git diff --check clean. Direct workflow preflight with --mask absolute mask.py reports ready; host loading is not claimed."}}]
---

# Report an ahead-only program checkout as current during update

Owner request (2026-10-11): fix `mask update` reporting “MASK was not updated:
this checkout is ahead of its remote” while tap fetching succeeds.

An ahead-only checkout already contains every fetched upstream commit. Treat
ordinary `update` as current, preserving its local commits and working tree,
and explain that there is no newer upstream MASK to apply. This amends the
historical ahead hold for ordinary update. Divergence retains its refusal.
Never reset, rebase, merge divergent history or push.

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
  Focused CLI fixtures and documentation gate pass.
