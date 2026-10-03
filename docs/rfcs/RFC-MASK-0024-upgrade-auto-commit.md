---
id: "RFC-MASK-0024"
title: "Opt-in commits of upgraded project selections and locks"
status: "Accepted"
metadata: {"milestone_plan":{"id":"upgrade-auto-commit","path":"docs/rfcs/plans/upgrade-auto-commit/milestone-plan.json"}}
---

# Optional commits after upgrade

## Problem and current behavior

`mask upgrade` updates project controls but leaves them uncommitted. The owner
wants an option to handle that repeated Git step.

`mask.py:COMMANDS` has no upgrade commit flag. `mask_update.py:dispatch` and
`mask_fs.py:plan` can update both `.mask.json` and `.mask.lock.json` when bundles
change. `mask_lifecycle.py:execute` applies those changes before setup completes,
so a later failure can leave an applied upgrade. Aggregate upgrades already
report partial success. These are observed behaviors, not proposed changes.

The existing [stable-lock fix](../issues/60-done/MASK-0125-stable-package-locks.md)
prevents lock-only source commits from repeatedly advancing unchanged packages;
controls inside a selected package still count as payload changes.

## Goals and boundaries

Add `mask upgrade --commit`. The owner confirmed including both changed project
controls and any existing uncommitted changes to them. Default upgrade stays as
it is. The commit set excludes setup outputs, personal controls and other files.
No push, persistent preference or commit option for other commands is included.

## Accepted behavior

### R1 — Interface

`--commit` is a boolean upgrade flag, exposed in help and capabilities. It works
with project/skill selection, `--all`, offline, JSON, dry-run and plan approval.
It authorizes the commit without an extra prompt; setup still needs its existing
consent. Use the message `chore(mask): upgrade skills`.

### R2 — Contents

After a successful upgrade, commit the final `.mask.json` and `.mask.lock.json`
files that differ from HEAD. Include existing staged, unstaged and untracked
changes, even when skill versions were already current. Partially staged MASK
files are committed in full and their index entries match the commit afterward.
Preserve unrelated staged entries and working files. Do not force-add ignored
controls, create empty commits, stash, reset, clean or broadly stage files.

### R3 — Scope and eligibility

Create at most one commit per selected project on its current branch, including
linked worktrees. Under `--all`, upgrade personal skills normally and report
committing them as `not_applicable`. Reject `--user --commit` with exit 2 before
refresh or consumer effects. No remote or upstream branch is required.

Preflight projects with prospective control differences before consumer writes:
require the Git worktree root, an attached branch with an existing HEAD, regular
nonignored controls, no unmerged entries and no merge, rebase, cherry-pick, revert
or bisect in progress. Refuse ineligible scoped candidates with
`upgrade.commit_ineligible`, exit 4. Under `--all`, block only those candidates
and return `upgrade.incomplete`, exit 4. Never commit blocked/skipped consumers.
If controls will match HEAD, report `not_needed` without commit eligibility checks.

### R4 — Preview and races

Dry-run shows scope, exact paths, message, existing changes and eligibility without
fetching, writing, staging, running hooks or signing. Commit-only work sets
`would_change=true`. Bind commit intent, message, Git identities/branches/HEADs,
control bytes and relevant index observations into the task hash. Changed intent
or observations invalidate approval with `plan.stale` before consumer effects.
Recheck Git state and expected final controls before committing; detected concurrent
changes abort the commit and are preserved. Existing setup review stays intact.

### R5 — Timing and failures

Start commits only after activation, setup and final readiness succeed. Use normal
Git identity, hooks and signing configuration with MASK's configured Git timeout;
do not disable configuration or prompt for credentials. Scoped commit failures
return `upgrade.commit_failed`, exit 5, leaving applied upgrades intact.

Under `--all`, attempt every eligible project's commit after successful readiness;
retain successful commits when another fails and return `upgrade.incomplete`,
exit 4, with nested errors. If activation/setup verification fails, start no
commits and report `not_attempted`. Git commits follow the MASK transaction;
neither failure nor recovery implicitly rolls them back, amends or resumes them.

Inspect actual HEAD and commit contents, including after Git errors. Success
requires the intended parent and only the expected control changes. Report any
created commit or uncertain outcome truthfully; preserve observable hook effects.
Rerunning can commit pending controls without duplicating completed commits.

### R6 — Results and compatibility

With `--commit`, add `data.commits` rows per selected consumer containing `root`,
`scope`, `status`, `paths`, `included_existing_changes` (paths), `message`,
`before_head`, `after_head`, `commit` and nullable structured `error`. Git IDs may
be null. Statuses: `planned`, `not_needed`, `not_applicable`, `blocked`,
`not_attempted`, `committed`, `failed`, `unknown`. Human output names commits and
failures by project. Preserve version/setup/fetch results and filesystem transaction
status; an actual Git commit also sets `changed=true`. JSON remains one document.

No control/state migration is needed. Update README, help, upgrade/CLI guides and
[CONTRIBUTING.md](../../CONTRIBUTING.md), whose current statement that MASK
has no automatic commit/push must describe the explicit local commit option.

## Alternatives and open decisions

Lock-only commits could omit changed bundle selections; refusing dirty controls
would retain the manual step. The owner chose both controls and existing changes.
Requiring a clean index is simpler but interrupts unrelated staged work.

Scope, Git eligibility, preview and failure policy were confirmed on 2026-10-03 in
[confirmed decisions](assets/upgrade-auto-commit/DECISIONS.md). Git/index implementation is deferred to engineering;
message customization and broader commit sets are outside this feature.

## Acceptance

- **AC01**: The flag is discoverable and composes with existing selectors; defaults and setup consent remain intact; personal-only invocation refuses before effects.
- **AC02**: Commits contain exactly the final differing controls, including existing/partially staged/untracked changes; unrelated work survives and clean controls create no commit.
- **AC03**: Preview is read-only, discloses commit-only work and binds reviewed intent and observations; stale approval refuses before consumer writes.
- **AC04**: Git eligibility, per-project aggregate blocking and linked-worktree scope follow R3; personal controls are never committed.
- **AC05**: Readiness precedes commits; Git errors, timeouts, hooks and races preserve applied effects and produce truthful results; retries avoid duplicate commits.
- **AC06**: Aggregate partial outcomes retain successes, exclude blocked consumers and return nonzero; human/JSON results distinguish upgrades from commits.
- **AC07**: Focused public CLI fixtures prove filesystem/Git effects, existing stable-lock/readiness behavior remains intact, and public documentation matches the feature.

## Handoff

Owner mandate `upgrade-auto-commit`, revision 2, confirms D4–D7 with “confirm go ahead”.
Preserve settled D2–D3. Feature implementation commits exclude this checkout's live
`.mask.json`, `.mask.lock.json`, unrelated `.gitignore`, and unrelated drafts.

[Implementation](../issues/30-in-progress/MASK-0129-upgrade-auto-commit.md),
[closeout](../issues/10-backlog/MASK-0130-upgrade-auto-commit-closeout.md),
[adopted plan](plans/upgrade-auto-commit/milestone-plan.json), and
[retained pack](assets/upgrade-auto-commit/README.md).
