# Sources, taps, package validation and updates

Everything behind `mask update`: taps, fetches, validation, curated imports, provenance and program self-update.

## Update skills or the program

> [!IMPORTANT]
> `mask update` with no scope updates **every registered project and personal consumer**, wherever you run it. Run it between active tasks; running agents may cache instructions.

```sh
mask update --dry-run
mask update
```

`mask update` fetches each tap that the selected consumers reference exactly once. It then re-resolves every consumer's selectors from the fetched cache and discloses each consumer's lock changes (`data.consumers[]`, with before and after commits and digests). All lock, store and link changes activate through one recoverable journal. `--project DIR`, `--user`, `--all` and `--skill SOURCE/ID` narrow the selection; with `--skill`, only the taps of the named bindings are fetched. Links always point into `MASK_HOME/store`, never into a Git checkout.

`--dry-run`, `--offline` and `--expect-plan-hash` never fetch. They resolve from the existing cache (run `mask source fetch` first to preview new content), and a consumer whose selector needs objects that are not fetched yet is reported `blocked` with `requires_fetch`. A guarded run with the reviewed `--expect-plan-hash` applies exactly the previewed candidates.

A tap that cannot be fetched blocks only the consumers that reference it. The others are applied, and the command exits 4 with `update.incomplete`, naming the blocked roots. A `--project` or `--user` update whose tap fails refuses with the fetch error (exit 5 for a Git failure) and applies nothing. When a locked tag or ref now names a different commit, `lock.ref_rebound` refuses the whole invocation unless you pass `--allow-ref-rebind`. An empty registry exits 0 with warning `project.empty_registry`. A consumer in an explicit development link is skipped with a `dev_link.active` warning by `update` and `update --all`, and refused by a `--project` or `--user` update; return it with `source dev-link --to-pinned`. `update` never runs package setup.

`mask source fetch` without a name fetches every approved tap into its cache and deploys nothing; a failing tap is named in the error while the others are still fetched. `mask source fetch NAME` fetches one tap, and `source fetch --locked` prepares exact locked artifacts.

Additional repositories are approved as taps:

```sh
mask tap add community https://github.com/OWNER/REPOSITORY.git --dry-run --json
mask tap add community https://github.com/OWNER/REPOSITORY.git --json
mask source list --json
mask source show community --json
mask source fetch community --json
```

Adding a tap only registers its repository, ref and package layout; `tap add` never fetches. `install` fetches a tap on demand, and `update` and `source fetch` fetch it explicitly, into a separate owned bare cache. HTTPS and SSH are distinct approved identities. Git credentials remain in the existing Git
configuration; URLs containing credentials and redirects are refused. Tap removal
retains the cache and refuses while a registered declaration or lock references the tap.

`tap add NAME URL --checkout PATH` binds an optional authoring checkout, whose `origin` must normalize to the tap's repository. `install`, `list`, `ensure` and `update` never read it. `source publish`, `source dev-link` and the curated imports below use it.

A tap keeps exact bytes: MASK never converts the line endings of its packages
unless you opt in when you register it, with `mask tap add NAME URL --checkout
PATH --autocrlf`. That tap's published and development bytes then follow Git's
`core.autocrlf=true` conversion. Without the opt-in, `source publish` and a new
`source dev-link` refuse `source.line_endings_converted` when Git converted an
authoring checkout's unedited files, and `tap add` warns when the checkout's own
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
mask tap add team https://github.com/OWNER/TEAM-SKILLS.git --checkout /path/to/TEAM-SKILLS --json
mask source fetch community --json
mask skill import community --mode copy --into team --path skills/example --dry-run --json
mask skill import community --mode copy --into team --path skills/example --expect-plan-hash RETURNED_HASH --json
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

Managed source fetches stage refs before advancing the catalog cursor. They
enforce the configured timeout and bounded command output, and monitor object
storage against 256 MiB growth per fetch and a 1 GiB cache ceiling. Storage is
sampled every 50 ms and checked after fetch; it can overshoot between samples.
This is not a hard network transfer or disk quota. Refused acquisitions may
retain objects and a staging ref for inspection, but do not select the package.

`mask self update --json` updates only the running ManageAgentSkills checkout. It checks protocol/schema compatibility and returns `next_invocation_required`; the next command loads the new implementation. It does not update skills or reinstall the launcher. Local skill management remains available while the program checkout has authoring changes.
