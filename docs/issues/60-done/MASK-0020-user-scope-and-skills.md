---
schema: "implement-rfc.card.v1"
id: "MASK-0020"
title: "Verify user scope and document CLI"
status: "Done"
rfcs: ["RFC-MASK-0005"]
depends_on: ["MASK-0019"]
acceptance: [{"criterion":"CLI documentation and schema contracts","outcome":"pass","revision":"fbaa5cb113486b1c520c656bd76d99c70e4a6d32","evidence":{"kind":"observation","detail":"README and command inventory cover all user commands, scope selection, persisted homes, version compatibility and error families. Structure gate: 5 RFCs / 21 cards / zero violations; runtime acceptance reused from 40dd1e7."}}]
---

# MASK-0020: Verify user scope and document CLI

Owned scope: runtime, schemas, tests and MASK documentation.

Acceptance: direct passing checks for the bounded slice and explicit source changes; record actual evidence before finish.
