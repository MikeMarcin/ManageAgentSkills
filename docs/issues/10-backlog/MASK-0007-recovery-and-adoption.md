---
id: MASK-0007
title: Add explicit recovery, exact link adoption and doctor
status: Backlog
rfc: RFC-MASK-0002
depends_on: ["MASK-0006"]
---

# MASK-0007: Add explicit recovery, exact link adoption and doctor

## Objective and owned paths

Own recover/adopt/doctor commands and `tests/test_recovery.py`.

## Bounded work

Implement inspect/complete/rollback from bounded journal states, refuse changed objects, support narrowly validated ownership adoption, and keep doctor observational. Test process restart and busy locks.

## Acceptance

No recovered path is removed solely because it appears in JSON. Unknown directories/junctions/links survive. Partial results require recovery and no automatic forced repair exists.

## Focused verification

`python -m unittest tests.test_recovery tests.test_cli_protocol` plus interruption/restart subprocess fixtures.

## Run record

Not started. Record actual commands, outcomes and commits here. Read the live board before claiming. Never stage unrelated paths.
