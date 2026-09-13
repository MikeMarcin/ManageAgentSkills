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

**Dispatch `d2` record (milestone `bootstrap` accepted).** Run `mask-rfc0020-2026-09-12-a`, producer `rfc-integrator-d2`, mandate revision `1`. The owner's mandate is unchanged: `/implement-rfc RFC-MASK-0020`, with no extra stop conditions. No push or publication is authorized, and the owner's real machine is changed only by attended MASK-0105.

- **Accepted milestone `bootstrap`:** MASK-0099 is Done at `eb2eff8`. The implementation is `01b2ae3` plus the review fix `94d4f1c`. MASK-0100 and MASK-0101 were promoted to Ready at `5ea6f13`.
  - Exit 1: `tests.test_tap_bootstrap` passes 6 tests. On an empty `MASK_HOME`, `tap add` followed by `install` deploys v2 consumers from the store, with one bare cache and no checkout anywhere on disk. Negative controls: the pre-implementation product fails 5 of 5, and a retained author checkout fails the no-checkout assertion.
  - Exit 2: on `94d4f1c`, the literal `python -B -m unittest` ran 391 tests OK (19 skipped) in 6477 s, and the per-module run passed all 44 modules. Tree hashes and the owner profile were unchanged across both. Only Windows 11 was exercised.
  - Evidence: [MASK-0099 execution record](../60-done/MASK-0099-machine-v3-and-tap-bootstrap.md#execution-record) and the complete reference in [tap-cutover-baseline.md](../../development/tap-cutover-baseline.md#runs).
- **Binding** (unchanged from dispatch to finish):
  - definition `sha256:4ffc77d27810b0f701a145961f84312dda7c289c56fad62d42261c1b2c20f0d8`
  - obligation `sha256:ea9a3810366abb09d53d794db32643b9c48d85ae82ed10845bde1288776632b2`
  - MASK-0099 source `sha256:9c05f5be4d20237474037f41814bc40bf7c115e67eaf0c7640d0661cca425717`
  - prerequisite `sha256:256c0a53f234c928aa94807fde2efc3ba3352a9c71bece6414d5effed374f87b`
  - The assignment and v2 return are in the ignored `.mask/generated/implement-rfc/runs/mask-rfc0020-2026-09-12-a/`.
  - Card evidence goes under a trailing `## Execution record` heading, which leaves bound text unchanged. The installed helper hashes raw bytes, so a CRLF checkout of a card computes a different source fingerprint.
- **Product state the next milestone inherits:**
  - Machine config v3 is accepted beside v1 and v2, which still work fully. There is no migration gate yet.
  - `init` no longer takes `--source`. `tap add` creates config and state when they are missing. Declarations created on v3 are v2, including those from `project init` and `user init`.
  - On v3, legacy-only paths refuse with typed errors:
    - `migration.required`: v1 declarations, legacy records, `update`, `inventory` rows and `link adopt`.
    - `source.legacy_absent`: `source migrate`, `migrate`, `source status` and `source fetch` without a name.
  - Pinned `update` still does not fetch.
  - Manual pinned `ensure` reaches its one-time consent; events still need approval.
- **Test state:**
  - `tests/support.py` and `tests/public_support.py` start tap-first, providing `TAP`, `self.upstream`, `publish()`, `install()` and `binding()`.
  - Tests of retired behavior start from `legacy_init` or `legacy_bootstrap` and carry a comment naming MASK-0100, MASK-0101 or MASK-0102. MASK-0100 ports or drops them, and should consolidate the local helper variants (`declare_pinned`, `authoring_init`, `push`).
  - `tests/test_tap_bootstrap.py` holds the bootstrap journey and the refusals for legacy records on v3.
- **Board:** MASK-0100 and MASK-0101 are Ready. MASK-0102 to MASK-0106 wait on their dependencies. The criterion rows below stay Not run.
  - MASK-0099 records fixture evidence toward AC01, the `init --source` refusal toward AC05, and the Windows suite toward AC08.
  - Still open: native qualification (AC07), the macOS suite, and the retirement work.
- **Open notes for later cards** (not accepted scope; details are on MASK-0099):
  - retained-pack case B04 names a different refusal code than the product returns;
  - `source publish` republishes LF blobs as CRLF under `core.autocrlf`;
  - a wrong-branch authoring checkout reports different codes with and without an origin;
  - the plan hash of pinned `ensure --dry-run` on a cold store differs from the applying run;
  - a refused `apply`, and a consent refusal after store hydration, both report `partial`;
  - `project init` without machine config still writes v1;
  - `scripts/qualify_real_package.py` still calls `init --source` (MASK-0104);
  - README prose and the guides still describe the checkout journey (MASK-0103).
- **Tooling notes:**
  - The installed `milestone_plan.py adopt` Windows separator defect recorded by d1 is unchanged.
  - Helper scripts need `PYTHONUTF8=1`.
  - A full Windows suite run needs `MASK_HOME`, `USERPROFILE` and `HOME` redirected, because some `Fixture` tests exercise personal scope.
- **Execution state:** all d2 children have returned: the scout, the diagnosis worker, five conversion workers and the critical reviewer. No command or child from d2 is active.
- **Next milestone:** `engine` (MASK-0100 and MASK-0101), in a fresh integrator context. It should retire the live-checkout engine, remove retired commands from `capabilities` so they exit 2, gate v1/v2 configuration with `migration.required`, and make `update` fetch each referenced tap once, with isolation and one journal.

**Dispatch `d1` record (historical; its next milestone and carried obligations were completed by d2).** Refreshed at the end of dispatch `d1`, run `mask-rfc0020-2026-09-12-a`, producer `rfc-integrator-d1`, mandate revision `1`. The owner's mandate is `/implement-rfc RFC-MASK-0020`, with no extra stop conditions. No push or publication is authorized. The owner's real machine is changed only by attended MASK-0105.

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
