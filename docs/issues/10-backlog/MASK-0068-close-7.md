---
schema: "implement-rfc.card.v1"
id: "MASK-0068"
title: "Verify and close RFC-MASK-0007"
status: "Backlog"
rfcs: ["RFC-MASK-0007"]
depends_on: ["MASK-0030", "MASK-0031", "MASK-0032", "MASK-0033"]
closeout_for: ["RFC-MASK-0007"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "close-7", "stage": "B — source foundation", "provisional_id": false, "closeout": true}
---

# MASK-0068: Verify and close RFC-MASK-0007

Governing RFC: [RFC-MASK-0007](../../rfcs/RFC-MASK-0007-sources-imports-and-provenance.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Reconcile every acceptance criterion against direct evidence at the stated boundary. Capture the real pre-implementation RFC_BASE_SHA and actual implementation/handoff commits. Reuse unchanged focused results; run a broader integration/review only where combined risk warrants it. Keep unavailable native, host, real-device or upstream handoff rows open. Do not claim packet validation as product acceptance.

Own only: `docs/rfcs/RFC-MASK-0007-sources-imports-and-provenance.md`, `the corresponding live closeout card`, `current affected public contract docs`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0007-AC01: Two private/public-style local bare remotes expose independent taps and nested/root packages; name ambiguity, path/ref ambiguity and conflicting aliases are actionable rather than silently selected.
- RFC-MASK-0007-AC02: Source identity checks bind the approved repository and transport policy, not just the basename; credential-bearing/unsupported URLs and unapproved redirects refuse without leaking secrets.
- RFC-MASK-0007-AC03: Copy import preserves byte provenance and notices, refuses existing unrelated destinations, records local adaptations, and performs no commit/push unless separately authorized.
- RFC-MASK-0007-AC04: Adversarial package fixtures cannot traverse paths, introduce special entries, run hooks/filters/package scripts, silently activate a plugin, or bypass bounded resource limits.
- RFC-MASK-0007-AC05: Source lifecycle and legacy-config migration preserve current ownership and old declarations; removing a referenced source refuses and reads/dry-runs remain observational.
- RFC-MASK-0007-AC06: Public CLI/capabilities describe resolution, catalog-only addition, mutation/network boundaries and provenance verification levels with deterministic errors.

Proposed direct checks (not executed by this packet):

- python -B scripts/verify_documentation.py --root .
- Only missing or invalidated direct acceptance checks for this RFC.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Durable closeout anchor

RFC_BASE_SHA: 9dc90df45febf2a6e048ace60a4ac959807aaaf6

Planned cards: MASK-0030, MASK-0031, MASK-0032, MASK-0033.

Cross-repository handoff: unrecorded; attach only an actual upstream ID/revision when required.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0007-AC01 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0007-AC02 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0007-AC03 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0007-AC04 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0007-AC05 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0007-AC06 | Not recorded | Not run | Unrecorded |

Closeout review runtime: not run. A skipped required native/host/device check leaves the criterion open.
