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
| RFC-MASK-0010-AC03 | 18 public bundle journeys plus 5 renderer checks; revision/digest stale guards, held/manual/overlap preservation, exact locks, conflicts, setup and recovery; canonical upstream bundle ready | Original pass; amendment pending | bc4f9f9 |
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

Focused amendment run: 7 initial checks pass; the first 32-test run has one failure
in new overlap/unrelated fixture preparation: implement-rfc install correctly
refused missing required consumer inputs (`workflow.incomplete`), before changes.
The fixture now supplies the existing consumer context. The other 31 checks passed.
That runner ended; rename steering arrived afterward. Owner next requested
refresh -> upgrade terminology; package-version semantics await an explicit answer
through the coordinator. Install/uninstall work continues independently.

Uninstall rollback fault check passes: after a journaled link removal, rollback
restores the receipt, lock and links; the reviewed setup script launch count stays
one. Current semantic frontier: owner choice between definition-only upgrade and
combined definition/unheld package-version upgrade remains pending. No amendment
completion or upgrade-version acceptance is asserted.

## Quiescent pending-choice handoff

Current assignment MASK-0128 plus upstream ASK-0096, mandate `named-bundles-v3`,
segment `coordinator-implementer-install-uninstall-upgrade`; same non-delegating
leaf `/root/bundles`, gpt-6.1-sol/xhigh and preserved strategy. Runtime candidate
`d31bf5cbbf85283e275f9668ae8ff8c702b9ddbc`; canonical source/verifier candidate
`de0d3736f4767ac1af49f30f336f6a9c2bcd0314`. Completed install/uninstall acceptance:
15 exact-candidate public/renderer checks pass in 47.164s; 44 ordinary task/CLI/
help/readiness regressions pass; canonical four-skill reviewed setup healthy, all
16 packages preserved, offline removal preserves manually selected grill-me,
repeat removal is a no-op and reinstall is healthy. [Amendment evidence](../../development/named-bundles-evidence.json)
retains every actual run/failure/correction and exact canonical receipt.

Changed paths: bundle runtime/CLI/rendering, focused bundle and capability tests,
current user/CLI/RFC docs, same adopted plan/strategy/checkpoint, follow-up cards
and bounded canonical README/verifier/evidence. Old completed card acceptance is
preserved. No unrelated work was modified. All test/setup/Git subprocesses ended;
all disposable consumers, source caches, local bare remotes and machine roots
were cleaned. No server, protected review candidate, worktree or extra agent.
Both repositories remain on main, with explicit-path commits and no publication,
real consumer migration, permission or credential changes.

Required pending: owner choice between bundle upgrade adopting the latest definition
plus unheld package versions, and a rename retaining existing versions. Current
candidate retains prior definition-only behavior; combined-version semantics are
not implemented or accepted. Coordinator owns the pending question. Resume this
same milestone/leaf with the answer; reuse ordinary `mask_resolve.resolve_candidate`
for scoped updates, holds, identical-package lock preservation and immutable-ref
safety if combined is selected. Then test that changed scope, reconcile docs/
canonical verification and finish MASK-0128 / ASK-0096. Cards remain In Progress;
RFC-MASK-0010 and reopened RFC-ASK-0015 remain Implementing. Original profiles/
fleet/native host-loading obligations stay open. No attended review is required.
Writer ownership releases on this pending-choice return and can resume on reply.
