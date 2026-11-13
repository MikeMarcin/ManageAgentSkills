---
schema: implement-rfc.card.v1
id: MASK-0153
title: Run controller-reviewed fleet setup for locally granted sources
status: "Done"
rfcs: []
depends_on: []
metadata: {"milestone_plan":{"id":"granted-source-fleet-setup","path":"docs/rfcs/plans/granted-source-fleet-setup/milestone-plan.json"}}
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"b86691fc917681f8c2d92dfc34eada7c6c4b98f6","evidence":{"kind":"observation","detail":"Public CLI and signed subprocess transport disclosed exact script/input/interpreter/role replacement facts, kept preview consumer files unchanged and generated roles, portable locks, signed receipts and canonical controls commits. Combined contribution setup passed."}},{"criterion":"AC2","outcome":"pass","revision":"b86691fc917681f8c2d92dfc34eada7c6c4b98f6","evidence":{"kind":"observation","detail":"Signed cases rejected unreviewed/tampered task, signature/expiry, invalid/stale inputs, changed destinations and ungranted source/scope/action; mismatched enrollment source refused. Same-id unrelated profile could not borrow source authority. Replacement backups and staged rollback preserved prior bytes; failed/launched setup did not silently rerun."}},{"criterion":"AC3","outcome":"pass","revision":"b86691fc917681f8c2d92dfc34eada7c6c4b98f6","evidence":{"kind":"observation","detail":"Disposable integration suite: 82 passed, 0 skipped/failed. Final-source focused setup pass: 9 passed; added interrupted replacement and updated authority cases: 2 passed (10 distinct new setup cases overall). Documentation gate: 26 RFCs, 153 cards, 0 violations. macOS fixture transport only; no new native SSH/Windows/loading claim."}}]
---

The owner explicitly approved amending fleet trust: a device's existing source
grant plus its scope/action grant permits the controller to review and authorize
that source's exact setup and native-role repairs during fleet upgrade. Preserve
signature, source identity, scope, freshness, input validation, backup/recovery and
billing/credential boundaries. No new grants or force overwrite are authorized.

Own the bounded MASK implementation, focused disposable integration tests and
current fleet docs/RFC amendments. Coordinate code changes in the canonical
ManageAgentSkills checkout; do not publish or perform live fleet mutations from
the engineering leaf. Root coordinator owns publication and rollout.

- AC1: Fleet previews disclose exact granted-source setup/role repair effects;
  signed approved apply performs them through ordinary setup/recovery machinery.
- AC2: Ungranted/mismatched sources, invalid inputs, stale/tampered plans and
  unauthorized scopes/actions remain rejected. Replacement preserves backups.
- AC3: Focused public CLI/transport tests pass in temporary fixtures and local
  bare remotes; current docs and RFC-MASK-0012 explain source-granted setup.

Baseline: `165ca56`. Owner mandate includes commit, push and fleet rollout after
verification. Existing canonical control commit propagation rules remain in scope
for rollout without weakening dirty/diverged-control protections.
