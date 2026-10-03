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
- RFC-MASK-0010-AC03: Bundle install/uninstall/combined upgrade is deterministic, source-revision bound and stale-plan guarded; overlapping bundles/manual selections do not cause accidental removals.
- RFC-MASK-0010-AC04: Profile subscription/removal preserves local contributions and reports version/target conflicts, unapproved sources, unavailable artifacts and offline freshness honestly.
- RFC-MASK-0010-AC05: One public import-and-apply path bootstraps selected personal scope through normal validation/recovery, with native Windows/macOS focused tests and no internal-state editing.

Proposed direct checks (not executed by this packet):

- python -B scripts/verify_documentation.py --root .
- Only missing or invalidated direct acceptance checks for this RFC.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Durable closeout anchor

RFC_BASE_SHA: 9dc90df45febf2a6e048ace60a4ac959807aaaf6

Planned cards: MASK-0041, MASK-0042, MASK-0043; owner-authorized named-bundle follow-up MASK-0128.

Cross-repository named-bundle handoff: actual AgentSkills ASK-0095, source candidate
`fb67261a5fd8a69231e963226189fd98458e4d82`, acceptance commit
`b9e413673b7dc7b618487def3831049451010632`; canonical public install verified with
MASK `bc4f9f9015ee2bd3495101e91d0077f35ebc1733`. Broader profile handoffs remain open.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0010-AC01 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0010-AC02 | Bundle union/manual/overlap/replace ownership passes in [public evidence](../../development/named-bundles-evidence.json); export/all-agent freezing still belongs to open MASK-0041 | Partial; remains open | bc4f9f9 |
| RFC-MASK-0010-AC03 | 43 successful public bundle/renderer checks plus separate scoped regression; combined named/default/--all definitions and unheld versions, guards, ownership, conflicts, setup/recovery; actual canonical 22-command handoff | Pass for amended named-bundle boundary | b879f81 |
| RFC-MASK-0010-AC04 | Not recorded | Not run | Unrecorded |
| RFC-MASK-0010-AC05 | Not recorded | Not run | Unrecorded |

Closeout review runtime: not run. A skipped required native/host/device check leaves the criterion open.

## Historical initial named-bundle checkpoint

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

## Historical install/uninstall amendment checkpoint

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

## Historical quiescent pending-choice handoff

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

## Combined-upgrade resumption record

Owner answered "yes go with recommendation" and requested `mask upgrade --all`
catch installed bundles. Pending policy is resolved. Same leaf resumes from clean
quiescent MASK 68fccad8 / AgentSkills 90b5678 under the preserved strategy and v3
mandate. Scope adds existing mask_update.py per-consumer proposal integration.
Frontier: combined receipt/version candidate through shared resolver/planner,
default and aggregate upgrade definitions, focused stale/conflict/hold/recovery
and mixed-scope tests, canonical upgrade check and final upkeep/acceptance.
Historical pending checkpoint/evidence remains provenance, not current state.

Combined upgrade progress: four focused named/aggregate/default/partial-scope cases
pass in 37.433s. First full affected run: 43 tests, one failure and one error.
Overlapping alpha was preserved but omitted from human diff; added preservation
disclosure. Setup test changed only SKILL.md, correctly leaving setup fingerprint
unchanged; the fixture now changes a declared script input. Existing moved-tag/
non-fast-forward whole-operation refusal remains intact; new bundle source/
constraint errors are reported per scope. Corrected checks plus ordinary update
regression passed (19 tests, 137.538s). Failure observations retained in current evidence.


## Current completed amendment checkpoint — named-bundles-v3

Assignment MASK-0128 / actual upstream ASK-0096; adopted plan `named-bundles`,
run `mask-named-bundles-20261002`, segment
`coordinator-implementer-install-uninstall-upgrade`. Owner answered "yes go with
recommendation" and explicitly requested installed bundles in `mask upgrade --all`.
Both decisions are implemented and accepted; the earlier pending-choice sections
are historical. Same non-delegating leaf `/root/bundles`, gpt-6.1-sol/xhigh,
preserved coordinator-implementer selection and original "dont use direct" amendment.
RFC_BASE_SHA stays unchanged.

Exact implementation/verified runtime: `b879f8136489a98cfa26e0aae1da7e7e268c589b`.
Canonical source/verifier: `39a6de558252eb0bf8c3cf9ae0d48f3fb10fa0ee`; actual
ASK-0096 completion: `ff9d05a15c767422d00d4f815297bbb3c5a7d5aa`.
[Bound acceptance](../../development/named-bundles-combined-upgrade-acceptance.json)
records 43 successful bundle/renderer checks from the exact runtime runner plus
one separate passing scoped regression (8.448s). The original runner's exit 1 is
retained: its sole error was an additional selector using a nonexistent test class,
corrected without repeating the 43 successful checks. Earlier 4 focused tests and
19 corrected/ordinary update checks pass; initial product/fixture failures and
corrections remain in [durable evidence](../../development/named-bundles-evidence.json).
Canonical receipt records 22 successful public commands: all four skills ready
with reviewed setup, all 16 packages discovered/validated, manual-safe offline
uninstall/reinstall and combined named preview/guarded `upgrade --all` application
of a separately derived disposable source/package revision, healthy status and no-op.

Runtime integration: recomposes frozen receipts together, then resolves eligible
unheld member coordinates through the existing resolver. Default scoped and aggregate
upgrade combine receipt and ordinary skill updates in one reviewed planner/setup/
journal. IDs remain package-only. Exact selectors/ref safeguards, manual target
choices, holds and local edits remain protected; conflicts are disclosed before
consumer edits and aggregate valid scopes can finish with `upgrade.incomplete`.
Uninstall drops only the named local contribution; manual/overlap/held/edited
survivors and exact rows remain. Ordinary standalone uninstall and positive manual
promotion are documented. Only implemented commands/capabilities are advertised.

Changed paths: mask_bundles.py, mask_update.py, mask_cli.py, mask_present.py,
focused bundle/update tests, current README/CLI/declaration/source guides, live RFC,
same plan/strategy/checkpoint and policy answer, MASK-0128, bounded MASK-0064/
canonical handoff and this closeout/evidence. Upstream owns canonical README,
verifier, ASK-0096 and its RFC/closeout/evidence. No unrelated work was modified.

All product/test/setup/Git subprocesses ended; disposable consumers, machine roots
and bare remotes were cleaned. No server, worktree, extra agent, protected review
candidate or uncertain command remains. No human review is required or substituted.
Documentation gates pass: MASK 23 RFCs/128 cards and AgentSkills 15 RFCs/96 cards,
zero structural violations; git diff --check passes. Final board/checkpoint validation
is recorded with acceptance upkeep.
Ownership releases after this completed return. No push/publication, real consumer
migration, credential or permission changes occurred. No running-host loading or
native Windows result is claimed.

No pending obligation remains inside this named-bundles-v3 milestone. MASK-0041,
MASK-0043, profile/export/frozen-agent/native acceptance and broader MASK-0064
management/provenance/fleet remain open; RFC-MASK-0010 remains Implementing.
Next action: stop this accepted milestone; coordinator selects newly authorized
eligible scope. Public examples: `mask bundle upgrade agentskills/rfc --dry-run
--json`, `mask upgrade --dry-run --json`, and `mask upgrade --all --dry-run --json`.

MASK-0128 acceptance commit: `e982c3431de84a9308aff86d5fd50eaf85ae0c2d`.
ASK-0096 acceptance/final upstream HEAD: `ff9d05a15c767422d00d4f815297bbb3c5a7d5aa`.
Final [checkpoint](../../rfcs/plans/named-bundles/checkpoint.json) binds current
Done cards and amended exits. Mechanical return checks continuation consistency;
it does not substitute for the product evidence above.
