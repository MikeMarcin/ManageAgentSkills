---
schema: "implement-rfc.card.v1"
id: "MASK-0052"
title: "Compose one-request copy or tap installation and fan-out"
status: "Backlog"
rfcs: ["RFC-MASK-0013"]
depends_on: ["MASK-0051", "MASK-0068", "MASK-0072"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "fleet-install", "stage": "D — personal fleet workflow", "provisional_id": true}
---

# MASK-0052: Compose one-request copy or tap installation and fan-out

Governing RFC: [RFC-MASK-0013](../../rfcs/RFC-MASK-0013-fleet-rollouts-and-continuous-sync.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Resolve one input and import mode, freeze exact content/device/scope intent, prepare and publish selected copy/tap/profile effects with existing authority, and dispatch local engine operations. Preserve unrelated staged source work and profile/local contributions. No recurring manual mechanics or silent public scope expansion.

Own only: `mask_fleet.py`, `mask_sources.py`, `mask_control.py`, `tests/test_fleet_install.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0013-AC01: A single name-or-GitHub-URL fleet install request composes copy/tap resolution, exact locking, authorized source/control publication, deployment and a per-device report without manual internal-state edits.
- RFC-MASK-0013-AC02: Frozen device/scope sets, local contribution preservation and source/package identity prevent unexpected project edits, hidden source enrollment or skill-name ambiguity.
- RFC-MASK-0013-AC07: Failure between import/publication/remote apply/receipt steps is resumable and truthful, and reports preserve the difference between filesystem verification and host discovery.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_fleet_install tests.test_imports tests.test_profile_contributions

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
