---
schema: "implement-rfc.card.v1"
id: "MASK-0104"
title: "Requalify the real AgentSkills package and legacy lab natively"
status: "Backlog"
rfcs: ["RFC-MASK-0020"]
depends_on: ["MASK-0101", "MASK-0102", "MASK-0103"]
priority: "P1"
metadata: {"packet": "mask-corrective-managed-taps", "provisional_id": true, "packet_key": "real-package-qualifier-on-taps"}
---

# MASK-0104: Requalify the real AgentSkills package and legacy lab natively

## Objective and owned paths

`scripts/qualify_real_package.py`, `docs/development/readiness-acceptance.md` and the recorded qualification reports.

## Bounded work

Replace `init --source` in the qualifier with `tap add agentskills <disposable upstream>`, create consumers with `install implement-rfc --project ROOT`, push a candidate to the disposable upstream and run `mask update`, and add a legacy-lab step that builds a v1 machine with `tests/legacy_support.py`, runs `doctor --check` (7), `doctor --migrate --dry-run`, `doctor --migrate`, `doctor --check` (0) and `update`. Run the qualifier on native Windows 11 and macOS and record both reports.

## Acceptance

The qualifier passes every step on both native platforms against the real AgentSkills repository as a tap, including the push-then-update and legacy-lab steps, with private `MASK_HOME`, `HOME` and `USERPROFILE`. Reports name the OS, Python, Git and MASK revisions actually exercised.

Criterion coverage: RFC-MASK-0020-AC01, RFC-MASK-0020-AC03, RFC-MASK-0020-AC04, RFC-MASK-0020-AC07.

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
