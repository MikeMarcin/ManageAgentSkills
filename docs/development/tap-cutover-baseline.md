# Tap cutover baseline (MASK-0098)

Pre-implementation record for RFC-MASK-0020. None of this is a product pass. It records the live-checkout behavior that later cards retire, and the legacy starting states their migration tests use.

## Revision and host

- RFC_BASE_SHA is `b92372f224c04368b6f76d50c0312d95f8035ff3`. Product sources at HEAD `1f93ab0` are byte-identical to it: `git diff --quiet b92372f HEAD` over the program, schemas, tests, scripts, README and guides. Between the two commits come only the pack import, plan adoption and the MASK-0098 claim.
- Host: Windows 11 Home 10.0.26200 (build 26200.9445), Python 3.14.6 (MSC v.1944, AMD64), Git 2.55.0.windows.3.
- Every CLI call used a disposable `MASK_HOME` and a fixture personal home (`USERPROFILE` and `HOME`). The owner's `~/.mask` was neither read nor written by these runs.
- macOS was not exercised for this card.

## Source reconciliation

The 17 SHA-256 values in the retained [SOURCE_BASIS.md](../rfcs/assets/mask-corrective-managed-taps/SOURCE_BASIS.md) do not match the Git blob bytes at the base. They match this Windows checkout's working-tree bytes, which are CRLF because `core.autocrlf=true`. Blob content is unchanged since the packet's source commit, so the packet's observed source facts apply. When comparing those checksums on another host, hash the CRLF working copy, not `git show` output.

## Legacy starting states

`tests/legacy_support.py` `build_legacy_machine(base, version)` writes the following without running MASK:

| State | Bytes written |
|---|---|
| v1 machine | `config.json` schema 1: `source.root` is the clone, remote `origin`, branch `main`, targets `claude` and `codex`, Git timeout 30 |
| v2 machine | The v1 block plus `legacy_source: legacy`. `sources.legacy` has the clone's `origin` URL as a `file` identity and `authoring` set to the clone. `sources.extra` is an empty local bare repository with `authoring: null` |
| Legacy project | `project with ü spaces/.mask.json` v1 (`alpha`) and a mode-less state record. Real directory links `.claude/skills/alpha` and `.agents/skills/alpha` point to `<clone>/skills/alpha` |
| Legacy personal scope | `MASK_HOME/user.json` v1 (`beta`), a state v2 `user` record, and the same two links under the personal home |
| Unregistered v1 declaration | `unregistered project/.mask.json` v1 (`alpha`), with no record and no links |

The clone is pushed to a local bare `upstream/AgentSkills.git`, so `refs/remotes/origin/main` equals HEAD. Options produce three variants: an empty registry (pass `None` for each consumer), a clone without a remote, and a v2 machine without the extra tap.

The builder never prepares effects that later cards must prove. It writes no cache (`MASK_HOME/sources`), store, lock, pending journal or v2 declaration, and it does not register the unregistered declaration. It also omits `operation.lock`, the base program's one-byte writer-lock file, which the byte comparison ignores.

`LegacyFixtureBytes` in `tests/test_legacy_baseline.py` checks three things for every state:
- Each file parses with `mask_core.config`, `mask_core.state` or `mask_core.manifest` to an equal value, and re-serializes to identical bytes.
- Keys follow `schemas/machine-v1.schema.json` or `machine-v2.schema.json`.
- Each link is a real directory symlink whose text equals its record and which resolves to `<clone>/skills/<id>`.

If legacy reading moves into the migration modules (MASK-0100 and MASK-0102), these parser assertions move with it. The fixture bytes stay the same.

## Recorded defects

`LiveCheckoutBaseline` drives the public CLI as a subprocess. Observations are from the base program on Windows.

| Command | Observation | Retired by |
|---|---|---|
| `mask init --source <clone> --json` | Exit 0. `config.json` is schema 1 with `source.root` set to the clone. State is schema 1, generation 0 | MASK-0099 |
| `mask install alpha --project <P> --json` | `<P>\.claude\skills\alpha` and `<P>\.agents\skills\alpha` have link text `\\?\<base>\AgentSkills\skills\alpha`. `.mask.json` is schema 1. The record is mode-less, with `last_source_revision` equal to the clone HEAD | MASK-0100 |
| `mask install beta --user --json` | `<personal>\.claude\skills\beta` and `<personal>\.agents\skills\beta` link to `\\?\<base>\AgentSkills\skills\beta`. `user.json` is schema 1; state becomes schema 2 | MASK-0100 |
| Write `<clone>\skills\alpha\unreviewed.md` (no MASK command) | The new file is readable at once through both project links | MASK-0100 |
| `mask source migrate --json`, then `mask tap add extra <bare> --json` | Config schema 2 keeps `source.root` and sets `sources.legacy.authoring` to the clone. Every consumer link still points into the clone, records stay mode-less, and no cache directory exists | MASK-0100, MASK-0102 |
| The same `init --source` and `source migrate` on a clone without a remote | `sources.legacy` uses the clone's own `file` identity as repository and the clone path as transport | MASK-0102 |
| `mask migrate --to-pinned --project <P>`, push upstream, then `mask update --project <P> --json` | Exit 4 `lock.resolution_required` ("Approved source has no cache"). The lock is unchanged and no cache is created | MASK-0101 |
| `mask source fetch legacy`, push upstream again, then `mask update --project <P> --json` | Exit 0, `changed: false`. The lock stays at the cached commit, cache refs are unchanged, and the new upstream commit is absent from the cache. Only another `source fetch legacy` lets `update` move the lock | MASK-0101 |

Each CLI test then removes exactly the files and links the program wrote, has the builder write the same state again, and compares a snapshot. The snapshot covers the bytes of `config.json`, `state.json`, `user.json` and each declaration, plus every link text.

MASK-0099 removed `init --source` (it now exits 2 `invocation.invalid`). The `init --source` rows above were observed on the base program at `82b4200`, where its configuration and state bytes equalled `v1_config` and `legacy_state`. From MASK-0099 on, `LiveCheckoutBaseline` starts from those builder bytes. The remaining legacy commands (`install`, `source migrate`, `tap add`, `migrate --to-pinned`, `update`) still run through the CLI and are compared as before. Test fixtures that exercise retired behavior use the same bytes through `tests/support.py` `legacy_init` and `tests/public_support.py` `legacy_bootstrap`.

The snapshots are identical in three cases:
- the v1 machine with a project and a personal scope
- the v2 machine with an extra tap
- the empty-registry machine on a clone without a remote

## Runs

- `python -B -m unittest tests.test_legacy_baseline -v`: 7 tests OK in 55 s on Windows. The implementation commit is recorded on MASK-0098.
- Negative controls: a scratch harness patched one builder function per case and restored it afterwards. The unpatched control passed. Each defect failed at least one test:

  | Injected defect | Failing check |
  |---|---|
  | Generation off by one | The v1 CLI comparison and the v1 bytes test |
  | Windows link text without the `\\?\` prefix | The v1 CLI comparison |
  | A `mode` field on a legacy record | `mask_core.state` (`Unexpected or missing fields`) |
  | Catalog `ref` spelled `refs/heads/main` | The v2 CLI comparison |

  Limitation: the remote-less CLI test compares against the test module's own `legacy_state` reference, so the generation patch did not reach it.
- Windows reference run of the existing suite at `1f93ab0`: **incomplete**. It ran every module except the new one in a single process, with `USERPROFILE` and `MASK_HOME` redirected to empty disposable directories. It was stopped after 32 minutes because progress had slowed to about two tests per minute; it is not an exit criterion for this card.
  - The owner's real profile snapshot was identical before the run and after the stop. The snapshot covers `~/.mask` file hashes and the skill, agent and launcher entries.
  - The first 155 results ran before the stop, through `tests.test_pin_migration`. These existing tests failed on unchanged product code; they are not diagnosed here:
    - `test_compatibility`:
      - `PolicyModelTests.test_closed_policy_authority_and_device_conditions`: error `Integers must be nonnegative JSON-safe integers`
      - `CompatibilityTests.test_final_policy_edits_retain_partial_recovery`: two failing subtests
      - `test_override_is_reasoned_physical_scope_local_and_cannot_enable` and `test_recovery_rederives_links_from_effective_after_policy`: `selection_policy.invalid` or unexpected exit codes
    - `test_git_integration.GitIntegrationTests.test_interrupted_install_is_recoverable`: `integration.drift`, exit 4 where 8 was expected
    - `test_pin_migration.MigrationTests.test_project_migration_preview_targets_and_unselected_preservation`: asserts a `/store/v1/` substring against a backslash Windows path
  - The results after the stop are not a reference. In 209 entries a child process exited `0xC0000142` (DLL initialization failed) while the stop tore down the console. One empty-stdout error in `test_pinned_recovery` came from the same burst. The summary `Ran 374 tests, failures=15, errors=202, skipped=18` therefore overstates failures. Modules from `test_pinned_recovery` onward are unobserved on Windows.
- **Complete Windows reference at `d05bad8` (MASK-0099, dispatch d2):** product sources are identical to RFC_BASE_SHA.
  - Method:
    - The reference ran in a disposable clone. Each of the 43 `tests.test_*` modules ran as its own `python -B -m unittest -v tests.MODULE` process, three at a time, for 27.6 minutes of wall time.
    - Each process had `MASK_HOME`, `USERPROFILE` and `HOME` redirected to empty per-module directories.
    - The owner's profile snapshot (`~/.mask` hashes and the skill, agent and launcher entries) was identical before and after.
  - Result: 381 tests, 19 skipped.
  - Load defect: `tests.test_imports` and `tests.test_provenance` cannot load in a process of their own. `mask_provenance` → `mask_git` → `mask_fs` → `mask_pinned` → `mask_resolve` imports `regular_bytes` back from the half-initialized `mask_provenance`. A single discovery process hides this because another module imports `mask_resolve` first. With `mask_resolve` imported first, those modules ran 8 and 6 tests OK.
  - Ten existing tests fail on unchanged code. The first six are the ones above. The last four are in modules the stopped run never reached:
    1. `test_compatibility`: `PolicyModelTests.test_closed_policy_authority_and_device_conditions`
    2. `test_compatibility`: `test_final_policy_edits_retain_partial_recovery`
    3. `test_compatibility`: `test_override_is_reasoned_physical_scope_local_and_cannot_enable`
    4. `test_compatibility`: `test_recovery_rederives_links_from_effective_after_policy`
    5. `test_git_integration.GitIntegrationTests.test_interrupted_install_is_recoverable`: `recover --complete` exits 4 `integration.drift` where 8 is expected
    6. `test_pin_migration.MigrationTests.test_project_migration_preview_targets_and_unselected_preservation`
    7. `test_reconcile_plan.PlannerTests.test_all_unavailable_and_poisoned_state`: `KeyError` on the `project with ü spaces` registry key
    8. `test_pinned_update.UpdateTests.test_isolated_publication_exact_paths_and_separate_push`: the publication commit also lists `skills/alpha/SKILL.md`
    9. `test_selection_conflicts.PublicConflictTests.test_public_scope_shadowing_warns_when_the_scopes_resolve_to_different_targets`: `git commit` in a second clone exits 128
    10. `test_workflow_roles.StaticRoles.test_fresh_clone_with_tracked_roles_passes_without_adoption`: `ensure` reports every tracked role in a fresh clone as `modified`
  - Root causes are recorded on MASK-0099. Scratch logs and the runner are not retained in the repository.
