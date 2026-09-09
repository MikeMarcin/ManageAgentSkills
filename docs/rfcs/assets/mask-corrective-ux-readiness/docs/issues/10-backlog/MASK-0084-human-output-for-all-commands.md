---
schema: "implement-rfc.card.v1"
id: "MASK-0084"
title: "Implement real human output and actionable errors"
status: "Backlog"
rfcs: ["RFC-MASK-0018"]
depends_on: ["MASK-0083"]
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": true, "packet_key": "human-output-for-all-commands"}
---

# MASK-0084: Implement real human output and actionable errors

## Objective and owned paths

mask.py output selection/help/version, a shared presentation module, tests/support.py and focused CLI/inventory fixtures. Do not move engine decisions into presentation.

## Bounded work

Keep one result object and add summary/table/change/error renderers. Cover every current command via the registration table; remove indented-JSON fallback. Preserve machine output, normalize readable error/remediation output, and fix no-argument help. Add human/terminal tests independent of Fixture.call that appends --json.

## Acceptance

The six-row inventory is rendered as three skill rows with separate agent states; paginated/conflicting/pinned/empty/unavailable cases are honest. No command returns raw envelope JSON by default, including version and rare commands. Redirected output stays text; JSON remains one parseable document and no terminal decoration contaminates it.

Criterion coverage: RFC-MASK-0018-AC02, RFC-MASK-0018-AC03.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary. Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation, and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Not started. Claim the live remapped card before edits. No code implementation,
native result, host loading, user approval, or quota improvement is asserted.
