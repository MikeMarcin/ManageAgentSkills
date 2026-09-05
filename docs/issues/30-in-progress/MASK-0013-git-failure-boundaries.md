---
id: MASK-0013
title: Verify noninteractive and partial-update boundaries
status: In Progress
rfc: RFC-MASK-0003
depends_on: ["MASK-0011", "MASK-0012"]
---

# MASK-0013: Verify noninteractive and partial-update boundaries

## Objective and owned paths

Own subprocess policy, fake-helper tests and any contained corrections to updates.

## Bounded work

Exercise hanging Git/helper process trees, remote ref changes between preview/apply, filter/hook boundaries, auth refusal, output redaction and source-advance-before-link-failure. Record no-effect versus partial state accurately.

## Acceptance

No continuing mutator is labeled safely stopped; no timeout/collision converts into a blind retry; pending state survives indeterminate failures. No live credentials needed.

## Focused verification

`python -m unittest tests.test_subprocess_policy tests.test_git_update tests.test_recovery` with targeted selectors.

## Run record

Not started. Record actual commands, outcomes and commits here. Read the live board before claiming. Never stage unrelated paths.
