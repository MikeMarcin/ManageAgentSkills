---
id: MASK-0018
title: Verify and close MASK v1
status: Done
rfc: RFC-MASK-0004
depends_on: ["MASK-0015", "MASK-0016", "MASK-0017"]
closeout: true
---

# MASK-0018: Verify and close MASK v1

## Objective and owned paths

Own v0.1.0 readiness notes, root user docs, this RFC and closeout.

## Bounded work

Finalize agent-friendly install/usage/recovery docs, native support claims, cross-repo handoffs and ignore rules. Keep a direct Python fallback. Report exactly what is implemented/tested; do not publish repositories or package releases without authority.

## Acceptance

All RFC-MASK-0004 criteria and required upstream cards are satisfied. No fleet sync, daemon, marketplace, copy mode, automatic credential grant or unrelated migration crept into v1.

## Focused verification

Structure gate and any missing/invalidated selected acceptance check; no blanket repeated verification matrix.

## Run record

Local v0.1.0 is ready at the documented boundaries. Direct checks and concrete commits populate every criterion. Root/docs are reconciled to delivered commands; missing project-show diagnostic fields were filled using the pure planner and verified observationally on both native platforms. Program/source remain distinct and both real consumers converge at AgentSkills 59a06af. Structure/live-board and final diff review PASS in both repositories. Windows scratch root removal confirmed; local test auxiliaries cleaned; intentional bootstrap backups retained. Shared workflow/management source remains committed and clean. No push/publication, credential change, unrelated migration or invented host-load claim. Closeout review runtime: native collaboration, inherited gpt-6-astra family; exact effort not surfaced. Opposite-family runtime unavailable; bounded review findings both resolved in c5853d9/f23237d. Commit: this Done move.

## Durable closeout anchor

RFC_BASE_SHA: d8ffdeceedd2070c45c5856c84fcaf6de38bab8c

Planned cards: MASK-0015, MASK-0016, MASK-0017.

Cross-repository handoff commits: AgentSkills shared closeout b66a562; second skill d8edaa8; dogfood 59a06af. MASK update/install d8ffdec; cutover e4b0e39; native 8a09784; final docs/diagnostics 1f973e0.

Next slice: none in this pack; all 18 MASK and 6 AgentSkills cards complete.

## Closeout checklist

| Acceptance | Direct check / command | Result | Commit |
|---|---|---|---|
| RFC-MASK-0004-AC01 | Two live declarations; eight canonical symlinks; distinct resolver context | PASS | e4b0e39 / AgentSkills 59a06af |
| RFC-MASK-0004-AC02 | 39-file inventory per bootstrap, exact seed+two overrides; retained independent copies | PASS | e4b0e39 |
| RFC-MASK-0004-AC03 | Subprocess end-to-end on native macOS/Windows; crash recovery/frozen update/no-op | PASS | 8a09784 |
| RFC-MASK-0004-AC04 | Native platform cards and corrected PATH identity test | PASS | 8a09784 |
| RFC-MASK-0004-AC05 | README/CLI guide, owned ignore entries and observational diagnostic selector | PASS | 1f973e0 |
| RFC-MASK-0004-AC06 | Real baseline and handoffs; bounded readiness with no publication/scope expansion | PASS | 1f973e0 |
