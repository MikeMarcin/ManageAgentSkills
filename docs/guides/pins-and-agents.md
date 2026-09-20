# Pins, development links and per-skill agents

Updating one pinned skill, authoring through a development link, per-skill agent selection, local compatibility policy and adapter facts.

## Pinned updates and development links

`mask upgrade --project PATH --skill SOURCE/ID` fetches that binding's tap and updates only that pin through one recoverable lock/link operation. Preview it with `--dry-run`, which uses cached objects and never fetches. Exact commit requirements stay fixed.

For scoped authoring, `mask source dev-link SOURCE/ID --project PATH
--authoring-root PATH --json` makes an explicit dirty/unpinned exception from the
tap's approved authoring checkout. Return
with `--to-pinned` in place of `--authoring-root`. Use `ensure --check` to inspect
readiness without changing a development scope; complete checks report
`ready_dev_link`, not pinned readiness. Ordinary apply and mutating ensure
refuse live overrides, and update skips or refuses them. `mask source publish SOURCE --paths PACKAGE_PATH --json`
previews exact package publication. Add `--commit` and separately `--push` only
when those effects are intended. Publication preserves the authoring HEAD/index
and reports its separate commit/ref. See the
[CLI contract](../architecture/cli-contract.md#selected-updates-and-authoring-exceptions)
for recovery, authority and platform limits.


## Per-skill agents and local compatibility

Registered v2 consumers can choose agents independently:

```sh
mask project set-agents vendor/alpha codex --apply --json
mask user set-agents vendor/alpha claude --apply --json
mask project set-agents vendor/alpha --inherit --apply --json
mask project set-targets --inherit --apply --json
```

`--all` on `set-agents` selects supported, locally enabled agents. `--inherit`
removes the binding choice; `set-targets --inherit` restores the v2 `all` default.
Run `project register` or `user register` first; registration without `--apply`
is supported. Without `--apply`, setters update declaration, coherent lock and
cached desired selection while retaining current owned links. Preview with
`--dry-run` and apply its `--expect-plan-hash` to guard the exact intent.

Bindings whose `when.platforms` or `when.architectures` do not match are reported
`not_applicable`, retain their lock rows, and need no artifact preparation.
Missing compatibility metadata means unspecified. Generic and specific metadata
are publisher assertions, never evidence that a skill was tested. Explicit
incompatible requests block; implicit `all` can exclude incompatible agents.
Requirements are informational and never execute or install tools.

Local policy defaults to both Claude and Codex without detecting executables:

```sh
mask selection-policy set --agent codex --dry-run --json
mask selection-policy clear --json
mask compatibility override vendor/alpha --project /path/to/project \
  --agent claude --reason "Reviewed for this project" --dry-run --json
mask compatibility clear vendor/alpha --project /path/to/project --json
```

Global enabled-agent changes reconcile every registered consumer; explicit
requests for disabled agents block the change.
Overrides affect one physical project or registered `--user` scope and one
coordinate. `--platform` and `--architecture` name the current device dimension.
Every override needs a reason and produces a warning; it cannot enable an
unsupported/disabled adapter or grant source trust. Local policy is bounded to
1 MiB and is never imported from a package. Policy, declaration and lock effects
use the existing recoverable journal. Dev-link evaluation reads validated live
metadata and remains unpinned. Identical coordinate/content contributions merge positive agent edges with all
origins retained. Different artifact authority under one coordinate refuses;
different coordinates conflict only when they share an agent invocation path.
Disjoint agents/scopes are allowed. Public profile storage remains separate work.


## Adapter facts and conflicting names

`mask capabilities --json` exposes the built-in Claude/Codex adapter contract:
project/personal discovery paths, startup configuration paths, reserved names,
package hazards and recorded readiness evidence. macOS/Windows readiness evidence
is distinct from first-prompt host loading, which remains unverified. Linux
behavior remains best-effort; no executable detection changes the agent set. The
`workflow` entry (`readiness: workflow_readiness_v1`, `native_roles`,
`staged_setup`, the entrypoints that share the verdict) is what an upstream
startup preflight must require before accepting a workflow-ready result.

A plan rejects different source coordinates named `alpha` when both require, for
example, the same project's Codex `alpha` path. It reports both coordinates,
origins and exact artifact claims. Assigning those coordinates to disjoint agents
is allowed. MASK never renames a package or chooses a last contribution. Equal
coordinate, repository identity and payload/metadata/provenance digests merge
positive agent selections, retaining all exact commits/selectors and origins.
Inapplicable contributions retain their lock attribution without participating
in conflicts or requiring their content. Public profile storage is still RFC10.

`plan`, `apply`, and project/user `show` expose `shadowing` and
`target.scope_shadowing` warnings for user/project discovery names. Observed owned
links and prospective overlaps are distinguished, and an overlap whose scopes
resolve to one directory is reported as `same_target` without a warning. Both
scopes remain independent; MASK does not assert which one the host loads. Full pinned where-used inventory
remains a separate reporting slice.
