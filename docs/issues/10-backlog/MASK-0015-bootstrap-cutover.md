---
id: MASK-0015
title: Retire bootstrap copies and dogfood both repositories
status: Backlog
rfc: RFC-MASK-0004
depends_on: ["MASK-0014"]
external_depends_on: ["AgentSkills:ASK-0006"]
---

# MASK-0015: Retire bootstrap copies and dogfood both repositories

## Objective and owned paths

Own ManageAgentSkills manifest/context/instructions and explicitly inventoried temporary bootstrap paths; request the AgentSkills integrator to commit its own manifest change.

## Bounded work

Inventory/hash bootstrap directories and generated shim, retain independent backups, move only packet-created unchanged content out of discovery roots, register the two named checkouts and deploy both shared skills. Do not edit SRV/SamplePlanner.

## Acceptance

Both consumers share the canonical payload and retain different project facts. No modified/tracked/unrecognized content is overwritten, and generated source bytes are unchanged.

## Focused verification

Implement/run `tests.test_end_to_end` fixture cutover; then record the explicitly authorized local dogfood commands and both repository commits.

## Run record

Not started. Record actual commands, outcomes and commits here. Read the live board before claiming. Never stage unrelated paths.
