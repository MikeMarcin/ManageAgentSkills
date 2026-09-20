![MASK — Declare. Preview. Deploy.](docs/assets/readme-header.svg)

**Agent skills for Claude Code and Codex, installed from Git and locked to exact commits.**

Approve a Git repository of skills (a *tap*, such as [AgentSkills](https://github.com/MikeMarcin/AgentSkills)), then `mask install` what you want. Each skill is locked to a commit in `.mask.lock.json`, so a teammate or another machine gets exactly the same thing.

## Install once

```sh
curl -fsSL https://raw.githubusercontent.com/MikeMarcin/ManageAgentSkills/main/install.sh | sh
```

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/MikeMarcin/ManageAgentSkills/main/install.ps1 | iex"
```

Needs Python 3.11+ and Git. Nothing runs as root and your shell profile is left alone. Run it again to update.

<details>
<summary>Prefer to do it by hand?</summary>

```sh
git clone https://github.com/MikeMarcin/ManageAgentSkills.git
mkdir -p "$HOME/.local/bin"
python3 ManageAgentSkills/mask.py self install --bin-dir "$HOME/.local/bin"
"$HOME/.local/bin/mask" tap agentskills https://github.com/MikeMarcin/AgentSkills.git
```

Keep the clone where it is: the launcher runs MASK from it. More in the [installation guide](docs/guides/installation.md), including private repositories and Windows.

</details>

## In your project

```sh
mask install implement-rfc
mask list
mask upgrade
```

`install` locks the selected version and links it for Claude Code and Codex. `upgrade` updates it and puts its declared prerequisites in place, asking before it runs any setup a skill ships. It also reconciles prerequisites when the version is already current. Use `pin` to hold a version across upgrades; its links and setup still receive repairs.

## Make everything work

```sh
mask upgrade --all
```

Updates every registered checkout and your personal skills, including required
setup. Bare `mask upgrade` affects only the checkout you are working in.

For a fresh clone or worktree, run `mask register`. It restores the declared
locked versions and completes setup. Use `mask repair` to restore an existing
checkout without upgrading versions.

## Everyday commands

| Task | Command |
|---|---|
| Add a skill here | `mask install ID` |
| Add a personal skill | `mask install ID --user` |
| Show this checkout's skills | `mask list` |
| Show personal skills | `mask list --user` |
| Register and prepare this checkout | `mask register` |
| Restore this checkout's pinned setup | `mask repair` |
| Remove a skill here | `mask uninstall ID` |
| Hold a skill at its installed version | `mask pin ID` |
| Release a version hold | `mask unpin ID` |
| Inspect this checkout's readiness | `mask status` |
| Update MASK itself and fetch your taps | `mask update` |
| Upgrade every registered checkout and personal skills | `mask upgrade --all` |
| Upgrade this checkout | `mask upgrade` |
| Upgrade personal skills | `mask upgrade --user` |
| Preview unused storage and backups | `mask cleanup --dry-run` |

`register`, `install`, `uninstall`, `list`, `pin`, `unpin`, `upgrade`, `repair`, and
`status` default to the **current checkout**. Add `--user` for personal skills.
`upgrade`, `repair`, `status`, and `list` accept `--all` for every registered
checkout plus personal skills. On `pin` and `unpin`, `--all` replaces ID and means
all skills in the selected checkout; combine it with `--user` for personal skills.
Pinned skills still receive link repairs and required setup during upgrade.

Long tasks show their current phase and setup location while they work. Reviews
group changes by location; setup and file replacements remain explicit. Terminal
output uses light color (`NO_COLOR=1` disables it). Pipes stay plain, and `--json`
returns one structured result without progress messages.

`tap` lists shared sources; `tap NAME URL` adds one; `untap NAME` removes one.
`search` and `info ID` browse their catalogs. These commands, `update`, and
`cleanup` are independent of your working directory.

- `update` refreshes MASK and the tap catalogs; `upgrade` changes selected skill versions and makes them ready. Install/upgrade refresh automatically when needed. `--no-update` skips that preliminary refresh; `--offline` forbids network access altogether.
- `--dry-run` previews without fetching, writing or running setup. `--json` gives scripts structured output and never prompts.
- Setup scripts and replacement of edited native role files share one review before any consumer changes. Automation approves the exact preview with `--approve-plan HASH`. Replaced files are backed up.
- `cleanup` deletes verified unused storage and disposable backups only when explicitly invoked and reviewed. It preserves referenced versions, active locks, pending recovery and unknown content.
- The same tap works over HTTPS or SSH, so one committed project file suits every machine. MASK uses whichever way you already sign in.
- `mask COMMAND --help` has examples. Bare `mask` shows this checkout's status.

## Learn more

- [Installation](docs/guides/installation.md) · [Sources, taps and upgrades](docs/guides/sources-and-updates.md) · [Readiness and setup](docs/guides/readiness-and-integrations.md)
- [Project files and layout](docs/guides/declarations.md) · [Recovery and uninstalling](docs/guides/recovery.md) · [Pins, dev links and per-skill agents](docs/guides/pins-and-agents.md)
- [CLI contract and exit codes](docs/architecture/cli-contract.md) · [Development](docs/guides/development.md) · [Contributing](CONTRIBUTING.md) · [RFCs](docs/rfcs/README.md)

MASK is pre-release (`0.3.0`). It needs no daemon, account or subscription. What has been verified on which platform is recorded in the [acceptance records](docs/development/readiness-acceptance.md).
