![MASK — Declare. Preview. Deploy.](docs/assets/readme-header.svg)

Manage your agent skills in a project or your personal environment.

MASK links skills from one local [AgentSkills](https://github.com/MikeMarcin/AgentSkills) checkout into the directories Claude Code and Codex read. Projects keep their selection in a versioned `.mask.json`; personal selections live in `MASK_HOME/user.json`.

## Install once

You need Python 3.11+, Git, local ManageAgentSkills and AgentSkills checkouts, and
existing directory-symlink support. MASK does not change privileges or install
Python or Git. From the checkouts' parent directory on macOS or Linux:

```sh
mkdir -p "$HOME/.local/bin"
python3 ManageAgentSkills/mask.py self install --bin-dir "$HOME/.local/bin"
"$HOME/.local/bin/mask" init --source "$PWD/AgentSkills"
```

Add that bin directory to PATH, or keep using the printed absolute launcher path.
`self install` writes only into an existing parent directory. Windows uses the
same Python entrypoint and a `mask.cmd` launcher; the
[installation reference](docs/guides/installation.md) gives the native PowerShell
example. Installing the program and selecting a skill source are separate steps.
Existing checkouts and Git authentication are reused.

## In your project

```sh
mask install implement-rfc
mask list
mask ensure
```

`install` adds the skill without removing your other selections, creates the
declaration and registration when they are missing, and links the skill for every
selected agent in the same command. Run it from the project or use `--project PATH`.
Packages that declare native agent roles have them copied exactly with the links;
roles you keep checked in are used as they are. When a declared role or consumer
input is still missing, `install` keeps the links and exits 4 naming it, the same
verdict `ensure`, `update`, `doctor --check` and `launch` share. `install` needs no confirmation. `ensure` asks before it changes anything in
an unapproved project (each invocation; `mask integration approve` in the
[readiness guide](docs/guides/readiness-and-integrations.md) makes that automatic)
and reports what is still missing: required consumer facts (for
`implement-rfc`, `.mask/skill-config/implement-rfc/`) are named, never copied from
another project. When a package declares Python setup for a generated role and no
checked-in lock vouches for it, a manual `ensure` in a terminal shows exactly what
would run (source, content fingerprint, interpreter, script, target; not sandboxed)
and asks `Run this setup? [y/N]`. Yes runs it, validates the staged outputs and
publishes them in the same command; no leaves the links in place and the result
incomplete. Checks, dry runs and events never run package code. JSON and
redirected streams never prompt, and `--yes` alone never authorizes setup.
Automation can pass the previewed `--expect-plan-hash` together with
`--allow-setup SOURCE/ID:ACTION`, or explicitly choose the repair mode below.

## Make everything work

```sh
mask ensure --all --repair
```

This explicitly authorizes setup for the skills already selected in every
registered project and your personal scope. It runs without prompts, backs up
existing role files before replacing them, and checks each scope again. `--yolo`
is an alias for `--repair`. Use `--project DIR` or `--user` instead of `--all` to
repair just one scope; add `--dry-run` to preview without changing files or
running setup.

Backups and a manifest of their original paths remain under
`MASK_HOME/backups/` (normally `~/.mask/backups/`). One broken project does not
stop the others; an interrupted transaction requiring recovery does. The result
names any missing consumer inputs, unsafe paths, unavailable sources or other
conditions it cannot fix. Repair does not invent project configuration or grant
persistent startup approval. Restart active agents to load changed roles.

## Everyday commands

| Task | Command |
|---|---|
| Add a skill here | `mask install ID` |
| Add a personal skill | `mask install ID --user` |
| Show this project's skills | `mask list` |
| Show personal skills | `mask list --user` |
| Check or reconcile declared setup | `mask ensure` |
| Repair every registered project and personal scope | `mask ensure --all --repair` |
| Remove a selection here | `mask remove ID` |
| Update the shared skill source | `mask update` |
| Update this pinned project | `mask update --project .` |
| Update personal pinned skills | `mask update --user` |
| Update MASK itself | `mask self update` |

Updates explain the affected scopes before applying. A shared live source affects
all of its registered consumers; pinned selections update independently. Run
updates between active tasks: a running agent may cache instructions, and a
changed file does not prove a host reloaded it.

Use `--dry-run` to preview local or cached changes without fetching or applying.
Use `--json` for structured machine output; without it MASK prints human text and
never asks a question when stdin or stdout is not a terminal. Declining a required
confirmation leaves an explicit incomplete result, not a false success. Colliding
or modified files are preserved and reported with the next safe action.
If setup is blocked by existing agent role files, repeating `ensure` cannot
replace them. The error lists their project and paths; follow the
[role-file recovery guide](docs/guides/recovery.md#when-ensure-preserves-existing-role-files)
to restore a matching lock or review the files. `mask ensure --help` and
`mask update --help` explain setup, scope, and examples.

## Reference

- [Installation reference](docs/guides/installation.md): requirements, launcher and Windows PowerShell.
- [Declarations and file layout](docs/guides/declarations.md): explicit `project`/`user` commands, plan hashes, what belongs where.
- [Readiness and integrations](docs/guides/readiness-and-integrations.md): approval, `launch`, Git/host startup adapters, inventory.
- [Sources and updates](docs/guides/sources-and-updates.md): taps, fetches, package validation, imports, provenance, `self update`.
- [Migration and pins](docs/guides/migration-and-pins.md): moving legacy consumers to exact pins, per-skill agents, compatibility policy.
- [Recovery](docs/guides/recovery.md): interrupted operations, unregistering and removing the program.
- [Development](docs/guides/development.md), [CLI contract and exit codes](docs/architecture/cli-contract.md), [Contributing](CONTRIBUTING.md), [RFCs](docs/rfcs/README.md) and the [issue board](docs/issues/README.md).

These are advanced operations, not prerequisites for adding another skill to a
working installation.

> [!NOTE]
> The task commands, human output, in-process confirmation and declarative native
> roles are unreleased additions; the program version remains `0.2.0`. No daemon,
> fleet enrollment, provider account or package-manager subscription is required.
> Declarations are versioned; machine ownership and approvals are local. Native
> macOS and Windows evidence exists for the everyday commands; see the
> [current acceptance records](docs/development/readiness-acceptance.md) and the
> [corrective baseline](docs/development/corrective-baseline.md) for exactly which
> native and host-loading behaviors have been verified. Linux remains best-effort.
