---
schema: "implement-rfc.card.v1"
id: "MASK-0122"
title: "Guide pending-operation recovery through repair"
status: "Done"
rfcs: []
depends_on: []
priority: "P1"
metadata: {"milestone_plan":{"id":"recovery-entrypoint","path":"docs/rfcs/plans/recovery-entrypoint/milestone-plan.json"}}
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"37fde42b32d3e6d324882908a981cffef4de35ee","evidence":{"kind":"observation","detail":"Bare recover inspects; repair reviews interrupted setup with exact-hash or terminal consent; blocked update points to repair; help and command buckets explain scope. See docs/rfcs/plans/recovery-entrypoint/verification.md."}},{"criterion":"AC2","outcome":"pass","revision":"37fde42b32d3e6d324882908a981cffef4de35ee","evidence":{"kind":"observation","detail":"Role-only frozen publication permits HEAD/index movement while exact inputs, controls, identities, authority, artifact source, destinations and registry remain guarded; linked and unknown cache content refuses. See docs/rfcs/plans/recovery-entrypoint/verification.md."}},{"criterion":"AC3","outcome":"pass","revision":"37fde42b32d3e6d324882908a981cffef4de35ee","evidence":{"kind":"observation","detail":"Seven public recovery, fourteen human-output, four retained setup recovery and eleven artifact checks pass, with final two guidance checks. Failure-injection and terminal journeys prove no package reruns. See docs/rfcs/plans/recovery-entrypoint/verification.md."}},{"criterion":"AC4","outcome":"pass","revision":"37fde42b32d3e6d324882908a981cffef4de35ee","evidence":{"kind":"observation","detail":"Reviewed public repair completed transaction 24e6c819-77a1-4099-86b2-c06624bf760c. Exact roles, role lock and registry match recorded after-state; journal absent and ten cache hashes preserved. Installed mask update from AgentSkills succeeds; no broader upgrade or setup rerun. See docs/rfcs/plans/recovery-entrypoint/verification.md."}}]
---

# MASK-0122: Guide pending-operation recovery through repair

Owner reports update blocked by pending recovery and bare recover rejecting the
invocation; recover was absent from the agreed command buckets. Continue directly.
Baseline: `e7017d0c3501d2ff8edbe3e0c5a981b1a4b4c09f`.

- AC1: Bare recover is observational inspection with a useful diagnosis and next
  steps. Repair guides recovery of an interrupted task using the same reviewed
  task/hash pattern. Normal blocked mutations point to repair. Help and buckets
  explain recovery as maintenance rather than an undisclosed ordinary prerequisite.
- AC2: Frozen native-role publication can recover after unrelated commits or after
  committing unchanged declaration/lock bytes. This narrow case still checks
  exact declarations/locks, identities, authority, artifacts, setup inputs,
  destination bytes and registry state. Broader journals retain their guards.
- AC3: Public fixtures cover complete/rollback/no-rerun, preview and approval,
  terminal review, edits/collisions/input changes and conservative refusal.
- AC4: Diagnose and restore the user's existing blocked operation through the
  supported CLI after safe preview if its original approved effects remain valid.
  Preserve concurrent work; no manually edited journal, unrequested upgrades,
  package reruns, push or publication. Record actual outcome and any remaining gap.

Direct primary execution; no delegation. Prior source-only boundary applies to
previous work; this corrective request includes resolving the reported live block.

## Closeout

Implementation: `37fde42b32d3e6d324882908a981cffef4de35ee`.
[Verification](../../rfcs/plans/recovery-entrypoint/verification.md) records
AC1–AC4, the narrow recovery exception, tested refusal boundaries and exact live
postconditions. Seven public recovery cases, fourteen human-output cases, four
retained setup recovery cases and eleven artifact cases pass. Two focused final
guidance checks pass. No full-suite or native Windows result is claimed.

The reported ExampleNotes journal was safely completed through reviewed public
repair. Its roles and lock match the recorded after-state, the journal is gone,
and the installed launcher's update succeeds. No setup scripts were rerun, skill
versions upgraded, internal state hand-edited, pushes or publication performed.
Original failure cause remains unknown because the old path discarded it. No
claim is made that the rest of the earlier multi-consumer upgrade completed.

Direct primary self-review and acceptance; no delegation. Source and tracking
commands are quiescent at closeout. No broader consumer migration is included.
