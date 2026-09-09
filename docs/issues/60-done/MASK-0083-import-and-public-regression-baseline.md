---
schema: "implement-rfc.card.v1"
id: "MASK-0083"
title: "Import and capture the actual broken public journeys"
status: "Done"
rfcs: ["RFC-MASK-0018", "RFC-MASK-0019"]
depends_on: []
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": false, "packet_key": "import-and-public-regression-baseline"}
acceptance: [{"criterion":"MASK-0083 starting states","outcome":"pass","revision":"b996f9be05e7c37b2892fec89b7b5db1598debce","evidence":{"kind":"command","detail":"python3 -B -m unittest tests.test_public_baseline: StartingStates 3/3 pass on macOS/Python 3.14.7. Fresh unregistered project, fresh personal home without user.json, and a linked implement-rfc consumer retaining an older rfc-worker file and no rfc-integrator exist; only mask init --source is prepared."}},{"criterion":"MASK-0083 recorded defects","outcome":"pass","revision":"b996f9be05e7c37b2892fec89b7b5db1598debce","evidence":{"kind":"command","detail":"Seven expectedFailure tests record exact commands and failing expectations: inventory/--version/capabilities print the result envelope (RFC-MASK-0018-AC02); install alpha and install alpha --user exit 2 invocation.invalid (AC01); ensure --check and ensure report ready_legacy_unpinned with rfc-integrator absent (RFC-MASK-0019-AC01/W01). Packet reproducer against live mask.py (sha256 0b93ecc6...) matched the packet observation. Record: docs/development/corrective-baseline.md."}},{"criterion":"MASK-0083 no prepared happy path","outcome":"pass","revision":"b996f9be05e7c37b2892fec89b7b5db1598debce","evidence":{"kind":"observation","detail":"tests/public_support.py human helper asserts --json is absent; no fixture registers, approves, renders or applies for the fresh states; the stale consumer's role files are retained before ensure. Import reconciliation: all packet-listed source hashes matched at 49e3971; no existing fix. Not observed: native Windows, terminal prompts, host loading, real AgentSkills package (RFC-MASK-0018-AC08, RFC-MASK-0019-AC07 remain open)."}}]
---

# MASK-0083: Import and capture the actual broken public journeys

Governing RFCs: [RFC-MASK-0018](../../rfcs/RFC-MASK-0018-task-oriented-cli-and-human-output.md), [RFC-MASK-0019](../../rfcs/RFC-MASK-0019-complete-workflow-readiness.md). Live IDs confirmed by the committed pack reservation `6d80121`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-ux-readiness.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-ux-readiness/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-ux-readiness/ACCEPTANCE.md).

## Objective and owned paths

Intake, the two new RFC families and index additions, new cards, scoped test fixtures and baseline record. Integrator owns allocation/reservations; no unrelated tracker history changes.

## Bounded work

Reconcile live source against supplied snapshots. Establish the current non-JSON result behavior and the new-skill/old-role readiness gap. Record source deltas and real baseline SHAs. Add public regression fixtures before any renderer/setup preconditions are installed; retain failures as baseline evidence, not synthetic product passes.

## Acceptance

One fresh unregistered project, one user scope and one already linked consumer with missing/stale roles exist as test starting states. Only source/launcher prerequisites may be prepared. Record the actual command and failing expectation for each defect. A baseline fixture must not automatically register, approve or render away the behavior being tested.

Criterion coverage: RFC-MASK-0018-AC02, RFC-MASK-0018-AC08, RFC-MASK-0019-AC01, RFC-MASK-0019-AC07.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary. Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation, and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Import landed at `27a463f` (reservation/baseline `6d80121`, acceptance `f7f8051`). Live source matched every packet-listed hash at `49e3971`; no prior fix existed. Baseline record: [docs/development/corrective-baseline.md](../../development/corrective-baseline.md). Starting states and non-injecting helpers: `tests/public_support.py`; retained failing expectations: `tests/test_public_baseline.py` (10 tests: 3 pass, 7 `expectedFailure`, macOS/Python 3.14.7). The packet reproducer against live `mask.py` matched the packet's observation. No implementation, native Windows result, host loading or real-package qualification is asserted; RFC-MASK-0018-AC08 and RFC-MASK-0019-AC07 rows stay open on the closeouts.
