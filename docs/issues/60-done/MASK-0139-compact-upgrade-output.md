---
schema: "implement-rfc.card.v1"
id: "MASK-0139"
title: "Make upgrade review, progress and outcomes readable"
status: "Done"
rfcs: []
depends_on: []
priority: "P1"
metadata: {"milestone_plan":{"id":"compact-upgrade-output","path":"docs/rfcs/plans/compact-upgrade-output/milestone-plan.json"}}
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"f0cf20fbdeac364ea4a4becfba897e5d81efd4ad","evidence":{"kind":"artifact","path":"docs/rfcs/plans/compact-upgrade-output/verification.md","detail":"Compact default review and public details/decline/approval checks preserve significant exceptions and full frozen disclosures."}},{"criterion":"AC2","outcome":"pass","revision":"f0cf20fbdeac364ea4a4becfba897e5d81efd4ad","evidence":{"kind":"artifact","path":"docs/rfcs/plans/compact-upgrade-output/verification.md","detail":"Single-line terminal progress clears before prompts/results; live public heartbeat, JSON and NO_COLOR checks pass."}},{"criterion":"AC3","outcome":"pass","revision":"f0cf20fbdeac364ea4a4becfba897e5d81efd4ad","evidence":{"kind":"artifact","path":"docs/rfcs/plans/compact-upgrade-output/verification.md","detail":"Public partial setup preserves first-consumer roles and second-consumer links, names the stale location and summarizes commits truthfully."}},{"criterion":"AC4","outcome":"pass","revision":"f0cf20fbdeac364ea4a4becfba897e5d81efd4ad","evidence":{"kind":"artifact","path":"docs/rfcs/plans/compact-upgrade-output/verification.md","detail":"Focused runs pass: 66 lifecycle/commit/consent, 45 integration, 17 final affected checks; docs and whitespace pass; selected live controls unchanged."}}]
---

# Make upgrade review, progress and outcomes readable

Owner mandate: work directly. Both supplied `mask upgrade --all --commit`
transcripts overwhelm the reader with repeated routine details. The second also
obscures that setup completed in eleven locations before another location failed.
Baseline: ee8bb172465f6a2b47307e1e0bace4eea7642fc8.

## Scope and acceptance

- AC1: Summarize shared skill/bundle changes and setup. Keep affected locations,
  blocked consumers, existing committed control edits and exact replacement paths
  visible. Offer full review details in the same prompt without granting approval.
- AC2: Terminal progress updates one live line, pauses cleanly for consent and
  clears before final output. Pipes and JSON stay free of progress output.
- AC3: Summarize success and partial results by counts. Name failed and unstarted
  setup locations and commit exceptions; preserve saved effects, backups and useful
  retry instructions. Do not claim nothing ran after earlier setup succeeded.
- AC4: Focused public CLI/terminal and presentation checks pass; consent decline,
  stale-plan refusal and the structured result remain intact. Document the behavior.

Owned paths: human renderer, terminal progress, consent/lifecycle setup disclosure,
focused tests and public output documentation. Test only disposable fixture roots
with local bare taps. Preserve live controls and AgentSkills; no publication or push.

## Integration identity

Renumbered from the Mac-local MASK-0138 to MASK-0139 during Mac/Windows reconciliation; the Windows ahead-update card retains MASK-0138. Original commit acceptance and the historical reservation remain unchanged.
