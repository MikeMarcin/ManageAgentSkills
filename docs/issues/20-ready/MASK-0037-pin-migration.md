---
schema: "implement-rfc.card.v1"
id: "MASK-0037"
title: "Add explicit legacy migration and pinned update operations"
status: "Ready"
rfcs: ["RFC-MASK-0008"]
depends_on: ["MASK-0036"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "pin-migration", "stage": "B — reproducible content", "provisional_id": false}
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

Dependency MASK-0036 is Done at 0301992 (source 5352257). RFC_BASE_SHA remains 9dc90df45febf2a6e048ace60a4ac959807aaaf6 on MASK-0069. No implementation or acceptance for this slice is asserted yet.

## Bounded implementation decisions

- Use the existing typed transition engine. Add bounded machine configuration migration with exact before/after bytes and selected legacy-to-pinned conversion. Prepare raw clean authoring HEAD artifacts outside the writer lock, then recheck source identity, HEAD/index/status and all control observations. Preserve resolved legacy target lists explicitly; preserve unselected records. Old pending recovery comes first.
- Implement selected pinned updates with cached, network-free previews, frozen candidates, explicit ref-rebind handling, and one journal for lock/link changes. Commit selectors stay fixed. Legacy targeted updates require migration; unqualified legacy update preserves shared-checkout semantics.
- Dev-link is an explicit scope-local dirty/unpinned exception derived from an approved physical authoring root and validated passive package. Guard returning to pins and forbid fleet eligibility. Never write back automatically.
- Publishing uses isolated worktree and exact validated package/provenance paths with separately explicit commit/push flags. Preserve unrelated source working/index bytes; refuse overlapping/concurrent changes. No filters/hooks execute. Only disposable local bare remotes are used for verification; no AgentSkills publication is authorized.
- Keep the existing program schema guard. Document an explicit reviewed-program install via direct Python before persisted migration, retaining the fallback.
- Focus verification on public project/user/all migration, exact rollback at typed effects, dirty/unborn/pending/concurrency refusal, two-consumer selected update isolation, dev-link and return, and scoped publishing. Reuse unchanged engine evidence; native changed engine/migration tests will be combined with targeting where practical.
