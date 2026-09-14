---
schema: "implement-rfc.card.v1"
id: "MASK-0106"
title: "Verify and close tap-only deployment"
status: "Backlog"
rfcs: ["RFC-MASK-0020"]
depends_on: ["MASK-0104", "MASK-0105"]
priority: "P1"
metadata: {"packet":"mask-corrective-managed-taps","provisional_id":false,"packet_key":"close-tap-only-deployment","milestone_plan":{"id":"tap-only-deployment","path":"docs/rfcs/plans/tap-only-deployment/milestone-plan.json"}}
closeout_for: ["RFC-MASK-0020"]
---

# MASK-0106: Verify and close tap-only deployment

Governing RFC: [RFC-MASK-0020](../../rfcs/RFC-MASK-0020-tap-only-deployment.md). Live IDs confirmed by the committed pack reservation `b92372f`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-managed-taps.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-managed-taps/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-managed-taps/ACCEPTANCE.md).

## Current frontier

**Dispatch `d7` checkpoint (milestone `qualification` in progress; start of dispatch).**
- Run `mask-rfc0020-2026-09-12-a`, producer `rfc-integrator-d7`, mandate revision `4`. The mandate is unchanged.
  - No push or publication is authorized. The owner's real `~/.mask` and global install are not changed. MASK-0105 is prepared but not run.
- **Binding** (`coordinator_handoff.py assign --milestone qualification`, with `baseline` to `truth` passed as accepted):
  - definition `sha256:aa93e809be657bee51b52964c541773e113e7fd308c172d9a51c3b24e6c5534f`
  - obligation `sha256:9f77f7a7a5220b905d239cf6f968f11e52b5c0ca7070e9c477d6eca1f37d5f2b`
  - prerequisite `sha256:dbbeb5f755f54376c25b2e6b4eaeab4ee3c9825debe46321a34226dd0b641875`
  - The assignment is `d7-assignment.json` in the ignored run directory. Without `--accepted-milestone`, `assign` answers `reconcile`.
- **Board:** MASK-0108 to MASK-0110 promoted at `7bd13fe`. Claims: MASK-0104 `c354a59`, MASK-0108 `72f13e2`, MASK-0109 `47a5105`, MASK-0110 `4e8af51`. MASK-0105 stays Ready until its attended ask is prepared.
- **Facts found:**
  - The global launcher `%LOCALAPPDATA%\Programs\MASK\mask.cmd` runs `C:\code\git\ManageAgentSkills\mask.py`, this main checkout. The owner's `mask` therefore runs whatever the main working tree holds. Product slices work in separate worktrees, and MASK-0105 must run on a clean tree at the recorded candidate.
  - The host is `JaegAW`: Windows 11 Home 10.0.26200, Python 3.14.6, Git 2.55.0.windows.3, system `core.autocrlf=true`. It is not the registered station host ExampleWinHost.
  - The station registry authorizes only the Windows station `mask-win-example-win-host` and names no macOS station. The earlier macOS evidence was run from an integrator on a Mac. No macOS path is authorized from this host.
  - The real AgentSkills clone is at `16192b76ec1bbaee001c718d3e82d447db4f25c5` on `main`, clean, with origin `git@github.com:MikeMarcin/AgentSkills.git`. The qualifier only clones it.
- **Planned slices:**
  - W1 `rfc-worker`: the MASK-0104 qualifier rewrite, `scripts/qualify_real_package.py` only. It runs against disposable clones.
  - W2 `rfc-worker`, worktree: MASK-0108.
  - W3 `rfc-worker`, worktree: MASK-0109 and MASK-0110 together, because they share the cold-store preparation and result-reporting code.
  - R1 `rfc-reviewer-critical`: a retry of the MASK-0107 review on the configured route. Q6 (an alternate reviewer route) stays with the owner.
- **Next:** collect W1 to W3 and R1, integrate on main, then run the Windows qualifier on the final candidate. macOS stays pending. Then prepare the MASK-0105 ask.

**Dispatch `d6` record (milestone `truth` accepted; MASK-0103 Done).**
- Run `mask-rfc0020-2026-09-12-a`, producer `rfc-integrator-d6`, mandate revision `4`. The mandate is unchanged.
  - No push or publication is authorized. The owner's real machine changes only through attended MASK-0105.
- **Accepted milestone `truth`:**
  - MASK-0103 was claimed at `cf8c725` and implemented at `4285146`; Done at `410733a` (evidence record `78f68c7`).
  - The d6 checkpoint is `b00d107`. MASK-0104 and MASK-0105 were promoted to Ready in the commit that records this frontier.
  - **Exit 1** (README recipes replay verbatim): `tests.test_readme_journeys`. It pins every fenced block and Everyday row and replays them through the launcher of a disposable program clone on a fixture tap. It fails against the README of `b00d107`.
  - **Exit 2** (the retired-spelling test passes): `tests.test_retired_spellings`. At `cf8c725` it had 6 failures (docs, the old-command table, dead presentation entries); at `4285146` it passes.
  - **Full suite on `4285146`:** guarded per-module run with 4 workers: 49 of 49 modules, 438 tests, 16 skipped, 2439 s. HEAD, tree status and the owner profile snapshot were unchanged. Only Windows 11 was exercised (Python 3.14.6, Git 2.55.0.windows.3), and this was not the literal single-process run. The summary is `d6-suite/out/summary.json` in the d6 session scratchpad.
  - Evidence: the [MASK-0103 execution record](../60-done/MASK-0103-help-docs-and-capabilities-truth.md#execution-record). The structure gate reports 0 violations.
- **Binding** (unchanged from dispatch to finish):
  - definition `sha256:71edb75ce31f56f93508fd3e51215f3258d810d56e932d2d7b8b22d62c5066eb`
  - obligation `sha256:36e421d5640b89b8d365caf8e3bc9cd2d8fa5c128cc74377a75857339a3d2e60`
  - prerequisite `sha256:8ab8bfb6f05b93d38cae2665c74bbd1b284a3204f882aa796c764ff11445d497`
  - The assignment, the finish decision and the return are in the ignored run directory as `d6-*`.
- **Product state the next milestone inherits:**
  - Help, README, guides, CLI contract and state/recovery architecture describe only taps, the fetching update and doctor migration.
  - The migration guide ("Migrating from a live checkout") holds the only old-command table.
  - `project/user set|require|unrequire` refuse `selection.command_unsupported` and point to `install`/`remove` (Q4).
  - `tests/test_retired_spellings.py` guards help, `capabilities` and current Markdown. Its historical exemptions are `docs/rfcs/`, `docs/issues/`, `docs/releases/` and two baseline reports under `docs/development/`.
- **For MASK-0104:** `scripts/qualify_real_package.py` still uses the retired `init --source` (d2 note) and `project unrequire` (lines 315 and 331), which now refuses on v2 declarations.
- **Contract notes for the closeout:**
  - The RFC rollout sentence is historical. `b92372f` fails `config.invalid` on a v3 machine, and the previous tap-era program refuses `line_endings` entries (`source.invalid`). Neither recovers this program's `update` journal, and the contract says so.
  - On a tap machine, the consumer-level `migration.required` remediation omits the `--project PATH --alias NAME` it needs there. It is left as is under Q5.
- **Review:**
  - **MASK-0103:** no independent review. It is a presentation, documentation and refusal-message change with no persistence, authority or destructive risk, and no reviewer route is available.
  - **MASK-0107:** the d6-R1 `rfc-reviewer-critical` retry, the third attempt, failed before output with "You've reached your Fable limit" (HTTP 429, `claude-fable-5-1`). Both reviewer roles bind that model, and no fallback is authorized.
    - **Judgment:** the review remains warranted. MASK-0107 changes persisted tap policy and the refusal before `source publish`, which can commit and push, and the owner's clone migrates as an exact tap in MASK-0105.
    - It should run before the attended MASK-0105 migration: retry when the Fable limit resets, or get the owner's authorization for another reviewer route.
- **Route observations:**
  - This integrator session exposes model `claude-opus-5[1m]` with runtime reasoning effort `40`, against the configured xhigh. That difference is unresolved.
  - Every leaf was dispatched by generated role with no model or effort override.
  - Banners: W1, W2, W4 and W5 `claude-opus-5`, xhigh; W3 `claude-opus-5[1m]`, effort `40`. R1 was served as `claude-fable-5-1` and failed with HTTP 429.
- **Execution state:**
  - Every d6 child (W1 to W5, R1) has returned or failed terminally.
  - The guarded suite command finished, and no d6 command or child is active.
  - Logs are in the d6 session scratchpad (`d6-w1` to `d6-w5`, `d6-integ`, `d6-suite`).
  - `git worktree list` shows only the main checkout. R1 created no scratch directory.
- **Next:** start a fresh integrator context for milestone `qualification` (MASK-0104, MASK-0105; both Ready).
  - MASK-0104 needs native Windows 11 and macOS lanes against the real AgentSkills repository as a tap.
  - MASK-0105 is the attended migration of the owner's real machine.
  - Before MASK-0105, resolve the MASK-0107 review. The authorized follow-ups MASK-0108 to MASK-0110 remain eligible independent work.

**Dispatch `d5` record (historical; MASK-0107 accepted and Done; its next milestone `truth` is d6's).**
- Run `mask-rfc0020-2026-09-12-a`, producer `rfc-integrator-d5`, mandate revision `3`. Amendment r4 arrived during the dispatch.
  - The mandate is unchanged. No push or publication is authorized.
  - The owner's real machine changes only through attended MASK-0105.
- **Plan position:** MASK-0107 (`rfcs: []`) is outside the adopted plan.
  - `milestone_plan.py discover --target MASK-0107` reports `absent`, and `coordinator_handoff.py assign` refuses without a plan.
  - `check-amendment` refuses adding MASK-0107 to the scope ("cannot change plan identity or authorized scope") and to `unplanned_work` ("must preserve every obligation").
  - It therefore ran as mandate-authorized work against its own card acceptance. The plan is unchanged.
  - The probe record is `d5-plan-position.json` in the ignored run directory.
- **Accepted MASK-0107:** claim `6496967`, implementation `4c0549f`, and Done in the finish commit that follows `0be6b26`.
  - Evidence and limitations: the [MASK-0107 execution record](../60-done/MASK-0107-tap-line-endings-exact-bytes.md#execution-record).
  - **Checks (Windows 11 only):**
    - `tests/test_tap_line_endings.py` passes 16 tests on the committed content, and every `tests/test_*.py` module passes.
    - Negative controls on an archive of `6496967` fail (publish previews `would_change: true`; the module gets 7 failures and 22 errors).
    - The structure gate reports 0 violations.
  - **Independent review was not performed.** `rfc-reviewer-critical` (`claude-fable-5-1`) hit an account usage limit (HTTP 429) on both attempts, and no model fallback is authorized.
- **Product state the next milestone inherits:**
  - Tap entries carry `line_endings`: `exact` by default, `autocrlf` only through `tap add --autocrlf`. `doctor --migrate` writes `exact`.
  - For an exact tap, `source publish` and a new `source dev-link` refuse `source.line_endings_converted` for Git-converted unedited files. `tap add --checkout` warns `source.line_endings_conversion`.
  - The remediation is to set `core.autocrlf false` in the checkout, delete the reported files, then run `git checkout -- PATH`. `checkout-index --force` leaves a stat-clean converted file in place.
  - `source dev-link` reports `data.development[].payload_digest`. Test fixtures author LF bytes.
  - For MASK-0104 and MASK-0105: the owner's AgentSkills clone migrates as an exact tap. Its CRLF working copies would refuse publishing and new dev links until restored or re-registered with `--autocrlf`. The migration steps themselves do not publish.
- **Owner decisions r4** (recorded at `0be6b26` on the RFC and on [MASK-0103](../60-done/MASK-0103-help-docs-and-capabilities-truth.md#owner-decisions-mandate-r4-september-13-2026)):
  - **Q4:** v2 set/require/unrequire are not implemented. The refusal remains, and MASK-0103 points it, the help and the contract to `install`/`remove`.
  - **Q5:** migration is best effort. The AC05 gate is unchanged, and MASK-0103 briefly documents restoring an unconvertible consumer on disk.
  - d4's migration notes are closed unless they block MASK-0105. No acceptance text is narrowed.
  - No owner question remains open.
- **Route observations:**
  - This integrator session exposes runtime reasoning effort `40` against the configured xhigh, an unresolved observation carried over from d4.
  - `d5-B1` was dispatched as `rfc-worker` with no model or effort override, and its banner reads `claude-opus-5`/xhigh. It stopped at its 56-turn limit, was resumed once, and completed.
  - `d5-R1` and `d5-R1b` were dispatched as `rfc-reviewer-critical` with no override. Both failed before producing output.
- **Execution state:**
  - Every d5 child has returned or failed terminally, and every d5 background command has completed.
  - No worker shell or `unittest` process remains.
  - Logs are in the d5 session scratchpad.
- **Next:** start a fresh integrator context for milestone `truth` (MASK-0103, Ready), which r4 unblocks. `qualification` (MASK-0104, MASK-0105) waits on it.

**Dispatch `d4` record (historical; its recommended next objective, MASK-0107, was completed by d5).**
- Run `mask-rfc0020-2026-09-12-a`, producer `rfc-integrator-d4`, mandate revision `3`.
  - The mandate is unchanged: `/implement-rfc RFC-MASK-0020`, with no added stop conditions.
  - r3 places no restriction on implementing MASK-0107 to MASK-0110.
- No push or publication is authorized. The owner's real machine changes only through attended MASK-0105.

- **Accepted milestone `migration`:**
  - MASK-0102 is Done at `645b3c0`.
  - Implementation: `e28d615` (doctor report), `5215741` (machine migration), `fe9c13a` (tap-machine path and review hardening). The evidence record is `d621bdc`.
  - MASK-0103 and MASK-0107 were promoted to Ready at `6e2326f`; the links that promotion repaired are committed with this record.
  - **Exit 1** (the fixture crash matrix recovers with rollback or complete at every checkpoint):
    - `tests.test_doctor_migration` `test_crash_at_every_checkpoint_rolls_back_exactly_or_completes` covers seven checkpoints.
    - `tests.test_doctor_straggler` `LegacyRecordOnTapMachine` covers the tap-machine journal.
    - Negative control: a rollback that skips `machine_config` fails.
    - Review R1 also completed the migration from every checkpoint.
  - **Exit 2** (an empty registry migrates its configuration only): `test_empty_registry_migrates_configuration_only`.
  - **Full suite on `d621bdc`:**
    - guarded per-module run, 4 workers: 47 of 47 modules, 413 tests, 16 skipped, 2687 s;
    - HEAD, tree status, tracked index and owner profile were unchanged;
    - only Windows 11 was exercised, and this was not the literal single-process run.
  - Evidence: the [MASK-0102 execution record](../60-done/MASK-0102-doctor-migration.md#execution-record).
- **Binding** (unchanged from dispatch to finish; each recomputed assignment matched every value):
  - definition `sha256:445ea1fc2709589c20b25ad52d356075f62b7cd3f2a22f9772a393e571d964f6`
  - obligation `sha256:3b1373c09a1afd12769793c33ca42785edfe4f6b256cdcc32135d0439faab981`
  - prerequisite `sha256:c0763bebfa7700e8d261bce15d6adc0a9468c1a026e93b0138175381445dcb14`
  - The assignment, the finish decision and the return are in the ignored run directory.
- **Product state the next milestone inherits:**
  - **`doctor` report:** `data.migration` on v1, v2 and tap machines. `--check` exits 7 while migration is required.
  - **v1/v2 machine:** `doctor --migrate`, unscoped or with `--all`, converts the machine configuration and every registered legacy consumer in one `doctor.migrate` journal.
    - `--dry-run` and `--expect-plan-hash` bind the plan.
    - With an empty registry, only the configuration migrates.
    - The clone's HEAD is acquired over file transport into `refs/mask/frozen/<head>`, and the cache and store effects are retained.
  - **Tap machine:** `doctor --migrate --project PATH --alias NAME` (or `--user --alias NAME`) converts an unregistered v1 declaration, or a registered legacy record with a v1 declaration, using install semantics.
  - **Surfaces:**
    - `capabilities` publishes `migration: doctor`, and `doctor` is plan-guarded.
    - `mask doctor --help` names `--migrate`. README, the guides and other help still name retired commands (MASK-0103).
  - **MASK-0107:** migrated tap entries don't carry a line-ending field yet. That card should make migration write its exact-bytes default.
- **Pending owner decisions:**
  - **Q4 (unchanged):** implement v2 `project/user set|require|unrequire`, or amend the contract to keep `selection.command_unsupported` and point to `install`/`remove`? Details below; needed before MASK-0103 describes these commands.
  - **Q5 (new):** on a v1/v2 machine, the AC05 gate refuses the MIGRATION.md blocker remediations (`project unregister --keep-links`, `workspace forget`).
    - The ask: exempt them from the gate, which amends AC05? Or keep the gate, and document that a consumer which can't be migrated must first be restored on disk?
    - The gate is unchanged. This blocks nothing accepted. It affects MASK-0103's documentation, and MASK-0105 only if the owner's machine held such a consumer; its registry is empty.
- **Notes for later cards** (from review R1 and worker B2):
  - Plain `doctor` on a legacy record with a v2 declaration and no lock stops at `lock.missing` before reporting, because of guard order.
  - Completing a migration rechecks the clone's HEAD, index, branch and remote, but not worktree cleanliness.
  - After preparation, `plan.stale` reports `transaction: partial`, because retained cache and store effects are merged in. MASK-0103 should document this.
  - `diverged` refuses `source.identity_mismatch` with reason `diverged`.
  - A legacy record with a v2 declaration refuses with the new code `migration.declaration_unsupported`.
- **Route observations:**
  - Every leaf was dispatched by generated role with no model or effort override.
  - Banners: B1 `claude-opus-5[1m]`, xhigh; B2 `claude-opus-5`, runtime reasoning effort `40`; R1 `claude-fable-5-1`, high.
  - This integrator session also shows reasoning effort `40` against the configured xhigh. That difference is an unresolved observation.
- **Execution state:**
  - Every d4 child (B1, B2, R1) has returned, and every background command was consumed. No command or child from d4 is active.
  - Logs remain in the session scratchpad (`b1/`, `b2/`, `r1/`, `integ/`).
- **Next:** a fresh integrator context.
  - Recommended first: MASK-0107 (exact-byte taps). It is Ready, independent of Q4 and Q5, and required before qualification.
  - Then milestone `truth` (MASK-0103, Ready), once Q4 is answered.

**Dispatch `d3` record (historical; its next milestone `migration` was accepted by d4).**
- Run `mask-rfc0020-2026-09-12-a`, producer `rfc-integrator-d3`.
- The mandate is still `/implement-rfc RFC-MASK-0020` with no added stop conditions. The coordinator's amendments r2 and r3 answered the three decisions d2 left open; see Owner decisions below.
- No push or publication is authorized. The owner's real machine changes only through attended MASK-0105.

- **Accepted milestone `engine`:**
  - MASK-0100 is Done at `e8c3052` and MASK-0101 at `de45c37`.
  - Implementation runs from `d61d4be` to `a62f7c4`, and MASK-0102 was promoted to Ready at `c254bc2`.
  - **Exit 1** (no link producer targets a checkout except `source dev-link`): `tests.test_link_producers`.
    - A static allowlist of every link spelling: `symlink_to`, `os.symlink`, `link_to`, `hardlink_to`, `CreateSymbolicLink` and `mklink`.
    - A CLI journey through every public link producer.
    - A refusal on mode-less records.
    - Negative controls: it fails at `be64043`, and fails again when `pinned.target` is mutated to point at the authoring checkout.
  - **Exit 2** (retired commands are absent from capabilities and exit 2; legacy configuration exits 4): `tests.test_retired_paths`. It covers the retired commands, the migration gate on v1 and v2 builder machines (which exempts `capabilities`, `config show`, `doctor`, `recover` and `self *`), and consumer-level remediation. It fails 5 of 5 at `be64043`.
  - **Exit 3** (`update` fetches each tap once, isolates failed taps and applies one journal): `tests.test_update` cases U01–U09 and `UpdateSafetyOnTaps`, which count Git fetch processes from trace2 events. The module has 10 failures and 1 error at `be64043`.
  - **Full suite on `a62f7c4`:**
    - guarded per-module run: 45 modules, 386 tests, 16 skipped;
    - literal `python -B -m unittest`: exit 0, 386 tests in 8694 s, OK with 16 skipped;
    - HEAD, tree and the code-tree guard were unchanged, and the owner profile snapshot was identical.
    - Only Windows 11 Home 10.0.26200 (Python 3.14.6, Git 2.55.0.windows.3) was exercised.
  - Evidence: the execution records on [MASK-0100](../60-done/MASK-0100-retire-live-checkout-engine.md#execution-record) and [MASK-0101](../60-done/MASK-0101-update-fetch-and-isolation.md#execution-record).
- **Binding** (unchanged; the recomputed assignment matched every value):
  - definition `sha256:e41ecb8e391879ede6dbc0126096ab78d5e8d489dfdb9bb6f48980538036a517`
  - obligation `sha256:ca9ace464b531dd11759bc20c98e3fed090a0e15ae26d3bb9b0ec13db457c20f`
  - prerequisite `sha256:6e3b48d4ed539c1028f2f5db223f859fd9b69b4324ad8b66feb22dbab1a46101`
  - The assignment and return are in the ignored run directory.
- **Product state the next milestone inherits:**
  - **Migration gate:** a v1 or v2 machine config refuses every command except `capabilities`, `config show`, `doctor`, `recover` and `self *` with `migration.required` (exit 4). The details carry `remediation` `mask doctor --migrate --dry-run`.
    - `doctor` reports the issue without planning, and `--check` exits 7.
    - `config show` reports `migration_required`.
  - **Retired paths:**
    - `source status`, `source migrate` and `migrate` exit 2.
    - The `migrate --to-pinned` machinery is gone; MASK-0102 ports it from `0658a40` (`mask_pinned` migration helpers, `mask_sources.migrated_config`, `tests/test_pin_migration.py`).
    - `pinned.target` refuses legacy link records, so doctor migration must derive the old clone targets itself and re-add the `migration` journal field, the `machine_config` role and the pending `doctor.migrate` operation.
    - A retired journal (`migrate`, a `migration` field, a source-scope git entry, legacy ownership) is shown by `recover --inspect` and refused `recovery.conflict`.
  - **Update:** `mask_update.py` owns `update` and no-name `source fetch`. The journal keeps `operation: update`.
  - **Inventory and where-used:** they report pinned rows.
  - **`project init`** without machine config writes an empty v2 declaration.
  - **Fixed in `a62f7c4`:**
    - a project install into the registered personal home now refuses `target.overlap`;
    - a moved registered root refuses `user.unavailable` or `project.unavailable` from `apply`, `ensure` and `source dev-link`;
    - `execute` verifies retained artifacts before writing a journal, and `remove` prepares the old artifacts of the rows it removes.
- **Test state:**
  - All fixtures are tap-first; `tests/legacy_support.py` stays for the doctor tests.
  - `legacy_init`, `declare` and `legacy_bootstrap` are gone.
  - `tests/test_pin_migration.py` and `tests/test_git_update.py` are removed. Coverage of the self update checkout journal moved to `tests/test_launcher.py`.
- **Owner decisions (r2 and r3):**
  1. Taps keep exact bytes, with `core.autocrlf` only on explicit opt-in at tap registration. This is filed as [MASK-0107](../60-done/MASK-0107-tap-line-endings-exact-bytes.md), and MASK-0104 and MASK-0105 depend on it. Recommended order: after `migration`, before `qualification`.
  2. An offline cold single-tap bare ID keeps refusing `source.unresolved`. RFC-MASK-0020 records how retained case B04 reads with this decision.
  3. The d2 follow-ups are filed as MASK-0108 to MASK-0110, outside this RFC.
- **Pending owner decision (new; blocks nothing accepted here; needed before MASK-0103 describes these commands):**
  - Retained `contracts/CLI.md` and the RFC Retirement paragraph say `project/user set|require|unrequire` "remain for v2 declarations" and write a v2 declaration and lock.
  - The product has refused them for v2 declarations with `selection.command_unsupported` since before this RFC, and d3 kept that behavior.
  - The ask: implement v2 set/require/unrequire, or amend the contract to keep the refusal and point to `install`/`remove`?
- **Contract notes for the closeout and later cards:**
  - The RFC rollout sentence is false: the previous program completes a crashed tap-fetching `update` journal with the same outcome instead of refusing it.
  - The update fetch holds the writer lock for the network round (MASK-0103 should document this).
  - A resolution error other than `lock.resolution_required` or `lock.ref_rebound` refuses the whole update (CLI.md step 6).
  - `skill show` no longer refuses a linked package entry (`validate` and `install` do), and `skill.path_escape` has no test.
  - On Windows, a long scratch path gives an untyped `git.failed` when a cache ref path exceeds MAX_PATH (MASK-0104).
  - The `MIGRATION.md` remediations `project unregister --keep-links` and `workspace forget` are gated on v1/v2 machines (MASK-0102).
  - `capabilities.migration: doctor` and the `doctor` plan guard land with MASK-0102.
  - `doctor --project <unregistered>` answers `project.not_registered` before any migration report (MASK-0102).
  - Help, README and guides still name retired commands (MASK-0103).
  - Reviewing a tag- or branch-pinned consumer after a no-name `source fetch` still needs `source inspect --ref`.
- **Execution state:** every d3 child has returned (retirement, update module, inventory, three porting slices, corrections, and the critical review with its follow-up). No command or child from d3 is active, and the consumed worktrees were removed.
- **Next milestone:** `migration` (MASK-0102), in a fresh integrator context.

**Dispatch `d2` record (historical; its next milestone `engine` was accepted by d3).** Run `mask-rfc0020-2026-09-12-a`, producer `rfc-integrator-d2`, mandate revision `1`. The owner's mandate is unchanged: `/implement-rfc RFC-MASK-0020`, with no extra stop conditions. No push or publication is authorized, and the owner's real machine is changed only by attended MASK-0105.

- **Accepted milestone `bootstrap`:** MASK-0099 is Done at `eb2eff8`. The implementation is `01b2ae3` plus the review fix `94d4f1c`. MASK-0100 and MASK-0101 were promoted to Ready at `5ea6f13`.
  - Exit 1: `tests.test_tap_bootstrap` passes 6 tests. On an empty `MASK_HOME`, `tap add` followed by `install` deploys v2 consumers from the store, with one bare cache and no checkout anywhere on disk. Negative controls: the pre-implementation product fails 5 of 5, and a retained author checkout fails the no-checkout assertion.
  - Exit 2: on `94d4f1c`, the literal `python -B -m unittest` ran 391 tests OK (19 skipped) in 6477 s, and the per-module run passed all 44 modules. Tree hashes and the owner profile were unchanged across both. Only Windows 11 was exercised.
  - Evidence: [MASK-0099 execution record](../60-done/MASK-0099-machine-v3-and-tap-bootstrap.md#execution-record) and the complete reference in [tap-cutover-baseline.md](../../development/tap-cutover-baseline.md#runs).
- **Binding** (unchanged from dispatch to finish):
  - definition `sha256:4ffc77d27810b0f701a145961f84312dda7c289c56fad62d42261c1b2c20f0d8`
  - obligation `sha256:ea9a3810366abb09d53d794db32643b9c48d85ae82ed10845bde1288776632b2`
  - MASK-0099 source `sha256:9c05f5be4d20237474037f41814bc40bf7c115e67eaf0c7640d0661cca425717`
  - prerequisite `sha256:256c0a53f234c928aa94807fde2efc3ba3352a9c71bece6414d5effed374f87b`
  - The assignment and v2 return are in the ignored `.mask/generated/implement-rfc/runs/mask-rfc0020-2026-09-12-a/`.
  - Card evidence goes under a trailing `## Execution record` heading, which leaves bound text unchanged. The installed helper hashes raw bytes, so a CRLF checkout of a card computes a different source fingerprint.
- **Product state the next milestone inherits:**
  - Machine config v3 is accepted beside v1 and v2, which still work fully. There is no migration gate yet.
  - `init` no longer takes `--source`. `tap add` creates config and state when they are missing. Declarations created on v3 are v2, including those from `project init` and `user init`.
  - On v3, legacy-only paths refuse with typed errors:
    - `migration.required`: v1 declarations, legacy records, `update`, `inventory` rows and `link adopt`.
    - `source.legacy_absent`: `source migrate`, `migrate`, `source status` and `source fetch` without a name.
  - Pinned `update` still does not fetch.
  - Manual pinned `ensure` reaches its one-time consent; events still need approval.
- **Test state:**
  - `tests/support.py` and `tests/public_support.py` start tap-first, providing `TAP`, `self.upstream`, `publish()`, `install()` and `binding()`.
  - Tests of retired behavior start from `legacy_init` or `legacy_bootstrap` and carry a comment naming MASK-0100, MASK-0101 or MASK-0102. MASK-0100 ports or drops them, and should consolidate the local helper variants (`declare_pinned`, `authoring_init`, `push`).
  - `tests/test_tap_bootstrap.py` holds the bootstrap journey and the refusals for legacy records on v3.
- **Board:** MASK-0100 and MASK-0101 are Ready. MASK-0102 to MASK-0106 wait on their dependencies. The criterion rows below stay Not run.
  - MASK-0099 records fixture evidence toward AC01, the `init --source` refusal toward AC05, and the Windows suite toward AC08.
  - Still open: native qualification (AC07), the macOS suite, and the retirement work.
- **Open notes for later cards** (not accepted scope; details are on MASK-0099):
  - retained-pack case B04 names a different refusal code than the product returns;
  - `source publish` republishes LF blobs as CRLF under `core.autocrlf`;
  - a wrong-branch authoring checkout reports different codes with and without an origin;
  - the plan hash of pinned `ensure --dry-run` on a cold store differs from the applying run;
  - a refused `apply`, and a consent refusal after store hydration, both report `partial`;
  - `project init` without machine config still writes v1;
  - `scripts/qualify_real_package.py` still calls `init --source` (MASK-0104);
  - README prose and the guides still describe the checkout journey (MASK-0103).
- **Tooling notes:**
  - The installed `milestone_plan.py adopt` Windows separator defect recorded by d1 is unchanged.
  - Helper scripts need `PYTHONUTF8=1`.
  - A full Windows suite run needs `MASK_HOME`, `USERPROFILE` and `HOME` redirected, because some `Fixture` tests exercise personal scope.
- **Execution state:** all d2 children have returned: the scout, the diagnosis worker, five conversion workers and the critical reviewer. No command or child from d2 is active.
- **Next milestone:** `engine` (MASK-0100 and MASK-0101), in a fresh integrator context. It should retire the live-checkout engine, remove retired commands from `capabilities` so they exit 2, gate v1/v2 configuration with `migration.required`, and make `update` fetch each referenced tap once, with isolation and one journal.

**Dispatch `d1` record (historical; its next milestone and carried obligations were completed by d2).** Refreshed at the end of dispatch `d1`, run `mask-rfc0020-2026-09-12-a`, producer `rfc-integrator-d1`, mandate revision `1`. The owner's mandate is `/implement-rfc RFC-MASK-0020`, with no extra stop conditions. No push or publication is authorized. The owner's real machine is changed only by attended MASK-0105.

- **Accepted milestone `baseline`:**
  - MASK-0098 is Done at `b294552`; implementation is `82b4200`.
  - Exit 1: the RFC_BASE_SHA below is a real pre-implementation revision. Product sources are identical to it through `82b4200`.
  - Exit 2: `python -B -m unittest tests.test_legacy_baseline -v` passed 7 tests on Windows 11.
  - Evidence: the [MASK-0098 verified outcome](../60-done/MASK-0098-intake-and-legacy-baseline.md#verified-outcome) and [tap-cutover-baseline.md](../../development/tap-cutover-baseline.md).
- **Board:** MASK-0099 is Ready (`f670371`). MASK-0100 to MASK-0105 wait on dependencies, and this closeout is Backlog. Every criterion row below stays Not run; the baseline only supplies fixtures and defect evidence toward AC04 and AC08.
- **Plan and binding:** the [plan](../../rfcs/plans/tap-only-deployment/milestone-plan.json) was adopted at `8a9ea21`. The d1 assignment used `coordinator_handoff.py assign --target RFC-MASK-0020 --milestone baseline` with the identity above.
  - Unchanged since dispatch: definition `sha256:3b9c167aa01b554e2a17f288d0def0d19d7833507fff8319367cbecf6164043a` and prerequisite `sha256:44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`.
  - Changed: obligation `sha256:229b3a9dbe595dc04d948a6425a7ee0a0cf6dd1971426790bc28a30a666f19fd` at dispatch is now `sha256:e9312d222eeaca3547ffef202943ac00af2c8f3285a92387e45601c5527bd434`.
  - Cause: a card's bound requirement text runs from `## Acceptance` to the end of the card unless an `## Execution record` heading ends it. MASK-0098 has no such heading, so replacing its `## Run record` with the verified outcome changed its source fingerprint (`d1dfe28f…` to `a8f03244…`). Its Acceptance text is byte-identical.
  - Action: renew the assignment before checking the d1 return. Evidence written under any other heading will change later bindings the same way.
- **Windows reference suite:** incomplete; it was stopped after 32 minutes. The first 155 results ran on unchanged code and include six failing existing tests, listed in [tap-cutover-baseline.md](../../development/tap-cutover-baseline.md#runs). Later results are a stop artefact. The owner profile snapshot was unchanged. No command or child from this dispatch is active.
- **Upstream note:** the installed `milestone_plan.py adopt` builds its receipt path with a Windows separator. Adoption was run under WSL; see [LIVE_IMPORT](../../rfcs/assets/mask-corrective-managed-taps.LIVE_IMPORT.md).
- **Next milestone:** `bootstrap` (MASK-0099), in a fresh integrator context:
  - config v3 alongside v1 and v2
  - `init` without `--source`
  - `tap add` bootstrap on an empty `MASK_HOME`
  - tap-first cutover of `tests/support.py` and `tests/public_support.py`
  - the full suite green while legacy code still exists
- **Carried obligations for MASK-0099:**
  - Replace the `LiveCheckoutBaseline` tests that call `init --source`; their evidence is recorded at `82b4200`. `LegacyFixtureBytes` stays.
  - Establish a complete Windows full-suite reference that separates the six existing failures from regressions.

## Objective and owned paths

This RFC, its closeout, current affected docs and exact native evidence references only.

## Bounded work

Reconcile every RFC-MASK-0020 criterion against direct evidence: fixture journeys, native qualifier reports, the owner migration transcript, the structure gate and the full suite on both platforms. Confirm no link producer remains that targets a checkout, no retired command survives in help or capabilities, and no migration path resets or deletes user data.

## Acceptance

Every criterion has direct actual evidence and an implementation revision; every linked card is Done. Pack validation, fixture success and documentation edits are not acceptance. A missing native lane or an unrun owner migration keeps this closeout open.

Criterion coverage: RFC-MASK-0020-AC01, RFC-MASK-0020-AC02, RFC-MASK-0020-AC03, RFC-MASK-0020-AC04, RFC-MASK-0020-AC05, RFC-MASK-0020-AC06, RFC-MASK-0020-AC07, RFC-MASK-0020-AC08.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary (subprocess argv, exit code, JSON stdout, stderr,
filesystem and Git effects). Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Not started. Claim the live remapped card before edits. No code implementation,
native result, host loading, user approval or migration of a real machine is
asserted by this card's existence.

## Durable closeout anchor

RFC_BASE_SHA: b92372f224c04368b6f76d50c0312d95f8035ff3

Planned cards: MASK-0098, MASK-0099, MASK-0100, MASK-0101, MASK-0102, MASK-0103, MASK-0104, MASK-0105.

| Acceptance | Direct check / observation | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0020-AC01 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0020-AC02 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0020-AC03 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0020-AC04 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0020-AC05 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0020-AC06 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0020-AC07 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0020-AC08 | Pending actual implementation evidence | Not run | Not recorded |

Closeout review runtime: Not recorded. Required native and owner-machine boundaries remain
open until their actual evidence is linked. Do not invent a PASS to close the board.
