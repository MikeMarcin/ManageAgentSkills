# Sources, taps, package validation and updates

Everything behind `mask update`: source catalog migration, taps, fetches, validation, curated imports, provenance and program self-update.

## Update skills or the program

> [!IMPORTANT]
> A source update affects **every registered project and personal consumer**. Run it between active tasks; all links share one checkout, and running agents may cache instructions.

```sh
mask update
```

One command fetches the approved candidate, freezes it, shows which registered scopes it affects, fast-forwards the source and reconciles their links. `mask update --dry-run` previews from the last fetch without touching the network (use `mask source fetch` first to preview new content); `--offline` applies only what is already fetched. `mask update --project DIR` on a shared legacy source shows every other affected scope and asks before widening; `--yes` never grants that, `--all` or the reported `--expect-plan-hash` does. A guarded run applies exactly the previewed candidate and never fetches a different one. Dirty, ahead, diverged, detached, unavailable or colliding inputs refuse instead of triggering a reset, stash, clean or push.

Additional repositories can be registered in an approved source catalog. First
preview `mask source migrate --dry-run --json`, then apply `mask source migrate
--json` to assign the existing source the `legacy` alias. This changes machine
configuration to v2 while preserving declarations, ownership and deployed links.
The preview exposes the full repository identity being approved. Existing v1
configuration remains supported; its historical basename check is replaced by
full URI matching after migration.

```sh
mask tap add community https://github.com/OWNER/REPOSITORY.git --dry-run --json
mask tap add community https://github.com/OWNER/REPOSITORY.git --json
mask source list --json
mask source show community --json
mask source fetch community --json
```

Adding a tap only registers its repository, ref and package layout. An explicit
fetch fills a separate owned bare cache; it does not deploy skills. HTTPS and SSH
are distinct approved identities. Git credentials remain in the existing Git
configuration; URLs containing credentials and redirects are refused. Tap removal
retains the cache and refuses references, including the legacy binding.

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

With a v2 catalog, `skill list` reports the fetched catalogs and `skill show
SOURCE/ID` selects an exact source. Duplicate bare names require qualification;
an unfetched source is reported explicitly. These queries read frozen Git objects.
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
Copy imports can now vendor one selected package into a new directory in an
approved authoring source. Fetch the upstream catalog first for an offline
preview, then apply its exact proposal:

```sh
mask source fetch community --json
mask skill import community --mode copy --into legacy --path skills/example --dry-run --json
mask skill import community --mode copy --into legacy --path skills/example --expect-plan-hash RETURNED_HASH --json
mask skill provenance legacy/example --json
```

An import preserves raw bytes and adjacent notices, writes a bounded provenance
record, and returns exact changed paths. It never commits, pushes, or edits the
Git index. Existing content—including an empty directory appearing concurrently—
refuses publication. Destination parents must already exist; an existing source
index must already map the selected ID. Package selection remains separate from
deployment. V2 consumer selections pin approved sources independently.

Provenance reports distinguish authoring observations, frozen tap objects,
recorded assertions, missing history, and independently rechecked upstream Git
facts. After editing imported content, preview `mask skill record-adaptation
legacy/example --note "Describe the adaptation" --dry-run --json`, then apply
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
