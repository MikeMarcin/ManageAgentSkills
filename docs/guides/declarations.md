# Project and personal declarations

Each checkout/worktree has its own `.mask.json` selection and `.mask.lock.json`
exact resolutions. Personal skills use `MASK_HOME/user.json` and `user.lock.json`.
Registration records a physical root on this machine; it is not committed to Git.

For a clone or worktree that already declares skills:

```sh
mask register
mask status
```

Register restores locked versions and completes required setup. For a new selection,
install performs enrollment and preparation in one task:

```sh
mask install manage-agent-skills
mask install manage-agent-skills --user
mask list
mask list --user
```

Commands default to the current checkout. `--project PATH` selects another checkout;
`--user` selects personal skills. Register also accepts a positional path. Personal
skills are independent of the checkout and are never silently included in its changes.

| Intent | Command |
|---|---|
| Add skills without removing others | `install ID ...` |
| Remove selected skills | `uninstall ID ...` |
| Hold installed versions | `pin ID` or `pin --all` |
| Release holds without upgrading | `unpin ID` or `unpin --all` |
| Restore declared pins and setup | `repair` |
| Upgrade allowed versions and setup | `upgrade` |
| Inspect readiness | `status` |
| See every registered selection | `list --all` |
| Stop managing this checkout | `unregister` |

`pin --all --user` holds every personal skill. `upgrade --all`, `repair --all`,
`status --all` and `list --all` select every registered checkout plus personal skills.
Unregister preserves declarations/locks and removes unchanged managed deployment;
`--keep-links` explicitly leaves links behind and abandons their ownership.

`--dry-run --json` returns a frozen plan without writes, network or package code.
Apply the reviewed task using `--approve-plan HASH`. Required setup and exact
native-role replacements share one review before any consumer changes. Collision
protection remains in force for unsafe paths and unmanaged skill directories.

## Files and targeting

Commit `.mask.json` and `.mask.lock.json` for reproducibility. Generated skill links
under `.agents/skills/` and `.claude/skills/` should be ignored. Workflow context under
`.mask/skill-config/SKILL/` belongs to the consumer and may need to be committed.
Generated evidence lives under `.mask/generated/SKILL/`; the current native-role lock
vouches for generated files and is not disposable while those files are active.

Bindings may select source/skill, explicit ref/commit, agents, applicability and an
optional `pinned: true` hold. Holds preserve the current lock during upgrade without
skipping readiness. Unpin preserves the selector and permits the next upgrade.

```sh
mask project set-agents vendor/alpha codex
mask user set-agents vendor/alpha claude
mask project set-targets --inherit
```

Target setters reconcile immediately. Preview with `--dry-run`; no separate apply
step is needed. Host discovery determines precedence when personal and project
skills share a name; MASK reports the overlap without claiming which the host loads.
See [pins and agents](pins-and-agents.md) and the [CLI contract](../architecture/cli-contract.md).
