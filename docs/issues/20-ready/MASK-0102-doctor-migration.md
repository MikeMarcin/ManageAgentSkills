---
schema: "implement-rfc.card.v1"
id: "MASK-0102"
title: "Detect and migrate legacy machines and consumers through doctor"
status: "Ready"
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
