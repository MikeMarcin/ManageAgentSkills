---
schema: "implement-rfc.card.v1"
id: "MASK-0121"
title: "Make command output concise and report live progress"
status: "Ready"
rfcs: []
depends_on: []
priority: "P1"
metadata: {"milestone_plan":{"id":"human-output-progress","path":"docs/rfcs/plans/human-output-progress/milestone-plan.json"}}
---

# MASK-0121: Make command output concise and report live progress

Owner request: fix stale implement-rfc command instructions; improve human command
output with concise presentation and restrained color; eliminate unexplained
silence after approving upgrade. Continue direct execution in the current checkout.

Baseline: `4b70729d1ee03d9eeb423ce981c73f4919e58109`.

- AC1: Current implement-rfc instructions and public caller tests use supported
  commands and combined task review. Preserve explicitly tested old-program
  compatibility, not stale user-facing advice. Canonical AgentSkills source handoff.
- AC2: Human reviews group ordinary changes and setup by scope/skill, suppress
  internal store paths and repeated role diagnostics, and retain exact significant
  setup/replacement/deletion disclosures. Results distinguish completed, failed,
  unstarted and stale pre-operation observations truthfully.
- AC3: Human terminal operations show flushed phase/consumer/setup progress before
  slow work and elapsed activity during long phases, including after confirmation.
  JSON stays one clean result; redirected output and NO_COLOR stay plain;
  progress stops on errors, declines and interruption.
- AC4: Investigate the pasted partial-publication error without mutating live
  consumers; preserve useful failure cause in output and test any identified fix
  with disposable fixtures. Document unresolved recovery facts explicitly.
- AC5: Focused renderer and public CLI tests cover the changes, including real
  terminal progress/consent and safe control-character handling; current docs
  explain the human output contract.

Boundary: source, local commits and disposable fixtures. No push or live recovery,
consumer migration, setup approval or internal-state edits. Preserve unrelated
lockfile changes in both repositories. Direct primary acceptance; no delegation.
