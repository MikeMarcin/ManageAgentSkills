---
schema: "implement-rfc.card.v1"
id: "MASK-0145"
title: "Integrate pinned BetterLeaks for local developer scans"
status: "Done"
rfcs: []
depends_on: []
metadata: {"mandate_revision":"local-betterleaks-v1","baseline":"ff24d8a4f1221d1ebad5f4a72ad089378fe4fe19","milestone_plan":{"id":"local-betterleaks","path":"docs/rfcs/plans/local-betterleaks/milestone-plan.json"}}
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"5833457ff10d710a89ceb2b2fbca2b86448d0890","evidence":{"kind":"observation","detail":"Explicit official macOS ARM64 1.9.0 setup verified pinned SHA-256 and exact version; reuse succeeds, checksum/missing/version negative controls fail closed. Scans/hooks never install.","artifact":"docs/rfcs/plans/local-betterleaks/verification.md"}},{"criterion":"AC2","outcome":"pass","revision":"5833457ff10d710a89ceb2b2fbca2b86448d0890","evidence":{"kind":"observation","detail":"Eight real-binary disposable fixture checks pass under network denial; strengthened target-ignore/caller-cwd control passes. Staged/tracked/history candidate scans report zero. Partial staging, other-ref history, redaction and narrow exceptions have direct controls.","artifact":"docs/rfcs/plans/local-betterleaks/verification.md"}},{"criterion":"AC3","outcome":"pass","revision":"5833457ff10d710a89ceb2b2fbca2b86448d0890","evidence":{"kind":"observation","detail":"Actual clean Git commits pass; staged/alternate-index secret commits fail without secret output. Hook collision/custom-path refusal and idempotence pass. Owned executable hook is active here and git hook run pre-commit passes.","artifact":"docs/rfcs/plans/local-betterleaks/verification.md"}},{"criterion":"AC4","outcome":"pass","revision":"5833457ff10d710a89ceb2b2fbca2b86448d0890","evidence":{"kind":"observation","detail":"Contributor documentation and verification record added. Standard discovery remains 601 cases with zero BetterLeaks cases. Existing CI/test entrypoints and verify.yml unchanged. Documentation gate: 24 RFCs, 145 cards, zero violations; whitespace passes.","artifact":"docs/rfcs/plans/local-betterleaks/verification.md"}}]
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
