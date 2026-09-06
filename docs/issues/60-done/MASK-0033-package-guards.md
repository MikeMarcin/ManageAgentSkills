---
schema: "implement-rfc.card.v1"
id: "MASK-0033"
title: "Harden passive package acquisition and plain-skill boundaries"
status: "Done"
rfcs: ["RFC-MASK-0007"]
depends_on: ["MASK-0031"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "package-guards", "stage": "B — source foundation", "provisional_id": false}
acceptance: [{"criterion":"MASK-0033/passive-payload","outcome":"pass","revision":"afd245d81489d436977e0f34cc115fa885c78b18","evidence":{"kind":"observation","detail":"Raw regular Git bytes, portable paths, passive frontmatter and known activation boundaries validated with synthetic adversarial public-path fixtures."}},{"criterion":"MASK-0033/resource-bounds","outcome":"pass","revision":"afd245d81489d436977e0f34cc115fa885c78b18","evidence":{"kind":"observation","detail":"Focused fixtures pass for pre-allocation size/count/depth and bounded process output/time; polled storage refusal preserves selected cursor and reports staging effects."}},{"criterion":"MASK-0033/native-containment","outcome":"pass","revision":"afd245d81489d436977e0f34cc115fa885c78b18","evidence":{"kind":"observation","detail":"Native Windows Job Object assignment and process-tree cleanup methods passed; corrected raw-Git-byte resource fixture passed at this revision."}},{"criterion":"MASK-0033/public-contract","outcome":"pass","revision":"afd245d81489d436977e0f34cc115fa885c78b18","evidence":{"kind":"observation","detail":"Public skill validation and capabilities expose payload validation and documented acquisition limits; existing source authority checks remain covered."}}]
---

# MASK-0033: Harden passive package acquisition and plain-skill boundaries

Governing RFC: [RFC-MASK-0007](../../rfcs/RFC-MASK-0007-sources-imports-and-provenance.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Validate resource bounds, regular entries, portable names, collision rules and known host plugin/activation markers. Read raw Git objects with filters/hooks suppressed. Reject unsupported LFS/submodules/metadata rather than execute helpers or strip content silently. Use synthetic malicious fixtures, not downloaded code execution.

Own only: `mask_sources.py`, `mask_core.py:package`, `mask_git.py`, `tests/test_import_safety.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0007-AC02: Source identity checks bind the approved repository and transport policy, not just the basename; credential-bearing/unsupported URLs and unapproved redirects refuse without leaking secrets.
- RFC-MASK-0007-AC04: Adversarial package fixtures cannot traverse paths, introduce special entries, run hooks/filters/package scripts, silently activate a plugin, or bypass bounded resource limits.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_import_safety tests.test_skill_catalog tests.test_subprocess_policy

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Implemented at `96b18ee3298b160e956ec2ce2a34c9439efc879d`; native fixture correction at `afd245d81489d436977e0f34cc115fa885c78b18`.

- macOS package/catalog/subprocess/source/discovery/launcher checks: 33 passed in 47.408s before final native/frontmatter additions. Final affected guard/subprocess/launcher set: 16 successful with one Windows-only skip in 29.913s; final frontmatter/subprocess checks: seven successful with one Windows-only skip in 15.016s. Final fetch-storage refusal check: one passed in 1.310s. `git diff --check` passed.
- Native Windows Python 3.14.6 / Git 2.55.0.windows.3 on ExampleWinHost: `tests.test_import_safety tests.test_subprocess_policy tests.test_launcher` ran 16 tests in 105.805s, with 15 methods passing and two failed assertions in one resource-limit fixture. The fixture incorrectly counted CRLF checkout bytes rather than raw Git object bytes; production's raw-byte count was correct. After correcting that measurement, the affected method passed on macOS (2.766s) and Windows (9.972s). Unchanged passing native methods include Job Object assignment refusal and real process-tree cleanup. No native skips.
- Acquisition has bounded time/output/object sizes and a polled cache-storage limit; storage may transiently overshoot between polls. The selected cursor advances only after post-fetch checks. No hard network-byte quota is asserted.
- Exact task roots were `C:/Users/example/AppData/Local/Temp/mask-guards-win-60ff62w0` and `/tmp/mask-guards-win-60ff62w0`. Native checkout was clean and removed; local transfer/log files were consumed into this record and removed. Tests used temporary fixtures; no station restart or modification to the owner's manual clone occurred.

These checks establish the passive payload/acquisition slice. Copy imports remain on MASK-0032; no fleet or host-load acceptance is asserted.

## Bounded implementation plan

Implement before copy imports so only validated passive payloads can reach new
curated paths. Extend owned paths to the shared bounded Git subprocess primitive
in `mask_core.py`, the CLI validation dispatcher in `mask.py`, and a new
`mask_packages.py` module if warranted (plus `mask_install.py`/launcher module
inventory and current docs). Git acquisition must cap command output before
allocation and stop/reap the process tree on size/time limits; fetch pack bytes
need an explicit bounded policy as well. Preserve the existing hook, auth and
process-tree contracts.

Expose one reusable frozen-object payload validator for later copy imports and
artifacts: exact regular file bytes and logical Git modes, per-file/cumulative
size, count/depth, portable path components/case/NFC collisions, LFS/submodule/
link/plugin/host-active rejection, and the existing frontmatter subset. Source
indexes should avoid enumerating unrelated large trees when exact package paths
are available. Public validation must exercise the chosen package path. No
package code or filter runs. Use only synthetic local Git fixtures.
