---
schema: "implement-rfc.card.v1"
id: "MASK-0097"
title: "Publish workflow paths and repair retired generated files"
status: "Ready"
rfcs: ["RFC-MASK-0019"]
depends_on: []
---

# MASK-0097

Owner-authorized direct implementation, September 12, 2026. Baseline:
`832380e051884634045a16d934f89b866da05a95`, with existing uncommitted lock
relocation edits preserved and incorporated. No adopted milestone plan exists.

One bounded milestone covers the owner's three deployment problems:

- AC1: setup requests and capabilities publish MASK-owned lock paths.
- AC2: readiness reports retired files; only explicit repair removes bounded
  files through recoverable transactions with durable backups. Normal commands,
  checks and previews preserve them, as do unsafe paths and active fallback locks.
- AC3: explicit package compatibility assertions admit prior input fingerprints
  without execution, retaining consumer-input and exact role-output verification.

Owned scope: workflow/setup/capability/repair transaction code, focused subprocess
tests and current contract documentation. AgentSkills integration is a separate
canonical-source handoff; no unrelated consumer migration or push. Existing
RFC-MASK-0019 host-loading obligations remain open.
