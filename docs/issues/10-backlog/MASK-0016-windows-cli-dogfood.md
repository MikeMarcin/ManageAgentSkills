---
id: MASK-0016
title: Verify Windows launcher and agent CLI path
status: Backlog
rfc: RFC-MASK-0004
depends_on: ["MASK-0015"]
platform: windows
---

# MASK-0016: Verify Windows launcher and agent CLI path

## Objective and owned paths

Own native Windows launcher/end-to-end evidence and contained fixes.

## Bounded work

Execute the actual installed launcher with spaced paths, JSON success/refusal/no-op and exit-code propagation. Verify selected shared skill context through the actual directory links; record host discovery only if observed.

## Acceptance

Windows support is backed by direct native CLI/launcher results; unobserved Claude/Codex loading is not asserted.

## Focused verification

Native Windows focused `tests.test_launcher` and `tests.test_end_to_end`; reuse unchanged symlink safety results from MASK-0008.

## Run record

Not started. Record actual commands, outcomes and commits here. Read the live board before claiming. Never stage unrelated paths.
