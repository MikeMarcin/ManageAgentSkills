![MASK — Declare. Preview. Deploy.](docs/assets/readme-header.svg)

**Agent skills for Claude Code and Codex, installed from Git and pinned to exact commits.**

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
"$HOME/.local/bin/mask" tap add agentskills https://github.com/MikeMarcin/AgentSkills.git
```

Keep the clone where it is: the launcher runs MASK from it. More in the [installation guide](docs/guides/installation.md), including private repositories and Windows.

</details>

## In your project

```sh
mask install implement-rfc
mask list
mask ensure
```

`install` pins the skill and links it for Claude Code and Codex. `ensure` checks that everything a skill needs is in place, and asks before it runs any setup a skill ships.

## Make everything work

```sh
mask ensure --all --repair
```

Fixes every project and your personal skills in one go, without prompts. Files it replaces are backed up under `~/.mask/backups/` first. Add `--dry-run` to look before you leap.

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

- `update` and `upgrade` work like `brew` and `apt`: `update` fetches what is new and changes nothing; `upgrade` moves your skills to it.
- `--dry-run` previews any command. `--json` gives scripts structured output and never prompts.
- The same tap works over HTTPS or SSH, so one committed project file suits every machine. MASK uses whichever way you already sign in.
- `mask COMMAND --help` has examples for every command.

## Learn more

- [Installation](docs/guides/installation.md) · [Sources, taps and upgrades](docs/guides/sources-and-updates.md) · [Readiness and setup](docs/guides/readiness-and-integrations.md)
- [Project files and layout](docs/guides/declarations.md) · [Recovery and uninstalling](docs/guides/recovery.md) · [Pins, dev links and per-skill agents](docs/guides/pins-and-agents.md)
- [CLI contract and exit codes](docs/architecture/cli-contract.md) · [Development](docs/guides/development.md) · [Contributing](CONTRIBUTING.md) · [RFCs](docs/rfcs/README.md)

MASK is pre-release (`0.2.0`). It needs no daemon, account or subscription. What has been verified on which platform is recorded in the [acceptance records](docs/development/readiness-acceptance.md).
