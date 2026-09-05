# MASK CLI contract v1

Normative for RFC-MASK-0001 through RFC-MASK-0005. The JSON result protocol remains v1; local program v0.2.0 adds user scope and state/journal v2. Historical native verification is recorded in docs/releases/v0.1.0.md; the RFC-MASK-0005 closeout records the new acceptance evidence.

## Common options

`--json`, `--debug`, `--help`, `--version` and `--home PATH` are recognized without confusing operand values with flags. `--home` overrides `MASK_HOME`; otherwise use `~/.mask`. `--project` accepts one root; project register/unregister also allow one positional root. Conflicting selections refuse. Support common options before or after subcommands as demonstrated in docs. Respect `--` for operand separation and reject an ID beginning with `-`.

All mutators accept `--dry-run`; project manifest mutators may accept `--apply`; mutators using a computed link/manifest plan accept `--expect-plan-hash HASH`. No prompts or generic `--force`. Debug diagnostics are stderr-only, bounded and redacted. Human rendering and JSON rendering share the same structured result object.

## Command inventory and effects

| Command | Exact principal arguments | Writes | Network |
|---|---|---|---|
| `capabilities` | none | None | No |
| `init` | `--source PATH [--remote NAME] [--branch NAME] [--target TARGET ...]` | Initial machine config/state/lock | No |
| `config show` | none | None | No |
| `config set` | `[--target TARGET ...] [--git-timeout SECONDS]`, at least one | Machine defaults only | No |
| `skill list` | none | None | No |
| `skill show` | `ID [--content]` | None | No |
| `skill validate` | `ID` or `--all` | None | No |
| `project init` | `[--project PATH]` | New empty `.mask.json` only | No |
| `project show` | `[--project PATH]` | None | No |
| `project set` | `--skill ID ...` or `--clear`, plus project/apply options | Manifest; registered links only with `--apply` | No |
| `project require` | `ID ...`, plus project/apply options | Set union; same apply rule | No |
| `project unrequire` | `ID ...`, plus project/apply options | Set subtraction; same apply rule | No |
| `project set-targets` | `TARGET ...` or `--inherit`, plus project/apply options | Explicit targets or remove field | No |
| `project register` | `[PATH | --project PATH] [--apply]` | Registry; optional links | No |
| `project unregister` | `[PATH | --project PATH] [--keep-links]` | Registry; unchanged owned links unless keeping | No |
| `project list` | none | None | No |
| `user init` | none | New empty `MASK_HOME/user.json` only | No |
| `user show` | none | None | No |
| `user set` | `--skill ID ...` or `--clear`, optional `--apply` | Personal manifest; registered links with apply | No |
| `user require` | `ID ... [--apply]` | Set union; same apply rule | No |
| `user unrequire` | `ID ... [--apply]` | Set subtraction; same apply rule | No |
| `user set-targets` | `TARGET ...` or `--inherit`, optional `--apply` | Explicit targets or remove field | No |
| `user register` | `[--user-home PATH] [--apply]` | Pinned home and v2 registry; optional links | No |
| `user unregister` | `[--keep-links]` | Registry; unchanged owned links unless keeping | No |
| `plan` | `[--project PATH | --user | --all]` | None | No |
| `apply` | `[--project PATH | --user | --all] [--expect-plan-hash HASH]` | Validated links/state | No |
| `link adopt` | `(--project PATH | --user) --skill ID --target TARGET --expect-source PATH` | Ownership record only | No |
| `recover` | Exactly one of `--inspect`, `--complete`, `--rollback` | Only complete/rollback modes | No |
| `doctor` | `[--project PATH | --user | --all] [--check]` | None | No |
| `source status` | none | None | No |
| `source fetch` | none | Source Git bookkeeping/remote refs only | Yes |
| `update` | `[--expect-plan-hash HASH]` | Source fast-forward + all registered links/state | Yes |
| `self status` | none | None | No |
| `self install` | `--bin-dir PATH` | Recognized launcher + ownership record | No |
| `self update` | none | Program checkout only | Yes |

`plan/apply` with no selector use the discovered current registered project. `doctor` with no selector checks machine/source and all registered projects and the personal consumer. `update` always selects all; it cannot pretend to isolate shared content to one project. `source update` is deliberately not a separate bypass command; use `update` or fetch-only `source fetch`.

A configuration default change does not relink anything until an explicit apply. There is no source-replacement command that silently relocates all ownership. v1 source relocation uses explicit unregister/setup/register as documented. `project init` and inspection can run before machine initialization where their operation does not need a source/registry. A missing source produces a typed refusal for operations that do need it.

## JSON envelope

Every normal machine-mode response includes:

```json
{
  "schema_version": 1,
  "tool": "mask",
  "tool_version": "0.2.0",
  "command": "project.require",
  "ok": true,
  "dry_run": false,
  "changed": false,
  "would_change": false,
  "transaction": "not_needed",
  "data": {},
  "actions": [],
  "warnings": [],
  "error": null
}
```

`data` contains command-specific results, including resolved project root/manifest, registration state, source root/revision/dirty/fingerprint, expected/actual links and plan hash as applicable. Actions have stable kinds and statuses. No fabricated revision is emitted for an unborn repository; use null plus an explicit condition.

`changed` reports actual remaining changes to managed configuration, registry, manifest, links, launchers or source/program checkout. Fetch-only Git transfer bookkeeping is explicitly reported in `data.fetch_effects`; remote-ref changes can be identified separately without implying skill activation. `would_change` is the preflight proposal. A dry run has `changed=false`, `transaction=not_started` (or `not_needed` when empty), even when actions are proposed.

`transaction` values:

- `not_started`: refusal or preview before application.
- `not_needed`: successful no-op.
- `committed`: planned managed effects completed and state recorded.
- `rolled_back`: core planned effects were restored; any retained empty created directories are separately reported and keep `changed=true`.
- `partial`: some persistent effects remain or source/operation state is indeterminate; nonzero exit and recovery guidance are mandatory.

An operation cannot set `ok=true` with `partial`. `ok=true` for observational `plan` means the plan was computed, **not** that it is applicable: `data.applicable=false` and `data.blockers` can describe safe-to-read precondition failures. `doctor` without `--check` likewise reports diagnostic health in data; `--check` converts actionable failures/drift into a nonzero result. Malformed input/state that prevents inspection is an ordinary command error.

Exactly one JSON document is guaranteed for errors MASK handles after Python starts, including parser errors, ordinary exceptions, timeout and caught interruption. SIGKILL, interpreter startup failure, disk-full stdout, a terminated host or power loss can prevent any response; recovery is on disk. Do not promise impossible output guarantees.

## Error representation and exits

```json
{
  "code": "target.collision",
  "message": "An unmanaged directory occupies the requested target.",
  "retryable": false,
  "details": {"path": "/example/project/.claude/skills/implement-rfc", "existing_type": "directory"},
  "remediation": [{"kind": "inspect", "message": "Inspect and preserve the existing directory. MASK did not modify it."}]
}
```

Remediation may include a validated argv example for an observational command; do not embed credentials or issue a destructive shell fix. `retryable=true` means safe to retry unchanged after the transient condition clears; a partial operation is not retryable until recovery.

| Exit | Meaning |
|---:|---|
| 0 | Successful operation/no-op or completed observational report |
| 2 | Invalid invocation |
| 3 | Invalid/missing/unsupported configuration or required input |
| 4 | Safety/precondition refusal, including stale plan and source divergence |
| 5 | External Git/network/filesystem failure without unresolved partial effects |
| 6 | Writer lock busy |
| 7 | `doctor --check` found drift/actionable health failures |
| 8 | Partial/indeterminate effects or recovery required |
| 10 | Internal invariant failure |
| 130 | Caught user interruption; persistent effects still determine transaction/recovery data |

Initial error families: `invocation.invalid`; `config.*`; `manifest.missing/invalid/unsupported_version`; `project.not_found/not_registered/unavailable/identity_changed`; `skill.unknown/invalid/metadata_unsupported/path_escape`; `target.collision/unmanaged_link/drift/parent_link/symlink_unsupported`; `source.missing/dirty/ahead/diverged/detached/remote_unknown/identity_mismatch/candidate_invalid`; `state.invalid/drift`; `plan.stale`; `recovery.required/conflict`; `lock.busy`; `git.failed/timeout/auth_required`; `filesystem.failed`; `internal.invariant`.

Error strings are stable once shipped. Additive output fields require consumers to ignore unknown fields; persisted configuration rejects unknown fields to catch typos. A major protocol/schema change is explicit, not a silent migration. Supply JSON Schemas as documentation and validate equivalently in the stdlib runtime; no schema library is required to execute MASK.

## Discovery data

Capabilities includes every command's canonical name, positional arguments, options (type/required/repeatable/conflicts), effect category, network flag, dry-run/guard support and exit classes. Keep descriptors beside command registration and snapshot-test them so the protocol cannot drift from argparse.

Skill list returns ID, asset path, description, validation status and issues. Project show reports configured/effective targets, source fingerprint, expected/actual leaf values, ownership and blockers. Project list retains unavailable projects. Source status names configured branch/remote, current HEAD, dirty/ahead/diverged and `remote_freshness`. Self status is independent of source status.

## Examples for agents

```text
mask capabilities --json
mask project show --project /work/example-project --json
mask project require implement-rfc --project /work/example-project --apply --dry-run --json
mask project require implement-rfc --project /work/example-project --apply --expect-plan-hash <returned-hash> --json
mask plan --project /work/example-project --json

mask source fetch --json
mask update --dry-run --json
mask update --expect-plan-hash <returned-hash> --json

mask recover --inspect --json
mask doctor --all --check --json
```

Shell placeholders are illustrative, not executable literal hashes. Tests replace them with the actual parsed value, pass paths as single argv elements, and never use `eval` or concatenate JSON into a shell command.

## User scope and compatibility

Personal declarations use the project v1 membership/target shape at
`MASK_HOME/user.json`. `user init` only creates that declaration. Registration
requires an initialized source and an existing user home, defaulting to the
current OS home. `--user-home` is accepted only at registration; subsequent
operations use the stored canonical root and its recorded identity. Changing
`--home` changes the MASK registry, not the deployment home. A different home
requires explicit unregister/register. One personal consumer is allowed per
MASK home; separate registries cannot adopt or replace one another's ownership.

Personal destinations use the same relative adapters as projects: `.agents/skills`
and `.claude/skills`. Registrations reject overlapping managed destination trees
and linked destination parents. Target lists apply to the entire selection;
per-skill target overrides and alternate sources are not supported.

`--user`, `--project`, and `--all` are mutually exclusive. `--all` includes both
scopes. Without selectors, plan/apply retain project discovery, while doctor
inspects every consumer. `project list` remains project-only; `user show` reports
personal scope. Plans retain `data.projects` and add `data.users`, each with
explicit scope, root, and manifest location. Adoption accepts exactly one
explicit scope selector. Source updates validate and reconcile all consumers.

State v2 preserves `projects` and `launchers` and adds a nullable `user` record
with the same root identity, manifest cache, revision, and link fields as a
project record. Root identity is unique across scopes. The first user registration
is the sole v1-to-v2 transition, journaled even without `--apply`. Reads and
project-only writes preserve v1 until that transition. Unregistering the user
retains v2 with `user: null`.

Journal v2 derives consumer scope from its validated before/after registries;
manifest destinations are recomputed as `<project>/.mask.json` or the current
`MASK_HOME/user.json`, never accepted as arbitrary serialized write paths.
V1 journals remain recoverable. V2 upgrade rollback restores exact v1 state
bytes. Mutators refuse pending recovery; unknown schema versions fail closed.
Capabilities report readable state/journal versions `[1, 2]` and latest version 2.
The source/configuration and result schemas remain v1.

Additional error families are `user.not_registered`, `user.not_found`,
`user.already_registered`, `user.unavailable`, `user.identity_changed`, and
`target.overlap`. Ownership, stale-plan, and recovery errors retain existing codes.
