---
schema: "implement-rfc.card.v1"
id: "MASK-0146"
title: "Upgrade once per repository and propagate to its other registered checkouts"
status: "Done"
rfcs: []
depends_on: []
metadata: {"mandate_revision":"upgrade-once-per-repository-v1","baseline":"8acc16ce935f05820f10500fdc61fb3b16c6ff4d","requested":"2026-10-25","follow_up":"MASK-0147"}
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"813b4a9e8b7729ea495dda56c44f59ced439feb4","evidence":{"kind":"observation","detail":"tests.test_upgrade_groups: dry-run/JSON groups, canonical invoking_checkout and default_branch_first_path selection, member actions, approve-plan over the grouped hash; --independent restores per-checkout rows and is rejected without --all (exit 2)."}},{"criterion":"AC2","outcome":"pass","revision":"813b4a9e8b7729ea495dda56c44f59ced439feb4","evidence":{"kind":"observation","detail":"Real Git: one canonical commit; feature worktree and same-HEAD clone fast-forwarded to it; clone with local work and detached worktree cherry-picked (same author/date/message, detached_only reported, no branch created); dirty clone uncommitted; unrelated repo commits on its own; origin and origin/main unmoved; failed canonical hook leaves members not_attempted."}},{"criterion":"AC3","outcome":"pass","revision":"813b4a9e8b7729ea495dda56c44f59ced439feb4","evidence":{"kind":"observation","detail":"11 tests: URL normalization, union of common dir and origin, canonical ranking, ambiguity/detached/operation/dev-link, adoption rules; integration with two worktrees, three clones and an unrelated repo; ambiguous feature worktrees block outside and succeed inside."}},{"criterion":"AC4","outcome":"pass","revision":"813b4a9e8b7729ea495dda56c44f59ced439feb4","evidence":{"kind":"observation","detail":"Help, README, sources-and-updates guide and CLI contract updated. Full suite baseline 8acc16c: 601 tests/43 skipped/5 failed (test_directory_rebind Windows KeyError); candidate: 612/43/same 5. Documentation gate 0 violations; git diff --check clean."}}]
---

# Upgrade once per repository

`mask upgrade --all` treats every registered checkout independently. When
several checkouts are worktrees or clones of one repository, each is re-pinned
on its own and, with `--commit`, gets its own `chore(mask): upgrade skills`
commit. Rebasing those duplicates needed `--ours` resolution and skipped
commits, and a tap fetch between hosts produced conflicting re-pins.

The owner requested (2026-10-25) that `upgrade --all` and
`upgrade --all --commit` upgrade one canonical checkout per repository by
default and propagate that result to the repository's other registered
checkouts. The owner later corrected (same day) that detached-HEAD members are
propagated by a commit on that detached HEAD, never skipped; the uncommitted
fallback is kept only for members with modified controls or a cherry-pick that
would conflict.

## Design decisions

- D1 Scope. Grouping applies to `upgrade --all`, with or without `--commit`.
  A single-checkout upgrade (`mask upgrade`, `--project`, `--user`) is
  unchanged. `--independent` (only with `--all`) restores the previous
  per-checkout behavior. Personal scope, non-Git roots and roots without HEAD
  are always independent.
- D2 Repository identity. Two registered project roots are one repository when
  they share a Git common directory (linked worktrees) or the normalized fetch
  URL of their `origin` remote (separate clones). Groups are the transitive
  closure of both relations. Only `origin` is compared: it is the clone
  default, and comparing every remote would merge forks that share an
  `upstream` remote. Normalization folds `scp`-style and URL forms to
  host/path, case-folds the host, drops user, port, a trailing `/` and `.git`,
  and resolves local paths. The branch is not part of the identity, because
  linked worktrees are always on different branches; it decides the canonical
  checkout and the propagation action.
- D3 Canonical checkout. Candidates are members that are not dev-linked and,
  with `--commit`, have an attached branch and an existing HEAD. Preference:
  the invoking checkout when it is a candidate; else candidates on the origin
  default branch (`refs/remotes/origin/HEAD`, or `main`/`master` when that is
  unknown); then clean project controls; then the lexicographically smallest
  path. Two or more candidates with none on the default branch and no invoking
  member is ambiguous: the group is blocked with `upgrade.group_ambiguous`
  and the report says to run from the intended checkout or use
  `--independent`. A group without candidates is upgraded independently and
  reported as such.
- D4 Adoption. A member adopts the canonical final `.mask.json` and
  `.mask.lock.json` bytes without resolving when its controls equal the
  canonical's starting controls. With `--commit` the condition is stricter:
  the member's controls are clean against its HEAD and its HEAD control blobs
  equal the canonical HEAD blobs, so the canonical commit applies cleanly. A
  member whose controls already equal the canonical result is `current`.
  Every adopting or current member takes part in the same journaled
  activation, so readiness and role repair run there.
- D5 Commit propagation (`--commit`). A member at the canonical commit's
  parent is fast-forwarded to that exact commit (attached branch or detached
  HEAD). Any other adopting member gets a cherry-pick: a commit with the
  canonical author, message and control blobs on the member HEAD, built with a
  private index and normal hooks and signing, exactly as the canonical commit.
  A cherry-pick on a detached HEAD is reported as reachable only from that
  HEAD. No branch is created or moved other than the member's checked-out
  branch advancing by its own commit. A separate clone first fetches the
  canonical commit's objects from the canonical checkout by local path with
  `--no-write-fetch-head`, which updates no ref. Nothing is pushed.
- D6 Fallback. A member with modified controls, or whose control blobs differ
  from the canonical parent (the cherry-pick would conflict, detected while
  planning, so no cherry-pick is started), is upgraded independently and left
  uncommitted, with the reason and a recovery hint (`git pull --ff-only` or
  rebase, then `mask repair`). Grouped mode never creates an independent
  commit in a member.
- D7 Disclosure. Dry-run and results include `groups` with the identity,
  canonical checkout, selection reason and each member's branch, action and
  reason. The plan hash covers the groups and each propagating member's Git
  observation.
- D8 Cross-home coordination (Windows profile versus WSL) is out of scope.
  WSL clones registered in another MASK home should `git pull --ff-only` and
  run `mask repair`, which already acquires locked commits that are missing
  from the tap cache. Whether `upgrade` in a clone whose committed lock is
  ahead of the cached tap should fetch instead of failing is
  [MASK-0147](../10-backlog/MASK-0147-upgrade-lock-ahead-of-cache.md).

## Acceptance

- AC1: `upgrade --all` groups registered projects by D2, chooses the canonical
  checkout by D3, resolves once there and propagates by D4 to D6. Dry-run and
  JSON show the grouping and per-member actions; the plan hash covers them.
  `--independent` restores the previous behavior.
- AC2: With `--commit`, exactly one upgrade commit is created per repository;
  other members are fast-forwarded to it or get a cherry-picked commit
  (including a detached HEAD), and fallback members are reported uncommitted.
- AC3: Unit tests cover identity normalization, grouping and canonical
  selection. An integration test with real Git covers two worktrees and two
  clones of one repository plus an unrelated repository.
- AC4: CLI help, README and docs describe the default and the opt-out. The
  full suite and the documentation gate show no new failures against the
  baseline.
