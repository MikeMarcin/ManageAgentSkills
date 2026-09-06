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
Capabilities retain readable state versions `[1, 2]` and state version 2. The readiness extension below adds journal v3 while preserving the v1/v2 readers.
The source/configuration and result schemas remain v1.

## Workspace readiness (unreleased RFC-MASK-0006 additions)

`integration approve --project PATH [--linked-worktrees] [--inactive-branches]`
records physical-root authority in `MASK_HOME/integration.json`. Approval is
separate from installing an integration and from ordinary explicit registration.
`integration revoke --project PATH` removes direct authority while preserving links. It refuses when a broader linked-worktree or repository approval would still authorize the root.
Both commands support dry-run and a plan guard. `integration inspect --project PATH`
reports approval, the registration identity used for retirement, owned adapter
configuration, and unverified host loading. `integration approve --repository ID --under ROOT` authorizes future repository roots beneath an existing physical clone directory. The directory identity and exact credential-free origin identity must match; outside or replaced boundaries refuse. Use the matching `integration revoke --repository ID --under ROOT` to remove that policy.

`ensure [--project PATH] [--event EVENT] [--check] [--offline] [--dry-run]`
registers and reconciles an approved project under the ordinary writer lock.
It reads the selected legacy source locally, validates selected packages, and
performs no fetch or whole-source status scan (`source.dirty` is null). It does
not require a caller-supplied plan hash. `--check` performs no writes and exits 7
for drift. Busy writers fail immediately with exit 6; pending recovery exits 8.
No-op runs preserve managed file bytes and registry generations. Filesystem
readiness is `ready_legacy_unpinned`, separately from `host_load: not_verified`.

Events are `manual`, `startup`, `post-checkout`, `post-merge`, `post-rewrite`, and
`post-commit`. A Git event includes already registered nested consumers in the same worktree, without crawling unregistered directories or entering separate nested repositories. Each selected project still requires its own applicable readiness authority. Startup also preflights the already registered personal consumer
before any selected scope changes. A session outside Git can reconcile that
personal consumer alone. It never creates a personal declaration or registration.

Inactive-branch cleanup requires an explicit root approval with
`--inactive-branches`, a previously observed tracked declaration matching the
cached selection, and unchanged worktree identity. HEAD/index must omit the
declaration without sparse checkout, conflicts, or an in-progress merge/rebase.
Cleanup removes only unchanged owned links, retains registration and the cached
selection, and creates no manifest. A linked worktree must receive its own
inactivity opt-in. Missing or ambiguous inputs block without treating them as
empty selections.

Readiness journals use v3 control observations, while state remains v1/v2.
Recovery checks exact declaration bytes or expected absence, Git/index identity,
physical roots, and approval bytes. Changed inputs block both stale completion
and rollback. Integration-entry journals are another typed v3 variant; recover
only the recorded owned hook/config entries. A new integration is recovered using its originally selected interpreter; an already owned installation retains its recorded interpreter. Inactive cleanup validates only packages whose links remain active, rather than unused cached requirements. V1/v2 journals retain their readers.
Program self-update still refuses schema changes (LF/CRLF checkout conversion alone is compatible): update the program checkout
explicitly before using this persistence boundary.

`integration enable|disable [--project PATH] (--git | --agent claude|codex)`
supports dry-run and guards. Git capability is probed: named hooks are preferred
when supported; otherwise only unoccupied per-repository hook files are used.
An existing hook manager is preserved. Installed events cover checkout, merge,
rewrite and post-commit, including manual merge completion. Per-repository
installation does not cover future clones; startup/prelaunch is the fallback.
Failures warn that the Git operation already completed. Internal Git commands
suppress directory and configured event hooks. Hook children have a 30-second
deadline and process-tree cleanup; interrupted effects require explicit recovery.

With `--project`, Claude configuration adds an owned SessionStart group to
`.claude/settings.local.json`; Codex uses `.codex/hooks.json`. Without `--project`, an agent adapter is installed at the registered personal home, or the OS home if personal scope is unregistered: Claude uses `.claude/settings.json`, and Codex uses `.codex/hooks.json`. This installs an adapter without creating a personal skill selection or registration. Git installation always requires `--project`. Other settings and
groups are preserved. Removal refuses an edited owned group and may retain empty
JSON containers. These edits do not approve a repository or change host trust.
Claude requests `reloadSkills` after readiness and is a warning-only startup
adapter. Codex uses its own context/stop fields and does not receive Claude's
reload field. Actual first-prompt loading and gate behavior remain unverified.
For Codex worktree setup, enable returns a pinned ensure command to compose into
an existing local-environment setup script without replacing that script.

`launch --agent claude|codex [--project PATH] -- HOST_ARGUMENTS...` ensures startup
readiness first, releases the writer lock, then invokes the selected executable
from PATH with an argv array. Capabilities mark launch as network-capable because the invoked host may use its own network services; ensure remains local-only. Dry-run never launches. Ordinary mode inherits host
I/O; `--json` before `--` captures host stdout/stderr in the result. Arguments after
`--` belong to the host. Missing executables and Windows batch-only launchers
refuse; direct native Windows host prelaunch was verified with installed executables and `--version`; first-prompt loading remains unverified. A failed
host exits MASK with 5 and records the host exit code without undoing readiness.

`workspace forget PATH --expect-identity ID` retires a registration only after
matching its recorded identity. Existing paths use normal owned unregister rules.
A missing path must be absent from the original, identity-checked Git common
repository's worktree list; unavailable storage that Git still records refuses.
The operation never infers removal by scanning/pruning unavailable consumers.

Adapter contracts: [Git hooks](https://git-scm.com/docs/git-hook),
[Claude hooks](https://code.claude.com/docs/en/hooks), and
[Codex hooks](https://learn.chatgpt.com/docs/hooks), checked September 5, 2026.

Additional error families are `user.not_registered`, `user.not_found`,
`user.already_registered`, `user.unavailable`, `user.identity_changed`, and
`target.overlap`. Ownership, stale-plan, and recovery errors retain existing codes.

## Legacy inventory (unreleased RFC-MASK-0011 slice)

`inventory [--project PATH | --user | --all] [--include-unmanaged]` reports the
selected registered consumers. Without a selector it uses the current project.
`skill where-used legacy/ID [--agent claude|codex] [--scope user|project]` searches
registered local declarations and ownership for that skill. The `legacy` alias
identifies the currently configured single source; other aliases refuse until
multi-source support ships.

Both commands accept `--limit 1..1000` (default 100) and `--offset N`, with
`total_rows` and `next_offset` in the result. Pagination limits output; the
reported work counters describe the full selected query. No network operation,
writer lock, package-content scan or registry update occurs. Narrow inverse
queries read relevant consumer declarations and only the selected skill/agent
leaves. `--include-unmanaged` enumerates supported discovery directories one
level deep and never follows neighboring links or adopts content.

Rows distinguish declared-but-missing deployment, converged or drifted ownership,
unmanaged entries, blocked input and unavailable consumers. Unavailable cached
selections are labeled diagnostic, with no claim that they are current. Broken
source targets are drifted. `artifact` and upstream repository identity are null;
`recorded_source_revision` is historical ownership metadata, never a content pin.
Compatibility is unspecified and host loading is unverified. Pin/profile/fleet
fields and full update-impact reports remain unimplemented RFC work.
