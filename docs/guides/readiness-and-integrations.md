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
without a caller-supplied plan hash. It reads selected packages from the local
source and never fetches. Registration alone does not grant readiness approval.
`--check` is observational and exits 7 for drift; a busy writer exits 6 and pending
recovery exits 8. A ready result describes filesystem deployment of unpinned
local content, not confirmation that an agent has loaded the skills.

A package may declare workflow prerequisites in a passive `mask-workflow.json`
beside `SKILL.md`: bounded consumer inputs and the native role files each
selected agent needs (`.codex/agents/<name>.toml`, `.claude/agents/<name>.md`).
`ensure` checks them with the links. Static role assets shipped by the package
are copied exactly through the same journaled engine (a package whose assets
carry fingerprints must disable Git line-ending normalization for them, for
example `* -text` in `.gitattributes`, or a checkout on an `autocrlf` host is
refused as `workflow.invalid` rather than deployed with converted bytes); roles already committed in
the consumer (optionally vouched for by
`.mask/skill-config/<skill>/native-roles.lock.json`) pass as repository-owned
and are never adopted, rewritten or deleted. Commit them as exact bytes: on an
`autocrlf` host a checkout that converts their line endings is reported as
`modified` and preserved, so a consumer that checks generated roles in should
exclude them from normalization (for example `.codex/agents/** -text`,
`.claude/agents/** -text` and the lock file in `.gitattributes`). Modified, unknown or colliding
files are preserved and reported, and `ensure` exits 4 with `workflow.incomplete`
until every applicable role and input matches. The result field
`workflow_readiness` lists each role's state, ownership and configured route;
host loading stays `not_verified`.

Every public entrypoint shares that one prerequisite verdict. `install`, `remove`
and `update` (shared source or pinned) report `workflow_readiness` and a per-scope
`workflow` summary after their link transaction commits; a declared role or input
that is still unmet makes them exit 4 with `workflow.incomplete` while the links
stay committed and the phases stay truthful. They never run setup: run
`mask ensure` for the consent path. `update` evaluates roles from the selected
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
mask ensure --project /absolute/path/to/project --expect-plan-hash RETURNED_HASH --allow-setup legacy/implement-rfc:prepare-roles --json
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
mask skill where-used legacy/manage-agent-skills --json
```

Inventory reports declarations, converged or drifted owned links, collisions and
unavailable consumers. `--include-unmanaged` lists neighboring entries without
following their links or adopting content. Cached selections for unavailable
consumers are diagnostic, not current observations. These commands do not fetch,
scan package contents, acquire the writer lock, or change state.

`legacy/ID` identifies a skill in the single configured source; other source
aliases are not implemented. Both commands support `--limit` (1–1000, default
100) and `--offset`, returning `total_rows` and `next_offset`. Recorded source
revisions are historical metadata, not content pins. See the
[inventory contract](../architecture/cli-contract.md#legacy-inventory-unreleased-rfc-mask-0011-slice)
for filters and result semantics.
