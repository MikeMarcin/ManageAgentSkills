---
schema: "implement-rfc.card.v1"
id: "MASK-0120"
title: "Unify the command lifecycle and checkout scope defaults"
status: "Done"
rfcs: []
depends_on: []
priority: "P1"
metadata: {"milestone_plan":{"id":"upgrade-readiness","path":"docs/rfcs/plans/upgrade-readiness/milestone-plan.json"}}
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"7bffe094bb9cf02defe14c3c741682bf11c2a480","evidence":{"kind":"observation","detail":"As amended by AC5: upgrade reconciles links and consented generated roles even at unchanged versions; no-op readiness checks and guarded qualification pass. The original global default is superseded. See docs/rfcs/plans/upgrade-readiness/verification.md for exact test records and limitations."}},{"criterion":"AC2","outcome":"pass","revision":"7bffe094bb9cf02defe14c3c741682bf11c2a480","evidence":{"kind":"observation","detail":"As amended by AC7: previews do not acquire or run setup; combined task approval binds setup identities and exact replacements; stale inputs and noninteractive missing approval refuse. Separate setup grants are superseded. See docs/rfcs/plans/upgrade-readiness/verification.md for exact test records and limitations."}},{"criterion":"AC3","outcome":"pass","revision":"7bffe094bb9cf02defe14c3c741682bf11c2a480","evidence":{"kind":"observation","detail":"As amended by AC7: modified/unmanaged content is protected until the combined review is approved; staged setup recovery preserves truthful committed link effects. The original repair flag is superseded. See docs/rfcs/plans/upgrade-readiness/verification.md for exact test records and limitations."}},{"criterion":"AC4","outcome":"pass","revision":"7bffe094bb9cf02defe14c3c741682bf11c2a480","evidence":{"kind":"observation","detail":"As amended by AC5/AC8/AC11: scope isolation, version holds, offline boundaries and blocked-tap disclosure pass public checks. Help uses register/repair/upgrade; public ensure is retired. See docs/rfcs/plans/upgrade-readiness/verification.md for exact test records and limitations."}},{"criterion":"AC5","outcome":"pass","revision":"7bffe094bb9cf02defe14c3c741682bf11c2a480","evidence":{"kind":"observation","detail":"Public subprocess checks pass checkout-only defaults, explicit user/all selection, selector conflicts and outside-checkout refusals. See docs/rfcs/plans/upgrade-readiness/verification.md for exact test records and limitations."}},{"criterion":"AC6","outcome":"pass","revision":"7bffe094bb9cf02defe14c3c741682bf11c2a480","evidence":{"kind":"observation","detail":"Public CLI and README replay pass fresh linked-worktree registration at locked versions, incremental install/uninstall, declaration-preserving unregister and catalog/tap operations. See docs/rfcs/plans/upgrade-readiness/verification.md for exact test records and limitations."}},{"criterion":"AC7","outcome":"pass","revision":"7bffe094bb9cf02defe14c3c741682bf11c2a480","evidence":{"kind":"observation","detail":"Guarded qualification and refusal-effects-v2.log pass combined review, terminal decline, stale-input refusal and unchanged consumer controls on missing consent; cache-only effects are disclosed. See docs/rfcs/plans/upgrade-readiness/verification.md for exact test records and limitations."}},{"criterion":"AC8","outcome":"pass","revision":"7bffe094bb9cf02defe14c3c741682bf11c2a480","evidence":{"kind":"observation","detail":"Disposable program-clone tests pass refresh age, explicit home, no-update/offline/reviewed-plan boundaries, re-exec, command retirement and protocol v2. See docs/rfcs/plans/upgrade-readiness/verification.md for exact test records and limitations."}},{"criterion":"AC9","outcome":"pass","revision":"7bffe094bb9cf02defe14c3c741682bf11c2a480","evidence":{"kind":"observation","detail":"Qualification tests pass conservative cleanup of verified owned artifacts, reference and recovery protection, stale-review refusal and preparation locking. See docs/rfcs/plans/upgrade-readiness/verification.md for exact test records and limitations."}},{"criterion":"AC10","outcome":"pass","revision":"7bffe094bb9cf02defe14c3c741682bf11c2a480","evidence":{"kind":"observation","detail":"README/help and public fixture journeys pass; AgentSkills source handoff f55aef46acbd451f4377512095cd0f3737a15147 has 12 preflight and 23 renderer checks passing. macOS observations are retained. Windows station DNS failure and no host-loading claim are explicit; broader RFC native acceptance remains open. See docs/rfcs/plans/upgrade-readiness/verification.md for exact test records and limitations."}},{"criterion":"AC11","outcome":"pass","revision":"7bffe094bb9cf02defe14c3c741682bf11c2a480","evidence":{"kind":"observation","detail":"Public pin/unpin tests pass named/all membership and user selection. Upgrade holds locked versions while rebuilding missing generated roles; unpin does not advance immediately; listings show holds. See docs/rfcs/plans/upgrade-readiness/verification.md for exact test records and limitations."}}]
---

# MASK-0120: Unify the command lifecycle and checkout scope defaults

## Mandate and boundary

Owner request, 2026-09-20: work directly; `upgrade` should be sufficient to make
existing registered projects and personal skills functional. `ensure` remains
useful for a new worktree or reconciling pinned versions without upgrading.
This amends the setup-only-on-ensure behavior recorded by RFC-MASK-0019; it does
not close that RFC's outstanding real-package/native acceptance.

Baseline: `0b2e41fcabe629a8916bc3820b3394f8240e255a`.
Owned surface: upgrade orchestration, shared setup/repair validation where needed,
CLI options and presentation, public CLI tests and current documentation.
No live consumer migration, source push, automatic approval or host-load claim.

## Acceptance

- AC1: Scoped and default all-registered upgrade reconciles links, static roles
  and consented generated roles in one invocation, including unchanged versions;
  a second unchanged invocation runs no setup.
- AC2: Preview binds candidate setup identities and writes/fetches/runs nothing;
  named setup with its hash succeeds, changed inputs refuse, terminal yes/no is
  honored, and JSON/redirected/--yes invocations never run unauthorized setup.
- AC3: Modified/unmanaged content remains protected by default. Explicit
  `upgrade --repair` uses the existing backup and staged repair semantics;
  failed setup never reports success and retains truthful committed link effects.
- AC4: Scope selection, pins, offline behavior and failed-tap isolation remain
  intact; help and README explain upgrade versus ensure and the setup path.

## Execution

Direct strategy, no delegation. The host has no scoped delegation-disable
setting exposed; no agent or external model calls are used. Direct preflight
reports `integration.approval_required` for this checkout. That is an automatic
readiness policy prerequisite, not a missing engineering role; this task changes
source and tests disposable consumers and does not grant live readiness approval.
The pre-existing `.mask.lock.json` edit is unrelated and preserved.

## Accepted command-surface amendment (2026-09-20)

The owner approved the final revised plan after reviewing the command buckets.
This supersedes AC1's all-registered default, AC2's separate setup grants, AC3's
repair flag, and AC4's retained public ensure command. Earlier evidence remains
historical evidence for the shared engine, not acceptance of this amended surface.

- AC5: upgrade, repair, status and list default to the current checkout; --user
  selects personal skills and --all selects every registered checkout plus user.
  Outside a checkout an explicit selector is required; selectors conflict.
- AC6: register [PATH] enrolls and prepares a fresh checkout/worktree using its
  pinned declaration. install/uninstall change skill selections and reconcile;
  unregister removes managed deployment/registration while preserving declarations.
  tap [NAME URL] lists/adds sources; untap removes sources. search/info browse taps.
- AC7: one review binds setup and exact backup/replacement actions before any
  consumer mutation. --approve-plan HASH grants that reviewed task. Decline or
  missing approval leaves consumer controls and deployment unchanged. Cache-only
  preparation effects are disclosed. Ordinary owned changes need no prompt.
- AC8: update refreshes MASK and catalogs. Live install/upgrade auto-refresh when
  older than 24 hours; --no-update skips automatic refresh and --offline forbids
  network. Preview/reviewed apply never refresh; program updates re-exec before
  consumer planning. Public ensure/apply/plan/doctor/remove and split initialization
  retire in a versioned CLI/JSON break; adapters use the shared readiness service.
- AC9: explicit cleanup previews and removes verified unused artifacts/caches,
  safely disposable backups and stale staging/retired generated locks. Preserve
  active locks, pending recovery, referenced versions, unknown content, and the
  persistent writer-lock file. Coordinate cleanup with preparation, not only
  consumer transactions. No automatic cleanup or age-only retention policy.
- AC10: public help/docs describe the buckets and end-to-end lifecycle; CLI fixtures
  cover scope isolation, fresh worktrees, consent, failures/recovery and cleanup
  concurrency. Native coverage is reported honestly; shared AgentSkills callers
  receive an explicit source handoff before public command retirement.

Execution remains direct in the current checkout, without delegation or live
consumer migration. Personal usage is one command: mask upgrade --all. Bare
maintenance never also selects personal skills. The pre-existing .mask.lock.json
edit remains unrelated.

Owner amendment during implementation: add pin/unpin SKILL, with --all replacing
SKILL to select every skill in the chosen checkout and --user selecting personal
skills. AC11: pin holds the current locked commit; unpin releases the hold without
upgrading immediately; upgrade preserves held versions while still reconciling
links and consented setup. This --all is skill membership, not registry scope.

## Closeout (2026-09-20)

Implemented locally in `7bffe094bb9cf02defe14c3c741682bf11c2a480`.
The canonical AgentSkills caller and management-instruction handoff is committed
in `f55aef46acbd451f4377512095cd0f3737a15147` in the AgentSkills repository.
Neither repository was pushed and no installed skill payload was migrated.

[Verification and acceptance evidence](../../rfcs/plans/upgrade-readiness/verification.md)
records the amended AC5–AC11 results, retained AC1–AC4 engine obligations,
intermediate failures and corrective reruns. Original command spellings, separate
approval grants and the all-registered default are superseded, not claimed as
current behavior. The final public surface uses checkout defaults and explicit
personal/all-installation selectors. Version holds preserve locked commits while
upgrade still restores links and runs consented setup.

The guarded qualification courses passed (58 tests with one native Windows skip,
then 24 tests); focused follow-up checks passed after the recorded corrections.
The initial full-suite migration run is retained as failed historical evidence,
not presented as a green full-suite result. All task-owned execution is quiescent.
Primary engineering acceptance is complete; no independent review is claimed.

Native Windows verification could not be repeated because the configured test
station failed DNS resolution. No new Windows or real host skill-loading
acceptance is claimed; broader RFC-MASK-0019 native obligations remain open.
The unrelated pre-existing `.mask.lock.json` edits in both repositories remain
preserved. This closes the selected source implementation and fixture acceptance
scope only.
