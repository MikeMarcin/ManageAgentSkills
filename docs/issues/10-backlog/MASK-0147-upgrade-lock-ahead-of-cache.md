---
schema: "implement-rfc.card.v1"
id: "MASK-0147"
title: "Decide how upgrade treats a committed lock that is ahead of the tap cache"
status: "Backlog"
rfcs: []
depends_on: ["MASK-0146"]
metadata: {"requested":"2026-10-25","origin":"MASK-0146"}
---

# Committed lock ahead of the tap cache

After a clone pulled a lock committed on another host, `mask upgrade` on
Windows reported a tap fetch from `049a46e` to `ac9c2e9` and then ended with
"no deployment changes were applied" until `mask update` ran. The exact
failing code was not captured.

`mask repair` online already acquires a locked commit that is missing from the
cache (`mask_lifecycle.restore` calls `acquire_exact`). `upgrade` does not:
when the automatic catalog refresh has already run, or under `--offline`,
`--dry-run` or `--approve-plan`, it resolves from the cache only, and a lock
row naming an uncached commit blocks the consumer with
`lock.resolution_required`.

## Acceptance

- AC1: Reproduce with a disposable fixture: clone B pulls a lock committed in
  clone A against a tap commit B's MASK home has not fetched, then runs
  `mask upgrade` and `mask repair`. Record the actual codes.
- AC2: Decide whether a live `upgrade` acquires the exact locked commits
  before resolving (as `repair` does) and implement it, or document why the
  refusal and its recovery hint are correct. Previews stay cache-only.
