---
schema: "implement-rfc.card.v1"
id: "MASK-0116"
title: "Selected workflow requirement profiles"
status: "Done"
rfcs: ["RFC-MASK-0023"]
depends_on: []
acceptance: [{"criterion":"AC01–AC03: selected passive profiles and public readiness guards","outcome":"pass","revision":"bc387f81f772b8c7ff26d7a1db50c8edd5d16546","evidence":{"kind":"command","detail":"42 MASK profile/scope/readiness/role/deployment/protocol tests passed; AgentSkills canonical candidate installed through a local bare tap in two disposable consumers passes selected preflight without role setup, while default roles and missing input remain blockers. No live host qualification."}}]
---

# MASK-0116: Selected workflow requirement profiles

Governing RFC: [RFC-MASK-0023](../../rfcs/RFC-MASK-0023-selected-workflow-requirements.md).

## Acceptance

Named passive profiles select scoped requirements without bypassing input/package/ownership checks or retiring unused roles. Default behavior and read-only checks remain correct. Verify public CLI fixtures in project and user scopes.
