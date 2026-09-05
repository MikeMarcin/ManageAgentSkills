---
id: MASK-0017
title: Verify macOS launcher and agent CLI path
status: Backlog
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

Not started. Record actual commands, outcomes and commits here. Read the live board before claiming. Never stage unrelated paths.
