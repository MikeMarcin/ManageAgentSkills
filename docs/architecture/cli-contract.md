# MASK 0.3 CLI contract

The public result protocol is **v2**. The program is a local Python CLI with
approved Git taps, immutable payload storage and project/personal declarations.
Skills are passive data unless the user approves a declared setup action.

## Commands and scope

| Bucket | Commands | Default target |
|---|---|---|
| Shared resources | `tap`, `untap`, `update`, `cleanup` | Program, approved catalog and storage |
| Catalog browsing | `search [QUERY]`, `info SKILL` | Fetched shared tap catalogs |
| Enrollment | `register [PATH]`, `unregister [PATH]` | Current checkout |
| Selection | `install SKILL ...`, `uninstall SKILL ...`, `list`, `pin SKILL`, `unpin SKILL` | Current checkout |
| Maintenance | `upgrade [SKILL ...]`, `repair`, `status` | Current checkout |

A checkout is the project root discovered within the current Git worktree.
Linked worktrees are independent registrations. `--project PATH` selects another
root; `--user` selects personal skills. No checkout means an explicit target is
required. Personal skills never join an implicit checkout mutation.

`upgrade`, `repair`, `status` and `list` accept `--all` for every registered checkout
plus personal skills. The three scope selectors are mutually exclusive. `pin` and
`unpin` use `--all` as an alternative to SKILL: all skills in the current checkout,
or all personal skills with `--user`. Bare `mask` is `status`.

## Complete tasks

`register` creates an empty declaration when necessary, enrolls the selected root,
restores existing locked versions and completes declared setup. A fresh worktree
needs only `mask register`. Missing lock bindings are resolved without moving
already locked selections. `install` can enroll a checkout automatically.

`install` and `uninstall` change membership incrementally and reconcile deployment.
`unregister` removes unchanged managed deployment and registration while retaining
project declarations and lock files; `--keep-links` explicitly abandons ownership.

`pin` marks a selected binding with `pinned: true` in declaration v2 and preserves
its existing locked resolution and selector. `unpin` removes that hold without
changing the resolution. Upgrade resolves only eligible unheld selections; held
skills still receive missing links, static roles and consented generated setup.

`repair` restores the declared pinned state. `upgrade` resolves newer allowed
versions then makes the selected installations ready, even when versions do not
change. Missing required inputs are diagnosed before consumer mutation.

## Review and JSON

The task pipeline is resolve, inspect, review, prepare, apply, verify. A single
review includes every required package setup action and exact native-role backup
and replacement. It binds consumer controls, root identities, locked content,
setup scripts/inputs/interpreter and observed replacement bytes. No declaration,
lock, registration or deployment changes occur before approval. Cache preparation
may remain after refusal and is reported separately.

Ordinary owned effects need no prompt. `--dry-run` never fetches, writes or runs
setup. `--approve-plan HASH` approves exactly the previewed task; changed inputs
refuse with `plan.stale`. JSON and redirected invocations never prompt. Decline
aborts the task before consumer writes. There is no blanket yes/repair/yolo flag.
Directories, symlinks and unsafe or unowned skill targets remain protected; only
validated regular native-role replacements enter the reviewed backup path.

Results have `schema_version: 2`, `command`, `ok`, `dry_run`, `changed`,
`would_change`, `transaction`, `data`, `actions`, `warnings` and `error`.
`data.scopes` lists examined roots and their project/user scope. Planning results
include `plan_hash`, actions, outcomes and the task review. Setup publications
retain separate transaction records; failure never erases earlier committed
effects or claims readiness. Filesystem readiness does not establish host loading.

Human output groups ordinary link/lock changes by location. Reviews name setup
code and its interpreter, target roles and locations, and exact files to back up
or replace. Internal store destinations stay in JSON. Terminal output uses
restrained color; `NO_COLOR` or `TERM=dumb` disables it. Redirected output remains
plain text. JSON always emits one result document without progress messages.

Long terminal tasks report phases as they begin and elapsed activity every ten
seconds while a phase is running. Progress pauses during the confirmation question
and resumes immediately after approval. It describes activity, not estimated
percentages or successful completion. On failure, setup results distinguish
published, incomplete and unstarted actions; pre-setup diagnostics are not presented
as a fresh readiness check. A failed rollback retains both failure causes along
with the journal for explicit recovery.

Existing v1/v2/v3 state and recovery journal readers remain. Their operation IDs
are private engine contracts, not public command aliases. Never rerun a package
script during recovery. Inspect with `recover --inspect`, then explicitly choose
`--complete` or `--rollback` as permitted by the recorded phase.

## Shared resources and updates

`tap` lists sources; `tap NAME URL` approves one; `untap NAME` removes an unused
source while retaining cached data for explicit cleanup. Advanced operations are
`tap fetch`, `tap show`, `tap inspect`, `tap transport`, `tap repair-cache`,
`tap migrate` and `tap publish`. These action names are reserved as tap operands.
Development links use `skill dev-link`.

`search` matches names and descriptions in fetched catalogs. `info` reports skill
metadata and the declared project/personal workflow; neither command runs scripts.

`update` fast-forwards the program when safe and refreshes all tap catalogs; dirty,
ahead or diverged program checkouts are preserved and reported. Install/upgrade
perform this refresh when no successful refresh is recorded within 24 hours.
`--no-update` skips that preliminary refresh; task-specific fetches remain allowed.
`--offline` forbids all network. Preview and approved-plan application never
refresh. A program change re-executes before consumer planning. No cleanup runs
automatically after upgrades.

## Cleanup and concurrency

`cleanup --dry-run` inventories verified unused artifacts, unused owned caches,
disposable backups and recognized retired generated files. Live and recorded
registered locks, personal locks and declared references protect content. An
unavailable registered root prevents unsafe reference assumptions. Pending recovery
prevents cleanup. Unknown, linked, modified or unverified content is preserved and
reported. Incomplete setup staging without an ownership journal remains unknown.

Cleanup is a reviewed deletion task. It rechecks references and exact candidate
bytes before deleting only inventoried entries. It never deletes the active
`.mask.lock.json`, personal lock, current native-role lock or persistent writer-lock
files. There is no age-only backup retention threshold.

A persistent lifecycle lock covers resolution, preparation and activation for all
public modifying commands, including startup integration. Cleanup takes the same
lock, so it cannot collect artifacts prepared by a task before its registration
commits. The transaction writer lock remains separate. Lock-file existence does
not imply a stale lock and is never grounds for deletion.

## Integrations and advanced controls

Adapters and launch use the shared pinned readiness engine; generated startup
commands invoke `integration run`. Events require the existing readiness authority,
never prompt and never grant package setup. `status --check --workflow-profile
SKILL=PROFILE` inspects selected declared requirements without running setup.

Agent target setters reconcile immediately; there is no separate `--apply` step.
Other advanced controls remain under `config`, `skill`, `project`, `user`,
`integration`, `selection-policy`, `compatibility` and `self`. Use capabilities and
command help for their exact arguments. Publication remains an explicit authoring
operation and is never part of install, upgrade or repair.

## Taps, payloads and caches

Approved taps name repository identities, refs and package layouts; artifact locks
name exact commits and byte digests. HTTPS and SSH spellings of supported forge
repositories share one identity. Transport preferences remain machine-local.
`tap fetch --locked` prepares the exact selected objects without upgrading them.
Ordinary consumers link to verified immutable store payloads; authoring checkouts
are used only by explicit development and publication commands. Unknown or corrupt
cache content is preserved for diagnosis. Read-only checks and previews never
remove interpreter bytecode; a mutating readiness task may clear recognized cache
files before verification.

## Cached selection locks

`lock` creates a v2 declaration's missing lock from fetched content and cannot
change an active consumer's versions. Existing resolutions stay fixed unless an
explicit eligible refresh is requested. `upgrade` owns active version transitions;
`repair` and `register` restore existing resolutions. Declaration and lock digests,
repository identities, selectors, package paths and content hashes are validated
together. Exact commit selectors stay fixed even without an explicit version hold.

## Selected updates and authoring exceptions

`upgrade TAP/SKILL` narrows version changes within the chosen scopes. It respects
explicit holds. Development links remain explicit live authoring exceptions:
`skill dev-link` chooses the authoring checkout and `--to-pinned` returns to the
locked payload. Scoped upgrade refuses active development links; `upgrade --all`
reports and skips them. `tap publish` requires named package paths, with separate
`--commit` and `--push` authorization. Recover pending journals with their owning
program before switching executables; neither update nor recovery resets a checkout.

## Exit classes

0 success; 2 invalid invocation; 3 invalid/missing configuration; 4 blocked task,
stale plan or missing consent; 5 external/filesystem/setup failure; 6 busy lock;
7 failed observational check; 8 pending/conflicting recovery; 10 internal invariant;
130 interruption. Typed error codes refine these classes.

The [accepted amendment](../rfcs/plans/upgrade-readiness/accepted-surface.md)
records the owner decisions. Earlier engine/recovery detail is retained in the
[historical v1 contract](../rfcs/plans/upgrade-readiness/legacy-cli-contract-v1.md).
