---
schema: "implement-rfc.card.v1"
id: "MASK-0011"
title: "Implement candidate-validated source fetch and update"
status: "Done"
rfcs: ["RFC-MASK-0003"]
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

Implemented noninteractive Git adapter, explicit fetch, cached-ref previews, frozen candidate tree/metadata validation and ff-only source update over every registered declaration. python3 -m unittest tests.test_git_update: 5 PASS using local bare remotes, including stale remote guard and post-advance crash/recovery without Git rollback. Fetch effects reported separately; no resets, pushes or skill execution. Commit: this Done move.
