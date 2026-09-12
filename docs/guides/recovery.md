# Recovery and stopping management

Interrupted operations, unregistering consumers, retiring worktrees and removing the program.

## When ensure preserves existing role files

For automatic repair, run `mask ensure --all --repair` (or `--yolo`). It explicitly
authorizes declared setup and replacement of regular role files after backing
them up. For just one scope, use `--project DIR --repair` or `--user --repair`.
Add `--dry-run` to inspect the repair without running setup or changing files.
Backups are retained under `MASK_HOME/backups/TRANSACTION/`, including a
`manifest.json` mapping backups to original paths. Normal `ensure` behaves as
described below.

`mask ensure` can create missing agent role files and update unchanged files it
manages. Permission to run setup does not grant permission to replace other
files. If existing role files have no matching verification record, setup is
blocked before prompting or running the generator. Repeating `ensure`, using
`--yes`, or running `update` cannot clear that conflict.

The error groups files under their project or personal root. Paths below that
root, such as `.codex/agents/rfc-integrator.toml`, identify the files to inspect.
"Setup needed" with an existing file means MASK cannot verify it; it does not
mean the file is missing or that its contents are necessarily wrong.

If version control contains a matching set, restore the role files together with
`.mask/generated/SKILL-ID/native-roles.lock.json` (MASK also reads the retired
`.mask/skill-config/SKILL-ID/` location when the canonical one is absent) and the
consumer inputs it verifies. A lock for different package content or different inputs will not
validate the files. Do not hand-edit hashes or MASK's machine ownership state.

Otherwise, compare the existing files with the intended role definitions. Back
up files outside the agent discovery directories before deciding which custom
content to keep and which destinations to clear for generation. MASK does not
make that replacement decision for you. After resolving the conflicts, run:

```sh
mask ensure --project /path/to/project
# Or, for personal skills:
mask ensure --user
```

Approve setup in the terminal if it is offered. The final result must say the
workflow is ready; a saved deployment or successful source fetch alone does not
mean setup completed. "Deployment changes were saved" refers to local MASK
changes, never a Git commit. Host loading is a separate check.

## Recover or stop managing a project

Inspect an interrupted operation with `mask recover --inspect --json`. After checking the recorded intent, choose explicit `--complete` or `--rollback`. Recovery preserves unexpected edits and never resets a Git checkout that has advanced. Git helpers and checkout filters remain trusted subprocesses; MASK is not a sandbox or an atomic deployment system.

`mask project unregister PATH --json` removes only unchanged owned links and preserves the declaration, context and source. `--keep-links` explicitly abandons ownership, including for an unavailable project. Exact existing declared links can be adopted with `link adopt`; consult the [CLI contract](../architecture/cli-contract.md) for its required preconditions.

If readiness adapters are installed, disable the owned adapters and revoke the
applicable approval when stopping automatic management. Unregistering alone does
not revoke approval. `workspace forget PATH --expect-identity ID` can retire a
removed Git worktree's registration after verifying its recorded identity and
absence from the original Git worktree list; it does not prune unavailable roots.

To remove the program, disable installed integrations and unregister the selected project and personal consumers first, then explicitly remove the verified owned launcher and program checkout while preserving source history and backups. There is no purge command. Source relocation likewise requires an explicit unregister/setup/register sequence; a new `--home PATH` can preserve the old machine state during setup.
