---
schema: "implement-rfc.card.v1"
id: "MASK-0098"
title: "Implement scope-specific personal workflow readiness"
status: "In Progress"
rfcs: ["RFC-MASK-0020"]
depends_on: []
metadata: {"criterion_coverage":["RFC-MASK-0020-AC01","RFC-MASK-0020-AC02","RFC-MASK-0020-AC03"]}
---

# MASK-0098: Implement scope-specific personal workflow readiness

Governing RFC: [RFC-MASK-0020](../../rfcs/RFC-MASK-0020-personal-workflow-readiness.md).

## Owned work

Extend the passive workflow descriptor and generic readiness engine to distinguish project and personal prerequisites. Personal roles come from canonical AgentSkills definitions without treating home as a project or writing source configuration. Integrate personal binding preflight after the upstream helper contract is available. Keep exact setup consent, collision preservation, route fidelity, managed-file ownership, project behavior and file-versus-host-loading distinction.

## Acceptance

- Disposable public CLI tests cover both scopes and missing/stale prerequisites; project mode remains compatible.
- Passive/check/JSON paths do not run package code or grant permission. The current checkout's integration.approval_required state is preserved.
- The actual upstream AgentSkills handoff revision is recorded; no hard-coded implement-rfc exception is added to MASK.

Contributes to: RFC-MASK-0020-AC01, RFC-MASK-0020-AC02, RFC-MASK-0020-AC03.

## Verification and execution record

Program `78cc57cdac4ea493a3e0ba38ca0e51218af7991a` implements complete project/user scope contracts and scope-specific setup requests without a skill-specific branch. AgentSkills source `9b47f12861c33f1f02b3aa4aaa7d848e37c2b094` supplies the canonical personal descriptor and preflight. [Direct readiness evidence](../../rfcs/MASK-0098.readiness.json) records five focused tests, the 379-test MASK suite (four skipped), a fresh committed-revision cross-repository CLI run, and the unchanged live `integration.approval_required` check. File readiness is qualified; native Codex and Claude Code loading remains a separate AgentSkills acceptance.
