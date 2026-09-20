# MASK CLI contract v1

Current CLI contract through RFC-MASK-0021 (tap-only deployment), with the lock, artifact store, pinned-consumer engine and authoring slices of RFC-MASK-0008, the inventory slice of RFC-MASK-0011 and the tap line-ending policy of MASK-0109. A skill source is a tap: an approved Git repository that MASK fetches into its own bare cache. Every project and personal selection is pinned by a lock and deployed from `MASK_HOME/store`; only an explicit `source dev-link` links an authoring checkout. The result envelope remains v1. Machine configuration is v3, new declarations are v2 with v1 locks, and ownership state and pending journals read v1/v2/v3. Native evidence is recorded in the corresponding RFC closeouts; RFC-MASK-0021 native qualification is pending.

## Common options

`--json`, `--debug`, `--help`, `--version` and `--home PATH` are recognized without confusing operand values with flags. `--home` overrides `MASK_HOME`; otherwise use `~/.mask`. `--project` accepts one root; project register/unregister also allow one positional root. Conflicting selections refuse. Support common options before or after subcommands as demonstrated in docs. Respect `--` for operand separation and reject an ID beginning with `-`.

All mutators accept `--dry-run` and `--yes`; project manifest mutators may accept `--apply`; mutators using a computed link/manifest plan accept `--expect-plan-hash HASH`. A direct task command authorizes its ordinary scoped effects without a question; genuinely significant new authority is asked for in-process (see Consent below). No generic `--force`. Debug diagnostics are stderr-only, bounded and redacted. Human rendering and JSON rendering share the same structured result object.

## Command inventory and effects

The table follows the registered command table (`mask.COMMANDS`), which `capabilities` publishes. Every mutating command also accepts `--dry-run` and `--yes`, and every plan-guarded command (`plan_guard` in `capabilities`) accepts `--expect-plan-hash HASH`; those options are not repeated below.

| Command | Exact principal arguments | Writes | Network |
|---|---|---|---|
| `capabilities` | none | None | No |
| `init` | `[--target TARGET ...] [--git-timeout SECONDS]` | Machine config v3 with an empty tap catalog, plus empty state, when no config exists; an existing config that matches the explicit options is kept, otherwise `config.already_initialized` (4) | No |
| `config show` | none | None | No |
| `config set` | `[--target TARGET ...] [--git-timeout SECONDS] [--forge-host HOST ...] [--clear-forge-hosts]`, at least one | Machine defaults and this machine's extra forge hosts only | No |
| `tap add` | `NAME URL [--ref REF] [--packages PATH] [--checkout PATH] [--autocrlf] [--pin-transport]` | Approved catalog entry and its line-ending policy; creates machine config v3 and empty state when no config exists | No |
| `tap transport` | `NAME [URL \| --derive]` | The catalog entry's `transport` and `transport_policy` only; never its identity | No |
| `tap remove` | `NAME` | Unreferenced catalog entry only; retains cache | No |
| `skill list` | none | None | No |
| `skill show` | `ID [--content]` | None | No |
| `skill validate` | `ID` or `--all` | None | No |
| `skill where-used` | `SOURCE/ID [--agent AGENT] [--scope project\|user] [--limit N] [--offset N]` | None | No |
| `skill import` | `URL-or-SOURCE --mode copy --into SOURCE [--ref REF] [--path PATH]` | New curated directory and provenance; owned upstream cache | Yes |
| `skill provenance` | `SOURCE/ID` | None | No |
| `skill record-adaptation` | `SOURCE/ID --note TEXT` | Existing provenance record only | No |
| `install` | `ID-or-SOURCE/ID ... [--project PATH \| --user] [--agent AGENT ...] [--offline]` | v2 declaration and lock (created if missing), registration, store artifacts, links, state; tap cache when a live install must resolve a new binding | Only for live resolution |
| `remove` | `ID-or-SOURCE/ID ... [--project PATH \| --user]` | Declaration, lock, owned unchanged links, state | No |
| `list` | `[--project PATH \| --user]` | None | No |
| `inventory` | `[--project PATH \| --user \| --all] [--include-unmanaged] [--limit N] [--offset N]` | None | No |
| `upgrade` | `[--project PATH \| --user \| --all] [--skill SOURCE/ID ...] [--allow-ref-rebind] [--offline]` | Caches of the referenced taps; then the selected consumers' locks, store artifacts, links and state through one journal | Fetches each referenced tap once unless `--dry-run`, `--offline` or `--expect-plan-hash` |
| `lock` | `[--project PATH \| --user] [--refresh] [--skill SOURCE/ID ...] [--allow-ref-rebind]` | Lock file only; a changed lock of a registered consumer refuses `lock.active` | No |
| `project init` | `[--project PATH]` | When `.mask.json` is missing: an empty v2 declaration, plus an empty `.mask.lock.json` if none exists | No |
| `project show` | `[--project PATH]` | None | No |
| `project set-targets` | `TARGET ...` or `--inherit`, plus project/apply options | v2 `default_agents`; links only with `--apply` | No |
| `project set-agents` | `SOURCE/ID AGENT ...`, `--all` or `--inherit`, plus project/apply options | Per-binding `agents`; links only with `--apply` | No |
| `project register` | `[PATH \| --project PATH] [--apply]` | Registry (pinned record); store artifacts and links with `--apply` | No |
| `project unregister` | `[PATH \| --project PATH] [--keep-links]` | Registry; unchanged owned links unless keeping | No |
| `project list` | none | None | No |
| `user init` | none | When `MASK_HOME/user.json` is missing: an empty v2 declaration, plus an empty `MASK_HOME/user.lock.json` if none exists | No |
| `user show` | none | None | No |
| `user set-targets` | `TARGET ...` or `--inherit`, optional `--apply` | Personal `default_agents`; links only with `--apply` | No |
| `user set-agents` | `SOURCE/ID AGENT ...`, `--all` or `--inherit`, optional `--apply` | Personal per-binding `agents`; links only with `--apply` | No |
| `user register` | `[--user-home PATH] [--apply]` | Pinned home and registry; optional store artifacts and links | No |
| `user unregister` | `[--keep-links]` | Registry; unchanged owned links unless keeping | No |
| `selection-policy set` / `clear` | `--agent AGENT ...` / none | `MASK_HOME/selection-policy.json`; affected scopes' links | No |
| `compatibility override` | `SOURCE/ID (--project PATH \| --user) --reason TEXT [--agent AGENT ...] [--platform] [--architecture]` | One override row in the selection policy; affected scope's links | No |
| `compatibility clear` | `SOURCE/ID (--project PATH \| --user)` | That override row only; affected scope's links | No |
| `plan` | `[--project PATH \| --user \| --all]` | None | No |
| `apply` | `[--project PATH \| --user \| --all]` | Store artifacts, validated links, state | No |
| `ensure` | `[--project PATH \| --user \| --all] [--event EVENT] [--check] [--offline] [--allow-setup SOURCE/ID:ACTION ...] [--repair]` | Registration, store artifacts, links, native roles, state; exact locked objects in a tap cache only under an explicit grant or `--repair` | Only an exact locked fetch under an explicit grant or `--repair` |
| `integration approve` | `--project PATH [--linked-worktrees] [--inactive-branches] [--allow-locked-fetch SOURCE ...]` or `--repository ID --under ROOT` | `MASK_HOME/integration.json` | No |
| `integration revoke` | `--project PATH` or `--repository ID --under ROOT` | `MASK_HOME/integration.json` | No |
| `integration inspect` | `[--project PATH] [--agent AGENT]` | None | No |
| `integration enable` / `disable` | `[--project PATH] (--git \| --agent claude\|codex)` | Owned hook or adapter configuration entries | No |
| `launch` | `--agent claude\|codex [--project PATH] -- HOST_ARGUMENTS...` | Startup readiness, as `ensure` | The invoked host may use the network |
| `workspace forget` | `PATH --expect-identity ID` | Registry; unchanged owned links of an existing path | No |
| `link adopt` | `(--project PATH \| --user) --skill ID --target TARGET --expect-source PATH` | Ownership record only | No |
| `recover` | Exactly one of `--inspect`, `--complete`, `--rollback` | Only complete/rollback modes | No |
| `doctor` | `[--project PATH \| --user \| --all] [--check] [--migrate]` | None; with `--migrate` (no scope option), only the tap catalog entries in `config.json` that record an older spelling of a tap identity, in one atomic write | No |
| `source fetch` | `[NAME]` or `--locked [--project PATH \| --user] [--offline]` | Without a name, every approved tap's cache; with `NAME`, that tap's cache; `--locked`, exact locked objects and store artifacts | Yes |
| `source list` | none | None | No |
| `source show` | `NAME` | None | No |
| `source inspect` | `URL-or-SOURCE [--ref REF] [--path PATH]` | Owned bare cache for already approved tap; never deployment | Yes |
| `source publish` | `SOURCE --paths PACKAGE_PATH ... [--commit] [--push] [--message TEXT]` | With `--commit`, a new commit and retained ref in the authoring repository; `--push` pushes that commit | Only with `--push` |
| `source dev-link` | `SOURCE/ID (--project PATH \| --user) (--authoring-root PATH \| --to-pinned)` | Scope-local development links into the approved authoring checkout, or their return to store links; state | No |
| `self status` | none | None | No |
| `self install` | `--bin-dir PATH` | Recognized launcher + ownership record | No |
| `self uninstall` | none | Each recorded launcher whose bytes MASK still recognizes, and its ownership record, one launcher journal each; an edited launcher is kept. Never the program checkout, `MASK_HOME` or any consumer | No |
| `update` | none | Program checkout (fast-forward through one journal), then the caches of every approved tap. No declaration, lock, link or consumer state | Yes, unless `--dry-run` |

`plan/apply` with no selector use the discovered current registered project. `doctor` with no selector checks the machine and every registered consumer of both scopes. `upgrade` with no selector updates every registered consumer; `--project`, `--user`, `--all` and `--skill` narrow it (see [update](#selected-updates-and-authoring-exceptions)). The vocabulary is that of `brew` and `apt`: `update` makes new versions available (the program and every tap) and changes no consumer, `upgrade` fetches what its consumers reference and applies, and `source fetch` fetches taps only.

A configuration default change does not relink anything until an explicit apply. No command silently relocates ownership to another tap; binding a different repository, ref, package path, authoring checkout or line-ending policy under an existing alias refuses `source.alias_conflict`. `project init`, `user init` and inspection can run before a machine configuration exists where they do not need a catalog or registry. Other commands refuse `config.missing` (exit 3), whose remediation is `mask tap add NAME URL`.

### Taps, payloads and caches

Machine configuration v3 ([schema](../../schemas/machine-v3.schema.json)) holds `schema_version` 3, `default_targets`, `git_timeout_seconds` and `sources`, a catalog of 0 to 256 taps. A tap entry has `repository` (normalized credential-free identity), `transport`, `cache` (`MASK_HOME/sources/<alias>-<16 hex>.git`), `ref` (the update selector), `packages`, `authoring` (absolute checkout path or `null`) and `line_endings` (`exact` or `autocrlf`; absent means `exact`). Every cache is a MASK-owned bare repository. `tap add --checkout PATH` binds an authoring checkout whose `origin` must normalize to the tap identity (`source.identity_mismatch`); a checkout without an origin is identified by its own path. Curated imports, provenance, `source publish` and `source dev-link` use it, and install, list, ensure and update never read it. Whether or not the checkout has an origin, `tap add --checkout`, an import destination, `skill record-adaptation`, `source publish` and `source dev-link` refuse before any effect when it is on a branch other than the tap's configured one (`source.identity_mismatch`, exit 4, with `details.branch` and `details.configured_branch`) or has a detached HEAD (`source.detached`, exit 4). `tap add` never fetches. A fetch never checks out or activates payloads; reads and previews never fetch. Missing cached resolution is reported as `resolution_required`. Approved identities
normalize scheme/host/default port while preserving repository case. **Identity and transport (RFC-MASK-0022).** A tap's `repository` names which repository is trusted; its transport is how this machine reaches it. On a forge host, `https://H/P`, `ssh://git@H/P` and `git@H:P`, each with or without `.git`, are one identity, canonically `https://H/P.git`. The forge hosts are `github.com`, `gitlab.com`, `bitbucket.org` and `codeberg.org`, plus the machine's own `forge_hosts` (`config set --forge-host HOST`, `--clear-forge-hosts`); a declaration or lock can never extend that set and refuses an unknown field. `ssh://git@H/~/P`, which is how MASK spelled the scp form before this RFC and which no forge serves, is read as the same identity. A non-default port, an SSH user other than `git` and every other host stay strict: there HTTPS and SSH are distinct identities, and scp home-relative paths stay distinct from absolute SSH paths. Every identity comparison goes through the normalizer. A file keeps the spelling it recorded, so its recorded `selection_digest` still verifies; `ensure`, `list`, `doctor` and fetches never rewrite a file for its spelling, and `install`, `remove` and an `upgrade` that writes anyway record the canonical identity with unchanged commits and digests. A tap entry has a `transport_policy`, `derived` (the default, and the reading of an entry without the field) or `pinned`. A pinned tap uses its `transport` and nothing else (`tap add --pin-transport`, `tap transport NAME URL`; `tap transport NAME --derive` unpins; a URL naming another identity refuses `source.identity_mismatch` without effect). For a derived tap on a forge host each fetch tries, in order and without prompting: the `origin` scheme of the one selected project consumer when it is on the same host; the transport a previous fetch proved; `gh config get git_protocol -h HOST` when `gh` is on PATH (no `gh` failure is fatal); the URL typed at `tap add`; then the other scheme. SSH always uses the scp form, never the `/~/` URI. Only an authentication or reachability failure (`git.auth_required`, `git.failed`, `git.timeout` from `ls-remote`) moves to the next candidate; a rewritten endpoint, a redirect policy or a malformed advertisement refuses at once, and when every candidate fails the result is `git.auth_required` with `details.tried`. A bare `upgrade` over several consumers skips the origin step. The proven transport is remembered in `mask-transport.json` beside the cache rather than in `config.json`, because fetches run inside journals that bind the configuration's bytes. Fetch results report `transport`, `transport_policy`, `chosen_by` and `tried` (under `data.transports`, or per tap in `data.fetches`), and `source show` reports the first three. A cache stays keyed as it was created: a catalog that recorded an older spelling keeps its cache path, which is accepted for any spelling of the same identity. An unscoped `doctor --migrate [--dry-run] [--expect-plan-hash HASH]` rewrites such catalog entries to the canonical identity, a usable transport and an explicit policy in one atomic write, reported by `doctor` as `migration.identity_canonicalization`; it changes no project file, state record or cache. Transport never changes content trust: commits, object format and payload digests are verified exactly as before. Passwords, tokens, unsupported protocols,
transport rewrites to other identities and effective redirect policies refuse.
Catalog mutation guards bind the before/after config. `tap remove` preserves all
cache files and refuses while a registered consumer's declaration or lock names
the tap (`source.referenced`) or a registered consumer is unavailable.
`skill list/show` use frozen fetched tap catalogs. Qualified
`SOURCE/ID` selects one catalog; bare-name duplicates return choices, and missing
cached sources cannot establish a unique bare-name match. Inspection supports
flat, root and exact indexed nested packages with bounded metadata reads.
GitHub tree/blob inputs are split against advertised refs, preserving slash
ambiguity. HTTP(S) GitHub browser spellings with and without `.git` may locate an
already approved HTTPS binding, but never grant SSH or a different host approval.
Remote inspection is explicit and fetches an exact advertised object. Inspecting
another ref does not advance the configured catalog cursor. Read/dry-run results
report missing cached resolution. List/show retain `validation=metadata_only`.
`skill validate SOURCE/ID` and `skill validate --all` read full frozen payloads
and return `validation=payload`, `payload_digest`, `file_count`, `total_bytes`
and the selected commit/path. These observational commands never fetch or write.
Missing catalogs refuse validation. The payload digest is `sha256:` plus the
SHA-256 of MASK canonical JSON for the path-sorted manifest array. Each entry is
exactly `{path, mode, size, sha256}`: package-relative UTF-8 path, logical Git
mode string, byte count and bare hexadecimal SHA-256 of the exact file bytes.
Every regular payload file is included, including provenance stored inside the
package. Source provenance records outside the payload are excluded.

Plain payloads permit regular Git blobs only, capped at 64 MiB per file,
256 MiB cumulative bytes, 10,000 tree entries (including directories), depth 32,
and 1024 UTF-8 bytes per path. Tree output is capped at 16 MiB and metadata at
1 MiB before complete capture; all Git diagnostic streams are capped at 64 KiB.
Case-colliding components, non-NFC paths, Windows reserved components, traversal,
links/submodules and LFS pointers refuse. `.git`, `.gitmodules`, `.claude`,
`.codex`, `.agents`, `.claude-plugin`, `.codex-plugin`, MCP JSON configuration
and `hooks/hooks.json` are unsupported activation/administration content at any
payload depth. Plain-skill frontmatter accepts unquoted `name`, `description`,
`license`, `compatibility` keys with single-line scalars and an optional flat
two-space-indented `metadata` scalar map. Quoted keys, flow/complex YAML, aliases,
unknown extensions, tool grants, hooks, MCP and plugin frontmatter refuse; bytes
are never rewritten. Every nested `SKILL.md` receives this guard too. Inline
shell preprocessing and executable fenced blocks refuse even in example text,
because [Claude skills support preprocessing and tool grants](https://code.claude.com/docs/en/skills#inject-dynamic-context)
and [frontmatter hooks](https://code.claude.com/docs/en/hooks#hooks-in-skills-and-agents).
Scripts
are read as bytes, never executed; raw Git object reads bypass checkout filters
and replacement objects. This is a structural package-kind boundary, not a
general malware detector or complete Agent Skills conformance check.

Managed bare-cache fetches use a staging ref, bounded stdout/stderr and the
configured Git timeout. Object storage is sampled every 50 ms and checked after
fetch: maximum growth is 256 MiB per fetch, total cache ceiling 1 GiB. This
polling policy permits transient disk overshoot and does not bound wire bytes.
Only a successful final check permits the selected ref to advance. A refusal
reports retained-object possibility and the staging ref; caches are never
silently deleted. Code-owned limits cannot be raised by downloaded metadata.
On Windows, Git starts suspended and joins an owned kill-on-close Job Object
before its primary thread resumes. Assignment/resume failure terminates the
suspended process and returns `git.containment_unavailable`; there is no
uncontained fallback. Job termination includes helpers after their parent exits.
POSIX uses a separate process group. Output-reader failures refuse incomplete
observations through the same cleanup path.
Which fetches `upgrade`, `source fetch` and a live `install` perform is described under [update](#selected-updates-and-authoring-exceptions) and [Task commands](#task-commands-rfc-mask-0018-mask-0086).

### Curated copy imports and provenance

`skill import URL-or-SOURCE --mode copy --into SOURCE [--ref REF] [--path PATH]`
uses the approved resolver and requires exactly one validated frozen package.
It is network-capable; `--dry-run` neither fetches nor stages and reports
`resolution_required` when cached resolution is unavailable. Preview/apply
support `--expect-plan-hash`, binding config, selected objects, notice content,
destination HEAD/root/parent identity, source index and Git index entries.

The destination requires an approved authoring checkout on its configured
branch, with no in-progress Git operation; it is observed before any fetch
([branch refusals](#taps-payloads-and-caches)). Unrelated working/staged changes are
preserved. A source index must already map the ID to a nonoverlapping path;
without an index the destination is `<packages>/<id>`. Its parent must exist.
Existing HEAD/index/worktree content refuses, including tracked deleted files.
Staging lives beneath real Git metadata, outside skill discovery. After verifying
staged bytes and final preconditions, native no-replace directory publication
uses macOS `renamex_np(RENAME_EXCL)`, Linux `renameat2(RENAME_NOREPLACE)`, or Windows
rename. Unsupported filesystems/cross-device staging refuse without a copy or
overwrite fallback. A concurrent empty destination is preserved. Interrupted
prepublication staging may leave a `mask-import-*` directory beneath Git metadata;
normal success/refusal cleans its own temporary directory. This does not protect
against a hostile same-user process racing every final precondition.

Imports reserve `.mask-provenance.json` and `.mask-notices`; upstream collisions
refuse instead of dropping data. Ancestor directories through the repository
root are inspected for regular LICENSE, LICENCE, NOTICE and COPYING files, with
an optional dot/hyphen suffix. At most 64 notices of 1 MiB each are incorporated
under `.mask-notices/<ancestor-level>/<name>` with explicit original paths and
byte hashes. Other notice conventions require separate review; absence does not
establish licensing permission. The original upstream manifest/digest remains
unchanged. Curated content comprises that original payload plus listed notices.

The [provenance v1 schema](../../schemas/provenance.schema.json) records both
manifests, exact upstream commit/coordinate, authoring HEAD at import, and bounded
adaptations. Only the generated root `.mask-provenance.json` is excluded from
the record's curated **content** digest to avoid self-reference. A full later
artifact **payload** digest includes its actual bytes, as it does every other
regular file. Import reports both digests and exact changed paths; no commit,
push, index mutation or deployment is implicit.

`skill provenance SOURCE/ID` is observational and never fetches. An available
authoring checkout on its configured branch uses `observation=authoring`; taps,
unavailable authoring roots and other checked-out branches use `frozen_cache`
with an exact observed commit. Missing records return absent/unknown history.
Authoring records are local assertions; cached embedded records are publisher
assertions. `verified_git_objects` means the original full upstream manifest and
all incorporated notices were independently rechecked in an approved cached
repository. It does not authenticate the publisher or adaptation narrative.
Missing upstream objects yield `recorded_only`; disagreeing objects yield
`mismatch`. Current bytes are compared with the last recorded content manifest,
reporting unrecorded adaptations. Windows authoring mode observations use
recorded logical modes; cached Git mode observations are exact. Import does not
set executable bits in the Windows Git index.

`skill record-adaptation SOURCE/ID --note TEXT` requires authoring scope and an
existing valid record. It supports preview/hash guards and appends the observed
before/after content digests and complete manifest with the supplied local note.
It changes only the provenance file, with no Git/index mutation. No content
change is a no-op. Records are capped at 1 MiB, 100 adaptation entries and 4096
characters per note; complex/unknown record shapes refuse. Recording is not
approval to execute the skill and never fabricates unknown earlier history.

## JSON envelope

Every normal machine-mode response includes:

```json
{
  "schema_version": 1,
  "tool": "mask",
  "tool_version": "0.2.0",
  "command": "install",
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

`data` contains command-specific results, including resolved consumer root and declaration, registration state, lock changes, fetch and preparation effects, expected/actual links and plan hash as applicable. Actions have stable kinds and statuses. No fabricated revision is emitted for an unborn repository; use null plus an explicit condition.

`changed` reports actual remaining changes to managed configuration, registry, declarations and locks, links, store artifacts, launchers, authoring commits and refs created by `source publish`, or the program checkout. Fetch transfers are reported in `data.fetch_effects` (`source fetch NAME`) or per tap in `data.fetches` (`upgrade`, `source fetch` without a name); named-source cache creation is reported in `data.cache_effects`. These fetch effects do not set `changed` and do not imply skill activation. Store artifacts and exact acquisitions retained by preparation are reported in `data.preparation` and do set `changed`; `data.retained_preparation` summarizes them as `artifacts` (created store payload paths), `directories` (retained created store directories) and `acquisitions` (`cache` and `commit`), apart from the consumer `transaction`. `would_change` is the preflight proposal. A dry run has `changed=false`, `transaction=not_started` (or `not_needed` when empty), even when actions are proposed.

`transaction` values:

- `not_started`: refusal or preview before application.
- `not_needed`: successful no-op.
- `committed`: planned managed effects completed and state recorded.
- `rolled_back`: core planned effects were restored; any retained empty created directories are separately reported and keep `changed=true`.
- `partial`: some persistent effects remain or source/operation state is indeterminate; nonzero exit and recovery guidance are mandatory.

An operation cannot set `ok=true` with `partial`. `transaction` describes the consumer transaction, not MASK-owned preparation. A refusal before any consumer effect, after preparation created store artifacts or cache objects, reports `transaction: not_started` with `changed: true` and lists the retained effects in `data.retained_preparation`. Examples are `plan.stale` found under the writer lock, a collision, or withheld readiness consent (`confirmation.required` or `confirmation.declined`) after `install`, `remove`, `upgrade`, `apply` or `ensure` prepared new payloads. No declaration, lock, link, registration, policy or project byte changed, no journal is pending and nothing needs recovery. A refusal after consumer effects keeps its `committed`, `rolled_back` or `partial` status. `ok=true` for observational `plan` means the plan was computed, **not** that it is applicable: `data.applicable=false` and `data.blockers` can describe safe-to-read precondition failures. `doctor` without `--check` likewise reports diagnostic health in data; `--check` converts actionable failures/drift into a nonzero result. Malformed input/state that prevents inspection is an ordinary command error.

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

Initial error families: `invocation.invalid`; `config.*`; `manifest.missing/invalid/unsupported_version`; `project.not_found/not_registered/unavailable/identity_changed`; `skill.unknown/invalid/metadata_unsupported/path_escape`; `target.collision/unmanaged_link/drift/parent_link/symlink_unsupported`; `source.missing/dirty/detached/remote_unknown/identity_mismatch/candidate_invalid`; `state.invalid/drift`; `plan.stale`; `recovery.required/conflict`; `lock.busy`; `git.failed/timeout/auth_required`; `filesystem.failed`; `internal.invariant`. The tap model adds `source.unresolved/alias_conflict/referenced` and `upgrade.incomplete`.

Error strings are stable once shipped. Additive output fields require consumers to ignore unknown fields; persisted configuration rejects unknown fields to catch typos. A major protocol/schema change is explicit, not a silent migration. Supply JSON Schemas as documentation and validate equivalently in the stdlib runtime; no schema library is required to execute MASK.

## Discovery data

Capabilities includes every command's canonical name, positional arguments, options (type/required/repeatable/conflicts), effect category, network flag, dry-run/guard support and exit classes. Keep descriptors beside command registration and snapshot-test them so the protocol cannot drift from argparse. The command list is exactly the registered command table.

Capabilities also publishes:

- `schemas`: `result` 1, `project` 2, `user` 2, `lock` 1, `machine` 3, `state` 3, `pending` 3.
- `readable_versions`: `machine` [3], `project` and `user` [2], `lock` [1], `state` and `pending` [1, 2, 3].
- `deployment_model: "taps"`: selections are pinned by locks and deployed from `MASK_HOME/store`.
- `line_endings`: `{"default": "exact", "values": ["exact", "autocrlf"], "opt_in": "tap add --autocrlf"}` (see Tap line endings under [authoring exceptions](#selected-updates-and-authoring-exceptions)).
- `scopes`, `targets`, `adapter_contracts`, `pinned_deployment`, `per_binding_targeting`, `python_minimum`, `program_root` and `workflow`.

Skill list returns ID, asset path, description, validation status and issues. Project show reports the declaration, mode, requested and effective agents, expected and actual links, ownership, outcomes, shadowing and blockers. Project list retains unavailable projects. `source show` reports the tap binding, its `line_endings` policy, the cached revision of its configured ref and `resolution_required`. Self status reports the program installation independently of any tap.

## Examples for agents

```text
mask capabilities --json
mask tap add agentskills https://github.com/MikeMarcin/AgentSkills.git --json
mask install implement-rfc --project /work/example-project --json
mask list --project /work/example-project --json

mask source fetch --json
mask upgrade --dry-run --json
mask upgrade --expect-plan-hash <returned-hash> --json

mask doctor --migrate --dry-run --json
mask doctor --migrate --expect-plan-hash <returned-hash> --json
mask recover --inspect --json
mask doctor --all --check --json
```

Shell placeholders are illustrative, not executable literal hashes. Tests replace them with the actual parsed value, pass paths as single argv elements, and never use `eval` or concatenate JSON into a shell command.

## User scope and compatibility

Personal declarations use the v2 selection shape at `MASK_HOME/user.json`, with
their lock at `MASK_HOME/user.lock.json`. `user init` only creates a missing
declaration, empty, and its empty lock when none exists. Registration requires a
machine configuration and an existing user
home, defaulting to the current OS home. `--user-home` is accepted only at
registration; subsequent
operations use the stored canonical root and its recorded identity. Changing
`--home` changes the MASK registry, not the deployment home. A different home
requires explicit unregister/register. One personal consumer is allowed per
MASK home; separate registries cannot adopt or replace one another's ownership.

Personal destinations use the same relative adapters as projects: `.agents/skills`
and `.claude/skills`. Registrations reject overlapping managed destination trees
and linked destination parents. Whole-selection `default_agents` and per-binding
`agents` choose destinations (see Targeting below).

`--user`, `--project`, and `--all` are mutually exclusive. `--all` includes both
scopes. Without selectors, plan/apply retain project discovery, while doctor
inspects every consumer. `project list` remains project-only; `user show` reports
personal scope. Plans retain `data.projects` and add `data.users`, each with
explicit scope, root, and manifest location. Adoption accepts exactly one
explicit scope selector. An unscoped `upgrade` selects every registered consumer
of both scopes.

State v2 preserves `projects` and `launchers` and adds a nullable `user` record
with the same root identity, manifest cache, revision, and link fields as a
project record. Root identity is unique across scopes. Registering a consumer
is journaled even without `--apply` and writes state v3. Reads preserve the
stored version. Unregistering the user retains `user: null`.

Journal v2 derives consumer scope from its validated before/after registries;
manifest destinations are recomputed as `<project>/.mask.json` or the current
`MASK_HOME/user.json`, never accepted as arbitrary serialized write paths.
Rollback restores the exact prior state bytes. Mutators refuse pending recovery; unknown schema versions fail closed.
Current capabilities report readable state versions `[1, 2, 3]` and state version 3. The readiness and pinned extensions use journal v3 while preserving the v1/v2 readers.
The result envelope remains v1.

## Task commands (RFC-MASK-0018, MASK-0086)

`install ID ...`, `remove ID ...` and `list` express one complete user task for the
current project (worktree-aware; the worktree root when no declaration exists yet)
or the personal scope with `--user`. They are engine operations, not shell aliases:
`mask_task` builds one prospective v2 declaration and one lock through the shared
resolver (`mask_resolve`), planner (`mask_fs.plan`) and journal, then activates that
single frozen plan under the writer lock. A missing declaration and registration
are folded into the same operation; a dry run of that case reports
`declaration_created` and computes no plan. A new consumer is always an empty v2
selection with the machine's default agents and an empty lock.

A declaration of any other version refuses `manifest.unsupported_version` (exit 4).
Install and remove resolve only the new bindings and retain unrelated exact
resolutions, source declarations, conditions and agents.
`--agent` selects the agents of the newly requested bindings; a no-op reinstall
changes nothing, including an already selected binding's agents.

A bare ID resolves only when exactly one relevant approved tap offers it; a
name already bound in the declaration prefers that source. Two matches return
`skill.ambiguous` with `SOURCE/ID` choices. A live install first fetches a tap it
cannot resolve from its cache into its bare cache to resolve a new binding (reported
under `data.acquisitions`, `data.network: fetch`), so a live bare-ID install may
fetch every such tap. `--offline` and `--dry-run` never fetch: a bare ID then
refuses `source.unresolved` naming the unresolved taps, and a qualified `SOURCE/ID`
refuses `lock.resolution_required`.
New repository identities still require `tap add`.

`remove` refuses with `target.collision` and applies nothing when an owned link was
replaced by real content; it never deletes edited files. A remove for a skill that
is not selected is a no-op with a `selection.not_selected` warning. `remove` on an
unregistered scope is refused; nothing is deployed there. The other scope's
selection is never touched. Both commands are plan-guarded (`--expect-plan-hash`);
they ask no confirmation because their scoped engine effects are ordinary authority.

`list` derives per-skill, per-agent states (`linked`, `missing`, `drift`,
`collision`, `not deployed`, `excluded`, `unknown`) from the same plan, reports
`links.expected/linked`, `source.mode: pinned` with the selected taps, and each
skill's commit and selector, and states its limitations
(host loading and workflow setup are not checked). An undeclared scope lists
nothing and suggests `mask install ID`.

## Consent (RFC-MASK-0018, MASK-0085)

`mask_consent.py` is the single seam for significant authority. The engine
builds one proposal (`kind`, `reason`, `scope`, `actions`, `plan_hash`) and calls
`require`. Kinds are `readiness`, `source.trust`, `package.setup`, `overwrite` and
`ref.rebind`; only `readiness` is ordinary. The proposal is
authorized by, in order: in-process consent retained from the prompt, a matching
`--expect-plan-hash`, or `--yes` for an ordinary kind. `--yes` never grants package
scripts, new source identities, overwriting edited content or ref rebinding,
and never persists integration approval.

A prompt appears only for a manual invocation with stdin, stdout and stderr on a
terminal and no `--json`/`--event`: the proposal and a default-no question go to
stderr; EOF declines (`confirmation.declined`, exit 4); Ctrl-C is interruption
(130). The dispatcher releases the writer lock before asking, then reacquires it,
recomputes the proposal and refuses a changed plan hash (`plan.stale`, exit 4)
before any effect. JSON, redirected streams and event hooks never wait: they
return `confirmation.required` (exit 4) with the proposal under
`data.confirmation` (`granted_by: null`), which is a proposed action, not a
receipt. A granted proposal is echoed with `granted_by` set. `--dry-run` shows
the proposal without asking. Plan hashes stay inside the program; humans copy
nothing.

## Workspace readiness (unreleased RFC-MASK-0006 additions)

### Explicit repair (September 10 correction)

`ensure [--project DIR|--user|--all] --repair` (`--yolo` alias) is explicit
one-invocation authority to run declared setup and replace regular native role
files after backing up their exact observed bytes. This owner-requested mode
amends the earlier preservation-only contract; normal ensure and `--yes` keep
their existing authority. Repair works without prompts, including with `--json`.
It is forbidden for events; `--check` and `--dry-run` never execute setup or
write backups. It does not persist integration approval. Pinned consumers may
fetch their exact locks from already approved sources unless `--offline` is set.

Role changes carry an explicit `repair: true` on typed native-role journal
entries. Only ensure may carry it; both before and after bytes are required,
paths remain adapter-derived, and after bytes must agree with validated role
content and ownership. Before replacing any role, save exact original bytes
and a path manifest under `MASK_HOME/backups/TRANSACTION/`. Backups are
idempotent, refuse changed destinations, and survive success or rollback.
Generated-role locks being replaced by repair are backed up too. Concurrent
role edits during setup refuse publication. Recovery restores the recorded
transaction side without rerunning scripts. Older readers reject the extension
rather than treating it as ordinary overwrite authority.

`--all --repair` processes each registered project and the personal scope
independently, including preparation and the writer lock. `data.repair_results`
contains each root, readiness and error; `data.backups` reports original paths,
backup paths and saved status. Ordinary scope failures do not stop later scopes;
pending recovery stops further mutation. An incomplete run exits 4 with
`repair.incomplete`. `--all --repair` intentionally authorizes fresh per-scope
plans and rejects a single `--expect-plan-hash`; select one scope to use a guard.
Missing consumer facts, unsafe paths, skill-link collisions and invalid sources
remain errors, never guessed configuration, directory deletion or new grants.

`integration approve --project PATH [--linked-worktrees] [--inactive-branches]`
records physical-root authority in `MASK_HOME/integration.json`. Approval is
separate from installing an integration and from ordinary explicit registration.
`integration revoke --project PATH` removes direct authority while preserving links. It refuses when a broader linked-worktree or repository approval would still authorize the root.
Both commands support dry-run and a plan guard. `integration inspect --project PATH`
reports approval, the registration identity used for retirement, owned adapter
configuration, and unverified host loading. `integration approve --repository ID --under ROOT` authorizes future repository roots beneath an existing physical clone directory. The directory identity and exact credential-free origin identity must match; outside or replaced boundaries refuse. Use the matching `integration revoke --repository ID --under ROOT` to remove that policy.

`ensure [--project PATH|--user|--all] [--event EVENT] [--check] [--offline] [--dry-run]`
registers and reconciles an approved project under the ordinary writer lock.
`--user` selects the registered personal consumer and `--all` every registered
consumer, in place of working-directory detection; both are mutually exclusive
with `--project` and skip the nested Git-event discovery an implicit selection
uses. Each selected project still needs its own readiness authority, and setup
consent still names one exact action per skill and consumer.
It reads each selected consumer's v2 declaration and exact lock and prepares the
locked artifacts from the tap cache and store. It fetches only an exact locked
commit, as described under [Pinned consumers](#pinned-consumers-and-recoverable-activation),
and never resolves a newer selector. It does
not require a caller-supplied plan hash. `--check` performs no writes and exits 7
for drift. A manual `ensure` of a project without integration approval builds
its proposal and asks for one-time consent (Consent below); events and `--check`
still require recorded approval (`integration.approval_required`). An already
usable unapproved project is a no-op reporting `approval: not_approved`. Busy writers fail immediately with exit 6; pending recovery exits 8.
No-op runs preserve managed file bytes and registry generations. Filesystem
readiness is `ready_pinned`, separately from `host_load: not_verified`.

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

Readiness journals use v3 control observations; pinned ownership uses state v3 with additional pinned journal observations.
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
from PATH with an argv array. Capabilities mark launch as network-capable because the invoked host may use its own network services; readiness fetches only an exact locked commit under an explicit grant. Dry-run never launches. Ordinary mode inherits host
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

## Inventory (unreleased RFC-MASK-0011 slice)

`inventory [--project PATH | --user | --all] [--include-unmanaged]` reports the
selected registered consumers from their live declarations, locks and owned links.
Without a selector it uses the current project.
`skill where-used SOURCE/ID [--agent claude|codex] [--scope user|project]` searches
every registered consumer for that coordinate; its alias must name an approved tap
(`source.unknown`).

Both commands accept `--limit 1..1000` (default 100) and `--offset N`, with
`total_rows` and `next_offset` in the result. Pagination limits output; the
reported work counters describe the full selected query. No network operation,
writer lock, fetch, store materialization or control-file write occurs; a
declaration or lock that changes during the report refuses `state.drift`. Present
metadata is read from the locked store copy and must match its locked digest.
`--include-unmanaged` enumerates supported discovery directories one
level deep and never follows neighboring links or adopts content.

Rows report the coordinate, the tap alias and repository, the package path,
`artifact` (`payload_digest`, `metadata_digest`, `commit`, `selector`),
`content_mode` (`pinned`, `dev_link` or `unknown`), whether the row is declared or
owned, the observed leaf, and a status: `managed_converged`, `managed_drifted`,
`declared_not_deployed`, `unmanaged_present`, `inapplicable`, `blocked` or
`unavailable_consumer`. `recorded_source_revision` is always null. A consumer whose
live controls cannot be read is reported from its cached pinned selection
(`declaration_basis: cached_pinned_selection`) as a diagnostic, with no claim that
it is current.
Compatibility is unspecified for development links and wherever locked store
metadata is not observable, and host loading is unverified.
Profile/fleet fields and full update-impact reports remain unimplemented RFC work.

### Cached selection locks

`mask lock [--project PATH | --user] [--refresh] [--skill SOURCE/ID ...]
[--allow-ref-rebind]` reads a v2 selection and writes `.mask.lock.json` or
`MASK_HOME/user.lock.json`. It supports `--dry-run` and `--expect-plan-hash`.
It never fetches, checks out files, builds artifacts or changes deployment links.
Approve sources and explicitly fetch required refs/commits first.
`source fetch NAME`, like `source fetch` without a name for every tap, acquires
only the configured selector; another annotated tag can be
advertised without its tag object being cached. Use
`source inspect NAME --ref refs/tags/TAG` to acquire that selected object before
locking. Missing tag objects return `lock.resolution_required`. Every selected
binding is resolved, including bindings with conditions false on this machine.
File repository URIs are machine-local fixtures/inputs; output reports
`portable: false` and makes no cross-machine portability claim for them.

The explicit `project-v2.schema.json` and `lock-v1.schema.json` contracts are
closed; the user declaration schema is the same v2 contract. The
`selection_manifest` reader refuses any other declaration version
(`manifest.unsupported_version`, exit 4). V2 consumer commands report `lock.missing` or `lock.stale` when required. New
v2 project/user consumers support pinned registration/apply/ensure,
per-binding targets and local compatibility policy.

Canonical bytes are sorted-key compact UTF-8 JSON without ASCII escaping or a
trailing newline. Duplicate keys, floats, nonfinite numbers, unsafe/negative
integers, invalid Unicode scalars and unknown closed fields are rejected. Source
maps have at most 256 entries and declarations/locks at most 4096 bindings and
4 MiB. Bindings sort by `source/id`; semantic string sets sort lexically.
Missing `default_agents` becomes `all`; missing binding `agents` remains omitted to preserve inheritance intent; missing source `packages` becomes `skills`. An omitted ref uses the
approved machine selector only at initial resolution/explicit refresh, normalized
to a cached fully qualified branch/tag or full commit. Portable explicit refs
must start with `refs/heads/` or `refs/tags/`. Lock resolution itself does not evaluate target applicability.

Locks retain exact path, full SHA-1/SHA-256 commit, object format, selector and
raw Git payload digest, including logical executable modes and every regular
payload file. Metadata digest hashes normalized passive `mask-skill.json`; an
absent file hashes the canonical bytes `null`. Present metadata uses sorted sets;
requirements are bounded human-readable assertions and grant no execution or
provider authority. The optional provenance digest hashes the exact bytes of
`.mask-provenance.json`, including whitespace/newlines, without certifying its
claims. Both files also participate in the complete payload digest.

A coherent existing lock remains byte-for-byte unchanged until explicit refresh,
even after cached refs or authoring files move. Selected refresh preserves other
resolutions. An intent-only edit can update the selection digest while retaining
resolutions. Changed identity/selector requires explicit refresh; an exact commit
requirement never resolves to another commit. Moved tags and branches not proven
fast-forward require `--allow-ref-rebind`. Missing original objects block exact
verification instead of substituting current refs. The command verifies retained
payloads at the frozen path and original index, not a later index. Publication
bounds serialized lock bytes before preview/write and rechecks physical project/
machine-home identities plus exact declaration/config/lock bytes under the machine writer lock; this
is a same-user concurrency guard, not a hostile-same-user security boundary.

### Exact artifact preparation

`mask source fetch --locked [--project PATH | --user] [--offline]` prepares
artifacts for an already coherent v2 lock. It changes no declaration, lock,
consumer state or deployment link. `--dry-run` is always observational and
network-free; unavailable exact objects are reported as resolution required.
`--offline` materializes only cached content. Online invocation may acquire only
the approved full locked commit, never resolve a newer selector. Exact acquisition
leaves `refs/mask/selected`, cached advertisements and FETCH_HEAD unchanged.
Network attempts and retained cache/store effects are reported separately.

Store paths are derived as `MASK_HOME/store/v1/<sha256-hex>/payload/<id>`.
The sibling `manifest.json` records every raw file, logical Git mode, size and
content hash plus metadata/provenance digests. Its 16 MiB limit accommodates the
bounded 10,000-entry payload policy. Source identity and revision remain in the
lock; identical validated content can share an artifact across revisions/sources.

Preparation revalidates supplied bytes, stages on the same volume, flushes files,
verifies the complete tree and publishes without replacing any existing directory.
It copies bytes without hardlinking authoring files. Reuse checks all files and
directories, including unexpected empty directories, links and special entries.
Corrupt existing artifacts are preserved and refused. No garbage collection or
automatic repair runs. Files are read-only as an accidental-edit guard; directories
are not a hostile-same-user boundary. POSIX executable bits are compared to logical
modes; Windows retains logical modes in the manifest without claiming POSIX mode
observations. Unchanged retained artifacts can be verified without Git or a cache.

The internal `mask_store.ensure` defaults to offline preparation. Its optional
`coordinates` subset must contain unique bindings from the fully validated lock;
default preparation includes all bindings. It does not activate links or evaluate
target policies. Artifact availability and acquisition
effects are preparation observations, not part of the consumer's exact intent.


### Pinned consumers and recoverable activation

New v2 consumers use `install`, or `project register [--apply]` / `user register [--apply]`,
then ordinary `plan`, `apply`, `ensure`, `doctor`, adoption and unregister.
Whole-selection `default_agents`, per-binding `agents` and `when` are operational.
The evaluator reports implicit metadata exclusions and blocks explicit incompatible
intent. Different-coordinate invocation collisions fail at a shared consumer/agent
destination; disjoint agents are permitted. Attributed contribution semantics
are described below.
Ordinary
`mask lock` refuses a changed active pinned lock with `lock.active`; lock changes
must go through the journaled update seam, not a separate file write.

State v3 adds pinned records containing cached selection/lock models and exact
resolution identities on owned links. User and launcher operations cannot
downgrade state v3. State v1/v2 hold no consumer record: every consumer
record is pinned or dev-link and requires state v3.

The existing engine derives old and new artifact targets independently and only
retains an old raw link spelling when it still names the desired target. Journal
v3 extends its bounded roles with project/user declaration and lock files. Paths
are reconstructed from selected roots; exact before text binds the observed live
controls, while after text binds desired ownership. Recovery checks both artifact
versions, root identities, branch/index observations, configuration and authority
before effects. Corrupt artifacts or changed control/branch evidence produce a
recovery conflict and preserve the journal. Rollback retains artifacts and restores
only unchanged owned links/control bytes. This is recoverable convergence across
files, not an atomic switch for running readers.

Preparation runs outside the consumer writer lock. After reacquiring the lock,
MASK compares exact control/policy/state bytes, generations and physical/worktree
identities before activation. Plan hashes describe consumer intent and remain
stable across artifact materialization. Plans/checks/previews do not fetch or
materialize. A plan whose store artifact is still absent examines the exact locked
payload in the approved tap cache instead, so a cold preview discloses and binds
the native role writes and setup identities that the applying run plans after
materializing it (MASK-0111). When the cache lacks the locked commit, that content
stays unexamined; a guarded run that must first acquire it refuses `plan.stale`
if the acquired content adds roles or setup to the plan. Warm artifact validation does not consult source Git; worktree Git
observations still establish branch/index preconditions. Each activation rechecks
its relevant old/new artifacts, with a deduplicated complete preflight.

`ensure` may fetch an unavailable exact commit only after an explicit
`integration approve --project PATH --allow-locked-fetch SOURCE` grant for that
physical scope/source. Ordinary integration approval grants no network authority;
omitting this option preserves existing grants. Generic/linked-worktree approval
does not infer a fetch grant for another root. `--offline` always prohibits fetch.
Personal readiness infers no network authority; `source fetch --locked --user`
remains the explicit preparation command. No readiness operation resolves a newer
ref or rewrites its selection/lock. Retained preparation effects survive failures,
including stale post-preparation inputs and consumer noops. A created artifact or
acquired object sets `changed: true` and is listed in `data.retained_preparation`;
it turns a successful `not_needed` result into `committed`, leaves a refusal
before any consumer effect `not_started` (MASK-0112; see
[JSON envelope](#json-envelope)), and keeps a consumer `committed`, `rolled_back`
or `partial` status.

### Selected updates and authoring exceptions

**Doctor.** `doctor` reports a tap catalog entry that records an older spelling of
its identity as `migration.identity_canonicalization`. `doctor --migrate [--dry-run]
[--expect-plan-hash HASH]` rewrites those entries (see
[Taps, payloads and caches](#taps-payloads-and-caches)). `--migrate` conflicts with
`--check`, and `--project`, `--user` or `--all` with `--migrate` is
`invocation.invalid`; `--dry-run`, `--yes` and `--expect-plan-hash` without
`--migrate` are `invocation.invalid`.

Unavailable registered project/personal roots appear as `project.unavailable` or
`user.unavailable` with their path and restoration/unregister guidance. Doctor
continues observing available scopes without changing registry or approval records;
plain inspection exits 0 with `healthy: false`, and `--check` exits 7 with
`state.drift`. `ensure --all --repair` likewise retains per-scope failures and attempts
the remaining roots (aggregate `repair.incomplete`, exit 4). Stale approvals are
retained: temporary unavailability does not authorize automatic pruning. Unhandled
filesystem errors preserve available `filename`, `filename2` and `errno` details.

**Cache repair.** `source repair-cache NAME [--dry-run] [--expect-plan-hash HASH]`
validates the approved cache location and recognized repository marker, then retains
the entire directory at a reported sibling path with an atomic no-replace move.
The plan binds the catalog bytes, actual directory identity, marker and destination.
It never blesses a mismatched identity, reuses objects, deletes content or contacts a
remote. Unrecognized markers, links and retention collisions refuse. Missing caches
are already ready for reconstruction. The next ordinary `source fetch NAME` creates
a fresh owned cache; catalog, registry, store and consumer deployments are unchanged.

**Update.** `upgrade [--project PATH | --user | --all] [--skill SOURCE/ID ...]
[--allow-ref-rebind] [--offline] [--dry-run] [--expect-plan-hash HASH]` fetches
and applies the selected consumers' updates end to end:

1. A pending journal refuses `recovery.required` (8). No scope, or `--all`, selects every registered consumer; an empty selection exits 0 with warning `project.empty_registry` and fetches nothing. Every selected root must still be available (`project.unavailable` and similar refuse before any fetch). `--skill` coordinates must be unique and declared by the selected consumers (`invocation.invalid`, 2); they narrow both the consumers and the taps. A dev-link consumer is skipped with warning `dev_link.active` by the unscoped form and `--all`, and refused (4) by `--project` or `--user`.
2. The referenced taps are the union of the selected declarations' sources, or of the `--skill` bindings' taps. Unless `--dry-run`, `--offline` or `--expect-plan-hash` is given, MASK takes the writer lock for the whole fetch round and fetches each tap exactly once, after listing its remote refs, with one `git fetch` that also acquires the objects the selected bindings' declared selectors name. Another writer meanwhile fails `lock.busy` (6). `data.fetches[alias]` reports `attempted`, `ok`, `before`, `after`, `remote_refs_changed` and `error`. Git and source errors are captured per tap; any other error propagates.
3. Consumers that reference a failed tap are `blocked` and left out of the plan. With `--project` or `--user`, a failed tap is a plain refusal with its Git error (exit 5).
4. Every remaining consumer is resolved from the cache. A moved tag or a branch not proven fast-forward (`lock.ref_rebound`) refuses the whole invocation (4) unless `--allow-ref-rebind`. In a run that did not fetch, `lock.resolution_required` marks the consumer `blocked` with `requires_fetch: true`. Every other resolution error, and `lock.resolution_required` after a fetch, refuses the whole invocation (4) before any plan or journal; the fetch effects stay disclosed and the fetched objects stay in the caches.
5. `data.consumers[]` rows carry `root`, `scope`, `status` (`updated`, `unchanged`, `blocked` or `skipped`), `changes` (`coordinate`, `before_commit`, `after_commit`, `before_digest`, `after_digest`, `selector`) and `error`, followed by the ordinary public plan. The plan hash also binds which roots were blocked or skipped, but not the fetch effects, so a dry run and a guarded rerun agree; a guarded rerun never fetches.
6. Apply prepares store artifacts offline, retakes the writer lock and rechecks the consumer snapshot (`plan.stale`, 4, reported `not_started` with `data.retained_preparation` when preparation created artifacts). It then activates one journal with `operation: update` and reports the shared readiness final status.
7. When any consumer was blocked, the others are applied or no-oped and the command ends `upgrade.incomplete` (4), naming the blocked roots in `details.blocked`; its `transaction` reflects what was applied to the other consumers (`committed` when any changed), and its details add the workflow verdict when declared roles are also incomplete.

**Fetching without deploying.** `source fetch` without a name fetches each approved
tap's configured ref once and deploys nothing; `data.fetches` has the same rows as
`upgrade`. A failed tap does not stop the others, and the command then refuses with
the first failure's code and `details.failed`. `--dry-run` fetches nothing. It does
not acquire objects that consumers' declared selectors name. A later
`upgrade --dry-run` review of a consumer whose declared tag or branch names an object
that the configured ref did not bring into the cache, such as an annotated tag
object or a commit that is only on another branch, reports that consumer `blocked`
with `requires_fetch: true` until `source inspect NAME --ref REF` acquires the
object; a lightweight tag at a fetched commit resolves. A plain `upgrade` acquires those objects in its own fetch. `source fetch NAME`
fetches only that tap's configured ref, and `source fetch --locked` is described
under [Exact artifact preparation](#exact-artifact-preparation).

**Switching executables.** Finish a pending journal with this program before
switching executables; a previous program does not recover one. A previous program
refuses a tap entry that carries `line_endings` (`source.invalid`, exit 3), so it
does not recover a pending `upgrade` journal either.

`source dev-link SOURCE/ID (--project PATH | --user) --authoring-root PATH`
creates a scope-local live exception to an existing pinned selection. It is the only
link producer whose target is a checkout. The source
must be an approved physical authoring checkout and the package must pass bounded
passive validation. State records `mode: dev-link`, exact root identity/path and
per-link overrides; the retained selection/lock still identifies the pinned
return destination. Dev-link is explicitly unpinned, not fleet eligible, and has
no automatic writeback. Read-only `ensure --check` inspects these declared links,
including selected workflow profiles, and reports `ready_dev_link` when complete;
it does not run setup or reconcile the scope. Ordinary `apply` and mutating `ensure` refuse an active override;
`upgrade` skips it without a scope and refuses it with `--project` or `--user`.
Use the same command with `--to-pinned` to preview and perform a guarded return.
Its typed development journal binds both old/new roots and the currently observed
package bytes; source changes during recovery refuse without overwriting edits.

`source publish SOURCE --paths PACKAGE_PATH ... [--commit] [--push]
[--message TEXT]` accepts up to 64 exact non-root package paths from the approved
layout/index. The selected index mapping must already be committed; uncommitted
mapping changes require an explicit separate authoring commit. Default and dry-run only preview. `--commit` separately authorizes
a new commit and retained `refs/mask/published/<commit>` ref; `--push` additionally
authorizes pushing that child commit to the configured branch only when its
remote parent still matches. Staged changes inside selected paths refuse;
unrelated authoring/index changes are preserved. A no-checkout isolated worktree
uses raw blob/index plumbing with filters, hooks, fsmonitor and signing helpers
excluded from execution. Temporary worktrees are removed. Reports distinguish
created commit/ref, attempted/completed push, and unchanged authoring HEAD/index;
the authoring checkout does not advance to the published revision. Failures after
object construction report potentially retained objects even without a commit.
An attempted push with a lost/failed acknowledgement reports an unknown outcome
and retains the created commit/ref for inspection. Source
publication never updates consumer locks. File-URI fixtures remain machine-local.

Tap line endings (MASK-0109, amending the RFC-MASK-0021 tap entry shape). A tap
keeps exact bytes: its catalog entry's `line_endings` is `exact`, or absent in an
entry written before the policy existed. `tap add --autocrlf` is the only opt-in
and records `autocrlf`; `tap add` writes the field, and
`tap add`, `source show`, `source publish` and `source dev-link` report it.
Changing an existing tap's policy is an alias conflict. Caches are bare and read
raw Git objects, so the policy governs only the bytes MASK derives from an
authoring checkout. For an exact tap those are the raw working bytes:
`source publish` and a new `source dev-link` refuse
`source.line_endings_converted` (exit 4, naming repository paths) when an unedited
package file differs from its committed copy only in line endings, as Git's own
conversion leaves it, and `tap add --checkout` warns
`source.line_endings_conversion` when the checkout's effective `core.autocrlf`
converts. MASK never edits the checkout's Git configuration; set
`core.autocrlf false` there, delete the reported unedited files and check them
out again (`git checkout -- PATH ...`; Git leaves a stat-clean converted file in
place), or register the tap with `--autocrlf`. For an autocrlf tap MASK applies Git's `core.autocrlf=true` check-in
conversion to published and development bytes (Git's text statistics decide, and a
file whose committed copy is text that already holds CRLF is not converted). Files with a `text`, `eol`, `crlf`,
`filter`, `ident` or `working-tree-encoding` attribute refuse
`source.line_endings_unsupported` instead of running a filter. An existing
development link's later observations use the same policy without refusing.
`source dev-link` reports each observed development payload digest. A previous
tap-era program refuses a catalog entry that carries `line_endings`.


### Targeting and machine-local compatibility policy

`project set-agents SOURCE/ID AGENT ...|--all|--inherit [--apply]` and its
`user` counterpart require an explicitly registered v2 consumer.
`set-targets AGENT ...|--inherit` changes
`default_agents`. Without apply, exact package rows and actual owned links remain
while selection/lock digests and cached desired controls change together. With
apply, prospective links and controls share one collision-preflighted journal.
All setters support dry-run and expected plan hashes.

`selection-policy set --agent AGENT ...` changes enabled supported adapters for
all registered scopes. `selection-policy clear` restores the supported default
while preserving overrides. `compatibility override SOURCE/ID --project PATH|--user
--reason TEXT [--agent AGENT ...] [--platform] [--architecture]` records one
reasoned local override; at least one dimension is required. `compatibility clear`
removes only that scope/coordinate row. These policy commands reconcile affected
scopes, use exact typed `selection_policy` before/after bytes and machine/root
identities, and expose every affected scope in the preview. Other override rows
remain exact. Overrides never grant adapter/source authority.

`MASK_HOME/selection-policy.json` is a closed, non-portable v1 object bounded to
1 MiB, with `enabled_agents` and up to 4096 `overrides`. Absent policy means both
supported adapters enabled. Each override binds canonical root, device/inode,
coordinate, reason and explicit compatibility dimensions. It cannot come from
remote metadata. Explicit disabled-agent intent blocks; implicit all ignores
disabled adapters.

Planner `data.outcomes` rows carry scope, coordinate, agent, origin, status,
compatibility assertion and `tested: false`. Status is selected, deployed,
not_applicable, excluded_by_metadata, blocked or overridden. Only observed owned
links with verified usable targets become deployed; missing artifacts remain
selected in observational plans, and corrupt retained artifacts block; an override retains its warning/status and may additionally
report `deployed: true`. Metadata requirements are plain informational strings.
False when conditions skip metadata and artifact acquisition while keeping all
locked bindings. Absent metadata is unspecified; generic/specific assertions
remain distinct. Applicable device incompatibility and explicit incompatible
agent requests block unless covered by local reasoned authority.

`mask_selection.evaluate` is a pure attributed-contribution input seam, currently
fed only the local declaration. Filesystem effects remain in the ordinary
planner. Attributed contribution union/conflict/shadowing is operational internally;
public profile producers remain RFC10. No native targeting acceptance is claimed by this implementation.


### Audited adapters and effective contribution conflicts

`mask_adapters.py` is the only built-in adapter data source. It supplies project
and user paths, startup-config paths, reload/gate fields, reserved invocation
names and known package-kind hazards. CLI/core path maps are derived views;
persisted schema enums have an explicit parity test. Capability
`adapter_contracts` exposes these facts and per-adapter evidence. Future rows have
no native evidence by default. Claude/Codex retain recorded macOS/Windows
readiness evidence and unverified host loading; Linux remains best-effort. There
are no dynamically loaded adapter plugins or additional advertised agents.

`mask_selection.evaluate` accepts up to 64 attributed contributions and 4096 total
bindings for one physical consumer scope. Evaluate `when` first. Inapplicable
contributions retain `not_applicable` outcomes and exact lock attribution without
metadata/content access or conflicts against an applicable edge. Positive edges
with equal coordinate, approved repository identity, payload digest, metadata
digest and optional provenance digest merge by union. Ordinary explicit agent
lists and absence are positive choices, never denials of another contribution.

Pure deployment/outcome rows retain `origins` and `resolutions` (every exact
origin/locked-resolution pair). Equal content at differing commits/selectors is
allowed; the canonical-byte-smallest complete resolution is the deterministic
representative for its identical destination. All source facts remain in the
attribution, so this is neither an implicit version update nor last-wins policy.
The caller must approve every contribution's source requirements before planning
effects; attribution itself grants no source authority.

Competing repository identities or content/metadata/provenance claims under one
coordinate yield `selection.conflict`. Different coordinates with one invocation
name collide only at the same consumer/agent destination and yield
`target.collision`. `conflicts` explains every competing origin and resolution.
Disjoint agent destinations are allowed. No renaming or implicit override occurs.
Unknown future agent names remain valid publisher restrictions while unsupported
consumer agent requests are rejected.

Planner/show `shadowing` rows report matched user/project names, scope, agent,
coordinate/digest when pinned, `same_target`, and observed-versus-planned link
status. An observed row means the recorded symlink and directory target are
present, not that host loading or unrelated payload integrity was attested. Every
overlap is reported; `same_target` marks the pair whose scopes resolve to one
directory, where precedence cannot change which bytes a host would load, and only
a pair without it raises the `target.scope_shadowing` warning. Host precedence
remains `not_assumed`. These diagnostic observations never suppress a deployment
or change unrelated scope ownership.
Full pinned inventory/where-used remains RFC11; public profiles/bundles remain
RFC10. Native integrated adapter acceptance remains MASK-0040.
