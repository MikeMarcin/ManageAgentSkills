---
schema: "implement-rfc.card.v1"
id: "MASK-0055"
title: "Demonstrate real two-machine install and offline convergence"
status: "Backlog"
rfcs: ["RFC-MASK-0013"]
depends_on: ["MASK-0054", "MASK-0050"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "fleet-dogfood", "stage": "D — personal fleet workflow", "provisional_id": false}
---

# MASK-0055: Demonstrate real two-machine install and offline convergence

Governing RFC: [RFC-MASK-0013](../../rfcs/RFC-MASK-0013-fleet-rollouts-and-continuous-sync.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

After explicit selection/enrollment, demonstrate one URL copied to a curated source and one tap installed on distinct macOS/native-Windows devices. Include an offline target and later matching receipt, plus one controlled collision. Capture compact actual commands/revisions/outcomes; no test-only simulation can satisfy the real-device criterion.

Own only: `docs/development/fleet-native-acceptance.md`, `tests/test_fleet_install.py`, `docs/architecture/cli-contract.md`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0013-AC01: A single name-or-GitHub-URL fleet install request composes copy/tap resolution, exact locking, authorized source/control publication, deployment and a per-device report without manual internal-state edits.
- RFC-MASK-0013-AC04: Offline, unknown, incompatible, recovery-required, canceled and superseded devices are reported distinctly; incomplete rollouts never claim installed everywhere or reuse stale receipts.
- RFC-MASK-0013-AC06: Actual two-machine macOS/native-Windows rollout and offline catch-up evidence is recorded, or that acceptance stays open with the exact environmental limitation.
- RFC-MASK-0013-AC07: Failure between import/publication/remote apply/receipt steps is resumable and truthful, and reports preserve the difference between filesystem verification and host discovery.

Proposed direct checks (not executed by this packet):

- Record actual multi-device operation IDs, signed receipt revisions, device status and host-loading limitations.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
