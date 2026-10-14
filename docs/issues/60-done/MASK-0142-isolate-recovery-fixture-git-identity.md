---
schema: "implement-rfc.card.v1"
id: "MASK-0142"
title: "Make recovery fixture commits independent of host Git identity"
status: "Done"
rfcs: []
depends_on: []
metadata: {"mandate":"public-prep-final-reconciliation-v1","baseline":"4ba72a7235d8a94d0d8cb386a672a51e671702bc","failed_ci":"38529937342","milestone_plan":{"id":"public-source-ci-repair","path":"docs/rfcs/plans/public-source-ci-repair/milestone-plan.json"}}
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"7a97e948ac21ce4141f6850e8eebc921d2c37652","evidence":{"kind":"artifact","path":"docs/development/public-source-finalization.md","detail":"CI38529937342 retains601tests/12skips/4fixture commit errors. Empty HOME baseline auto-detected identity on macOS; strict isolated user.useConfigOnly=true reproduced missing author exit128 in fresh clone."}},{"criterion":"AC2","outcome":"pass","revision":"7a97e948ac21ce4141f6850e8eebc921d2c37652","evidence":{"kind":"artifact","path":"docs/development/public-source-finalization.md","detail":"ce77dd9 sets Fixture/fixture@example.invalid only in the recovery consumer repository; AST comparison preserves all10original methods and7test bodies. Production/workflow inputs unchanged."}},{"criterion":"AC3","outcome":"pass","revision":"7a97e948ac21ce4141f6850e8eebc921d2c37652","evidence":{"kind":"artifact","path":"docs/development/public-source-finalization.md","detail":"All7recovery-entrypoint cases pass13.363s from exactce77dd9 fresh clone with empty profile/strict isolated Git config/no inherited identities. Docs/scans pass at7a97e94; ordinary source push/remote confirmed. Original full failures/skips retained and final CI is coordinator-owned."}}]
---

# Private source CI correction

The complete private-source CI run on the M2 candidate reports 601 tests, 12
declared skips and four errors, all at recovery-entrypoint fixture Git commits.
The consumer repository lacks local author identity; a configured or auto-detected
host identity hides that fixture requirement. M3 owns its diagnosis and repair.

## Acceptance

- AC1: An isolated fresh-clone baseline check exposes the missing consumer Git
  identity; macOS author auto-detection is explicitly controlled and the original
  CI failures remain recorded.
- AC2: RecoveryEntrypoint sets an explicit local fixture author identity. Existing
  assertions, test methods and production behavior remain unchanged.
- AC3: All seven recovery-entrypoint tests pass from the exact corrected candidate
  in a fresh clone with an empty profile and strict isolated Git configuration.
  Documentation/scans/ordinary push and command state are recorded. Reuse unaffected
  full-suite evidence; final GitHub CI remains observed by the coordinator.
