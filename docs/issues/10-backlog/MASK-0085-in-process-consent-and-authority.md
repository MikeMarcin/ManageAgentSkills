---
schema: "implement-rfc.card.v1"
id: "MASK-0085"
title: "Integrate consent without manual plan-hash copying"
status: "Backlog"
rfcs: ["RFC-MASK-0018"]
depends_on: ["MASK-0084"]
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": false, "packet_key": "in-process-consent-and-authority"}
---

# MASK-0085: Integrate consent without manual plan-hash copying

Governing RFC: [RFC-MASK-0018](../../rfcs/RFC-MASK-0018-task-oriented-cli-and-human-output.md). Live IDs confirmed by the committed pack reservation `6d80121`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-ux-readiness.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-ux-readiness/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-ux-readiness/ACCEPTANCE.md).

## Objective and owned paths

mask.py common options, plan/authority service seams, confirmation presentation, capability descriptors and prompt/stale-input tests.

## Bounded work

Implement the manual/noninteractive/event policy in contracts/CLI.md. Ordinary direct tasks authorize their narrow engine effects; significant new authority gets a default-no in-process prompt. Hold no writer lock while waiting for input. Recheck the exact proposal after consent. Add --yes and typed pending confirmation without making either a force bypass or persistent integration approval.

## Acceptance

Consent completes the requested operation in the same invocation. Decline/EOF/interruption run no unapproved action. JSON, redirected streams and event hooks never wait for input. --yes does not authorize package scripts, new sources or hidden expanded scope. A concurrent input change after the prompt causes a stale-plan refusal.

Criterion coverage: RFC-MASK-0018-AC03, RFC-MASK-0018-AC04, RFC-MASK-0018-AC06.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary. Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation, and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Not started. Claim the live remapped card before edits. No code implementation,
native result, host loading, user approval, or quota improvement is asserted.
