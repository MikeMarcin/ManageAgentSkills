# Public acceptance, not just helper qualification

This is the required test plan, **not a record that MASK passes**. Use temporary
`MASK_HOME`, consumer and upstream roots with local bare repositories added as
`file` taps. Do not change the owner's real machine, clone, credentials or host
trust to run these cases; the owner migration is its own attended card.

## Journey rules

The first user invocation after `self install` is `tap add`. No fixture may
pre-create `config.json`, pre-fetch a cache, pre-register a consumer or
pre-migrate a legacy machine before the invocation under test. Legacy starting
states are built by the schema-true fixture builder, and its bytes are asserted
to parse with the current program before any migration test uses them.

Separate a raw subprocess helper, a `--json` helper and a human terminal helper.
Count Git invocations where a case says "exactly once". Native symlink and
launcher checks must name the OS actually exercised.

## Bootstrap and install cases

| ID | Starting state and public operation | Required observation |
|---|---|---|
| B01 | Empty `MASK_HOME`; `tap add agentskills file:///upstream.git` | Config v3 with one tap, empty state, no fetch, actions `config.create` and `source.catalog`; dry run writes nothing |
| B02 | B01 then `install alpha --project P` | Cache created under `MASK_HOME/sources`, one fetch, v2 `.mask.json` and lock, links to `MASK_HOME/store/v1/...`, registration; no checkout anywhere |
| B03 | B01 then `install alpha --user` | Same for `user.json`, `user.lock.json` and the personal home; project untouched |
| B04 | B01 then `install alpha --offline` | `lock.resolution_required` naming `agentskills`; nothing written |
| B05 | Two taps both offering `alpha`; `install alpha` | `skill.ambiguous` with both `SOURCE/ID`; `install second/alpha` resolves only that tap |
| B06 | One tap unfetched; bare `install beta` | `source.unresolved` naming the unfetched tap under `--offline`; live install fetches it |
| B07 | `tap add NAME URL --checkout PATH` where origin matches; then `install` | Link targets unchanged (store), `authoring` recorded; mismatched origin refuses `source.identity_mismatch` |
| B08 | `init` with `--source` | Exit 2 `invocation.invalid`; `init --target codex` writes an empty v3 catalog |
| B09 | Every registered command on a v1 and on a v2 configuration | Only `capabilities`, `config show`, `doctor`, `recover`, `self *` proceed; all others exit 4 `migration.required` naming `doctor --migrate --dry-run` |
| B10 | `capabilities` | No `init --source`, `source status`, `source migrate`, `migrate`; `schemas.machine` 3; `deployment_model` taps |

## Update cases

| ID | Starting state and public operation | Required observation |
|---|---|---|
| U01 | Two taps, three consumers (two on tap A, one on tap B); push a new commit to A; `update` | Each tap fetched exactly once; A's consumers updated in one journal with per-consumer diffs; B's consumer lock byte-identical and reported `unchanged` |
| U02 | Same, but tap B's bare repository renamed away | A's consumers updated; B's consumer `blocked` with the Git error; exit 4 `update.incomplete`; transaction committed |
| U03 | `update --project P` where P's only tap is unreachable | Plain refusal with the Git error, exit 5, nothing written |
| U04 | `update --dry-run`, `update --offline`, `update --expect-plan-hash H` on a cold or moved cache | No fetch; cold consumers `blocked` with `requires_fetch`; guarded rerun binds the reviewed candidate or `plan.stale` |
| U05 | Consumer pinned to a tag; tag moved upstream; `update` | `lock.ref_rebound` refuses the invocation; `--allow-ref-rebind` applies it |
| U06 | Empty registry; `update` | Exit 0, warning `project.empty_registry`, no fetch |
| U07 | One consumer in dev-link mode | Unscoped `update` skips it with `dev_link.active` warning; `update --project` on it refuses |
| U08 | `source fetch` with no name | Every approved tap fetched; nothing deployed |
| U09 | Links before and after every update case | All owned links resolve under `MASK_HOME/store/v1/`; a test enumerates every link producer |

## Migration cases

| ID | Starting state and public operation | Required observation |
|---|---|---|
| M01 | v1 fixture machine with legacy project, legacy personal scope, unregistered v1 declaration; `doctor` | `data.migration.required`, `machine: legacy_v1`, proposed tap alias `agentskills`, per-consumer rows and link states; `--check` exits 7 |
| M02 | M01; `doctor --migrate --dry-run` | Full disclosed plan; snapshot of `MASK_HOME` and consumers unchanged |
| M03 | M01; `doctor --migrate` | Config v3 with the clone as tap (`authoring` = clone path), v2 declarations, locks at clone HEAD, cache holds `refs/mask/frozen/<head>`, links retarget to the store, records `mode: pinned`; `doctor --check` exits 0 afterwards; clone HEAD, index and worktree unchanged |
| M04 | v2 fixture machine (legacy binding plus one extra tap); `doctor --migrate` | Alias stays `legacy`; the extra tap and any v2 consumers untouched |
| M05 | M03 interrupted at every journal checkpoint (intent, unlinked, declaration, lock, config, state) | `recover --rollback` restores exact prior bytes and links; `recover --complete` finishes; never both |
| M06 | v1 machine with empty registry; `doctor --migrate` | Config v3 only; no cache, store or link effects; dirty clone is a warning |
| M07 | Dirty, unborn, detached, diverged or missing clone with consumers present | `source.dirty`, `migration.unborn`, `source.identity_mismatch`, `source.missing`; nothing written |
| M08 | Clone without a remote | `file` identity tap plus warning `migration.local_only_source` |
| M09 | Alias already bound to a different repository | `source.alias_conflict`; `--alias other` succeeds |
| M10 | HEAD not pushed to the remote-tracking branch | Migration succeeds with warning `migration.unpublished_commit` |
| M11 | v3 machine; unregistered v1 `.mask.json`; `doctor --migrate --project P --alias agentskills` | Declaration rewritten to v2, resolved (fetching unless `--offline`), registered and linked |
| M12 | Journal written by the new program read by the previous program | `recovery.conflict`; no state change |

## Documentation and native cases

| ID | Starting state and public operation | Required observation |
|---|---|---|
| D01 | `mask --help`, `mask update --help`, `mask doctor --help`, every command's help | Renders; names no retired command |
| D02 | README recipes replayed through the public CLI on the tap-first fixture | Every recipe completes as written |
| D03 | Documentation grep test | Retired spellings only under `docs/rfcs/assets`, historical RFC text and the migration guide's old-command table |
| N01 | `scripts/qualify_real_package.py` on native Windows 11 and macOS | Passes with `tap add`, push-then-update and the legacy-lab steps; report names OS, Python, Git and MASK revisions |
| N02 | Owner's real v1 machine (attended) | `doctor`, `--migrate --dry-run`, `--migrate`, `install implement-rfc --user`, `update`, `doctor --check` 0; clone untouched; transcript recorded |
| G01 | `python scripts/verify_documentation.py --root .` and full `python -B -m unittest` on both platforms | Zero violations; suite green |

## Reporting and test economy

Record each acceptance criterion with its exact command or observation, outcome,
implementation revision and relevant limitation. Cases can share one fixture
journey where that is clearer. Reuse unchanged results. A focused regression
that actually fails before the fix is stronger than another broad label. Keep the
closeout open when a native lane or the owner migration was not exercised.
