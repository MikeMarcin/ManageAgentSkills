---
schema: "implement-rfc.card.v1"
id: "MASK-0026"
title: "Install owned Git integrations and suppress internal hooks"
status: "Ready"
rfcs: ["RFC-MASK-0006"]
depends_on: ["MASK-0025"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "git-integration", "stage": "A — first usable milestone", "provisional_id": false}
---

# MASK-0026: Install owned Git integrations and suppress internal hooks

Governing RFC: [RFC-MASK-0006](../../rfcs/RFC-MASK-0006-automatic-workspace-readiness.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Probe named-hook capability in disposable Git config. Implement additive owned events plus a non-destructive legacy integration fallback and explicit coverage report. Bind launchers to fixed program/interpreter paths. Suppress configured and directory hooks for internal Git operations and cover recursion/ref transactions. Preserve existing hooks/config on enable/disable and explain post-operation failure semantics.

Own only: `mask_integration.py (new)`, `mask_core.py:git`, `mask_install.py`, `tests/test_git_integration.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0006-AC01: Actual clone, worktree add, branch switch, merge and manual-merge completion fixtures invoke integration and converge without a user executing apply; unsupported Git integration reports its coverage accurately.
- RFC-MASK-0006-AC05: Owned hook installation/removal preserves unrelated hooks/settings, suppresses configured and directory hooks for MASK internal Git commands, and prevents recursion.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_git_integration tests.test_subprocess_policy
- Run actual clone/switch/worktree/merge event fixtures on the available Git versions.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
