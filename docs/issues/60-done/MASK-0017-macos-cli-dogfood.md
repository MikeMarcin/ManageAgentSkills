---
id: MASK-0017
title: Verify macOS launcher and agent CLI path
status: Done
rfc: RFC-MASK-0004
depends_on: ["MASK-0015"]
platform: macos
---

# MASK-0017: Verify macOS launcher and agent CLI path

## Objective and owned paths

Own native macOS launcher/end-to-end evidence and contained fixes.

## Bounded work

Execute the actual launcher with spaced paths, JSON success/refusal/no-op and exit propagation. Verify the two consumers' shared-context behavior and private source update scope.

## Acceptance

macOS support is backed by direct native results; a second runtime/provider is not invented as an unnecessary gate.

## Focused verification

Native macOS focused `tests.test_launcher` and `tests.test_end_to_end`; reuse unchanged safety results from MASK-0009.

## Run record

Native macOS 26.6.2 build 25G83 / Python 3.14.7: tests.test_end_to_end 2 PASS with explicit shared skill/context fixtures; actual launcher forwarding/exit/no-op/collision and PATH test PASS. Named ~/.local/bin/mask installed through self install after dry-run, discovered on existing PATH, repeated install no-op; invalid command exit 2. Actual apply --all converges and doctor --all --check healthy. Linked audit_board.py and resolver invoked in both repos: distinct mask/agent-skills contexts, same canonical asset root. Earlier safety and update checks reused. No agent UI load claim. Commit: this Done move.
