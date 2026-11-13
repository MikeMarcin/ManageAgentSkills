---
schema: implement-rfc.card.v1
id: MASK-0153
title: Run controller-reviewed fleet setup for locally granted sources
status: Ready
rfcs: []
depends_on: []
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
