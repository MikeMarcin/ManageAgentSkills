---
schema: "implement-rfc.card.v1"
id: "MASK-0128"
title: "Amend named bundles to install and ownership-safe uninstall"
status: "In Progress"
rfcs: ["RFC-MASK-0010"]
depends_on: ["MASK-0042"]
external_depends_on: ["AgentSkills:ASK-0096"]
metadata: {"milestone_plan":{"id":"named-bundles","path":"docs/rfcs/plans/named-bundles/milestone-plan.json"}}
---

# Amend named bundles to install and ownership-safe uninstall

Owner amendment, 2026-10-02: "Make the admendment to the rfc and update it",
following agreement on bundle install/uninstall. Mandate `named-bundles-v2`.
Follow up MASK-0042 without rewriting its historical acceptance. Own bundle
runtime/CLI/rendering, focused public tests, affected docs and the existing plan,
RFC and closeout. Coordinate the actual upstream ASK-0096 handoff.

Replace the newly introduced pre-release `bundle apply` with `bundle install`;
no obsolete alias is advertised or retained. Install remains additive and locks
membership until explicit refresh. Uninstall removes only the named frozen local
contribution, preserving manual/overlapping selections, exact locks, held and
locally edited bindings. Last-origin held/edited survivors become positive manual
selections. Reinstall creates a new receipt while preserving those survivors.
Uninstall uses local receipts without fetching or adopting source definitions;
unknown/uninstalled bundles are idempotent no-ops. Use normal guarded planner,
ownership checks and frozen journal recovery; no setup script rerun on recovery.

Acceptance: public install/uninstall/refresh and human/JSON interfaces; preview,
stale guard, overlap/manual/hold/edit preservation, reinstall/no-op/offline and
recovery checks; canonical all-four readiness plus safe removal; docs and clean
explicit-path commits. Preserve profile/fleet/native-host pending obligations.
No push, real consumer migration, credentials or permission changes.

Terminology amendment: owner "refresh seems like it should be upgade, no?"
selects install/uninstall/upgrade; mandate `named-bundles-v3`. Obsolete apply and
refresh are removed before release. Package-version policy choice remains pending
through the coordinator; existing install/uninstall acceptance work continues.
