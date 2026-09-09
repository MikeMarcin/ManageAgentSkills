# MASK CLI contract v1

Current CLI contract through RFC-MASK-0007, with the implemented lock, artifact store, pinned-consumer engine, migration and authoring slices of RFC-MASK-0008 and the legacy inventory slice of RFC-MASK-0011. The result envelope remains v1; machine configuration and declarations read v1/v2, ownership state reads v1/v2/v3, and pending journals read v1/v2/v3. Source-catalog migration is explicit; selected consumer conversion is explicit. Historical and current native evidence is recorded in the corresponding RFC closeouts; pinned-engine native acceptance is pending.

## Common options

`--json`, `--debug`, `--help`, `--version` and `--home PATH` are recognized without confusing operand values with flags. `--home` overrides `MASK_HOME`; otherwise use `~/.mask`. `--project` accepts one root; project register/unregister also allow one positional root. Conflicting selections refuse. Support common options before or after subcommands as demonstrated in docs. Respect `--` for operand separation and reject an ID beginning with `-`.

All mutators accept `--dry-run` and `--yes`; project manifest mutators may accept `--apply`; mutators using a computed link/manifest plan accept `--expect-plan-hash HASH`. A direct task command authorizes its ordinary scoped effects without a question; genuinely significant new authority is asked for in-process (see Consent below). No generic `--force`. Debug diagnostics are stderr-only, bounded and redacted. Human rendering and JSON rendering share the same structured result object.

## Command inventory and effects

| Command | Exact principal arguments | Writes | Network |
|---|---|---|---|
| `capabilities` | none | None | No |
| `init` | `--source PATH [--remote NAME] [--branch NAME] [--target TARGET ...]` | Initial machine config/state/lock | No |
| `config show` | none | None | No |
| `config set` | `[--target TARGET ...] [--git-timeout SECONDS]`, at least one | Machine defaults only | No |
| `skill list` | none | None | No |
| `install` | `ID-or-SOURCE/ID ... [--project PATH | --user] [--agent AGENT ...] [--offline] [--expect-plan-hash HASH]` | Declaration (created if missing), lock for pinned scopes, registration, links, state; approved source cache when a live install must resolve a new binding | Only for live resolution |
| `remove` | `ID-or-SOURCE/ID ... [--project PATH | --user] [--expect-plan-hash HASH]` | Declaration, lock for pinned scopes, owned unchanged links, state | No |
| `list` | `[--project PATH | --user]` | None | No |
| `skill show` | `ID [--content]` | None | No |
| `skill validate` | `ID` or `--all` | None | No |
| `skill import` | `URL-or-SOURCE --mode copy --into SOURCE [--ref REF] [--path PATH] [--expect-plan-hash HASH]` | New curated directory and provenance; owned upstream cache | Yes |
| `skill provenance` | `SOURCE/ID` | None | No |
| `skill record-adaptation` | `SOURCE/ID --note TEXT [--expect-plan-hash HASH]` | Existing provenance record only | No |
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
| `source fetch` | `[SOURCE]` | Legacy checkout refs or named source bare cache only | Yes |
| `source list` | none | None | No |
| `source show` | `SOURCE` | None | No |
| `source inspect` | `URL-or-SOURCE [--ref REF] [--path PATH]` | Owned bare cache for already approved source; never deployment | Yes |
| `source migrate` | `[--alias NAME] [--expect-plan-hash HASH]` | Explicit machine v1 → v2 migration; legacy alias defaults to `legacy` | No |
| `tap add` | `SOURCE URL [--ref REF] [--packages PATH] [--checkout PATH] [--expect-plan-hash HASH]` | Approved catalog binding only | No |
| `tap remove` | `SOURCE [--expect-plan-hash HASH]` | Unreferenced catalog binding only; retains cache | No |
| `update` | `[--expect-plan-hash HASH]` | Source fast-forward + all registered links/state | Yes |
| `self status` | none | None | No |
| `self install` | `--bin-dir PATH` | Recognized launcher + ownership record | No |
| `self update` | none | Program checkout only | Yes |

`plan/apply` with no selector use the discovered current registered project. `doctor` with no selector checks machine/source and all registered projects and the personal consumer. `update` always selects all; it cannot pretend to isolate shared content to one project. `source update` is deliberately not a separate bypass command; use `update` or fetch-only `source fetch`.

A configuration default change does not relink anything until an explicit apply. There is no source-replacement command that silently relocates all ownership. v1 source relocation uses explicit unregister/setup/register as documented. `project init` and inspection can run before machine initialization where their operation does not need a source/registry. A missing source produces a typed refusal for operations that do need it.

Source catalog commands use explicit machine schema v2 migration. Existing v1
declarations, state and local source behavior remain supported. A named fetch
never checks out or activates payloads; reads and previews never fetch. Missing
cached resolution is reported as `resolution_required`. Approved identities
normalize scheme/host/default port while preserving repository case and `.git`
suffixes. HTTPS and SSH stay distinct; scp home-relative paths retain that
distinction from absolute SSH paths. Passwords, tokens, unsupported protocols,
transport rewrites to other identities and effective redirect policies refuse.
Catalog mutation guards bind the before/after config. `tap remove` preserves all
cache files and refuses the legacy binding or live selection/lock references.
In machine v2, `skill list/show` use frozen fetched source catalogs. Qualified
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
Legacy authoring-checkout updates retain their existing acquisition behavior.
V2 consumer selection follows in later slices.

### Curated copy imports and provenance

`skill import URL-or-SOURCE --mode copy --into SOURCE [--ref REF] [--path PATH]`
uses the approved resolver and requires exactly one validated frozen package.
It is network-capable; `--dry-run` neither fetches nor stages and reports
`resolution_required` when cached resolution is unavailable. Preview/apply
support `--expect-plan-hash`, binding config, selected objects, notice content,
destination HEAD/root/parent identity, source index and Git index entries.

The destination requires an approved authoring checkout on its configured
branch, with no in-progress Git operation. Unrelated working/staged changes are
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

`changed` reports actual remaining changes to managed configuration, registry, manifest, links, launchers or source/program checkout. Fetch-only Git transfer bookkeeping is explicitly reported in `data.fetch_effects`; named-source cache creation is reported in `data.cache_effects`. These effects do not imply skill activation. `would_change` is the preflight proposal. A dry run has `changed=false`, `transaction=not_started` (or `not_needed` when empty), even when actions are proposed.

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
Current capabilities report readable state versions `[1, 2, 3]` and state version 3. The readiness and pinned extensions use journal v3 while preserving the v1/v2 readers.
Legacy user declarations remain v1; pinned user selections use v2. The result envelope remains v1. The source-catalog extension reads machine v1/v2 and migrates explicitly to v2.

## Task commands (RFC-MASK-0018, MASK-0086)

`install ID ...`, `remove ID ...` and `list` express one complete user task for the
current project (worktree-aware; the worktree root when no declaration exists yet)
or the personal scope with `--user`. They are engine operations, not shell aliases:
`mask_task` builds one prospective declaration, and for pinned scopes one lock,
through the shared resolver (`mask_resolve`), planner (`mask_fs.plan`) and journal,
then activates that single frozen plan under the writer lock. A missing declaration
and registration are folded into the same operation; a dry run of that case reports
`declaration_created` and computes no plan. New consumers follow the machine's
source mode: v1 on a schema-1 machine, v2 selection plus lock on a catalog machine.

Legacy (v1) declarations are set union/subtraction. `--agent` on a legacy install
sets whole-declaration targets only for a fresh declaration; otherwise a different
agent set is refused with `selection.per_binding_unsupported` rather than editing
every skill's targets. Pinned (v2) declarations resolve only the new bindings and
retain unrelated exact resolutions, source declarations, conditions and agents; a
v2 add/remove never reaches the legacy `selection.command_unsupported` branch.
`--agent` selects the agents of the newly requested bindings; a no-op reinstall
changes nothing, including an already selected binding's agents.

A bare ID resolves only when exactly one relevant approved catalog offers it; a
name already bound in the declaration prefers that source. Two matches return
`skill.ambiguous` with `SOURCE/ID` choices; an unresolved approved catalog returns
`source.unresolved`. A live install may fetch an approved source to resolve a new
binding (reported under `data.acquisitions`, `data.network: fetch`); `--offline`
and `--dry-run` never fetch and report `lock.resolution_required`. New source
identities still require `tap add`.

`remove` refuses with `target.collision` and applies nothing when an owned link was
replaced by real content; it never deletes edited files. A remove for a skill that
is not selected is a no-op with a `selection.not_selected` warning. `remove` on an
unregistered scope is refused; nothing is deployed there. The other scope's
selection is never touched. Both commands are plan-guarded (`--expect-plan-hash`);
they ask no confirmation because their scoped engine effects are ordinary authority.

`list` derives per-skill, per-agent states (`linked`, `missing`, `drift`,
`collision`, `not deployed`, `excluded`, `unknown`) from the same plan, reports
`links.expected/linked`, the source mode and pins, and states its limitations
(host loading and workflow setup are not checked). An undeclared scope lists
nothing and suggests `mask install ID`.

## Consent (RFC-MASK-0018, MASK-0085)

`mask_consent.py` is the single seam for significant authority. The engine
builds one proposal (`kind`, `reason`, `scope`, `actions`, `plan_hash`) and calls
`require`. Kinds are `readiness`, `source.trust`, `package.setup`, `overwrite`,
`ref.rebind` and `scope.expand`; only `readiness` is ordinary. The proposal is
authorized by, in order: in-process consent retained from the prompt, a matching
`--expect-plan-hash`, or `--yes` for an ordinary kind. `--yes` never grants package
scripts, new source identities, overwriting edited content, ref rebinding or
cross-consumer expansion, and never persists integration approval.

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
for drift. A manual `ensure` of a project without integration approval builds
its proposal and asks for one-time consent (Consent below); events and `--check`
still require recorded approval (`integration.approval_required`). An already
usable unapproved project is a no-op reporting `approval: not_approved`. Busy writers fail immediately with exit 6; pending recovery exits 8.
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

Readiness journals use v3 control observations. Legacy consumers retain state v1/v2; pinned ownership uses state v3 with additional pinned journal observations.
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

### Cached selection locks

`mask lock [--project PATH | --user] [--refresh] [--skill SOURCE/ID ...]
[--allow-ref-rebind]` reads a v2 selection and writes `.mask.lock.json` or
`MASK_HOME/user.lock.json`. It supports `--dry-run` and `--expect-plan-hash`.
It never fetches, checks out files, builds artifacts or changes deployment links.
Approve sources and explicitly fetch required refs/commits first.
`source fetch NAME` acquires its configured selector; another annotated tag can
be advertised without its tag object being cached. Use
`source inspect NAME --ref refs/tags/TAG` to acquire that selected object before
locking. Missing tag objects return `lock.resolution_required`. Every selected
binding is resolved, including bindings with conditions false on this machine.
File repository URIs are machine-local fixtures/inputs; output reports
`portable: false` and makes no cross-machine portability claim for them.

The explicit `project-v2.schema.json` and `lock-v1.schema.json` contracts are
closed. `project.schema.json` remains the historical v1 contract, including its
references from state v1/v2; the user declaration schema accepts either version.
`core.manifest` retains strict v1 persisted-state semantics. The separate
`selection_manifest` reader dispatches declaration versions. V2 consumer commands report `lock.missing` or `lock.stale` when required. New
v2 project/user consumers support pinned registration/apply/ensure, explicit legacy
conversion, per-binding targets and local compatibility policy.

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

New v2 consumers use `project register [--apply]` or `user register [--apply]`,
then ordinary `plan`, `apply`, `ensure`, `doctor`, adoption and unregister.
Whole-selection `default_agents`, per-binding `agents` and `when` are operational.
The evaluator reports implicit metadata exclusions and blocks explicit incompatible
intent. Different-coordinate invocation collisions fail at a shared consumer/agent
destination; disjoint agents are permitted. Attributed contribution semantics
are described below.
An already registered legacy consumer requires explicit migration. Ordinary
`mask lock` refuses a changed active pinned lock with `lock.active`; lock changes
must go through the journaled update seam, not a separate file write.

State v3 adds pinned records containing cached selection/lock models and exact
resolution identities on owned links. Unselected legacy records remain unchanged;
user and launcher operations cannot downgrade state v3. Historical state v1/v2
and journal v1/v2 readers keep their original manifest semantics. Partial legacy
inventory explicitly marks omitted pinned detail instead of reporting it as a
legacy live-source deployment.

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
materialize. Warm artifact validation does not consult source Git; worktree Git
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
including stale post-preparation inputs and consumer noops; consumer partial or
rollback status is preserved separately from those cache/store observations.

### Explicit migration, selected updates and authoring exceptions

`migrate --to-pinned [--project PATH | --user | --all]` converts registered legacy
consumers and, when needed, machine configuration v1 through the same v3 journal.
The source must have a clean committed HEAD on its configured branch; dirty,
unborn, sparse, skip-worktree and assume-unchanged checkouts refuse without
changing authoring content. Migration freezes raw Git bytes and explicitly copies
the resolved legacy target list into `default_agents`. Unselected records remain
exact. Preview is observational, including a cold artifact store. Empty migration
selections refuse; already pinned selected records retain their resolutions.

The typed `machine_config` role derives `MASK_HOME/config.json`; exact old/new
config text and the clean authoring identity/HEAD/index baseline are retained in
the migration extension. Recovery requires that baseline to remain unchanged and
restores exact legacy config, declaration, lock absence and state bytes on
rollback. Recover any existing journal before starting migration. Install a
reviewed compatible program revision first using its direct Python entrypoint,
for example `python3 /reviewed/ManageAgentSkills/mask.py self install --bin-dir
PATH --json`, then preview/run persisted migration. Keep that direct entrypoint
available for recovery. The self-update schema compatibility guard remains in
force; migration never upgrades the executable or resets its checkout.

`update [--project PATH | --user | --all] [--skill SOURCE/ID ...]
[--allow-ref-rebind]` updates selected pinned locks and links in one journal.
Pinned update uses cached source objects only; explicitly fetch or inspect the
chosen source selector first. Dry-run never fetches or materializes artifacts.
Exact commit requirements remain fixed; moved tags and non-fast-forward branch
selectors require `--allow-ref-rebind`. Explicit update can repair a changed
selection with an older disk lock; exact before bytes remain rollback inputs and
the after declaration/lock must be coherent. Ensure/apply do not repair stale
locks. Unqualified update still advances the legacy shared source for all legacy
consumers, including source-only updates with an empty registry. A targeted
legacy update refuses with `migration.required`; pinned consumers are unaffected
by a legacy shared-checkout update.

`source dev-link SOURCE/ID (--project PATH | --user) --authoring-root PATH`
creates a scope-local live exception to an existing pinned selection. The source
must be an approved physical authoring checkout and the package must pass bounded
passive validation. State records `mode: dev-link`, exact root identity/path and
per-link overrides; the retained selection/lock still identifies the pinned
return destination. Dev-link is explicitly unpinned, not fleet eligible, and has
no automatic writeback. Ordinary apply/update/ensure refuse an active override.
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


### Targeting and machine-local compatibility policy

`project set-agents SOURCE/ID AGENT ...|--all|--inherit [--apply]` and its
`user` counterpart require an explicitly registered v2 consumer. Existing v1
`set-targets` behavior remains; on v2, `set-targets AGENT ...|--inherit` changes
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
disabled adapters. Legacy explicit/resolved targets retain their meaning.

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
coordinate/digest when pinned, and observed-versus-planned link status. An observed
row means the recorded symlink and directory target are present, not that host
loading or unrelated payload integrity was attested. Corresponding warnings use
`target.scope_shadowing`; host precedence remains `not_assumed`. These diagnostic
observations never suppress a deployment or change unrelated scope ownership.
Full pinned inventory/where-used remains RFC11; public profiles/bundles remain
RFC10. Native integrated adapter acceptance remains MASK-0040.
