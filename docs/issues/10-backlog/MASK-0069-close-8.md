---
schema: "implement-rfc.card.v1"
id: "MASK-0069"
title: "Verify and close RFC-MASK-0008"
status: "Backlog"
rfcs: ["RFC-MASK-0008"]
depends_on: ["MASK-0034", "MASK-0035", "MASK-0036", "MASK-0037"]
closeout_for: ["RFC-MASK-0008"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "close-8", "stage": "B — reproducible content", "provisional_id": false, "closeout": true}
---

# MASK-0069: Verify and close RFC-MASK-0008

Governing RFC: [RFC-MASK-0008](../../rfcs/RFC-MASK-0008-pinned-artifacts-and-recovery.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Reconcile every acceptance criterion against direct evidence at the stated boundary. Capture the real pre-implementation RFC_BASE_SHA and actual implementation/handoff commits. Reuse unchanged focused results; run a broader integration/review only where combined risk warrants it. Keep unavailable native, host, real-device or upstream handoff rows open. Do not claim packet validation as product acceptance.

Own only: `docs/rfcs/RFC-MASK-0008-pinned-artifacts-and-recovery.md`, `the corresponding live closeout card`, `current affected public contract docs`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0008-AC01: Two worktrees simultaneously use distinct immutable versions of one skill, and source authoring/ref movement changes neither deployment until an explicit selected update.
- RFC-MASK-0008-AC02: Locks reproduce raw package bytes across fixture machines; digest, package path, source identity, executable mode, malformed lock and moved-ref errors fail closed.
- RFC-MASK-0008-AC03: Ensure restores available exact artifacts, optionally hydrates only approved locked content, never resolves latest or rewrites lockfiles, and reports unavailable exact commits honestly.
- RFC-MASK-0008-AC04: Planner/executor/adoption/recovery correctly retarget an unchanged owned legacy or old-artifact link to a new artifact and preserve collisions, rather than retaining the old target.
- RFC-MASK-0008-AC05: Interruptions before/after lock, link and state effects preserve bounded v3 recovery; configuration/state migrations preserve exact legacy rollback bytes and reject concurrent edits.
- RFC-MASK-0008-AC06: Explicit migration covers project and personal consumers, dirty/unborn sources, old pending journals, schema-incompatible old programs, and direct-entrypoint escape paths.
- RFC-MASK-0008-AC07: Cache preparation, retention, dev-link exceptions and scoped publishing cannot silently alter other consumers, delete authoring history or claim atomicity across readers/devices.

Proposed direct checks (not executed by this packet):

- python -B scripts/verify_documentation.py --root .
- Only missing or invalidated direct acceptance checks for this RFC.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Durable closeout anchor

RFC_BASE_SHA: 9dc90df45febf2a6e048ace60a4ac959807aaaf6

Planned cards: MASK-0034, MASK-0035, MASK-0036, MASK-0037.

Cross-repository handoff: unrecorded; attach only an actual upstream ID/revision when required.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0008-AC01 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0008-AC02 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0008-AC03 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0008-AC04 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0008-AC05 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0008-AC06 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0008-AC07 | Not recorded | Not run | Unrecorded |

Closeout review runtime: not run. A skipped required native/host/device check leaves the criterion open.

## Implementation progress

MASK-0034 model/resolver source: `c5a359f` (Done card records focused checks and corrections). MASK-0035 store/exact-hydration source: `d17a607` (Done card records 17 passing focused methods plus affected/new checks). These supply bounded lock/raw-artifact evidence, not full RFC acceptance. MASK-0036 now owns activation/recovery and unlocked readiness preparation; MASK-0037 owns selected migration/update/dev-link/publishing. Native pinned-engine/targeting checks remain planned at the coherent milestone; do not repeat unchanged RFC-0007 source/import native results.
