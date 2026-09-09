---
schema: "implement-rfc.card.v1"
id: "MASK-0086"
title: "Deliver complete project and personal task commands"
status: "Done"
rfcs: ["RFC-MASK-0018"]
depends_on: ["MASK-0085"]
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": false, "packet_key": "complete-install-remove-list"}
acceptance: [{"criterion":"RFC-MASK-0018-AC01","outcome":"pass","revision":"681e26b","evidence":{"kind":"command","detail":"python3 -B -m unittest tests.test_task_commands tests.test_public_baseline (macOS): fresh project and fresh personal scope each need one install; v2 install/remove retain unrelated pins, overrides and the other scope; ambiguity refused with qualified choices"}},{"criterion":"RFC-MASK-0018-AC02","outcome":"pass","revision":"681e26b","evidence":{"kind":"command","detail":"tests.test_task_commands and tests.test_human_output: install/remove/list render text without --json; undeclared scope gets deliberate empty text; errors on stderr"}},{"criterion":"RFC-MASK-0018-AC06","outcome":"pass","revision":"681e26b","evidence":{"kind":"command","detail":"tests.test_task_commands: remove over an edited leaf refuses with target.collision, preserves the file and lock row; dry run of a fresh scope writes nothing; pending journal refuses with recovery.required"}}]
---

# MASK-0086: Deliver complete project and personal task commands

Governing RFC: [RFC-MASK-0018](../../rfcs/RFC-MASK-0018-task-oriented-cli-and-human-output.md). Live IDs confirmed by the committed pack reservation `6d80121`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-ux-readiness.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-ux-readiness/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-ux-readiness/ACCEPTANCE.md).

## Objective and owned paths

mask.py command registration, mask_core/mask_fs/mask_pinned/mask_resolve selection/planning seams as needed, minimal mask_report pinned views, focused public tests.

## Bounded work

Implement install/remove/list as complete services rather than sequential CLI shellouts. Fold missing declaration/registration, scoped membership edit, new-binding resolution, preparation, engine activation and checks into the task. Handle legacy and pinned paths explicitly, retain unrelated exact pins/targets, and preserve checked-in context and other-scope selections. Limit report work to basic accurate list/inventory; do not wait for full impact reporting.

## Acceptance

A fresh project and first personal selection each need one task command after one-time source setup. A v2 add/remove does not hit the legacy selection.command_unsupported branch. Tests exercise source ambiguity, effective per-binding targeting, no-op reinstall, removal with edited files, and other-scope independence through actual subprocesses.

Criterion coverage: RFC-MASK-0018-AC01, RFC-MASK-0018-AC02, RFC-MASK-0018-AC06.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary. Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation, and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Implemented at `681e26b` (macOS, Python 3.14, direct CLI subprocesses via
`tests/public_support.py`; no `--json` injection, no pre-registration).

- `mask_task.py`: `install`/`remove` build one proposal (declaration, and lock
  for v2) and activate one frozen plan through `mask_fs.plan`/`execute`; `list`
  reads the same plan. Missing declaration/registration are created in the same
  operation (fresh v2 scopes also get an empty lock before planning; both files
  are removed again unless the task commits). Journal allowlist and the user
  state-schema upgrade rule accept `install`/`remove`.
- Focused checks: `python3 -B -m unittest tests.test_task_commands
  tests.test_public_baseline tests.test_human_output tests.test_cli_protocol`
  pass (baseline `expectedFailure` decorators for C01/C02 removed). Full suite:
  295 tests, only the known unrelated `tests.test_user_scope` failure.
- Structure gate `python3 scripts/verify_documentation.py --root .`: 0 violations.
- Limitations recorded on MASK-0093: dry-run of a fresh scope computes no plan;
  a legacy `--agent` differing from the declaration is refused; `remove` on an
  unregistered scope is refused; `merge_preparation` still labels retained
  store artifacts after a refused v2 task as `partial`; native Windows lane open.
