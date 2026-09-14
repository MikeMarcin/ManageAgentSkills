# Local state and recovery data

The public API is the CLI, not these internal files. This page describes the current tap-model serialization under `MASK_HOME` (RFC-MASK-0020). No agent hand-edits it during ordinary management. The schema files named below document the closed JSON shapes; runtime validation is stricter (canonical roots, digests, recomputed paths, source approval).

## config.json

`schemas/machine-v3.schema.json`. Version 3 holds `default_targets`, `git_timeout_seconds` and `sources`, 0 to 256 taps keyed by alias. A tap entry records `repository` (a normalized, credential-free identity), `transport`, `cache`, `ref`, `packages`, `authoring` and the optional `line_endings`: `exact`, or `autocrlf` from `tap add --autocrlf`. An entry without `line_endings` keeps exact bytes. `authoring` is null or the tap's authoring checkout, which `source publish`, `source dev-link` and curated imports use; it is never an ordinary link target. `init` and a bootstrapping `tap add` write an empty catalog.

Versions 1 and 2 (`machine-v1.schema.json`, `machine-v2.schema.json`; `machine.schema.json` selects the version) come from the retired live-checkout program. Only `config show`, `doctor` (with or without `--migrate`), `recover` and `self *` read them. Every other command except `capabilities` refuses them `migration.required` (exit 4) before any effect.

## state.json

`schemas/state.schema.json` selects `state-v1`, `state-v2` or `state-v3.schema.json`. `init` and a bootstrapping `tap add` write the empty version 1 registry; storing the first pinned or dev-link record writes version 3.

- The registry holds `generation`, `projects` keyed by canonical root, `user` (the personal-scope record or null) and `launchers` (owned launcher path to program root, interpreter and content digest; not a command list loaded from a project).
- A current consumer record has `mode` `pinned` or `dev-link`, `root`, `root_identity`, `last_manifest` (its v2 declaration, `project-v2.schema.json`) with `last_manifest_digest`, `last_lock` (`lock-v1.schema.json`), `last_source_revision` null and optional `native_roles` (owned role files with their SHA-256).
- `links` maps each agent-relative path to `skill`, `target`, the exact owned `link_text` and `resolution`, the lock row it deploys. The link text names `MASK_HOME/store/v1/<payload hex>/payload/<id>`; on native Windows it is the extended `\\?\` spelling that readlink returns.
- A `dev-link` record adds `dev_links` and a per-link `dev` binding (source, ID, authoring root and identity, package path). Only an explicit `source dev-link` produces a link text into an authoring checkout.
- A record without `mode` is a live-checkout record. It stays readable so `doctor` can report it and `doctor --migrate` can convert it; the planner refuses it `migration.required` and never derives a link target from it.

The root identity is an available-platform consistency check, not a globally stable UUID or proof of ownership; never infer that a replacement directory is owned because it occupies the same path. Validate each registry key against its canonical root and recompute each relative link path from its agent and skill; the on-disk link's raw value must still agree before unlink. Desired links derive from the live declaration and lock, not the cached `last_manifest`. A true no-op does not increment `generation` or rewrite cached fields, and read-only inspections write nothing.

## Caches and store

- `MASK_HOME/sources/<alias>-<digest prefix>.git` is one bare Git cache per tap, marked by `mask-source.json`. `tap add` never fetches; `install`, `update`, `source fetch` and `doctor --migrate` acquire into it.
- `MASK_HOME/store/v1/<payload hex>/` holds `manifest.json` (`schemas/artifact-v1.schema.json`) and `payload/<id>`: content-addressed payloads, verified before reuse and shared by identical content.

Cache and store writes are MASK-owned preparation effects made before a journal exists. They are reported (`preparation`, `retained_directories`) and retained: neither a failed operation nor `recover --rollback` removes them, and nothing prunes them.

## pending.json

`schemas/pending.schema.json` selects `pending-v1`, `pending-v2` or `pending-v3.schema.json`, or `pending-integration-v3.schema.json` for `integration.enable` and `integration.disable`. A journal records `operation`, `phase`, `base_generation`, the `selected` canonical roots, `links` (root, relative path, skill, target agent, exact `before` and `after` link text or null), `manifests`, `before_state` and `after_state` with their exact UTF-8 text, the planned `config` and the `directories` it may create. A journal that touches a pinned consumer is version 3. It adds `pinned` (the observed consumer workspaces and the exact `config.json`, `integration.json` and selection-policy text) and typed `files`, each with exact before and after text or null: `project_declaration`, `project_lock`, `user_declaration`, `user_lock`, `selection_policy` and `machine_config`. Other extensions record readiness controls, native roles, staged setup and retired-file repair. The only Git intent is `self update` of this program's own checkout (`git.scope` `program`). A journal never contains credentials, script bodies to execute, arbitrary command lines or a copy of source history.

The intent is written before the first effect. Recovery validates the whole intent against the fixed adapters, the selected registered roots and the current filesystem before any effect; no journal path is blindly trusted.

**`update`.** `update` fetches each referenced tap once under the writer lock and materializes store payloads before it writes its journal. One `update` journal then carries the lock and link changes of every applied consumer. It recovers like any pinned journal, and the fetched objects and payloads stay.

**`doctor.migrate`.** Migration is best effort (owner decision recorded in RFC-MASK-0020).
- **Journal shape.** A machine migration of a v1 or v2 configuration is one version 3 journal with no `manifests`. Its typed `files` end with the `machine_config` role: the exact `config.json` before and after bytes. Its `migration` field records:
  - `config_before` and `config_after`;
  - `source`, the legacy checkout observed at planning: root, identity, HEAD, branch, index digest, repository and object format;
  - `cache`: alias, cache path and the commit acquired from the clone. It is null when the registry is empty, and then only the configuration converts.
- **Order of effects.** The clone HEAD is acquired into the tap cache and payloads are materialized before the journal is written. Effects then apply in order: links, declarations, locks, `config.json`, `state.json`. Tests inject a crash at the intent and at each of those checkpoints.
- **Recovery.** Recovery recomputes `config_after`, each migrated declaration and every lock commit from the journal, and `config.json` must still equal its recorded before or after bytes.
  - `recover --rollback` restores the exact prior configuration, declarations, link texts (including live-checkout ones) and registry. It removes created locks and never reads the clone.
  - `recover --complete` first requires the clone to match the recorded observation; otherwise it refuses `recovery.conflict`.
- **Tap machine.** A straggler conversion (`doctor --migrate --project PATH --alias NAME`, or `--user --alias NAME`) writes a `doctor.migrate` journal with no `migration` field and no `machine_config` role. Its recovery reads no checkout.

## Retired journals

A journal is retired when it records a live-checkout transition:
- operation `migrate`;
- a `migration` field or `machine_config` role on any operation other than `doctor.migrate`;
- a shared-checkout Git advance (`git.scope` `source`);
- a selected record without `mode`, outside `doctor.migrate`.

`recover --inspect` shows it with `data.retired` set to `migration`, `shared_checkout_update` or `legacy_ownership`. `recover --complete` and `recover --rollback` refuse it `recovery.conflict` (exit 8) and write nothing. Finish pending recovery with this program before switching program revisions; a previous program does not recover this program's journals (see "Switching executables" in the [CLI contract](cli-contract.md#explicit-migration-selected-updates-and-authoring-exceptions)).

## Recovery invariants

Before-state records whether each leaf was absent or the exact previous owned link; after-state records the intended value or absence. Unlink and replacement require exact raw equality with a recorded value. A link created immediately before process death may exist before a completion marker is saved. Recovery uses the bounded creation intent plus the unchanged planned value, under the cooperative-writer and OS-lock model (`operation.lock`), to complete or roll back only that operation. A hostile same-user process can forge state or recreate an identical path; MASK does not claim to defeat that adversary.

If an existing file or directory or a mismatching symlink appears, recovery refuses and preserves it. An old link is recreated only in an absent destination. Declaration, lock, configuration and registry text is replaced only while the current bytes still match a recorded side. The journal is preserved whenever safe completion cannot be established. Recovery never resets a Git checkout.

## Failure boundaries

Tests inject process exit at these points and check completion and rollback where supported:
- after the intent write;
- after an owned unlink, and after link creation;
- after declaration, lock or configuration replacement but before state;
- after state replacement but before journal cleanup;
- after a program Git advance but before project effects;
- after parent or leaf replacement by a cooperative external writer.

An exception-injection test does not establish operating-system power-loss durability.
