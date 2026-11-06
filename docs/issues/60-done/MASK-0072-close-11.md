---
schema: "implement-rfc.card.v1"
id: "MASK-0072"
title: "Verify and close RFC-MASK-0011"
status: "Done"
rfcs: ["RFC-MASK-0011"]
depends_on: ["MASK-0044", "MASK-0045", "MASK-0046"]
closeout_for: ["RFC-MASK-0011"]
metadata: {"packet":"mask-readiness-fleet-2026-09-05","packet_key":"close-11","stage":"C — explainability","provisional_id":false,"closeout":true,"milestone_plan":{"id":"fleet-portable-composition","path":"docs/rfcs/plans/fleet-portable-composition/milestone-plan.json"}}
acceptance: [{"criterion":"RFC-MASK-0011-AC01","outcome":"pass","revision":"67e0c8451368d4dd4338f8a02a8e643998b952ed","evidence":{"kind":"command","detail":"Public where-used joins qualified taps, exact artifacts, both scopes, local/profile and bundle origins. Duplicate IDs stay distinct and actual host loading remains unverified."}},{"criterion":"RFC-MASK-0011-AC02","outcome":"pass","revision":"67e0c8451368d4dd4338f8a02a8e643998b952ed","evidence":{"kind":"command","detail":"The public diff and preview cover support files, binary sizes/hashes, compatibility targeting and provenance-only movement. A pinned personal consumer retained the old bytes while the project advanced."}},{"criterion":"RFC-MASK-0011-AC03","outcome":"pass","revision":"67e0c8451368d4dd4338f8a02a8e643998b952ed","evidence":{"kind":"command","detail":"Report and upgrade use the same approval hash. Public guarded apply succeeded after a paginated/exported preview. A moved cached ref with identical payload and changed consumer control bytes each caused a stale refusal."}},{"criterion":"RFC-MASK-0011-AC04","outcome":"pass","revision":"67e0c8451368d4dd4338f8a02a8e643998b952ed","evidence":{"kind":"command","detail":"Local inventory fixtures preserved state and unmanaged files and labeled unavailable consumers. An explicit dated projection fixture was stale against the current desired revision. A missing projection was unavailable. No live fleet probe ran."}},{"criterion":"RFC-MASK-0011-AC05","outcome":"pass","revision":"67e0c8451368d4dd4338f8a02a8e643998b952ed","evidence":{"kind":"command","detail":"A public saved receipt renders compact text, JSON and offline escaped HTML. It omits local roots, endpoint and package text. The first and repeated narrow CLI query observed one leaf, 738 declaration bytes, 1514 lock bytes and zero payload files or Git scans."}}]
---

# MASK-0072: Verify and close RFC-MASK-0011

Governing RFC: [RFC-MASK-0011](../../rfcs/RFC-MASK-0011-inventory-and-update-impact.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Reconcile every acceptance criterion against direct evidence at the stated boundary. Capture the real pre-implementation RFC_BASE_SHA and actual implementation/handoff commits. Reuse unchanged focused results; run a broader integration/review only where combined risk warrants it. Keep unavailable native, host, real-device or upstream handoff rows open. Do not claim packet validation as product acceptance.

Own only: `docs/rfcs/RFC-MASK-0011-inventory-and-update-impact.md`, `the corresponding live closeout card`, `current affected public contract docs`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0011-AC01: Where-used accurately joins source-qualified skill identities to each project/personal consumer, agent, origin and artifact, without conflating duplicate names or inferring unknown host loading.
- RFC-MASK-0011-AC02: Update reports include supporting-file/binary/metadata/provenance changes and affected consumers even when membership is unchanged, while distinguishing unaffected pinned consumers from legacy shared-source impact.
- RFC-MASK-0011-AC03: Reports and application use the same frozen candidate/plan; source/ref/control-file movement stales a guarded plan, while formatting changes do not.
- RFC-MASK-0011-AC04: Inspection preserves state and unmanaged content, scopes filesystem/network work explicitly, and labels unavailable consumers and stale fleet receipts.
- RFC-MASK-0011-AC05: Compact text/JSON and optional offline HTML safely display untrusted skill content with escaping/redaction; focused query workloads record actual bounded work.

Proposed direct checks (not executed by this packet):

- python -B scripts/verify_documentation.py --root .
- Only missing or invalidated direct acceptance checks for this RFC.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Durable closeout anchor

RFC_BASE_SHA: 9dc90df45febf2a6e048ace60a4ac959807aaaf6

Planned cards: MASK-0044, MASK-0045, MASK-0046.

Cross-repository handoff: none required for the local report engine. RFC-MASK-0013 owns production of live fleet observations.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0011-AC01 | Public where-used joins qualified taps, exact artifacts, both scopes, local/profile and bundle origins. Duplicate IDs stay distinct and actual host loading remains unverified. | Pass | 67e0c8451368d4dd4338f8a02a8e643998b952ed |
| RFC-MASK-0011-AC02 | The public diff and preview cover support files, binary sizes/hashes, compatibility targeting and provenance-only movement. A pinned personal consumer retained the old bytes while the project advanced. | Pass | 67e0c8451368d4dd4338f8a02a8e643998b952ed |
| RFC-MASK-0011-AC03 | Report and upgrade use the same approval hash. Public guarded apply succeeded after a paginated/exported preview. A moved cached ref with identical payload and changed consumer control bytes each caused a stale refusal. | Pass | 67e0c8451368d4dd4338f8a02a8e643998b952ed |
| RFC-MASK-0011-AC04 | Local inventory fixtures preserved state and unmanaged files and labeled unavailable consumers. An explicit dated projection fixture was stale against the current desired revision. A missing projection was unavailable. No live fleet probe ran. | Pass | 67e0c8451368d4dd4338f8a02a8e643998b952ed |
| RFC-MASK-0011-AC05 | A public saved receipt renders compact text, JSON and offline escaped HTML. It omits local roots, endpoint and package text. The first and repeated narrow CLI query observed one leaf, 738 declaration bytes, 1514 lock bytes and zero payload files or Git scans. | Pass | 67e0c8451368d4dd4338f8a02a8e643998b952ed |

Closeout review runtime: not run. A skipped required native/host/device check leaves the criterion open.

## Legacy inventory slice

Revision `79c3d611709cf719bb30169adafdd73fdd5646d3`: python3 -B -m unittest tests.test_inventory tests.test_manifest_registry tests.test_launcher: 14 tests passed. Direct CLI fixtures cover desired/owned/drifted rows, scope/agent filtering, pagination, unavailable cached selections, shallow unmanaged inspection, linked-parent refusal, and absent source targets. A narrow query inspected one leaf and one declaration with zero payload reads or Git scans. Full multi-source/pinned/profile/fleet fields remain explicitly unavailable until predecessor features ship.

This is the independently authorized legacy inventory boundary. Full RFC acceptance remains open for exact locks, layered selections and impact reporting. Temporary fixtures cleaned automatically.


## Current Stage C verification

The report candidate `67e0c8451368d4dd4338f8a02a8e643998b952ed` passed 19
macOS checks in `tests.test_report_rendering tests.test_inventory
tests.test_update_impact tests.test_human_output.RendererRegistry`. Native
Windows 11 build 26200, Python 3.14.7 and Git 2.55.0.windows.3 passed all six
cases in `tests.test_report_rendering tests.test_update_impact` without skips.
Native transfer, disposable checkout and fixtures were removed. The earlier
focused update and pinned-update suite passed 16 checks.

Two standalone narrow query processes took 180.0 ms and 157.0 ms in the
disposable fixture. Each inspected one link and one declaration/lock pair,
read the controls twice to detect drift, enumerated no directory and made
zero Git scans. The full inventory fixture also measured 42 package metadata
bytes when compatibility needed that file.

The original prepublication RFC_BASE_SHA stays recorded above. The surviving
pre-implementation boundary is `794cc2ac322135c940478dc6cab09f4465346b90`.
The scope-specific diff retains the historical inventory proof and closes
the exact local report boundary. The fleet row was a synthetic dated fixture.
Receipt production, signatures, real-device effects and agent host loading
have their own acceptance in the subsequent work.
