---
schema: "implement-rfc.card.v1"
id: "MASK-0118"
title: "Preserve invalid source caches for an explicit rebuild"
status: "Done"
rfcs: []
depends_on: []
acceptance: [{"criterion":"Guarded cache retention preserves suspect bytes and permits fresh approved fetch without consumer changes","outcome":"pass","revision":"29814c58c4b62b817e5169e35d731b8cf8d15780","evidence":{"kind":"artifact","detail":"docs/development/cache-and-doctor-repair.md: 69 distinct regression tests passed plus final narrow rechecks; documentation gate passes. Reported live cache retained and rebuilt, stale temporary registration removed through guarded public CLI, mask update succeeds and mask doctor --check is healthy."}}]
---

# MASK-0118: Preserve invalid source caches for an explicit rebuild

Field report: `mask update` refuses the agentskills cache because its recorded device
number is 16777230 and the observed number is 16777231; inode and repository match.
Do not silently relax directory ownership or rewrite the marker to trust old objects.

## Acceptance

- A guarded public `source repair-cache NAME` preview retains the complete cache at a
  reported sibling path using an atomic no-replace move. The next ordinary fetch
  reconstructs the active cache from the approved remote. No old objects/config are reused.
- Preserve catalog, registry, declarations, store, consumer links and global settings.
  Refuse unsafe paths, unrecognized markers, stale plans and retention collisions.
- Public local-bare-remote fixtures prove refusal, preservation, re-fetch and no consumer
  changes. Record actual repair observations for the reported cache.
