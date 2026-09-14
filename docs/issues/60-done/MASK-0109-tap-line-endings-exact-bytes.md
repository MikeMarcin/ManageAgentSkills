---
schema: "implement-rfc.card.v1"
id: "MASK-0109"
title: "Keep exact bytes on taps unless line-ending conversion is opted in at tap registration"
status: "Done"
rfcs: []
depends_on: ["MASK-0102", "MASK-0103"]
priority: "P1"
metadata: {"origin":"RFC-MASK-0021 owner decision, mandate r2 (2026-09-13)","follow_up_of":"MASK-0101","sequenced_before":["MASK-0106","MASK-0107"]}
acceptance: [{"criterion":"A1 exact tap: unchanged LF package publishes no change; a changed file publishes exact bytes","outcome":"pass","revision":"4c0549fd6b1d1183557d0b4418bfc402eec3d4c3","evidence":{"kind":"command","detail":"python -B -m unittest tests.test_tap_line_endings: ExactTap.test_unchanged_lf_package_publishes_no_change_and_an_edit_publishes_exact_bytes; session scratchpad d5/final-module/tests.test_tap_line_endings.log (16 tests OK, 514 s, Windows 11, Git 2.55.0.windows.3, system core.autocrlf=true)"}},{"criterion":"A2 source dev-link of an unchanged package observes the locked payload digest","outcome":"pass","revision":"4c0549fd6b1d1183557d0b4418bfc402eec3d4c3","evidence":{"kind":"command","detail":"ExactTap.test_dev_link_of_an_unchanged_package_observes_the_locked_payload_digest and AutocrlfTap.test_a_converted_clone_publishes_no_change_and_dev_links_the_locked_digest compare data.development[].payload_digest with the lock; session scratchpad d5/final-module/tests.test_tap_line_endings.log (16 tests OK, 514 s, Windows 11, Git 2.55.0.windows.3, system core.autocrlf=true)"}},{"criterion":"A3 with the opt-in, conversion follows core.autocrlf=true and is disclosed","outcome":"pass","revision":"4c0549fd6b1d1183557d0b4418bfc402eec3d4c3","evidence":{"kind":"command","detail":"AutocrlfTap (4 tests: disclosure without warning, no change on a converted clone, CRLF edit equals git hash-object oracle, attribute refusal) and AutocrlfFidelity (new-file and committed-copy cases against git hash-object and git add); session scratchpad d5/final-module/tests.test_tap_line_endings.log (16 tests OK, 514 s, Windows 11, Git 2.55.0.windows.3, system core.autocrlf=true)"}},{"criterion":"A4 configurations written before this card keep working","outcome":"pass","revision":"4c0549fd6b1d1183557d0b4418bfc402eec3d4c3","evidence":{"kind":"command","detail":"EntryWrittenBeforeThePolicy (entry without line_endings: show, install, update, publish, dev-link, identical tap add keeps config bytes, --autocrlf conflicts); every tests/test_*.py module passes (worker post/rerun logs and d5 integ run)"}},{"criterion":"A5 machine v3 schema, CLI contract, help and capabilities describe the policy","outcome":"pass","revision":"4c0549fd6b1d1183557d0b4418bfc402eec3d4c3","evidence":{"kind":"command","detail":"PolicySurfaces (capabilities line_endings and --autocrlf flag, tap add --help, schema enum not required); docs/architecture/cli-contract.md Tap line endings; python scripts/verify_documentation.py --root . reports 0 structural violations"}},{"criterion":"Bounded work: doctor --migrate writes the exact default","outcome":"pass","revision":"4c0549fd6b1d1183557d0b4418bfc402eec3d4c3","evidence":{"kind":"command","detail":"MigrationWritesTheDefault (v1, v2 kept and extra, v2 renamed; report, dry run and written config) and tests.test_doctor_migration 22 OK"}},{"criterion":"Bounded work: an exact tap over a Git-converted checkout no longer republishes CRLF","outcome":"pass","revision":"4c0549fd6b1d1183557d0b4418bfc402eec3d4c3","evidence":{"kind":"command","detail":"ExactTap.test_exact_tap_over_a_converted_clone_warns_then_refuses_before_any_effect (warning, refusal before any effect for publish, publish --commit, dev-link dry run and apply; delete-and-checkout remediation); negative control on an archive of 6496967: publish previews would_change true and the module fails 7 failures and 22 errors"}}]
---

# MASK-0109: Keep exact bytes on taps unless line-ending conversion is opted in at tap registration

Owner decision (September 13, 2026, run `mask-rfc0020-2026-09-12-a`, mandate revision r2, verbatim): "we should disable autocrlf on taps by default unless explicitly requested keeping exact bytes and only if a user explicitly opts in during tap registration should wee use autocrlf true". Filing was authorized with "sure file"; implementation is not restricted (r3).

## Evidence

[MASK-0101 execution record](MASK-0101-machine-v3-and-tap-bootstrap.md#contract-notes-and-follow-up-candidates): under `core.autocrlf=true`, `source publish` hashes working bytes without filters, so it republishes LF blobs as CRLF. Tests now disable conversion by hand (for example a `* -text` publisher attribute). The owner's Windows machine uses `core.autocrlf=true`.

## Objective and owned paths

Tap registration, catalog entry, and every MASK Git operation on a tap's cache or approved authoring checkout: `mask_sources.py` (binding, `tap add`, publication), `mask_provenance.py` (working payloads), `mask_pinned.py` (dev-link observation), `schemas/machine-v3.schema.json`, the CLI contract and capabilities, and focused tests.

## Bounded work

- By default, a tap keeps exact bytes. MASK disables Git line-ending conversion for its operations on that tap and for its authoring checkout, so published blobs, development payloads and locked payload digests agree.
- Only an explicit opt-in at `tap add` enables `core.autocrlf` for that tap. The opt-in is recorded in the catalog entry and disclosed in output.
- Existing v3 entries without the field mean exact bytes. `doctor --migrate` writes the default.
- Record the amendment to the RFC-MASK-0021 tap entry shape in the RFC and the machine v3 schema.

## Acceptance

On a host whose Git configuration has `core.autocrlf=true`:
- For a tap added without the opt-in, `source publish` of an unchanged LF package reports no change, and a changed file is published with its exact bytes.
- `source dev-link` of an unchanged package observes the locked payload digest.
- With the opt-in, conversion follows `core.autocrlf=true` and is disclosed.
- Configurations written before this card keep working.
- The machine v3 schema, CLI contract, help and capabilities describe the policy.

## Sequencing

MASK-0106 (native real-package qualification) and MASK-0107 (owner machine migration) depend on this card. Both run on the owner's `core.autocrlf=true` Windows host and should exercise the final byte policy.

## Execution record

Dispatch `d5` of run `mask-rfc0020-2026-09-12-a`, producer `rfc-integrator-d5`, mandate revision `3` (r4 arrived during the dispatch). Claim `6496967`; implementation `4c0549f`. The r4 decision record is the separate commit `0be6b26`.

- **Plan position:** this card sits outside the adopted `tap-only-deployment` plan.
  - `milestone_plan.py discover` reports `absent` for this card, and `coordinator_handoff.py assign` refuses without a plan.
  - `check-amendment` refuses adding the card to the plan scope or to `unplanned_work`.
  - The outcome is therefore this card's own acceptance, and the plan is unchanged.
- **Behavior:**
  - **Tap entries** carry `line_endings`: `exact` by default, and an absent field also means exact. Only `tap add --autocrlf` records `autocrlf`.
    - `tap add` and `doctor --migrate` write the field.
    - `tap add`, `source show`, `source publish` and `source dev-link` report it, and `source dev-link` also reports observed development payload digests.
  - **An exact tap** reads raw authoring bytes.
    - `source publish` and a new `source dev-link` refuse `source.line_endings_converted` (exit 4, with repository paths) when unedited files differ from their committed copies only in line endings.
    - `tap add --checkout` warns `source.line_endings_conversion` when the checkout's effective `core.autocrlf` converts.
    - MASK never writes the checkout's Git configuration.
  - **An autocrlf tap** applies Git's `core.autocrlf=true` check-in conversion (`mask_provenance.autocrlf`). A `text`, `eol`, `crlf`, `filter`, `ident` or `working-tree-encoding` attribute refuses `source.line_endings_unsupported`.
- **Acceptance:** exercised on Windows 11 Home 10.0.26200 with Python 3.14.6 and Git 2.55.0.windows.3, whose system configuration sets `core.autocrlf=true`. `tests/test_tap_line_endings.py` also forces that setting through `GIT_CONFIG_GLOBAL`.

| Criterion | Evidence | Outcome |
|---|---|---|
| Without the opt-in, an unchanged LF package publishes no change and a changed file publishes exact bytes | `ExactTap.test_unchanged_lf_package_publishes_no_change_and_an_edit_publishes_exact_bytes` | Pass |
| `source dev-link` of an unchanged package observes the locked payload digest | `ExactTap.test_dev_link_of_an_unchanged_package_observes_the_locked_payload_digest`; `AutocrlfTap.test_a_converted_clone_publishes_no_change_and_dev_links_the_locked_digest` | Pass |
| With the opt-in, conversion follows `core.autocrlf=true` and is disclosed | `AutocrlfTap` (4 tests); `AutocrlfFidelity` against `git hash-object` and `git add` | Pass |
| Configurations written before this card keep working | `EntryWrittenBeforeThePolicy`; every existing test module passes | Pass |
| The schema, CLI contract, help and capabilities describe the policy | `PolicySurfaces`; "Tap line endings" in `docs/architecture/cli-contract.md`; structure gate with 0 violations | Pass |
| Bounded work: `doctor --migrate` writes the default | `MigrationWritesTheDefault`; `tests.test_doctor_migration` | Pass |
| Bounded work: an exact tap never republishes a converted checkout | `ExactTap.test_exact_tap_over_a_converted_clone_warns_then_refuses_before_any_effect` | Pass |

- **Negative controls** on an archive of `6496967`:
  - A public-CLI scratch run shows `tap add --autocrlf` exiting 2, and `source publish` over a converted clone previewing `would_change: true`.
  - The new module fails there with 7 failures and 22 errors.
- **Suite:** every `tests/test_*.py` module passes.
  - The new module ran 16 tests OK (514 s) on the committed content.
  - Seven more modules ran after the final product change. The rest ran after the fixture change but before the final autocrlf fix, which affects only `--autocrlf` taps.
  - Three modules failed once under six parallel lanes with a Windows DLL initialization error (`0xC0000142`), then passed on a sequential rerun.
  - Logs are in the d5 session scratchpad. This was not the literal single-process run, and macOS was not exercised.
- **Defect found and fixed during the slice:** the first `autocrlf` treated any committed CR as Git's `has_crlf_in_index`. Git requires a committed text copy that contains CRLF. A public-CLI reproducer and fidelity cases now cover it.
- **Remediation finding:** Git leaves a stat-clean converted file in place for both `checkout-index --force` and `checkout HEAD --`. The refusal and the docs therefore say to delete the unedited files, then run `git checkout -- PATH`.
- **Review:** no independent review was performed.
  - `rfc-reviewer-critical` was dispatched twice, and both attempts failed with an account usage limit on `claude-fable-5-1` (HTTP 429).
  - `rfc-reviewer` binds the same model, and no model fallback is authorized.
- **Limitations:**
  - Recovery recomputes the migrated configuration, so it now refuses a `doctor.migrate` journal written by the previous program. Finish pending recovery before switching executables; no real machine holds such a journal.
  - No test covers later observations of an existing dev link over a converted checkout. Those observations follow the policy without refusing.
  - An autocrlf tap refuses every specified line-ending attribute, including `-text`, instead of modeling it.
  - A previous tap-era program refuses a catalog entry that carries `line_endings`.
