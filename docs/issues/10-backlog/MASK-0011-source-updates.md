---
id: MASK-0011
title: Implement candidate-validated source fetch and update
status: Backlog
rfc: RFC-MASK-0003
depends_on: ["MASK-0010"]
---

# MASK-0011: Implement candidate-validated source fetch and update

## Objective and owned paths

Own Git adapter, source commands/update and `tests/test_git_update.py`.

## Bounded work

Implement explicit fetch, frozen candidate, tree type/metadata checks and ff-only update of AgentSkills; select every registered project and reuse the reconciler. Preserve recovery intent across checkout and late-apply failures.

## Acceptance

Dirty/ahead/diverged/wrong branch/missing skill/collision/unavailable project conditions never trigger destructive Git operations. Dry-run uses labeled cached refs and stale hashes refuse.

## Focused verification

`python -m unittest tests.test_git_update` using temporary local bare remotes.

## Run record

Not started. Record actual commands, outcomes and commits here. Read the live board before claiming. Never stage unrelated paths.
