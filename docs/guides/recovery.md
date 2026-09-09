# Recovery and stopping management

Interrupted operations, unregistering consumers, retiring worktrees and removing the program.

## Recover or stop managing a project

Inspect an interrupted operation with `mask recover --inspect --json`. After checking the recorded intent, choose explicit `--complete` or `--rollback`. Recovery preserves unexpected edits and never resets a Git checkout that has advanced. Git helpers and checkout filters remain trusted subprocesses; MASK is not a sandbox or an atomic deployment system.

`mask project unregister PATH --json` removes only unchanged owned links and preserves the declaration, context and source. `--keep-links` explicitly abandons ownership, including for an unavailable project. Exact existing declared links can be adopted with `link adopt`; consult the [CLI contract](../architecture/cli-contract.md) for its required preconditions.

If readiness adapters are installed, disable the owned adapters and revoke the
applicable approval when stopping automatic management. Unregistering alone does
not revoke approval. `workspace forget PATH --expect-identity ID` can retire a
removed Git worktree's registration after verifying its recorded identity and
absence from the original Git worktree list; it does not prune unavailable roots.

To remove the program, disable installed integrations and unregister the selected project and personal consumers first, then explicitly remove the verified owned launcher and program checkout while preserving source history and backups. There is no purge command. Source relocation likewise requires an explicit unregister/setup/register sequence; a new `--home PATH` can preserve the old machine state during setup.
