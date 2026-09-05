---
id: MASK-0012
title: Implement portable launchers and separate self update
status: Backlog
rfc: RFC-MASK-0003
depends_on: ["MASK-0011"]
---

# MASK-0012: Implement portable launchers and separate self update

## Objective and owned paths

Own self install/status/update, launcher ownership and `tests/test_launcher.py`.

## Bounded work

Install recognized quoted launchers without changing PATH. Update only the running ManageAgentSkills checkout through ff-only safety; return next-invocation-required without re-exec or chained skill apply.

## Acceptance

Program/source histories remain distinct; unrelated launchers survive; selected supported interpreter/args/exit codes are preserved.

## Focused verification

`python -m unittest tests.test_launcher tests.test_git_update`; native launcher execution completed in final platform cards.

## Run record

Not started. Record actual commands, outcomes and commits here. Read the live board before claiming. Never stage unrelated paths.
