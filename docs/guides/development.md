# Development and reference

Local smoke scenario, structure gate, source dumps, selection locks and the current implementation status.

## Development and reference

For a local CLI smoke scenario, run `python3 -B -m unittest tests.test_end_to_end.EndToEndTests.test_public_management_sequence` from this checkout. It uses disposable projects and local bare Git remotes. Run `python3 -B scripts/verify_documentation.py` for the RFC/issue structure gate; choose additional tests for the behavior being changed.

Run the whole suite with `python3 -B scripts/run_tests.py`. It runs each test class in its own process, one per CPU, and prints output only for a class that fails; `-k TEXT` selects classes, `-j 1` runs them serially and `--slowest N` lists the slowest. `python3 -m unittest MODULE` still works for one module.

To create a single Markdown file for ChatGPT project sources or a code review:

```sh
python3 -B scripts/make_project_source_dumps.py
```

The dump is written to `artifacts/manage_agent_skills_project_source.md` (ignored
by Git). It includes current working-tree source, tests, schemas, documentation,
and portable `.mask/skill-config/` context, including new untracked text sources.
It skips links, local agent directories, other `.mask/` data, virtual environments,
caches, generated output, and binary file types. Selected text files must be UTF-8
without NUL bytes; invalid content reports an error before writing the dump.
This is a source-file filter, not a secret scanner or a Git-ignore filter.

Use `--output PATH` for another destination, `--stdout` to print the dump, or
`--root PATH` for another checkout. Relative output paths are resolved under the
selected root; the default root is the checkout containing the script, regardless
of the working directory. `--include-generated` adds build/output directories
while keeping links, caches, virtual environments, and local state excluded.
The selected output file is always excluded from its own dump.

`mask lock --project PATH --dry-run --json` previews an exact lock for a v2
selection. Add the tap and fetch it with `mask source fetch NAME` first, then run `mask lock`
with the returned `--expect-plan-hash`. `--user` selects the personal declaration.
Locking uses cached objects only and never changes deployed skills. Existing locks
retain their resolution; `--refresh --skill SOURCE/ID` updates selected bindings.
Ref rewrites require explicit `--allow-ref-rebind`. New consumers can register/apply those artifacts; a registered
consumer changes its lock through `mask update` (`mask lock` refuses `lock.active`), and a consumer left by the
live-checkout program converts with `mask doctor --migrate`. Missing or stale locks block readiness. See the
[selection/lock contract](../architecture/cli-contract.md#cached-selection-locks)
for canonical defaults, exact digests and the machine-local file-source limitation.

- [CLI contract and exit codes](../architecture/cli-contract.md)
- [JSON schemas](../../schemas/)
- [Contributing](../../CONTRIBUTING.md), [RFCs](../rfcs/README.md) and [issue board](../issues/README.md)
- [Current readiness acceptance and verification limits](../development/readiness-acceptance.md)
- [Local v0.1.0 readiness and implementation provenance](../releases/v0.1.0.md)

The September 2026 RFC pack is imported, with workspace readiness, integration,
recovery and legacy inventory slices implemented. Native Windows
readiness acceptance passed on ExampleWinHost after the recorded Windows fixes. The tap
catalog supports fetch, package validation, curated
copy imports and provenance. Cached v2 selection locks now record exact commits,
paths and payload digests. Exact artifact preparation is available through `source fetch --locked`;
consumers deploy isolated store artifacts through the recoverable engine.
Pinned engine verification is currently local; native pinned-deployment acceptance
remains pending. [RFC-MASK-0021](../rfcs/RFC-MASK-0021-tap-only-deployment.md) retires the live-checkout mode:
`mask update` fetches taps and `mask doctor --migrate` converts live-checkout machines; its closeout records what
is qualified. Scoped dev-link and isolated source publication are available. Per-binding targeting and local compatibility policy are available. Attributed contribution conflicts are checked. Public profiles, bundles, fleet
management and full update-impact reports remain RFC work. Importing their specifications does not
make those features available. MASK has no daemon. Source publication requires explicit package paths and separate commit/push flags.

Both named repositories consume the shared skills. Verified bootstrap copies
remain outside discovery roots in each
`.mask/bootstrap-retired/implement-rfc-2026-09-05`. Filesystem deployment and bounded
workflow invocation were verified; agent UI loading was not.
