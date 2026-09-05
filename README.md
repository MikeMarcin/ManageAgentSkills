# MASK — Manage Agent SKills

This is an initial documentation scaffold for the MASK implementation pack. Reconcile it with any existing repository rather than overwriting prior instructions.

The program is a dependency-free Python 3.11+ CLI in MikeMarcin/ManageAgentSkills. It reads skill payloads from a separate local MikeMarcin/AgentSkills checkout, manages .mask.json membership and machine-local registration, and creates per-skill directory symlinks for Claude and Codex.

No finished implementation is claimed by this scaffold. Follow docs/rfcs/README.md and docs/issues/README.md. The implementation agent completes usage, bootstrap, update, recovery and platform documentation as the CLI lands. Runtime protocol and implementation details live in the RFCs; do not document planned commands as shipped until they exist.

Keep repository visibility and inherited-source licensing unchanged until explicitly reviewed. Generated links and machine state are not project source. Project facts live under `.mask/skill-config/implement-rfc/`, separate from the shared skill payload.
