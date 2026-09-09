---
schema: "implement-rfc.card.v1"
id: "MASK-0089"
title: "Run genuinely required setup with exact consent and recovery"
status: "Backlog"
rfcs: ["RFC-MASK-0019"]
depends_on: ["MASK-0085", "MASK-0088"]
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": true, "packet_key": "approved-staged-setup"}
---

# MASK-0089: Run genuinely required setup with exact consent and recovery

## Objective and owned paths

Bounded setup service over mask_process.py, shared proposal/authority/journal seams, role staging validation and timeout/crash tests. No general shell hook framework.

## Bounded work

Implement the fixed Python preparation interface with frozen package/context inputs, exact named action authority and staged role outputs. A human yes covers the disclosed bounded sequence. Package validators are not executed implicitly. Use existing process-tree control, stream bounds and typed operation recovery; do not duplicate the renderer or let it own final paths.

## Acceptance

Yes runs then verifies; no/EOF/check/dry-run/JSON-without-approval runs nothing. Changed imported code or inputs invalidates consent. Timeout/cancellation/crash retains truthful stage/pending status and never automatically reexecutes uncertain code. Malformed/extra/stale stage outputs cannot reach host discovery paths. No claim of a security sandbox is made.

Criterion coverage: RFC-MASK-0019-AC04, RFC-MASK-0019-AC05.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary. Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation, and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Not started. Claim the live remapped card before edits. No code implementation,
native result, host loading, user approval, or quota improvement is asserted.
