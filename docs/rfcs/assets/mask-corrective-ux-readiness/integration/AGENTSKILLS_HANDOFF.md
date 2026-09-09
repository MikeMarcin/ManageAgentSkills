# Explicit AgentSkills handoff — no silent cross-repository work

MASK's source snapshot and the shared AgentSkills snapshot are separate inputs.
This pack requests a MASK correction; it does not grant permission to modify
AgentSkills or all consuming repositories. The needed upstream integration is
specified here so it cannot be 'qualified' out of the test fixture.

## Upstream responsibilities

Publish implement-rfc's applicable required role set through the passive workflow
descriptor. For the supplied coordinator design it includes rfc-integrator and
the current permitted leaf roles, not the old routine/default naming scheme.
Derive names/routes from the actual current roles/routing configuration; do not
hard-code model IDs or use this pack to change model/effort policy.

Prefer committed, generic native definitions under neutral package paths.
Preserve role-specific tools, delegation limits, entrypoint selection, consumer
addenda and explicit routing/profile overrides. Where those facts cannot safely
be represented by universal static files, support author-time generation of
consumer-checked-in files plus their portable input/output lock. The first fresh
clone check must work without old .mask/generated ownership metadata.

For genuinely dynamic setup, provide a staged preparation entrypoint compatible
with WORKFLOW_READINESS.md. It reads the selected consumer context and frozen
inputs, writes only requested stage outputs, and does not deploy final files or
write the MASK registry. The supplied render_runtime_adapters.py does not already
satisfy this interface. Refactor/reuse its pure generation logic; do not copy it
into MASK. Preserve standalone authoring behavior where still useful.

The public implement-rfc entrypoint must check its required native role contract
before first delegation. Missing roles are a setup problem, not permission to
spawn default and call it an integrator. Readiness does not require rereading the
entire runtime/routing manuals on every normal start. Use a compact check/result
and branch only on actual missing requirements.

The common startup/Status identity format must be authored once for all roles.
Report workflow role, actual native role requested, configured model/effort, and
observed route separately when available. Unknown remains unknown. A launcher
record should preserve dispatch identity even if a child omits its prose banner;
do not spend model turns enforcing cosmetic repetition. MASK reports configuration,
not fabricated child telemetry, and does not add a native-session supervisor.

Update manage-agent-skills instructions to use explicit --json for automation and
the supported complete task commands; retain precise raw plan/guard examples in
an advanced reference. Keep AgentSkills and MASK human README instructions in
agreement. Tests must not quietly pre-render consumer fixtures or inject --json
into a human scenario.

## Required handoff evidence

Record the upstream card and actual integration commit, selected package digest,
workflow descriptor identity, required role names, authoring/staged interface,
input-lock rules, and focused tests for two distinct consumer contexts. Confirm
consumer addenda and explicit route overrides do not leak or get erased. Include
a new-skill/old-role fixture, a checked-in fresh-clone fixture, and a missing
rfc-integrator failure before delegation.

MASK's integration card consumes that specific handoff and tests through normal
MASK commands. No ASK IDs, PASS results, live consumer changes, or model sessions
are pre-authorized or pre-created by this file. If upstream work is not available,
ship the independently complete CLI correction and keep RFC-MASK-0019 open.

## Old-program/new-skill skew

Require the implemented `workflow_readiness_v1` capability and corresponding
result before accepting complete MASK readiness. An older MASK may ignore the
new sidecar and return a successful link-only ensure. Test that this cannot pass
the shared skill's preflight. Report the unsupported program or obtain explicit
standalone-check authority; do not fabricate native roles, silently choose
`default`, or update the user's program/schema as a side effect.
