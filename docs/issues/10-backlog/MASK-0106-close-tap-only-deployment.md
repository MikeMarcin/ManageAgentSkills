---
schema: "implement-rfc.card.v1"
id: "MASK-0106"
title: "Verify and close tap-only deployment"
status: "Backlog"
rfcs: ["RFC-MASK-0020"]
depends_on: ["MASK-0104", "MASK-0105"]
priority: "P1"
metadata: {"packet":"mask-corrective-managed-taps","provisional_id":false,"packet_key":"close-tap-only-deployment","milestone_plan":{"id":"tap-only-deployment","path":"docs/rfcs/plans/tap-only-deployment/milestone-plan.json"}}
closeout_for: ["RFC-MASK-0020"]
---

# MASK-0106: Verify and close tap-only deployment

Governing RFC: [RFC-MASK-0020](../../rfcs/RFC-MASK-0020-tap-only-deployment.md). Live IDs confirmed by the committed pack reservation `b92372f`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-managed-taps.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-managed-taps/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-managed-taps/ACCEPTANCE.md).

## Objective and owned paths

This RFC, its closeout, current affected docs and exact native evidence references only.

## Bounded work

Reconcile every RFC-MASK-0020 criterion against direct evidence: fixture journeys, native qualifier reports, the owner migration transcript, the structure gate and the full suite on both platforms. Confirm no link producer remains that targets a checkout, no retired command survives in help or capabilities, and no migration path resets or deletes user data.

## Acceptance

Every criterion has direct actual evidence and an implementation revision; every linked card is Done. Pack validation, fixture success and documentation edits are not acceptance. A missing native lane or an unrun owner migration keeps this closeout open.

Criterion coverage: RFC-MASK-0020-AC01, RFC-MASK-0020-AC02, RFC-MASK-0020-AC03, RFC-MASK-0020-AC04, RFC-MASK-0020-AC05, RFC-MASK-0020-AC06, RFC-MASK-0020-AC07, RFC-MASK-0020-AC08.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary (subprocess argv, exit code, JSON stdout, stderr,
filesystem and Git effects). Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Not started. Claim the live remapped card before edits. No code implementation,
native result, host loading, user approval or migration of a real machine is
asserted by this card's existence.

## Durable closeout anchor

RFC_BASE_SHA: b92372f224c04368b6f76d50c0312d95f8035ff3

Planned cards: MASK-0098, MASK-0099, MASK-0100, MASK-0101, MASK-0102, MASK-0103, MASK-0104, MASK-0105.

| Acceptance | Direct check / observation | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0020-AC01 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0020-AC02 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0020-AC03 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0020-AC04 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0020-AC05 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0020-AC06 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0020-AC07 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0020-AC08 | Pending actual implementation evidence | Not run | Not recorded |

Closeout review runtime: Not recorded. Required native and owner-machine boundaries remain
open until their actual evidence is linked. Do not invent a PASS to close the board.
