---
schema: "implement-rfc.card.v1"
id: "MASK-0110"
title: "Report a refusal after retained store preparation without claiming a partial consumer transaction"
status: "Ready"
rfcs: []
depends_on: ["MASK-0100"]
priority: "P2"
metadata: {"origin":"RFC-MASK-0020 d2 follow-up candidate filed under mandate r2 (2026-09-13)","follow_up_of":"MASK-0099"}
---

# MASK-0110: Report a refusal after retained store preparation without claiming a partial consumer transaction

## Evidence

[MASK-0099 execution record](../60-done/MASK-0099-machine-v3-and-tap-bootstrap.md#contract-notes-and-follow-up-candidates):
- A refused `apply --all` on a cold store reports `changed` with `transaction: partial`, because store preparation is retained.
- An unapproved manual `ensure` hydrates the store from the local cache before its consent refusal, so the refusal also reports `changed: true, transaction: partial`, although no link, registration, policy or project byte changed.

## Bounded work

When a command refuses before any consumer effect, but MASK-owned store or cache preparation was retained, report the retained preparation separately from the consumer transaction state. Apply the same rule to `apply`, `ensure`, `install` and `update`, and update the CLI contract result description.

## Acceptance

Through the public CLI:
- A refused `apply --all` on a cold store reports no consumer transaction and discloses the retained preparation.
- An unapproved manual `ensure` whose consent is declined reports no consumer transaction and discloses the retained preparation.
- In both cases no link, registration, policy or project byte changes.
- Commands that did apply consumer effects keep their current reporting.
