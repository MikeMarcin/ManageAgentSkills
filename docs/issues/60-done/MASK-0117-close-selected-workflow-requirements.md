---
schema: "implement-rfc.card.v1"
id: "MASK-0117"
title: "Close selected workflow requirements"
status: "Done"
rfcs: ["RFC-MASK-0023"]
depends_on: ["MASK-0116"]
closeout_for: ["RFC-MASK-0023"]
acceptance: [{"criterion":"AC01 passive named profiles","outcome":"pass","revision":"bc387f81f772b8c7ff26d7a1db50c8edd5d16546","evidence":{"kind":"artifact","detail":"RFC-MASK-0023 closeout: 42 focused MASK tests and AgentSkills 9c29dd8 installed-link integration passed; selected profiles observational, defaults/ownership preserved. No live host qualification or deployment claim."}},{"criterion":"AC02 scoped readiness guards and role preservation","outcome":"pass","revision":"bc387f81f772b8c7ff26d7a1db50c8edd5d16546","evidence":{"kind":"artifact","detail":"RFC-MASK-0023 closeout: 42 focused MASK tests and AgentSkills 9c29dd8 installed-link integration passed; selected profiles observational, defaults/ownership preserved. No live host qualification or deployment claim."}},{"criterion":"AC03 public project/user paths and capability documentation","outcome":"pass","revision":"bc387f81f772b8c7ff26d7a1db50c8edd5d16546","evidence":{"kind":"artifact","detail":"RFC-MASK-0023 closeout: 42 focused MASK tests and AgentSkills 9c29dd8 installed-link integration passed; selected profiles observational, defaults/ownership preserved. No live host qualification or deployment claim."}}]
---

# MASK-0117: Close selected workflow requirements

Governing RFC: [RFC-MASK-0023](../../rfcs/RFC-MASK-0023-selected-workflow-requirements.md).

## Acceptance

Named passive profiles select scoped requirements without bypassing input/package/ownership checks or retiring unused roles. Default behavior and read-only checks remain correct. Verify public CLI fixtures in project and user scopes.

RFC_BASE_SHA: 7e38d17d99f8c5546add5020cf64c30575749071

Planned cards: MASK-0116. AgentSkills handoff: RFC-ASK-0014 / ASK-0083. No live qualification or consumer migration.

## Acceptance evidence

| Criterion | Check and outcome | Implementation commit |
| --- | --- | --- |
| AC01 | PASS: `tests.test_workflow_profiles` exercises empty/subset profile selection, malformed/unknown refusal, and unchanged default role requirements | `bc387f81f772b8c7ff26d7a1db50c8edd5d16546` |
| AC02 | PASS: profile public CLI checks preserve input/link/ownership guards and state bytes, including unused modified managed roles; profile setup/repair mutations refuse | `bc387f81f772b8c7ff26d7a1db50c8edd5d16546` |
| AC03 | PASS: 42 profile, scope, readiness, role, deployment and CLI-protocol tests; actual canonical AgentSkills package installed through a local bare tap into two disposable consumers, selected readiness passes without role setup and default/missing-input controls fail as expected | MASK `bc387f8`; AgentSkills integration `9c29dd8` |

The direct/native profile handoff is implemented in AgentSkills `b1db75d`/`d12abc1`;
M3 adds the strict recipe and preserves this generic MASK seam at `9c29dd8`.
Its integrated 148-test run includes `test_strategy_mask_public` using this checkout's
absolute `mask.py` entrypoint. Tests used temporary source/consumer roots and local
bare remotes on macOS. Both documentation gates pass with no structural violations.

Closeout review runtime: primary-session self-review; code-simplifier pass. No
independent subagent or live model qualification was used, per owner instruction.
Host loading, serving and native behavior remain unverified; this RFC's acceptance
concerns the local CLI requirement-profile capability only. No global settings,
authentication, consumer deployment, publication or push changed.
