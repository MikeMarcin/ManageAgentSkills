---
schema: "implement-rfc.card.v1"
id: "MASK-0098"
title: "Record baseline and build the legacy machine fixture"
status: "Done"
rfcs: ["RFC-MASK-0020"]
depends_on: []
priority: "P1"
metadata: {"packet":"mask-corrective-managed-taps","provisional_id":false,"packet_key":"intake-and-legacy-baseline","milestone_plan":{"id":"tap-only-deployment","path":"docs/rfcs/plans/tap-only-deployment/milestone-plan.json"}}
acceptance: [{"criterion":"baseline:exit:1 closeout carries the real pre-implementation revision","outcome":"pass","revision":"82b4200f8aaa4ef107faebbb3e76eede7021bbae","evidence":{"kind":"observation","detail":"MASK-0106 durable closeout anchor records RFC_BASE_SHA b92372f224c04368b6f76d50c0312d95f8035ff3; git diff --quiet b92372f 1f93ab0 over mask*.py, schemas, tests, scripts, README.md and docs/guides reported no change, so the base precedes all RFC-MASK-0020 source work."}},{"criterion":"baseline:exit:2 baseline test proves parsers accept legacy fixture bytes and a legacy install links into the clone","outcome":"pass","revision":"82b4200f8aaa4ef107faebbb3e76eede7021bbae","evidence":{"kind":"command","detail":"python -B -m unittest tests.test_legacy_baseline -v on Windows 11 Home 10.0.26200, Python 3.14.6, Git 2.55.0.windows.3: 7 tests OK (55 s) on bytes identical to 82b4200. LegacyFixtureBytes parses every file unchanged; LiveCheckoutBaseline reads project and personal links whose text is \\\\?\\<base>\\AgentSkills\\skills\\<id>."}},{"criterion":"MASK-0098 reusable starting states: v1 machine, v2 machine with extra tap, legacy project, legacy personal scope, unregistered v1 declaration","outcome":"pass","revision":"82b4200f8aaa4ef107faebbb3e76eede7021bbae","evidence":{"kind":"artifact","detail":"tests/legacy_support.py build_legacy_machine(base, version) and write_machine; LiveCheckoutBaseline proves the builder reproduces the base program's bytes and link texts for the v1 machine, the v2 machine with an extra tap and the remote-less empty registry."}},{"criterion":"MASK-0098 each recorded defect names its command and the observed link target","outcome":"pass","revision":"82b4200f8aaa4ef107faebbb3e76eede7021bbae","evidence":{"kind":"artifact","detail":"docs/development/tap-cutover-baseline.md, Recorded defects table: init --source, install (project and --user), clone edit, source migrate plus tap add, remote-less source migrate, pinned update cold and warm cache."}},{"criterion":"MASK-0098 mask_core.config and mask_core.state accept the fixture bytes unchanged","outcome":"pass","revision":"82b4200f8aaa4ef107faebbb3e76eede7021bbae","evidence":{"kind":"command","detail":"LegacyFixtureBytes (3 tests in the run above): parse(value) == value and text_json(value) == raw bytes for config, state and declarations; machine v1/v2 schema key shape. Negative control: a mode field on a legacy record fails mask_core.state (Unexpected or missing fields)."}},{"criterion":"MASK-0098 no fixture pre-migrates, pre-fetches or pre-registers","outcome":"pass","revision":"82b4200f8aaa4ef107faebbb3e76eede7021bbae","evidence":{"kind":"observation","detail":"assert_legacy_consumers requires MASK_HOME/sources, store, pending.json, user.lock.json, the project lock and the unregistered declaration's links to be missing and the straggler to be absent from state; config.json and state.json are the only files of the empty-registry machine."}}]
---

# MASK-0098: Record baseline and build the legacy machine fixture

Governing RFC: [RFC-MASK-0020](../../rfcs/RFC-MASK-0020-tap-only-deployment.md). Live IDs confirmed by the committed pack reservation `b92372f`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-managed-taps.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-managed-taps/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-managed-taps/ACCEPTANCE.md).

## Objective and owned paths

Intake, the live RFC and index rows, new cards, `tests/legacy_support.py`, `tests/test_legacy_baseline.py` and `docs/development/tap-cutover-baseline.md`. The integrator owns allocation and reservations; no unrelated tracker history changes.

## Bounded work

Record the real pre-implementation revision in the closeout. Capture the current behavior as evidence through the public CLI: `init --source` creates a v1 machine, `install` links `<consumer>/.claude/skills/<id>` and `<consumer>/.agents/skills/<id>` to `<clone>/skills/<id>`, `source migrate` still binds the clone, and pinned `update` does not fetch. Write a schema-true legacy fixture builder that produces v1 and v2 machines with mode-less records, v1 declarations and real directory symlinks, and assert that the current parsers accept every fixture byte so later doctor tests migrate exactly what old MASK wrote.

## Acceptance

A v1 machine fixture, a v2 machine fixture (legacy binding plus one extra tap), a legacy project, a legacy personal scope and an unregistered v1 declaration exist as reusable starting states. Each recorded defect names its command and the observed link target. The fixture builder writes files that `mask_core.config` and `mask_core.state` accept unchanged. No fixture pre-migrates, pre-fetches or pre-registers what a later card is meant to prove.

Criterion coverage: RFC-MASK-0020-AC04, RFC-MASK-0020-AC08.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary (subprocess argv, exit code, JSON stdout, stderr,
filesystem and Git effects). Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Verified outcome

Implementation commit: `82b4200f8aaa4ef107faebbb3e76eede7021bbae`. It adds `tests/legacy_support.py`, `tests/test_legacy_baseline.py` and [tap-cutover-baseline.md](../../development/tap-cutover-baseline.md). Intake on main adopted the plan and recorded RFC acceptance at `8a9ea21`; the claim is `1f93ab0`. RFC_BASE_SHA `b92372f` is on closeout MASK-0106, and product sources at HEAD are byte-identical to it.

The focused run used Windows 11 Home 10.0.26200, Python 3.14.6 and Git 2.55.0.windows.3, with a disposable `MASK_HOME` and a fixture personal home. `python -B -m unittest tests.test_legacy_baseline -v` passed 7 tests in 55 s on bytes identical to the implementation commit.

- **Starting states.** `build_legacy_machine` writes a v1 machine and a v2 machine (legacy binding plus an extra tap). Each has a registered legacy project, a registered legacy personal scope and an unregistered v1 declaration. Options give an empty registry and a clone without a remote.
- **Parser acceptance.** Each file parses unchanged with `mask_core.config`, `mask_core.state` or `mask_core.manifest`, and re-serializes to identical bytes. Keys follow the machine v1 and v2 schemas.
- **Base program equality.** The CLI ran `init --source`, `install` (project and `--user`), `source migrate` and `tap add`. Removing exactly what the CLI wrote and rebuilding gave identical bytes and link texts. This held for the v1 machine, the v2 machine and the remote-less empty registry.
- **Recorded defects.** Each names its command and the observed link target; see [recorded defects](../../development/tap-cutover-baseline.md#recorded-defects).
- **No preparation.** Tests assert that none of these exist: `MASK_HOME/sources`, a store, a lock, a pending journal, or a registration or links for the unregistered declaration.
- **Negative controls.** Four deliberate builder defects each failed the corresponding check: the generation, the Windows link-text prefix, a `mode` field and the catalog `ref` spelling. The unpatched control passed.

Limitations:
- macOS was not exercised for this card.
- `LiveCheckoutBaseline` asserts retired behavior. MASK-0099, MASK-0100 and MASK-0101 replace it.
- The builder omits the base program's one-byte `operation.lock`.
- No real machine, host loading or AgentSkills repository was touched.

Independent review was not commissioned. No product behavior changed. The material risk is fixtures that differ from what the base program wrote, and the byte comparison and its negative controls test that directly.
