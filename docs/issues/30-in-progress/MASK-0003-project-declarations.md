---
id: MASK-0003
title: Implement project declarations and local registration
status: In Progress
rfc: RFC-MASK-0001
depends_on: ["MASK-0002"]
---

# MASK-0003: Implement project declarations and local registration

## Objective and owned paths

Own project commands, deterministic root resolution, registry serialization and `tests/test_manifest_registry.py`.

## Bounded work

Implement init/show/set/require/unrequire/set-targets/register/unregister/list, explicit clear/keep-links and prospective manifest planning interface. Never invent a source URL inside a project manifest.

## Acceptance

Incremental commands preserve unrelated requirements; exact set requires explicit operands/clear; aliases/worktrees resolve deterministically; unavailable roots remain recorded. --apply cannot bypass registration/preflight.

## Focused verification

`python -m unittest tests.test_manifest_registry tests.test_cli_protocol`.

## Run record

Not started. Record actual commands, outcomes and commits here. Read the live board before claiming. Never stage unrelated paths.
