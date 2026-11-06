---
schema: "implement-rfc.card.v1"
id: "MASK-0148"
title: "Recreate owned skill links blocked by Windows error 448"
status: "Ready"
rfcs: []
depends_on: []
---

# Windows skill link repair

On JaegAW, MASK reported existing symlinks as linked while traversing them
returned WinError 448. Newly created symlinks to the same locked payloads
worked. Restore this condition through explicit `mask repair` using the
existing ownership, review and journal boundaries.

- AC1: Preview and repair replace only an owned, still-selected link whose
  recorded target is unchanged and whose traversal returns WinError 448.
  Healthy links and the locked payload stay intact.
- AC2: Interrupted replacement is recoverable from a missing leaf. Recovery
  preserves unexpected objects and repeat repair converges.
