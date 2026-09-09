---
schema: "implement-rfc.card.v1"
id: "MASK-0087"
title: "Make updates complete without hiding their impact"
status: "In Progress"
rfcs: ["RFC-MASK-0018"]
depends_on: ["MASK-0086"]
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": false, "packet_key": "one-command-safe-updates"}
---

# MASK-0087: Make updates complete without hiding their impact

Governing RFC: [RFC-MASK-0018](../../rfcs/RFC-MASK-0018-task-oriented-cli-and-human-output.md). Live IDs confirmed by the committed pack reservation `6d80121`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-ux-readiness.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-ux-readiness/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-ux-readiness/ACCEPTANCE.md).

## Objective and owned paths

mask.py update entrypoint, mask_git/mask_pinned/mask_sources update preparation, shared approval service, update tests and narrowly affected docs.

## Bounded work

Coordinate approved acquisition, frozen candidate, useful scope/content proposal, consent, engine activation and final verification. Preserve old selector meaning and exact hash-guard behavior as defined in CLI.md; never let output mode choose different effects. Use existing cached/legacy/pinned update seams and retain the self-update boundary.

## Acceptance

Normal update needs no fetch/hash-copy/apply ceremony. Dry-run/offline does not fetch; guarded application binds a frozen candidate. Shared legacy impact is shown and cannot be silently isolated or widened; selected pinned changes preserve unrelated and exact-commit locks. Decline reports retained cache effects, not an activated update.

Criterion coverage: RFC-MASK-0018-AC04, RFC-MASK-0018-AC05, RFC-MASK-0018-AC06.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary. Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation, and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Not started. Claim the live remapped card before edits. No code implementation,
native result, host loading, user approval, or quota improvement is asserted.
