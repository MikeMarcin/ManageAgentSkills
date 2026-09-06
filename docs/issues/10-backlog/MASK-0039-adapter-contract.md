---
schema: "implement-rfc.card.v1"
id: "MASK-0039"
title: "Consolidate adapter metadata and reject deployment-name conflicts"
status: "Backlog"
rfcs: ["RFC-MASK-0009"]
depends_on: ["MASK-0038"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "adapter-contract", "stage": "B — selection semantics", "provisional_id": false}
---

# MASK-0039: Consolidate adapter metadata and reject deployment-name conflicts

Governing RFC: [RFC-MASK-0009](../../rfcs/RFC-MASK-0009-scope-agent-targeting-and-compatibility.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Drive paths/enums/capabilities/package-kind guard/discovery claims from one audited adapter contract. Detect source-name collisions per consumer/agent and explain scope shadowing without rewriting names. Test unknown future metadata separately from unsupported requested adapters; add no new supported agents.

Own only: `mask_adapters.py (new)`, `mask.py`, `mask_core.py`, `mask_fs.py`, `tests/test_adapters.py (new)`, `tests/test_selection_conflicts.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0009-AC04: Multi-source name conflicts, conflicting profiles and user/project duplicate names are explained without overwriting content, silently renaming packages or assuming host precedence.
- RFC-MASK-0009-AC05: A single adapter contract drives paths/capabilities/validation, and existing native Claude/Codex scope tests cover the change; additional agents stay unadvertised until independently proven.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_adapters tests.test_selection_conflicts tests.test_cli_protocol

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
