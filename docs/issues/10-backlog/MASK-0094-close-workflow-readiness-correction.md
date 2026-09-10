---
schema: "implement-rfc.card.v1"
id: "MASK-0094"
title: "Verify and close complete workflow readiness"
status: "Backlog"
rfcs: ["RFC-MASK-0019"]
depends_on: ["MASK-0092"]
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": false, "packet_key": "close-workflow-readiness-correction"}
closeout_for: ["RFC-MASK-0019"]
---

# MASK-0094: Verify and close complete workflow readiness

Governing RFC: [RFC-MASK-0019](../../rfcs/RFC-MASK-0019-complete-workflow-readiness.md). Live IDs confirmed by the committed pack reservation `6d80121`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-ux-readiness.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-ux-readiness/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-ux-readiness/ACCEPTANCE.md).

## Objective and owned paths

This RFC, its closeout, current affected docs and exact upstream/native evidence references only.

## Bounded work

Reconcile all RFC-MASK-0019 criteria, including the real AgentSkills handoff and the public fresh-consumer/missing-role cases. Confirm no setup/recovery path silently executes unapproved code, retries uncertain actions, rewrites tracked files, or claims loaded roles from configuration alone.

## Acceptance

Every criterion has direct actual evidence and an implementation revision; every linked required card is Done. A fixture package, source-only validator or successful symlink operation cannot substitute for the real workflow journey. Unavailable upstream/native acceptance remains open.

Criterion coverage: RFC-MASK-0019-AC01, RFC-MASK-0019-AC02, RFC-MASK-0019-AC03, RFC-MASK-0019-AC04, RFC-MASK-0019-AC05, RFC-MASK-0019-AC06, RFC-MASK-0019-AC07, RFC-MASK-0019-AC08.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary. Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation, and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Not started. Claim the live remapped card before edits. No code implementation,
native result, host loading, user approval, or quota improvement is asserted.

## Durable closeout anchor

RFC_BASE_SHA: 6d80121b1c870f1be7864e8bc9db2b02a0e41c2d

Planned cards: MASK-0083, MASK-0088, MASK-0089, MASK-0090, MASK-0092.

| Acceptance | Direct check / observation | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0019-AC01 | `python3 -B -m unittest tests.test_workflow_roles tests.test_public_baseline` (macOS, subprocess CLI, synthetic static/generated packages, disposable consumers): with correct links and `rfc-integrator` absent, `ensure --check` is nonzero and names the role (exit 7 `readiness.drift` when the package can supply it, exit 4 `workflow.incomplete` when only preserved/unlocked roles remain); `ensure` never reports `ready_legacy_unpinned` while a declared role or required input is missing/modified; plain skills report `workflow: not_declared`; unavailable payload bytes report `unexamined`, never complete (MASK-0088). Install/update final status, `doctor --check` and prelaunch gating are not wired yet (MASK-0090) | Pass at card boundary for ensure; other entrypoints open | `bc90418cc4f97f3e62c1eeef80815fe769ccef44` |
| RFC-MASK-0019-AC02 | Same run: static package assets deploy as exact bytes with no generator, script or prompt; a fresh Git clone with tracked correct role files (no lock, no local renderer manifest) passes as `repository-owned` with tracked bytes/index unchanged; the generated variant passes only through a coherent `native-roles.lock.json` (descriptor digest, input digests, output hashes) and no `__pycache__` or script execution occurs (MASK-0088) | Pass at card boundary; real AgentSkills package not exercised | `bc90418cc4f97f3e62c1eeef80815fe769ccef44` |
| RFC-MASK-0019-AC03 | Same run: destinations come from `mask_adapters.role_relative` (`.codex/agents/<name>.toml`, `.claude/agents/<name>.md`), written through `pending.native_roles` (v3 journal, rollback/complete, `recovery.conflict` on a replaced file); modified/unknown files, linked parents (`target.parent_link`), a collision between two skills and repository-owned files are preserved and reported; valid checked-in files are neither adopted (no ownership record) nor deleted on `unrequire`; unchanged managed outputs are retired, an edited one is released with `native_role.released` (MASK-0088) | Pass at card boundary; explicit manual overwrite approval for tracked edits deferred to MASK-0089/0090 | `bc90418cc4f97f3e62c1eeef80815fe769ccef44` |
| RFC-MASK-0019-AC04 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0019-AC05 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0019-AC06 | Same run: requirements follow each binding's effective agents (`targets: [codex]` -> Claude roles `not_applicable`, no `.claude` directory) and physical scope; missing `rfc-integrator` is explicit; a role whose native `name` differs from the declared role (`rfc-critical-integrator`) is refused as `workflow.role_invalid`; the configured route (`model`, effort fields) is reported per role separately from `host_load: not_verified` (MASK-0088). Selected-candidate recomputation on `update` shares the planner but is not separately exercised | Pass at card boundary; update-path recheck and consumer profile/override semantics open (MASK-0089/0090) | `bc90418cc4f97f3e62c1eeef80815fe769ccef44` |
| RFC-MASK-0019-AC07 | Baseline uses the synthetic static package only; real package and native lanes not exercised (MASK-0083) | Not run | Not recorded |
| RFC-MASK-0019-AC08 | Pending actual implementation evidence | Not run | Not recorded |

Closeout review runtime: Not recorded. Required native/upstream boundaries remain
open until their actual evidence is linked. Do not invent a PASS to close the board.

## Current continuation

See the corrective-pack continuation on [MASK-0093](../60-done/MASK-0093-close-human-cli-correction.md). Upstream AgentSkills handoff: no card or integration commit exists yet; MASK-0090 remains open until it does.
