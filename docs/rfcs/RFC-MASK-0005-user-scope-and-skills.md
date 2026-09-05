---
id: "RFC-MASK-0005"
title: "User-level skill management"
status: "Implementing"
owner: "MikeMarcin"
created: "2026-09-05"
---

# RFC-MASK-0005: User-level skill management

## Accepted scope

Implement the user-approved plan from 2026-09-05. MASK owns user commands, scope-aware planning, v1/v2 state and journal compatibility, source updates, schemas, tests and CLI documentation. AgentSkills owns four personal imports (coauthoring, code-simplifier, technical-book-humanizer, instamat-image-to-pbr), TRELLIS and concept-art imports from sample_studio, the generic sprite workflow from AST, management guidance, and the selected migrations. Keep personal selection separate from the three project-derived skills. Preserve project-specific tooling, unrelated edits, and existing contracts; no push or publication.

## Verification boundary

Public CLI subprocess tests with temporary roots and local bare remotes, offline imported-package tests, AST existing validation/build wrapper, and guarded live migration with backups. Native macOS evidence only; do not infer native Windows or host UI loading acceptance.

## Acceptance criteria

- **RFC-MASK-0005-AC01** — User commands and independent declarations work through the public CLI.
- **RFC-MASK-0005-AC02** — Both scopes retain safe reconciliation, versioned recovery, and complete source-update validation.
- **RFC-MASK-0005-AC03** — Selected live personal/project deployments converge and docs describe actual support.
