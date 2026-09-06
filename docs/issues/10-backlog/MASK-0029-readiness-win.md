---
schema: "implement-rfc.card.v1"
id: "MASK-0029"
title: "Verify native Windows workspace and host readiness"
status: "Backlog"
rfcs: ["RFC-MASK-0006"]
depends_on: ["MASK-0026", "MASK-0027"]
platforms: ["win"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "readiness-win", "stage": "A — first usable milestone", "provisional_id": false}
---

# MASK-0029: Verify native Windows workspace and host readiness

Governing RFC: [RFC-MASK-0006](../../rfcs/RFC-MASK-0006-automatic-workspace-readiness.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Exercise native Windows directory links, missing privilege handling, spaced/Unicode paths, Git hook execution and host startup paths. Do not use WSL as acceptance or alter privileges. Record real installed hosts and loading limitations, retaining an open criterion when unavailable.

Own only: `tests/test_workspace_lifecycle.py`, `tests/test_host_integration.py`, `tests/test_launcher.py`, `docs/development/readiness-acceptance.md`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0006-AC01: Actual clone, worktree add, branch switch, merge and manual-merge completion fixtures invoke integration and converge without a user executing apply; unsupported Git integration reports its coverage accurately.
- RFC-MASK-0006-AC06: Native Claude and Codex startup/worktree scenarios record actual versions and first-prompt discovery or an explicit fallback limitation; a warning-only adapter is not called a strict gate.
- RFC-MASK-0006-AC07: Native Windows and macOS readiness/launcher paths receive focused direct checks; worktree removal and unavailable-root handling preserve ownership and are independently tested.

Proposed direct checks (not executed by this packet):

- Run focused native readiness/launcher cases with actual Windows Git/Python/host versions and no unrelated user directories.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
