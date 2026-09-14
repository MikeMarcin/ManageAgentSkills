---
schema: "implement-rfc.card.v1"
id: "MASK-0105"
title: "Migrate the owner's real machine and personal scope (attended)"
status: "In Progress"
rfcs: ["RFC-MASK-0020"]
depends_on: ["MASK-0102", "MASK-0103", "MASK-0107"]
priority: "P1"
metadata: {"packet":"mask-corrective-managed-taps","provisional_id":false,"packet_key":"owner-machine-migration-dogfood","milestone_plan":{"id":"tap-only-deployment","path":"docs/rfcs/plans/tap-only-deployment/milestone-plan.json"}}
---

# MASK-0105: Migrate the owner's real machine and personal scope (attended)

Governing RFC: [RFC-MASK-0020](../../rfcs/RFC-MASK-0020-tap-only-deployment.md). Live IDs confirmed by the committed pack reservation `b92372f`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-managed-taps.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-managed-taps/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-managed-taps/ACCEPTANCE.md).

## Objective and owned paths

`docs/development/tap-cutover-baseline.md` (evidence section) only. No source changes; any defect found returns to its owning card.

## Bounded work

With the owner present, run `mask doctor`, `mask doctor --migrate --dry-run` and `mask doctor --migrate` on the real v1 machine (`~/.mask`, source root `C:\code\git\AgentSkills`, empty registry), then `mask install implement-rfc --user`, `mask list --user`, `mask update` and `mask doctor --check`. Record the transcript, the resulting `config.json` shape (redacting nothing that is not secret) and the link targets. Do not reset or clean the clone.

## Acceptance

After migration `config.json` is v3 with the `agentskills` tap whose `authoring` is the clone path, `doctor --check` exits 0, personal links resolve under `MASK_HOME/store/v1/`, `update` fetches and no-ops, and the clone's HEAD, index and worktree are unchanged. The transcript is recorded in the baseline document.

Criterion coverage: RFC-MASK-0020-AC04, RFC-MASK-0020-AC07.

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
