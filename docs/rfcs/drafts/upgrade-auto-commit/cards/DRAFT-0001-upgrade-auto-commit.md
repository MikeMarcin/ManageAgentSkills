---
schema: "implement-rfc.card.v1"
id: "DRAFT-0001"
title: "Upgrade project controls with optional isolated Git commits"
status: "Backlog"
rfcs: ["RFC-DRAFT-0001"]
depends_on: []
---

# Upgrade project controls with optional isolated Git commits

## Scope and acceptance

Implement the public `upgrade --commit` interface, planning, Git isolation,
post-readiness execution, failures and output defined in
[RFC-DRAFT-0001](../RFC-DRAFT-0001-upgrade-auto-commit.md), R1–R6 and AC01–AC07.
The RFC owns acceptance definitions; this card derives work from them.

Expected owned surfaces: command registration/public routing and validation,
upgrade/lifecycle integration, a bounded Git helper if needed, human/JSON output,
appropriate schemas, focused subprocess fixture tests, README, CONTRIBUTING and
the public upgrade/CLI guides. Select exact files during authorized implementation.
Use disposable repositories and local bare taps; preserve live consumer files.

Verify actual commit trees and branches, unrelated index/worktree preservation,
existing/untracked/partially staged controls, no-op convergence, preview staleness,
linked worktrees, aggregate partial failures and setup/commit failures. Reuse the
existing stable-lock and readiness suites where relevant. No source publication,
push, live migration or native-platform acceptance is inferred.

D4–D7 were confirmed by the owner on 2026-10-03 in [DECISIONS.md](../DECISIONS.md).
Live execution records eligibility and actual acceptance evidence.
