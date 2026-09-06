---
id: "RFC-MASK-0014"
title: "Optional MCP facade over the MASK management API"
status: "Proposed"
owner: "MikeMarcin"
created: "2026-09-05"
---

# RFC-MASK-0014: Optional MCP facade over the MASK management API

**Delivery stage:** E — optional interface extension. **Packet status:** proposed implementation contract; no implementation or acceptance is claimed.

**Predecessors:** RFC-MASK-0013.

The new behavior below explicitly extends the historical v1 scope. Preserve settled RFCs 0001–0005; update current architecture/user documentation only when the relevant implementation ships. See [source reconciliation](../design/SOURCE-RECONCILIATION.md), [shared contracts](../design/CONTRACTS.md), and [references](../design/REFERENCES.md).

## Decision and scope

Claude and Codex can already drive a deterministic CLI; no MCP server is required for workspace readiness or fleet installation. Offer an optional stdio MCP facade for clients that prefer discoverable structured tools. It exposes MASK management, not an installer for arbitrary third-party MCP servers and not a new execution engine.

Keep this implementation separately installable/enabled. Core local/fleet capability does not depend on the MCP SDK or a hosted endpoint. Use the official maintained SDK selected and pinned at implementation time; do not hand-roll protocol framing, assume a remembered protocol version, or add the SDK to the core runtime's mandatory dependencies. [E10]

## Tool surface

Expose a small set of intent-level tools: capabilities, inspect selection, where-used, resolve install request, preview change, apply approved change, operation status, and report. These call the same typed internal service/public result model as the CLI. Do not expose raw shell, arbitrary Git, credential readback, arbitrary filesystem writes, or “force” variants.

`mask mcp serve --stdio` owns its process lifetime. stdout is MCP protocol only; diagnostics go to bounded redacted stderr. Start no TCP listener by default, and do not enable it implicitly while importing a skill. The bootstrap/runtime remains independent of the managed skill payload.

MCP tool annotations describe effects for UX only. Local MASK policy—not a tool's `readOnlyHint`, a model-supplied confirmation boolean, or package text—enforces authority. A result of `resolve` may include an untrusted description from upstream; it must remain labelled data and cannot change the requested action, identity, scope or device set.

## Authorization and previews

For enrolled owner use, the facade runs under a previously selected local profile: permitted sources, roots, scopes, devices and allowed mutations. It cannot grant itself wider authority. Meaningful new source enrollment/publishing remains a separate explicit operation or owner-delegated policy.

A preview produces a plan/intent ID bound to actor, request digest, scope, source and resolved artifacts, expiry and local observed generation. Application revalidates current filesystem/policy state exactly as the CLI. The facade cannot rely solely on an LLM echoing a plan hash as proof of human approval; standing delegated policy or an actual external user action establishes permission.

Avoid imposing a preview/apply/doctor round-trip on every deterministic ensure or previously authorized additive install. The facade may expose a single high-level install operation that internally prepares and applies under policy, returning the same report/operation ID. New authority decisions stay explicit without becoming perpetual ceremony.

## Progress and cancellation

Use protocol-supported progress/cancellation only after verifying the actual SDK/host contract. A disconnect or cancellation cannot undo an already committed local or remote change. Return/persist operation IDs and let a later connection query receipts. A terminated stdio process does not promise future notifications; durable fleet runners are RFC-MASK-0013, not hidden background work inside this facade.

Returned content is compact and paginated, with optional local report references. Never return secret values, full private catalogs or transcripts as incidental debugging. Detailed content reading is an explicit observational request with the same privacy limits as the CLI.

## Installation and verification

Install the optional adapter by its explicitly named package/module, not an unrelated registry package named `mask`. Pin dependency versions and record their licenses/source provenance. Bind the configured host integration to a known interpreter/entrypoint with owned configuration entries and support removal that preserves unrelated MCP entries. Native host trust/consent is not bypassed.

Test protocol initialization/version negotiation, malformed request schema, parity with CLI outcomes, output separation, authority failure, cancellation/unknown remote outcome and reconnect status. Record one actual Claude and one actual Codex client integration when available; SDK unit tests alone cannot prove client UI behavior.

## Acceptance criteria

- **RFC-MASK-0014-AC01** — Optional facade installation does not alter core runtime requirements and advertises only implemented tools/protocol capabilities.
- **RFC-MASK-0014-AC02** — Tool operations produce the same selections/plans/effects/errors as the CLI and cannot bypass scope/source/device authorization, recovery or ownership checks.
- **RFC-MASK-0014-AC03** — Protocol negotiation, malformed inputs, output separation, bounded content and secret redaction pass direct client/fixture checks using the selected SDK.
- **RFC-MASK-0014-AC04** — Cancellation/disconnect/reconnect preserves durable operation truthfulness, and actual supported-client discovery/tool invocation is recorded before claiming host support.
