---
schema: "implement-rfc.card.v1"
id: "MASK-0035"
title: "Build isolated raw-byte artifacts and exact hydration"
status: "Done"
rfcs: ["RFC-MASK-0008"]
depends_on: ["MASK-0034", "MASK-0033"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "artifact-store", "stage": "B — reproducible content", "provisional_id": false}
acceptance: [{"criterion":"MASK-0035 bounded immutable store and exact hydration","outcome":"pass","revision":"d17a607d60797b88efb312a349e8f823fcc90111","evidence":{"kind":"observation","detail":"17 focused methods plus four affected and two added checks pass; public source fetch --locked validates raw bytes and exact acquisition with preserved controls. Engine/native acceptance remains open."}}]
---

# MASK-0035: Build isolated raw-byte artifacts and exact hydration

Governing RFC: [RFC-MASK-0008](../../rfcs/RFC-MASK-0008-pinned-artifacts-and-recovery.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Compute canonical payload manifests including supporting bytes/logical modes; stage and atomically publish digest directories without hardlinking authoring files. Validate preexisting artifacts and corruption. Hydrate only exact approved locked objects, including controller-forwarded packages later. Leave retention conservative and report cache effects separately.

Own only: `mask_store.py (new)`, `mask_git.py`, `tests/test_artifacts.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0008-AC01: Two worktrees simultaneously use distinct immutable versions of one skill, and source authoring/ref movement changes neither deployment until an explicit selected update.
- RFC-MASK-0008-AC02: Locks reproduce raw package bytes across fixture machines; digest, package path, source identity, executable mode, malformed lock and moved-ref errors fail closed.
- RFC-MASK-0008-AC03: Ensure restores available exact artifacts, optionally hydrates only approved locked content, never resolves latest or rewrites lockfiles, and reports unavailable exact commits honestly.
- RFC-MASK-0008-AC07: Cache preparation, retention, dev-link exceptions and scoped publishing cannot silently alter other consumers, delete authoring history or claim atomicity across readers/devices.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_artifacts
- Compare fixture raw bytes across independent roots and simulated platform mode mappings.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Implemented bounded artifact construction/hydration slice at `d17a607d60797b88efb312a349e8f823fcc90111`. Public `source fetch --locked --project/--user [--offline]` verifies retained artifacts first without Git, otherwise acquires only the full approved locked commit. Cache selector/ref advertisements and consumer control/link/state bytes remain unchanged. Store-v1 paths derive from validated digest/ID; raw-file validation, closed bounded manifest, complete no-follow inventory and bytes/modes checks protect creation and reuse. Same-volume staging uses no-replace publication; corrupt existing directories are preserved. No hardlinks, checkout filters, script execution or garbage collection. Retained directories and actual/possible acquisition effects are reported separately, including failures.

Verification: `python3 -B -m unittest tests.test_artifacts tests.test_import_safety tests.test_launcher` passed 17 methods in 47.722s without skips. Four affected effects/subset/hydration methods passed in 10.350s after effect-report corrections. Two added fresh-machine/manifest-hardlink checks passed in 4.952s. Exact method names are retained in the focused test module; unchanged passing evidence reused. `git diff --check` passed. Task-created fixtures cleaned; user `.DS_Store` untouched.

This is bounded support for AC01–03/07. Engine link activation, preparation outside the consumer writer lock, ensure fetch policy, state migration and native pinned-deployment acceptance remain MASK-0036/0037 and the coherent native milestone. No full RFC acceptance, actual pinned consumer deployment or POSIX permission result on Windows is asserted.

## Bounded implementation plan

Build a runtime-derived store-v1 path from validated SHA-256 payload identity and skill ID. Revalidate incoming raw files and logical modes before staging; use the same passive package constraints for Git and future forwarded payloads. Write unique same-volume staging directories, validate bytes/manifest, flush, and publish without replacing an existing digest directory. Validate reused artifacts completely (missing/extra entries, links, special files, byte digests and logical modes); never rely on timestamps. Preserve existing corruption for explicit repair. No hardlinks, checkout filters, execution or garbage collection.

Extend ownership narrowly to shared payload validation, exact-source acquisition, resolver/CLI dispatch and capabilities, launcher runtime inventory, an explicit artifact-manifest schema and current documentation as necessary. Public `source fetch --locked --project/--user` may acquire only the exact approved locked commits and materialize verified artifacts; cached/offline preparation never resolves selectors or changes lock/control/link/state bytes. Keep possible network and retained cache effects explicit on failures as well as success. Engine activation/ensure policy remain MASK-0036.

Focused checks cover independent roots with identical raw CRLF/executable content, immutable reuse across authoring/ref movement, full corruption/collision refusal, stage-publication failure cleanup, exact missing commit without substitution, source approval, and observational offline previews. Native mode evidence waits for the coherent pinned-deployment milestone. Retain all published artifacts conservatively.

## Native Windows follow-through

ExampleWinHost native Python3.14.6/Windows11, committed candidate `8cb1ab00c1fae6c38a576466efb834398fb5e622`: `python -B -m unittest tests.test_locks tests.test_artifacts` ran 22 methods/219.598s, 21 passed and one fixture error before the hydration path (readonly loose Git object during task-owned cleanup). Fixture-only correction `6d36d6f` reran `tests.test_artifacts.ArtifactTests.test_public_exact_hydration_keeps_selectors_and_controls_unchanged`: passed/10.870s. No production correction or unittest skip. Logical modes were checked without claiming POSIX permission evidence on Windows. The later MASK-0036 stage changes one lock guard expectation; that changed method remains for the engine native milestone.

Both disposable native checkouts (`mask-native-driver-6_3rql1g-2zcsbrrm` and `mask-native-driver-6_3rql1g-dzj59o9r` beneath example's Temp) were removed after clean Git status. Shared implement-rfc `project_config.py --repo-root` validated each checkout. Owner clone and retained station were untouched. Logs consumed here; only the reusable local native driver remains for later native checks.
