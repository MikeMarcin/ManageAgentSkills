# CLI contract amendments for tap-only deployment

Normative for RFC-MASK-0020. Exit codes follow the existing contract: 0 success,
2 invocation, 3 configuration/input, 4 refusal, 5 environment, 7 doctor drift,
8 recovery required, 10 invariant. Every command keeps `--json`, `--dry-run` on
mutating commands, and the single-document result envelope.

## Command inventory changes

| Command | Principal arguments | Writes | Network | Change |
|---|---|---|---|---|
| `init` | `[--target TARGET ...] [--git-timeout SECONDS]` | Machine config v3 with an empty catalog, empty state | No | `--source`, `--remote`, `--branch` removed |
| `tap add` | `NAME URL [--ref REF] [--packages PATH] [--checkout PATH]` | Catalog; also creates config v3 and state when missing | No | Bootstraps a machine |
| `tap remove` | `NAME` | Catalog only; cache retained | No | Unchanged |
| `install` | `ID-or-SOURCE/ID ... [--project PATH | --user] [--agent AGENT ...] [--offline] [--expect-plan-hash HASH]` | Declaration, lock, registration, store, links, state; tap cache on live resolution | Only for live resolution | Always v2; never links a checkout |
| `remove` / `list` | unchanged | unchanged | No | Legacy branches removed |
| `update` | `[--project PATH | --user | --all] [--skill SOURCE/ID ...] [--allow-ref-rebind] [--offline] [--expect-plan-hash HASH]` | Locks, store, links, state for selected consumers | Fetches each referenced tap once unless `--dry-run`, `--offline` or `--expect-plan-hash` | Unscoped form selects every consumer; no shared checkout |
| `source fetch` | `[NAME] [--locked ...]` | Tap caches | Yes | No name fetches every approved tap |
| `source list` / `show` / `inspect` | unchanged | None | inspect only | `migration_required` flag removed |
| `doctor` | `[--project PATH | --user | --all] [--check]` | None | No | Adds `data.migration` |
| `doctor --migrate` | `[--alias NAME] [--project PATH | --user | --all] [--dry-run] [--expect-plan-hash HASH]` | Config v3, tap cache, store, declarations, locks, links, state through one journal | No (file transport from the local clone only) | New guarded mutating form |
| `config show` | none | None | No | Reports `migration_required` on v1/v2 |
| `source status` | | | | Removed |
| `source migrate` | | | | Removed |
| `migrate` | | | | Removed |
| `project set` / `require` / `unrequire`, `user set` / `require` / `unrequire` | unchanged | v2 declaration and lock | No | v1 branches removed |

`capabilities` publishes `schemas.machine: 3`, `readable_versions.machine: [1, 2, 3]`
(1 and 2 read for migration only), `deployment_model: "taps"` and
`migration: "doctor"`. `GUARDED` gains `doctor` (for `--migrate`).

## Machine configuration

`MASK_HOME/config.json` v3: `schema_version` 3, `default_targets`,
`git_timeout_seconds`, `sources` with 0 to 256 tap entries. A tap entry keeps the
v2 shape: `repository` (normalized credential-free identity), `transport`, `cache`
(`MASK_HOME/sources/<alias>-<16 hex>.git`), `ref` (update selector), `packages`,
`authoring` (absolute checkout path or `null`). The schema draft is
`machine-v3.schema.json` beside this file.

`mask_core.config(value, *, legacy=False)` parses v1, v2 and v3. With
`legacy=False` (the default for every command) a v1 or v2 value fails
`migration.required` (exit 4) with details `schema_version` and a remediation
argv `mask doctor --migrate --dry-run`. `capabilities`, `config show`, `doctor`,
`recover` and `self *` pass `legacy=True`.

## Bootstrap journey

```sh
python3 /path/ManageAgentSkills/mask.py self install --bin-dir "$HOME/.local/bin"
mask tap add agentskills https://github.com/MikeMarcin/AgentSkills.git
cd /work/project
mask install implement-rfc
mask list
mask ensure
```

`tap add` on a machine without `config.json` reports actions `config.create` and
`source.catalog`; dry run reports both as planned. `install` reports
`data.acquisitions[]` with the fetched tap and `data.network: "fetch"` when a
live resolution fetched.

Typed outcomes on the install path (all existing codes):

| Situation | Code | Exit |
|---|---|---|
| No machine config | `config.missing`, remediation `mask tap add NAME URL` | 3 |
| `--offline` before any fetch | `lock.resolution_required` with `source` | 4 |
| Bare ID while a tap is unfetched | `source.unresolved` naming the taps | 4 |
| Bare ID present in several taps | `skill.ambiguous` with `SOURCE/ID` choices | 4 |
| Unknown alias | `source.unknown` | 4 |
| Authoring checkout origin differs from the tap identity | `source.identity_mismatch` | 4 |

## Update semantics

1. Preconditions: no pending journal (`recovery.required`, 8); config v3;
   `--skill` coordinates must exist in the selected consumers
   (`invocation.invalid`, 2).
2. Selection: no scope flag selects every registered consumer; an empty registry
   returns exit 0 with warning `project.empty_registry` and no fetch. Dev-link
   consumers are skipped with a `dev_link.active` warning by the unscoped form and
   refused (4) by a scoped form.
3. Referenced taps are the union of `declaration.sources` over the selected
   consumers, restricted to the taps of the named `--skill` bindings when given.
4. Fetch phase (only without `--dry-run`, `--offline`, `--expect-plan-hash`):
   `sources.fetch` once per tap; `data.fetches[alias] = {attempted, ok, before,
   after, remote_refs_changed, error}`. Git and source family errors are captured
   per tap; recovery and invariant errors propagate.
5. Consumers referencing a failed tap are `blocked` and excluded from the plan;
   the others proceed. A scoped update whose only tap failed is a plain refusal
   with the Git error (exit 5).
6. Resolution per consumer from cache with the existing candidate resolver.
   `lock.ref_rebound` refuses the whole invocation (4) unless
   `--allow-ref-rebind`. `lock.resolution_required` under dry-run/offline marks
   the consumer `blocked` with `requires_fetch: true` instead of failing.
7. Disclosure: `data.consumers[] = {root, scope, status: updated | unchanged |
   blocked | skipped, changes: [{coordinate, before_commit, after_commit,
   before_digest, after_digest, selector}], error}`; then the ordinary public plan
   and `--expect-plan-hash` guard. A guarded rerun never fetches.
8. Apply: store preparation, writer lock, snapshot recheck, one journal with
   `operation: update`, then the shared readiness final status.
9. Exit: any `blocked` consumer after the rest applied or no-oped ends
   `update.incomplete` (4) naming the blocked roots with a truthful committed
   transaction.

The `scope.expand` consent of the shared-checkout update is retired with it.

## Doctor

`mask doctor` adds `data.migration`:

```json
{"required": true,
 "machine": "legacy_v1",
 "proposed_tap": {"alias": "agentskills", "repository": "https://github.com/MikeMarcin/AgentSkills.git",
                  "transport": "https://github.com/MikeMarcin/AgentSkills.git",
                  "authoring": "C:\\code\\git\\AgentSkills", "ref": "main", "packages": "skills"},
 "clone": {"root": "C:\\code\\git\\AgentSkills", "head": "<40 hex>", "branch": "main",
           "dirty": false, "unborn": false, "published": true},
 "consumers": []}
```

`consumers[]` rows carry `root`, `scope`, `registered`, `declaration_version`,
`mode`, `skills`, `links` (per-link `ok | drift | missing | collision`),
`migratable` and `blockers`. `issues` gains `migration.required`; `--check` exits
7. `--migrate` conflicts with `--check`; `--expect-plan-hash` without
`--migrate` is `invocation.invalid`. Full migration semantics are in
`MIGRATION.md`.

## Help and documentation

`mask --help` start-here text, `mask update --help`, `mask doctor --help`,
`README.md`, `docs/guides/installation.md`, `docs/guides/sources-and-updates.md`,
`docs/guides/migration-and-pins.md` (retitled to migrating from a live checkout),
`docs/architecture/cli-contract.md` and `docs/architecture/state-and-recovery.md`
describe only the tap model. A documentation test asserts that the retired
spellings `init --source`, `source migrate`, `migrate --to-pinned` and
`source status` appear only under `docs/rfcs/assets`, in historical RFC text and
in the migration guide's old-command table.
