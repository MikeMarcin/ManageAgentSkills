---
schema: "implement-rfc.card.v1"
id: "MASK-0037"
title: "Add explicit legacy migration and pinned update operations"
status: "Done"
rfcs: ["RFC-MASK-0008"]
depends_on: ["MASK-0036"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "pin-migration", "stage": "B — reproducible content", "provisional_id": false}
acceptance: [{"criterion":"RFC-MASK-0008-AC05","outcome":"pass","revision":"7bbe2dbb4749ee3f69351b5c069b1b0ee28dae86","evidence":{"kind":"observation","detail":"Public typed migration rollback checkpoints and affected exact-config/source-change recovery tests pass; selected update binds stale before lock bytes and coherent after controls. Native combined engine checks remain tracked separately."}},{"criterion":"RFC-MASK-0008-AC06","outcome":"pass","revision":"7bbe2dbb4749ee3f69351b5c069b1b0ee28dae86","evidence":{"kind":"observation","detail":"Project, personal and mixed all migration passed; dirty/unborn/pending/hidden checkout flags refuse. Historical d17a607 reader refuses state3 without effects; current direct Python apply succeeds unchanged; existing launcher schema guard tests passed."}},{"criterion":"RFC-MASK-0008-AC07","outcome":"pass","revision":"7bbe2dbb4749ee3f69351b5c069b1b0ee28dae86","evidence":{"kind":"observation","detail":"Public selected updates preserve disjoint consumers; dev-link/return preserves authoring edits; isolated exact-path publication preserves unrelated index/HEAD and reports retained objects and unknown push outcome. Non-root and committed selected-index mapping limits are explicit."}}]
---

# MASK-0037: Add explicit legacy migration and pinned update operations

Governing RFC: [RFC-MASK-0008](../../rfcs/RFC-MASK-0008-pinned-artifacts-and-recovery.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Preserve dirty/unborn sources and old recovery. Implement reviewed program upgrade then explicit selected-scope migration, dev-link escape hatch, targeted pinned update and legacy all-source behavior. Source publication uses isolated worktree/exact paths under explicit authority. No hidden schema migration or reset.

Own only: `mask.py`, `mask_resolve.py`, `mask_install.py`, `mask_git.py`, `tests/test_pin_migration.py (new)`, `tests/test_pinned_update.py (new)`, bounded integration changes in `mask_pinned.py`, `mask_core.py`, `mask_fs.py`, `mask_sources.py`, `mask_provenance.py`, affected persisted schemas, runtime inventory tests, and current README/CLI/architecture docs. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0008-AC05: Interruptions before/after lock, link and state effects preserve bounded v3 recovery; configuration/state migrations preserve exact legacy rollback bytes and reject concurrent edits.
- RFC-MASK-0008-AC06: Explicit migration covers project and personal consumers, dirty/unborn sources, old pending journals, schema-incompatible old programs, and direct-entrypoint escape paths.
- RFC-MASK-0008-AC07: Cache preparation, retention, dev-link exceptions and scoped publishing cannot silently alter other consumers, delete authoring history or claim atomicity across readers/devices.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_pin_migration tests.test_pinned_update tests.test_launcher

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Dependency MASK-0036 is Done at 0301992 (source 5352257). RFC_BASE_SHA remains 9dc90df45febf2a6e048ace60a4ac959807aaaf6 on MASK-0069. Implementation and direct evidence are recorded below; native engine/targeting verification remains at MASK-0040.

## Bounded implementation decisions

- Use the existing typed transition engine. Add bounded machine configuration migration with exact before/after bytes and selected legacy-to-pinned conversion. Prepare raw clean authoring HEAD artifacts outside the writer lock, then recheck source identity, HEAD/index/status and all control observations. Preserve resolved legacy target lists explicitly; preserve unselected records. Old pending recovery comes first.
- Implement selected pinned updates with cached, network-free previews, frozen candidates, explicit ref-rebind handling, and one journal for lock/link changes. Commit selectors stay fixed. Legacy targeted updates require migration; unqualified legacy update preserves shared-checkout semantics.
- Dev-link is an explicit scope-local dirty/unpinned exception derived from an approved physical authoring root and validated passive package. Guard returning to pins and forbid fleet eligibility. Never write back automatically.
- Publishing uses isolated worktree and exact validated package/provenance paths with separately explicit commit/push flags. Preserve unrelated source working/index bytes; refuse overlapping/concurrent changes. No filters/hooks execute. Only disposable local bare remotes are used for verification; no AgentSkills publication is authorized.
- Keep the existing program schema guard. Document an explicit reviewed-program install via direct Python before persisted migration, retaining the fallback.
- Focus verification on public project/user/all migration, exact rollback at typed effects, dirty/unborn/pending/concurrency refusal, two-consumer selected update isolation, dev-link and return, and scoped publishing. Reuse unchanged engine evidence; native changed engine/migration tests will be combined with targeting where practical.


## Implemented boundary and evidence

Source revision: `7bbe2dbb4749ee3f69351b5c069b1b0ee28dae86`. Planning `05c7247`; claim `d5e733b`.

Selected project/personal/all migration uses clean raw authoring HEAD artifacts and a typed machine-config transition through the existing engine. Resolved legacy targets and unselected records are preserved. Exact before configuration text, declarations, lock absence, ownership and source observations remain recovery inputs. Source changes after recovered link effects or before state/journal finalization preserve partial recovery rather than claim success.

Pinned updates use cached candidates with selected coordinate intersections across consumers; unrelated consumers remain exact. Explicit update can repair a changed selector with an older disk lock while binding exact before bytes and requiring coherent after controls. Ordinary ensure/apply do not repair stale locks. Unqualified legacy shared-source updates, including an empty registry, retain compatibility behavior. Dev-link records a scope-local unpinned authoring override and has an explicit guarded return. Source publication creates only selected package commits/retained refs through an isolated unfiltered index; it preserves unrelated authoring/index content and reports retained objects and unknown attempted-push outcomes.

Direct local verification (macOS; no native result inferred):

- Initial five public methods: 43.406s, three passes and two legacy-only declaration-reader failures. Corrected dispatch to the v1/v2 reader; subsequent combined run covers those corrections.
- `python3 -B -m unittest tests.test_pin_migration tests.test_pinned_update tests.test_launcher`: 12 methods, 99.514s, 11 passed and one changed-selector repair failure. Corrected explicit-update-only live-lock validation; no broad rerun.
- `python3 -B -m unittest tests.test_pinned_update.UpdateTests.test_fixed_commit_and_rebound_selector_updates tests.test_pinned_update.RecoveryUpdateTests tests.test_pin_migration.MigrationTests.test_recovery_rejects_changed_config_and_source`: four affected methods passed in 29.671s, no skips, before later focused review corrections.
- Four affected methods covering exact config-byte tampering, after-link source change, uncommitted index mapping/retained-object failure, and lost push acknowledgement passed in 24.874s, no skips. The recovered-link source test was then strengthened as described below.
- `test_after_link_authoring_change_retains_partial_journal` (including public recover-complete injection) and `test_migration_preview_refuses_unreadable_generated_lock`: two passed in 12.450s, no skips.
- `RecoveryUpdateTests.test_cold_update_metadata_and_source_effects_preserve_intent`: passed in 6.301s. Cold generic migration and dev-link checks also passed; the publication invalid-path assertion was corrected to the actual typed exit 3, with the public publication body passing.
- `python3 -B -m unittest tests.test_pinned_update.UpdateTests.test_all_selected_skill_preserves_disjoint_consumer`: one passed in 9.525s, no skips. Both upstream packages advance; only the selected alpha consumer changes, while beta state/lock/link remain exact. Missing and duplicate coordinates refuse.
- `python3 -B -m unittest tests.test_cli_protocol tests.test_subprocess_policy`: ten methods in 7.757s, nine passed; one expected macOS skip for the native Windows suspended Job Object prerequisite path.
- An actual extracted prior program at `d17a607d60797b88efb312a349e8f823fcc90111` refused public apply against migrated state with exit 3 / `state.unsupported_version`, preserving the full fixture. The current direct Python apply then succeeded unchanged. The first observation harness expected the less precise `state.invalid` code; its assertion was corrected, with no product change, before verifying preservation and fallback.
- Formatting-only cleanup retained AST equivalence (worker observation); `git diff --check` passed. A newly inherited test alias was disabled to avoid running the identical public all-scope test twice.

Closeout review runtime: one `rfc-reviewer`, GPT-6 Astra/high, read-only migration/update boundary against `d5e733b`. It reproduced two AC05 defects: independently formatted config-before copies could change rollback bytes, and source edits between recovered link effects could escape finalization. Exact before-byte agreement and grouped/final source rechecks corrected both; only affected checks were repeated. No second review or full-suite claim.

Limitations remain explicit: publication accepts non-root package paths and requires selected index mappings already committed; indexed mapping publication is not silently inferred. Pinned update is cached-only after explicit source fetch/inspect. Detailed pinned/dev-link inventory remains RFC-0011. Native engine/migration/targeting verification remains open at MASK-0040; this Done slice does not close RFC-0008 or advertise fleet support.

All worker/reviewer test roots and temporary publishing worktrees were removed. Primary old-reader fixtures `mask-fixture-mjaiut16` and `mask-fixture-nk02oi8o` were removed. No real source publication or user consumer migration occurred. The reusable native driver is retained only for the planned native checks; no Windows checkout/process is active. Unrelated `.DS_Store` remains untouched.
