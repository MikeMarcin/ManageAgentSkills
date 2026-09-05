---
schema: "implement-rfc.card.v1"
id: "MASK-0021"
title: "Close out user scope and live migration"
status: "Done"
rfcs: ["RFC-MASK-0005"]
depends_on: ["MASK-0020"]
closeout_for: ["RFC-MASK-0005"]
acceptance: [{"criterion":"RFC-MASK-0005-AC01","outcome":"pass","revision":"40dd1e732a914a45c5976ecd6598f462dead3e21","evidence":{"kind":"observation","detail":"python3 -B -m unittest discover -s tests: 80 passing tests, three native-platform skips; user membership and byte-stable no-op subprocess cases"}},{"criterion":"RFC-MASK-0005-AC02","outcome":"pass","revision":"40dd1e732a914a45c5976ecd6598f462dead3e21","evidence":{"kind":"observation","detail":"Integration cases cover both scopes, linked parents, collisions, stale plans, rollback/recovery, v1 state/journals and user-only source requirements"}},{"criterion":"RFC-MASK-0005-AC03","outcome":"pass","revision":"fbaa5cb113486b1c520c656bd76d99c70e4a6d32","evidence":{"kind":"observation","detail":"Guarded selected live deployments converge with passing doctor checks; README/CLI contract and canonical management examples updated; two executable example sequences pass"}}]
---

# MASK-0021: Close out user scope and live migration

Owned scope: runtime, schemas, tests and MASK documentation.

RFC_BASE_SHA: 6af55211e23110df236061398ee92c3dca9143c7

Planned cards: MASK-0019, MASK-0020, MASK-0021

| Criterion | Check / evidence | Outcome | Revision |
|---|---|---|---|
| RFC-MASK-0005-AC01 | python3 -B -m unittest discover -s tests: 80 passing tests, three native-platform skips; user membership and byte-stable no-op subprocess cases | Pass | `40dd1e732a914a45c5976ecd6598f462dead3e21` |
| RFC-MASK-0005-AC02 | Integration cases cover both scopes, linked parents, collisions, stale plans, rollback/recovery, v1 state/journals and user-only source requirements | Pass | `40dd1e732a914a45c5976ecd6598f462dead3e21` |
| RFC-MASK-0005-AC03 | Guarded selected live deployments converge with passing doctor checks; README/CLI contract and canonical management examples updated; two executable example sequences pass | Pass | `fbaa5cb113486b1c520c656bd76d99c70e4a6d32` |

Closeout review runtime: primary agent, local diff and contract review; no delegated review. Native macOS filesystem/command evidence only. Native Windows user scope and loading by running agent UIs were not exercised. Temporary fixture roots were automatically removed; the named migration backups are intentionally retained. No push or publication.
