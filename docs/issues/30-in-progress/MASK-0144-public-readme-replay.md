---
schema: "implement-rfc.card.v1"
id: "MASK-0144"
title: "Replay the revised public README commands"
status: "In Progress"
rfcs: []
depends_on: ["MASK-0143"]
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
