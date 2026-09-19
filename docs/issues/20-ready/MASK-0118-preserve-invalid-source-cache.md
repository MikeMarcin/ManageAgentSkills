---
schema: "implement-rfc.card.v1"
id: "MASK-0118"
title: "Preserve invalid source caches for an explicit rebuild"
status: "Ready"
rfcs: []
depends_on: []
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
