---
schema: "implement-rfc.card.v1"
id: "MASK-0121"
title: "Make command output concise and report live progress"
status: "Done"
rfcs: []
depends_on: []
priority: "P1"
metadata: {"milestone_plan":{"id":"human-output-progress","path":"docs/rfcs/plans/human-output-progress/milestone-plan.json"}}
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"84231dc9b4f3da1ca2c15a3d88c72fd18efd6c7b","evidence":{"kind":"observation","detail":"Current canonical skill instructions and public examples use the supported lifecycle, with tested old-program compatibility. AgentSkills fbd909de1fad209dab8f2fcec6baca9b27ce0bfd; two-consumer canonical scenario and 12 preflight checks pass. See docs/rfcs/plans/human-output-progress/verification.md."}},{"criterion":"AC2","outcome":"pass","revision":"84231dc9b4f3da1ca2c15a3d88c72fd18efd6c7b","evidence":{"kind":"observation","detail":"Human reviews/previews group ordinary changes and common setup while preserving exact replacement paths, script identity, interpreter and target roles. Partial setup reports use completed/incomplete/unstarted outcomes, not obsolete observations. Presentation and failure checks pass. See docs/rfcs/plans/human-output-progress/verification.md."}},{"criterion":"AC3","outcome":"pass","revision":"84231dc9b4f3da1ca2c15a3d88c72fd18efd6c7b","evidence":{"kind":"observation","detail":"A public pseudoterminal upgrade waits for an observed live heartbeat before releasing blocked setup; it completes successfully. JSON on a terminal is one clean document. Tests cover flushing, pause, shutdown, NO_COLOR and pipe behavior. See docs/rfcs/plans/human-output-progress/verification.md."}},{"criterion":"AC4","outcome":"pass","revision":"84231dc9b4f3da1ca2c15a3d88c72fd18efd6c7b","evidence":{"kind":"observation","detail":"Read-only journal investigation is recorded with uncertainty. Injected publication and rollback failures retain typed causes, root and schema-conforming failed actions with unknown effects. Existing live recovery remains unmodified. See docs/rfcs/plans/human-output-progress/verification.md."}},{"criterion":"AC5","outcome":"pass","revision":"84231dc9b4f3da1ca2c15a3d88c72fd18efd6c7b","evidence":{"kind":"observation","detail":"Final dedicated progress 7, presentation/help 14, failure/schema 5, launcher/re-exec 2 and source checks pass. Documentation gates report no violations. Intermediate failures and limits are preserved in the evidence document. See docs/rfcs/plans/human-output-progress/verification.md."}}]
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

## Closeout

MASK implementation: `84231dc9b4f3da1ca2c15a3d88c72fd18efd6c7b`.
AgentSkills source handoff: `fbd909de1fad209dab8f2fcec6baca9b27ce0bfd`.
[Verification](../../rfcs/plans/human-output-progress/verification.md) records
AC1–AC5 evidence, corrected test/fixture failures, source-manifest regeneration
and the limits of the live failure diagnosis. Dedicated final progress checks (7),
presentation/help checks (14), failure/schema checks (5), launcher/re-exec checks
(2), upstream preflight checks (12), and the two-consumer canonical skill scenario
pass. No complete-suite or native Windows acceptance is claimed.

The observational direct preflight reports incomplete installed readiness; its
receipt is in the runtime session. This source task grants no live readiness
approval and makes no host-loading claim. The existing staged ExampleNotes recovery
remains intact. Current journal drift includes ExampleReview's HEAD and this
checkout's advanced HEAD; the original failure cause was not retained by the old
program. No live recovery, installed-skill migration, push or publication occurred.
Unrelated lockfile edits remain preserved; task-owned test execution is quiescent.
