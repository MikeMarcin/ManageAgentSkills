---
id: MASK-0002
title: Implement machine setup and passive skill inspection
status: In Progress
rfc: RFC-MASK-0001
depends_on: ["MASK-0001"]
---

# MASK-0002: Implement machine setup and passive skill inspection

## Objective and owned paths

Own machine config, strict JSON validation, flat skill catalog and `tests/test_skill_catalog.py`.

## Bounded work

Implement init/config and source-vs-program identity. Validate MASK package conventions without a YAML dependency; inspect supporting entries without execution or link traversal.

## Acceptance

Invalid schemas/IDs/special entries refuse; no-op setup preserves bytes; source skill text cannot invoke shell/install behavior; inspections work with JSON.

## Focused verification

`python -m unittest tests.test_skill_catalog tests.test_cli_protocol` with no network.

## Run record

Not started. Record actual commands, outcomes and commits here. Read the live board before claiming. Never stage unrelated paths.
