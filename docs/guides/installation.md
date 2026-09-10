# Installation reference

Program installation, the launcher and source selection in detail, including the native Windows PowerShell example. The short [README](../../README.md) covers the everyday path.

## Requirements

- Python 3.11+ and Git. The runtime uses the Python standard library; there is no pip installation.
- Local checkouts of ManageAgentSkills and AgentSkills. Cloning and remote updates use your existing Git access.
- Directory symlink support. Windows needs existing symlink privileges; MASK does not elevate or substitute junctions or copies.

> [!NOTE]
> The new workspace readiness and inventory commands are unreleased additions; the program version remains `0.2.0`. Readiness has native macOS and Windows evidence, including named Git hooks on Windows. Actual first-prompt host loading remains unverified. See the [current acceptance report](../development/readiness-acceptance.md). The [v0.1.0 report](../releases/v0.1.0.md) records earlier macOS and Windows checks, not acceptance of these additions. Linux remains best-effort.

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
py -3.14 'C:\work\ManageAgentSkills\mask.py' self install --bin-dir $maskBin
& "$maskBin\mask.cmd" init --source 'C:\work\AgentSkills'
& "$maskBin\mask.cmd" skill list
```

The direct entrypoint remains available if the launcher is missing: `python3 /absolute/path/to/ManageAgentSkills/mask.py ...` (or the corresponding supported Windows interpreter). `self status --json` reports the program, interpreter and launcher discovery. Installing the launcher and selecting the skill source are separate operations.
