---
schema: "implement-rfc.card.v1"
id: "MASK-0100"
title: "Remove legacy paths, commands and add the migration gate"
status: "Backlog"
rfcs: ["RFC-MASK-0020"]
depends_on: ["MASK-0099"]
priority: "P1"
metadata: {"packet": "mask-corrective-managed-taps", "provisional_id": false, "packet_key": "retire-live-checkout-engine"}
---

# MASK-0100: Remove legacy paths, commands and add the migration gate

Governing RFC: [RFC-MASK-0020](../../rfcs/RFC-MASK-0020-tap-only-deployment.md). Live IDs confirmed by the committed pack reservation `b92372f`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-managed-taps.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-managed-taps/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-managed-taps/ACCEPTANCE.md).

## Objective and owned paths

`mask.py` (command table, `local_dispatch` tail, `project_dispatch` v1 branches, `diagnostics` checkout probe), `mask_fs.py` (planner legacy branch, `adopt`, `recover`, `registration_safe`), `mask_pinned.py` (`target` checkout case, the update/migrate transition split), `mask_task.py` (`v1_proposal`, `legacy_alias`, `listing` legacy branch), `mask_git.py` (`update` and the `AgentSkills` basename checks), `mask_core.py` (`package`, `catalog`, `registry_record`), `mask_resolve.py` (`guard_command` v1 branches), `mask_report.py`, `schemas/pending-v3.schema.json` and the tests that exercised the checkout model.

## Bounded work

Delete the live-checkout deployment paths and the `init --source`, `source status`, `source migrate` and `migrate` commands. Add the `migration.required` gate in `mask_core.config` with the documented exemptions, and an early planner refusal for legacy records and v1 declarations without `allow_migration`. Rewrite inventory over pinned records. Keep `project/user set|require|unrequire` for v2 declarations. Port or drop legacy-only tests; keep `tests/legacy_support.py` for the doctor card.

## Acceptance

No code path can compute a link text into a Git checkout except `source dev-link`; a test enumerates every link producer. `capabilities` lists no retired command and invoking one exits 2. On a v1 or v2 configuration every non-exempt command exits 4 `migration.required` with the doctor remediation. The full suite passes.

Criterion coverage: RFC-MASK-0020-AC02, RFC-MASK-0020-AC05.

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
