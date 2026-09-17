# Installation reference

Program installation, the launcher and the first tap in detail, including the native Windows PowerShell example. The short [README](../../README.md) covers the everyday path.

## Requirements

- Python 3.11+ and Git. The runtime uses the Python standard library; there is no pip installation.
- A local clone of ManageAgentSkills. The launcher runs the program from that clone, and `mask update` fast-forwards it. You do not need an AgentSkills checkout: MASK fetches each approved tap into its own bare cache under `MASK_HOME/sources` (normally `~/.mask/sources`). Cloning and fetching use your existing Git access.
- Directory symlink support. Windows needs existing symlink privileges; MASK does not elevate or substitute junctions or copies.

> [!NOTE]
> Tap-only deployment and the workspace readiness and inventory commands are unreleased additions; the program version remains `0.2.0`. Tap-only deployment is not yet natively qualified. Readiness has native macOS and Windows evidence, including named Git hooks on Windows. Actual first-prompt host loading remains unverified. See the [current acceptance report](../development/readiness-acceptance.md). The [v0.1.0 report](../releases/v0.1.0.md) records earlier macOS and Windows checks, not acceptance of these additions. Linux remains best-effort.

## Install and approve a tap

On macOS or Linux, run the following from the directory that will hold the clone, using a supported `python3`:

```sh
git clone https://github.com/MikeMarcin/ManageAgentSkills.git
mkdir -p "$HOME/.local/bin"
python3 ManageAgentSkills/mask.py self install --bin-dir "$HOME/.local/bin"
"$HOME/.local/bin/mask" tap add agentskills https://github.com/MikeMarcin/AgentSkills.git
"$HOME/.local/bin/mask" capabilities
"$HOME/.local/bin/mask" source fetch
"$HOME/.local/bin/mask" skill list
```

MASK writes a launcher that records the selected interpreter and program clone. It leaves PATH unchanged. Use the absolute launcher path immediately, or add its directory to PATH yourself before using the shorter `mask` commands. An unrelated or edited existing launcher is preserved and causes a refusal.

`tap add` approves the repository under the name `agentskills`. When `MASK_HOME/config.json` and the state file are missing, it creates them, so this one command bootstraps the machine; it does not use the network. `capabilities` confirms the program, interpreter and supported commands. `skill list` reads only fetched taps: before any fetch it lists nothing and names the unfetched tap, so `source fetch` fills the tap's cache first without deploying anything. You can skip both and run `mask install ID` in a project instead, which fetches the tap on demand.

On Windows, use PowerShell with a known supported Python installation. For example, if Python 3.14 is installed and the clone goes under `C:\work`:

```powershell
git clone https://github.com/MikeMarcin/ManageAgentSkills.git 'C:\work\ManageAgentSkills'
$maskBin = Join-Path $env:LOCALAPPDATA 'Programs\MASK'
New-Item -ItemType Directory -Force -Path $maskBin | Out-Null
py -3.14 'C:\work\ManageAgentSkills\mask.py' self install --bin-dir $maskBin
& "$maskBin\mask.cmd" tap add agentskills https://github.com/MikeMarcin/AgentSkills.git
& "$maskBin\mask.cmd" source fetch
& "$maskBin\mask.cmd" skill list
```

The direct entrypoint remains available if the launcher is missing: `python3 /absolute/path/to/ManageAgentSkills/mask.py ...` (or the corresponding supported Windows interpreter). `self status` reports the program, interpreter and launcher discovery. Installing the launcher and approving a tap are separate operations; `mask init` creates an empty tap catalog if you want the machine configuration before approving any tap.

A machine where MASK still links skills from a local AgentSkills checkout needs no new bootstrap: preview `mask doctor --migrate --dry-run` and follow [Migrating from a live checkout](migration-and-pins.md).
