---
schema: "implement-rfc.card.v1"
id: "MASK-0088"
title: "Check and deploy declared native roles without rendering"
status: "Done"
rfcs: ["RFC-MASK-0019"]
depends_on: ["MASK-0083"]
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": false, "packet_key": "declarative-native-role-artifacts"}
acceptance: [{"criterion":"RFC-MASK-0019-AC01","outcome":"pass","revision":"bc90418cc4f97f3e62c1eeef80815fe769ccef44","evidence":{"kind":"command","detail":"python3 -B -m unittest tests.test_workflow_roles tests.test_public_baseline (macOS, subprocess CLI, synthetic pack fixtures in disposable roots): ensure --check with rfc-integrator absent is nonzero and names the role; ensure never reports ready while a declared role or required input is missing/modified; unavailable payload bytes report unexamined. Ensure boundary only; install/update final status, doctor --check and launch gating stay with MASK-0090"}},{"criterion":"RFC-MASK-0019-AC02","outcome":"pass","revision":"bc90418cc4f97f3e62c1eeef80815fe769ccef44","evidence":{"kind":"command","detail":"python3 -B -m unittest tests.test_workflow_roles tests.test_public_baseline (macOS, subprocess CLI, synthetic pack fixtures in disposable roots): static assets deploy as exact bytes with no generator, script or prompt; fresh clone with tracked role files passes as repository-owned with tracked bytes/index unchanged and no local manifest; generated variant passes only through a coherent native-roles.lock.json; no package code executed"}},{"criterion":"RFC-MASK-0019-AC03","outcome":"pass","revision":"bc90418cc4f97f3e62c1eeef80815fe769ccef44","evidence":{"kind":"command","detail":"python3 -B -m unittest tests.test_workflow_roles tests.test_public_baseline (macOS, subprocess CLI, synthetic pack fixtures in disposable roots): adapter-derived destinations, pending.native_roles journal with rollback/complete/conflict; modified, unknown, colliding, linked-parent and repository-owned files preserved; checked-in files neither adopted nor deleted; unchanged managed outputs retired and edited ones released with a warning"}},{"criterion":"RFC-MASK-0019-AC06","outcome":"pass","revision":"bc90418cc4f97f3e62c1eeef80815fe769ccef44","evidence":{"kind":"command","detail":"python3 -B -m unittest tests.test_workflow_roles tests.test_public_baseline (macOS, subprocess CLI, synthetic pack fixtures in disposable roots): targets [codex] leaves Claude roles not_applicable with no .claude directory; missing rfc-integrator explicit; native name drift refused as workflow.role_invalid; configured route reported per role separately from host_load not_verified; integration pass over compatibility/pinned-recovery/selection-conflicts/ensure/human-output/recovery/task-command/consent/adapters/launcher suites and the full unit suite (known pre-existing test_user_scope failure excluded)"}}]
---

# MASK-0088: Check and deploy declared native roles without rendering

Governing RFC: [RFC-MASK-0019](../../rfcs/RFC-MASK-0019-complete-workflow-readiness.md). Live IDs confirmed by the committed pack reservation `6d80121`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-ux-readiness.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-ux-readiness/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-ux-readiness/ACCEPTANCE.md).

## Objective and owned paths

mask_packages.py passive workflow descriptor validation, mask_adapters.py typed role destinations, mask_fs/mask_pinned typed outputs and recovery schema, focused role fixtures.

## Bounded work

Implement the minimal descriptor, static asset validation and required consumer-input observation. Support already committed role files and portable locks without prior local renderer ownership. Publish absent/unchanged managed role files via the existing engine. Keep repository-owned files separate and preserve package hazard guards; add only the narrow explicit native-role artifact kind.

## Acceptance

Static package roles and valid consumer-checked-in roles pass on a fresh clone with zero script calls. Missing rfc-integrator, changed inputs, stale locks, invalid role content and wrong targets fail complete readiness. Unknown/edited/tracked files, linked parents, role collisions and foreign ownership are preserved; unrelated source docs do not cause regeneration.

Criterion coverage: RFC-MASK-0019-AC01, RFC-MASK-0019-AC02, RFC-MASK-0019-AC03, RFC-MASK-0019-AC06.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary. Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation, and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Implemented on macOS (darwin, Python 3.14.7) against disposable sources, consumers
and a private `MASK_HOME`; the pack's synthetic packages (`fixture-model-do-not-run`)
were never installed into a real host. Baseline for this card: `6697041` (claim).

Delivered: `mask_workflow.py` (passive `mask-workflow.json` validation with the
pack's v1 shape and bounds, exact static asset verification, passive native field
parsing for Codex TOML / Claude frontmatter with a supported-field allowlist and
declared-name check, consumer input observation, portable
`.mask/skill-config/<skill>/native-roles.lock.json` reading, destination
observation and ownership resolution); `mask_adapters.role_relative` (typed
destinations `.codex/agents/<name>.toml`, `.claude/agents/<name>.md`);
`mask_fs.plan` derives required roles from each root's selected bindings (legacy
source checkout, materialized store or the in-memory payload view) and plans
`native_role.write`/`native_role.remove` through the same journal (`pending.native_roles`,
schema v3, preflight/rollback/complete, checkpoint `native_role`); `state` records
carry `native_roles` ownership; `ensure` reports `workflow_readiness`, per-scope
`workflow`, exits 7 (`readiness.drift`, roles named) when the package can supply
what is missing and 4 (`workflow.incomplete`) when preserved files or inputs keep
readiness incomplete, with links still committed and reported; human renderer
lists roles and inputs; schemas extended; `mask_install.validate_program` and the
launcher fixture list the new module.

Focused verification (subprocess CLI):
`python3 -B -m unittest tests.test_workflow_roles tests.test_public_baseline`
(W01 `ensure --check` names `rfc-integrator` and is nonzero; W02 exact asset bytes
deployed, older `rfc-worker` bytes preserved, rerun script-free/no-op; W03 fresh
clone with tracked roles passes as repository-owned with tracked bytes/index
unchanged and no ownership record, and `unrequire` keeps them; W03/W04 generated
variant accepted only through a coherent lock, invalidated by a relevant input
change, an edited output or a missing lock, with nothing overwritten or executed;
W05 unrelated README edit changes nothing; targets `codex` only -> Claude roles
`not_applicable`, no `.claude` directory; asset hash drift -> `workflow.invalid`;
unsupported `[hooks]` table and declared-name drift -> `workflow.role_invalid`;
two skills with different bytes for one role -> `collision`, nothing written;
crash at `native_role` -> rollback removes writes, complete refuses a replaced
file and finishes otherwise; unrequire retires unchanged managed roles and
releases an edited one with `native_role.released`). Plus `tests.test_ensure`,
`tests.test_recovery`, `tests.test_task_commands`, `tests.test_human_output`,
`tests.test_consent`, `tests.test_adapters`, `tests.test_launcher` and the full
unit suite (known pre-existing failure `tests.test_user_scope.test_scope_selection_and_parser`
excluded from judgment).

Decided: `apply`/`install`/`update`/`remove` deploy or retire declared static roles
with the links (same engine), but only `ensure` fails on incomplete workflow
readiness until MASK-0090 wires final status into the other entrypoints.
Modified, unknown, tracked or colliding destinations are never overwritten;
the explicit manual overwrite approval for tracked edits (W04 second half) is
deferred to the consent work of MASK-0089/0090. Approved setup, `doctor --check`,
`launch` gating, capability advertisement (`workflow_readiness_v1`) and the real
AgentSkills package/native lanes remain open (MASK-0089/0090/0092).
