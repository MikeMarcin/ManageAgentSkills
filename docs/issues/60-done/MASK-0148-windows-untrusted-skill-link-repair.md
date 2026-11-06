---
schema: "implement-rfc.card.v1"
id: "MASK-0148"
title: "Recreate owned skill links blocked by Windows error 448"
status: "Done"
rfcs: []
depends_on: []
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"c373bdb353e0d93b32a8a3746892b0b988d6a038","evidence":{"kind":"observation","detail":"Public repair planned one link.replace for an unchanged owned link under injected WinError 448, ignored a different Windows error and refused a stale approval after traversal recovered. Approved repair reached the same locked SKILL.md, preserved the other link and converged. macOS reconciliation, repair, recovery and link-producer suites ran 45 tests with 2 platform skips. JaegAW Windows 11 26200.9711 with Python 3.14.6 passed 4 targeted tests and 2 cross-volume tests with a C: store and D: checkout. Tests injected the traversal error and used real symlinks in disposable roots."}},{"criterion":"AC2","outcome":"pass","revision":"c373bdb353e0d93b32a8a3746892b0b988d6a038","evidence":{"kind":"observation","detail":"Process exit after unlink left a missing leaf and a journal. Complete and rollback refused an unexpected directory and restored the owned link once the test collision was removed. Tests also covered a replacement still returning 448 and reported a readable replacement retained after a later failure. Restart recovery passed on macOS and native Windows, including the cross-volume fixture."}}]
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
