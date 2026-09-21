---
schema: "implement-rfc.card.v1"
id: "MASK-0124"
title: "Show tap fetch results before the upgrade summary"
status: "Done"
rfcs: []
depends_on: []
metadata: {"milestone_plan":{"id":"upgrade-fetch-output-order","path":"docs/rfcs/plans/upgrade-fetch-output-order/milestone-plan.json"}}
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"0ad405c371450630ac1b4fab19800cccf12f62c7","evidence":{"kind":"observation","detail":"Exact 31-skills/7-projects/personal renderer example begins with the unchanged tap fetch line, a blank line, then the upgrade summary. A minimal no-fetch result has no added prefix; rendering leaves the result object unchanged. Public before/after journey in /tmp/mask-fetch-order/public_check.py confirms the ordering correction. Product diff is only mask_present.py (4 insertions, 3 deletions)."}},{"criterion":"AC2","outcome":"pass","revision":"0ad405c371450630ac1b4fab19800cccf12f62c7","evidence":{"kind":"command","detail":"python3 -B -m unittest tests.test_human_output tests.test_cli_protocol: 21 tests pass on macOS. Public fixture upgrade --all --no-update against a local bare tap upgrades one project skill and one personal skill, with fetch text before summary; repeat --json is one clean result with no changes. Cooperative qualification check preserves selected live declaration/config/lock bytes; temporary roots cleaned. Documentation gate: 23 RFCs, 124 cards, 0 violations. git diff --check clean. No native Windows or human acceptance is claimed or required for this bounded presentation change."}}]
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
