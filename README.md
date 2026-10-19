![MASK — Declare. Preview. Deploy.](docs/assets/readme-header.svg)

**Agent skills for Claude Code and Codex, installed from Git and locked to exact commits.**

Approve a Git repository of skills (a *tap*, such as [AgentSkills](https://github.com/MikeMarcin/AgentSkills)), then `mask install` what you want. Each skill is locked to a commit in `.mask.lock.json`, so a teammate or another machine gets exactly the same thing.

## Install once

```sh
curl -fsSL https://raw.githubusercontent.com/MikeMarcin/ManageAgentSkills/main/install.sh | sh
```

```powershell
$install = (Invoke-WebRequest -Uri 'https://raw.githubusercontent.com/MikeMarcin/ManageAgentSkills/main/install.ps1').Content
Invoke-Expression $install
```

Needs Python 3.11+, Git and directory symlink support. On Windows, enable Developer
Mode or use an account with symlink privileges. Nothing runs as root and your shell
profile is left alone. Follow the installer's PATH instructions, then approve the
companion skill source once:

```sh
mask tap agentskills https://github.com/MikeMarcin/AgentSkills.git
```

Run the same installer again to cross a reviewed MASK schema/protocol update;
ordinary compatible updates can use `mask update`.

<details>
<summary>Prefer to do it by hand?</summary>

```sh
git clone https://github.com/MikeMarcin/ManageAgentSkills.git
mkdir -p "$HOME/.local/bin"
python3 ManageAgentSkills/mask.py self install --bin-dir "$HOME/.local/bin"
"$HOME/.local/bin/mask" tap agentskills https://github.com/MikeMarcin/AgentSkills.git
```

Keep the clone where it is: the launcher runs MASK from it. On Windows, `self install` writes `mask.cmd` for PowerShell and cmd, and an extensionless `mask` for Git Bash. More in the [installation guide](docs/guides/installation.md), including private repositories and Windows.

</details>

## In your project

```sh
mask install code-simplifier
mask list
mask upgrade
```

`install` locks the selected version and links it for Claude Code and Codex. `upgrade` updates it and puts its declared prerequisites in place, asking before it runs any setup a skill ships. It also reconciles prerequisites when the version is already current. Use `pin` to hold a version across upgrades; its links and setup still receive repairs.

Commit `.mask.json` and `.mask.lock.json` so other checkouts can restore the same
selections and versions. To use `implement-rfc`, first configure its
[consumer workflow context](https://github.com/MikeMarcin/AgentSkills#configure-implement-rfc).

## Make everything work

```sh
mask upgrade --all
```

Updates every registered checkout and your personal skills, including installed bundle definitions and required
setup. Bare `mask upgrade` affects only the checkout you are working in.

For a fresh clone or worktree, run `mask register`. It restores the declared
locked versions and completes setup. Use `mask repair` to restore an existing
checkout without upgrading versions.

## Everyday commands

| Task | Command |
|---|---|
| Add a skill here | `mask install ID` |
| Add a personal skill | `mask install ID --user` |
| Remove a skill here | `mask uninstall ID` |
| Show this checkout's skills | `mask list` |
| Show personal skills | `mask list --user` |
| Inspect this checkout's readiness | `mask status` |
| Inspect a named bundle | `mask bundle show TAP/BUNDLE` |
| Install a named bundle here | `mask bundle install TAP/BUNDLE` |
| Review bundle membership and member versions | `mask bundle upgrade TAP/BUNDLE --dry-run` |
| Uninstall a bundle contribution here | `mask bundle uninstall TAP/BUNDLE` |
| Update MASK itself and fetch your taps | `mask update` |
| Upgrade this checkout | `mask upgrade` |
| Upgrade and commit changed project controls | `mask upgrade --commit` |
| Upgrade personal skills | `mask upgrade --user` |
| Upgrade every registered checkout and personal skills | `mask upgrade --all` |
| Hold a skill at its installed version | `mask pin ID` |
| Release a version hold | `mask unpin ID` |
| Register and prepare this checkout | `mask register` |
| Restore pinned setup, or review an interrupted setup | `mask repair` |
| Preview unused storage and backups | `mask cleanup --dry-run` |

`register`, `install`, `uninstall`, `list`, `pin`, `unpin`, `upgrade`, `repair`, and
`status` default to the **current checkout**. Add `--user` for personal skills.
ID names a skill and TAP/BUNDLE a named bundle, such as `agentskills/rfc`.
`upgrade`, `repair`, `status`, and `list` accept `--all` for every registered
checkout plus personal skills. On `pin` and `unpin`, `--all` replaces ID and means
all skills in the selected checkout; combine it with `--user` for personal skills.
Pinned skills still receive link repairs and required setup during upgrade.

An interrupted setup can block changes across MASK. `repair` first names that
operation's location and offers to finish its validated files or roll back the
attempt, without rerunning setup. This recovery ends the command; retry your
original command afterward. Advanced `mask recover` inspects the pending operation
without changing anything. See the [recovery guide](docs/guides/recovery.md).

Long tasks update one terminal line with their current phase and setup location.
Reviews summarize shared upgrades, setup and commits; blocked projects, existing
control edits included in commits and file replacements stay explicit. Enter `d`
at the approval prompt for full locations, versions and generated files. Results
summarize completed work and name failures and unstarted setup. Terminal output
uses light color (`NO_COLOR=1` disables it). Pipes stay plain, and `--json` returns
one structured result without progress messages. For full preview details in a
pipe, combine `--dry-run --json`.

`tap` lists shared sources; `tap NAME URL` adds one; `untap NAME` removes one.
`search` and `info ID` browse their catalogs. These commands, `update`, and
`cleanup` are independent of your working directory.

Named bundles expand a fetched source definition into explicit selections and exact
locks. The canonical `agentskills/rfc` bundle contains author-rfc, grill-rfc, grill-me
and implement-rfc. Configure implement-rfc's consumer context before installing it;
the installation review includes its required setup. Use `mask tap fetch agentskills`
before browsing or previewing. Install adds to existing selections, and later definition
changes and newer unheld members are reviewed together by `bundle upgrade`.
Ordinary `upgrade`, including `--all`, includes installed bundles too. Bundle uninstall removes its local
contribution while preserving other selections and held or locally edited members. See [bundle contributions](docs/guides/declarations.md#named-bundles).

- `update` refreshes MASK and the tap catalogs; `upgrade` changes selected skill versions and makes them ready. Install/upgrade refresh automatically when needed. `--no-update` skips that preliminary refresh; `--offline` forbids network access altogether.
- Uncommitted edits in the MASK clone stay in place through `update` unless the update changes the same files. Then MASK names those files and holds; `mask update --stash` moves only them into a new `git stash`, updates, and prints the stash's id. MASK never pops or applies that stash.
- `upgrade --commit` creates one local commit per successful project after readiness, including existing changes to `.mask.json` and `.mask.lock.json`. It preserves unrelated staging and uses normal Git hooks and signing. Under `--all`, personal skills upgrade normally without a commit. `--user --commit` is invalid. Commit failures preserve applied upgrades; no push occurs.
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

## License

Original code and documentation are licensed under the [MIT License](LICENSE),
adopted by the owner on 2026-10-14. Dependencies and skills supplied by approved
taps retain their own licenses and provenance; MASK's license does not grant
rights to their content. The companion AgentSkills repository documents its
[original contributions and third-party notices](https://github.com/MikeMarcin/AgentSkills/blob/main/docs/development/skill-provenance.md).
