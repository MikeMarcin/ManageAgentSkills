---
schema: "implement-rfc.card.v1"
id: "MASK-0104"
title: "Requalify the real AgentSkills package and legacy lab natively"
status: "Parked"
rfcs: ["RFC-MASK-0020"]
depends_on: ["MASK-0101", "MASK-0102", "MASK-0103", "MASK-0107"]
priority: "P1"
metadata: {"packet":"mask-corrective-managed-taps","provisional_id":false,"packet_key":"real-package-qualifier-on-taps","milestone_plan":{"id":"tap-only-deployment","path":"docs/rfcs/plans/tap-only-deployment/milestone-plan.json"}}
parked_on: "human-review"
acceptance: [{"criterion":"Bounded work: the qualifier uses tap add, install, a pushed candidate followed by update, remove instead of project unrequire, and a legacy-lab doctor migration","outcome":"pass","revision":"f9c7fbc","evidence":{"kind":"artifact","detail":"scripts/qualify_real_package.py at f9c7fbc (sha256 d565fe3453872338f0451774ab399c87d3a2a40595e416f439edd4b15b0a63c2): tap lab, legacy lab (tests/legacy_support.py v1 machine: doctor --check 7, --migrate --dry-run, --migrate, doctor --check 0, update) and owner-shape rehearsal sections."}},{"criterion":"The qualifier passes every step on native Windows 11 against the real AgentSkills repository as a tap, including push-then-update and the legacy lab, with private MASK_HOME, HOME and USERPROFILE; the report names OS, Python, Git and MASK revisions","outcome":"pass","revision":"8ea0fe5","evidence":{"kind":"command","detail":"Guarded run (implement-rfc qualification_guard; owner ~/.mask files, AgentSkills .git files and this repository's .mask.json unchanged): python -B scripts/qualify_real_package.py --mask <disposable clone at 8ea0fe595489fe702a51b446f7ed1c6ec106de8f>/mask.py --agentskills C:\\code\\git\\AgentSkills --work <disposable> --fake-host windows. 61/61 steps (tap lab 47, legacy lab 6, owner rehearsal 8). Windows 11 Home (Core) 10.0.26200 AMD64, Python 3.14.6, Git 2.55.0.windows.3, system core.autocrlf=true; AgentSkills 16192b76ec1bbaee001c718d3e82d447db4f25c5 unchanged. Record: docs/development/readiness-acceptance.md 'Real-package qualification on taps (RFC-MASK-0020, MASK-0104)'; report, guard receipt and log in the d7 session scratchpad d7-final/qualifier/."}},{"criterion":"The qualifier passes every step on native macOS with the same scope and report facts","outcome":"pending","revision":"8ea0fe5","evidence":{"kind":"freeform","detail":"Not run: the station registry (docs/development/remote-stations.md) names no macOS station and dispatch d7 ran on Windows. Exact ask on this card's execution record: run the qualifier on a Mac with --fake-host posix from a disposable clone at the candidate, or authorize a macOS station."}}]
---

# MASK-0104: Requalify the real AgentSkills package and legacy lab natively

Governing RFC: [RFC-MASK-0020](../../rfcs/RFC-MASK-0020-tap-only-deployment.md). Live IDs confirmed by the committed pack reservation `b92372f`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-managed-taps.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-managed-taps/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-managed-taps/ACCEPTANCE.md).

## Objective and owned paths

`scripts/qualify_real_package.py`, `docs/development/readiness-acceptance.md` and the recorded qualification reports.

## Bounded work

Replace `init --source` in the qualifier with `tap add agentskills <disposable upstream>`, create consumers with `install implement-rfc --project ROOT`, push a candidate to the disposable upstream and run `mask update`, and add a legacy-lab step that builds a v1 machine with `tests/legacy_support.py`, runs `doctor --check` (7), `doctor --migrate --dry-run`, `doctor --migrate`, `doctor --check` (0) and `update`. Run the qualifier on native Windows 11 and macOS and record both reports.

## Acceptance

The qualifier passes every step on both native platforms against the real AgentSkills repository as a tap, including the push-then-update and legacy-lab steps, with private `MASK_HOME`, `HOME` and `USERPROFILE`. Reports name the OS, Python, Git and MASK revisions actually exercised.

Criterion coverage: RFC-MASK-0020-AC01, RFC-MASK-0020-AC03, RFC-MASK-0020-AC04, RFC-MASK-0020-AC07.

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

## Execution record

Dispatch `d7` of run `mask-rfc0020-2026-09-12-a`, producer `rfc-integrator-d7`, mandate revision `4`. The card was claimed at `c354a59`, and the qualifier was implemented at `f9c7fbc` (W1, `rfc-worker`).

- **Bounded work:** all of it is in the driver.
  - The tap bootstrap replaces `init --source`, and `install` creates the consumers.
  - `remove` replaces the retired `project unrequire`.
  - A candidate is pushed to a disposable bare upstream and followed by a plain `update`.
  - A legacy lab runs `doctor --check` 7, `--migrate --dry-run`, `--migrate`, `doctor --check` 0 and `update`.
  - A small owner-shape rehearsal of MASK-0105 was added.
- **Native Windows 11:** 61/61 steps against MASK `8ea0fe5` and AgentSkills `16192b7`, with private `MASK_HOME`, `HOME` and `USERPROFILE`. The guard passed, and the owner's live files and the AgentSkills clone were unchanged. The report names the OS, Python, Git, `core.autocrlf`, both revisions and the script digest. Record: [readiness acceptance](../../development/readiness-acceptance.md#real-package-qualification-on-taps-rfc-mask-0020-mask-0104).
- **Native macOS:** not run. The [station registry](../../development/remote-stations.md) names no macOS station, and this dispatch ran on Windows. The card stays open until a macOS report exists.
- **Exact ask (macOS):**
  - Where: a Mac with Python 3 and Git, in a disposable clone of ManageAgentSkills at the recorded candidate, with a clone of AgentSkills at `16192b7`.
  - Run:
    `python3 -B scripts/qualify_real_package.py --mask "$PWD/mask.py" --agentskills <AgentSkills clone> --work <new disposable directory> --fake-host posix --report <report.json>`
  - Then either hand back `report.json`, or authorize a macOS station row so an integrator can run it.
  - Acceptance needs every step to pass, with the report naming macOS, Python, Git and the MASK revision.
- **Findings:** no product defect was found.
  - The owner-shape rehearsal's `doctor --check` exit 7 is a fact about MASK-0105's acceptance and is recorded there.
  - A `doctor --check` failure reports the documented umbrella code `state.drift`, with the specific codes in its issue rows.
- **Review:** no independent review. This is an evidence driver with no product change.
