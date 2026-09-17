# Migrating from a live checkout

Converting a machine or consumer from the retired live-checkout model to taps with `mask doctor --migrate`, the old commands and their replacements, pinned updates, per-skill agent selection, local compatibility policy and adapter facts.

## Migration

The live-checkout program recorded one clone as the machine's single source, and every link pointed into that clone. MASK now deploys every selection from a lock and `MASK_HOME/store`. `mask doctor` converts an existing machine. Migration is best effort and meant to run once per machine.

Finish any pending recovery with the program that wrote it before switching to this version. `mask recover --inspect` shows a journal from the live-checkout program, but recovery does not replay it.

### Check what would convert

`mask doctor` reports `data.migration`: the machine (`legacy_v1`, `legacy_v2` or `current`), the proposed tap, the clone's HEAD, branch, dirty, unborn and published state, and a row per legacy consumer with its links and blockers. `mask doctor --check` exits 7 while migration is required.

On a v1 or v2 machine configuration, only `capabilities`, `config show`, `doctor`, `recover` and the `self` commands run. Every other command exits 4 with `migration.required`, naming `mask doctor --migrate --dry-run`.

### Convert the machine

```sh
mask doctor --migrate --dry-run --json
mask doctor --migrate --expect-plan-hash RETURNED_HASH --json
```

The dry run writes nothing. It discloses the configuration before and after, the proposed tap, each consumer's declaration, lock and link changes, and the cache acquisition. The guarded apply refuses `plan.stale` if the clone's HEAD, a consumer declaration or an owned link changed since the preview. One recoverable `doctor.migrate` journal then converts the machine configuration and every registered legacy consumer, all or nothing:

- The clone becomes a tap whose repository is the clone's configured remote. A clone without a remote becomes a machine-local `file://` identity, with warning `migration.local_only_source`. The tap's `authoring` keeps the clone path, so `source publish` and `source dev-link` still work from it.
- `--alias NAME` names the tap. Without it, a v2 machine keeps its existing legacy alias (normally `legacy`). A v1 machine derives the alias from the remote's repository name in lowercase (`AgentSkills` becomes `agentskills`), or falls back to `legacy`. A v2 machine's other taps are kept. An alias that already names a different tap refuses `source.alias_conflict`.
- Each v1 declaration becomes a v2 declaration bound to that alias. Its lock names the clone's current HEAD, which is acquired into the tap cache from the local clone over file transport, without network access.
- Payloads are materialized in the store, owned links are retargeted from the clone to the store, and the consumer records become pinned.
- With no registered consumers, only the configuration migrates, and a dirty or unborn clone is only a warning.

If HEAD is not on the remote-tracking branch, migration warns `migration.unpublished_commit`: other machines cannot reproduce those locks until you push that commit. The first `mask upgrade` afterwards fetches the remote normally.

Migration never resets, stashes, deletes or pushes anything. It refuses with a typed error, writing nothing, when the clone is:

- dirty (`source.dirty`), including untracked files, a sparse checkout, hidden index flags or an unfinished merge or rebase;
- unborn (`migration.unborn`);
- detached, on another branch or diverged from its remote-tracking branch (`source.identity_mismatch`);
- missing (`source.missing`).

Changed or colliding owned links, a declared skill absent at HEAD and a registered legacy consumer that already declares a v2 selection also block migration. On a v1 or v2 machine, `--project` and `--user` are invocation errors (exit 2), because the whole machine migrates together.

If `doctor --migrate` cannot convert a consumer, restore that consumer on disk (its v1 declaration and its recorded links into the clone), then retry. `project unregister --keep-links` and `workspace forget` stay refused until the machine is migrated.

An interrupted migration leaves its `doctor.migrate` journal; inspect it with `mask recover --inspect`. `mask recover --rollback` restores the exact prior configuration, declarations and links, and removes the created locks. `mask recover --complete` finishes the recorded conversion, but refuses if the clone changed since planning. Recovery never modifies the clone, and prepared cache and store content is retained.

### Convert a straggler on a tap machine

A v1 `.mask.json`, or a v1 personal `user.json`, can remain after the machine is migrated; `mask doctor --project PATH` reports it. A consumer record left by the live-checkout program converts the same way. Fetch the tap, then convert the declaration with install semantics:

```sh
mask source fetch agentskills --json
mask doctor --migrate --project /path/to/project --alias agentskills --dry-run --json
mask doctor --migrate --project /path/to/project --alias agentskills --expect-plan-hash RETURNED_HASH --json
```

Use `--user --alias NAME` for the personal declaration. The declaration is rewritten to a v2 declaration bound to the approved tap `NAME`. It is then resolved (fetching on demand unless `--offline`), registered and linked from the store, all through one `doctor.migrate` journal, and the configuration is unchanged. `--dry-run` never fetches, so a tap that is not cached refuses `lock.resolution_required`. Rerunning on a converted scope is a no-op.

## Old commands

| Old command | Use instead |
|---|---|
| `mask init --source PATH` | `mask tap add NAME URL`; add `--checkout PATH` to keep authoring from the clone. An existing machine migrates with `mask doctor --migrate`. |
| `mask init --remote REMOTE`, `mask init --branch BRANCH` | `mask tap add NAME URL --ref REF` |
| `mask source status` | `mask source show NAME` and `mask doctor` |
| `mask source migrate` | `mask doctor --migrate` |
| `mask migrate --to-pinned` | `mask doctor --migrate`; on a tap machine, `mask doctor --migrate --project PATH --alias NAME` or `--user --alias NAME` |
| `mask upgrade` fast-forwarding the shared checkout | `mask upgrade`, which fetches every referenced tap and updates locks and store links. Push authoring changes first, or use `mask source dev-link` for unpublished edits. |
| `mask project require ID`, `mask user require ID` | `mask install ID`, with `--user` for personal skills |
| `mask project unrequire ID`, `mask user unrequire ID` | `mask remove ID`, with `--user` for personal skills |
| `mask project set --skill ID`, `mask project set --clear` and the `user set` forms | `mask install` and `mask remove` for each skill that differs |

The removed commands and `init` options exit 2 with `invocation.invalid`. The `project` and `user` `set`, `require` and `unrequire` commands refuse `selection.command_unsupported`.

## Pinned updates and development links

`mask upgrade --project PATH --skill SOURCE/ID` fetches that binding's tap and updates only that pin through one recoverable lock/link operation. Preview it with `--dry-run`, which uses cached objects and never fetches. Exact commit requirements stay fixed.

For scoped authoring, `mask source dev-link SOURCE/ID --project PATH
--authoring-root PATH --json` makes an explicit dirty/unpinned exception from the
tap's approved authoring checkout. Return
with `--to-pinned` in place of `--authoring-root`. Ordinary apply and ensure
refuse live overrides, and update skips or refuses them. `mask source publish SOURCE --paths PACKAGE_PATH --json`
previews exact package publication. Add `--commit` and separately `--push` only
when those effects are intended. Publication preserves the authoring HEAD/index
and reports its separate commit/ref. See the
[CLI contract](../architecture/cli-contract.md#explicit-migration-selected-updates-and-authoring-exceptions)
for recovery, authority and platform limits.


### Per-skill agents and local compatibility

Registered v2 consumers can choose agents independently:

```sh
mask project set-agents vendor/alpha codex --apply --json
mask user set-agents vendor/alpha claude --apply --json
mask project set-agents vendor/alpha --inherit --apply --json
mask project set-targets --inherit --apply --json
```

`--all` on `set-agents` selects supported, locally enabled agents. `--inherit`
removes the binding choice; `set-targets --inherit` restores the v2 `all` default.
Run `project register` or `user register` first; registration without `--apply`
is supported. Without `--apply`, setters update declaration, coherent lock and
cached desired selection while retaining current owned links. Preview with
`--dry-run` and apply its `--expect-plan-hash` to guard the exact intent.

Bindings whose `when.platforms` or `when.architectures` do not match are reported
`not_applicable`, retain their lock rows, and need no artifact preparation.
Missing compatibility metadata means unspecified. Generic and specific metadata
are publisher assertions, never evidence that a skill was tested. Explicit
incompatible requests block; implicit `all` can exclude incompatible agents.
Requirements are informational and never execute or install tools.

Local policy defaults to both Claude and Codex without detecting executables:

```sh
mask selection-policy set --agent codex --dry-run --json
mask selection-policy clear --json
mask compatibility override vendor/alpha --project /path/to/project \
  --agent claude --reason "Reviewed for this project" --dry-run --json
mask compatibility clear vendor/alpha --project /path/to/project --json
```

Global enabled-agent changes reconcile every registered consumer; explicit
requests for disabled agents block the change.
Overrides affect one physical project or registered `--user` scope and one
coordinate. `--platform` and `--architecture` name the current device dimension.
Every override needs a reason and produces a warning; it cannot enable an
unsupported/disabled adapter or grant source trust. Local policy is bounded to
1 MiB and is never imported from a package. Policy, declaration and lock effects
use the existing recoverable journal. Dev-link evaluation reads validated live
metadata and remains unpinned. Identical coordinate/content contributions merge positive agent edges with all
origins retained. Different artifact authority under one coordinate refuses;
different coordinates conflict only when they share an agent invocation path.
Disjoint agents/scopes are allowed. Public profile storage remains separate work.


### Adapter facts and conflicting names

`mask capabilities --json` exposes the built-in Claude/Codex adapter contract:
project/personal discovery paths, startup configuration paths, reserved names,
package hazards and recorded readiness evidence. macOS/Windows readiness evidence
is distinct from first-prompt host loading, which remains unverified. Linux
behavior remains best-effort; no executable detection changes the agent set. The
`workflow` entry (`readiness: workflow_readiness_v1`, `native_roles`,
`staged_setup`, the entrypoints that share the verdict) is what an upstream
startup preflight must require before accepting a workflow-ready result.

A plan rejects different source coordinates named `alpha` when both require, for
example, the same project's Codex `alpha` path. It reports both coordinates,
origins and exact artifact claims. Assigning those coordinates to disjoint agents
is allowed. MASK never renames a package or chooses a last contribution. Equal
coordinate, repository identity and payload/metadata/provenance digests merge
positive agent selections, retaining all exact commits/selectors and origins.
Inapplicable contributions retain their lock attribution without participating
in conflicts or requiring their content. Public profile storage is still RFC10.

`plan`, `apply`, and project/user `show` expose `shadowing` and
`target.scope_shadowing` warnings for user/project discovery names. Observed owned
links and prospective overlaps are distinguished, and an overlap whose scopes
resolve to one directory is reported as `same_target` without a warning. Both
scopes remain independent; MASK does not assert which one the host loads. Full pinned where-used inventory
remains a separate reporting slice.
