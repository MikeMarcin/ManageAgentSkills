# Workspace readiness, startup adapters and inventory

Readiness approval, `ensure`, `launch`, Git/host startup adapters and detailed inventory. `mask ensure` from the [README](../../README.md) asks for the one-time readiness approval itself; the explicit commands below remain available.

## Workspace readiness and startup

For a project with an existing `.mask.json`, explicitly approve automatic
readiness, then reconcile or check it:

```sh
mask integration approve --project /absolute/path/to/project --dry-run --json
mask integration approve --project /absolute/path/to/project --expect-plan-hash RETURNED_HASH --json
mask ensure --project /absolute/path/to/project --json
mask ensure --project /absolute/path/to/project --check --json
```

`ensure` registers and reconciles an approved project under one writer lock,
without a caller-supplied plan hash. It prepares locked payloads from the local
tap cache. Unless `--offline` is given, it fetches locked commits only from taps
that the approval names with `--allow-locked-fetch`, or from every locked tap under
`--repair`. Registration alone does not grant readiness approval.
`--check` is observational and exits 7 for drift; a busy writer exits 6 and pending
recovery exits 8. A ready result describes filesystem deployment of locked store
content, not confirmation that an agent has loaded the skills.

A package may declare workflow prerequisites in a passive `mask-workflow.json`
beside `SKILL.md`: bounded consumer inputs and the native role files each
selected agent needs (`.codex/agents/<name>.toml`, `.claude/agents/<name>.md`).
`ensure` checks them with the links. Static role assets shipped by the package
are copied exactly through the same journaled engine (a package whose assets
carry fingerprints must disable Git line-ending normalization for them, for
example `* -text` in `.gitattributes`, or a checkout on an `autocrlf` host is
refused as `workflow.invalid` rather than deployed with converted bytes); roles already committed in
the consumer (optionally vouched for by
`.mask/generated/<skill>/native-roles.lock.json`) pass as repository-owned
and are never adopted, rewritten or deleted. That lock is regenerable machine-local
state and lives beside the skill's other generated files, where the conventional
`/.mask/generated/` ignore rule already covers it; MASK still reads a lock at the
retired `.mask/skill-config/<skill>/native-roles.lock.json` when the canonical one is
absent, so an upgraded consumer keeps vouching until it moves or drops that file.
Committing the lock is therefore a deliberate choice: a consumer that wants a fresh
clone to pass without running setup must un-ignore the canonical path and commit it
with the role files as exact bytes. On an `autocrlf` host a checkout that converts
their line endings is reported as `modified` and preserved, so such a consumer should
exclude them from normalization (for example `.codex/agents/** -text`,
`.claude/agents/** -text` and the lock file in `.gitattributes`). Modified, unknown or colliding
files are preserved and reported, and `ensure` exits 4 with `workflow.incomplete`
until every applicable role and input matches. The result field
`workflow_readiness` lists each role's state, ownership and configured route;
host loading stays `not_verified`.

A descriptor can add `scopes.user` to declare a complete personal-scope contract.
The top-level `inputs`, `native_roles`, `setup`, `retired_paths` and
`compatible_locks` retain their project meaning. The user contract requires
`inputs` and `native_roles`, accepts the same optional fields, and has no
`schema_version` or nested `scopes`. Fields are not merged. Without `scopes.user`,
the original contract applies to both scopes. Only the `user` override is
accepted, and both contracts are validated even when only one is selected.
The user override has a distinct contract fingerprint, so a project lock cannot
automatically vouch for personal roles.

For example, a package can declare project configuration inputs at the top level
and `inputs: []` with a separate setup action under `scopes.user`. Personal setup
then prepares shared roles without requiring a Git repository or project facts
in the user's home. `mask ensure --user` uses the same consent, staging, collision
and ownership checks as project setup. Role destinations and lock paths are
relative to the registered personal home: `.codex/agents/`, `.claude/agents/` and
`.mask/generated/<skill>/native-roles.lock.json`. A workflow's source/tracker
binding remains a separate prerequisite checked by that workflow's preflight;
MASK's generic file readiness does not establish that binding or host loading.

Setup requests (`mask.setup-request.v1`) include `scope` (`project` or `user`), `paths.native_role_lock` and
`paths.retired_native_role_locks`, relative to the consumer root. Standalone
tools read the same keys under `data.workflow.paths` in `mask capabilities
--json`, substituting their skill ID for `{skill}`. These are observational
locations, not permission for a setup script to publish outside its stage.
Packages must consume these fields instead of hardcoding MASK's internal layout.

Descriptors may declare `retired_paths`, a unique list of at most 32 relative
file paths inside `.mask/skill-config/<skill>/` or `.mask/generated/<skill>/`.
Active inputs and the current native-role lock cannot be retired. MASK also
reports its own retired lock location without requiring a package edit.
`workflow_readiness[].skills[].retired_files` reports absent, present, unsafe,
or still-in-use entries. These advisory observations do not invalidate readiness.
Normal commands never remove them. Manual `ensure --repair` backs up and journals
removal of regular UTF-8 files up to 1 MiB once the workflow can be reconciled;
directories, links, linked parents, binary/oversized files and an active fallback
lock are preserved. After successful setup publishes a new canonical lock, repair
can remove the old one in the same invocation. Backups survive rollback; recovery
never reruns setup. This is an explicit repair exception to preserving repository-
owned files, including files tracked in Git; directories are never removed.

A package can vouch for a byte-identical setup refactor with `compatible_locks`:
up to 32 objects containing exact prior `contract_sha256` and
`role_inputs_sha256` values. Both are required because adding this declaration
also changes the descriptor hash. An exact pair can retain an old lock without
running code or rewriting it. Consumer inputs and every role's on-disk SHA-256
are still checked against that lock. This is a package-author assertion of output
equivalence, not an automatic inference; verify equivalent outputs before adding
a pair. Unlisted input changes still require setup, and malformed declarations
are rejected. Setup consent continues to fingerprint the complete current package.

Every public entrypoint shares that one prerequisite verdict. `install`, `remove`
and `upgrade` report `workflow_readiness` and a per-scope
`workflow` summary after their link transaction commits; a declared role or input
that is still unmet makes them exit 4 with `workflow.incomplete` while the links
stay committed and the phases stay truthful. They never run setup: run
`mask ensure` for the consent path. `upgrade` evaluates roles from the selected
candidate, so an added, renamed or re-routed role is deployed, retired or reported
from the candidate bytes, and an edited legacy-name file is preserved. `doctor`
observes the same roles and inputs without deploying or running package code,
lists them under `issues` (`workflow.incomplete`) and in the human text, and
`doctor --check` exits 7 `state.drift` while any is unmet. `launch` runs the
strict prelaunch through `ensure --event startup` and never starts the host behind
an unmet prerequisite; a provider startup hook that cannot stop its host says it
is warning-only. `list` and `inventory` stay cheap and label workflow state as not
checked. `mask capabilities --json` advertises the contract as
`workflow.readiness = workflow_readiness_v1` with typed native roles and approved
staged setup; an older MASK without it still reports link-only readiness.

A package may instead declare a Python setup action that generates a role from
the consumer inputs. MASK offers it only when a selected generated role has no
coherent lock, and only under explicit consent: a manual `ensure` on a terminal
shows the skill and source with its content fingerprint, the exact interpreter
and script, the consumer and role files, and that execution is ordinary user
process execution (not a sandbox), then asks `Run this setup? [y/N]`. Yes runs
the frozen package copy with `--repo-root`, `--output-root` and `--request-file`
(an inert JSON request), bounded by the declared timeout and 64 KiB per stream;
the staged `AGENT/NAME.ext` files are validated, the portable
`native-roles.lock.json` is computed and both are published through the same
journaled engine, after which readiness is rechecked. No or EOF keeps the links
and reports `workflow.incomplete`. `--json`, `--check`, `--dry-run`, `--yes`,
`--event` hooks and redirected streams never prompt and never run package code.
Unattended runs pass the previewed hash with the named action:

```sh
mask ensure --project /absolute/path/to/project --dry-run --json      # review data.plan_hash and data.setup
mask ensure --project /absolute/path/to/project --expect-plan-hash RETURNED_HASH --allow-setup agentskills/implement-rfc:prepare-roles --json
```

A changed package, descriptor, consumer input or interpreter after the preview is
`plan.stale`; a timeout, unsuccessful exit or output overflow stops the owned
process tree and reports `setup.failed` (nothing published, stage discarded);
extra, linked, escaping or unsupported outputs are `setup.outputs_invalid`. A
crash after launch leaves a journal that `mask recover --complete` refuses
(`setup.unverified`) and `--rollback` discards; MASK never reruns package code
from a journal and never claims to undo a script's own side effects.

To run readiness before starting an installed host:

```sh
mask launch --agent codex --project /absolute/path/to/project --
```

Use `--agent claude` for Claude Code. Arguments after `--` go to the host.
MASK releases its writer lock before launching; normal mode inherits host I/O,
while `--json` before `--` captures it. The host may use the network. Startup also
reconciles an already registered personal consumer; it never creates personal
requirements or registration.

Optional Git and host startup adapters have their own preview and apply steps:

```sh
mask integration enable --project /absolute/path/to/project --git --dry-run --json
mask integration enable --project /absolute/path/to/project --git --expect-plan-hash RETURNED_HASH --json
mask integration enable --project /absolute/path/to/project --agent codex --dry-run --json
mask integration enable --project /absolute/path/to/project --agent codex --expect-plan-hash RETURNED_HASH --json
mask integration inspect --project /absolute/path/to/project --json
```

Use each preview's hash for its matching operation. Git installation is per
repository and preserves existing hook managers. Host adapters preserve unrelated
settings and do not grant repository approval or host trust. Claude's startup
adapter can warn and request reload; Codex emits stop/context fields whose native
enforcement remains unverified. Use `mask launch` when readiness must precede
starting the host.

Omitting `--project` from an agent adapter installation selects the registered
personal home, or the OS home if personal scope is unregistered. A user-level
adapter can cover future clones approved with
`integration approve --repository ID --under ROOT`: both the physical clone
directory and exact credential-free origin identity must match. Linked-worktree
approval and inactive-branch cleanup are separate opt-ins. See the
[readiness contract](../architecture/cli-contract.md#workspace-readiness-unreleased-rfc-mask-0006-additions)
for those policies, adapter removal, and recovery constraints.

## Inspect deployment and usage

```sh
mask inventory --project /absolute/path/to/project --json
mask inventory --all --include-unmanaged --json
mask skill where-used agentskills/manage-agent-skills --json
```

Inventory reports declarations, converged or drifted owned links, collisions and
unavailable consumers. `--include-unmanaged` lists neighboring entries without
following their links or adopting content. Cached selections for unavailable
consumers are diagnostic, not current observations. These commands do not fetch,
scan package contents, acquire the writer lock, or change state.

`skill where-used` takes a source-qualified `SOURCE/ID` that names an approved
tap. Both commands support `--limit` (1–1000, default
100) and `--offset`, returning `total_rows` and `next_offset`. Rows report the tap,
package path and locked artifact behind each link. See the
[inventory contract](../architecture/cli-contract.md#inventory-unreleased-rfc-mask-0011-slice)
for filters and result semantics.

### Selected workflow requirements

A package may declare passive `profiles` alongside each project/user workflow
contract, for example `"direct": {"native_roles": []}`. Role entries are unique
`agent/name` references to that scope's declared roles. Profiles retain every
consumer input and package/binding check; absence of a selector preserves the full
existing contract. Invalid profiles refuse even when inactive.

`mask ensure --project ROOT --check --workflow-profile implement-rfc=direct --json`
checks only that declared role subset. Use `--user` for personal scope. This is an
observational capability, advertised as `workflow_requirement_profiles_v1`; it
requires an explicit single scope and rejects setup, repair and automatic events.
It never deploys or retires roles, changes the selected strategy, or proves host
loading. Missing links, approval, invalid inputs and artifact drift remain blockers.
Other selected skills keep their normal requirements. Normal `ensure`, installation
and upgrades still reconcile the complete default role contract.
