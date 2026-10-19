---
schema: "implement-rfc.card.v1"
id: "MASK-0145"
title: "Integrate pinned BetterLeaks for local developer scans"
status: "In Progress"
rfcs: []
depends_on: []
metadata: {"mandate_revision":"local-betterleaks-v1","baseline":"ff24d8a4f1221d1ebad5f4a72ad089378fe4fe19","milestone_plan":{"id":"local-betterleaks","path":"docs/rfcs/plans/local-betterleaks/milestone-plan.json"}}
---

The owner requested BetterLeaks integration locally, without GitHub Actions costs.
Provide a reusable developer command and an opt-in pre-commit hook for this repo.

- AC1: Explicit setup installs stable BetterLeaks 1.9.0 from a pinned SHA-256
  verified official release in an ignored checkout cache. Scans and hooks never
  download; missing or wrong versions fail with recovery instructions.
- AC2: Local staged, full tracked working-source, and all-ref history commands
  force reproducible default rules, full redaction, no live validation, and no
  discovered remote sources. Ambient config/ignore settings cannot disable checks.
  Disposable fixtures prove detection, clean success and partial-staging behavior.
- AC3: Opt-in hook installation preserves existing hooks and core.hooksPath,
  refuses collisions, and is idempotent. Activate the hook in this checkout when
  safe, and verify it with real local Git execution without adding secrets here.
- AC4: Contributor documentation records commands, scope and actual platform
  evidence. Focused checks use real 1.9.0; no scanner dependency or download enters
  standard CI/test paths, .github/workflows/verify.yml stays unchanged, and the
  documentation gate passes. Finish explicit-path local commits and handoff.

No push, global configuration change, remote validation, consumer migration or
MASK registration repair is authorized. No human/native acceptance beyond the
locally exercised host is required by this standalone milestone; other platforms
must remain explicit limitations. Existing unrelated readiness drift is retained.
