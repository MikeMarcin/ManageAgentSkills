# References and verification boundaries

External documentation below was retrieved on September 5, 2026 for narrow integration/security facts. It is not proof that those paths work on the user's installed host versions. Source-derived current behavior is M1; proposed MASK behavior is the RFC text. No competitor download/star figures are needed to implement this pack, and earlier disputed metrics are not repeated.

## Supplied materials

- **M1 — ManageAgentSkills project source dump.** Actual supplied `manage_agent_skills_project_source.md`; baseline and byte digest in SOURCE-RECONCILIATION.md. Relevant source symbols are cited inline by file/function. The dump is not duplicated in the distributable archive.
- **M2 — Competitive feature adoption report.** Actual supplied `MASK-Competitive-Feature-Adoption-Report.md`; useful idea inventory, superseded by the user's later feature/priority decisions.
- **U1 — Latest user instructions in this conversation.** Requirement decisions are preserved in DECISIONS.md and mapped to RFCs in TRACEABILITY.md.

## Primary external references

| ID | Source | Narrow fact used |
|---|---|---|
| E1 | [Git githooks](https://git-scm.com/docs/githooks) | Checkout/clone/worktree and post-operation hook boundaries |
| E2 | [Git named hooks](https://git-scm.com/docs/git-hook), [Git configuration](https://git-scm.com/docs/git-config) | Additive configured hooks, traditional-hook coexistence, per-event disabling; capability probe needed |
| E3 | [Claude Code hooks](https://code.claude.com/docs/en/hooks) | SessionStart skill reload output and its nonblocking decision boundary |
| E4 | [Codex hooks](https://developers.openai.com/codex/hooks) | Startup hook configuration and explicit trust; retrieved page redirects to official ChatGPT Learn |
| E5 | [Codex local environments](https://developers.openai.com/codex/app/local-environments), [Codex skills](https://developers.openai.com/codex/skills) | Worktree setup surface and skill discovery; actual native host acceptance still required |
| E6 | [Agent Skills specification](https://agentskills.io/specification) | Skills include instructions/resources/scripts and human compatibility metadata; MASK sidecar is its own contract |
| E7 | [Claude plugins reference](https://code.claude.com/docs/en/plugins-reference#skills-directory-plugins) | A plugin manifest inside a skill directory can change host activation behavior |
| E8 | [OpenSSH ssh-keygen](https://man.openbsd.org/ssh-keygen) | Detached file signing/verification, allowed signers and signature namespaces |
| E9 | [OpenSSH ssh](https://man.openbsd.org/ssh) | Remote command arguments form a command string; forwarding/security choices remain explicit |
| E10 | [MCP server development](https://modelcontextprotocol.io/docs/develop/build-server) | Established protocol/SDK and stdio integration; pin actual provider at implementation |
| E11 | [age upstream](https://github.com/FiloSottile/age) | Established encryption tool/provider candidate, not a homemade crypto scheme |
| E12 | [TUF security model](https://theupdateframework.io/docs/security/) | Mature update-security model to evaluate for a future program channel |
| E13 | [GitHub artifact attestations](https://docs.github.com/en/actions/concepts/security/artifact-attestations) | Optional release provenance/verification surface when publication is authorized |

The design does not require all of these tools in the core runtime. Git/Python remain the baseline; SSH/signing are selected optional fleet prerequisites, SDK dependencies belong to the optional MCP facade, and an encryption provider belongs to the optional vault. Current source instructions and real program capabilities are authoritative during implementation.
