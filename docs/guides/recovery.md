# Recovery, cleanup and retirement

If an interrupted setup blocks another command, run:

```sh
mask repair
```

MASK names the interrupted setup's location, which may be a different checkout
from the one you are in. It offers to finish publishing validated role files, or
roll back an attempt whose outputs were never validated. Review and confirm that
specific recovery. The command stops after recovery; retry your original command
or run `repair` again to check readiness. Earlier committed links or setup groups
remain committed. Package script side effects are unknown and are not rolled back.

For automation, preview and approve the exact recovery:

```sh
mask repair --dry-run --json
mask repair --approve-plan RETURNED_HASH --json
```

`mask recover` (also `mask recover --inspect`) is advanced, read-only inspection.
Non-setup operations still require explicit advanced recovery: inspect first, then
preview `mask recover --complete --dry-run` or `mask recover --rollback --dry-run`.
Remove `--dry-run` to apply the chosen direction when its checks pass.

Recovery validates current bytes, physical roots, source identity and control
snapshots. Changed inputs, controls or destination files block recovery and are
preserved. For an already validated, role-only setup publication, committing
unrelated work or unchanged declaration/lock files does not block recovery: Git
HEAD and index may advance while the exact generation inputs and all other guards
must still match. Broader operations retain their Git guards. Recovery never
reruns a setup script.

Old journal versions remain readable even though old public command spellings have
retired. Program self-update preserves protocol/schema compatibility checks; a
breaking program transition needs an explicitly reviewed checkout update.

An interrupted `mask update` recovers its program checkout without resetting Git.
Uncommitted changes that the fast-forward does not touch never block recovery.
`recover --complete` refuses with `source.dirty` and `blocking_paths` only when
local changes touch files the update changes. `recover --rollback` never moves the
checkout, so local changes never block it. When the update ran with `--stash`, the
journal records the stash message and, once Git made it, its commit. `mask recover`
reports that stash and `git stash show -p <id>` in every mode. Recovery never pops,
applies or drops it.

## Reclaim unused storage

```sh
mask cleanup --dry-run --json
mask cleanup --approve-plan RETURNED_HASH --json
```

Cleanup lists exact paths and reclaimable bytes. It removes verified unused payloads,
unused owned tap caches, disposable backups and recognized retired generated files.
There is no age-only backup retention policy and no automatic cleanup after upgrade.

Current declarations/locks, referenced versions, in-use native-role locks and pending
recovery protect their data. Unavailable registered roots prevent unsafe assumptions
about references. Modified backups, unknown files, links and unverifiable staging
are preserved and reported. A persistent lifecycle lock excludes cleanup throughout
another operation's preparation and publication. The existence of `operation.lock`
or `lifecycle.lock` does not mean it is stale; neither file is deleted by cleanup.

## Stop managing a checkout

```sh
mask unregister
mask unregister /path/to/checkout
mask unregister --user
```

Unregister removes unchanged owned deployment and the registration, preserving the
declaration and version lock. `--keep-links` explicitly leaves links in place and
abandons ownership. `workspace forget PATH --expect-identity VALUE` is the narrower
retirement operation for a removed Git worktree: it verifies the recorded identity
and absence from the original worktree list, without pruning unavailable roots.

To remove MASK itself, first disable its integrations and unregister consumers you
intend to retire, then preview `mask self uninstall --dry-run`. Self-uninstall removes
only unchanged launchers that MASK owns, preserves the program checkout and remaining
data, and reports what remains. Cleanup never deletes arbitrary consumer directories.
