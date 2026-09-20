# Installation reference

Program installation, the launcher and the first tap in detail, including the native Windows PowerShell example. The short [README](../../README.md) covers the everyday path.

## Requirements

- Python 3.11+ and Git. The runtime uses the Python standard library; there is no pip installation.
- A local clone of ManageAgentSkills. The launcher runs the program from that clone, and `mask update` fast-forwards it. You do not need an AgentSkills checkout: MASK fetches each approved tap into its own bare cache under `MASK_HOME/sources` (normally `~/.mask/sources`). Cloning and fetching use your existing Git access.
- Directory symlink support. Windows needs existing symlink privileges; MASK does not elevate or substitute junctions or copies.

> [!NOTE]
> Tap-only deployment and the workspace readiness and inventory commands are unreleased additions; the program version remains `0.2.0`. Tap-only deployment is not yet natively qualified. Readiness has native macOS and Windows evidence, including named Git hooks on Windows. Actual first-prompt host loading remains unverified. See the [current acceptance report](../development/readiness-acceptance.md). The [v0.1.0 report](../releases/v0.1.0.md) records earlier macOS and Windows checks, not acceptance of these additions. Linux remains best-effort.

## Install and approve a tap

### With the installer

```sh
curl -fsSL https://raw.githubusercontent.com/MikeMarcin/ManageAgentSkills/main/install.sh | sh
```

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/MikeMarcin/ManageAgentSkills/main/install.ps1 | iex"
```

[`install.sh`](../../install.sh) and [`install.ps1`](../../install.ps1) do exactly what the by-hand steps below do: check for Git and Python 3.11+, clone ManageAgentSkills (or fast-forward an existing clone, never discarding local work), and run `mask.py self install` to write the launcher. They run nothing as root or elevated, do not edit your shell profile or PATH (they print the line to add), and install neither Python nor Git. Running the installer again updates in place; afterwards `mask update` does the same from inside MASK.

| Variable | Default | Meaning |
|---|---|---|
| `MASK_INSTALL_DIR` | `${XDG_DATA_HOME:-~/.local/share}/mask`; `%LOCALAPPDATA%\mask\program` on Windows | Where the program clone lives. Keep it: the launcher runs MASK from there |
| `MASK_BIN_DIR` | `~/.local/bin`; `%LOCALAPPDATA%\mask\bin` on Windows | Where the `mask` launcher is written |
| `MASK_REPO` | `https://github.com/MikeMarcin/ManageAgentSkills.git` | The Git URL to clone, for a fork or an SSH URL |
| `MASK_PYTHON` | first of `python3`, `python` (`py -3`, `python` on Windows) that is 3.11+ | The interpreter the launcher will use |

The raw URLs are served only while the repository is public. With access to a private copy, fetch the script through your GitHub sign-in instead: `gh api repos/MikeMarcin/ManageAgentSkills/contents/install.sh -H 'Accept: application/vnd.github.raw' | sh`. Each script is a single function called on its last line, so a download that is cut short runs nothing. `install.sh` is exercised end to end against a local program repository by `tests.test_installer`; `install.ps1` has only been parse-checked, not run on Windows.

### By hand

On macOS or Linux, run the following from the directory that will hold the clone, using a supported `python3`:

```sh
git clone https://github.com/MikeMarcin/ManageAgentSkills.git
mkdir -p "$HOME/.local/bin"
python3 ManageAgentSkills/mask.py self install --bin-dir "$HOME/.local/bin"
"$HOME/.local/bin/mask" tap agentskills https://github.com/MikeMarcin/AgentSkills.git
"$HOME/.local/bin/mask" capabilities
"$HOME/.local/bin/mask" tap fetch
"$HOME/.local/bin/mask" skill list
```

MASK writes a launcher that records the selected interpreter and program clone. It leaves PATH unchanged. Use the absolute launcher path immediately, or add its directory to PATH yourself before using the shorter `mask` commands. An unrelated or edited existing launcher is preserved and causes a refusal.

`tap NAME URL` approves the repository under the name `agentskills`. When `MASK_HOME/config.json` and the state file are missing, it creates them, so this one command bootstraps the machine; it does not use the network. `capabilities` confirms the program, interpreter and supported commands. `search` reads only fetched taps: before any fetch it lists nothing and names the unfetched tap, so `tap fetch` fills the tap's cache first without deploying anything. You can skip both and run `mask install ID` in a project instead, which fetches the tap on demand.

On Windows, use PowerShell with a known supported Python installation. For example, if Python 3.14 is installed and the clone goes under `C:\work`:

```powershell
git clone https://github.com/MikeMarcin/ManageAgentSkills.git 'C:\work\ManageAgentSkills'
$maskBin = Join-Path $env:LOCALAPPDATA 'Programs\MASK'
New-Item -ItemType Directory -Force -Path $maskBin | Out-Null
py -3.14 'C:\work\ManageAgentSkills\mask.py' self install --bin-dir $maskBin
& "$maskBin\mask.cmd" tap agentskills https://github.com/MikeMarcin/AgentSkills.git
& "$maskBin\mask.cmd" tap fetch
& "$maskBin\mask.cmd" skill list
```

The direct entrypoint remains available if the launcher is missing: `python3 /absolute/path/to/ManageAgentSkills/mask.py ...` (or the corresponding supported Windows interpreter). `self status` reports the program, interpreter and launcher discovery. Approving the first tap initializes the machine configuration; registering a checkout is a separate operation.
