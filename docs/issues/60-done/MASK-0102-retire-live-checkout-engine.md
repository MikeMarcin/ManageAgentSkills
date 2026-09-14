---
schema: "implement-rfc.card.v1"
id: "MASK-0102"
title: "Remove legacy paths, commands and add the migration gate"
status: "Done"
rfcs: ["RFC-MASK-0021"]
depends_on: ["MASK-0101"]
priority: "P1"
metadata: {"packet":"mask-corrective-managed-taps","provisional_id":false,"packet_key":"retire-live-checkout-engine","milestone_plan":{"id":"tap-only-deployment","path":"docs/rfcs/plans/tap-only-deployment/milestone-plan.json"}}
acceptance: [{"criterion":"MASK-0102 AC1 (engine:exit:1; RFC-MASK-0021-AC02 fixture evidence): no code path can compute a link text into a Git checkout except source dev-link; a test enumerates every link producer","outcome":"pass","revision":"a62f7c482229c0964ff0f14b30753633f7c6e74e","evidence":{"kind":"command","detail":"tests.test_link_producers on a62f7c4 (Windows 11 Home 10.0.26200, Python 3.14.6, Git 2.55.0.windows.3; MASK_HOME, USERPROFILE and HOME redirected): 4 tests OK. LinkProducers enumerates every symlink_to, bare or os symlink, link_to, hardlink_to, CreateSymbolicLink(W/A) call and mklink string in mask*.py and asserts the set equals three allowlisted producers, each with its target derivation. pinned.target returns only a store payload or an explicit dev authoring package. StoreTargetedLinks drives install (project and --user), apply, ensure, project register --apply, project set-agents --apply, pinned link adopt, a crash at the link checkpoint with recover --rollback and --complete, tap add --checkout (B07: targets unchanged; mismatched origin refuses source.identity_mismatch) and source dev-link with --to-pinned. After each step every link recorded in state.json and every link on disk resolves under MASK_HOME/store/v1, except the explicit dev link. LegacyRecordsYieldNoLinks: plan, apply, ensure, register, unregister and adopt on a mode-less record refuse migration.required with the snapshot unchanged. tests.test_update U01-U09 assert store links in every update case. Negative controls: at be64043, 2 of 4 fail (the mask_fs.plan clone link producer and the pinned.target checkout return); a mutation that points pinned.target at the authoring checkout fails the journey at the first install; injected bare os symlink, CreateSymbolicLinkW and mklink producers are all reported by the widened scanner."}},{"criterion":"MASK-0102 AC2 (engine:exit:2; RFC-MASK-0021-AC05): capabilities lists no retired command and invoking one exits 2","outcome":"pass","revision":"a62f7c482229c0964ff0f14b30753633f7c6e74e","evidence":{"kind":"command","detail":"tests.test_retired_paths RetiredCommands on a62f7c4. capabilities has no source.status, source.migrate or migrate descriptor. init has no source, remote or branch argument. schemas.machine is 3 and deployment_model is taps. source status, source migrate, migrate and migrate --to-pinned --project P exit 2 invocation.invalid, and a snapshot of the whole disposable base is unchanged. tests.test_legacy_baseline LiveCheckoutBaseline: the formerly clone-linking commands refuse on the builder states and write nothing. Negative control: tests.test_retired_paths fails 5 of 5 at be64043."}},{"criterion":"MASK-0102 AC3 (engine:exit:2; RFC-MASK-0021-AC05): on a v1 or v2 configuration every non-exempt command exits 4 migration.required with the doctor remediation","outcome":"pass","revision":"a62f7c482229c0964ff0f14b30753633f7c6e74e","evidence":{"kind":"command","detail":"tests.test_retired_paths MigrationGate on a62f7c4, on the v1 and v2 machines from tests.legacy_support.build_legacy_machine. Every capabilities descriptor except capabilities, config.show, doctor, recover and self.* exits 4 migration.required, with details.schema_version and details.remediation [mask, doctor, --migrate, --dry-run]; the whole disposable base is unchanged. The exempt commands proceed: config show reports migration_required true; doctor reports a migration.required issue and --check exits 7; recover --inspect works; self status, self install --dry-run and self update --dry-run never return migration.required. Retired journals (migrate, shared-checkout git, legacy ownership) are shown with data.retired and refused recovery.conflict. LegacyConsumerRemediation: consumer-level refusals from update, apply, source dev-link and inventory carry the same remediation argv. tests.test_legacy_baseline: legacy bytes parse only with mask_core.config(..., legacy=True), and the default refuses. Independent critical review reproducers confirmed launch, ensure --repair --all, source fetch --locked, update --dry-run and --offline, install --dry-run, init, tap add, project show, list, inventory and lock all refuse on v1 and v2 with nothing written."}},{"criterion":"MASK-0102 AC4: the full suite passes","outcome":"pass","revision":"a62f7c482229c0964ff0f14b30753633f7c6e74e","evidence":{"kind":"command","detail":"Guarded per-module run on a62f7c4 (Windows 11 Home 10.0.26200, Python 3.14.6, Git 2.55.0.windows.3): every tests.test_* module ran as its own python -B -m unittest -v tests.MODULE process, 3 in parallel, with MASK_HOME, USERPROFILE and HOME redirected to empty per-module directories. Result: 45 of 45 modules OK, 386 tests, 16 skipped, 47 minutes wall time. HEAD a62f7c4, tree 31280ec and an empty git status were identical before and after the run. The literal single-process command python -B -m unittest on a62f7c4, with MASK_HOME, USERPROFILE and HOME redirected to empty directories, finished exit 0: Ran 386 tests in 8694 s, OK (skipped=16). HEAD and a hash guard over the product, schema, test and script files were identical before and after. The owner profile snapshot (the ~/.mask file hashes and the skill, agent and launcher entries) was identical before integration, before the final suites and after them. macOS was not exercised (RFC-MASK-0021-AC08 remains open for the closeout)."}},{"criterion":"MASK-0102 bounded work: retired paths and commands deleted, migration gate added with the documented exemptions, planner refuses legacy records and v1 declarations, inventory rewritten over pinned records, set/require/unrequire kept for v2, legacy-only tests ported or dropped, tests/legacy_support.py kept","outcome":"pass","revision":"a62f7c482229c0964ff0f14b30753633f7c6e74e","evidence":{"kind":"artifact","detail":"d61d4be deletes the live-checkout engine: mask_git.update, candidate_packages, explicit_selection and every AgentSkills literal; mask_core package, catalog, registry_record and legacy_source; the mask_fs.plan legacy branch; the adopt legacy branch and recover package loop; the mask_pinned.target checkout case and migrate machinery; mask_task v1_proposal and legacy_alias; the v1 branches of project_dispatch and guard_command; scope.expand. The migrate --to-pinned machinery is deleted, and MASK-0104 ports it from 0658a40. mask_core.config refuses v1/v2 unless legacy=True, and mask.migration_gate runs before any command effect. tests.test_inventory: 9 tap-first cases (converged, drifted, unmanaged, unavailable, dev-link, two taps with one ID, both scopes, pagination and work bounds, a legacy record giving migration.required with no rows), all writing nothing; all 9 fail at be64043. project/user set, require and unrequire stay registered and keep their pre-existing v2 behavior, the typed selection.command_unsupported refusal. tests/legacy_support.py is unchanged."}},{"criterion":"Legacy-marked tests ported or retired, with an independent port-integrity review adjudicated","outcome":"pass","revision":"a62f7c482229c0964ff0f14b30753633f7c6e74e","evidence":{"kind":"artifact","detail":"938eb36 ports these modules to tap-first pinned consumers, keeping their engine invariants: test_reconcile_apply, test_reconcile_plan, test_recovery, test_manifest_registry, test_locks, test_pinned_recovery, test_ensure, test_user_scope, test_targeting, test_skill_catalog, test_sources, test_end_to_end, test_update_task, test_readme_journeys and test_readiness_entrypoints. Retired: tests/test_pin_migration.py (migrate --to-pinned; MASK-0104 ports the crash matrix from 0658a40), the scope.expand consent classes, and tests/test_git_update.py, whose tap-model scenarios are covered by tests.test_update. rfc-reviewer-critical found one blocking gap in the port: the self update program-checkout journal had lost coverage. 97edf2d ports it to tests/test_launcher.py (crash after the advance refuses rollback and completes; a failed merge keeps a partial journal and rolls back without reset; a failure after the advance keeps the journal). 5 tests OK; a mutation letting rollback proceed after the advance fails the crash test. The fixture bases no longer contain legacy_init, declare or legacy_bootstrap."}},{"criterion":"Defects exposed by the ported tests fixed with regression tests","outcome":"pass","revision":"a62f7c482229c0964ff0f14b30753633f7c6e74e","evidence":{"kind":"command","detail":"a62f7c4 fixes three defects that predate this card. (1) install --project into the registered personal home rewrote user.json and its links; the planner now plans the requested scope and the install refuses target.overlap (test_user_scope test_linked_parent_and_cross_scope_overlap_refuse). (2) apply, ensure and source dev-link on a moved registered root exited 5 filesystem.failed; they now refuse user.unavailable or project.unavailable (test_adopt_unregister_keep_links_and_unavailable_home). (3) remove with a missing store artifact left a journal that could be neither completed nor rolled back; mask_fs.execute now verifies retained artifacts before writing a journal and refuses typed, and remove prepares the removed rows' old artifacts offline (test_reconcile_apply test_dangling_owned_link_is_removed, test_dangling_owned_link_with_an_uncached_commit_refuses_without_a_journal, test_unverifiable_old_artifact_refuses_before_any_journal). Every new or extended test fails at 07848a5 and passes on a62f7c4."}},{"criterion":"Independent critical review of the candidate adjudicated","outcome":"pass","revision":"a62f7c482229c0964ff0f14b30753633f7c6e74e","evidence":{"kind":"observation","detail":"rfc-reviewer-critical, route claude-fable-5-1 at high effort (matching the generated role), reviewed d61d4be for link authority, gate completeness, recovery safety and update isolation, and found no blocking finding. Its reproducers covered crafted state and journals, the gate on v1 and v2, a previous-program install journal recovered by the new program, annotated-tag and branch selectors, and guarded reruns. Non-blocking findings adjudicated: update.incomplete masked by workflow.incomplete (fixed, a62f7c4); consumer-level remediation argv (fixed); scanner spellings (widened, 07848a5); the RFC rollout sentence about update journals (a contract note, not a safety problem); the writer lock held during fetch (note for MASK-0105); capabilities.migration and the doctor guard (MASK-0104); whole-invocation refusal on a resolution error (a contract note); untyped git.failed on Windows long cache paths (note for MASK-0106). Open contract question, not blocking this card: contracts/CLI.md says project/user set, require and unrequire write a v2 declaration and lock, but the product has refused them for v2 since before this RFC. That needs an owner decision before MASK-0105."}}]
---

# MASK-0102: Remove legacy paths, commands and add the migration gate

Governing RFC: [RFC-MASK-0021](../../rfcs/RFC-MASK-0021-tap-only-deployment.md). Live IDs reconciled after rebase; the reservation is `f81155a`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-managed-taps.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-managed-taps/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-managed-taps/ACCEPTANCE.md).

## Objective and owned paths

`mask.py` (command table, `local_dispatch` tail, `project_dispatch` v1 branches, `diagnostics` checkout probe), `mask_fs.py` (planner legacy branch, `adopt`, `recover`, `registration_safe`), `mask_pinned.py` (`target` checkout case, the update/migrate transition split), `mask_task.py` (`v1_proposal`, `legacy_alias`, `listing` legacy branch), `mask_git.py` (`update` and the `AgentSkills` basename checks), `mask_core.py` (`package`, `catalog`, `registry_record`), `mask_resolve.py` (`guard_command` v1 branches), `mask_report.py`, `schemas/pending-v3.schema.json` and the tests that exercised the checkout model.

## Bounded work

Delete the live-checkout deployment paths and the `init --source`, `source status`, `source migrate` and `migrate` commands. Add the `migration.required` gate in `mask_core.config` with the documented exemptions, and an early planner refusal for legacy records and v1 declarations without `allow_migration`. Rewrite inventory over pinned records. Keep `project/user set|require|unrequire` for v2 declarations. Port or drop legacy-only tests; keep `tests/legacy_support.py` for the doctor card.

## Acceptance

No code path can compute a link text into a Git checkout except `source dev-link`; a test enumerates every link producer. `capabilities` lists no retired command and invoking one exits 2. On a v1 or v2 configuration every non-exempt command exits 4 `migration.required` with the doctor remediation. The full suite passes.

Criterion coverage: RFC-MASK-0021-AC02, RFC-MASK-0021-AC05.

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
- Claim `f038340`; integrated at `d61d4be`; tests ported at `938eb36`; corrections at `a62f7c4`.
- The heading above ends the bound Acceptance text, so this record does not change the milestone binding. A recomputed assignment matched every fingerprint.

### Acceptance evidence
- **No link into a checkout except `source dev-link`:** `tests.test_link_producers`.
  - The static test enumerates every link-producing call, including bare `os.symlink`, the Win32 `CreateSymbolicLink` API and `mklink`, against an allowlist of three producers, each with its target derivation.
  - `pinned.target` returns only a store payload or an explicit dev authoring package.
  - A CLI journey drives every public link producer on a tap-first machine. Every recorded and on-disk link resolves under `MASK_HOME/store/v1`, except the explicit dev link. The producers are install for project and personal scopes, apply, ensure, `project register --apply`, set-agents, pinned adoption, crash rollback and completion, `tap add --checkout` (B07) and dev-link to-pinned.
  - A mode-less record refuses `migration.required` from every planner entry point with the snapshot unchanged.
  - Negative controls: at `be64043`, 2 of 4 fail; a mutation that points `pinned.target` at the authoring checkout fails the journey.
- **Retired commands:** `tests.test_retired_paths` `RetiredCommands`.
  - `capabilities` lists no `source.status`, `source.migrate` or `migrate`; `init` has no source, remote or branch; `schemas.machine` is 3 and `deployment_model` is `taps`.
  - Invoking the retired commands exits 2 `invocation.invalid` and writes nothing.
- **Migration gate:** `tests.test_retired_paths` `MigrationGate`.
  - On v1 and v2 builder machines, every command except `capabilities`, `config show`, `doctor`, `recover` and `self *` exits 4 `migration.required`, with `details.remediation` `[mask, doctor, --migrate, --dry-run]` and the whole disposable base unchanged.
  - The exempt commands proceed: `config show` reports `migration_required`; `doctor` reports the issue and `--check` exits 7; `recover --inspect` works; `self status`, `self install --dry-run` and `self update --dry-run` run.
  - Retired journals are shown on inspection and refused `recovery.conflict`.
  - `LegacyConsumerRemediation`: consumer-level refusals carry the same remediation.
  - Negative control: at `be64043` the module fails 5 of 5.
- **Full suite:** guarded per-module run on `a62f7c4`: 45 of 45 modules OK, 386 tests, 16 skipped; literal `python -B -m unittest`: exit 0, 386 tests in 8694 s, OK (skipped=16); HEAD, tree and the code-tree guard unchanged across both runs, and the owner profile snapshot identical.
- **Bounded work:**
  - The planner refuses mode-less records and v1 declarations early.
  - Inventory and where-used are rewritten over pinned records: `tests.test_inventory`, 9 cases, 9 of 9 fail at `be64043`.
  - `project/user set|require|unrequire` are kept, with their existing v2 refusal.
  - `tests/legacy_support.py` is kept for MASK-0104.

### Legacy-marked tests
- **Ported to tap-first consumers:** the planner, apply, recovery, lock, registry, personal-scope, targeting, catalog, sources, end-to-end, update-task, README and readiness tests. `tests.test_update` `UpdateSafetyOnTaps` holds the update safety cases.
- **Retired:**
  - `tests/test_pin_migration.py`; MASK-0104 ports its crash matrix from `0658a40`;
  - `tests/test_git_update.py`; its program-checkout journal coverage moved to `tests/test_launcher.py`;
  - the `scope.expand` consent tests.
- **Independent port-integrity review:** one blocking gap, the `self update` journal coverage. It was ported, and a mutation control proves it.

### Defects found by the ports and fixed in `a62f7c4`
Each fix has a regression test that fails at `07848a5`.
- **Project install into the registered personal home:** it rewrote `user.json`; it now refuses `target.overlap`.
- **`apply`, `ensure` and `source dev-link` on a moved registered root:** they exited 5 `filesystem.failed`; they now refuse `user.unavailable` or `project.unavailable`.
- **`remove` with a missing store artifact:** it left a journal that could not be recovered. Now `execute` verifies the retained artifacts before writing any journal, and `remove` prepares the old artifacts of the rows it removes from the cache.

### Independent review
- **Reviewer:** `rfc-reviewer-critical`, requested route `claude-fable-5-1` at high effort, matching the generated role.
- **Product review of `d61d4be`:** no blocking finding.
  - Reproducers covered crafted state and journals, the gate on v1 and v2, old-program journals recovered by the new program, annotated-tag and branch selectors, and a guarded rerun.
- **Port-integrity follow-up at `938eb36`:** one blocking coverage gap, fixed in `97edf2d`.
- **Non-blocking findings adjudicated:**
  - `update.incomplete` masked by `workflow.incomplete`: fixed.
  - Consumer-level remediation argv: fixed.
  - The link scanner missed some spellings: widened.
  - The rollout sentence is false: contract note.
  - The writer lock held during fetch: note for MASK-0105.
  - `capabilities.migration` and the doctor guard: MASK-0104.
  - Whole-invocation refusal on another consumer's resolution error: note.
  - An untyped `git.failed` on Windows long cache paths: note for MASK-0106.
  - `skill show` no longer refuses a linked entry, and `skill.path_escape` is untested: note.
  - The `inventory complete` flip in `test_pinned_recovery` is intended; it follows the pinned inventory rewrite.

### Open contract question (not blocking this card)
- The retained `contracts/CLI.md` inventory row and the RFC Retirement paragraph say `project/user set|require|unrequire` write a v2 declaration and lock.
- The product has refused them for v2 with `selection.command_unsupported` since before this RFC, and this card keeps that behavior.
- Implementing them or correcting the contract is an owner decision, needed before MASK-0105 describes these commands.

### Limitations
- Only Windows 11 was exercised.
- Help, README and guides still name retired commands (MASK-0105).
- `capabilities` does not yet publish `migration: doctor` (MASK-0104).
