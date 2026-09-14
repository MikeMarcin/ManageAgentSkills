---
schema: "implement-rfc.card.v1"
id: "MASK-0102"
title: "Detect and migrate legacy machines and consumers through doctor"
status: "In Progress"
rfcs: ["RFC-MASK-0020"]
depends_on: ["MASK-0098", "MASK-0100"]
priority: "P1"
metadata: {"packet":"mask-corrective-managed-taps","provisional_id":false,"packet_key":"doctor-migration","milestone_plan":{"id":"tap-only-deployment","path":"docs/rfcs/plans/tap-only-deployment/milestone-plan.json"}}
---

# MASK-0102: Detect and migrate legacy machines and consumers through doctor

Governing RFC: [RFC-MASK-0020](../../rfcs/RFC-MASK-0020-tap-only-deployment.md). Live IDs confirmed by the committed pack reservation `b92372f`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-managed-taps.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-managed-taps/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-managed-taps/ACCEPTANCE.md).

## Objective and owned paths

`mask_legacy.py` and `mask_migrate.py` (new), `diagnostics` in `mask.py`, the `doctor` command table entry and `GUARDED`, the `validate_pending` hooks in `mask_fs.py`, `schemas/pending-v3.schema.json`, `tests/test_doctor_migration.py` (new) and the doctor cases in `tests/test_recovery.py` and `tests/test_pinned_recovery.py`.

## Bounded work

Implement `contracts/MIGRATION.md`: detection and `data.migration` reporting, `--check` exit 7, `--migrate` with `--alias`, `--dry-run` and `--expect-plan-hash`, alias derivation, remote or `file` identity, acquisition of the clone HEAD into the tap cache over file transport, declaration and lock mapping, store materialization, link retargeting and record conversion in one `doctor.migrate` journal, typed refusals, the machine-only path and the v3 straggler path. Port the `test_pin_migration` crash matrix to `doctor --migrate`.

## Acceptance

On the v1 and v2 fixtures from MASK-0098 with a legacy project, a legacy personal scope and an unregistered v1 declaration: `doctor` reports `migration.required`, `--check` exits 7, `--migrate --dry-run` writes nothing, `--migrate` produces v3 config, v2 declarations, locks at the clone HEAD, store-targeted links and pinned records, and a crash at every checkpoint recovers with `--rollback` to exact prior bytes and links or with `--complete`. A machine with an empty registry migrates its configuration only. Dirty, unborn, detached, alias-conflict and no-remote clones produce the documented typed results.

Criterion coverage: RFC-MASK-0020-AC04, RFC-MASK-0020-AC05.

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

## Execution record

Dispatch `d4` of run `mask-rfc0020-2026-09-12-a`, milestone `migration`.
- **Commits:** claim `333c2f7`; doctor report `e28d615`; machine migration `5215741`; tap-machine path and review hardening `fe9c13a`.
- **Binding:** the heading above ends the bound Acceptance text, so this record does not change the milestone binding. A recomputed assignment matched every fingerprint.

### Acceptance evidence
The evidence is `tests.test_doctor_migration` (22 tests) and `tests.test_doctor_straggler` (5 tests). Both drive CLI subprocesses on the schema-true legacy fixtures from `tests/legacy_support.py`.
- **doctor reports `migration.required` and `--check` exits 7 (M01):** tested by `DoctorReport` and `CurrentMachineReport`.
  - v1 reports:
    - the proposed tap `agentskills` with the clone as authoring;
    - the clone's head, branch, dirty, unborn and published observations;
    - per-consumer rows with link states and typed blockers.
  - v2 keeps the alias `legacy`.
  - An unregistered v1 declaration named by `--project` or `--user` is reported rather than refused.
  - Negative control: against `d0afac8` the report tests error 6 of 6 with `KeyError: 'migration'`.
- **`--migrate --dry-run` writes nothing (M02):**
  - A snapshot of the whole fixture base is unchanged.
  - `--expect-plan-hash` applies the reviewed plan.
  - A stale hash, a changed declaration and a moved clone HEAD each refuse `plan.stale`.
- **The migrated machine (M03, M04):**
  - config v3 with the clone as tap authoring;
  - v2 declarations with `ref: refs/heads/main`, and locks at the clone HEAD;
  - the cache holds `refs/mask/frozen/<head>`, with no `refs/mask/selected` and no `mask-refs.json`;
  - store links and pinned records, and `doctor --check` exits 0;
  - the clone's HEAD, index, status and worktree, and the upstream, are unchanged;
  - the unregistered straggler stays v1;
  - on v2, `legacy` and the extra tap are kept byte-identical.
- **Crash at every checkpoint (M05; milestone exit 1):**
  - Checkpoints: `intent`, `link_unlinked`, `link`, `manifest`, `lock`, `config` and `state`.
  - `recover --rollback` restores exact config, state and declaration bytes, removes created locks and restores every link text.
  - `recover --complete` finishes the migration.
  - The tap-machine journal passes the same checkpoints except `config`, with the same outcome.
  - Negative control (worker): a rollback that skips `machine_config` fails the `config` and `state` subtests.
  - The independent reviewer also completed from every checkpoint, and rolled back v2-state machines with the clone renamed away.
- **Empty registry (M06; milestone exit 2):**
  - The journal's files hold only `machine_config`, `selected` is empty, and `cache` is null.
  - Only config v3 is written; no `sources` or `store` directory appears.
  - A dirty clone is a warning.
- **Typed refusals (M07–M10):**
  - Each writes nothing:
    - dirty: `source.dirty`;
    - unborn: `migration.unborn`;
    - detached, and diverged: `source.identity_mismatch`, with reason `diverged` for the latter;
    - missing clone: `source.missing` (exit 3).
  - A clone without a remote becomes a `file` identity tap, with warning `migration.local_only_source`.
  - On v2, `--alias extra` refuses `source.alias_conflict`. `--alias other` renames the legacy tap, but is refused while a pinned consumer names it.
  - An unpushed HEAD migrates with warning `migration.unpublished_commit`.
  - A refusal keeps its typed exit code; for example, `source.identity_invalid` exits 3.
- **Straggler on a tap machine (M11):**
  - `--project PATH --alias NAME` and `--user --alias NAME` rewrite the declaration, resolve it, register the consumer and link it. On a cold cache, `--offline` and `--dry-run` refuse `lock.resolution_required`.
  - A registered legacy record converts the same way, and a rerun is a no-op.
  - Each refusal writes nothing: missing or unscoped arguments, an unknown alias, a v2-declaration legacy record, and a pending journal.
  - A tampered after-selection refuses recovery.
  - Negative controls (worker): disabling the selection check, reverting the planner target, or removing the before-link equality each makes a test fail.
- **Previous program (M12):** the `b92372f` program refuses a `doctor.migrate` journal with `recovery.conflict` and changes nothing. The reviewer repeated this after the `config` and `state` checkpoints.

### Decisions and interpretations
- **Journal operation `doctor.migrate`:** it alone may record a migration, the machine configuration or legacy ownership. Rollback never reads the clone; completion requires the clone and its remote to be unchanged.
- **AC02 and AC04 rollback:** `set_link` restores legacy link text only inside a validated `doctor.migrate` rollback.
  - On a v1/v2 machine the text must name the journal's recorded checkout.
  - On a tap machine it must equal the before record exactly.
  - `mask_pinned.target` and the link-producer allowlist are unchanged.
- **Diverged checkout:** HEAD and the remote-tracking branch each hold commits the other lacks. This refuses `source.identity_mismatch`; a HEAD strictly ahead only warns.
- **Empty registry:** dirty and unborn checkouts warn. Detached, wrong-branch and diverged checkouts still refuse, as the MIGRATION.md table states.
- **Legacy record with a v2 declaration:** refuses `migration.declaration_unsupported`, both in the report and in `--migrate`.
- **Tap machine:** `--alias` and exactly one of `--project` or `--user` are required. The conversion uses install semantics and writes no ref.
- **Preparation effects:** the cache and store effects stay outside the journal and are never deleted.

### Independent review
- **Reviewer:** `rfc-reviewer-critical`, generated route `claude-fable-5-1` at high effort; the banner matched.
  - It reviewed `5215741` and `e28d615` from archived copies with 95 probes on Windows 11.
- **No blocking finding.** Non-blocking findings and their dispositions:
  1. A link edited before the writer lock left a retained journal. Fixed in `fe9c13a`: it now refuses `plan.stale` with nothing written, and is tested.
  2. Manifest entries were admitted on a `doctor.migrate` journal. Fixed in `fe9c13a`: refused, and tested.
  3. Plain `doctor` on a legacy record with a v2 declaration and no lock stops at `lock.missing` before reporting, because of guard order. Follow-up note.
  4. Completion does not recheck worktree cleanliness. The deployed bytes come from the recorded commit. Note.
  5. Malformed journals refuse with the generic `state.invalid` or `recovery.invalid`. Note.
  6. `plan.stale` after preparation reports `transaction: partial`, because the retained cache and store effects are merged in. MASK-0103 should document this.

### Open owner decisions and notes
- **Q5 (new):** on v1/v2 machines, AC05 gates the MIGRATION.md blocker remediations (`project unregister --keep-links`, `workspace forget`).
  - The ask: exempt them from the gate (amending AC05), or keep the gate and document that a non-migratable consumer must be restored on disk first?
  - The gate is unchanged here.
- **Q4:** unchanged.
- **MASK-0107:** `doctor --migrate` should write the exact-bytes tap default once that card lands.
- **Routes:**
  - Every leaf was dispatched by generated role with no model or effort override.
  - Worker banners: B1 reported `claude-opus-5[1m]` with xhigh as configured; B2 reported `claude-opus-5` with the runtime reasoning effort `40`.
  - The difference between the runtime effort value and the configured `xhigh` remains an unresolved observation.

### Limitations
- **Platform:** only Windows 11 was exercised; no macOS or POSIX run.
- **Not exercised:** `source.fetch_limit`, `lock.limit`, sha256 clones, two concurrent migrations, and a migration that also writes native roles.
