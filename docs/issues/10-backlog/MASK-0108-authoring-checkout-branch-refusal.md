---
schema: "implement-rfc.card.v1"
id: "MASK-0108"
title: "Refuse a wrong-branch authoring checkout with one typed code whether or not it has an origin"
status: "Backlog"
rfcs: []
depends_on: ["MASK-0100"]
priority: "P2"
metadata: {"origin":"RFC-MASK-0020 d2 follow-up candidate filed under mandate r2 (2026-09-13)","follow_up_of":"MASK-0099"}
---

# MASK-0108: Refuse a wrong-branch authoring checkout with one typed code whether or not it has an origin

## Evidence

[MASK-0099 execution record](../60-done/MASK-0099-machine-v3-and-tap-bootstrap.md#contract-notes-and-follow-up-candidates): a wrong-branch authoring checkout reports `source.identity_mismatch` when it has an origin and `source.detached` when it has none.

## Bounded work

Make every authoring-checkout observation — `tap add --checkout`, `source publish`, `source dev-link` and import destinations — report a branch other than the configured one with the same typed refusal, independent of whether an origin exists. Keep a detached HEAD distinct only where the current contract names it. Update the CLI contract where it names these codes.

## Acceptance

Through the public CLI with disposable checkouts, a wrong-branch checkout with an origin and one without produce the same code and exit, and write nothing. A detached checkout and a missing origin keep their documented codes.
