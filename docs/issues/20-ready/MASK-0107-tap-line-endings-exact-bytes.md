---
schema: "implement-rfc.card.v1"
id: "MASK-0107"
title: "Keep exact bytes on taps unless line-ending conversion is opted in at tap registration"
status: "Ready"
rfcs: []
depends_on: ["MASK-0100", "MASK-0101"]
priority: "P1"
metadata: {"origin":"RFC-MASK-0020 owner decision, mandate r2 (2026-09-13)","follow_up_of":"MASK-0099","sequenced_before":["MASK-0104","MASK-0105"]}
---

# MASK-0107: Keep exact bytes on taps unless line-ending conversion is opted in at tap registration

Owner decision (September 13, 2026, run `mask-rfc0020-2026-09-12-a`, mandate revision r2, verbatim): "we should disable autocrlf on taps by default unless explicitly requested keeping exact bytes and only if a user explicitly opts in during tap registration should wee use autocrlf true". Filing was authorized with "sure file"; implementation is not restricted (r3).

## Evidence

[MASK-0099 execution record](../60-done/MASK-0099-machine-v3-and-tap-bootstrap.md#contract-notes-and-follow-up-candidates): under `core.autocrlf=true`, `source publish` hashes working bytes without filters, so it republishes LF blobs as CRLF. Tests now disable conversion by hand (for example a `* -text` publisher attribute). The owner's Windows machine uses `core.autocrlf=true`.

## Objective and owned paths

Tap registration, catalog entry, and every MASK Git operation on a tap's cache or approved authoring checkout: `mask_sources.py` (binding, `tap add`, publication), `mask_provenance.py` (working payloads), `mask_pinned.py` (dev-link observation), `schemas/machine-v3.schema.json`, the CLI contract and capabilities, and focused tests.

## Bounded work

- By default, a tap keeps exact bytes. MASK disables Git line-ending conversion for its operations on that tap and for its authoring checkout, so published blobs, development payloads and locked payload digests agree.
- Only an explicit opt-in at `tap add` enables `core.autocrlf` for that tap. The opt-in is recorded in the catalog entry and disclosed in output.
- Existing v3 entries without the field mean exact bytes. `doctor --migrate` writes the default.
- Record the amendment to the RFC-MASK-0020 tap entry shape in the RFC and the machine v3 schema.

## Acceptance

On a host whose Git configuration has `core.autocrlf=true`:
- For a tap added without the opt-in, `source publish` of an unchanged LF package reports no change, and a changed file is published with its exact bytes.
- `source dev-link` of an unchanged package observes the locked payload digest.
- With the opt-in, conversion follows `core.autocrlf=true` and is disclosed.
- Configurations written before this card keep working.
- The machine v3 schema, CLI contract, help and capabilities describe the policy.

## Sequencing

MASK-0104 (native real-package qualification) and MASK-0105 (owner machine migration) depend on this card. Both run on the owner's `core.autocrlf=true` Windows host and should exercise the final byte policy.
