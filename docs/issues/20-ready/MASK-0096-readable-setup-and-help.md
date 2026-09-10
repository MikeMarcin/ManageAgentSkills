---
schema: "implement-rfc.card.v1"
id: "MASK-0096"
title: "Stop futile setup retries and explain CLI tasks and failures"
status: "Ready"
rfcs: ["RFC-MASK-0018", "RFC-MASK-0019"]
depends_on: []
priority: "P1"
---

User-requested correction from the pasted SampleReview ensure/update output.
Baseline: e7c8466. Direct engineering authorized after the required workflow
preflight refused on this checkout's missing readiness approval.

One bounded milestone: prevent setup offers from promising to replace occupied,
unowned destinations; report failures grouped by consumer with actual file paths,
clear effects and actionable recovery; provide task help with scope explanations,
argument descriptions and runnable examples. Preserve JSON structure, ownership,
consent and unrelated changes. No consumer migration or approval changes.

Owned paths: mask_setup.py, mask_workflow.py, mask_present.py, mask.py,
tests/test_setup.py, tests/test_human_output.py, README.md and recovery guidance.
Acceptance: subprocess tests for the reproduced conflict and no repeated setup;
human multi-project errors identify each root; help explains everyday commands
and their scope; focused setup, presentation and parser checks pass.
