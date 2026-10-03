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

## Named bundles

Bundles are flat source-owned lists of explicit `SOURCE/ID` bindings. Inspect a fetched
approved catalog, then review and install through the normal setup and recovery pipeline:

```sh
mask tap fetch agentskills --json
mask bundle list --source agentskills --json
mask bundle show agentskills/rfc --json
mask bundle install agentskills/rfc --dry-run --json
mask bundle install agentskills/rfc --approve-plan RETURNED_HASH --json
```

`install` adds a local contribution. It preserves manual per-skill agent targets,
unrelated skills and every existing exact package row. Conflicting version constraints,
conditions or competing bundle targets report their origins before consumer changes.
An unapproved source must be approved separately; bundle data cannot enroll it.
All bindings are validated before activation. Browsing and dry runs never fetch.
A live first installation may acquire an unfetched approved tap; `--offline` prevents it.

Declaration v2 optionally records `bundle_state`: the explicit manual coordinates
and each expanded bundle's source repository, exact definition commit/digest and
active bindings. These records are portable declaration data and enter the selection
digest, exact lock and journal. `introduced_by` is an explanation only. Ordinary
`install ID` records a positive manual selection even when a bundle already supplies
it; `uninstall ID` explicitly removes it from the local manual and expanded selections.
Repeat bundle install retains that expansion and its exact locks, including explicit
uninstalls. It does not change membership when a source branch advances.

Fetch a newer catalog and review `mask bundle upgrade SOURCE/NAME --dry-run`. The
result exposes the before/after selection, additions, removals, preserved contributions
and frozen definition identity. Apply with the returned hash. A changed fetched source
revision or definition makes an earlier plan stale. Package version upgrades remain
the separate `upgrade` task; a refresh retains existing locks unless this contribution's
explicit version selector changes without competing/manual/held authority.

Both `upgrade` and `install --replace` replace **only the named bundle's local
contribution**. They remove a former member only when it is exclusive to that
contribution, unheld and unchanged from its expanded binding. Manual selections,
overlapping bundles and unrelated bindings remain. Local target/condition edits or
held removed members become explicit retained manual contributions. Exact removal
still refuses edited/unmanaged deployment collisions through the planner.

`mask bundle uninstall SOURCE/NAME --dry-run` reviews removal of only that frozen
local contribution. Approve the returned hash to remove its receipt and exclusive
unchanged unheld members. Manual/overlapping members remain; last-origin held or
locally edited bindings become positive manual selections. Retained package rows
stay exact. It uses the installed receipt rather than a current source definition,
so no catalog fetch or membership adoption is needed, including with `--offline`.
Machine source approval and artifact ownership checks still apply; missing exact
artifacts require repair. An absent contribution is a no-op and does not register
an empty consumer. Reinstall creates a new receipt, preserves manual survivors
and reviews any required setup. Interrupted uninstall uses normal frozen-journal
recovery; recovery never reruns scripts.

The newly introduced pre-release `bundle apply` spelling is replaced by
`bundle install`; there is no compatibility alias. There is no recursion, dependency
solver, source enrollment or automatic membership update. Project is the default scope; `--project PATH` and
`--user` select one explicit consumer, with no aggregate bundle mutation.
