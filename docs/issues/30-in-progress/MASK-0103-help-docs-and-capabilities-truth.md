---
schema: "implement-rfc.card.v1"
id: "MASK-0103"
title: "Make help, docs and capabilities describe only the tap model"
status: "In Progress"
rfcs: ["RFC-MASK-0020"]
depends_on: ["MASK-0100", "MASK-0101", "MASK-0102"]
priority: "P1"
metadata: {"packet":"mask-corrective-managed-taps","provisional_id":false,"packet_key":"help-docs-and-capabilities-truth","milestone_plan":{"id":"tap-only-deployment","path":"docs/rfcs/plans/tap-only-deployment/milestone-plan.json"}}
---

# MASK-0103: Make help, docs and capabilities describe only the tap model

Governing RFC: [RFC-MASK-0020](../../rfcs/RFC-MASK-0020-tap-only-deployment.md). Live IDs confirmed by the committed pack reservation `b92372f`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-managed-taps.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-managed-taps/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-managed-taps/ACCEPTANCE.md).

## Objective and owned paths

`mask_present.py`, `README.md`, `docs/guides/installation.md`, `docs/guides/sources-and-updates.md`, `docs/guides/migration-and-pins.md`, `docs/architecture/cli-contract.md`, `docs/architecture/state-and-recovery.md`, `docs/architecture/test-boundaries.md`, `AGENTS.md`, `.mask/skill-config/implement-rfc/project.md` where it names retired commands, `tests/test_human_output.py`, `tests/test_readme_journeys.py` and a new retired-spelling documentation test.

## Bounded work

Rewrite the start-here text, everyday table and command help for `init`, `tap add`, `install`, `update`, `source fetch` and `doctor --migrate`. Replace the local-clone installation journey with the tap bootstrap in README and the installation guide; rewrite the sources guide around fetching updates; turn the migration guide into migrating from a live checkout with an old-command table. Update the CLI contract inventory and the state/recovery architecture for `doctor.migrate`. Replay the README recipes through the public CLI.

## Owner decisions (mandate r4, September 13, 2026)

- **Q4**, verbatim: "point users to install and remove".
  - v2 `project/user set|require|unrequire` are not implemented; they keep refusing `selection.command_unsupported`.
  - This card makes that refusal, its help and the CLI contract point to `install` and `remove`. The refusal text is in `mask.py`, which this decision adds to the owned paths.
  - It also supersedes the RFC-MASK-0020 Retirement sentence that says these commands "remain for v2 declarations".
- **Q5**, verbatim: "just make migration best effort, we're going to run migration on a single machine and then drop it entirely so dont put a lot into it".
  - The AC05 gate is unchanged: `project unregister --keep-links` and `workspace forget` stay refused on a v1 or v2 machine.
  - The migration guide says briefly that a consumer `doctor --migrate` cannot convert must be restored on disk before migrating.
  - Add no migration features or hardening.

## Acceptance

README recipes execute verbatim through the tap-first fixtures. Help output for every registered command renders and names no retired command. The documentation test finds the retired spellings only under `docs/rfcs/assets`, in historical RFC text and in the migration guide's old-command table. `capabilities` reflects the final command table.

Criterion coverage: RFC-MASK-0020-AC05, RFC-MASK-0020-AC06.

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

Dispatch `d6` of run `mask-rfc0020-2026-09-12-a`, producer `rfc-integrator-d6`, mandate revision `4`. The card was worked as milestone `truth` of the adopted `tap-only-deployment` plan. Claim `cf8c725`; implementation `4285146`.

- **Binding** (unchanged at finish):
  - definition `sha256:71edb75ce31f56f93508fd3e51215f3258d810d56e932d2d7b8b22d62c5066eb`
  - obligation `sha256:36e421d5640b89b8d365caf8e3bc9cd2d8fa5c128cc74377a75857339a3d2e60`
  - prerequisite `sha256:8ab8bfb6f05b93d38cae2665c74bbd1b284a3204f882aa796c764ff11445d497`
- **Help:** the following describe taps, the fetching update and doctor migration:
  - root help ("Start here", "Everyday commands", "Choose where");
  - `init`, `tap add`, `install`, `update`, `source fetch`, `doctor` (including `--migrate` and the tap-machine form);
  - `skill list/show/validate`, `source list/show/inspect` and `config show`.
  The dead presentation entries for `source.status`, `source.migrate` and `migrate`, and the unused option texts, are removed.
- **Owner decision Q4:** `project/user set|require|unrequire` still refuse `selection.command_unsupported` (exit 4).
  - The refusal is `mask_resolve.refuse_selection_setter`. `guard_command` reaches it first; `project_dispatch` keeps it as a fallback.
  - The refusal and the help name `mask install ID` and `mask remove ID` with the matching scope flag.
- **Owner decision Q5:** the migration guide says a consumer that `doctor --migrate` cannot convert is restored on disk first, and that `project unregister --keep-links` and `workspace forget` stay refused until migration. No migration code changed.
- **Documents changed:**
  - README, and the installation, sources, migration, declarations, readiness, recovery and development guides, plus CONTRIBUTING.
  - The migration guide is retitled "Migrating from a live checkout" and has an `## Old commands` table.
  - The CLI contract: its inventory matches `capabilities`, and it covers the migration gate, retired commands, update semantics, doctor migration and switching executables.
  - The state/recovery architecture: v3 config, state, caches and store, the `update` and `doctor.migrate` journals, and retired journals.
  - The test boundaries.
- **Acceptance:** exercised on Windows 11 Home 10.0.26200 with Python 3.14.6 and Git 2.55.0.windows.3.

| Criterion | Evidence | Outcome |
|---|---|---|
| README recipes execute verbatim through the tap-first fixtures (milestone exit 1) | `tests.test_readme_journeys`. `ReadmeText` pins every fenced README block and every Everyday row. `ReadmeRecipes` replays them through the launcher that `self install` wrote from a disposable program clone, on a local fixture tap; the module docstring names each substitution, and `mask self update` updates only that clone. Negative controls: `ReadmeText` fails against the README of `b00d107`, and fails for one changed Everyday row | Pass; the pty prompt case is POSIX-only and was skipped |
| Help for every registered command renders and names no retired command | `tests.test_retired_spellings.HelpAndCapabilities` checks the root, every group and every leaf page through `mask.help_text`, and public `--help`, `update --help` and `doctor --help`. The presentation tables name only registered commands; at `cf8c725` that test failed on the dead `migrate`, `source.migrate` and `source.status` entries | Pass |
| The documentation test finds retired spellings only under `docs/rfcs/assets`, in historical RFC text and in the migration guide's old-command table (milestone exit 2) | `tests.test_retired_spellings.CurrentDocumentation`. At `cf8c725` it failed for `cli-contract.md`, `installation.md`, `migration-and-pins.md` and `sources-and-updates.md`, and because the table was missing | Pass |
| `capabilities` reflects the final command table | `test_public_help_and_capabilities` compares `capabilities --json` names with `mask.COMMANDS`. `tests.test_retired_paths` shows the retired commands absent. W3 cross-checked the contract inventory against `capabilities` and found no missing or extra row | Pass |
| Owner decision Q4 | `tests.test_human_output`: `test_selection_setter_help_points_to_install_and_remove` covers six help pages. `test_v2_selection_setters_refuse_and_point_to_install_and_remove`: exit 4, stderr names the code, install and remove, and the declaration, lock, `user.json` and `state.json` bytes are unchanged | Pass |
| Owner decision Q5 | Migration guide "Convert the machine"; the migration gate subsection of the CLI contract | Pass (documentation) |

- **What "historical" means in the documentation test.** RFC-MASK-0020 keeps historical RFCs and evidence unchanged, so these are exempt:
  - `docs/rfcs/`: retained packets, RFC text and plans;
  - `docs/issues/`: the card records of RFC work, including this closeout;
  - `docs/releases/`;
  - two named baseline evidence reports under `docs/development/`.
  Every other Markdown file, including `.mask/skill-config`, is current documentation.
- **Suite:** guarded per-module run with 4 workers: 49 of 49 modules, 438 tests, 16 skipped, 2439 s. HEAD, tree status and the owner profile snapshot were unchanged. Only Windows 11 was exercised (Python 3.14.6, Git 2.55.0.windows.3), and this was not the literal single-process run. The summary is `d6-suite/out/summary.json` in the d6 session scratchpad.
- **Other checks:**
  - The structure gate reports 0 violations.
  - A link and anchor check over the 23 current Markdown files found 0 problems.
  - Focused rerun after integration: `tests.test_retired_spellings`, `tests.test_tap_line_endings.PolicySurfaces` and `tests.test_human_output` ran 27 tests OK.
- **Integrator corrections to slice output:**
  - The `tap add` help and the state/recovery architecture said only publish and dev-link use the authoring checkout. `skill import` also requires it (`import.authoring_required`).
  - The state/recovery architecture overstated the previous program's `recovery.conflict` refusal; it now points to the contract's precise "Switching executables" text.
- **Review:** no independent review.
  - Under the risk policy this card changes presentation, documentation and a refusal message on an unchanged refusal path, with no persistence, protocol, authority or destructive change.
  - Both reviewer roles route to `claude-fable-5-1`, which hit its usage limit (d6-R1, HTTP 429), and no fallback is authorized.
- **Notes for later cards** (not acceptance scope):
  - **Tap-machine remediation:** a consumer-level `migration.required` on a tap machine names `mask doctor --migrate --dry-run`, which needs `--project PATH --alias NAME` there. The contract documents the full form. Left unchanged under Q5.
  - **Doctor network flag:** `capabilities` reports `doctor` `network: false`, but the tap-machine conversion can fetch. The contract says so.
  - **Previous programs:** the RFC rollout sentence is historical. `b92372f` cannot read a v3 configuration (`config.invalid`), and the previous tap-era program refuses a tap entry carrying `line_endings` (`source.invalid`). Neither recovers this program's `update` journal. The contract documents this.
  - **Qualifier (MASK-0104):** `scripts/qualify_real_package.py` still calls `project unrequire` (lines 315 and 331), which refuses on v2 declarations, as well as the retired `init --source` noted by d2.
  - **Help wrapping:** argparse still wraps option-help lines at hyphens.
- **Limitations:**
  - Only Windows 11 was exercised; macOS was not run.
  - The pty prompt case was skipped.
  - The documentation test checks spellings, not the rest of the documentation's accuracy.
  - Host loading is not verified.
