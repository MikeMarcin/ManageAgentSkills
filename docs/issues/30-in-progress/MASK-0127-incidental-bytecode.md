---
schema: "implement-rfc.card.v1"
id: "MASK-0127"
title: "Preserve interpreter caches during artifact verification"
status: "In Progress"
rfcs: []
depends_on: []
priority: "P1"
---

# Preserve interpreter caches during artifact verification

Owner amendment on 2026-09-29 to station local takeover delivery; mandate
`station-local-takeover-20260929-v2`. RFC_BASE_SHA:
aa72588162fb9e9a0b92a32059e6dd3c674c4665. Exclusive bounded ownership of store
verification, callers, focused tests and this record; preserve unrelated lock edits.

- AC1: Normal imports through managed links can write bytecode without making status,
  preview, repair, upgrade or recovery fail. Valid caches survive checks and mutation.
- AC2: Cache churn leaves artifact identity and original approved preview hash stable.
- AC3: Locked source bytes and modes remain exact; linked/hardlinked/special caches,
  unknown mixed contents and shipped bytecode are refused. Cache-only concurrent
  atomic writes are tolerated within existing entry/depth/size bounds.
- AC4: Focused public CLI, artifact, recovery and setup regressions pass; documentation
  states the same contract for every caller. Fixture roots and local remotes only.

Continuation and paired AgentSkills candidate:
[station takeover checkpoint](../../development/station-takeover.md).
