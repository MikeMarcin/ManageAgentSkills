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

## Current frontier

Refreshed at the end of dispatch `d1`, run `mask-rfc0020-2026-09-12-a`, producer `rfc-integrator-d1`, mandate revision `1`. The owner's mandate is `/implement-rfc RFC-MASK-0020`, with no extra stop conditions. No push or publication is authorized. The owner's real machine is changed only by attended MASK-0105.

- **Accepted milestone `baseline`:**
  - MASK-0098 is Done at `b294552`; implementation is `82b4200`.
  - Exit 1: the RFC_BASE_SHA below is a real pre-implementation revision. Product sources are identical to it through `82b4200`.
  - Exit 2: `python -B -m unittest tests.test_legacy_baseline -v` passed 7 tests on Windows 11.
  - Evidence: the [MASK-0098 verified outcome](../60-done/MASK-0098-intake-and-legacy-baseline.md#verified-outcome) and [tap-cutover-baseline.md](../../development/tap-cutover-baseline.md).
- **Board:** MASK-0099 is Ready (`f670371`). MASK-0100 to MASK-0105 wait on dependencies, and this closeout is Backlog. Every criterion row below stays Not run; the baseline only supplies fixtures and defect evidence toward AC04 and AC08.
- **Plan and binding:** the [plan](../../rfcs/plans/tap-only-deployment/milestone-plan.json) was adopted at `8a9ea21`. The d1 assignment used `coordinator_handoff.py assign --target RFC-MASK-0020 --milestone baseline` with the identity above.
  - Unchanged since dispatch: definition `sha256:3b9c167aa01b554e2a17f288d0def0d19d7833507fff8319367cbecf6164043a` and prerequisite `sha256:44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`.
  - Changed: obligation `sha256:229b3a9dbe595dc04d948a6425a7ee0a0cf6dd1971426790bc28a30a666f19fd` at dispatch is now `sha256:e9312d222eeaca3547ffef202943ac00af2c8f3285a92387e45601c5527bd434`.
  - Cause: a card's bound requirement text runs from `## Acceptance` to the end of the card unless an `## Execution record` heading ends it. MASK-0098 has no such heading, so replacing its `## Run record` with the verified outcome changed its source fingerprint (`d1dfe28f…` to `a8f03244…`). Its Acceptance text is byte-identical.
  - Action: renew the assignment before checking the d1 return. Evidence written under any other heading will change later bindings the same way.
- **Windows reference suite:** incomplete; it was stopped after 32 minutes. The first 155 results ran on unchanged code and include six failing existing tests, listed in [tap-cutover-baseline.md](../../development/tap-cutover-baseline.md#runs). Later results are a stop artefact. The owner profile snapshot was unchanged. No command or child from this dispatch is active.
- **Upstream note:** the installed `milestone_plan.py adopt` builds its receipt path with a Windows separator. Adoption was run under WSL; see [LIVE_IMPORT](../../rfcs/assets/mask-corrective-managed-taps.LIVE_IMPORT.md).
- **Next milestone:** `bootstrap` (MASK-0099), in a fresh integrator context:
  - config v3 alongside v1 and v2
  - `init` without `--source`
  - `tap add` bootstrap on an empty `MASK_HOME`
  - tap-first cutover of `tests/support.py` and `tests/public_support.py`
  - the full suite green while legacy code still exists
- **Carried obligations for MASK-0099:**
  - Replace the `LiveCheckoutBaseline` tests that call `init --source`; their evidence is recorded at `82b4200`. `LegacyFixtureBytes` stays.
  - Establish a complete Windows full-suite reference that separates the six existing failures from regressions.

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
