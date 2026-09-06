---
schema: "implement-rfc.card.v1"
id: "MASK-0057"
title: "Verify optional client integration and cancellation semantics"
status: "Backlog"
rfcs: ["RFC-MASK-0014"]
depends_on: ["MASK-0056"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "mcp-hosts", "stage": "E — optional interface extension", "provisional_id": true}
---

# MASK-0057: Verify optional client integration and cancellation semantics

Governing RFC: [RFC-MASK-0014](../../rfcs/RFC-MASK-0014-optional-mcp-management-facade.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Record actual Claude/Codex tool discovery and trust-preserving configuration. Test disconnect/cancel/reconnect with durable fleet operation status. Never promise future results from a dead stdio process; keep missing client evidence open.

Own only: `optional/mcp/*`, `tests/test_mcp_facade.py`, `docs/development/mcp-acceptance.md (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0014-AC03: Protocol negotiation, malformed inputs, output separation, bounded content and secret redaction pass direct client/fixture checks using the selected SDK.
- RFC-MASK-0014-AC04: Cancellation/disconnect/reconnect preserves durable operation truthfulness, and actual supported-client discovery/tool invocation is recorded before claiming host support.

Proposed direct checks (not executed by this packet):

- Run direct selected client/SDK protocol and cancellation checks; name exact versions.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
