---
schema: "implement-rfc.card.v1"
id: "MASK-0027"
title: "Add Claude and Codex startup adapters and prelaunch fallback"
status: "Backlog"
rfcs: ["RFC-MASK-0006"]
depends_on: ["MASK-0025"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "host-integration", "stage": "A — first usable milestone", "provisional_id": true}
---

# MASK-0027: Add Claude and Codex startup adapters and prelaunch fallback

Governing RFC: [RFC-MASK-0006](../../rfcs/RFC-MASK-0006-automatic-workspace-readiness.md). IDs are packet-local until the main integrator imports/reserves them.

## Objective and owned paths

Use installed runtime entrypoints outside managed skills. Preserve host settings and trust flows; implement host-specific output/discovery behavior with explicit gate-versus-warning capability. Include Codex worktree setup integration and a fixed argv prelaunch wrapper. Host startup can inspect already registered personal scope without giving the project authority to create it.

Own only: `mask_integration.py`, `mask.py`, `tests/test_host_integration.py (new)`, `docs/architecture/cli-contract.md`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0006-AC02: Ensure combines authorization, registration and selected-scope reconciliation through the existing safety engine; unchanged runs preserve managed bytes/generation and perform no unrelated scans.
- RFC-MASK-0006-AC05: Owned hook installation/removal preserves unrelated hooks/settings, suppresses configured and directory hooks for MASK internal Git commands, and prevents recursion.
- RFC-MASK-0006-AC06: Native Claude and Codex startup/worktree scenarios record actual versions and first-prompt discovery or an explicit fallback limitation; a warning-only adapter is not called a strict gate.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_host_integration tests.test_launcher
- Fixture hook protocol output must match the selected documented host contract; native loading evidence follows.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
