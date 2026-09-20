# Recovery, cleanup and retirement

When an operation is interrupted, inspect its pending journal before another mutation:

```sh
mask recover --inspect --json
mask recover --complete --json
```

Choose `--rollback` instead when the journal permits restoring the before-state.
MASK validates current bytes, physical roots, source identity and control snapshots.
Changed files or Git state can block either direction; preserve them and inspect the
typed error. Recovery never reruns a setup script. A script that exited before its
outputs were validated requires rollback of that publication. Earlier committed
links or setup groups remain reported as committed.

Old journal versions remain readable even though old public command spellings have
retired. Program self-update preserves protocol/schema compatibility checks; a
breaking program transition needs an explicitly reviewed checkout update.

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
