---
schema: "implement-rfc.card.v1"
id: "MASK-0071"
title: "Verify and close RFC-MASK-0010"
status: "Backlog"
rfcs: ["RFC-MASK-0010"]
depends_on: ["MASK-0041", "MASK-0042", "MASK-0043"]
closeout_for: ["RFC-MASK-0010"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "close-10", "stage": "C — portable composition", "provisional_id": false, "closeout": true}
---

# MASK-0071: Verify and close RFC-MASK-0010

Governing RFC: [RFC-MASK-0010](../../rfcs/RFC-MASK-0010-portable-selections-and-bundles.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Reconcile every acceptance criterion against direct evidence at the stated boundary. Capture the real pre-implementation RFC_BASE_SHA and actual implementation/handoff commits. Reuse unchanged focused results; run a broader integration/review only where combined risk warrants it. Keep unavailable native, host, real-device or upstream handoff rows open. Do not claim packet validation as product acceptance.

Own only: `docs/rfcs/RFC-MASK-0010-portable-selections-and-bundles.md`, `the corresponding live closeout card`, `current affected public contract docs`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0010-AC01: Export/import round-trips selections and exact content locks between different machine/home/source paths without including credentials, registry identities, journals or launchers.
- RFC-MASK-0010-AC02: Incremental and replace modes preserve their declared ownership scopes; exported all-agent behavior and optional frozen-agent behavior are explicit and tested.
- RFC-MASK-0010-AC03: Bundle expansion/refresh is deterministic, source-revision bound and stale-plan guarded; overlapping bundles/manual selections do not cause accidental removals.
- RFC-MASK-0010-AC04: Profile subscription/removal preserves local contributions and reports version/target conflicts, unapproved sources, unavailable artifacts and offline freshness honestly.
- RFC-MASK-0010-AC05: One public import-and-apply path bootstraps selected personal scope through normal validation/recovery, with native Windows/macOS focused tests and no internal-state editing.

Proposed direct checks (not executed by this packet):

- python -B scripts/verify_documentation.py --root .
- Only missing or invalidated direct acceptance checks for this RFC.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Durable closeout anchor

RFC_BASE_SHA: 9dc90df45febf2a6e048ace60a4ac959807aaaf6

Planned cards: MASK-0041, MASK-0042, MASK-0043.

Cross-repository handoff: unrecorded; attach only an actual upstream ID/revision when required.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0010-AC01 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0010-AC02 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0010-AC03 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0010-AC04 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0010-AC05 | Not recorded | Not run | Unrecorded |

Closeout review runtime: not run. A skipped required native/host/device check leaves the criterion open.

## Current named-bundle checkpoint

Assignment MASK-0042 / `named-bundles`, mandate `named-bundles-v1`, run
`mask-named-bundles-20261002`, segment `coordinator-implementer`; engineering writer
`/root/bundles`, rfc-implementer gpt-6.1-sol/xhigh. The owner's "dont use direct"
amendment selects the preserved [strategy](../../rfcs/plans/named-bundles/strategy-selection.json).
The adopted [plan/checkpoint](../../rfcs/plans/named-bundles/checkpoint.json) retains
all bundle, canonical-handoff and upkeep exits. RFC_BASE_SHA above is unchanged;
this slice's live intake baseline is `4b983e3516cf0928e2eeff2ce35e9c84ff10e1ee`.
MASK-0041 remains open; no profile/fleet/native-host acceptance is supplied.

Candidate work adds mask_bundles.py, public CLI/rendering, strict declaration
bundle_state, source-index binding validation, manual install/uninstall membership,
runtime module inventory, schemas, public bundle tests and affected docs.
The shortest public composition passed; 12/13 expanded checks passed, with the sole
test exit-class expectation corrected. Setup failure, interrupted setup without
rerun and frozen activation recovery passed. The first broader focused regression passed 70 tests in 211 seconds. A second
81-test pass (two skips) isolated a human-preview omission, four missing argument-help
subtests and an expected source error code; all affected tests now pass in the
eight-test public/renderer recheck. Other selected recovery/manifest/user/target checks passed. Canonical AgentSkills `a32377166fd02d3b4b35feb2dfb3c178e7b80f7e`
passed public discovery of all 16 packages, four-skill installation, reviewed setup,
healthy status and repeat no-op; the exact committed MASK candidate rerun remains.
All task commands ended before the candidate commit; no review server, protected candidate or extra agent
exists. Next: collect regression results, commit explicit owned paths, rerun exact
canonical candidate, finish ASK-0095/MASK-0042 and record final evidence/quiescence.
