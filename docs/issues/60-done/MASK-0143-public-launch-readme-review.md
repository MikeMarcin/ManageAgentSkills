---
schema: "implement-rfc.card.v1"
id: "MASK-0143"
title: "Review the README for public launch"
status: "Done"
rfcs: []
depends_on: []
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"7d1af2ef3ba9b1c01a3519a6a2d071c767b82833","evidence":{"kind":"observation","detail":"Reviewed README against installer, CLI help and companion workflow requirements; added tap approval, symlink prerequisite, code-simplifier first install, committed locks and consumer-context link; removed prepublication caveat."}},{"criterion":"AC2","outcome":"pass","revision":"7d1af2ef3ba9b1c01a3519a6a2d071c767b82833","evidence":{"kind":"observation","detail":"Documentation: 24 RFCs / 143 cards / zero structural violations. Both README link sets: 59 local and companion targets and anchors, zero failures. Public management scenario passes; both canonical public CLI/setup scenarios pass. git diff --check passes."}}]
---

The owner requested a final README review followed by making ManageAgentSkills
and AgentSkills public. Correct the public onboarding instructions and verify
their links and CLI behavior. Existing native acceptance remains separate.

- AC1: The README includes tap approval, a usable first skill and the workflow
  configuration prerequisite, without obsolete prepublication wording.
- AC2: Documentation, local README links and focused public CLI checks pass.

Publication and the post-switch Source checks runs are authorized owner operations
following this documentation review. Preserve unrelated consumer state.
