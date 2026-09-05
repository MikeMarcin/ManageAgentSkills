---
id: MASK-0015
title: Retire bootstrap copies and dogfood both repositories
status: Done
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

AgentSkills handoff d8edaa8; manifest/cutover integration 59a06af. Both untracked 39-file bootstrap trees byte-match seed plus exact two overrides; no symlinks, shim or native adapters existed. Preserved independent copies at each .mask/bootstrap-retired/implement-rfc-2026-09-05. MASK bootstrap inventory-map SHA-256 d65c7f0148a5eaea25efb6524c4a7fd8cb4ce059a6d3fadd1434d96ed966d37c; AgentSkills cfeaf6a03e638c502724a686bb37a7f127e7da1f1bf7520962ed2903468b2043. No prior ~/.mask configuration or mask launcher existed. Ran init with actual AgentSkills root, register each named repo, prospective require both skills --apply --dry-run then exact --expect-plan-hash. All eight native symlinks resolve canonical payloads. Shared audit_board.py passes in each repo; resolver selects mask vs agent-skills from the same asset root. tests.test_end_to_end public subprocess scenario PASS; additional shared-context fixture runs in platform cards. Shared source bytes unchanged. Agent UI loading unobserved. Commit: this Done move.
