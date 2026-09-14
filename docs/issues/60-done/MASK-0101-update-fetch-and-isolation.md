---
schema: "implement-rfc.card.v1"
id: "MASK-0101"
title: "Fetch every referenced tap and update all consumers in one journal"
status: "Done"
rfcs: ["RFC-MASK-0020"]
depends_on: ["MASK-0099"]
priority: "P1"
metadata: {"packet":"mask-corrective-managed-taps","provisional_id":false,"packet_key":"update-fetch-and-isolation","milestone_plan":{"id":"tap-only-deployment","path":"docs/rfcs/plans/tap-only-deployment/milestone-plan.json"}}
acceptance: [{"criterion":"MASK-0101 AC1 (engine:exit:3; RFC-MASK-0020-AC03 fixture evidence): with two taps and three consumers, an upstream push followed by mask update fetches each tap exactly once (fixture counts Git invocations), updates the affected consumers in one journal and leaves the untouched consumer's lock byte-identical","outcome":"pass","revision":"a62f7c482229c0964ff0f14b30753633f7c6e74e","evidence":{"kind":"command","detail":"tests.test_update on a62f7c4 (Windows 11 Home 10.0.26200, Python 3.14.6, Git 2.55.0.windows.3): 17 tests OK. The fixture has two local bare taps and three consumers created through install: a project and the personal scope on agentskills, and a second project on second. git fetch processes are counted from Git trace2 event files, with no product instrumentation. test_u01_push_then_update_fetches_each_tap_once_and_isolates_the_other_tap: after a push to agentskills, update fetches {agentskills: 1, second: 1}. The statuses are updated, updated and unchanged, each updated consumer gets change rows with before and after commits and digests, the second tap's consumer lock stays byte-identical with its link unchanged, every link resolves under MASK_HOME/store/v1, and a rerun is a no-op. test_u01_one_journal_activates_every_updated_consumer: a crash at the intent checkpoint leaves one pending journal with operation update, selecting all three consumers, with typed lock files for the two updated consumers; recover --complete finishes. Negative control: at be64043 the module has 10 failures and 1 error in 11 tests; U01 counted {0,0} fetches and the lock never moved."}},{"criterion":"MASK-0101 AC2 (RFC-MASK-0020-AC03): renaming one bare repository away blocks only its consumers and exits 4 update.incomplete","outcome":"pass","revision":"a62f7c482229c0964ff0f14b30753633f7c6e74e","evidence":{"kind":"command","detail":"tests.test_update test_u02_unreachable_tap_blocks_only_its_consumers: with the second tap's bare repository renamed away, the two agentskills consumers update, the second tap's consumer is blocked with git.failed, and update exits 4 update.incomplete with details.blocked naming that root and a committed transaction. Its lock and link are unchanged, and human output names the blocked root and the failed fetch. test_u03_scoped_update_on_an_unreachable_tap_is_a_plain_refusal: update --project on that consumer exits 5 git.failed with nothing written and no fetch of the healthy tap. UpdateSafetyOnTaps test_blocked_consumer_keeps_update_incomplete_beside_incomplete_workflow_roles: with a generated-role package also incomplete, the command still ends update.incomplete with details.blocked and the workflow details (fixed in a62f7c4; the test fails at 07848a5)."}},{"criterion":"MASK-0101 AC3 (RFC-MASK-0020-AC03): --dry-run, --offline and a guarded rerun perform no fetch","outcome":"pass","revision":"a62f7c482229c0964ff0f14b30753633f7c6e74e","evidence":{"kind":"command","detail":"tests.test_update test_u04_dry_run_and_offline_never_fetch_and_block_a_cold_selector: update --dry-run and update --offline count zero fetches, leave the snapshot unchanged and mark the tag-pinned consumer blocked with requires_fetch; offline ends update.incomplete; a plain update then fetches once per tap and applies. test_u04_guarded_rerun_never_fetches_and_binds_the_reviewed_candidate: a guarded rerun after a newer fetch refuses plan.stale with zero fetches; a guarded rerun of a reviewed plan applies the reviewed commit with zero fetches, even after a further unfetched push. test_update_task PreviewAndGuard (2 tests) repeats this through the human journey. The critical review's reproducer confirmed that a dry run followed by a guarded rerun does zero fetches and applies the reviewed candidate."}},{"criterion":"MASK-0101 AC4 (RFC-MASK-0020-AC03): a moved tag refuses without --allow-ref-rebind","outcome":"pass","revision":"a62f7c482229c0964ff0f14b30753633f7c6e74e","evidence":{"kind":"command","detail":"tests.test_update test_u05_moved_tag_refuses_the_whole_invocation_without_allow_ref_rebind: a consumer pinned to annotated tag release resolves through the single update fetch, with no source inspect needed. After the tag is force-moved upstream, update fetches once and refuses lock.ref_rebound naming the coordinate, with transaction not_started and every consumer's lock byte-identical. update --allow-ref-rebind then applies the moved tag."}},{"criterion":"MASK-0101 bounded work: fetch-once algorithm, per-tap failure capture, isolation of blocked consumers, cache resolution, per-consumer disclosure, one journal, update.incomplete, source fetch without a name fetches every approved tap, scope.expand consent retired","outcome":"pass","revision":"a62f7c482229c0964ff0f14b30753633f7c6e74e","evidence":{"kind":"command","detail":"mask_update.py (d61d4be, a62f7c4) implements contracts/CLI.md update semantics 1-9. test_u06: an empty registry exits 0 with project.empty_registry and no fetch. test_u07: a dev-link consumer is skipped with dev_link.active by the unscoped form and by --all, and refused by --project. test_u08: source fetch without a name fetches every approved tap once and deploys nothing; a failed tap is reported while the others are fetched. test_skill_scope_fetches_only_the_taps_of_the_named_bindings. UpdateSafetyOnTaps: a removed declared skill refuses without writing; an unsafe package refuses; Git hooks are suppressed during the fetch; a late apply failure rolls back to exact prior bytes; an unavailable consumer refuses before any fetch. The scope.expand consent kind is removed from mask_consent. Porting test_update_task, test_readme_journeys and test_readiness_entrypoints to taps shows the human journeys and native-role conversion on update."}},{"criterion":"MASK-0101: the full suite passes","outcome":"pass","revision":"a62f7c482229c0964ff0f14b30753633f7c6e74e","evidence":{"kind":"command","detail":"Guarded per-module run on a62f7c4: 45 of 45 modules OK, 386 tests, 16 skipped, with MASK_HOME, USERPROFILE and HOME redirected per module. HEAD, tree 31280ec and an empty git status were identical before and after. The literal single-process command python -B -m unittest on a62f7c4, with MASK_HOME, USERPROFILE and HOME redirected to empty directories, finished exit 0: Ran 386 tests in 8694 s, OK (skipped=16). HEAD and a hash guard over the product, schema, test and script files were identical before and after. macOS was not exercised."}},{"criterion":"Independent critical review of the update module adjudicated","outcome":"pass","revision":"a62f7c482229c0964ff0f14b30753633f7c6e74e","evidence":{"kind":"observation","detail":"rfc-reviewer-critical, route claude-fable-5-1 at high effort, reviewed mask_update at d61d4be and found no blocking finding. It confirmed one fetch for an annotated tag pre-frozen by source inspect, refs/mask/frozen retaining the peeled commit with no leftover acquiring refs, a branch selector on another ref leaving refs/mask/selected unmoved, and dry-run followed by a guarded rerun doing zero fetches. Contract notes recorded: the update journal keeps operation update, so the previous program 0658a40 completes a crashed tap-fetching update journal with the same outcome instead of refusing it as the rollout sentence states; the fetch phase holds the writer lock for the network round; a resolution error other than lock.resolution_required or lock.ref_rebound refuses the whole invocation, as CLI.md step 6 states."}}]
---

# MASK-0101: Fetch every referenced tap and update all consumers in one journal

Governing RFC: [RFC-MASK-0020](../../rfcs/RFC-MASK-0020-tap-only-deployment.md). Live IDs confirmed by the committed pack reservation `b92372f`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-managed-taps.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-managed-taps/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-managed-taps/ACCEPTANCE.md).

## Objective and owned paths

`mask_update.py` (new), the `update` and `source fetch` dispatch lines in `mask.py`, `tests/test_update.py` (new) and `tests/test_pinned_update.py`. Do not edit the planner, the journal or the fixture bases in this card.

## Bounded work

Implement the update algorithm from `contracts/CLI.md`: select consumers, compute referenced taps, fetch each once unless `--dry-run`, `--offline` or `--expect-plan-hash`, capture per-tap failures, block only the consumers that reference a failed tap, resolve the rest from cache, refuse rebound selectors without `--allow-ref-rebind`, disclose per-consumer diffs, apply through one journal and end `update.incomplete` when any consumer stayed blocked. Make `source fetch` without a name fetch every approved tap. Retire the shared-checkout `scope.expand` consent.

## Acceptance

With two taps and three consumers, an upstream push followed by `mask update` fetches each tap exactly once (fixture counts Git invocations), updates the affected consumers in one journal and leaves the untouched consumer's lock byte-identical. Renaming one bare repository away blocks only its consumers and exits 4 `update.incomplete`. `--dry-run`, `--offline` and a guarded rerun perform no fetch. A moved tag refuses without `--allow-ref-rebind`.

Criterion coverage: RFC-MASK-0020-AC03.

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

Dispatch `d3` of run `mask-rfc0020-2026-09-12-a`, milestone `engine`.
- Claim `66fb4e2`; implementation integrated at `d61d4be`; tests ported and corrected through `a62f7c4`.
- The heading above ends the bound Acceptance text.

### Acceptance evidence
`tests.test_update` runs through the subprocess CLI against two local bare taps and three consumers, one of them personal. `git fetch` processes are counted from Git trace2 event files.
- **Push then update:**
  - `test_u01_push_then_update_fetches_each_tap_once_and_isolates_the_other_tap`: fetch counts `{1, 1}`; statuses updated, updated, unchanged, with per-consumer change rows; the untouched tap's consumer lock is byte-identical; all links stay in the store.
  - `test_u01_one_journal_activates_every_updated_consumer`: a crash at `intent` leaves one `update` journal selecting all three consumers, with typed lock files for the two that changed; `recover --complete` finishes.
- **Unreachable tap:**
  - `test_u02`: with one bare repository renamed away, its consumer is blocked with `git.failed`, the others update, and the command exits 4 `update.incomplete` with a committed transaction.
  - `test_u03`: a scoped update on that tap is a plain refusal, exit 5, with nothing written.
- **No fetch in guarded modes:**
  - `test_u04` (two tests): `--dry-run`, `--offline` and a guarded rerun perform no fetch.
  - A cold selector is blocked with `requires_fetch`.
  - The guard binds the reviewed candidate, or refuses `plan.stale` after the cache moves.
- **Moved tag:** `test_u05`. `lock.ref_rebound` refuses the whole invocation with every lock unchanged; `--allow-ref-rebind` applies; the annotated tag object arrives in the single fetch.
- **Negative control:** at `be64043`, 10 failures and 1 error in 11 tests.
- **Bounded work:**
  - `test_u06`: empty registry.
  - `test_u07`: dev-link consumer skipped, or refused when scoped.
  - `test_u08`: `source fetch` without a name fetches every approved tap and deploys nothing.
  - `--skill` restricts the fetch to the named taps.
  - The `scope.expand` consent is retired.
  - `UpdateSafetyOnTaps`: removed skill, unsafe package, hooks suppressed, late failure rolled back, unavailable consumer before any fetch, and `update.incomplete` beside incomplete workflow roles.
- **Full suite:** guarded per-module run on `a62f7c4`: 45 of 45 modules OK, 386 tests, 16 skipped; literal `python -B -m unittest`: exit 0, 386 tests in 8694 s, OK (skipped=16).

### Contract notes
- The update journal keeps `operation: update`. The previous program (`0658a40`) therefore completes a crashed tap-fetching update journal with the same outcome, instead of refusing it as the RFC's rollout sentence states.
- The fetch phase holds the writer lock for the network round, as `source fetch NAME` does.
- A resolution error other than `lock.resolution_required` or `lock.ref_rebound` refuses the whole invocation, as CLI.md step 6 states.
- Reviewing a tag- or branch-pinned consumer after a no-name `source fetch` still needs `source inspect --ref`.
