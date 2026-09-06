---
schema: "implement-rfc.card.v1"
id: "MASK-0068"
title: "Verify and close RFC-MASK-0007"
status: "Ready"
rfcs: ["RFC-MASK-0007"]
depends_on: ["MASK-0030", "MASK-0031", "MASK-0032", "MASK-0033"]
closeout_for: ["RFC-MASK-0007"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "close-7", "stage": "B — source foundation", "provisional_id": false, "closeout": true}
---

# MASK-0068: Verify and close RFC-MASK-0007

Governing RFC: [RFC-MASK-0007](../../rfcs/RFC-MASK-0007-sources-imports-and-provenance.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Reconcile every acceptance criterion against direct evidence at the stated boundary. Capture the real pre-implementation RFC_BASE_SHA and actual implementation/handoff commits. Reuse unchanged focused results; run a broader integration/review only where combined risk warrants it. Keep unavailable native, host, real-device or upstream handoff rows open. Do not claim packet validation as product acceptance.

Own only: `docs/rfcs/RFC-MASK-0007-sources-imports-and-provenance.md`, `the corresponding live closeout card`, `current affected public contract docs`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0007-AC01: Two private/public-style local bare remotes expose independent taps and nested/root packages; name ambiguity, path/ref ambiguity and conflicting aliases are actionable rather than silently selected.
- RFC-MASK-0007-AC02: Source identity checks bind the approved repository and transport policy, not just the basename; credential-bearing/unsupported URLs and unapproved redirects refuse without leaking secrets.
- RFC-MASK-0007-AC03: Copy import preserves byte provenance and notices, refuses existing unrelated destinations, records local adaptations, and performs no commit/push unless separately authorized.
- RFC-MASK-0007-AC04: Adversarial package fixtures cannot traverse paths, introduce special entries, run hooks/filters/package scripts, silently activate a plugin, or bypass bounded resource limits.
- RFC-MASK-0007-AC05: Source lifecycle and legacy-config migration preserve current ownership and old declarations; removing a referenced source refuses and reads/dry-runs remain observational.
- RFC-MASK-0007-AC06: Public CLI/capabilities describe resolution, catalog-only addition, mutation/network boundaries and provenance verification levels with deterministic errors.

Proposed direct checks (not executed by this packet):

- python -B scripts/verify_documentation.py --root .
- Only missing or invalidated direct acceptance checks for this RFC.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Durable closeout anchor

RFC_BASE_SHA: 9dc90df45febf2a6e048ace60a4ac959807aaaf6

Planned cards: MASK-0030, MASK-0031, MASK-0032, MASK-0033.

Cross-repository handoff: unrecorded; attach only an actual upstream ID/revision when required.

## Closeout checklist

| Acceptance | Direct check / evidence | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0007-AC01 | Two independent local bare sources, root/nested/indexed discovery, qualified-name and ref/path ambiguity: source/discovery public subprocess tests; 31-test native source slice also passed. | Pass at stated source/import boundary | `c45f771ca0cfcef280cc0f4c0726a9bc65f4266b` (reuses unchanged earlier slice revisions) |
| RFC-MASK-0007-AC02 | Machine-v2 approved URI/transport checks, rewrite/redirect/scp refusal and corrected independent-review findings passed; explicit v1 compatibility remains documented until source migration. | Pass at stated source/import boundary | `c45f771ca0cfcef280cc0f4c0726a9bc65f4266b` (reuses unchanged earlier slice revisions) |
| RFC-MASK-0007-AC03 | Public copy/import/provenance integration preserves raw bytes, notice mappings, staged work and HEAD; collisions and late changed inputs refuse; explicit adaptation recording and cached assertions are covered. | Pass at stated source/import boundary | `c45f771ca0cfcef280cc0f4c0726a9bc65f4266b` (reuses unchanged earlier slice revisions) |
| RFC-MASK-0007-AC04 | Raw-object and import adversarial tests cover links/submodules/LFS/activation metadata, path aliases, byte/count/depth limits, bounded subprocess capture and native process-tree containment. Polled fetch storage may transiently overshoot. | Pass at stated source/import boundary | `c45f771ca0cfcef280cc0f4c0726a9bc65f4266b` (reuses unchanged earlier slice revisions) |
| RFC-MASK-0007-AC05 | Explicit source migration preserves exact old control/link bytes, repeated init and old recovery; live references prevent removal, and read/dry-run snapshots remain observational. | Pass at stated source/import boundary | `c45f771ca0cfcef280cc0f4c0726a9bc65f4266b` (reuses unchanged earlier slice revisions) |
| RFC-MASK-0007-AC06 | Registered CLI commands/capabilities and current docs agree on catalog-only approval, resolution_required, import/fetch effects, offline preview, provenance levels, limits and no default publication. | Pass at stated source/import boundary | `c45f771ca0cfcef280cc0f4c0726a9bc65f4266b` (reuses unchanged earlier slice revisions) |

Closeout review runtime: `rfc-reviewer`, GPT-6 Astra/high, for the source-authority surface. URL-specific redirect policy and scp path-identity findings were corrected and directly regression-tested. The primary reviewed copy publication/provenance integration; no repeated independent review was needed. Native source/guard results are recorded below; final import native verification passed after the CRLF correction recorded below.

## Resumed dependency scope

On September 5, 2026, the owner requested RFCs 0012/0013 next and their required
prerequisites. RFC-0006 is complete. The dependency path begins at MASK-0030,
then source discovery/import/guards, pinning and targeting before enrollment;
profiles and impact reporting are required before rollout composition. The
original RFC_BASE_SHA and planned card IDs above remain unchanged.

## Source catalog/discovery native evidence

Source revision `d45a8811860b6d03ced50d912a472dcd66df38e3` was checked out
from a local Git bundle on ExampleWinHost and exercised through native Windows Python
3.14.6 and Git 2.55.0.windows.3 using explicit PowerShell over the existing
`example-win-host` SSH alias as `ExampleWinHost\example`.

`python -B -m unittest tests.test_sources tests.test_source_discovery
tests.test_cli_protocol tests.test_git_update tests.test_launcher`: **31 passed**
in 82.637s, no skips. This proves the committed catalog/discovery and legacy
regression slice, not the later package guards or fleet. The implement-rfc
`project_config.py --repo-root CHECKOUT` helper validated the native checkout
after its temporary bundle origin was restored to the configured repository URL.

Exact temporary roots were
`C:/Users/example/AppData/Local/Temp/mask-catalog-win-0u27jcmp` and
`/tmp/mask-catalog-win-0u27jcmp`.
The native checkout was clean after tests and removed, clearing read-only
attributes only on its owned Git pack files during cleanup. No station was
restarted; the retained station and the owner's manual clone were untouched.
Local transfer/log files were consumed into this record and removed.

## Integration evidence and boundary

The MASK-0032 combined 21-test source/discovery/import/provenance/launcher pass
(71.760s) is the integration-focused pass: a public import is committed only by
the fixture, fetched as an independent tap and queried through frozen provenance.
Reuse earlier unchanged catalog, authority, legacy-update and native containment
checks; do not rerun the complete matrix merely for a new bookkeeping commit.

All four implementation cards were checked against the original RFC_BASE_SHA.
AgentSkills payload publication is outside this program implementation; no
cross-repository source-data handoff is required or claimed. This closeout does
not establish pinned consumers, fleet enrollment, host loading or a malware
safety verdict. The following dependency is MASK-0034 (selection/lock model).

## Final import and cleanup evidence

Implementation `c45f771ca0cfcef280cc0f4c0726a9bc65f4266b` and CRLF discovery
correction `815fb060e6d51ffe034141275a62fd3d1a898c96` complete the copy/provenance
slice. Native Windows ran all 14 import/provenance methods (177.030s): 13 passed,
and the remaining method exposed raw CRLF name inference. The corrected method
and explicit CRLF public inspect/show/validate regression passed (11.710s),
with unchanged passing methods reused and no skips. Native empty-directory and
case-collision refusal, byte/index preservation and provenance checks passed.

The shared `project_config.py` helper validated the native repository. Its clean
checkout under `C:/Users/example/AppData/Local/Temp/mask-native-driver-6_3rql1g-03nmm45j`
was removed. Consumed transfer/log files under
`/tmp/mask-native-driver-6_3rql1g`
were removed; only the task's native fixture driver is retained for the already
planned remaining native prerequisite checks. No owner clone, station, consumer
or credential settings were changed.
