---
id: MASK-0012
title: Implement portable launchers and separate self update
status: Done
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

Implemented owned POSIX/Windows launchers with journaled install, actual interpreter paths, exact-content collision refusal and no PATH edits. Program updates use a separate frozen ff-only transition, preflight protocol/schema compatibility, and return next_invocation_required without re-execution. Eager imports retain loaded implementation. Focused launcher and Git fixture tests pass (7). Recovery tests pass (6). Included exact-newline preservation and review corrections at shared journal/candidate boundaries; regressions follow in MASK-0013. Native launcher execution follows final platform cards. Commit: this Done move.
