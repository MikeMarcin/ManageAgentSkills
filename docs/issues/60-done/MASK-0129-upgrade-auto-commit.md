---
schema: "implement-rfc.card.v1"
id: "MASK-0129"
title: "Upgrade project controls with optional isolated Git commits"
status: "Done"
rfcs: ["RFC-MASK-0024"]
depends_on: []
metadata: {"milestone_plan":{"id":"upgrade-auto-commit","path":"docs/rfcs/plans/upgrade-auto-commit/milestone-plan.json"}}
acceptance: [{"criterion":"AC01","outcome":"pass","revision":"4ef044c1639d7ac106e1e86c65801592aee2c89b","evidence":{"kind":"artifact","path":"docs/development/upgrade-auto-commit-verification.json","detail":"Public flag/help/capabilities, unchanged defaults, positional skill selection, setup consent and early personal-only refusal."}},{"criterion":"AC02","outcome":"pass","revision":"4ef044c1639d7ac106e1e86c65801592aee2c89b","evidence":{"kind":"artifact","path":"docs/development/upgrade-auto-commit-verification.json","detail":"Exact parent/message/control-only trees, both-control bundle upgrade, existing untracked and partial staging, real index synchronization, unrelated staged/working preservation and no-op convergence."}},{"criterion":"AC03","outcome":"pass","revision":"4ef044c1639d7ac106e1e86c65801592aee2c89b","evidence":{"kind":"artifact","path":"docs/development/upgrade-auto-commit-verification.json","detail":"Read-only preview/index bytes/hook sentinel, commit-only would_change, intent/control/staging/HEAD/branch/eligibility stale approval before consumer changes."}},{"criterion":"AC04","outcome":"pass","revision":"4ef044c1639d7ac106e1e86c65801592aee2c89b","evidence":{"kind":"artifact","path":"docs/development/upgrade-auto-commit-verification.json","detail":"Nonregular/ignored/no-HEAD/detached/unmerged/active-operation refusal, clean detached no-op, aggregate per-project blocking, linked worktree branch/index and personal not_applicable."}},{"criterion":"AC05","outcome":"pass","revision":"4ef044c1639d7ac106e1e86c65801592aee2c89b","evidence":{"kind":"artifact","path":"docs/development/upgrade-auto-commit-verification.json","detail":"Setup consent/readiness before hooks; setup failure not_attempted; identity/signing/hook/timeout/message/tree/control/index-race failures retain upgrades and observed commits; retry convergence."}},{"criterion":"AC06","outcome":"pass","revision":"4ef044c1639d7ac106e1e86c65801592aee2c89b","evidence":{"kind":"artifact","path":"docs/development/upgrade-auto-commit-verification.json","detail":"Aggregate eligible successes, blocked project controls unchanged, personal upgrades without commits, commit failure nested error; human review/error output and one JSON result."}},{"criterion":"AC07","outcome":"pass","revision":"4ef044c1639d7ac106e1e86c65801592aee2c89b","evidence":{"kind":"artifact","path":"docs/development/upgrade-auto-commit-verification.json","detail":"Guarded focused integration 126 tests/14 classes, 1 Windows-only skip, zero failed classes; final affected feature rerun 24 tests, zero skips/failures; docs/schema/help, documentation gate and whitespace/self-review."}}]
---

# Upgrade project controls with optional isolated Git commits

## Scope and acceptance

Implement the public `upgrade --commit` interface, planning, Git isolation,
post-readiness execution, failures and output defined in
[RFC-MASK-0024](../../rfcs/RFC-MASK-0024-upgrade-auto-commit.md), R1–R6 and AC01–AC07.
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

D4–D7 were confirmed by the owner on 2026-10-03 in [DECISIONS.md](../../rfcs/assets/upgrade-auto-commit/DECISIONS.md).
Live execution records eligibility and actual acceptance evidence.
