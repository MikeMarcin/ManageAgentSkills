---
schema: "implement-rfc.card.v1"
id: "MASK-0033"
title: "Harden passive package acquisition and plain-skill boundaries"
status: "In Progress"
rfcs: ["RFC-MASK-0007"]
depends_on: ["MASK-0031"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "package-guards", "stage": "B — source foundation", "provisional_id": false}
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

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.

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
