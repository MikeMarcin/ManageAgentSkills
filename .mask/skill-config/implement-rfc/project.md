# MASK (Manage Agent SKills) project rules

## Identity and read first

Origin `MikeMarcin/ManageAgentSkills`. Confirm the actual Git root and branch before editing. Read root and nearest nested `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, `docs/rfcs/README.md`, `docs/issues/README.md`, the requested RFC and its linked cards. The root `README.md` and `CONTRIBUTING.md` are created/reconciled during bootstrap; do not replace existing instructions wholesale.

## Ownership and side effects

MASK owns its program, CLI schemas, tests, installation, and documentation. AgentSkills owns skill payloads and portable workflow helpers; reference explicit cross-repository handoffs.

Consumer migrations require explicit task scope. The approved unified workflow
pack includes all six named consumers. Preserve unrelated product work, commit
explicit paths and use temporary tooling fixtures/local bare remotes. No push,
publication, credentials or access changes are implied.

No daemon, fleet synchronization, marketplace or remote agent orchestration is part of MASK v1. Existing optional workflow helpers are retained without enabling them. The station registry is deliberately empty; unavailable optional models are limitations, not blockers.

## Direct surfaces and acceptance

The selected public surface is the Python CLI as a subprocess: argv, exit code, JSON stdout, stderr and actual filesystem/Git effects. Unit tests alone do not prove command behavior. Native symlink/launcher checks must name the OS actually exercised.

Run focused checks per card. No broad soak, proof-of-proof bundle or repeated unchanged verification. If no separate repository code-simplifier is installed, perform a concise local simplification review of changed code; do not invent a required new dependency. Optional independent review is risk-triggered; record the actual runtime when used.

## Board and closeout

Issue IDs are `MASK-NNNN`; RFCs are `RFC-MASK-NNNN`. Statuses: Proposed, Accepted, Implementing, Auto-Verified, Rejected, Superseded. Import supplied RFCs as Proposed; when directed to implement an agreed RFC, record acceptance and proceed. Auto-Verified is reserved for its actual acceptance boundary, not a promise or a test skip.

Every RFC has a card whose `closeout_for` includes the RFC. Before implementation, set `RFC_BASE_SHA` to a live pre-implementation Git commit and record its planned local cards. Cross-repository prerequisites use `external_depends_on`, a recorded upstream completion commit, and a local handoff check; never duplicate another repository's mutable board.

The closeout checklist has one row per RFC acceptance ID: check/command, outcome, and implementation commit. Unavailable native lanes stay open and are reported. No fabricated hashes, PASS results or attended-review requirements. Record optional review as `Closeout review runtime: ...`.

Only the integrator on main imports packs, advances NEXT_ID, writes reservations and edits tracker rules. Claimed cards live in their configured lane with matching status. Source-only lane work does not grant permission to mutate another repository's tracker. Retain the original packet as provenance; live cards and RFCs are authoritative after import.

Normally run one integration-focused pass at pack/milestone completion; select full relevant suites and critical review when warranted. No default exhaustive matrices, hermetic replay or manual checkpoints.
