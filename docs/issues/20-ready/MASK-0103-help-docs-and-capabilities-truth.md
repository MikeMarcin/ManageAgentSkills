---
schema: "implement-rfc.card.v1"
id: "MASK-0103"
title: "Make help, docs and capabilities describe only the tap model"
status: "Ready"
rfcs: ["RFC-MASK-0020"]
depends_on: ["MASK-0100", "MASK-0101", "MASK-0102"]
priority: "P1"
metadata: {"packet":"mask-corrective-managed-taps","provisional_id":false,"packet_key":"help-docs-and-capabilities-truth","milestone_plan":{"id":"tap-only-deployment","path":"docs/rfcs/plans/tap-only-deployment/milestone-plan.json"}}
---

# MASK-0103: Make help, docs and capabilities describe only the tap model

Governing RFC: [RFC-MASK-0020](../../rfcs/RFC-MASK-0020-tap-only-deployment.md). Live IDs confirmed by the committed pack reservation `b92372f`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-managed-taps.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-managed-taps/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-managed-taps/ACCEPTANCE.md).

## Objective and owned paths

`mask_present.py`, `README.md`, `docs/guides/installation.md`, `docs/guides/sources-and-updates.md`, `docs/guides/migration-and-pins.md`, `docs/architecture/cli-contract.md`, `docs/architecture/state-and-recovery.md`, `docs/architecture/test-boundaries.md`, `AGENTS.md`, `.mask/skill-config/implement-rfc/project.md` where it names retired commands, `tests/test_human_output.py`, `tests/test_readme_journeys.py` and a new retired-spelling documentation test.

## Bounded work

Rewrite the start-here text, everyday table and command help for `init`, `tap add`, `install`, `update`, `source fetch` and `doctor --migrate`. Replace the local-clone installation journey with the tap bootstrap in README and the installation guide; rewrite the sources guide around fetching updates; turn the migration guide into migrating from a live checkout with an old-command table. Update the CLI contract inventory and the state/recovery architecture for `doctor.migrate`. Replay the README recipes through the public CLI.

## Acceptance

README recipes execute verbatim through the tap-first fixtures. Help output for every registered command renders and names no retired command. The documentation test finds the retired spellings only under `docs/rfcs/assets`, in historical RFC text and in the migration guide's old-command table. `capabilities` reflects the final command table.

Criterion coverage: RFC-MASK-0020-AC05, RFC-MASK-0020-AC06.

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
