---
id: "RFC-MASK-0017"
title: "Staged migration, agent workflow handoff and personal-use acceptance"
status: "Accepted"
owner: "MikeMarcin"
created: "2026-09-05"
---

# RFC-MASK-0017: Staged migration, agent workflow handoff and personal-use acceptance

**Delivery stage:** A–D — integration and owner workflow. **Packet status:** proposed implementation contract; no implementation or acceptance is claimed.

**Predecessors:** RFC-MASK-0006, RFC-MASK-0007, RFC-MASK-0008, RFC-MASK-0009, RFC-MASK-0010, RFC-MASK-0011, RFC-MASK-0012, RFC-MASK-0013.

The new behavior below explicitly extends the historical v1 scope. Preserve settled RFCs 0001–0005; update current architecture/user documentation only when the relevant implementation ships. See [source reconciliation](../design/SOURCE-RECONCILIATION.md), [shared contracts](../design/CONTRACTS.md), and [references](../design/REFERENCES.md).

## Decision

Integrate the core features in small usable milestones rather than require all optional extensions before the owner benefits. Import new RFCs/cards without editing settled history, then prove ordinary workspace readiness, pinned personal/project use and the named all-devices installation story.

The pack is implementation planning, not completed implementation. Existing native closeouts establish only the historical boundaries they actually exercised. Native Windows personal scope, host first-prompt discovery and real new fleet behavior need new evidence. Do not turn source-level inspection or packet validation into product acceptance. [M1: RFC-MASK-0005 closeout]

## Milestones

**A — workspace readiness.** RFC-MASK-0006 lands independently on the legacy source mode. Git/host lifecycle calls ensure automatically within one-time approved scopes; no new-source/fleet dependency blocks this improvement.

**B — reproducible content and targeting.** RFC-MASK-0007/0008/0009 deliver multiple sources, provenance, exact artifact locks and scope-specific all-agent defaults with declared compatibility. Explicit migration preserves older ownership, dirty authoring work and pending recovery. Do not advertise partial schema fields as fully supported during the milestone.

**C — composition and understanding.** RFC-MASK-0010/0011 deliver portable personal profiles, flat bundles, where-used, content diffs and impact. A portable profile can rebuild a configured new machine without copying local state.

**D — owner's fleet.** RFC-MASK-0012/0013 deliver enrolled device transport, source/copy publication under delegated authority, signed desired state, per-device receipts, and optional ongoing catch-up. Updating the canonical management skill is a required handoff for the one-request agent workflow, but the CLI does not depend on loading that skill.

**E — optional extensions.** RFC-MASK-0014/0015/0016 remain independent optional/stretch tracks. Core release can close without them, provided capabilities clearly state they are not implemented/enabled. Do not mark their RFCs terminal by calling them optional.

## Live source reconciliation before import

The supplied dump contains five settled RFCs and NEXT_ID `MASK-0023`. These are snapshot facts, not reserved IDs or a current Git baseline. The integrator checks the actual live board/counter/history, allocates the full selected card count through the canonical allocator on main, commits the real reservation, remaps packet IDs and records LIVE_IMPORT. Do not copy this packet's temporary next number over a live counter or fabricate allocator receipts.

Read the current canonical implement-rfc skill and external project context. The dump supplies MASK's context and wrappers, but omits the linked AgentSkills skill bodies. If bootstrap is needed, use the known installed CLI/direct entrypoint and supplied explicit manual fallback; do not invent canonical helper files or recreate another mutable board.

Retain the original ZIP unchanged under assets as provenance if desired. Live imported RFCs and cards become authoritative. Update the tracker by merging rows, not replacing historical README content. Exactly one closeout card owns each new RFC's acceptance record.

## Scope changes to current instructions

Revise current AGENTS.md, README.md, CONTRIBUTING.md, CLI/state contracts, remote-station documentation and implement-rfc project context as the relevant features ship. Replace blanket no-fleet/no-source-expansion language with precise effect/authority boundaries. Leave historical v1/v0.1.0 scope records and settled RFC status unchanged.

The current source distribution and schemas change deliberately. Capture actual RFC_BASE_SHA before source implementation, validate old journal recovery first, and keep the explicit program-upgrade/migration sequence. Do not weaken the old updater's schema safety check to force the new version through unnoticed.

## Canonical AgentSkills handoff

Request the AgentSkills integrator to update `manage-agent-skills` instructions for capabilities, ensure, source-qualified names, copy/tap choice, default all-agent intent, locks, portable profiles and one-request fleet install. It must use public CLI/tool contracts, preserve selection-vs-replacement intent and describe partial/offline results correctly. No shell snippets should mutate internal state or replace unmanaged directories.

Where useful, AgentSkills adds reviewed `mask-skill.json`, source-index/bundle definitions and provenance records. Preserve existing notices and project-specific workflow context. Actual skill payloads were not supplied, so the handoff record must name the upstream revision and a local integration check when implemented. The packet does not assign speculative live ASK IDs or invent completion hashes.

The management workflow should need a choice only for genuinely unresolved intent (ambiguous name, absent copy/tap policy, new authority). It should not ask the user to manually register every worktree, hand-copy a hash, or say “done” when the CLI can report completion itself. All deterministic work belongs in durable MASK operations; the agent chooses scope, interprets ambiguity and reports outcomes.

## Focused acceptance scenarios

Use temporary roots/local bare remotes for normal testing. At milestones, run one integration-focused pass over changed boundaries; reuse unchanged evidence. Broader suite/review is justified for combined persistence or remote-authority changes, not automatically multiplied across every interpreter/OS/host combination.

For authorized live dogfood, record the exact selected checkouts/homes/devices, actual program/source revisions and preserved backups. No implicit migration of every known personal project is authorized by creating this pack. Roll out to named scopes after the user/integrator selects them; real changes are never performed by packet generation.

Representative personal-use walkthrough: clone an approved project; start each supported agent and observe skills; create another worktree with a distinct pinned revision; switch branches and verify membership/revision convergence; inspect where-used/update impact; export/import personal selections on a second configured machine; request one skill by URL as copy and another as tap across enrolled devices; bring an offline device back; receive truthful final receipts. Include one controlled collision, one unreachable artifact and one interrupted local transaction.

Windows and macOS cards must name actual native environments. No invented dates, host versions, passing results, attended decisions or hashes. Unavailable lanes stay open while independent work proceeds. Do not introduce mandatory manual attendance for mechanically observable results.

## Completion

Close the core integration RFC after A–D required criteria and the actual canonical management handoff are satisfied. Report optional E tracks and deferred additional agents/audit separately. The final documentation should explain one-time setup and ordinary daily operation, not require users to understand internal journaling to keep skills available.

## Acceptance criteria

- **RFC-MASK-0017-AC01** — Live import preserves historical RFCs/cards/counters, uses real reservations and baseline commits, and imports one closeout per RFC with no fabricated evidence.
- **RFC-MASK-0017-AC02** — Readiness, multi-source/pinning/targeting, composition/reporting and fleet milestones have focused integrated evidence and current public docs/capabilities that match what shipped.
- **RFC-MASK-0017-AC03** — Actual canonical AgentSkills management guidance and selected metadata/bundle/provenance handoffs are recorded by upstream revision and verified locally without duplicate tracker ownership.
- **RFC-MASK-0017-AC04** — Explicit selected-scope migrations preserve declarations, user data, ownership/recovery and source history on native macOS/Windows; unknown/unavailable acceptance stays open.
- **RFC-MASK-0017-AC05** — The real one-request fleet story demonstrates exact revisions, online/offline reporting and catch-up on distinct devices; optional MCP/vault/public-release work remains separately tracked and does not falsify core status.

## Live authorization

Accepted for implementation by the owner’s 2026-09-05 import-and-implement request. Follow the live card dependencies; native and external acceptance remain open until directly exercised.
