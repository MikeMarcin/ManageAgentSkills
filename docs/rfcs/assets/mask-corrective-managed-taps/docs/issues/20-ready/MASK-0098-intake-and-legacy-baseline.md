---
schema: "implement-rfc.card.v1"
id: "MASK-0098"
title: "Record baseline and build the legacy machine fixture"
status: "Ready"
rfcs: ["RFC-MASK-0020"]
depends_on: []
priority: "P1"
metadata: {"packet": "mask-corrective-managed-taps", "provisional_id": true, "packet_key": "intake-and-legacy-baseline"}
---

# MASK-0098: Record baseline and build the legacy machine fixture

## Objective and owned paths

Intake, the live RFC and index rows, new cards, `tests/legacy_support.py`, `tests/test_legacy_baseline.py` and `docs/development/tap-cutover-baseline.md`. The integrator owns allocation and reservations; no unrelated tracker history changes.

## Bounded work

Record the real pre-implementation revision in the closeout. Capture the current behavior as evidence through the public CLI: `init --source` creates a v1 machine, `install` links `<consumer>/.claude/skills/<id>` and `<consumer>/.agents/skills/<id>` to `<clone>/skills/<id>`, `source migrate` still binds the clone, and pinned `update` does not fetch. Write a schema-true legacy fixture builder that produces v1 and v2 machines with mode-less records, v1 declarations and real directory symlinks, and assert that the current parsers accept every fixture byte so later doctor tests migrate exactly what old MASK wrote.

## Acceptance

A v1 machine fixture, a v2 machine fixture (legacy binding plus one extra tap), a legacy project, a legacy personal scope and an unregistered v1 declaration exist as reusable starting states. Each recorded defect names its command and the observed link target. The fixture builder writes files that `mask_core.config` and `mask_core.state` accept unchanged. No fixture pre-migrates, pre-fetches or pre-registers what a later card is meant to prove.

Criterion coverage: RFC-MASK-0020-AC04, RFC-MASK-0020-AC08.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary (subprocess argv, exit code, JSON stdout, stderr,
filesystem and Git effects). Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Not started. Claim the live remapped card before edits. No code implementation,
native result, host loading, user approval or migration of a real machine is
asserted by this card's existence.
