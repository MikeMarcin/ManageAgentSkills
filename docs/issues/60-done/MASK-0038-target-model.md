---
schema: "implement-rfc.card.v1"
id: "MASK-0038"
title: "Implement per-binding agent choices and compatibility metadata"
status: "Done"
rfcs: ["RFC-MASK-0009"]
depends_on: ["MASK-0036"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "target-model", "stage": "B — selection semantics", "provisional_id": false}
acceptance: [{"criterion":"RFC-MASK-0009-AC01","outcome":"pass","revision":"c2fa4962f06349d33169fae478b69b7f758e7bb4","evidence":{"kind":"observation","detail":"Local public independent project/user choices, all/inherit, enabled policy, no executable probes and physical CAS passed; native milestone remains0040."}},{"criterion":"RFC-MASK-0009-AC02","outcome":"pass","revision":"c2fa4962f06349d33169fae478b69b7f758e7bb4","evidence":{"kind":"observation","detail":"Guarded setters preserve exact package rows and no-apply links, collision/preview/no-op checks pass; reuse0037 migration preservation."}},{"criterion":"RFC-MASK-0009-AC03","outcome":"pass","revision":"c2fa4962f06349d33169fae478b69b7f758e7bb4","evidence":{"kind":"observation","detail":"Generic/specific/absent metadata, conditional cold skip, scope-local overrides and corrected policy recovery/artifact status regressions passed."}}]
---

# MASK-0038: Implement per-binding agent choices and compatibility metadata

Governing RFC: [RFC-MASK-0009](../../rfcs/RFC-MASK-0009-scope-agent-targeting-and-compatibility.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Implement all/explicit agent semantics independently per consumer, machine-readable generic/specific/unspecified metadata and when filters. Explicit incompatible intent blocks; implicit all-agent restrictions report exclusions. Preserve v1 effective targets at migration and avoid installation-detection-based default changes.

Own only: `mask_selection.py (new)`, `mask_core.py`, `mask.py`, `tests/test_targeting.py (new)`, `tests/test_compatibility.py (new)`, bounded integration in `mask_pinned.py`, `mask_fs.py`, `mask_resolve.py`, `mask_ensure.py`, local selection-policy schema, affected state/journal schemas, current README/CLI docs, and affected existing targeting-gate tests. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0009-AC01: The same skill has independently configurable personal and project agent sets, with new selections defaulting to all supported/enabled agents and no executable-detection side effects.
- RFC-MASK-0009-AC02: V1 migration preserves explicit and inherited target behavior; per-skill edits/locks/plans remain guarded and no-op stable.
- RFC-MASK-0009-AC03: Generic, absent and agent/platform-specific metadata produce distinct truthful reports; explicit incompatibilities block, and conditional/inapplicable bindings are not called installed.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_targeting tests.test_compatibility tests.test_user_scope

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Dependency MASK-0036 is Done; MASK-0037 migration/update source is 7bbe2db and Done at a5b887c. RFC_BASE_SHA remains 9dc90df45febf2a6e048ace60a4ac959807aaaf6 on MASK-0070. Implementation and local acceptance are recorded below; native milestone acceptance remains MASK-0040.

## Bounded implementation decisions

- Use one pure effective-selection evaluator for normalized declaration/lock, verified metadata, current platform/architecture, enabled adapters, scope and origins. Return stable selected/deployed/not_applicable/excluded_by_metadata/blocked/overridden outcomes. The existing planner consumes deployable rows and carries all outcomes; no second installer or host executable detection.
- Replace temporary per-binding and restrictive-metadata gates. Absent metadata is unspecified; generic and specific publisher assertions remain distinct, never called tested. False when conditions do not require artifact hydration; all portable bindings retain exact lock rows. Explicit incompatible agents block; all/default implicit agents may be excluded. Otherwise applicable platform/architecture restrictions block unless an explicit local policy allows them.
- Add a bounded local selection-policy object for enabled supported adapters and explicit reasoned compatibility overrides tied to one physical consumer and coordinate. Public policy changes are previewable/guarded; exact policy bytes/identity participate in the same typed journal and preparation CAS. No downloaded declaration/package grants itself authority. Default absent policy enables the currently supported Claude/Codex set. Global policy changes show all affected registered scopes; per-consumer overrides remain narrow.
- Add guarded project/user set-agents for one binding and v2 whole set-targets compatibility semantics. Preserve unrelated bindings/origins and exact package resolutions while updating the selection digest; --apply reconciles prospective declaration/lock/policy together, with collisions preserving all before bytes. Local compatibility overrides have a separate explicit public set/clear operation, reason and warning; they do not enable unsupported adapters or grant source trust.
- Read pinned metadata from validated artifact or validated raw candidate payload views. A dev-link uses its validated live authoring input and remains reported unpinned. Conditional preparation passes only applicable coordinates to store.ensure; no lock/ref mutation from ensure.
- The contribution evaluator accepts attributed internal contribution rows, with the local declaration as the current public producer. RFC-0039 establishes union/conflict/shadowing semantics; RFC-0010 later connects public profile storage. Do not invent a dependency cycle or advertise profile commands here.
- Focused public targeting/compatibility checks cover independent personal/project choices, implicit/all versus explicit restrictions, when/architecture conditions, no executable side effects, local override/policy authority, collision rollback, stale/no-op guards and cold skipped-package preparation. Reuse unchanged migration target-preservation evidence. Native affected engine/migration/targeting checks remain MASK-0040 after the adapter slice.

## Integrated result

Source revision: `c2fa4962f06349d33169fae478b69b7f758e7bb4`.

The pure evaluator, public registered-v2 setters, machine-local enabled-agent policy and reasoned physical-scope overrides now feed the ordinary planner/recovery engine. Runtime module inventory includes mask_selection.py. Declaration-only setters preserve owned links; apply setters use one prospective declaration/lock/link plan. False when bindings keep their locks and skip acquisition. Dev-link metadata is validated live. Actual deployment reporting requires verified target content; a dangling owned leaf is not deployed.

Local direct verification (macOS):

- `python3 -B -m unittest tests.test_targeting tests.test_compatibility tests.test_locks.LockTests.test_v2_missing_stale_coherent_guards_and_legacy_mutations tests.test_pinned_recovery.PinnedTests.test_readiness_exact_authority_and_no_inferred_network tests.test_launcher.LauncherTests.test_program_update_separate_and_incompatible_refused`: 12/12 passed in 76.223s, no skips, before the bounded review corrections.
- After those corrections: `python3 -B -m unittest tests.test_compatibility.CompatibilityTests.test_recovery_rederives_links_from_effective_after_policy tests.test_compatibility.CompatibilityTests.test_final_policy_edits_retain_partial_recovery tests.test_targeting.TargetingTests.test_dangling_and_corrupt_artifacts_are_never_reported_deployed tests.test_targeting.LegacyPolicyTests tests.test_compatibility.PolicyModelTests tests.test_targeting.TargetingTests.test_independent_agents_inheritance_noop_and_declaration_only`: 6/6 passed in 28.516s, no skips. An initial mechanical indentation error prevented that command from loading tests; corrected before the successful run.
- Earlier focused iterations corrected a cold-cache fixture setup and required recovery exit-code mapping. The combined successful run above covers those fixes. JSON schema syntax and Python syntax checks passed; jsonschema was unavailable, so no JSON Schema validator execution is claimed. Final git diff --check passed.

Closeout review runtime: one independent rfc-reviewer, gpt-6-astra/high, bounded to new policy and typed-transition authority. Two confirmed failures were fixed: saved recovery now recomputes owned links from effective after-policy, and exact final controls are rechecked after typed effects, before state and before journal deletion. Reviewer fixtures mask-fixture-ofjif4rt and mask-fixture-bf_ij2f3 were removed. Primary public plan reproduction found dangling artifact links incorrectly reported deployed; mask-fixture-hu6k_xn5 was removed and the focused regression covers missing and corrupt artifacts. No repeat review was run.

Worker temporary fixtures used TemporaryDirectory cleanup; individual names were not logged. The worker confirmed no mask-fixture-* roots remained in Python's temporary directory and its /tmp/mask-target-capabilities.json was absent. User .DS_Store was preserved. Reuse unchanged MASK-0037 migration target-preservation evidence. Native engine/migration/targeting and full adapter/contribution acceptance remain MASK-0039/0040; this Done card does not claim RFC-0009 terminal status.
