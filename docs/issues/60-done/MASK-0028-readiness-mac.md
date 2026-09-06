---
schema: "implement-rfc.card.v1"
id: "MASK-0028"
title: "Verify native macOS workspace and host readiness"
status: "Done"
rfcs: ["RFC-MASK-0006"]
depends_on: ["MASK-0026", "MASK-0027"]
platforms: ["mac"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "readiness-mac", "stage": "A — first usable milestone", "provisional_id": false}
acceptance: [{"criterion":"RFC-MASK-0006-AC01","outcome":"pass","revision":"98c0f2e24666bcf0b50b11fd8f3973d80f2eaf9a","evidence":{"kind":"command","detail":"Native macOS launcher/prelaunch test passed on macOS 26.6.2 arm64, APFS, Python 3.14.7, Apple Git 2.50.1. Claude 2.1.260 and Codex 0.153.2 version invocations succeeded. Git lifecycle evidence reused from 2c3fd27; first-prompt loading is explicitly unverified with prelaunch fallback, not claimed. Windows is separately open."}},{"criterion":"RFC-MASK-0006-AC06","outcome":"pass","revision":"98c0f2e24666bcf0b50b11fd8f3973d80f2eaf9a","evidence":{"kind":"command","detail":"Native macOS launcher/prelaunch test passed on macOS 26.6.2 arm64, APFS, Python 3.14.7, Apple Git 2.50.1. Claude 2.1.260 and Codex 0.153.2 version invocations succeeded. Git lifecycle evidence reused from 2c3fd27; first-prompt loading is explicitly unverified with prelaunch fallback, not claimed. Windows is separately open."}},{"criterion":"RFC-MASK-0006-AC07","outcome":"pass","revision":"98c0f2e24666bcf0b50b11fd8f3973d80f2eaf9a","evidence":{"kind":"command","detail":"Native macOS launcher/prelaunch test passed on macOS 26.6.2 arm64, APFS, Python 3.14.7, Apple Git 2.50.1. Claude 2.1.260 and Codex 0.153.2 version invocations succeeded. Git lifecycle evidence reused from 2c3fd27; first-prompt loading is explicitly unverified with prelaunch fallback, not claimed. Windows is separately open."}}]
---

# MASK-0028: Verify native macOS workspace and host readiness

Governing RFC: [RFC-MASK-0006](../../rfcs/RFC-MASK-0006-automatic-workspace-readiness.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Use native macOS disposable roots for actual Git lifecycle and installed launcher paths. Observe first-prompt skill visibility for available Claude/Codex versions and strict-gate or warning behavior. Record unsupported/missing hosts accurately; do not turn fixture stdout into host-load evidence.

Own only: `tests/test_workspace_lifecycle.py`, `tests/test_host_integration.py`, `docs/development/readiness-acceptance.md (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0006-AC01: Actual clone, worktree add, branch switch, merge and manual-merge completion fixtures invoke integration and converge without a user executing apply; unsupported Git integration reports its coverage accurately.
- RFC-MASK-0006-AC06: Native Claude and Codex startup/worktree scenarios record actual versions and first-prompt discovery or an explicit fallback limitation; a warning-only adapter is not called a strict gate.
- RFC-MASK-0006-AC07: Native Windows and macOS readiness/launcher paths receive focused direct checks; worktree removal and unavailable-root handling preserve ownership and are independently tested.

Proposed direct checks (not executed by this packet):

- Run focused native readiness/launcher cases and record OS, filesystem, Git, interpreter and actual host versions.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.
