---
schema: "implement-rfc.card.v1"
id: "MASK-0056"
title: "Add optional SDK-based MCP management facade"
status: "Backlog"
rfcs: ["RFC-MASK-0014"]
depends_on: ["MASK-0074"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "mcp-service", "stage": "E — optional interface extension", "provisional_id": false}
---

# MASK-0056: Add optional SDK-based MCP management facade

Governing RFC: [RFC-MASK-0014](../../rfcs/RFC-MASK-0014-optional-mcp-management-facade.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Pin an official supported SDK at implementation, keep it out of core dependencies, and expose narrow typed management tools over the same service model. Bind local authority and plan IDs; never add raw shell/credential access or implicit network listeners.

Own only: `optional/mcp/* (new)`, `tests/test_mcp_facade.py (new)`, `optional dependency manifest`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0014-AC01: Optional facade installation does not alter core runtime requirements and advertises only implemented tools/protocol capabilities.
- RFC-MASK-0014-AC02: Tool operations produce the same selections/plans/effects/errors as the CLI and cannot bypass scope/source/device authorization, recovery or ownership checks.
- RFC-MASK-0014-AC03: Protocol negotiation, malformed inputs, output separation, bounded content and secret redaction pass direct client/fixture checks using the selected SDK.

Proposed direct checks (not executed by this packet):

- Run the optional SDK protocol test suite plus CLI/facade parity scenarios.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
