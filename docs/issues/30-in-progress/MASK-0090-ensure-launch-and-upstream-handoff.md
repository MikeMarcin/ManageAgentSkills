---
schema: "implement-rfc.card.v1"
id: "MASK-0090"
title: "Connect complete readiness to every public entrypoint"
status: "In Progress"
rfcs: ["RFC-MASK-0019"]
depends_on: ["MASK-0086", "MASK-0087", "MASK-0089"]
external_depends_on: ["AgentSkills:ASK-0059"]
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": false, "packet_key": "ensure-launch-and-upstream-handoff"}
---

# MASK-0090: Connect complete readiness to every public entrypoint

Governing RFC: [RFC-MASK-0019](../../rfcs/RFC-MASK-0019-complete-workflow-readiness.md). Live IDs confirmed by the committed pack reservation `6d80121`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-ux-readiness.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-ux-readiness/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-ux-readiness/ACCEPTANCE.md).

## Objective and owned paths

mask_ensure.py, install/update/doctor/prelaunch final status, typed workflow readiness reporting, current MASK instructions, and the recorded AgentSkills integration handoff.

## Bounded work

Share one prerequisite evaluation between ensure, install/update completion, doctor checks and launch. Preserve cheap inventory as observational. Consume the explicitly authorized upstream contract/asset/staging handoff; update the local dependency record with its actual ASK card and commit when available. Do not edit the shared source through a symlink or pretend the current renderer already stages outputs.

## Acceptance

Public commands cannot report complete success with required roles missing. Launch does not start a host when setup is blocked; warning-only hooks remain labelled. The real selected AgentSkills package, explicit routing/addenda and current role names are used. Configured route and host observation stay separate. Until the upstream handoff exists, this card remains open.

Criterion coverage: RFC-MASK-0019-AC01, RFC-MASK-0019-AC06, RFC-MASK-0019-AC08.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary. Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation, and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

MASK-side engineering landed September 9, 2026 inside integrated outcome M7
(dispatch D8, mandate revision 2) at `3bbac77` (rfc-worker, claude-fable-5-1,
effort high; integrated and committed by the integrator). `mask_ensure.final_status`
is the one prerequisite verdict: `ensure`, `install`/`remove` (`mask_task`),
legacy and pinned `update` (`mask_git`, `mask_pinned`) call it after their
committed transaction and exit 4 `workflow.incomplete` naming the unmet
role/input (links stay committed, phases truthful, no package code runs; setup
consent stays on `ensure` and the remediation says so); `doctor` shares
`mask_ensure.observe` (issue `workflow.incomplete`, `--check` exit 7
`state.drift` with `details.workflow`); `launch` goes through `ensure --event
startup` and never starts the host when a role is missing (fake host sentinel
never written); the Claude startup hook labels itself warning-only; the update
planner evaluates roles from the frozen candidate bytes
(`PackageView(files=...)`) so an upstream role addition/rename is planned from
the selected candidate (unchanged managed file under the retired name retired,
edited one preserved and released); `mask capabilities` advertises
`workflow=dict(readiness='workflow_readiness_v1', native_roles=True,
staged_setup=True, entrypoints=[...], host_load='not_verified')`. Behaviour
change: `install` on a consumer lacking implement-rfc's declared inputs now
exits 4 with the link committed (README/guides and two tests updated).
Verified (macOS): `python3 -B -m unittest tests.test_workflow_roles
tests.test_setup tests.test_task_commands tests.test_update_task
tests.test_host_integration tests.test_human_output tests.test_ensure
tests.test_public_baseline tests.test_readiness_entrypoints
tests.test_readme_journeys` (97 tests, OK); structure gate 0 violations.
Full discovery at `3bbac77`: 343 tests, 4 skipped, 1 failure = the known
pre-existing `tests.test_user_scope.test_scope_selection_and_parser`.

At `3bbac77` the upstream handoff did not exist (AgentSkills `2e45a4e` shipped
no descriptor, preflight or staging entrypoint), so this card was Blocked
(`agentskills-handoff`) without an invented ASK ID. The MASK side consumes any
conforming descriptor (static assets, checked-in lock or declared setup) without
a renderer or repository-name exception. Limitations: `list`/`inventory` stay
observational (`unexamined`); `doctor` for a pinned consumer without a local
package directory counts `unexamined` as incomplete.

Upstream handoff (recorded September 9, 2026, dispatch D11, mandate revision 3;
the user authorized the AgentSkills work separately): `external_depends_on`
`AgentSkills:ASK-0059`, Done in that repository at completion commit
`154025bdd374a448a0aaa9742703d6459d64be2e` ("Finish ASK-0059"; implementation
commits `4bd053c`, `0f8b3cd`; governing RFC `RFC-ASK-0011`, Auto-Verified there).
It ships `skills/implement-rfc/mask-workflow.json` (sha256
`9575dc4fa8a69900236bd8d68634fdca5759124d91acf3cf8c22c6e83e4d70f1`; 16 generated
roles = the 8 current roles x codex/claude, setup action `prepare-roles`,
entrypoint `scripts/prepare_mask_roles.py`, required inputs `project-config` and
`project-rules`, optional `execution-selection`), the startup preflight
`scripts/workflow_preflight.py`, and `generate_roles` in
`render_runtime_adapters.py`. Local handoff check (macOS, this MASK as a
subprocess, private `MASK_HOME`/`HOME`, disposable clone of AgentSkills at
`154025b` as the source, disposable consumer with real `project.json`/
`project.md`): `skill validate implement-rfc` valid with fingerprint
`sha256:7ff27a61692d396346221f8d14e7f0618a39618f446be8df01cc26b215ebc116`; first
`ensure` exit 4 `workflow.incomplete` with all 16 roles `setup_required`, links
committed, no role files and no package code run; `doctor --check` exit 7;
`launch --agent codex|claude` exit 4 with a fake host on PATH never started;
upstream `workflow_preflight.py --mask mask.py` reports `incomplete` with 16
blockers before setup and `ready` (`host_load: not_verified`) after the
consented setup. Real-package journeys continue on MASK-0092. Inherited upstream
limitations: no Windows/Linux lane there, no fresh-host loading evidence
(`host_load=not_verified`), local review only, staged setup is ordinary user
process execution.
