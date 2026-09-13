---
schema: "implement-rfc.card.v1"
id: "MASK-0099"
title: "Add config v3, tap-add bootstrap and tap-first fixtures"
status: "In Progress"
rfcs: ["RFC-MASK-0020"]
depends_on: ["MASK-0098"]
priority: "P1"
metadata: {"packet":"mask-corrective-managed-taps","provisional_id":false,"packet_key":"machine-v3-and-tap-bootstrap","milestone_plan":{"id":"tap-only-deployment","path":"docs/rfcs/plans/tap-only-deployment/milestone-plan.json"}}
---

# MASK-0099: Add config v3, tap-add bootstrap and tap-first fixtures

Governing RFC: [RFC-MASK-0020](../../rfcs/RFC-MASK-0020-tap-only-deployment.md). Live IDs confirmed by the committed pack reservation `b92372f`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-managed-taps.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-managed-taps/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-managed-taps/ACCEPTANCE.md).

## Objective and owned paths

`mask_core.py` (`config`), `mask_sources.py` (`validate_config`, `selected`, `dispatch`), `mask.py` (`init`, `capabilities`), `schemas/machine-v3.schema.json`, `schemas/machine.schema.json`, `mask_task.py` (`fresh_declaration`), `tests/support.py`, `tests/public_support.py`, `tests/test_sources.py`, `tests/test_cli_protocol.py` and the tests those fixtures feed.

## Bounded work

Accept machine config v3 beside v1 and v2 without the migration gate yet. Make `init` write an empty v3 catalog without `--source`, and make `tap add` create config and state when they are missing. New declarations become v2 on a v3 machine. Cut both test fixture bases over to a local bare repository added as a `file` tap followed by `install`; keep every existing test green while legacy code still exists. Publish the new schema and readable versions through `capabilities`.

## Acceptance

An empty `MASK_HOME` plus `tap add` plus `install` deploys a v2 consumer with a bare cache and store-targeted links and no checkout on disk. `init` no longer accepts `--source`. `tests/support.py` and `tests/public_support.py` no longer call `init --source`. The full suite passes on the cut-over fixtures.

Criterion coverage: RFC-MASK-0020-AC01, RFC-MASK-0020-AC05.

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
