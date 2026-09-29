---
schema: "implement-rfc.card.v1"
id: "MASK-0127"
title: "Preserve interpreter caches during artifact verification"
status: "Done"
rfcs: []
depends_on: []
priority: "P1"
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"2fcd627c6ef89b0bd0d722a8802adc0ec30485fa","evidence":{"kind":"observation","detail":"Normal managed-link import plus public status/repair/upgrade and recovery preserve interpreter caches; real AgentSkills/BPR readiness restored with 101 source and 5 cache hashes unchanged."}},{"criterion":"AC2","outcome":"pass","revision":"2fcd627c6ef89b0bd0d722a8802adc0ec30485fa","evidence":{"kind":"observation","detail":"Public normal import leaves original repair preview hash unchanged and original approval applies."}},{"criterion":"AC3","outcome":"pass","revision":"2fcd627c6ef89b0bd0d722a8802adc0ec30485fa","evidence":{"kind":"observation","detail":"Artifact negative controls reject linked, hardlinked, nested and unknown cache contents and edited source; explicit shipped-bytecode regression passes; atomic churn, portable paths and derived entry budget pass."}},{"criterion":"AC4","outcome":"pass","revision":"2fcd627c6ef89b0bd0d722a8802adc0ec30485fa","evidence":{"kind":"observation","detail":"23 focused passing observations, exact source structure gate zero violations; setup failures recorded and corrected; docs contract unified."}}]
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
