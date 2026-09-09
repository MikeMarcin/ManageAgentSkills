# MASK

Manage your agent skills in a project or your personal environment.

> Proposed replacement README specimen. Remove this notice only after the
> examples below pass against the implemented CLI. Advanced reference links are
> repository links for the eventual live README, not files supplied here.

## Install once

You need Python 3.11+, Git, a local ManageAgentSkills checkout, a local AgentSkills
checkout, and existing directory-symlink support. MASK does not change privileges
or install Python/Git. From their parent directory on macOS:

```sh
python3 ManageAgentSkills/mask.py self install --bin-dir "$HOME/.local/bin"
"$HOME/.local/bin/mask" init --source "$PWD/AgentSkills"
```

Add that bin directory to PATH, or keep using the printed absolute launcher path.
Windows uses the same Python entrypoint and `mask.cmd` launcher; the installation
reference gives a native PowerShell example. Installing the program is separate
from selecting a skill source. Existing checkouts and authentication are reused.

## In your project

```sh
mask install implement-rfc
mask list
mask ensure
```

Install adds the skill without removing your other selections and makes the
project ready. Run it from the project or use `--project PATH`. Required consumer
facts are requested/reported rather than copied from another project. Native
roles can be supplied as checked-in files. When additional setup code really is
needed, MASK asks before running it and verifies the result in the same command.

## Everyday commands

| Task | Command |
|---|---|
| Add a skill here | `mask install ID` |
| Add a personal skill | `mask install ID --user` |
| Show this project's skills | `mask list` |
| Check/reconcile declared setup | `mask ensure` |
| Remove a selection here | `mask remove ID` |
| Update shared legacy skills | `mask update` |
| Update this pinned project | `mask update --project .` |
| Update personal pinned skills | `mask update --user` |
| Update MASK itself | `mask self update` |

Updates explain the affected scopes before applying. A shared live source affects
all of its registered consumers; pinned selections can update independently.
Changes do not prove an already-running agent reloaded its instructions. Update
between active tasks when role/instruction changes affect ongoing work.

Use `--dry-run` to preview local/cached changes without fetching or applying.
Use `--json` for structured machine output. Without it, MASK prints human text.
Declining required setup leaves an explicit incomplete result, not a false success.
Colliding or modified files are preserved and accompanied by the next safe action.

## Reference

See the CLI reference for exact automation/plan guards, the source guide for taps
and provenance, the migration guide for legacy-to-pinned conversion, and the
recovery guide for interrupted operations. These are advanced operations, not
prerequisites for adding another skill to a working installation.

No daemon, fleet enrollment, provider account, or package-manager subscription is
required for local use. Source and skill declarations are versioned; machine
ownership and execution approvals are local. See the current acceptance report
for precisely which native host-loading behaviors have been verified.
