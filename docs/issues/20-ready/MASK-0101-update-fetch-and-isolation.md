---
schema: "implement-rfc.card.v1"
id: "MASK-0101"
title: "Fetch every referenced tap and update all consumers in one journal"
status: "Ready"
rfcs: ["RFC-MASK-0020"]
depends_on: ["MASK-0099"]
priority: "P1"
metadata: {"packet":"mask-corrective-managed-taps","provisional_id":false,"packet_key":"update-fetch-and-isolation","milestone_plan":{"id":"tap-only-deployment","path":"docs/rfcs/plans/tap-only-deployment/milestone-plan.json"}}
---

# MASK-0101: Fetch every referenced tap and update all consumers in one journal

Governing RFC: [RFC-MASK-0020](../../rfcs/RFC-MASK-0020-tap-only-deployment.md). Live IDs confirmed by the committed pack reservation `b92372f`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-managed-taps.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-managed-taps/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-managed-taps/ACCEPTANCE.md).

## Objective and owned paths

`mask_update.py` (new), the `update` and `source fetch` dispatch lines in `mask.py`, `tests/test_update.py` (new) and `tests/test_pinned_update.py`. Do not edit the planner, the journal or the fixture bases in this card.

## Bounded work

Implement the update algorithm from `contracts/CLI.md`: select consumers, compute referenced taps, fetch each once unless `--dry-run`, `--offline` or `--expect-plan-hash`, capture per-tap failures, block only the consumers that reference a failed tap, resolve the rest from cache, refuse rebound selectors without `--allow-ref-rebind`, disclose per-consumer diffs, apply through one journal and end `update.incomplete` when any consumer stayed blocked. Make `source fetch` without a name fetch every approved tap. Retire the shared-checkout `scope.expand` consent.

## Acceptance

With two taps and three consumers, an upstream push followed by `mask update` fetches each tap exactly once (fixture counts Git invocations), updates the affected consumers in one journal and leaves the untouched consumer's lock byte-identical. Renaming one bare repository away blocks only its consumers and exits 4 `update.incomplete`. `--dry-run`, `--offline` and a guarded rerun perform no fetch. A moved tag refuses without `--allow-ref-rebind`.

Criterion coverage: RFC-MASK-0020-AC03.

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
