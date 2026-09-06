---
schema: "implement-rfc.card.v1"
id: "MASK-0036"
title: "Retarget owned links and recover lock/artifact transitions"
status: "In Progress"
rfcs: ["RFC-MASK-0008"]
depends_on: ["MASK-0035"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "artifact-reconcile", "stage": "B — reproducible content", "provisional_id": false}
---

# MASK-0036: Retarget owned links and recover lock/artifact transitions

Governing RFC: [RFC-MASK-0008](../../rfcs/RFC-MASK-0008-pinned-artifacts-and-recovery.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Replace the old-target-retention assumption with separately validated old/current/new targets. Derive journal paths from typed roles and old/new artifact records. Integrate lock/declaration/link changes in bounded recovery; preserve old journal readers and no-op semantics. Crash injection covers each meaningful write boundary and subsequent branch movement.

Own only: `mask_fs.py`, `mask_core.py:state`, `schemas/state-v3.schema.json (new)`, `schemas/pending-v3.schema.json`, `tests/test_pinned_recovery.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0008-AC04: Planner/executor/adoption/recovery correctly retarget an unchanged owned legacy or old-artifact link to a new artifact and preserve collisions, rather than retaining the old target.
- RFC-MASK-0008-AC05: Interruptions before/after lock, link and state effects preserve bounded v3 recovery; configuration/state migrations preserve exact legacy rollback bytes and reject concurrent edits.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_pinned_recovery tests.test_reconcile_apply tests.test_recovery

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.

## Bounded implementation plan

Extend the existing planner/executor/recovery engine, with a small versioned helper if needed. State v3 retains unrelated legacy records and adds explicit pinned mode, cached v2 selection/exact lock and validated resolution identities on owned links. Derive old/new artifact paths separately; preserve an old raw spelling only when equivalent to the desired new target. Never downgrade v3 while updating personal or launcher ownership. Historical state/journal readers remain strict.

Add bounded typed project/user declaration and lock file roles to journal v3, preserving exact before/after bytes and missing-file state. Bind roles to selected roots and recorded models; derive paths at runtime. Validate before/after link ownership and artifacts, preflight all recovery effects, reject concurrent control/root/branch edits and preserve collisions. Retain rollback artifacts. Machine-config and selected legacy-to-pinned migration are integrated by MASK-0037, using these same journal seams.

Extend ownership narrowly to a pinned model/orchestration helper, public dispatcher, resolver active-lock guard, readiness policy/observations, reporting guard, runtime inventory and affected schemas/docs/tests. Enable basic new v2 project/personal registration, plan/apply/ensure, adoption, doctor and unregister. Legacy consumer conversion stays explicit. Until RFC-0009, nontrivial per-binding targeting/conditions/restrictive metadata remain typed unsupported, while whole default/all selection is supported. Do not misreport pinned records as legacy inventory.

Prepare exact artifacts outside the consumer writer lock. Capture then revalidate exact declaration/lock/config/policy bytes, generations, roots and artifact identities after reacquiring it. Plan/check/dry-run remain observational and offline; cache effects do not change consumer intent identity. Ensure never resolves refs or rewrites a lock. Missing/stale locks block. Source/scope locked-fetch authority must be explicitly persisted and independently checked; integration approval alone does not grant network authority. Existing pure lock writes must not bypass a pinned consumer's journal; selected update routing follows MASK-0037.

Focused verification uses the public CLI for two independent worktree versions, project/user isolation, warm/offline restoration/noop, collision/adoption/doctor behavior and preserved legacy records. Inject interruption at intent/lock/link/state boundaries, complete and roll back exact bytes, reject tampered typed roles/artifacts and concurrent branch/control replacements. Verify preparation can acquire the writer lock itself (it is outside) and that changed generation/authority/control bytes then refuse activation. Run affected legacy recovery/readiness/launcher checks; native verification follows at the coherent pinned/targeting milestone.
