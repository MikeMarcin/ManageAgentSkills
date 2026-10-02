---
schema: "implement-rfc.card.v1"
id: "MASK-0042"
title: "Implement flat named bundle expansion and guarded refresh"
status: "In Progress"
rfcs: ["RFC-MASK-0010"]
depends_on: []
metadata: {"packet":"mask-readiness-fleet-2026-09-05","packet_key":"bundles","stage":"C — portable composition","provisional_id":false,"milestone_plan":{"id":"named-bundles","path":"docs/rfcs/plans/named-bundles/milestone-plan.json"}}
---

# MASK-0042: Implement flat named bundle expansion and guarded refresh

Governing RFC: [RFC-MASK-0010](../../rfcs/RFC-MASK-0010-portable-selections-and-bundles.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Expand source-revision-bound bundles to explicit binding sets. Preserve manual target intent and overlapping membership, report conflicts, require source approval, stale changed definitions, and avoid naive bundle deletion/dependency execution.

Own the named-bundle runtime, public CLI/planner integration, selection schemas,
focused public tests and truthful affected documentation. The owner explicitly
authorized both source repositories for the canonical `agentskills/rfc` handoff.
No profile/fleet implementation or consumer migration is implied.

## Acceptance and focused verification

- RFC-MASK-0010-AC02: Incremental and replace modes preserve their declared ownership scopes; exported all-agent behavior and optional frozen-agent behavior are explicit and tested.
- RFC-MASK-0010-AC03: Bundle expansion/refresh is deterministic, source-revision bound and stale-plan guarded; overlapping bundles/manual selections do not cause accidental removals.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_bundles tests.test_profiles

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

2026-10-02 mandate `named-bundles-v1`, strategy amendment: the owner said
"dont use direct"; coordinator-implementer replaces the earlier direct request.
The dispatched rfc-implementer owns this complete milestone without delegation.
MASK-0041 remains open and unimplemented. Its full export/import prerequisite is
removed for this bounded card because the shipped v2 selection, exact-lock,
planner and recovery engines already support explicit bundle expansion.
This refinement neither accepts nor implements profile export/import.
