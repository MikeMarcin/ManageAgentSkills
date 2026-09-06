# Source reconciliation and changed decisions

## Evidence basis

**M1:** `manage_agent_skills_project_source.md`, generated 2026-09-05T16:45:20-07:00; 81 included source/documentation files; runtime `VERSION = '0.2.0'`; SHA-256 of the actual supplied dump bytes: `57ac9173be3043ab6c3b7a6fb047542e0fad699aeafa9e7687c9a80b5ce36a8a`.

**M2:** `MASK-Competitive-Feature-Adoption-Report.md`, user-provided report from this conversation. It is an inspiration/research record, not current implementation authority. Its earlier prioritization and suggested deferrals are superseded by the user's later decisions recorded below.

**U1:** The user's latest request accepts readiness as the next workstream, selects the feature set and requests this downloadable RFC pack. Those requirements take precedence over the earlier recommendation to defer taps, version isolation or fleet design.

The pack inspected the supplied snapshot, not a live GitHub repository. It did not run the MASK test suites, change live source, reserve issue IDs, enroll devices, install host hooks, import real skills, or publish repositories. Packet validation is not product verification. Linked AgentSkills payloads and the canonical implement-rfc helper implementation are absent from M1; its external consumer context and board-wrapper contracts are present.

## Implemented baseline retained

| Area | Evidence in M1 | Implication |
|---|---|---|
| Python/JSON public CLI | mask.py; result schema; CLI contract | Reuse result envelope, capability metadata, error/exit conventions |
| Personal scope | README, RFC-MASK-0005, tests/test_user_scope.py | Do not propose “global skills” as wholly new |
| One local canonical source | config(), package(), fs.plan() | Federation and pinned artifacts are real architecture changes |
| Whole-selection agent targets | manifest(), project_dispatch(), fs.plan() | Add per-skill and per-scope targeting deliberately |
| Register-and-apply | project_dispatch() | Do not mandate plan/copy-hash/apply/doctor for every startup |
| Ownership/recovery | mask_fs.py; state v1/v2, journal v1/v2 | Preserve exact leaf checks and explicit recovery |
| Update scope | mask_git.update() | Existing all-consumer behavior is correct only for the shared mutable source mode |
| Source identity | checkout_preconditions() | Basename comparison is not full repository binding |
| Host loading | doctor()/project.show() report not_verified | New first-prompt claims need actual host evidence |
| Source publishing | AGENTS.md/CONTRIBUTING/RFC0003 disallow automatic push | New publish/runner authority must be narrow and explicit |
| Native history | earlier closeouts and RFC0005 closeout | Old Windows checks do not prove new personal/fleet/host behavior |
| Tracker | RFCs 0001–0005; NEXT_ID MASK-0023 | All new IDs in this pack are provisional until live reservation |
| Stations | docs/development/remote-stations.md empty | No device is assumed enrolled or authorized |

## Concrete implementation traps to fix

1. `mask_fs.plan` retains an old raw link value whenever a prior record exists. That is appropriate while every desired target is one source path, but wrong for artifact retargeting. Compute desired new artifact path while independently checking the old raw value.
2. `validate_pending` currently validates both sides against `config.source.root/skills/<id>`. Its new validator must derive before/after targets from their versioned artifact records and permit only the bounded scope transition.
3. `core.git` disables directory hooks with `core.hooksPath`. New named hooks require separate suppression. Test configured hook execution explicitly, rather than reusing only a `.git/hooks/post-merge` fixture.
4. `state()` validates cached manifests through the current v1 parser, and `recover()` revalidates packages from one source. State v3 and typed declaration readers must preserve old parsers for old journals and resolve new records through their artifacts.
5. `mask_install.validate_program` rejects changed schema bytes. Use a reviewed program update plus explicit migration. Do not force an incompatible schema through self-update.
6. `package()` accepts regular support files but does not classify host autoactivation packages. Add a package-kind boundary for imported plain skills without falsely describing it as a complete content audit.
7. Adapter constants and target enums are repeated across modules/schemas. Consolidate their definition before broadening targeting semantics.
8. The source dump wrapper delegates allocation/documentation checks to the linked canonical skill. That implementation was not included; the integrator must use the real deployed helper, not a fabricated replacement.
9. The current COMMANDS/parser builder supports at most two command components. New `fleet device enroll` and related paths require one hierarchical registration model that drives argparse and capabilities, not a second hand-written parser. Preserve existing leaf commands, `update` versus `update report`, option placement, `--` operand separation, JSON errors and no silent command abbreviation.

## User-approved features versus proposed design decisions

**Approved feature requirements:** readiness first; where-used; update diff/impact; portable personal selections; bundles; upstream provenance; per-skill/per-user-or-project targeting defaulting to all supported agents; advertised compatibility/generic support; multiple sources/taps; true pinning; agent-driven all-device installation; a design for continued fleet convergence; security/public trust as a stretch goal after personal usefulness.

**Proposed implementation choices in this pack:** `ensure` command naming; additive named Git hooks when available; immutable content store; v2 selection/v1 lock schemas; flat bundle expansion; private Git desired-state store; OpenSSH transport and signatures; optional scheduled pull runner; optional stdio MCP facade; credential-provider-first vault design. These are design recommendations, not features already implemented or separately ratified by the user.

**Deferred by the user:** heuristic passive audit and additional agent support. The latter is tracked as an adoption opportunity with actual-host evidence prerequisites.

## Explicit amendments to earlier recommendations

The latest request reverses earlier deferral of multiple sources and true version isolation, so both are core scope. Fleet synchronization is now in scope as opt-in functionality, not a forbidden category. Core remains usable without any runner/service. “Copy” means a curated import, never a silent symlink-to-directory fallback. Normal readiness may restore missing approved exact locked bytes; it may not resolve newer upstream content. MCP management means an optional facade for MASK's own API; arbitrary third-party MCP-server lifecycle is not needed for the accepted skill-install story.

Historical RFCs/release notes remain historical. New RFCs explicitly extend their scope, while current instructions/capabilities change only when corresponding functionality ships. No blanket repo visibility change, credential grant, privilege change, destructive filesystem workaround or unattended program update is authorized.
