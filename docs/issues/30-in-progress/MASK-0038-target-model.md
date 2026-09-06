---
schema: "implement-rfc.card.v1"
id: "MASK-0038"
title: "Implement per-binding agent choices and compatibility metadata"
status: "In Progress"
rfcs: ["RFC-MASK-0009"]
depends_on: ["MASK-0036"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "target-model", "stage": "B — selection semantics", "provisional_id": false}
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

Dependency MASK-0036 is Done; MASK-0037 migration/update source is 7bbe2db and Done at a5b887c. RFC_BASE_SHA remains 9dc90df45febf2a6e048ace60a4ac959807aaaf6 on MASK-0070. No implementation or acceptance for this slice is asserted yet.

## Bounded implementation decisions

- Use one pure effective-selection evaluator for normalized declaration/lock, verified metadata, current platform/architecture, enabled adapters, scope and origins. Return stable selected/deployed/not_applicable/excluded_by_metadata/blocked/overridden outcomes. The existing planner consumes deployable rows and carries all outcomes; no second installer or host executable detection.
- Replace temporary per-binding and restrictive-metadata gates. Absent metadata is unspecified; generic and specific publisher assertions remain distinct, never called tested. False when conditions do not require artifact hydration; all portable bindings retain exact lock rows. Explicit incompatible agents block; all/default implicit agents may be excluded. Otherwise applicable platform/architecture restrictions block unless an explicit local policy allows them.
- Add a bounded local selection-policy object for enabled supported adapters and explicit reasoned compatibility overrides tied to one physical consumer and coordinate. Public policy changes are previewable/guarded; exact policy bytes/identity participate in the same typed journal and preparation CAS. No downloaded declaration/package grants itself authority. Default absent policy enables the currently supported Claude/Codex set. Global policy changes show all affected registered scopes; per-consumer overrides remain narrow.
- Add guarded project/user set-agents for one binding and v2 whole set-targets compatibility semantics. Preserve unrelated bindings/origins and exact package resolutions while updating the selection digest; --apply reconciles prospective declaration/lock/policy together, with collisions preserving all before bytes. Local compatibility overrides have a separate explicit public set/clear operation, reason and warning; they do not enable unsupported adapters or grant source trust.
- Read pinned metadata from validated artifact or validated raw candidate payload views. A dev-link uses its validated live authoring input and remains reported unpinned. Conditional preparation passes only applicable coordinates to store.ensure; no lock/ref mutation from ensure.
- The contribution evaluator accepts attributed internal contribution rows, with the local declaration as the current public producer. RFC-0039 establishes union/conflict/shadowing semantics; RFC-0010 later connects public profile storage. Do not invent a dependency cycle or advertise profile commands here.
- Focused public targeting/compatibility checks cover independent personal/project choices, implicit/all versus explicit restrictions, when/architecture conditions, no executable side effects, local override/policy authority, collision rollback, stale/no-op guards and cold skipped-package preparation. Reuse unchanged migration target-preservation evidence. Native affected engine/migration/targeting checks remain MASK-0040 after the adapter slice.
