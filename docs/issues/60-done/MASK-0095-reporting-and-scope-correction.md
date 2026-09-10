---
schema: "implement-rfc.card.v1"
id: "MASK-0095"
title: "Report native role and scope states truthfully and select every consumer from ensure"
status: "Done"
rfcs: ["RFC-MASK-0019"]
depends_on: []
priority: "P2"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": false, "origin": "operator repair session on this repository, September 9-10, 2026"}
acceptance: [{"criterion":"RFC-MASK-0019-AC03","outcome":"pass","revision":"b64e1ec","evidence":{"kind":"observation","detail":"The portable lock was rebuilt from one transaction's outputs, so a partial publication recorded preserved destinations as deployed and dropped roles an earlier run had published; tests.test_setup caught the second effect when the first was fixed naively. mask_setup.vouchable derives the lock from the rechecked report instead. test_new_collision_during_staging_is_preserved_not_overwritten now asserts the lock names only the published role, that a rerun reports the preserved destination as setup_required with the unmanaged-file detail, and that the earlier published role stays vouched."}},{"criterion":"RFC-MASK-0019-AC03","outcome":"pass","revision":"b64e1ec","evidence":{"kind":"observation","detail":"A deleted managed role was released as 'changed outside MASK; it is preserved', wrong on both counts; both release sites in mask_workflow.requirements now distinguish deletion and mask_fs.released_message drops the false preservation claim. New test_deleted_managed_role_is_released_as_deleted_not_preserved covers it. A setup_required destination occupied by an unmanaged file said 'approved setup can produce it', which loops the operator because setup is what refuses to overwrite it; it now names the file and the removal."}},{"criterion":"RFC-MASK-0019-AC03","outcome":"pass","revision":"b64e1ec","evidence":{"kind":"observation","detail":"target.scope_shadowing warned on every user/project name overlap, including pairs resolving to one content-addressed directory where precedence cannot change what a host loads. Rows now carry same_target, every overlap stays in the shadowing inventory, and only a pair without it warns. tests.test_selection_conflicts covers both the same-target and the distinct-target case; the human line no longer promises warnings that will not follow."}},{"criterion":"RFC-MASK-0019-AC01","outcome":"pass","revision":"814d675","evidence":{"kind":"observation","detail":"ensure was the only scope-taking command without --user and --all, and the only command that runs package setup, so user-scope generated roles were reachable solely through --event startup; the workflow.incomplete remediation named 'mask ensure --user' while no such flag existed. Both flags now exist with the plan/apply/doctor/update conflict parity. New test_explicit_scope_selects_the_personal_consumer_or_every_consumer and test_all_scope_reaches_the_setup_proposal_like_an_explicit_project. On this machine mask ensure --all --check correctly refused on an unapproved registered project, and mask ensure --user cleared a registry record the personal consumer could never reach before (--check then exit 0, mask doctor --user healthy, all five user-scope links intact)."}},{"criterion":"RFC-MASK-0019-AC02","outcome":"pass","revision":"bb4e064","evidence":{"kind":"command","detail":"python3 -m unittest discover -s tests -t . on macOS 26.6.2: 349 tests, 4 skipped. The one standing failure was pre-existing and independently reproduced at clean HEAD c6431a1: tests.test_user_scope pinned readable state versions to [1, 2] and was never updated when state and pending moved to v3. It now asserts every declared write schema is among its readable versions, the property that would have caught the drift."}}]
---

# MASK-0095: Report native role and scope states truthfully and select every consumer from ensure

Governing RFC: [RFC-MASK-0019](../../rfcs/RFC-MASK-0019-complete-workflow-readiness.md).

## Objective and owned paths

`mask_setup.py`, `mask_workflow.py`, `mask_fs.py`, `mask_present.py`, `mask_core.py`,
`mask.py`, `mask_ensure.py`, their focused tests, and the affected CLI contract and
migration guidance.

## Bounded work

Correct four reporting defects and one missing scope selector found while repairing a
real consumer, without changing what MASK preserves or which files it will overwrite.
The lock must vouch for exactly the destinations that hold the expected bytes. A
preserved or deleted destination must be described accurately enough for an operator
to resolve it. A scope overlap that cannot change what a host loads must stay
observable without raising a warning. `ensure` must be able to name the personal
consumer and every consumer, and its remediation must name flags the command accepts.

## Acceptance

No reported state describes a file MASK did not write or a fix the operator cannot
perform. Preservation behavior, ownership records and consent surfaces are unchanged;
`--all` still requires each selected project's own readiness authority and still names
one exact setup action per skill and consumer. Host loading stays `not_verified`.

Criterion coverage: RFC-MASK-0019-AC01, RFC-MASK-0019-AC02, RFC-MASK-0019-AC03.

## Focused verification

Focused suites per change plus the full local suite; every claim rests on an exercised
command or an observed CLI result, never on reading the diff.

## Run record

Landed September 9-10, 2026 on macOS 26.6.2 across `b64e1ec` (reporting corrections),
`814d675` (ensure scope selection) and `bb4e064` (readable-schema assertion). The work
originated in an operator repair session on this repository rather than a planned
dispatch: `mask ensure` reported ten `implement-rfc` roles as modified against a lock
that had recorded bytes never published to them, which exposed the lock defect, the
misleading preserved and deleted role messages, the same-target shadowing noise and the
absent `ensure --user`/`--all`. The consumer itself was repaired through public commands
only. Open: host loading of deployed roles stays unverified; `--all` across many
consumers with declared setup is covered structurally by the grouped publication path
and by one proposal test, not by a multi-consumer setup fixture.
