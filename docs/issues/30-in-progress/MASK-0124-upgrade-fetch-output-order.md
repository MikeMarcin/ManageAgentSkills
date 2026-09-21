---
schema: "implement-rfc.card.v1"
id: "MASK-0124"
title: "Show tap fetch results before the upgrade summary"
status: "In Progress"
rfcs: []
depends_on: []
metadata: {"milestone_plan":{"id":"upgrade-fetch-output-order","path":"docs/rfcs/plans/upgrade-fetch-output-order/milestone-plan.json"}}
---

# MASK-0124: Show tap fetch results before the upgrade summary

Owner amendment to the completed MASK-0121 presentation: place
`tap agentskills: fetched, nothing new` before the `Upgraded ...` summary so the
result follows the operation order. Preserve wording, JSON and operation behavior.

Baseline: `3e78da1a945cbc91c51c176a0c2d5de671d1e530`.
Mandate: `fetch-output-order`, revision 1; assigned owner `/root/fetch_output_order`.

- AC1: Fetch results precede the human upgrade summary, separated by a blank line
  when present; output without fetch results has no added blank prefix.
- AC2: Existing human-output and JSON checks pass; a disposable public upgrade
  demonstrates the order and retains successful deployment behavior.

Scope: `mask_present.py` and this follow-up's bookkeeping. No publication, live
consumer changes or setup repair. Preserve the unrelated `.mask.lock.json` edit.

## Checkpoint

Plan: prefix the existing fetch lines; retain the remaining notes as the footer.
Use the existing test suite plus a disposable public CLI journey; no new test file.
No human or independent acceptance is required for this bounded presentation edit.
