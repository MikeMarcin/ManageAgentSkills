# Doctor migration contract

Normative for RFC-MASK-0020-AC04 and AC05. Migration converts a live-checkout
machine and its consumers to the tap model through the existing recoverable
journal. It never resets, stashes, deletes, pushes or edits the user's clone.

## Modules

- `mask_legacy.py` (new): the only module permitted to read v1/v2 machine
  configuration, mode-less consumer records and v1 declarations. Exposes
  `inspect(home, roots) -> report`.
- `mask_migrate.py` (new): ports `authoring_snapshot`, `migrated_selection`,
  `validate_migration` and `check_migration` from `mask_pinned.py` and the
  migrate branch of `transition_dispatch`; adds `migrated_config`,
  `acquire_from_clone` and the doctor entry point.

## Detection

| Input | Report |
|---|---|
| `config.json` with `schema_version` 1 | `machine: legacy_v1`, `source.root/remote/branch` |
| `config.json` with `schema_version` 2 | `machine: legacy_v2`, existing `legacy_source` alias |
| State record without `mode` (or `mode: legacy`) | consumer `mode: legacy`; expected legacy target `<clone>/skills/<id>`; per-link observation `ok`, `drift`, `missing` or `collision` |
| Registered consumer whose `.mask.json` or `user.json` is v1 | `declaration_version: 1` |
| `--project PATH` naming an unregistered directory with a v1 `.mask.json` | unregistered consumer row |
| `--user` with a v1 `user.json` and no user record | unregistered personal row |

`clone` observations: `root`, `head`, `branch`, `dirty`, `unborn`, `published`
(`true` when HEAD is an ancestor of `refs/remotes/<remote>/<branch>`, `false`
when not, `unknown` without a remote-tracking ref).

## Mapping

| Legacy fact | Migrated value |
|---|---|
| Alias | `--alias`, else the v2 `legacy_source`, else the remote basename lowercased when it is a valid alias (`AgentSkills` becomes `agentskills`), else `legacy` |
| `repository` / `transport` | `git remote get-url <remote>` normalized; without a remote, the clone path as a `file` identity plus warning `migration.local_only_source` |
| `authoring` | the clone path |
| `ref` | the configured branch |
| `packages` | `skills` |
| v1 declaration | `{schema_version: 2, sources: {alias: {repository, packages: "skills", ref: "refs/heads/<branch>"}}, default_agents: legacy targets or config default_targets, skills: [{source: alias, id}]}` |
| Lock rows | one per skill at the clone HEAD: `path` from package discovery at HEAD, payload digests from `mask_packages.validate`, `selector: {ref: "refs/heads/<branch>"}`, object format from the clone |
| Cache | HEAD acquired into the tap cache from the local clone: bare-init with the tap's `mask-source.json`, `git fetch <clone> +<head>:refs/mask/frozen/<head>` with `protocol.allow=never` and `protocol.file.allow=always`, existing byte limits; no `refs/mask/selected`, no `mask-refs.json` |
| Links | retargeted from `<clone>/skills/<id>` to the store payload through the shared planner with `allow_migration=True`, `operation: doctor.migrate` |
| Records | `mode: pinned`, `last_lock` set, `last_source_revision` null |
| Existing different tap under the chosen alias | `source.alias_conflict` (4) |

Acquiring from the local clone is chosen because it works offline, the deployed
bytes are exactly the clone's HEAD (which may be ahead of origin), and identity
is still checked against the remote URL through `sources.endpoint`. When
`published` is `false` the result carries warning `migration.unpublished_commit`.
The first `mask update` afterwards fetches the remote normally.

## Scope and atomicity

On a v1 or v2 machine `--migrate` must be unscoped or `--all`: the machine
configuration and every registered legacy consumer migrate in one journal,
all-or-nothing. Non-migratable consumers block the whole migration with typed
blockers; remediation is `project unregister --keep-links` or
`workspace forget`, then retry. A machine whose registry is empty migrates its
configuration only: journal `files` holds the `machine_config` role, `selected`
is empty, no cache, store or link effect occurs, and a dirty clone is a warning
rather than a refusal because nothing locks its HEAD.

On a v3 machine `--migrate --project PATH --alias NAME` (or `--user --alias
NAME`) converts a straggler v1 declaration: rewrite it to v2 bound to `NAME`,
resolve through the ordinary binding resolver (fetching on demand unless
`--offline`), register and link. This is install semantics with a declaration
rewrite.

## Journal

`pending.operation = "doctor.migrate"` (added to the pending v3 schema
enumeration; `migrate` is removed). `pending.migration = {config_before,
config_after, source: {root, identity, head, branch, index, repository,
object_format}, cache: {alias, path, commit}}`. Typed files: `machine_config`,
per-consumer declaration and lock roles, and the link entries.

`validate_migration` checks that `config_after` equals
`mask_migrate.migrated_config(config_before, home, alias)`, that
`source.root` equals `config_after.sources[alias].authoring`, that every
migrated selection equals the mapping of the observed v1 declaration, and that
every lock commit equals `source.head`. `check_migration` re-snapshots the clone
before completion. `recover --rollback` restores the exact prior configuration,
declarations and links and removes created locks; `recover --complete` finishes
the recorded intent. Recovery never touches the clone.

## Preconditions and refusals

| Condition | Code | Exit |
|---|---|---|
| Pending journal | `recovery.required` | 8 |
| Clone missing or not a checkout root | `source.missing` | 3 |
| No commit on HEAD (consumers present) | `migration.unborn` | 4 |
| Dirty worktree, sparse checkout, skip-worktree or assume-unchanged flags, unfinished merge/rebase/cherry-pick (consumers present) | `source.dirty` | 4 |
| Detached HEAD or a branch other than the configured one; v2 remote not matching the approved identity | `source.identity_mismatch` | 4 |
| Alias already bound to a different repository | `source.alias_conflict` | 4 |
| Registered project directory missing or identity changed | `project.unavailable` / `project.identity_changed` | 4 |
| Owned link text differs from the record, unmanaged link, real entry in the way | `target.drift` / `target.unmanaged_link` / `target.collision` | 4 |
| Declared skill absent at HEAD | `skill.unknown` | 4 |
| Cache growth over policy | `source.fetch_limit` | 4 |
| Serialized control over 4 MiB | `lock.limit` | 4 |
| Snapshot or clone changed between preparation and the writer lock | `plan.stale` | 4 |

`--dry-run` computes and discloses the full plan (config diff, proposed tap,
per-consumer declaration/lock/link changes, cache acquisition) and writes nothing.
`--expect-plan-hash` binds the reviewed plan; a changed clone HEAD or consumer
control yields `plan.stale`.

## The owner's machine

`~/.mask/config.json` is v1 with `source.root` `C:\code\git\AgentSkills`,
`remote` `origin`, `branch` `main`; `state.json` has no projects and no user
record. `doctor` must report `machine: legacy_v1`, `consumers: []` and
`proposed_tap` with alias `agentskills`; `doctor --migrate` must write config v3
only and afterwards `doctor --check` exits 0, `mask install implement-rfc --user`
fetches the tap and links from the store, and `mask update` fetches and no-ops.
This run is the attended dogfood card and is recorded, not assumed.
