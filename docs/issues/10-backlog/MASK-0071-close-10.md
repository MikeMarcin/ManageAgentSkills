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

Cross-repository named-bundle handoff: actual AgentSkills ASK-0095, source candidate
`fb67261a5fd8a69231e963226189fd98458e4d82`, acceptance commit
`b9e413673b7dc7b618487def3831049451010632`; canonical public install verified with
MASK `bc4f9f9015ee2bd3495101e91d0077f35ebc1733`. Broader profile handoffs remain open.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0010-AC01 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0010-AC02 | Bundle union/manual/overlap/replace ownership passes in [public evidence](../../development/named-bundles-evidence.json); export/all-agent freezing still belongs to open MASK-0041 | Partial; remains open | bc4f9f9 |
| RFC-MASK-0010-AC03 | 18 public bundle journeys plus 5 renderer checks; revision/digest stale guards, held/manual/overlap preservation, exact locks, conflicts, setup and recovery; canonical upstream bundle ready | Pass | bc4f9f9 |
| RFC-MASK-0010-AC04 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0010-AC05 | Not recorded | Not run | Unrecorded |

Closeout review runtime: not run. A skipped required native/host/device check leaves the criterion open.

## Current named-bundle checkpoint

Assignment MASK-0042 / `named-bundles`, mandate `named-bundles-v1`, run
`mask-named-bundles-20261002`, segment `coordinator-implementer`; engineering owner
`/root/bundles`, rfc-implementer gpt-6.1-sol/xhigh. The owner's "dont use direct"
amendment selects the preserved [strategy](../../rfcs/plans/named-bundles/strategy-selection.json)
and [plan/checkpoint](../../rfcs/plans/named-bundles/checkpoint.json). All named-bundle,
canonical-handoff and upkeep exits pass. RFC_BASE_SHA above stays unchanged; this
slice's live intake baseline is `4b983e3516cf0928e2eeff2ce35e9c84ff10e1ee`.

Runtime implementation: `ab625a6e1735a3d79fda24ae5b6c52355d465014`; exact verified
MASK candidate: `bc4f9f9015ee2bd3495101e91d0077f35ebc1733`. MASK-0042
acceptance commit: `8181738c38553679d96b7179658b5240af29798c`. Canonical AgentSkills
candidate: `fb67261a5fd8a69231e963226189fd98458e4d82`; upstream ASK-0095 acceptance:
`b9e413673b7dc7b618487def3831049451010632`. [Evidence](../../development/named-bundles-evidence.json)
records the actual commands, outcomes and corrections: first 70-test regression
pass; final 23-test public/renderer pass; canonical four-skill installation with
reviewed setup, healthy status and all 16 package discoveries. Two preexisting
native Windows skips (junction behavior and symlink error mapping) in the selected 81-test run remain declared. Initial human
preview/help issues and clean-checkout fixture auto-refresh failures were corrected
and directly rechecked; the failed exact-candidate receipt is retained.

Changed paths: named-bundle module, public CLI/rendering and runtime inventory,
selection/source validators, task manual membership, source/declaration schemas,
focused bundle/launcher tests, affected user/CLI/RFC docs, adopted plan/strategy,
MASK-0042 and bounded MASK-0064/closeout handoff. No unrelated work was modified.
Both canonical repositories remain on main; no push/publication, real consumer
migration, permission/credential/persistent approval change occurred.

All task-owned Git/test/setup/verification commands ended; no descendants,
background commands, protected candidate, review session/server or owned worktree
exists. Disposable consumers, local bare remotes and machine roots were consumed
and cleaned. Ownership releases when this milestone returns. No required human
review is imposed or substituted. MASK-0041/profile subscription/export/frozen-agent
and broader MASK-0064/fleet/native host-loading work remain outside this mandate.
Next eligible continuation is coordinator selection of newly authorized scope;
RFC-MASK-0010 remains Implementing with its other acceptance rows open.

## Active install/uninstall amendment checkpoint

Owner authorized `named-bundles-v2`; same leaf and preserved coordinator-implementer
strategy, new segment `coordinator-implementer-install-uninstall`. Intake HEADs:
MASK c3fdaf8676329d056c471be1797695e6e3d90771; AgentSkills
b9e413673b7dc7b618487def3831049451010632. Prior commands were quiescent and
repositories clean. Follow-up MASK-0128 / upstream ASK-0096 are claimed before
source changes. Existing plan now includes this amendment; historical acceptance
and RFC_BASE_SHA are preserved. Frontier: implement install vocabulary and receipt-
bounded uninstall, then public removal/reinstall/recovery tests and canonical
verification. No required human review. Profiles/fleet/native host loading remain
outside the mandate. Ownership releases only after final cleanup and return.
