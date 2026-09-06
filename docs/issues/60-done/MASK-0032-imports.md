---
schema: "implement-rfc.card.v1"
id: "MASK-0032"
title: "Add curated copy imports with verifiable provenance"
status: "Done"
rfcs: ["RFC-MASK-0007"]
depends_on: ["MASK-0031"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "imports", "stage": "B — source foundation", "provisional_id": false}
acceptance: [{"criterion":"MASK-0032/copy-boundary","outcome":"pass","revision":"815fb060e6d51ffe034141275a62fd3d1a898c96","evidence":{"kind":"observation","detail":"Public fixture import preserves original raw payload and explicit notices, selected changed paths, unrelated staged bytes and HEAD; no default commit/push/index mutation."}},{"criterion":"MASK-0032/publication","outcome":"pass","revision":"815fb060e6d51ffe034141275a62fd3d1a898c96","evidence":{"kind":"observation","detail":"Native macOS and Windows no-replace publication refuses existing empty and case-aliased destinations; staged mutation/config changes refuse before effects."}},{"criterion":"MASK-0032/provenance","outcome":"pass","revision":"815fb060e6d51ffe034141275a62fd3d1a898c96","evidence":{"kind":"observation","detail":"Authoring and frozen-tap/root observations distinguish missing history, local/publisher assertions, independent upstream Git facts, mismatch and explicit adaptation records."}},{"criterion":"MASK-0032/public-contract","outcome":"pass","revision":"815fb060e6d51ffe034141275a62fd3d1a898c96","evidence":{"kind":"observation","detail":"CLI capabilities/docs expose network-capable import, offline preview, selection/plan guards and bounded provenance. Raw CRLF discovery regression and affected native import passed."}}]
---

# MASK-0032: Add curated copy imports with verifiable provenance

Governing RFC: [RFC-MASK-0007](../../rfcs/RFC-MASK-0007-sources-imports-and-provenance.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Prepare exact packages outside discovery, preserve notices and upstream coordinate/commit/digests, then write only selected new curated paths. Refuse unknown existing content. Record adaptation without guessing unknown history. Return changed paths without default commit/push; define the scoped publication seam for later fleet use.

Own only: `mask_sources.py`, `mask_provenance.py (new)`, `tests/test_imports.py (new)`, `tests/test_provenance.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0007-AC03: Copy import preserves byte provenance and notices, refuses existing unrelated destinations, records local adaptations, and performs no commit/push unless separately authorized.
- RFC-MASK-0007-AC06: Public CLI/capabilities describe resolution, catalog-only addition, mutation/network boundaries and provenance verification levels with deterministic errors.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_imports tests.test_provenance

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Implemented at `c45f771ca0cfcef280cc0f4c0726a9bc65f4266b`.

- `python3 -B -m unittest tests.test_imports tests.test_provenance tests.test_source_discovery tests.test_launcher`: 21 passed in 71.760s. The combined public-path fixture imports raw bytes and notices, preserves HEAD/index/unrelated staged work, commits only fixture data, fetches that curated repository as a tap, and independently checks upstream provenance.
- Subsequent affected import/provenance checks: 13 passed in 50.399s; case-collision plus launcher checks: three passed in 8.195s; final byte/index preservation and adaptation checks: two passed in 7.595s; final root-package/config-precondition checks: two passed in 6.829s. No macOS skips. Final diff, module and schema parsing checks passed.
- Primary review identified cached-tap/root-package provenance gaps and a stale-precondition window during staged hashing; corrected before this revision and covered by the affected checks.
- Native Windows Python 3.14.6 / Git 2.55.0.windows.3: `tests.test_imports tests.test_provenance` ran 14 methods in 177.030s. Thirteen passed; one exposed CRLF frontmatter name inference rejecting valid raw Git bytes. Production fix `815fb060e6d51ffe034141275a62fd3d1a898c96` adds CRLF recognition without rewriting payloads. The failing import method plus a new raw-CRLF public discovery/show/validate regression both passed on Windows in 11.710s. Local affected checks passed (two in 4.133s; final CRLF fixture in 2.480s). No native skips. Unchanged native passes include atomic empty-directory/case-collision refusal, raw byte/index preservation and provenance/adaptation checks.
- Native root was `C:/Users/example/AppData/Local/Temp/mask-native-driver-6_3rql1g-03nmm45j`; shared implement-rfc `project_config.py` validated its repository context. The clean native checkout and transfer directory were removed after verification. Transfer/log files were held in `/tmp/mask-native-driver-6_3rql1g`; only the temporary driver remains needed for later native prerequisite checks after logs are consumed.

No package code ran. Temporary local test fixtures/staging were cleaned. Windows logical execute modes are recorded separately from filesystem evidence; imports never set Git index mode bits. Notice naming conventions and unsupported no-replace filesystem refusal are explicit in the CLI contract. Default imports neither commit nor push and do not deploy to consumers.

## Bounded implementation plan

Use the now-implemented frozen payload validator from MASK-0033 before writing
curated content. Import only one explicit package into a new path in an approved
authoring checkout, with unchanged source/config/destination preconditions.
Stage outside discovery and publish without replacing an existing directory,
even an empty concurrent collision. A reusable no-replace directory primitive
may use documented native APIs; no unsafe overwrite/copy fallback.

Retain original upstream payload digest separately from any curated digest and
record adjacent notice incorporation explicitly. Provenance queries distinguish
verified object facts, local recorded assertions, absent history and observed
unrecorded adaptations. Never synthesize upstream provenance from a package ID.
Default import returns exact changed paths and makes no commit/push or index
sweep. Preserve unrelated staged edits. Public URL/ref/path resolution reuses
MASK-0031, and previews never fetch or stage.

Extend ownership to `mask.py` public commands, `mask_install.py`/launcher module
inventory, relevant schema and current docs; `mask_core.py` may hold the bounded
no-replace directory primitive. Import/publication is separate from deployment.
