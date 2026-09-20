---
id: "RFC-MASK-0023"
title: "Selected workflow requirement profiles"
status: "Auto-Verified"
---

# Selected workflow requirement profiles

Accepted narrow capability handoff from AgentSkills RFC-ASK-0014. [MASK-0117](../issues/60-done/MASK-0117-close-selected-workflow-requirements.md) owns closeout.

- **AC01:** Passive named requirement profiles allow an explicit empty custom-role requirement without changing the default contract or project/user storage semantics. Malformed/unknown profiles refuse.
- **AC02:** Explicit scoped readiness keeps core package, input, registration, source and ownership guards, is observational, and never retires unused roles.
- **AC03:** Public project/personal CLI fixtures and existing readiness regressions pass; capability discovery and documentation describe exact support. Live host qualification and consumer migration are excluded.

Verified at MASK `bc387f8` with 42 focused public CLI/regression tests and the
AgentSkills `9c29dd8` installed-link handoff in two disposable consumers. The closeout
records criterion-level evidence and limitations. AgentSkills M4 remains open and
unrun; this status makes no live host or experiment claim.

The local default-workflow follow-up [MASK-0119](../issues/60-done/MASK-0119-development-readiness-check.md)
adds read-only inspection of an explicitly approved development link. Mutating
reconciliation remains blocked until the scope returns to pinned deployment.
Verified in `5c5c176` by 32 profile, readiness, scope and pinned-update regression
tests, plus AgentSkills' public installed-skill test in two disposable consumers.
Project and personal development checks preserve state, run no setup, and continue
to reject missing inputs and link drift. This is filesystem readiness evidence;
no live model was launched.
