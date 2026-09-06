---
schema: "implement-rfc.card.v1"
id: "MASK-0070"
title: "Verify and close RFC-MASK-0009"
status: "Backlog"
rfcs: ["RFC-MASK-0009"]
depends_on: ["MASK-0038", "MASK-0039", "MASK-0040"]
closeout_for: ["RFC-MASK-0009"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "close-9", "stage": "B — selection semantics", "provisional_id": true, "closeout": true}
---

# MASK-0070: Verify and close RFC-MASK-0009

Governing RFC: [RFC-MASK-0009](../../rfcs/RFC-MASK-0009-scope-agent-targeting-and-compatibility.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Reconcile every acceptance criterion against direct evidence at the stated boundary. Capture the real pre-implementation RFC_BASE_SHA and actual implementation/handoff commits. Reuse unchanged focused results; run a broader integration/review only where combined risk warrants it. Keep unavailable native, host, real-device or upstream handoff rows open. Do not claim packet validation as product acceptance.

Own only: `docs/rfcs/RFC-MASK-0009-scope-agent-targeting-and-compatibility.md`, `the corresponding live closeout card`, `current affected public contract docs`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0009-AC01: The same skill has independently configurable personal and project agent sets, with new selections defaulting to all supported/enabled agents and no executable-detection side effects.
- RFC-MASK-0009-AC02: V1 migration preserves explicit and inherited target behavior; per-skill edits/locks/plans remain guarded and no-op stable.
- RFC-MASK-0009-AC03: Generic, absent and agent/platform-specific metadata produce distinct truthful reports; explicit incompatibilities block, and conditional/inapplicable bindings are not called installed.
- RFC-MASK-0009-AC04: Multi-source name conflicts, conflicting profiles and user/project duplicate names are explained without overwriting content, silently renaming packages or assuming host precedence.
- RFC-MASK-0009-AC05: A single adapter contract drives paths/capabilities/validation, and existing native Claude/Codex scope tests cover the change; additional agents stay unadvertised until independently proven.

Proposed direct checks (not executed by this packet):

- python -B scripts/verify_documentation.py --root .
- Only missing or invalidated direct acceptance checks for this RFC.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Durable closeout anchor

RFC_BASE_SHA: UNRECORDED — capture actual live pre-implementation commit before source changes.

Planned cards: MASK-0038, MASK-0039, MASK-0040.

Cross-repository handoff: unrecorded; attach only an actual upstream ID/revision when required.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0009-AC01 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0009-AC02 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0009-AC03 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0009-AC04 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0009-AC05 | Not recorded | Not run | Unrecorded |

Closeout review runtime: not run. A skipped required native/host/device check leaves the criterion open.
