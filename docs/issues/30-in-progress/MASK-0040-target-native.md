---
schema: "implement-rfc.card.v1"
id: "MASK-0040"
title: "Verify native scope-specific pinned targeting"
status: "In Progress"
rfcs: ["RFC-MASK-0009"]
depends_on: ["MASK-0039", "MASK-0037"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "target-native", "stage": "B — selection semantics", "provisional_id": false}
---

# MASK-0040: Verify native scope-specific pinned targeting

Governing RFC: [RFC-MASK-0009](../../rfcs/RFC-MASK-0009-scope-agent-targeting-and-compatibility.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Exercise one skill with different personal and project agent choices on both native supported platforms. Record physical links, per-agent names and compatibility outcomes. Reuse unchanged readiness loading evidence when relevant; do not invent a full host/OS matrix.

Own only: `tests/test_targeting.py`, `tests/test_user_scope.py`, `docs/development/targeting-acceptance.md (new)`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0009-AC01: The same skill has independently configurable personal and project agent sets, with new selections defaulting to all supported/enabled agents and no executable-detection side effects.
- RFC-MASK-0009-AC02: V1 migration preserves explicit and inherited target behavior; per-skill edits/locks/plans remain guarded and no-op stable.
- RFC-MASK-0009-AC03: Generic, absent and agent/platform-specific metadata produce distinct truthful reports; explicit incompatibilities block, and conditional/inapplicable bindings are not called installed.
- RFC-MASK-0009-AC04: Multi-source name conflicts, conflicting profiles and user/project duplicate names are explained without overwriting content, silently renaming packages or assuming host precedence.
- RFC-MASK-0009-AC05: A single adapter contract drives paths/capabilities/validation, and existing native Claude/Codex scope tests cover the change; additional agents stay unadvertised until independently proven.

Proposed direct checks (not executed by this packet):

- Run selected native Windows and macOS user/project targeting checks; keep a missing platform result open.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Integration candidate: ececbf7e391211744b7e3c7b2c628da0136e8b77, source d33323e6a9f7054ae7ffc073bd6d082c0110b7c7 plus targeting c2fa4962f06349d33169fae478b69b7f758e7bb4. Native Windows execution is in progress; no Windows result is asserted yet.

## Current verification

The macOS unittest loader check passed 11 selected methods in 123.364s, no skips: seven combined pin/migration/update recovery methods, independent v2 user/project agents, legacy scope independence, collision preflight and linked-parent/overlap refusal. Exact names and fixture cleanup will be retained in the targeting acceptance note. All eleven tracked fixture roots were absent after execution.

The Windows run uses existing example-win-host SSH, explicit noninteractive PowerShell and native Python314 in a detached disposable checkout of the candidate. It validates the shared implement-rfc project context before the unittest loader. Owned remote root: C:/Users/example/AppData/Local/Temp/mask-native-driver-6_3rql1g-vql84kve. The owner clone/station is not its output root. Run the new engine/migration/update/targeting/compatibility/adapter/conflict suites, changed lock guard, three native user-scope ownership methods, launcher suite and native Windows Job assignment-prerequisite test. Reuse unchanged earlier native source/import/artifact coverage. Exact remaining fixtures are reported by the temporary driver before cleanup.
