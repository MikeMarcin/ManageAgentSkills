---
schema: "implement-rfc.card.v1"
id: "MASK-0084"
title: "Implement real human output and actionable errors"
status: "Done"
rfcs: ["RFC-MASK-0018"]
depends_on: ["MASK-0083"]
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": false, "packet_key": "human-output-for-all-commands"}
acceptance: [{"criterion":"RFC-MASK-0018-AC02","outcome":"pass","revision":"bc579976a289eb65cff1dee7224e36ba3752c8c5","evidence":{"kind":"command","detail":"python3 -B -m unittest tests.test_human_output tests.test_public_baseline: HumanOutputBaseline passes without expectedFailure; inventory renders 3 skill rows / 6 links with CODEX and CLAUDE states, partial page names --offset, `mask` alone prints everyday help exit 0, `mask --version` prints `mask 0.2.0`, capabilities/skill list/project list/show/config show/self status/plan/doctor/recover render text; RENDERERS covers all 64 registered commands (registry coverage test)."}},{"criterion":"RFC-MASK-0018-AC03","outcome":"pass","revision":"bc579976a289eb65cff1dee7224e36ba3752c8c5","evidence":{"kind":"command","detail":"Same run: --json remains one sorted document on stdout with empty stderr for success and handled errors (project.not_registered exit 4 in both formats); `skill show -- --json` treats the operand as data (stdout empty, error on stderr); dry-run/apply effects identical between human and machine invocations; tests.test_cli_protocol unchanged and passing."}}]
---

# MASK-0084: Implement real human output and actionable errors

Governing RFC: [RFC-MASK-0018](../../rfcs/RFC-MASK-0018-task-oriented-cli-and-human-output.md). Live IDs confirmed by the committed pack reservation `6d80121`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-ux-readiness.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-ux-readiness/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-ux-readiness/ACCEPTANCE.md).

## Objective and owned paths

mask.py output selection/help/version, a shared presentation module, tests/support.py and focused CLI/inventory fixtures. Do not move engine decisions into presentation.

## Bounded work

Keep one result object and add summary/table/change/error renderers. Cover every current command via the registration table; remove indented-JSON fallback. Preserve machine output, normalize readable error/remediation output, and fix no-argument help. Add human/terminal tests independent of Fixture.call that appends --json.

## Acceptance

The six-row inventory is rendered as three skill rows with separate agent states; paginated/conflicting/pinned/empty/unavailable cases are honest. No command returns raw envelope JSON by default, including version and rare commands. Redirected output stays text; JSON remains one parseable document and no terminal decoration contaminates it.

Criterion coverage: RFC-MASK-0018-AC02, RFC-MASK-0018-AC03.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary. Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation, and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Implemented at `bc579976a289eb65cff1dee7224e36ba3752c8c5` (run mask-corrective-ux-readiness, dispatch D2). `mask_present.py`
renders every registered command from the result object (`RENDERERS` coverage
table); `mask.py::main` writes text via the renderer and errors via
`render_error` to stderr; `mask` alone prints everyday help (exit 0);
`--version` prints a version line; `mask GROUP` names its subcommands (exit 2);
`mask_core.REMEDIATION` supplies per-code next steps. `mask_install.validate_program`
and the launcher fixture require the new module.

Focused verification (macOS, Python 3.14.7): `python3 -B -m unittest
tests.test_human_output tests.test_public_baseline tests.test_cli_protocol
tests.test_launcher` — OK; the three `HumanOutputBaseline` decorators are removed
and pass. Full suite: 274 tests, one pre-existing unrelated failure
(`tests.test_user_scope` readable state versions `[1, 2, 3]`, reproduced at
`541b34c` before this card). Structure gate: 0 violations. Not asserted: native
Windows console rendering, terminal prompts, host loading (RFC-MASK-0018-AC08).
