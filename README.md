![MASK — Declare. Preview. Deploy.](docs/assets/readme-header.svg)

Manage your agent skills in a project or your personal environment.

MASK installs skills from Git repositories you approve as taps, such as [AgentSkills](https://github.com/MikeMarcin/AgentSkills). It fetches each tap into its own cache, pins every selection to an exact commit and links that stored copy into the directories Claude Code and Codex read. Projects keep their selection in versioned `.mask.json` and `.mask.lock.json` files; personal selections live in `MASK_HOME/user.json` and `MASK_HOME/user.lock.json`.

## Install once

You need Python 3.11+, Git and existing directory-symlink support. You do not need an
AgentSkills checkout. MASK does not change privileges, edit your shell profile or install
Python or Git.

The installer clones MASK into `~/.local/share/mask`, writes the `mask` launcher into
`~/.local/bin`, and updates in place when you run it again:

```sh
curl -fsSL https://raw.githubusercontent.com/MikeMarcin/ManageAgentSkills/main/install.sh | sh
```

On Windows, in PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/MikeMarcin/ManageAgentSkills/main/install.ps1 | iex"
```

Those URLs are served only while this repository is public. With access to a private copy,
`gh api repos/MikeMarcin/ManageAgentSkills/contents/install.sh -H 'Accept: application/vnd.github.raw' | sh`
does the same through your GitHub sign-in. `MASK_INSTALL_DIR`, `MASK_BIN_DIR`, `MASK_REPO` and `MASK_PYTHON`
override the defaults; read the script first if you prefer, it is short.

Or do the same by hand. From the directory that will hold the clone, on macOS or Linux:

```sh
git clone https://github.com/MikeMarcin/ManageAgentSkills.git
mkdir -p "$HOME/.local/bin"
python3 ManageAgentSkills/mask.py self install --bin-dir "$HOME/.local/bin"
"$HOME/.local/bin/mask" tap add agentskills https://github.com/MikeMarcin/AgentSkills.git
```

The launcher runs MASK from that clone, so keep the clone where it is. Add the bin
directory to PATH, or keep using the printed absolute launcher path. `self install`
writes only into an existing parent directory. `tap add` approves the repository
and creates the machine configuration without fetching anything; `install`
fetches the tap when it needs it, using your existing Git authentication. Windows
uses the same Python entrypoint and a `mask.cmd` launcher; the
[installation reference](docs/guides/installation.md) gives the native PowerShell
example.

If MASK on this machine still links skills from a local AgentSkills checkout, other
commands refuse with `migration.required` until you migrate. Preview the
conversion with `mask doctor --migrate --dry-run` and follow
[Migrating from a live checkout](docs/guides/migration-and-pins.md).

## In your project

```sh
mask install implement-rfc
mask list
mask ensure
```

`install` adds the skill without removing your other selections, fetches its tap
as needed, pins the exact commit in `.mask.lock.json`, creates the declaration and
registration when they are missing, and links the skill for every selected agent
in the same command. Run it from the project or use `--project PATH`.
Packages that declare native agent roles have them copied exactly with the links;
roles you keep checked in are used as they are. When a declared role or consumer
input is still missing, `install` keeps the links and exits 4 naming it, the same
verdict `ensure`, `upgrade`, `doctor --check` and `launch` share. `install` needs no confirmation. `ensure` asks before it changes anything in
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
| Update MASK itself and fetch your taps | `mask update` |
| Upgrade every registered project and personal scope | `mask upgrade` |
| Upgrade only this project | `mask upgrade --project .` |
| Upgrade only personal skills | `mask upgrade --user` |

The two commands mean what they mean in `brew` and `apt`. `mask update` refreshes what
is available: it fast-forwards the MASK program clone and fetches every approved tap,
and changes no project. `mask upgrade` moves your skills to it.

`mask upgrade` fetches each tap your selections use once, resolves every registered
project and your personal scope against the branch or tag each selection follows,
shows each lock change and applies them together. `--project DIR` or `--user`
limits it to one scope; `--all` names the default explicitly. A tap that cannot be
fetched blocks only the scopes that use it: the others still upgrade, and the
command exits 4 (`upgrade.incomplete`) naming the blocked roots. When a tag moved or
a branch is no longer a fast-forward of the locked commit, upgrade refuses until you
review it and pass `--allow-ref-rebind`. `mask source fetch NAME` fetches one tap
without deploying. Run upgrades
between active tasks: a running agent may cache instructions, and a changed file
does not prove a host reloaded it.

A tap is the same tap over HTTPS or SSH: on GitHub, GitLab, Bitbucket and Codeberg, project files record one
identity (`https://github.com/O/R.git`), and each machine reaches it the way it already signs in, following the
project's `origin`, what worked last, then `gh`. `mask tap transport NAME URL` pins one on this machine only. See
[Sources and updates](docs/guides/sources-and-updates.md#one-tap-however-each-machine-signs-in).

Use `--dry-run` to preview local or cached changes without fetching or applying.
Use `--json` for structured machine output; without it MASK prints human text and
never asks a question when stdin or stdout is not a terminal. Declining a required
confirmation leaves an explicit incomplete result, not a false success. Colliding
or modified files are preserved and reported with the next safe action.
If setup is blocked by existing agent role files, repeating `ensure` cannot
replace them. The error lists their project and paths; follow the
[role-file recovery guide](docs/guides/recovery.md#when-ensure-preserves-existing-role-files)
to restore a matching lock or review the files. `mask ensure --help` and
`mask upgrade --help` explain setup, scope, and examples.

## Reference

- [Installation reference](docs/guides/installation.md): requirements, launcher, the first tap and Windows PowerShell.
- [Declarations and file layout](docs/guides/declarations.md): explicit `project`/`user` commands, plan hashes, what belongs where.
- [Readiness and integrations](docs/guides/readiness-and-integrations.md): approval, `launch`, Git/host startup adapters, inventory.
- [Sources and updates](docs/guides/sources-and-updates.md): taps, fetching updates, package validation, imports, provenance, `update` and `upgrade`.
- [Migrating from a live checkout](docs/guides/migration-and-pins.md): `doctor --migrate`, the old-command table, per-skill agents and local compatibility.
- [Recovery](docs/guides/recovery.md): interrupted operations, unregistering and removing the program.
- [Development](docs/guides/development.md), [CLI contract and exit codes](docs/architecture/cli-contract.md), [Contributing](CONTRIBUTING.md), [RFCs](docs/rfcs/README.md) and the [issue board](docs/issues/README.md).

These are advanced operations, not prerequisites for adding another skill to a
working installation.

> [!NOTE]
> Tap-only deployment, the task commands, human output, in-process confirmation
> and declarative native roles are unreleased additions; the program version
> remains `0.2.0`. No daemon, fleet enrollment, provider account or
> package-manager subscription is required. Declarations are versioned; machine
> ownership and approvals are local. Native macOS and Windows evidence exists for
> the everyday commands as they worked before tap-only deployment, whose native
> qualification is still open; see the
> [current acceptance records](docs/development/readiness-acceptance.md) and the
> [corrective baseline](docs/development/corrective-baseline.md) for exactly which
> native and host-loading behaviors have been verified. Linux remains best-effort.
