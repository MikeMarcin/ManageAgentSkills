---
id: "RFC-MASK-0025"
title: "Fleet command defaults and approved program and skill maintenance"
status: "Auto-Verified"
owner: "MikeMarcin"
created: "2026-11-05"
metadata: {"milestone_plan":{"id":"fleet-command-maintenance","path":"docs/rfcs/plans/fleet-command-maintenance/milestone-plan.json"}}
---

# RFC-MASK-0025: Fleet command defaults and approved program and skill maintenance

Follow-on to [fleet transport](RFC-MASK-0012-fleet-enrollment-and-transport.md),
[fleet rollouts](RFC-MASK-0013-fleet-rollouts-and-continuous-sync.md) and
[local upgrade commits](RFC-MASK-0024-upgrade-auto-commit.md). The November 5
owner clarification assigns program maintenance to `fleet update` and skill
maintenance to `fleet upgrade`. Previous fleet acceptance remains historical.

- AC1. `fleet install SKILL` plans an exact approved tap selection for enrolled
  active devices and their personal rollout scopes. Explicit targets, configured
  mode and copy review retain their existing meaning.
- AC2. `fleet upgrade` and `fleet upgrade --all` review exact skill upgrades for
  granted scopes, respect pins and keep locally selected skills separate from
  fleet contributions. Project upgrades use one canonical commit per eligible
  repository with exact fast-forward or cherry-pick. They preserve unrelated
  edits and block controls drift. No project Git commit occurs in personal scope.
- AC3. Bare `fleet update` reviews one exact program revision for all active
  enrolled devices. Repeated `--device NAME` options select a subset. The update
  requires distinct device authority, an approved origin and the checked local
  updater. Incompatible, blocked, disconnected and unknown peers remain visible.
  `fleet update SOURCE/ID` retains its signed rollout meaning.
- AC4. Prove the public paths in disposable macOS and Windows fixture checkouts.
  Record exact source, signed receipts, convergence or pending states, and
  cleanup. Production enrollment and publication are outside this milestone.

The owner amended AC3 to remove the redundant `--all` spelling from
`fleet update`. The [native verification record](../development/fleet-native-acceptance.md#fleet-command-maintenance)
preserves the commands exercised at their original revisions.

Closeout: [MASK-0149](../issues/60-done/MASK-0149-fleet-command-maintenance.md).
