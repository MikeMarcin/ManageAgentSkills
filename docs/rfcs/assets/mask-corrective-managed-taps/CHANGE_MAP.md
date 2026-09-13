# Correction map

| Existing boundary | Deliberate amendment | Retained invariant |
|---|---|---|
| `init --source PATH` records the user's clone as the machine's live source | `init` takes only defaults; `tap add NAME URL` bootstraps the machine | Machine, program and consumer roots stay distinct; no privilege change |
| Machine config v1/v2 require a `source` block; v2 also requires `legacy_source` bound to it | Machine config v3 is a catalog only; v1/v2 are readable for migration and refused everywhere else | Tap entry shape, cache derivation, identity normalization and credential refusal |
| Legacy consumers link `<consumer>/<agent path>/<id>` to `<clone>/skills/<id>` | Every link targets `MASK_HOME/store/v1/...`; only `source dev-link` may target a checkout | Ownership records, drift/collision refusals, journaled link changes |
| New consumers on a v1 machine are legacy (`fresh_declaration`) | New declarations are always v2 with an empty lock | Set union/subtraction, scope independence, unrelated pins retained |
| `update` without scope fast-forwards the user's clone and relinks all legacy consumers | `update` fetches each referenced tap once, resolves every consumer from cache, isolates failed taps, applies one journal | Selector versus lock rule, ref-rebind approval, dry-run and offline never fetch |
| Pinned `update` resolves from cache only | Fetch phase precedes resolution unless `--dry-run`, `--offline` or `--expect-plan-hash` | Guarded rerun binds the reviewed candidate; `plan.stale` on change |
| `source migrate` (machine) and `migrate --to-pinned` (per consumer) | `doctor --migrate` converts the machine and every registered legacy consumer in one journal; `doctor` reports what it would do | Clean-clone requirement when HEAD is locked, exact-byte rollback, typed refusals |
| `checkout_preconditions` basename check against `AgentSkills` | Removed; identity is the normalized repository URI of the tap | `self update` keeps its `ManageAgentSkills` program check |
| `source status` reports the live checkout | Removed; `source list`/`show`/`fetch` report caches | Fetch-only commands never deploy |
| Docs and fixtures bootstrap through `init --source` | Docs, fixtures and the qualifier bootstrap through `tap add` | Public CLI as subprocess is the acceptance surface |

## Module inventory

**Removed:** `init --source/--remote/--branch`; commands `source.status`,
`source.migrate`, `migrate`; `mask_git.update`, its `recover_git` source scope,
`candidate_packages`, `explicit_selection` and every `'AgentSkills'` literal;
the legacy tail of `mask.local_dispatch` (v1 `skill list/show/validate`, legacy
`source fetch`); the `diagnostics` checkout probe; v1 branches of
`project_dispatch`; `mask_task.v1_proposal`, `legacy_alias` and the `listing`
legacy branch; the `mask_fs.plan` legacy link branch, `adopt` legacy branch and
`recover` package loop; `mask_pinned.target` checkout case, `authoring_snapshot`,
`migrated_selection`, `validate_migration`, `check_migration` and
`transition_dispatch` (ported into the new modules); `mask_core.package`,
`catalog` and `registry_record`; `mask_resolve.guard_command` v1 branches;
`mask_report` legacy alias and `inventory.pinned_unsupported`; `mask_present`
help for retired commands; `scope.expand` consent for updates.

**Added:** `mask_update.py` (fetching, isolating update), `mask_legacy.py`
(read-only legacy detection), `mask_migrate.py` (doctor migration and its
journal validation), `schemas/machine-v3.schema.json`, `tests/legacy_support.py`,
`tests/test_update.py`, `tests/test_doctor_migration.py`, a retired-spelling
documentation test, `docs/development/tap-cutover-baseline.md`.

**Retained unchanged:** `source dev-link`, `source publish`, `skill import`,
`skill provenance`, `skill record-adaptation`, `lock`, `source fetch NAME`,
`source fetch --locked`, `source inspect/list/show`, `tap add/remove` semantics
apart from bootstrap, `project init`, `project/user set-targets`, `set-agents`,
`set`, `require`, `unrequire` (v2 only), `selection-policy`, `compatibility`,
`ensure`, `integration.*`, `launch`, `link adopt` (pinned branch), `recover`,
`self *`, store and cache limits, the pending v3 journal apart from its
operation enumeration.

Update current AGENTS.md, project.md, CLI contract, state-and-recovery,
test-boundaries, help, capabilities and README where the implementation changes
their instructions. Leave settled RFC text and historical closeout evidence
unchanged; RFC-MASK-0020 explicitly amends the applicable clauses of 0003, 0007,
0008 and 0018.
