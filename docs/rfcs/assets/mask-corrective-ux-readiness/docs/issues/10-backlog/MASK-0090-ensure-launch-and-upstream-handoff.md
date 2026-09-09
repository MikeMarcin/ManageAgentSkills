---
schema: "implement-rfc.card.v1"
id: "MASK-0090"
title: "Connect complete readiness to every public entrypoint"
status: "Backlog"
rfcs: ["RFC-MASK-0019"]
depends_on: ["MASK-0086", "MASK-0087", "MASK-0089"]
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": true, "packet_key": "ensure-launch-and-upstream-handoff"}
---

# MASK-0090: Connect complete readiness to every public entrypoint

## Objective and owned paths

mask_ensure.py, install/update/doctor/prelaunch final status, typed workflow readiness reporting, current MASK instructions, and the recorded AgentSkills integration handoff.

## Bounded work

Share one prerequisite evaluation between ensure, install/update completion, doctor checks and launch. Preserve cheap inventory as observational. Consume the explicitly authorized upstream contract/asset/staging handoff; update the local dependency record with its actual ASK card and commit when available. Do not edit the shared source through a symlink or pretend the current renderer already stages outputs.

## Acceptance

Public commands cannot report complete success with required roles missing. Launch does not start a host when setup is blocked; warning-only hooks remain labelled. The real selected AgentSkills package, explicit routing/addenda and current role names are used. Configured route and host observation stay separate. Until the upstream handoff exists, this card remains open.

Criterion coverage: RFC-MASK-0019-AC01, RFC-MASK-0019-AC06, RFC-MASK-0019-AC08.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary. Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation, and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Not started. Claim the live remapped card before edits. No code implementation,
native result, host loading, user approval, or quota improvement is asserted.
