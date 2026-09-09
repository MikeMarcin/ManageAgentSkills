---
schema: "implement-rfc.card.v1"
id: "MASK-0093"
title: "Verify and close the task CLI and human-output correction"
status: "Backlog"
rfcs: ["RFC-MASK-0018"]
depends_on: ["MASK-0091"]
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": false, "packet_key": "close-human-cli-correction"}
closeout_for: ["RFC-MASK-0018"]
---

# MASK-0093: Verify and close the task CLI and human-output correction

Governing RFC: [RFC-MASK-0018](../../rfcs/RFC-MASK-0018-task-oriented-cli-and-human-output.md). Live IDs confirmed by the committed pack reservation `6d80121`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-ux-readiness.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-ux-readiness/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-ux-readiness/ACCEPTANCE.md).

## Objective and owned paths

This RFC, its closeout, current affected docs and integrated evidence references only.

## Bounded work

Reconcile all RFC-MASK-0018 criteria at their stated public boundaries. Reuse unchanged focused evidence, check current diff and documentation, and confirm no non-JSON command falls back to envelope serialization. This closeout does not certify unfinished workflow-role work.

## Acceptance

Every criterion has direct actual evidence and an implementation revision; every linked required card is Done. Required native human journeys cannot be marked passed from pipes/mocks alone. Preserve honest limitations and the real pre-implementation baseline.

Criterion coverage: RFC-MASK-0018-AC01, RFC-MASK-0018-AC02, RFC-MASK-0018-AC03, RFC-MASK-0018-AC04, RFC-MASK-0018-AC05, RFC-MASK-0018-AC06, RFC-MASK-0018-AC07, RFC-MASK-0018-AC08.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary. Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation, and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Not started. Claim the live remapped card before edits. No code implementation,
native result, host loading, user approval, or quota improvement is asserted.

## Durable closeout anchor

RFC_BASE_SHA: 6d80121b1c870f1be7864e8bc9db2b02a0e41c2d

Planned cards: MASK-0083, MASK-0084, MASK-0085, MASK-0086, MASK-0087, MASK-0091.

| Acceptance | Direct check / observation | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0018-AC01 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0018-AC02 | Baseline only: `tests.test_public_baseline` retains envelope-dump failures for inventory/version/capabilities (MASK-0083) | Not run | Not recorded |
| RFC-MASK-0018-AC03 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0018-AC04 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0018-AC05 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0018-AC06 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0018-AC07 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0018-AC08 | Baseline fixtures do not inject --json (MASK-0083); native macOS/Windows journeys not yet exercised | Not run | Not recorded |

Closeout review runtime: Not recorded. Required native/upstream boundaries remain
open until their actual evidence is linked. Do not invent a PASS to close the board.

## Current continuation (corrective pack)

Milestone M0 (MASK-0083) is Done: import, reconciliation and the public regression baseline exist; see `docs/development/corrective-baseline.md`. Usable result: `tests/public_support.py` provides raw/machine/human helpers and the three unprepared starting states; `tests/test_public_baseline.py` records seven failing expectations as `expectedFailure`. Invariants: never inject `--json` in the human helper; never pre-register, approve or render roles for the command under test; the linked-consumer state keeps its old role files. Next bounded milestone: MASK-0084 (human renderer for every registered command, readable errors, help/version, remove the indented-JSON fallback in `mask.py::main`), which should flip the three `HumanOutputBaseline` expected failures. MASK-0088 is the independent RFC-MASK-0019 start after MASK-0083. Open obligations: native Windows lane (ExampleWinHost station), real AgentSkills handoff (no ASK ID yet), host-loading observation. MASK-0094 links here rather than duplicating this record.
