---
id: MASK-0001
title: Build the CLI protocol and capability registry
status: In Progress
rfc: RFC-MASK-0001
depends_on: []
external_depends_on: ["AgentSkills:ASK-0004"]
---

# MASK-0001: Build the CLI protocol and capability registry

## Objective and owned paths

Own `mask.py` command dispatch/rendering, JSON result schema and `tests/test_cli_protocol.py`.

## Bounded work

Record the upstream ASK handoff commit. Build one result envelope, parser error interception, machine/human rendering and command metadata. Return explicit unsupported behavior for not-yet-built commands; no false-success stubs.

## Acceptance

Capabilities describes implemented argument shapes/effects; subprocess parser/help/version/error paths all emit correct single JSON and exit status.

## Focused verification

Implement/run `python -m unittest tests.test_cli_protocol`.

## Run record

Not started. Record actual commands, outcomes and commits here. Read the live board before claiming. Never stage unrelated paths.

External dependency AgentSkills:ASK-0004 / RFC-ASK-0001 integrated at b66a562452eec00c6b97079e0376878f0b7d87f2. Verified commit exists in authorized sibling checkout and closeout is Done. Boundary: shared consumer context and safe renderer.
