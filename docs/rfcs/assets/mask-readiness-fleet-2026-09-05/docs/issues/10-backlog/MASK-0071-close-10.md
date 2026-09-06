---
schema: "implement-rfc.card.v1"
id: "MASK-0071"
title: "Verify and close RFC-MASK-0010"
status: "Backlog"
rfcs: ["RFC-MASK-0010"]
depends_on: ["MASK-0041", "MASK-0042", "MASK-0043"]
closeout_for: ["RFC-MASK-0010"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "close-10", "stage": "C — portable composition", "provisional_id": true, "closeout": true}
---

# MASK-0071: Verify and close RFC-MASK-0010

Governing RFC: [RFC-MASK-0010](../../rfcs/RFC-MASK-0010-portable-selections-and-bundles.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Reconcile every acceptance criterion against direct evidence at the stated boundary. Capture the real pre-implementation RFC_BASE_SHA and actual implementation/handoff commits. Reuse unchanged focused results; run a broader integration/review only where combined risk warrants it. Keep unavailable native, host, real-device or upstream handoff rows open. Do not claim packet validation as product acceptance.

Own only: `docs/rfcs/RFC-MASK-0010-portable-selections-and-bundles.md`, `the corresponding live closeout card`, `current affected public contract docs`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0010-AC01: Export/import round-trips selections and exact content locks between different machine/home/source paths without including credentials, registry identities, journals or launchers.
- RFC-MASK-0010-AC02: Incremental and replace modes preserve their declared ownership scopes; exported all-agent behavior and optional frozen-agent behavior are explicit and tested.
- RFC-MASK-0010-AC03: Bundle expansion/refresh is deterministic, source-revision bound and stale-plan guarded; overlapping bundles/manual selections do not cause accidental removals.
- RFC-MASK-0010-AC04: Profile subscription/removal preserves local contributions and reports version/target conflicts, unapproved sources, unavailable artifacts and offline freshness honestly.
- RFC-MASK-0010-AC05: One public import-and-apply path bootstraps selected personal scope through normal validation/recovery, with native Windows/macOS focused tests and no internal-state editing.

Proposed direct checks (not executed by this packet):

- python -B scripts/verify_documentation.py --root .
- Only missing or invalidated direct acceptance checks for this RFC.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Durable closeout anchor

RFC_BASE_SHA: UNRECORDED — capture actual live pre-implementation commit before source changes.

Planned cards: MASK-0041, MASK-0042, MASK-0043.

Cross-repository handoff: unrecorded; attach only an actual upstream ID/revision when required.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0010-AC01 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0010-AC02 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0010-AC03 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0010-AC04 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0010-AC05 | Not recorded | Not run | Unrecorded |

Closeout review runtime: not run. A skipped required native/host/device check leaves the criterion open.
