---
schema: "implement-rfc.card.v1"
id: "MASK-0067"
title: "Verify and close RFC-MASK-0006"
status: "Done"
rfcs: ["RFC-MASK-0006"]
depends_on: ["MASK-0024", "MASK-0025", "MASK-0026", "MASK-0027", "MASK-0028", "MASK-0029", "MASK-0081", "MASK-0082"]
closeout_for: ["RFC-MASK-0006"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "close-6", "stage": "A — first usable milestone", "provisional_id": false, "closeout": true}
acceptance: [{"criterion":"RFC-MASK-0006-AC01","outcome":"pass","revision":"c03f85c","evidence":{"kind":"observation","detail":"Native macOS fallback and Windows named Git lifecycle; clone/startup fixtures. Pass. Native evidence: docs/development/readiness-acceptance.md; completed prerequisite cards and recorded original revisions remain authoritative."}},{"criterion":"RFC-MASK-0006-AC02","outcome":"pass","revision":"c03f85c","evidence":{"kind":"observation","detail":"Approved ensure, nested/personal preflight, bounded reads and no-op byte/generation checks. Pass. Native evidence: docs/development/readiness-acceptance.md; completed prerequisite cards and recorded original revisions remain authoritative."}},{"criterion":"RFC-MASK-0006-AC03","outcome":"pass","revision":"c03f85c","evidence":{"kind":"observation","detail":"Ownership, collisions, pending/busy refusal, unavailable worktree preservation. Pass. Native evidence: docs/development/readiness-acceptance.md; completed prerequisite cards and recorded original revisions remain authoritative."}},{"criterion":"RFC-MASK-0006-AC04","outcome":"pass","revision":"c03f85c","evidence":{"kind":"observation","detail":"Inactive-branch cleanup and exact control/authority recovery checks. Pass. Native evidence: docs/development/readiness-acceptance.md; completed prerequisite cards and recorded original revisions remain authoritative."}},{"criterion":"RFC-MASK-0006-AC05","outcome":"pass","revision":"c03f85c","evidence":{"kind":"observation","detail":"Owned entries and recovery; native directory and named Git hook suppression. Pass. Native evidence: docs/development/readiness-acceptance.md; completed prerequisite cards and recorded original revisions remain authoritative."}},{"criterion":"RFC-MASK-0006-AC06","outcome":"pass","revision":"c03f85c","evidence":{"kind":"observation","detail":"Native macOS/Windows mask launch with installed Claude/Codex --version; separate adapter protocols. Pass at explicit prelaunch fallback; first-prompt loading unverified. Native evidence: docs/development/readiness-acceptance.md; completed prerequisite cards and recorded original revisions remain authoritative."}},{"criterion":"RFC-MASK-0006-AC07","outcome":"pass","revision":"c03f85c","evidence":{"kind":"observation","detail":"Native macOS APFS and Windows NTFS launcher/link/lifecycle checks; WinError1314 mapping. Pass. Native evidence: docs/development/readiness-acceptance.md; completed prerequisite cards and recorded original revisions remain authoritative."}}]
---

# MASK-0067: Verify and close RFC-MASK-0006

Governing RFC: [RFC-MASK-0006](../../rfcs/RFC-MASK-0006-automatic-workspace-readiness.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Reconcile every acceptance criterion against direct evidence at the stated boundary. Capture the real pre-implementation RFC_BASE_SHA and actual implementation/handoff commits. Reuse unchanged focused results; run a broader integration/review only where combined risk warrants it. Keep unavailable native, host, real-device or upstream handoff rows open. Do not claim packet validation as product acceptance.

Own only: `docs/rfcs/RFC-MASK-0006-automatic-workspace-readiness.md`, `the corresponding live closeout card`, `current affected public contract docs`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0006-AC01: Actual clone, worktree add, branch switch, merge and manual-merge completion fixtures invoke integration and converge without a user executing apply; unsupported Git integration reports its coverage accurately.
- RFC-MASK-0006-AC02: Ensure combines authorization, registration and selected-scope reconciliation through the existing safety engine; unchanged runs preserve managed bytes/generation and perform no unrelated scans.
- RFC-MASK-0006-AC03: Untrusted roots, collisions, replaced parents, busy locks and pending recovery cannot be converted to success or silently repaired; hooks never claim to roll back completed Git actions.
- RFC-MASK-0006-AC04: Inactive-branch handling distinguishes verified branch absence from deleted, sparse, unreadable or conflicted input; interrupted readiness refuses completion after its control files change.
- RFC-MASK-0006-AC05: Owned hook installation/removal preserves unrelated hooks/settings, suppresses configured and directory hooks for MASK internal Git commands, and prevents recursion.
- RFC-MASK-0006-AC06: Native Claude and Codex startup/worktree scenarios record actual versions and first-prompt discovery or an explicit fallback limitation; a warning-only adapter is not called a strict gate.
- RFC-MASK-0006-AC07: Native Windows and macOS readiness/launcher paths receive focused direct checks; worktree removal and unavailable-root handling preserve ownership and are independently tested.

Proposed direct checks (not executed by this packet):

- python -B scripts/verify_documentation.py --root .
- Only missing or invalidated direct acceptance checks for this RFC.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Durable closeout anchor

RFC_BASE_SHA: 9dc90df45febf2a6e048ace60a4ac959807aaaf6

Planned cards: MASK-0024, MASK-0025, MASK-0026, MASK-0027, MASK-0028, MASK-0029.

Cross-repository handoff: unrecorded; attach only an actual upstream ID/revision when required.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0006-AC01 | Native macOS fallback and Windows named Git lifecycle; clone/startup fixtures | Pass | c03f85c |
| RFC-MASK-0006-AC02 | Approved ensure, nested/personal preflight, bounded reads and no-op byte/generation checks | Pass | c0d37e7; unchanged at c03f85c |
| RFC-MASK-0006-AC03 | Ownership, collisions, pending/busy refusal, unavailable worktree preservation | Pass | c03f85c |
| RFC-MASK-0006-AC04 | Inactive-branch cleanup and exact control/authority recovery checks | Pass | c03f85c |
| RFC-MASK-0006-AC05 | Owned entries and recovery; native directory and named Git hook suppression | Pass | c03f85c |
| RFC-MASK-0006-AC06 | Native macOS/Windows mask launch with installed Claude/Codex --version; separate adapter protocols | Pass at explicit prelaunch fallback; first-prompt loading unverified | 3456e3 (Windows); c0d37e7 (macOS); unchanged host path at c03f85c |
| RFC-MASK-0006-AC07 | Native macOS APFS and Windows NTFS launcher/link/lifecycle checks; WinError1314 mapping | Pass | c03f85c |

Closeout review runtime: not run. A skipped required native/host/device check leaves the criterion open.

## Ensure core slice

Revision `029adabec841e59515ec45b6f2d9a51b5e6517b5`: 17 focused tests passed (one existing Windows-only skip), covering approved project registration/reconciliation, no-op bytes, check-only drift, selected-package scan, collisions, parent substitution, pending and busy refusal. AC02/AC03 core evidence; full lifecycle/integration/native rows remain open. Next: MASK-0025. Temporary test roots were automatically cleaned by unittest fixtures.

## Lifecycle slice

Revision `b6ce556029fdf45e650681fc06235034f827a53b`: 22 focused tests passed across lifecycle, ensure, recovery and launcher; after adding unrelated-commit and conflicted-index cases, all 6 lifecycle tests passed. Direct subprocess/Git fixtures cover inactive branch removal/restoration, local deletion, sparse checkout, conflicted index, changed branch/declaration/authority recovery, and verified worktree retirement. Existing v1/v2 recovery remains exercised. Busy lock fails immediately without takeover. Native Windows/host acceptance remains on separate cards.

Owned-path extension: CLI registration/capability metadata, pending schema union and launcher module inventory changed with the new runtime/journal boundary. Inactivity requires an explicit root approval with `--inactive-branches` and tracked declaration evidence; inherited linked-worktree approval alone does not opt a new worktree into deactivation. No live consumer was migrated. Next: MASK-0026 and MASK-0027.

## Git integration slice

Revision `2c3fd278787df3136125f82784f0f020f0ab963d`: 9 Git-integration/subprocess tests passed. After bounding hook child process-tree termination, the affected manual-merge/warning test and launcher tests passed (3 tests). Actual Apple Git 2.50.1 fixtures exercised switch, linked worktree creation, fast-forward merge, manual conflict-resolution commit, clone coverage limitation, collision preservation, existing hook manager refusal, crash recovery and internal directory-hook suppression. Named-hook capability was probed unavailable on installed Git (also fallback Git 2.53.0); its configured execution branch remains unverified, not a native pass.

This release offers per-repository installation. Future-clone coverage is false, with startup/prelaunch as the required fallback. No live hook was installed. Integration entry journals have their own typed v3 variant; core state remains v1/v2. Current Git contract checked against https://git-scm.com/docs/git-hook and https://git-scm.com/docs/githooks on 2026-09-05. Next: MASK-0027.

## Host adapter slice

Revision `93b595dbfd2dbf8f660979ef6b2ec61e5fadfa94`: 22 startup/ensure/lifecycle/launcher tests passed; 17 host/Git/protocol tests passed; affected subprocess and settings-preservation checks passed after review. Direct argv subprocess fixtures verify distinct Claude/Codex output, joint project/personal preflight, personal-only sessions, preserving unrelated host settings and trust files, changed-entry refusal, and prelaunch outside the writer lock. Claude requests reload; Codex startup stop is documented but actual host loading/gating is unverified. Codex setup integration returns a pinned command without replacing existing scripts.

Native versions observed: Claude Code 2.1.260; codex-cli 0.153.2. No host trust grant or live host configuration edit occurred. Current official contracts checked at https://code.claude.com/docs/en/hooks and https://learn.chatgpt.com/docs/hooks. Next: native macOS boundary, Windows target selection, and independent MASK-0044 inventory.

## Native macOS boundary

Revision `98c0f2e24666bcf0b50b11fd8f3973d80f2eaf9a`: installed launcher, native links and both host prelaunch version invocations passed; full boundary and limitations are in [readiness acceptance](../../development/readiness-acceptance.md). Required native Windows acceptance remains open. No terminal RFC claim.

Integration discovery: required MASK-0081 completes repository-boundary approval and user-level startup for future clones. These were missing from the first explicit-root slices; their bounded tests do not prove this broader workflow.

## Clone/startup integration follow-up

Revision `8ddb5d30c2fc876a458c11c9414d7e70fb822b1b`: python3 -B -m unittest tests.test_ensure tests.test_host_integration tests.test_workspace_lifecycle: 24 tests passed. A generated user-level adapter command readies a future approved local clone and registered personal scope. Wrong-origin/outside/replaced-boundary requests and credential-bearing identities refuse; direct revoke refuses inherited authority. Project-local and user-level settings remain independently owned, with no actual host-loading claim.

The earlier explicit-root-only limitation is resolved at the fixture/public-command boundary. Native host first-prompt loading still uses the recorded fallback limitation. No live approval or user-level configuration was installed.

Integration follow-up MASK-0082 records the full-suite failure and inactive cleanup recovery edge discovered during the final scoped diff review. Terminal status remains open.

## Integration recovery fixes

Revision `c0d37e78d72802c90ae73f39a7d9e342612494f1`: Full integration at runtime revision 3a8182f ran 123 tests: 119 passes, three skips, one hook recovery failure. The reused path variable is fixed. The 33 affected Git/ensure/lifecycle/host tests all pass (47.140s), covering new-interpreter journal refusal, no unused-package dependency in inactive cleanup, and registered nested consumers without a filesystem crawl. Earlier 29 affected recovery/integration tests passed; unchanged full-suite results are reused.

Final scoped source diff reviewed against immutable RFC_BASE_SHA `9dc90df`. No known critical failure remains on the exercised macOS/public-command boundary. Named-hook execution on newer Git, native Windows and actual first-prompt host loading remain explicitly limited. Native Windows is the required open platform criterion; later core stages retain their live dependencies.

## Earlier stop boundary (resolved by Windows acceptance)

All currently eligible unattended slices are complete. MASK-0029 is blocked on selecting a native Windows test station; its required evidence is not waived. The dependency graph therefore keeps MASK-0067 and stages B–D open. Optional stage E and the two Inbox tracking items remain deferred. No independent review agent was used; the integrator reviewed the scoped diff and consumed one integration suite plus focused defect rechecks.

Final capability reconciliation marks launch network-capable because the external host may use network services; ensure stays local, inventory remains observational, and pending readers advertise 1/2/3. Direct capability assertions passed. The change is metadata only; prior runtime checks remain relevant.

Task-created scratch root `.mask/generated/implement-rfc/pack-work` held only finish decision files, whose records have been consumed into Done cards. It is removed after consumption. No task worktree or verification checkout was created; test-owned temporary roots were cleaned by fixture teardown. The original untracked `.DS_Store` is preserved. No push, publication, live adapter install, consumer migration, credentials or trust changes occurred.

## Final readiness closeout

MASK-0029 is Done at `a51dab1`. Native Windows fixes are `c03f85c`; the precise
initial failures, affected rechecks, native hosts and cleanup are recorded in
[readiness acceptance](../../development/readiness-acceptance.md). The original
Windows-station blocker is resolved. Planned followups MASK-0081 and MASK-0082
are integrated and Done alongside MASK-0024–0029.

The final scoped implementation was reviewed against immutable RFC_BASE_SHA
`9dc90df45febf2a6e048ace60a4ac959807aaaf6`, reusing the prior integration review and
unchanged passing evidence. The Windows delta corrects separator handling,
named-hook argument forwarding and CRLF schema comparison, with focused checks
covering each. No known critical failure remains at the accepted readiness
boundary. First-prompt skill loading and native host trust/gate behavior are
explicit limitations; AC06 permits the documented prelaunch fallback.

RFC-MASK-0006 is Auto-Verified at this bounded local-source readiness boundary.
Later source/pin/profile/fleet RFCs remain separate work and are not completed
by this closeout. No live consumer or host configuration was migrated.
The persistent station/source checkouts are retained at the owner's request;
the invisible SSH runner stopped and released its lease. The separate direct
verification clone and transfer archives were deleted after their results were
consumed. The owner's manual clone and original untracked `.DS_Store` are untouched.
