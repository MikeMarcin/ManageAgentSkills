---
schema: "implement-rfc.card.v1"
id: "MASK-0039"
title: "Consolidate adapter metadata and reject deployment-name conflicts"
status: "Done"
rfcs: ["RFC-MASK-0009"]
depends_on: ["MASK-0038"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "adapter-contract", "stage": "B — selection semantics", "provisional_id": false}
acceptance: [{"criterion":"RFC-MASK-0009-AC04","outcome":"pass","revision":"d33323e6a9f7054ae7ffc073bd6d082c0110b7c7","evidence":{"kind":"observation","detail":"Public two-source collision preserves controls/payloads, disjoint agents deploy, user/project warnings preserve both scopes; pure equal-artifact union and attributed conflicts passed."}},{"criterion":"RFC-MASK-0009-AC05","outcome":"pass","revision":"d33323e6a9f7054ae7ffc073bd6d082c0110b7c7","evidence":{"kind":"observation","detail":"Audited adapter data drives runtime paths/capabilities/validation/hazards; schema enum parity and installed runtime plus host protocol checks pass locally. Native integration remains0040."}}]
---

# MASK-0039: Consolidate adapter metadata and reject deployment-name conflicts

Governing RFC: [RFC-MASK-0009](../../rfcs/RFC-MASK-0009-scope-agent-targeting-and-compatibility.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Drive paths/enums/capabilities/package-kind guard/discovery claims from one audited adapter contract. Detect source-name collisions per consumer/agent and explain scope shadowing without rewriting names. Test unknown future metadata separately from unsupported requested adapters; add no new supported agents.

Own only: `mask_adapters.py (new)`, `mask.py`, `mask_core.py`, `mask_fs.py`, `mask_pinned.py`, `mask_selection.py`, bounded adapter-data integration in `mask_integration.py` and `mask_packages.py`, runtime inventory in `mask_install.py`/`tests/test_launcher.py`, current README/CLI documentation and affected schema enum parity, `tests/test_adapters.py (new)`, `tests/test_selection_conflicts.py (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0009-AC04: Multi-source name conflicts, conflicting profiles and user/project duplicate names are explained without overwriting content, silently renaming packages or assuming host precedence.
- RFC-MASK-0009-AC05: A single adapter contract drives paths/capabilities/validation, and existing native Claude/Codex scope tests cover the change; additional agents stay unadvertised until independently proven.

Proposed direct checks (not executed by this packet):

- python -B -m unittest tests.test_adapters tests.test_selection_conflicts tests.test_cli_protocol

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Dependency MASK-0038 is Done at 4291d5d; source c2fa4962f06349d33169fae478b69b7f758e7bb4. Native acceptance remains MASK-0040. No implementation result is asserted for this slice.

## Bounded implementation decisions

One audited built-in adapter contract owns Claude/Codex IDs, project/user discovery paths, current supported native platform boundary, discovery/reload/gate claims, reserved names and package-kind hazards. Existing readiness evidence remains honest about host loading. Derive runtime paths/capabilities/validation from this data and test persisted schema enum parity. Unknown future publisher metadata is distinct from an unsupported requested adapter. No new adapters or executable plugins.

The pure attributed contribution seam merges identical coordinate/artifact positive target edges by union and retains every origin; absence or an ordinary explicit agent list is not a denial of another contribution. Different artifact or repository-authority claims for the same applicable coordinate refuse explicitly until a recorded deviation/override can resolve them; never choose last contribution. Equal payload/metadata/provenance digests under the same approved repository identity merge even if commit/selector differs. Retain all exact origin/resolution pairs and choose the lexically canonical full resolution as the documented representative for the identical destination. Different coordinates sharing an invocation name conflict only at a shared consumer/agent destination and explain both origins/digests. Disjoint agents/scopes are allowed. Report user/project duplicate names as shadowing without asserting host precedence or rewriting payloads. Public profile storage and bundle-local manual choices remain RFC-0010.

Focused checks: public two-source collision and disjoint-agent deployment, pure identical-union/conflicting-version contributions, public user/project shadow warning, adapter path/capability/schema/package-hazard parity and CLI protocol. Reuse existing native host evidence where unchanged; run the newly integrated native path once at MASK-0040. One shared-checkout source writer; primary alone stages/commits/changes the board.

## Integrated result

Source revision: `d33323e6a9f7054ae7ffc073bd6d082c0110b7c7`.

One immutable built-in adapter contract drives paths, validation, startup settings/capabilities, reserved names and passive package hazards. Each adapter records its own evidence/platform boundary; new rows default to unverified claims. Claude/Codex native readiness evidence remains separate from actual host loading, and Linux behavior remains best-effort/unverified. Persisted adapter enums pass parity without schema changes.

The attributed evaluator merges equal artifact/repository authority by positive agent union, retains exact resolutions and origins, evaluates when before metadata/conflicts, and blocks effective artifact/name conflicts without last-wins behavior. Public plan/apply/show expose user/project discovery-name shadowing and truthful observed/prospective status. Full pinned where-used reporting remains RFC-0011; public profile contribution storage remains RFC-0010.

Local direct evidence (macOS):

- Initial adapter and pure-contribution unit selection: 8 passed in 0.019s.
- Combined public/unit check: 16 passed in 19.415s, no failures or skips. Actual command was a `python3 -B -` unittest loader wrapper selecting `tests.test_adapters`, `tests.test_selection_conflicts`, `tests.test_cli_protocol`, `tests.test_launcher.LauncherTests.test_program_update_separate_and_incompatible_refused`, and `tests.test_host_integration.HostIntegrationTests.test_host_specific_ready_and_blocked_protocols`. It wrapped Fixture.setUp to record roots, ran TextTestRunner/loadTestsFromNames, and confirmed remaining roots were empty.
- After adding the future-metadata implicit-all exclusion assertion, `python3 -B -m unittest tests.test_adapters.AdapterTests.test_future_publisher_assertion_is_not_requested_adapter_support`: 1 passed in 0.007s, no skips.
- Twelve affected Python syntax checks and final git diff --check passed. Primary bounded integration inspection found no additional failures beyond addressed equal-artifact semantics and explicit per-adapter evidence fields. No additional independent review was requested for unchanged policy authority.

The four tracked roots were /private/tmp/mask-fixture-392aee6a, mask-fixture-zftuieac, mask-fixture-wx361zur and mask-fixture-l8f1vxq8 (same parent); all were confirmed absent. /tmp/mask-0039-context.txt was removed. User .DS_Store was preserved. MASK-0040 will consume native changed engine/migration/targeting evidence; no new native acceptance is asserted here.
