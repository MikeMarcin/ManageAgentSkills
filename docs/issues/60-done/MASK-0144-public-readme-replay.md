---
schema: "implement-rfc.card.v1"
id: "MASK-0144"
title: "Replay the revised public README commands"
status: "Done"
rfcs: []
depends_on: ["MASK-0143"]
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"c36d3f7d6d6b5f20b4d2562005cec8e64a1d911c","evidence":{"kind":"observation","detail":"README fenced-command equality includes standalone tap approval and code-simplifier. The public replay creates a passive fixture package, installs/lists/upgrades it without consumer workflow context, and checks both adapters plus the lockfile."}},{"criterion":"AC2","outcome":"pass","revision":"c36d3f7d6d6b5f20b4d2562005cec8e64a1d911c","evidence":{"kind":"observation","detail":"python3 -B -m unittest tests.test_readme_journeys: all five tests pass in 36.672 seconds, including implement-rfc missing-context refusal, by-hand setup, repair and every everyday command. Documentation: 24 RFCs / 144 cards, zero structural violations. git diff --check passes. No runtime code changed. Initial public CI run 39295325087 recorded one obsolete replay expectation among 601 cases; remaining cases passed or had declared skips."}}]
---

Public CI run 39295325087 found that the README replay fixture still pinned the
old command blocks after MASK-0143. Its other 600 cases passed or had declared
platform skips. Update the replay fixture without changing runtime behavior.

- AC1: The fenced-command assertion includes standalone tap approval and the
  code-simplifier quick start. The revised quick start runs in a fresh consumer
  without workflow context and produces both skill links and a lockfile.
- AC2: Preserve the separate implement-rfc missing-context refusal and existing
  by-hand installation, repair and everyday-command coverage. The README replay
  module and documentation checks pass; publish the correction for public CI.
