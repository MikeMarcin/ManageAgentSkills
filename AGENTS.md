# ManageAgentSkills: agent instructions

Read README.md, CONTRIBUTING.md, docs/rfcs/README.md, docs/issues/README.md, the requested live RFC and card, and the nearest nested AGENTS.md. Use the portable implement-rfc workflow with this repository's `.mask/skill-config/implement-rfc/` context. Both canonical skills are now deployed through managed links; verified retired bootstrap copies are retained outside discovery roots. Use the public CLI guide in README.md if the launcher is absent.

MASK is a local Python CLI, not a service or general package manager. AgentSkills supplies data; MASK does not execute skill scripts during installation.

Routine skill management uses `mask ... --json`, or the known absolute Python entrypoint if PATH is not configured. Inspect capabilities/state and preview meaningful changes. Preserve incremental versus exact-set intent. Never edit MASK's internal state or bypass a collision with destructive shell commands.

Preserve unrelated changes; stage explicit paths. No publication, credential grants, permission changes, unrequested Git push or migration of SRV/SamplePlanner. Test in temporary fixture roots/local bare remotes. No daemon, fleet sync, marketplace, force overwrite or copy fallback. Reorient from live boards and recorded closeouts after interruption.
