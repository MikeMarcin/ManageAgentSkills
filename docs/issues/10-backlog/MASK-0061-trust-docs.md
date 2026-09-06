---
schema: "implement-rfc.card.v1"
id: "MASK-0061"
title: "Publish inspectable threat and effect boundaries for review"
status: "Backlog"
rfcs: ["RFC-MASK-0016"]
depends_on: ["MASK-0068", "MASK-0069", "MASK-0074"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "trust-docs", "stage": "E — stretch public assurance", "provisional_id": false}
---

# MASK-0061: Publish inspectable threat and effect boundaries for review

Governing RFC: [RFC-MASK-0016](../../rfcs/RFC-MASK-0016-public-trust-and-supply-chain-hardening.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Document actual authority, threat coverage/noncoverage, optional providers and no-telemetry default. Reuse core security tests and expose observational dirty/unsigned/unverified trust facts without a safety badge. Publication of the repository is not implied.

Own only: `SECURITY.md (new)`, `docs/security/* (new)`, `mask_report.py`, `tests/test_trust_report.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0016-AC01: Threat/effect documentation distinguishes integrity, authorization, deployment, host loading and content safety, with explicit non-goals and no universal safety claim.
- RFC-MASK-0016-AC02: Core boundary tests and provider/dependency inventory are reused in a compact trust report that labels dirty/unsigned/unverified conditions truthfully.

Proposed direct checks (not executed by this packet):

- Run trust-report/effect metadata consistency checks and focused previously changed security boundary tests only.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
