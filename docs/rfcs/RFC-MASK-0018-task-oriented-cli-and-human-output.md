---
id: "RFC-MASK-0018"
title: "Task-oriented CLI and human output"
status: "Auto-Verified"
owner: "MikeMarcin"
created: "2026-09-08"
---

# RFC-MASK-0018: Task-oriented CLI and human output

**Auto-Verified at its public boundary (September 9, 2026).** Implemented by MASK-0083 to MASK-0087 and MASK-0091 from base `6d80121`; closeout with per-criterion evidence is [MASK-0093](../issues/60-done/MASK-0093-close-human-cli-correction.md), native lanes in [corrective-baseline.md](../development/corrective-baseline.md). Host loading of skills/roles is outside this RFC (RFC-MASK-0019). Live import of packet `RFC-MASK-0018` (no renumber needed; live RFCs ended at RFC-MASK-0017). Retained packet: [assets/mask-corrective-ux-readiness/](assets/mask-corrective-ux-readiness/README.md); import record: [LIVE_IMPORT](assets/mask-corrective-ux-readiness.LIVE_IMPORT.md).

Amends applicable current behavior from RFC-MASK-0001, 0003, 0005, 0006 and the implemented reporting/selection slices. Historical RFCs and evidence
remain unchanged; update current contracts when this implementation lands.

## Decision

The ordinary MASK interface must express a complete user task, not expose its
internal deployment protocol. Add install/remove/list over the existing engine;
make human output the default across all commands; integrate meaningful consent
instead of requiring plan-hash copying; simplify everyday update/readiness use.
Keep the machine API explicit with --json and preserve scope/ownership semantics.

## Evidence and failure mechanism

In the supplied snapshot, mask.py::main serializes the entire successful result
as indented JSON when --json is absent. tests/support.py::Fixture.call appends
--json to every invocation. The README teaches initialization, registration,
preview, manual hash extraction, apply, and diagnostic steps for a basic install.
These are distinct defects at the public journey boundary, not missing safety
checks. Existing pinned consumers additionally reject the legacy string
membership mutation functions, so a superficial alias cannot repair that path.
See the retained pack's SOURCE_BASIS.md for exact source hashes and locations.

## Contract

The normative contract is `assets/mask-corrective-ux-readiness/contracts/CLI.md`.
It fixes command meanings, scope defaults and legacy update compatibility;
ordinary versus exceptional authority; output/stream behavior; and exit semantics.

The command inventory and capability descriptors continue to share one parser
registration model. The planner returns one structured result, with human and
machine renderers. Task services reuse the existing resolver, artifact preparation,
planner and journal; they do not shell out through a second orchestration layer.

All successful commands need intentional human layouts, not only inventory.
Errors must show relevant detail and safe remediation. A formatting-only change
must not cause different mutating behavior under JSON. Explicitly amend the
current blanket no-prompts rule while keeping automation and event hooks prompt-free.

## Completion boundaries

Ship the renderer before optional setup support. Current docs may describe only
the behavior actually integrated at each milestone. After RFC-MASK-0019 lands,
install/update/ensure final success includes declared workflow prerequisites.
Do not claim prerequisite completeness merely because RFC-MASK-0018's task and
link tests passed.

Use the proposed short README as an acceptance specimen, not an unconditional
replacement for the existing file before those commands work. Advanced engine,
source, migration, recovery and security reference material remains accessible,
but it no longer interrupts the first-project workflow.

## Out of scope

No CLI grammar rebuild beyond the required ordinary verbs/options, no daemon,
fleet/MCP/profile implementation, no quota experiment, no package-code trust
manager, and no automatic legacy-to-pinned migration. Do not make a simple local
install depend on unfinished roadmap features.


## Acceptance criteria

**RFC-MASK-0018-AC01** — **Complete install/remove.** From an unregistered project and an unregistered personal scope, one task command performs the requested additive/removal intent through the engine. Exercise legacy and pinned declarations; unrelated membership, pins, routes and scope remain unchanged.

**RFC-MASK-0018-AC02** — **Readable default results.** Every command has intentional human output without --json. The supplied six-row inventory becomes three truthful skill rows with separate Claude/Codex states, source and limitations. Help, version, empty, paginated, pinned and failure results do not dump the result envelope.

**RFC-MASK-0018-AC03** — **Machine compatibility.** Explicit --json emits one versioned result document, including handled errors and interruption. Format does not change effects or scope; redirected human output remains text, and operand/-- parsing is correct.

**RFC-MASK-0018-AC04** — **In-process consent.** Required interactive approvals are completed inside the task without human hash copying. No-op and already-authorized mechanics do not ask repeatedly. Noninteractive/event/JSON paths never prompt; --yes cannot bypass script/source/overwrite/scope authority.

**RFC-MASK-0018-AC05** — **Update the selected content honestly.** One normal update coordinates acquisition and a frozen guarded application with truthful scope. Dry-run/offline do not fetch, pinned unrelated/exact bindings remain fixed, and legacy shared impact is disclosed and separately authorized where expanded.

**RFC-MASK-0018-AC06** — **Failure and recovery preservation.** Stale inputs after consent, collisions, edits, busy/pending operations and interruption preserve the existing ownership guarantees and accurate exit/transaction/partial state. No new destructive shortcut or implicit migration is introduced.

**RFC-MASK-0018-AC07** — **README is the usable path.** The short current README and help are executed as written through the public CLI; normal recipes do not require --json, internal state edits, manually copied hashes, registration chores or knowledge of implementation helper scripts.

**RFC-MASK-0018-AC08** — **Public native acceptance.** Actual native macOS and Windows CLI/launcher/text/confirmation journeys are recorded at the exercised boundary, with focused regression checks. Test helpers do not inject --json or prepare the behavior being qualified. Unavailable required lanes stay open.

## Rollout and rollback

Import against live IDs, record the actual pre-implementation baseline, and
implement through the linked cards. Preserve existing interfaces where their
semantics remain supported; publish deliberate stricter readiness/consent changes
in capabilities and release notes. A compatible prior program is not automatically
safe after a new typed journal/schema has been written: finish pending recovery
before switching executables and retain the explicit updater compatibility guard.
Never delete user files or relax safety checks to make rollback look successful.

## Closeout

Exactly one linked closeout card records every criterion, actual command or
observation, outcome and implementation revision. A missing required native lane,
upstream handoff, or public journey remains open. Packet validation and synthetic
fixtures cannot supply those results. Reuse unchanged focused evidence; do not
create an exhaustive proof archive or repeated model-review loop.
