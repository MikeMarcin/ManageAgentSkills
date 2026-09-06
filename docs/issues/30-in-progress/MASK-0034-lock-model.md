---
schema: "implement-rfc.card.v1"
id: "MASK-0034"
title: "Implement portable v2 selections and exact resolution locks"
status: "In Progress"
rfcs: ["RFC-MASK-0008"]
depends_on: ["MASK-0068"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "lock-model", "stage": "B — reproducible content", "provisional_id": false}
---

# MASK-0034: Implement portable v2 selections and exact resolution locks

Governing RFC: [RFC-MASK-0008](../../rfcs/RFC-MASK-0008-pinned-artifacts-and-recovery.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Implement closed normalized selection/lock models and a commit/ref resolver with full source/path/object identities. Preserve all selected package resolutions across platforms. Target fields follow RFC0009 and must not be advertised operationally until implemented. Missing/stale locks block v2 ensure; refresh stays explicit and cached-ref dry runs stay offline.

Own only: `mask_resolve.py (new)`, `mask_core.py`, `schemas/project-v2.schema.json (new)`, `schemas/lock-v1.schema.json (new)`, `tests/test_locks.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0008-AC01: Two worktrees simultaneously use distinct immutable versions of one skill, and source authoring/ref movement changes neither deployment until an explicit selected update.
- RFC-MASK-0008-AC02: Locks reproduce raw package bytes across fixture machines; digest, package path, source identity, executable mode, malformed lock and moved-ref errors fail closed.
- RFC-MASK-0008-AC03: Ensure restores available exact artifacts, optionally hydrates only approved locked content, never resolves latest or rewrites lockfiles, and reports unavailable exact commits honestly.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_locks tests.test_cli_protocol

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.

## Bounded implementation plan

After RFC-0007 closes, implement the normalized closed selection-v2 and lock-v1
models, explicit cached-only `mask lock --project/--user [--refresh] [--skill ...]`,
and exact full-commit resolution through the approved source catalog and passive
payload validator. Lock all bindings, including currently inapplicable ones.
Canonical serialization rejects duplicate/unknown fields, floats, unsafe integers
and invalid Unicode; normalize semantic sets and document default values.

Bind selection digest, approved repository identity/layout, exact package path,
object format/full commit, selector and raw payload/metadata/provenance digests.
Retain an existing coherent resolution until explicit refresh; reject moved tags
and non-fast-forward ref rewrites unless an explicit bounded rebind option is
selected. No network on lock or preview; missing cached objects report resolution
required. File-source fixtures remain explicitly machine-local, never portable
repository claims.

Extend ownership to the public CLI registrar/dispatcher, project/user schema
version dispatch, runtime module inventory and current docs. Existing legacy
consumer operations must fail closed on unsupported v2 deployment instead of
iterating binding objects as v1 IDs. Missing/stale v2 locks receive precise
errors. Artifact deployment, state migration and effective per-binding targeting
remain on MASK-0035/0036/0037 and RFC-0009; do not advertise them early.

Focused public checks cover canonical order and malformed inputs, exact SHA-1/
SHA-256/path identity, raw CRLF/executable supporting bytes, source approval,
missing/stale lock handling, selected refresh/ref-rebind refusal, unchanged refs
and source movement leaving a lock unchanged, and observational previews.
