![MASK — Declare. Preview. Deploy.](docs/assets/readme-header.svg)

**[Install](#install-and-select-a-source) · [First project](#add-skills-to-a-project) · [Readiness](#workspace-readiness-and-startup) · [Inventory](#inspect-deployment-and-usage) · [Updates](#update-skills-or-the-program) · [CLI reference](docs/architecture/cli-contract.md)**

MASK manages project and personal skill selections as directory symlinks to one local skill checkout. Projects keep requirements in `.mask.json`; personal requirements live in `MASK_HOME/user.json`. MASK validates the source, previews changes, and manages the links used by Claude and Codex.

This repository contains the Python CLI. The companion [AgentSkills repository](https://github.com/MikeMarcin/AgentSkills) contains the canonical skill instructions. Both repositories remain private.

## Requirements

- Python 3.11+ and Git. The runtime uses the Python standard library; there is no pip installation.
- Local checkouts of ManageAgentSkills and AgentSkills. Cloning and remote updates use your existing Git access.
- Directory symlink support. Windows needs existing symlink privileges; MASK does not elevate or substitute junctions or copies.

> [!NOTE]
> The new workspace readiness and inventory commands are unreleased additions; the program version remains `0.2.0`. Readiness has native macOS and Windows evidence, including named Git hooks on Windows. Actual first-prompt host loading remains unverified. See the [current acceptance report](docs/development/readiness-acceptance.md). The [v0.1.0 report](docs/releases/v0.1.0.md) records earlier macOS and Windows checks, not acceptance of these additions. Linux remains best-effort.

## Install and select a source

Clone both repositories into a directory of your choice:

```sh
git clone https://github.com/MikeMarcin/ManageAgentSkills.git
git clone https://github.com/MikeMarcin/AgentSkills.git
```

On macOS or Linux, run the following from their parent directory using a supported `python3`:

```sh
mask_program="$PWD/ManageAgentSkills/mask.py"
skill_source="$PWD/AgentSkills"
mkdir -p "$HOME/.local/bin"
python3 "$mask_program" self install --bin-dir "$HOME/.local/bin" --json
"$HOME/.local/bin/mask" init --source "$skill_source" --json
"$HOME/.local/bin/mask" capabilities --json
"$HOME/.local/bin/mask" skill list --json
```

MASK writes a launcher that records the selected interpreter and program checkout. It leaves PATH unchanged. Use the absolute launcher path immediately, or add its directory to PATH yourself before using the shorter `mask` commands below. An unrelated or edited existing launcher is preserved and causes a refusal.

On Windows, use PowerShell with a known supported Python installation. For example, if Python 3.14 is installed and the repositories are under `C:\work`:

```powershell
$maskBin = Join-Path $env:LOCALAPPDATA 'Programs\MASK'
New-Item -ItemType Directory -Force -Path $maskBin | Out-Null
py -3.14 'C:\work\ManageAgentSkills\mask.py' self install --bin-dir $maskBin --json
& "$maskBin\mask.cmd" init --source 'C:\work\AgentSkills' --json
& "$maskBin\mask.cmd" capabilities --json
```

The direct entrypoint remains available if the launcher is missing: `python3 /absolute/path/to/ManageAgentSkills/mask.py ...` (or the corresponding supported Windows interpreter). `self status --json` reports the program, interpreter and launcher discovery. Installing the launcher and selecting the skill source are separate operations.

## Add skills to a project

Use an existing project root. These examples use `/absolute/path/to/project` as a placeholder; replace it before running them. `project init` creates an empty declaration, while `project register` records the project on this machine.

```sh
mask project init --project /absolute/path/to/project --json
mask project register /absolute/path/to/project --json
mask project require manage-agent-skills --project /absolute/path/to/project --apply --dry-run --json
```

Inspect the proposed actions and `data.plan_hash`. Apply that same proposal using its returned hash, then check the result:

```sh
mask project require manage-agent-skills --project /absolute/path/to/project --apply --expect-plan-hash RETURNED_HASH --json
mask plan --project /absolute/path/to/project --json
mask doctor --project /absolute/path/to/project --check --json
```

> [!TIP]
> A converged plan reports `would_change: false`. If the hash is stale, review a new preview. Preserve collisions rather than deleting existing skill content.

Deploying `implement-rfc` also requires [consumer workflow context](https://github.com/MikeMarcin/AgentSkills#configure-implement-rfc).

| Intent | Command |
|---|---|
| Add requirements without removing others | `project require ID ...` |
| Remove selected requirements | `project unrequire ID ...` |
| Replace the complete membership | `project set --skill ID --skill OTHER` |
| Explicitly empty membership | `project set --clear` |
| Choose agent targets | `project set-targets claude codex` |
| Restore default targets | `project set-targets --inherit` |
| Inspect declaration and deployment | `project show --project PATH` |
| Reconcile existing declarations | `plan --project PATH`, then guarded `apply --project PATH` |

Membership edits change the manifest. Add `--apply` to reconcile a registered project in the same operation; add `--dry-run` to preview it first. Use `--json` for structured results throughout.

## Add personal skills

Personal skills apply across projects. Initialize a separate selection and register
the current user's home, then preview a membership change:

```sh
mask user init --json
mask user register --dry-run --json
mask user register --expect-plan-hash RETURNED_HASH --json
mask user require manage-agent-skills --apply --dry-run --json
mask user require manage-agent-skills --apply --expect-plan-hash RETURNED_HASH --json
mask doctor --user --check --json
```

Use each preview's returned hash for its matching operation. `user require`,
`unrequire`, `set --skill ...` / `set --clear`, and `set-targets` have the same
incremental, exact-set, and target semantics as the project commands. They edit
only the declaration unless `--apply` is supplied. `user show` reports the pinned
home, declaration, ownership, and blockers. `user unregister` removes unchanged
owned links and retains the declaration; `--keep-links` abandons ownership.

Codex links live in `<user-home>/.agents/skills`; Claude links live in
`<user-home>/.claude/skills`. MASK does not install into the legacy personal
`.codex/skills` directory. An existing real directory is a collision; imports and
backups are explicit migration work, never an overwrite option.

`user register --user-home PATH` explicitly selects another existing home, useful
for fixtures. Registration pins that physical root; later `HOME` changes do not
redirect it. Unregister before changing the selected root. `--home` continues to
select MASK's state/configuration directory, independently of the deployment home.

`plan --user` and `apply --user` select personal scope. `--all` and unqualified
`doctor` include all registered project and personal consumers. Unqualified
`plan` / `apply` still select the current project. Selections are independent:
adding or removing a personal requirement never edits a project declaration.
Hosts decide how duplicate skill names are discovered; MASK does not suppress
one scope because another declares the same skill.

Existing project-only v1 state is read without conversion. The first user
registration upgrades state through a recoverable v2 journal. Readiness and
integration changes use typed v3 journals; v1/v2 recovery readers remain available.
Pending operations must be recovered before further mutation. The JSON result
protocol and declarations remain version 1, and ownership state remains v1/v2.
Finish recovery with a compatible program before changing installations. The
self-updater refuses changed schema contracts; adopting these additions from an
older schema boundary requires an explicit, reviewed program-checkout update.

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
[readiness contract](docs/architecture/cli-contract.md#workspace-readiness-unreleased-rfc-mask-0006-additions)
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
[inventory contract](docs/architecture/cli-contract.md#legacy-inventory-unreleased-rfc-mask-0011-slice)
for filters and result semantics.

## What belongs where

A portable declaration contains skill IDs and optional targets:

```json
{
  "schema_version": 1,
  "skills": ["manage-agent-skills"],
  "targets": ["claude", "codex"]
}
```

| Location | Purpose |
|---|---|
| `AgentSkills/skills/<id>/` | Canonical skill payload, including `SKILL.md` |
| `<project>/.mask.json` | Versioned project requirements |
| `MASK_HOME/user.json` | Personal requirements, separate from deployment state |
| `<user-home>/.agents/skills/<id>` / `.claude/skills/<id>` | Generated personal skill links |
| `<project>/.mask/skill-config/implement-rfc/` | Versioned workflow context for that consumer |
| `<project>/.agents/skills/<id>` | Generated Codex directory symlink |
| `<project>/.claude/skills/<id>` | Generated Claude directory symlink |
| `~/.mask/` | Local machine configuration, ownership and recovery state |
| `MASK_HOME/integration.json` | Machine-local readiness approvals |
| `MASK_HOME/integrations.json` | Ownership records for installed adapters |

Commit declarations and project context. Ignore generated links and `.mask/generated/`; prefer per-entry ignore rules when unrelated real skills share the directory. `--home PATH` overrides `MASK_HOME`, which otherwise defaults to `~/.mask`. Normal operation never requires editing internal state files.

## Update skills or the program

> [!IMPORTANT]
> A source update affects **every registered project and personal consumer**. Run it between active tasks; all links share one checkout, and running agents may cache instructions.

```sh
mask source status --json
mask source fetch --json
mask update --dry-run --json
mask update --expect-plan-hash RETURNED_HASH --json
```

`source fetch` refreshes Git objects and remote-tracking refs without activating content. The dry run performs no fetch and reports last-fetched state. `update` validates a frozen candidate against live consumer declarations, fast-forwards the source, and reconciles its consumers. Dirty, ahead, diverged, detached, unavailable or colliding inputs refuse instead of triggering a reset, stash, clean or push.

Additional repositories can be registered in an approved source catalog. First
preview `mask source migrate --dry-run --json`, then apply `mask source migrate
--json` to assign the existing source the `legacy` alias. This changes machine
configuration to v2 while preserving declarations, ownership and deployed links.
The preview exposes the full repository identity being approved. Existing v1
configuration remains supported; its historical basename check is replaced by
full URI matching after migration.

```sh
mask tap add community https://github.com/OWNER/REPOSITORY.git --dry-run --json
mask tap add community https://github.com/OWNER/REPOSITORY.git --json
mask source list --json
mask source show community --json
mask source fetch community --json
```

Adding a tap only registers its repository, ref and package layout. An explicit
fetch fills a separate owned bare cache; it does not deploy skills. HTTPS and SSH
are distinct approved identities. Git credentials remain in the existing Git
configuration; URLs containing credentials and redirects are refused. Tap removal
retains the cache and refuses references, including the legacy binding.

With a v2 catalog, `skill list` reports the fetched catalogs and `skill show
SOURCE/ID` selects an exact source. Duplicate bare names require qualification;
an unfetched source is reported explicitly. These queries read frozen Git objects.
`source inspect URL [--ref REF] [--path PATH]` inspects an already approved
repository and reports package coordinates, without deploying them. Its dry run
uses cached refs/objects and reports `resolution_required` when they are missing.
Root, flat and indexed nested layouts are supported. GitHub tree/blob URLs with
ambiguous branch/path splits return choices. Package metadata inspection is not
full payload validation. Use `mask skill validate SOURCE/ID --json` (or `--all`)
to validate exact cached payload bytes and logical Git modes without fetching or
checking out files. It rejects links, submodules, LFS pointers, nonportable or
colliding paths, and known host activation metadata. Limits are 64 MiB per file,
256 MiB per package, 10,000 tree entries, and depth 32. Plain frontmatter uses a
closed passive scalar subset; tool grants, hooks and dynamic shell preprocessing
refuse (including executable examples). Arbitrary package scripts
remain passive data; this is structural validation, not a malware safety claim.
Copy imports can now vendor one selected package into a new directory in an
approved authoring source. Fetch the upstream catalog first for an offline
preview, then apply its exact proposal:

```sh
mask source fetch community --json
mask skill import community --mode copy --into legacy --path skills/example --dry-run --json
mask skill import community --mode copy --into legacy --path skills/example --expect-plan-hash RETURNED_HASH --json
mask skill provenance legacy/example --json
```

An import preserves raw bytes and adjacent notices, writes a bounded provenance
record, and returns exact changed paths. It never commits, pushes, or edits the
Git index. Existing content—including an empty directory appearing concurrently—
refuses publication. Destination parents must already exist; an existing source
index must already map the selected ID. Package selection remains separate from
deployment. Multi-source consumer selections are still being implemented.

Provenance reports distinguish authoring observations, frozen tap objects,
recorded assertions, missing history, and independently rechecked upstream Git
facts. After editing imported content, preview `mask skill record-adaptation
legacy/example --note "Describe the adaptation" --dry-run --json`, then apply
with its returned plan hash. This records the observed changes without modifying
payload files or inventing earlier history. Windows records logical execute
modes; copying does not establish executable Git index bits for a later commit.

Managed source fetches stage refs before advancing the catalog cursor. They
enforce the configured timeout and bounded command output, and monitor object
storage against 256 MiB growth per fetch and a 1 GiB cache ceiling. Storage is
sampled every 50 ms and checked after fetch; it can overshoot between samples.
This is not a hard network transfer or disk quota. Refused acquisitions may
retain objects and a staging ref for inspection, but do not select the package.

`mask self update --json` updates only the running ManageAgentSkills checkout. It checks protocol/schema compatibility and returns `next_invocation_required`; the next command loads the new implementation. It does not update skills or reinstall the launcher. Local skill management remains available while the program checkout has authoring changes.

## Recover or stop managing a project

Inspect an interrupted operation with `mask recover --inspect --json`. After checking the recorded intent, choose explicit `--complete` or `--rollback`. Recovery preserves unexpected edits and never resets a Git checkout that has advanced. Git helpers and checkout filters remain trusted subprocesses; MASK is not a sandbox or an atomic deployment system.

`mask project unregister PATH --json` removes only unchanged owned links and preserves the declaration, context and source. `--keep-links` explicitly abandons ownership, including for an unavailable project. Exact existing declared links can be adopted with `link adopt`; consult the [CLI contract](docs/architecture/cli-contract.md) for its required preconditions.

If readiness adapters are installed, disable the owned adapters and revoke the
applicable approval when stopping automatic management. Unregistering alone does
not revoke approval. `workspace forget PATH --expect-identity ID` can retire a
removed Git worktree's registration after verifying its recorded identity and
absence from the original Git worktree list; it does not prune unavailable roots.

To remove the program, disable installed integrations and unregister the selected project and personal consumers first, then explicitly remove the verified owned launcher and program checkout while preserving source history and backups. There is no purge command. Source relocation likewise requires an explicit unregister/setup/register sequence; a new `--home PATH` can preserve the old machine state during setup.

## Development and reference

For a local CLI smoke scenario, run `python3 -B -m unittest tests.test_end_to_end.EndToEndTests.test_public_management_sequence` from this checkout. It uses disposable projects and local bare Git remotes. Run `python3 -B scripts/verify_documentation.py` for the RFC/issue structure gate; choose additional tests for the behavior being changed.

To create a single Markdown file for ChatGPT project sources or a code review:

```sh
python3 -B scripts/make_project_source_dumps.py
```

The dump is written to `artifacts/manage_agent_skills_project_source.md` (ignored
by Git). It includes current working-tree source, tests, schemas, documentation,
and portable `.mask/skill-config/` context, including new untracked text sources.
It skips links, local agent directories, other `.mask/` data, virtual environments,
caches, generated output, and binary file types. Selected text files must be UTF-8
without NUL bytes; invalid content reports an error before writing the dump.
This is a source-file filter, not a secret scanner or a Git-ignore filter.

Use `--output PATH` for another destination, `--stdout` to print the dump, or
`--root PATH` for another checkout. Relative output paths are resolved under the
selected root; the default root is the checkout containing the script, regardless
of the working directory. `--include-generated` adds build/output directories
while keeping links, caches, virtual environments, and local state excluded.
The selected output file is always excluded from its own dump.

`mask lock --project PATH --dry-run --json` previews an exact lock for a v2
selection. Approve and fetch the source explicitly first, then run `mask lock`
with the returned `--expect-plan-hash`. `--user` selects the personal declaration.
Locking uses cached objects only and never changes deployed skills. Existing locks
retain their resolution; `--refresh --skill SOURCE/ID` updates selected bindings.
Ref rewrites require explicit `--allow-ref-rebind`. V2 deployment currently returns
a typed unsupported error after checking for a missing or stale lock. See the
[selection/lock contract](docs/architecture/cli-contract.md#cached-selection-locks)
for canonical defaults, exact digests and the machine-local file-source limitation.

- [CLI contract and exit codes](docs/architecture/cli-contract.md)
- [JSON schemas](schemas/)
- [Contributing](CONTRIBUTING.md), [RFCs](docs/rfcs/README.md) and [issue board](docs/issues/README.md)
- [Current readiness acceptance and verification limits](docs/development/readiness-acceptance.md)
- [Local v0.1.0 readiness and implementation provenance](docs/releases/v0.1.0.md)

The September 2026 RFC pack is imported, with workspace readiness, integration,
recovery and legacy inventory slices implemented. Native Windows
readiness acceptance passed on ExampleWinHost after the recorded Windows fixes. The source
catalog supports explicit migration, taps, fetch, package validation, curated
copy imports and provenance. Cached v2 selection locks now record exact commits,
paths and payload digests. Exact artifact preparation is available through `source fetch --locked`;
deployment of those artifacts, profiles, bundles, fleet management
and full update-impact reports remain RFC work. Importing their specifications does not
make those features available. MASK has no daemon or publishing command.

Both named repositories consume the shared skills. Verified bootstrap copies
remain outside discovery roots in each
`.mask/bootstrap-retired/implement-rfc-2026-09-05`. Filesystem deployment and bounded
workflow invocation were verified; agent UI loading was not.
