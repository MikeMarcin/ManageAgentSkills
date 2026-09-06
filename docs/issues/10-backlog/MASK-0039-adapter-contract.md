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

Own only: `mask_adapters.py (new)`, `mask.py`, `mask_core.py`, `mask_fs.py`, `mask_pinned.py`, `mask_selection.py`, bounded adapter-data integration in `mask_integration.py` and `mask_packages.py`, runtime inventory in `mask_install.py`/`tests/test_launcher.py`, current README/CLI documentation and affected schema enum parity, `tests/test_adapters.py (new)`, `tests/test_selection_conflicts.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0009-AC04: Multi-source name conflicts, conflicting profiles and user/project duplicate names are explained without overwriting content, silently renaming packages or assuming host precedence.
- RFC-MASK-0009-AC05: A single adapter contract drives paths/capabilities/validation, and existing native Claude/Codex scope tests cover the change; additional agents stay unadvertised until independently proven.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_adapters tests.test_selection_conflicts tests.test_cli_protocol

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Dependency MASK-0038 is Done at 4291d5d; source c2fa4962f06349d33169fae478b69b7f758e7bb4. Native acceptance remains MASK-0040. No implementation result is asserted for this slice.

## Bounded implementation decisions

One audited built-in adapter contract owns Claude/Codex IDs, project/user discovery paths, current supported native platform boundary, discovery/reload/gate claims, reserved names and package-kind hazards. Existing readiness evidence remains honest about host loading. Derive runtime paths/capabilities/validation from this data and test persisted schema enum parity. Unknown future publisher metadata is distinct from an unsupported requested adapter. No new adapters or executable plugins.

The pure attributed contribution seam merges identical coordinate/artifact positive target edges by union and retains every origin; absence or an ordinary explicit agent list is not a denial of another contribution. Different resolutions of the same coordinate refuse explicitly until a recorded deviation/override can resolve them; never choose last contribution. Different coordinates sharing an invocation name conflict only at a shared consumer/agent destination and explain both origins/digests. Disjoint agents/scopes are allowed. Report user/project duplicate names as shadowing without asserting host precedence or rewriting payloads. Public profile storage and bundle-local manual choices remain RFC-0010.

Focused checks: public two-source collision and disjoint-agent deployment, pure identical-union/conflicting-version contributions, public user/project shadow warning, adapter path/capability/schema/package-hazard parity and CLI protocol. Reuse existing native host evidence where unchanged; run the newly integrated native path once at MASK-0040. One shared-checkout source writer; primary alone stages/commits/changes the board.
