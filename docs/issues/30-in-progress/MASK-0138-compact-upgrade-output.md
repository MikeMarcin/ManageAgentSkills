---
schema: "implement-rfc.card.v1"
id: "MASK-0138"
title: "Make upgrade review, progress and outcomes readable"
status: "In Progress"
rfcs: []
depends_on: []
priority: "P1"
metadata: {"milestone_plan":{"id":"compact-upgrade-output","path":"docs/rfcs/plans/compact-upgrade-output/milestone-plan.json"}}
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
