# Sources, taps, package validation and updates

Everything behind `mask update` and `mask upgrade`: taps, fetches, validation, curated imports, provenance and the program's own update.

`mask update` refreshes the program and every tap catalog without changing consumer
selections. `mask upgrade` upgrades the current checkout and makes its skills ready.

```sh
mask update
mask upgrade --dry-run
mask upgrade
mask upgrade --all       # every registered checkout plus personal skills
```

## Upgrade skills

Bare upgrade selects only the current checkout. `--user` selects personal skills;
`--all` selects the complete registered set. These commands review installed bundle
definitions and newer unheld member versions together with ordinary selected skills.
`upgrade SOURCE/ID` narrows the package versions and keeps bundle definitions frozen.
`pin SKILL` holds its current locked version; `unpin SKILL` releases that hold without
upgrading immediately. Held skills still receive readiness repair and consented setup.

Install and upgrade refresh MASK and the shared catalogs when the last successful
refresh is older than 24 hours. `--no-update` skips this preliminary refresh while
allowing task-specific acquisition; `--offline` forbids all network. Program updates
re-execute before consumer planning. Dirty/ahead/diverged program checkouts are held.

Upgrade resolves candidates, inspects setup and exact native-role replacements,
collects one review if needed, then applies and verifies. `--dry-run` and
`--approve-plan HASH` use cached content without fetching. JSON and redirected
commands never prompt. Declining significant actions leaves consumers untouched.

Use `mask upgrade --commit` to record the final changed `.mask.json` and
`.mask.lock.json` after readiness succeeds. Existing staged, unstaged, partially
staged and untracked changes to those controls are included in full, even when
versions were already current. Unrelated staging and working files are preserved;
setup outputs stay outside the commit. The message is `chore(mask): upgrade skills`.
Normal Git identity, hooks and signing apply, with the configured Git timeout.
MASK creates no empty commit and never pushes.

`--all --commit` makes at most one commit per eligible project on its current
branch, including linked worktrees. Personal skills upgrade normally and report
`not_applicable`; `--user --commit` is invalid. Prospective differing controls need
an attached branch with an existing HEAD, regular nonignored controls, no unmerged
entries and no active merge, rebase, cherry-pick, revert or bisect. An ineligible
project refuses before consumer changes; under `--all` only that project is blocked.
Controls that already match HEAD need no commit eligibility check.

Preview with `mask upgrade --commit --dry-run --json`, then pass the shown hash
with `--approve-plan`. The preview discloses paths, existing changes, message and
eligibility without staging or running hooks. Commit intent, Git identity, branch,
HEAD, controls and staging bind the hash; changed observations refuse as `plan.stale`
before consumer effects. Git state and final controls are rechecked before committing.

A Git failure does not undo an applied upgrade or successful commits in other
projects. A scoped failure returns `upgrade.commit_failed` (exit 5); aggregate
blocking or commit failures return `upgrade.incomplete` (exit 4), with per-project
outcomes. If setup or readiness fails, commits remain `not_attempted`. Created
commits and hook effects are inspected and reported even after a timeout. Retry
can record pending controls without duplicating completed commits. Recovery does
not roll back, amend or resume these Git commits.

For a branch selector, an upgrade keeps the existing exact lock when that package's
path, bytes, executable modes, metadata and provenance are unchanged. Commits to
other skills or repository bookkeeping do not advance its lock. This lets a skill
repository commit its own consumer lock without triggering another lock update.
Real package changes and explicit selector changes still advance the resolution;
unchanged packages still receive readiness repair. A lock inside the selected
package itself is payload content, so changing it remains a package change.

For `--all`, a failed tap or incompatible bundle constraint blocks its dependent consumers and reports
`upgrade.incomplete` while independent consumers may complete. A single-checkout
failure applies no consumer changes. Moved tag/non-fast-forward ref resolutions
require explicit `--allow-ref-rebind`; an approved rebind records the new resolution
even if its package bytes match. Branch ancestry is checked against the locked
commit, not every head previously inspected: a rewrite confined to later commits
can still descend from that locked commit. Unavailable ancestry is not assumed safe.
Dev-link consumers are skipped only with
`--all`; a single selected development checkout refuses ordinary upgrade.

`mask tap fetch [NAME]` refreshes approved caches without deployment. The advanced
`tap fetch --locked --project PATH` prepares exact locked artifacts. These caches
are shared; deployed links always point into the immutable store.

If a recognized cache refuses with `source.cache_invalid`, inspect its reported
path and identities. Device numbers can change after a remount; matching inode
numbers alone do not prove ownership. Do not edit the marker to make it pass.
Retain the entire cache and rebuild from the approved remote:

```sh
mask tap repair-cache agentskills --dry-run --json
mask tap repair-cache agentskills --approve-plan RETURNED_HASH --json
mask tap fetch agentskills --json
```

`repair-cache` atomically moves the directory to the reported sibling retention
path without replacing anything, deleting contents, reading its Git configuration
or trusting its objects. The next fetch creates a fresh active cache. The operation
refuses unrecognized markers, symlinks, stale previews and retention collisions.
Catalog, registry, store, consumers and authentication remain unchanged. Retained
objects stay available for inspection; old locked commits may need a later exact
fetch if their store payloads are also unavailable. No automatic cleanup is implied.

### One tap, however each machine signs in

A tap names a repository, not a way of reaching it. On GitHub, GitLab, Bitbucket and Codeberg, `https://github.com/O/R`, `ssh://git@github.com/O/R.git` and `git@github.com:O/R.git` are the same tap, written in project files as `https://github.com/O/R.git`. A project file committed from a machine that uses HTTPS therefore works unchanged on a machine that uses SSH keys, and the other way round. Files written before this rule, including the old `ssh://git@github.com/~/O/R.git` spelling, keep working byte for byte.

How a machine reaches the tap is its own business and never enters a project file. By default MASK works it out on each fetch, without ever prompting: it follows the project's own `origin` (if your project clones over SSH, so does the tap), then whatever worked last time, then your `gh` `git_protocol` setting, then the URL you typed at `tap`, and finally the other scheme. It moves on only when a transport cannot authenticate or connect, and tells you when it had to.

```sh
mask tap show agentskills                                                # which transport is in use, and why
mask tap transport agentskills git@github.com:MikeMarcin/AgentSkills.git    # always use SSH on this machine
mask tap transport agentskills --derive                                     # work it out again
mask config set --forge-host git.example.com                                # a self-hosted forge where both URLs reach the same repositories
```

Every other host stays strict: there an HTTPS URL and an SSH URL are different taps, because nothing says they serve the same repositories. Only this machine's configuration can say so; a project file cannot. A machine set up before this rule still works; `mask status` mentions it, and `mask tap migrate --dry-run` previews the one-step catalog cleanup.

Additional repositories are approved as taps:

```sh
mask tap community https://github.com/OWNER/REPOSITORY.git --dry-run --json
mask tap community https://github.com/OWNER/REPOSITORY.git --json
mask tap --json
mask tap show community --json
mask tap fetch community --json
```

A source may commit `mask-source.json` with `schema_version: 1`, a complete
`packages` map from package ID to relative package directory, and an optional
`bundles` map. An index replaces automatic package discovery, so list every package
that should remain discoverable. Each bundle has `skills` (a flat array of
source-qualified bindings) and an optional `description`; only the supported binding
fields `source`, `id`, `agents`, `version`, `when` and `introduced_by` are accepted.
Duplicate, recursive, malformed and unsupported entries refuse. The source index
grants no machine approval or setup authority. See [named bundles](declarations.md#named-bundles).

Adding a tap only registers its repository, ref and package layout; `tap` never fetches. `install` fetches a tap on demand, and `upgrade` and `tap fetch` fetch it explicitly, into a separate owned bare cache. HTTPS and SSH are distinct approved identities. Git credentials remain in the existing Git
configuration; URLs containing credentials and redirects are refused. Tap removal
retains the cache and refuses while a registered declaration or lock references the tap.

`tap NAME URL --checkout PATH` binds an optional authoring checkout, whose `origin` must normalize to the tap's repository. `install`, `list`, `repair` and `upgrade` never read it. `tap publish`, `skill dev-link` and the curated imports below use it.

A tap keeps exact bytes: MASK never converts the line endings of its packages
unless you opt in when you register it, with `mask tap NAME URL --checkout
PATH --autocrlf`. That tap's published and development bytes then follow Git's
`core.autocrlf=true` conversion. Without the opt-in, `tap publish` and a new
`skill dev-link` refuse `source.line_endings_converted` when Git converted an
authoring checkout's unedited files, and `tap` warns when the checkout's own
`core.autocrlf` converts. MASK does not change that checkout's Git configuration:
run `git -C PATH config core.autocrlf false`, delete the reported files (they
have no edits) and restore them with `git -C PATH checkout -- FILE ...`, or
register the tap with `--autocrlf`.

`skill list` reports the fetched tap catalogs and `skill show
SOURCE/ID` selects an exact tap. Duplicate bare names require qualification;
an unfetched tap is reported explicitly. These queries read frozen Git objects.
`source inspect URL [--ref REF] [--path PATH]` inspects an already approved
repository and reports package coordinates, without deploying them. Its dry run
uses cached refs/objects and reports `resolution_required` when they are missing.
Root, flat and indexed nested layouts are supported. GitHub tree/blob URLs with
ambiguous branch/path splits return choices. Package metadata inspection is not
full payload validation. Use `mask skill validate SOURCE/ID --json` (or `--all`)
to validate exact cached payload bytes and logical Git modes without fetching or
checking out files. It rejects links, submodules, LFS pointers, nonportable or
colliding paths, and known host activation metadata. Limits are 64 MiB per file,
256 MiB per package, 10,000 tree entries, and depth 32. Plain frontmatter uses a
closed passive scalar subset; tool grants, hooks and dynamic shell preprocessing
refuse (including executable examples). Arbitrary package scripts
remain passive data; this is structural validation, not a malware safety claim.
Copy imports can vendor one selected package into a new directory in a tap's
authoring checkout. The destination tap needs that checkout (`import.authoring_required`
otherwise), and the checkout must be on the tap's configured branch. Fetch the upstream catalog first for an offline
preview, then apply its exact proposal:

```sh
mask tap team https://github.com/OWNER/TEAM-SKILLS.git --checkout /path/to/TEAM-SKILLS --json
mask tap fetch community --json
mask skill import community --mode copy --into team --path skills/example --dry-run --json
mask skill import community --mode copy --into team --path skills/example --approve-plan RETURNED_HASH --json
mask skill provenance team/example --json
```

An import preserves raw bytes and adjacent notices, writes a bounded provenance
record, and returns exact changed paths. It never commits, pushes, or edits the
Git index. Existing content—including an empty directory appearing concurrently—
refuses publication. Destination parents must already exist; an existing source
index must already map the selected ID. Package selection remains separate from
deployment: consumers receive the imported package only after it is published to the tap and installed or updated.

Provenance reports distinguish authoring observations, frozen tap objects,
recorded assertions, missing history, and independently rechecked upstream Git
facts. After editing imported content, preview `mask skill record-adaptation
team/example --note "Describe the adaptation" --dry-run --json`, then apply
with its returned plan hash. This records the observed changes without modifying
payload files or inventing earlier history. Windows records logical execute
modes; copying does not establish executable Git index bits for a later commit.

Managed tap fetches stage refs before advancing the catalog cursor. They
enforce the configured timeout and bounded command output, and monitor object
storage against 256 MiB growth per fetch and a 1 GiB cache ceiling. Storage is
sampled every 50 ms and checked after fetch; it can overshoot between samples.
This is not a hard network transfer or disk quota. Refused acquisitions may
retain objects and a staging ref for inspection, but do not select the package.

## Update the program and the taps

`mask update` first fast-forwards the running ManageAgentSkills checkout from its `origin` `main`. It checks protocol/schema compatibility and reports `data.program` (`status`, `program_before`, `program_after`, `next_invocation_required`); the next command loads the new implementation. It then fetches every approved tap, exactly as `mask tap fetch` does, and reports each under `data.fetches`. It never changes a declaration, lock, link or consumer, and it does not reinstall the launcher.

A program checkout that is ahead of its remote, diverged, detached, on another branch or carrying uncommitted changes is somebody's work in progress: `update` leaves it alone, reports `status: held` with the reason, and still fetches the taps. A candidate that fails the compatibility check refuses `source.candidate_invalid`. A Git failure while fetching the program is reported after the taps were still fetched. `--dry-run` contacts nothing. On a machine that predates taps, `update` advances the program and skips the taps.
