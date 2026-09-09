# Implement the MASK corrective pack

Implement RFC-MASK-0018 and RFC-MASK-0019 from this pack in ManageAgentSkills.
Preserve unrelated work and closed RFC history. Read the actual local instructions
and scoped consumer rules, then import with live IDs using IMPORT.md. Record the
real pre-implementation revision in both closeouts; do not invent a baseline.

Deliver the human renderer early. Then deliver complete install/remove/list,
integrated confirmation, and update workflows over the existing engine. Finish
declared workflow readiness, checked-in role assets, and optional consented setup.
The engine, not a chain of shell commands or another LLM, coordinates mechanics.

User decisions are settled: normal output is human-readable unless --json is
passed; everyday tasks are one command; manual plan-hash copying is not the human
workflow; required scripts prompt for approval in interactive ensure; checked-in
roles are valid; a linked skill with missing required roles is not ready.

Use the current planner, source resolver, artifact store, typed journal, adapter
registry, and structured result object. Do not implement only aliases that retain
--apply/registration ceremony. New task commands must work for existing legacy
and v2 pinned selections and preserve unrelated pins and scope choices. Do not
silently migrate legacy consumers or widen a local update to every consumer.

Use explicit --json for agent automation. Read the confirmation/format rules in
contracts/CLI.md: JSON changes presentation, not selection or safety policy.
Keep observational commands and dry runs passive. Package code, including a
package-provided validator, is code execution and needs the stated authority.

Role generation and shared startup/reporting belong to AgentSkills. Consume the
small, explicit handoff in integration/AGENTSKILLS_HANDOFF.md. An absent upstream
handoff is a recorded dependency, not permission to copy its renderer into MASK,
edit the AgentSkills checkout through a skill symlink, or call generic agents
rfc-integrator. No live SRV/PLN/other consumer changes are authorized by this pack.

Do not bootstrap circularly. The candidate ensure does not have to exist before
implementing it. When the current host lacks required native roles, use an
explicitly approved existing setup or direct nondelegating implementation; never
silently claim that default loaded a missing named role. Record that bootstrap
separately from the candidate's acceptance journey.

Start the main regressions from a fresh/unregistered project and from the actual
failure shape: new shared skill, stale/missing roles, no pre-rendered fixture.
Exercise terminal commands without --json. Tests must not hide registration,
approval, native role creation, or hash copying in fixture setup. Pure unit tests
remain useful but do not qualify the public workflow by themselves.

Run focused checks per milestone and reuse unchanged evidence. One substantive
integration review is appropriate for the new executable-setup boundary; do not
create repeated review/polling loops. Required native macOS/Windows checks stay
open until actually run. Do not start paid model sessions without a separate
approved budget. Keep requested/configured routes distinct from observed runtime.

Publish current README/help only with working commands. Before closeout, replay
the README through the public CLI, confirm failures preserve content and truthful
status, and record actual test commands/results/revisions. No push, publication,
credential or permission change, bulk migration, or quota purchase is implied.
