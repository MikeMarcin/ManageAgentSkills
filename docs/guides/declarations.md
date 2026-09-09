# Declarations, lower-level selection commands and file layout

The task commands in the [README](../../README.md) (`install`, `remove`, `list`) cover everyday use. This reference keeps the explicit declaration/registration/plan commands and the on-disk layout.

## Project declaration commands

Use an existing project root. These examples use `/absolute/path/to/project` as a placeholder; replace it before running them. `project init` creates an empty declaration, while `project register` records the project on this machine.

```sh
mask project init --project /absolute/path/to/project --json
mask project register /absolute/path/to/project --json
mask project require manage-agent-skills --project /absolute/path/to/project --apply --dry-run --json
```

Inspect the proposed actions and `data.plan_hash`. Apply that same proposal using its returned hash, then check the result:

```sh
mask project require manage-agent-skills --project /absolute/path/to/project --apply --expect-plan-hash RETURNED_HASH --json
mask plan --project /absolute/path/to/project --json
mask doctor --project /absolute/path/to/project --check --json
```

> [!TIP]
> A converged plan reports `would_change: false`. If the hash is stale, review a new preview. Preserve collisions rather than deleting existing skill content.

Deploying `implement-rfc` also requires [consumer workflow context](https://github.com/MikeMarcin/AgentSkills#configure-implement-rfc).

| Intent | Command |
|---|---|
| Add requirements without removing others | `project require ID ...` |
| Remove selected requirements | `project unrequire ID ...` |
| Replace the complete membership | `project set --skill ID --skill OTHER` |
| Explicitly empty membership | `project set --clear` |
| Choose agent targets | `project set-targets claude codex` |
| Restore default targets | `project set-targets --inherit` |
| Inspect declaration and deployment | `project show --project PATH` |
| Reconcile existing declarations | `plan --project PATH`, then guarded `apply --project PATH` |

Membership edits change the manifest. Add `--apply` to reconcile a registered project in the same operation; add `--dry-run` to preview it first. Use `--json` for structured results throughout.

## Personal declaration commands

Personal skills apply across projects. Initialize a separate selection and register
the current user's home, then preview a membership change:

```sh
mask user init --json
mask user register --dry-run --json
mask user register --expect-plan-hash RETURNED_HASH --json
mask user require manage-agent-skills --apply --dry-run --json
mask user require manage-agent-skills --apply --expect-plan-hash RETURNED_HASH --json
mask doctor --user --check --json
```

Use each preview's returned hash for its matching operation. `user require`,
`unrequire`, `set --skill ...` / `set --clear`, and `set-targets` have the same
incremental, exact-set, and target semantics as the project commands. They edit
only the declaration unless `--apply` is supplied. `user show` reports the pinned
home, declaration, ownership, and blockers. `user unregister` removes unchanged
owned links and retains the declaration; `--keep-links` abandons ownership.

Codex links live in `<user-home>/.agents/skills`; Claude links live in
`<user-home>/.claude/skills`. MASK does not install into the legacy personal
`.codex/skills` directory. An existing real directory is a collision; imports and
backups are explicit migration work, never an overwrite option.

`user register --user-home PATH` explicitly selects another existing home, useful
for fixtures. Registration pins that physical root; later `HOME` changes do not
redirect it. Unregister before changing the selected root. `--home` continues to
select MASK's state/configuration directory, independently of the deployment home.

`plan --user` and `apply --user` select personal scope. `--all` and unqualified
`doctor` include all registered project and personal consumers. Unqualified
`plan` / `apply` still select the current project. Selections are independent:
adding or removing a personal requirement never edits a project declaration.
Hosts decide how duplicate skill names are discovered; MASK does not suppress
one scope because another declares the same skill.

Existing project-only v1 state is read without conversion. The first legacy user
registration upgrades state through a recoverable v2 journal. New pinned
consumers use selection v2 and ownership state v3. Readiness, integration, and
pinned changes use typed v3 journals; v1/v2 recovery readers remain available.
Pending operations must be recovered before further mutation. The JSON result
protocol remains version 1; declarations read v1/v2 and ownership state reads v1/v2/v3.
Finish recovery with a compatible program before changing installations. The
self-updater refuses changed schema contracts; adopting these additions from an
older schema boundary requires an explicit, reviewed program-checkout update.

## What belongs where

A portable declaration contains skill IDs and optional targets:

```json
{
  "schema_version": 1,
  "skills": ["manage-agent-skills"],
  "targets": ["claude", "codex"]
}
```

| Location | Purpose |
|---|---|
| `AgentSkills/skills/<id>/` | Canonical skill payload, including `SKILL.md` |
| `<project>/.mask.json` | Versioned project requirements |
| `MASK_HOME/user.json` | Personal requirements, separate from deployment state |
| `<user-home>/.agents/skills/<id>` / `.claude/skills/<id>` | Generated personal skill links |
| `<project>/.mask/skill-config/implement-rfc/` | Versioned workflow context for that consumer |
| `<project>/.codex/agents/<name>.toml` / `.claude/agents/<name>.md` | Declared native role files: package-managed copies or repository-owned checked-in definitions |
| `<project>/.agents/skills/<id>` | Generated Codex directory symlink |
| `<project>/.claude/skills/<id>` | Generated Claude directory symlink |
| `~/.mask/` | Local machine configuration, ownership and recovery state |
| `MASK_HOME/integration.json` | Machine-local readiness approvals |
| `MASK_HOME/integrations.json` | Ownership records for installed adapters |

Commit declarations and project context. Ignore generated links and `.mask/generated/`; prefer per-entry ignore rules when unrelated real skills share the directory. `--home PATH` overrides `MASK_HOME`, which otherwise defaults to `~/.mask`. Normal operation never requires editing internal state files.
