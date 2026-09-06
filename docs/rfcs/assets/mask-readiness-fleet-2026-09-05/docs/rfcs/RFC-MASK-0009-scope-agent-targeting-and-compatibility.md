---
id: "RFC-MASK-0009"
title: "Per-skill scope-specific agent targeting and advertised compatibility"
status: "Proposed"
owner: "MikeMarcin"
created: "2026-09-05"
---

# RFC-MASK-0009: Per-skill scope-specific agent targeting and advertised compatibility

**Delivery stage:** B — selection semantics. **Packet status:** proposed implementation contract; no implementation or acceptance is claimed.

**Predecessors:** RFC-MASK-0008.

The new behavior below explicitly extends the historical v1 scope. Preserve settled RFCs 0001–0005; update current architecture/user documentation only when the relevant implementation ships. See [source reconciliation](../design/SOURCE-RECONCILIATION.md), [shared contracts](../design/CONTRACTS.md), and [references](../design/REFERENCES.md).

## Decision

A skill's deployment is selected independently for each **consumer scope** and each **agent**. `user` and a particular `project` are scopes; Claude and Codex are agents; Windows/macOS/Linux are platforms. Stop overloading the word “target” to mean all three.

The default is **every currently supported and enabled agent adapter**, not “whichever agent happened to be detected” and not a mandatory explicit list. The same generic skill can target only Claude in personal scope and both Claude/Codex in one project without either declaration editing the other.

## Selection semantics

Selection v2 uses source-qualified bindings. A binding can specify `agents: "all"` or a nonempty explicit subset, and an optional `when` platform/architecture filter. Omitted `agents` inherits the declaration's `default_agents`, whose v2 default is `"all"`. All means the supported adapter set exposed by this installed MASK version and local enabled-adapter policy. Initially that set is Claude and Codex.

Do not require the corresponding host executable to exist before writing its declared discovery links. Detection is diagnostic, not a silent selector. Never add a new untested adapter to the supported set merely because a path is known.

Existing v1 explicit target lists remain exact. Migration of a v1 inherited target policy must preserve its resolved behavior unless the user deliberately selects `all`; changing a schema is not permission to broaden deployment. New v2 declarations default to all. Future adapters enter all only after native support is enabled and its impact is shown; disabled/unsupported adapters remain reported rather than ignored.

`project set-targets` and `user set-targets` remain whole-declaration compatibility commands. Add narrow `project set-agents SOURCE/ID --all|AGENT...` and matching user operations. Selection mutation with `--apply` uses one prospective declaration/lock/reconciliation plan; collisions leave both declaration and lock untouched. An empty explicit list is not deletion; use unrequire.

## Compatibility metadata

Use optional `mask-skill.json` alongside SKILL.md for deterministic machine-readable metadata:

```json
{
  "schema_version": 1,
  "agents": "generic",
  "platforms": "generic",
  "architectures": "generic",
  "requirements": []
}
```

Lists may replace `generic`, for example `agents: ["claude"]`, `platforms: ["macos"]`. Generic is a publisher assertion of no known restriction. Absent metadata is `unspecified`, treated permissively for backward compatibility but never labelled tested. Preserve the ordinary Agent Skills free-text compatibility field for humans; do not infer an OS support matrix by having an LLM interpret it. [E6]

Metadata is content-addressed with the package. Upstream authors can advertise restrictions; a curated copy can record reviewed corrections with provenance. A local owner may explicitly override a restriction using a separately recorded scope policy and warning; the package itself cannot grant such authority. Required tool descriptions are information, not executable probes, package installation commands, or permission grants.

## Effective deployment algorithm

1. Select the binding from one consumer's local declaration and approved profile contributions.
2. Evaluate an explicit `when` clause. False means intentionally not applicable, with a recorded reason.
3. Resolve the requested agent set from binding/default/all.
4. Compare package metadata. For implicit/all agents, exclude explicitly unsupported agents and report them. For an explicitly named unsupported agent, block with `compatibility.unsupported`; never silently rewrite the request.
5. A platform/architecture mismatch in an otherwise applicable binding blocks by default. Users/profile authors can make cross-platform intent conditional through `when`, or a fleet request may explicitly permit compatibility skips and record them in its frozen plan. An unsupported device is not “installed.”
6. Reject collisions between different coordinates sharing a host invocation name in the same `(consumer, agent)` destination. Identical names at disjoint agents/scopes are permissible. Do not rename SKILL.md, rewrite payload instructions, or pick the first source silently.

No host precedence assumptions suppress duplicates between user and project scopes. Warn about same-name shadowing and expose it in where-used; the host decides which instructions it loads. `where-used` reports actual scope/agent/coordinate/digest rather than conflating all names.

## Local and fleet contribution conflicts

Portable profiles can contribute bindings without owning an entire user declaration. Merge identical coordinate+artifact positive target contributions by union, keeping origin attribution; absence from one contribution is not an explicit deny. A local per-binding manual setting is preserved when expanding a bundle into that same local contribution. Different versions or conflicting explicit targeting for the same deployment require an explicit override record; there is no implicit “last profile wins.” Removing a fleet contribution does not remove a local requirement. An explicit local override is visible as a deviation from fleet policy; it cannot generate a false successful exact-intent receipt.

## Adapter contract and scope

Consolidate the duplicated `ADAPTERS` definitions in mask.py/mask_core.py into one audited data model: agent ID, relative paths per scope, supported platform boundary, discovery/reload/gate capability, reserved names and package-kind hazards. Render schema enums/capabilities from that source or test them against it. Do not introduce arbitrary executable third-party adapter plugins.

Additional agents are **tracked but deferred**. An adapter contribution needs discovery-path evidence, native ownership/readiness checks, and at least one real supported-host load scenario before being advertised. Merely passing a filesystem path test cannot prove host support. Existing Claude/Codex coverage should not wait for an agent the owner does not use.

## Reporting

Each candidate deployment gets a stable outcome: selected, deployed, not_applicable, excluded_by_metadata, blocked, or overridden. Include the deciding scope, declaration/profile origin and compatibility assertion level (`generic_asserted`, `specific_asserted`, `unspecified`, separately tested). Inspection does not run platform-specific setup. Passive heuristic audit remains deferred; this RFC covers declared applicability and deterministic selection only.

## Acceptance criteria

- **RFC-MASK-0009-AC01** — The same skill has independently configurable personal and project agent sets, with new selections defaulting to all supported/enabled agents and no executable-detection side effects.
- **RFC-MASK-0009-AC02** — V1 migration preserves explicit and inherited target behavior; per-skill edits/locks/plans remain guarded and no-op stable.
- **RFC-MASK-0009-AC03** — Generic, absent and agent/platform-specific metadata produce distinct truthful reports; explicit incompatibilities block, and conditional/inapplicable bindings are not called installed.
- **RFC-MASK-0009-AC04** — Multi-source name conflicts, conflicting profiles and user/project duplicate names are explained without overwriting content, silently renaming packages or assuming host precedence.
- **RFC-MASK-0009-AC05** — A single adapter contract drives paths/capabilities/validation, and existing native Claude/Codex scope tests cover the change; additional agents stay unadvertised until independently proven.
