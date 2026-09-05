---
schema: "implement-rfc.card.v1"
id: "MASK-0019"
title: "Implement user consumers and recovery"
status: "Done"
rfcs: ["RFC-MASK-0005"]
depends_on: []
acceptance: [{"criterion":"User consumers and recovery","outcome":"pass","revision":"40dd1e732a914a45c5976ecd6598f462dead3e21","evidence":{"kind":"command","command":["python3","-B","-m","unittest","discover","-s","tests"],"detail":"80 tests passed, 3 native-platform skips; includes public user commands, v1 rollback, mixed-scope recovery and user-only update validation."}}]
---

# MASK-0019: Implement user consumers and recovery

Owned scope: runtime, schemas, tests and MASK documentation.

Acceptance: direct passing checks for the bounded slice and explicit source changes; record actual evidence before finish.
