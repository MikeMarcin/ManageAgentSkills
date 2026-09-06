---
id: "RFC-MASK-0007"
title: "Multiple sources, taps, curated imports and upstream provenance"
status: "Accepted"
owner: "MikeMarcin"
created: "2026-09-05"
---

# RFC-MASK-0007: Multiple sources, taps, curated imports and upstream provenance

**Delivery stage:** B — source foundation. **Packet status:** proposed implementation contract; no implementation or acceptance is claimed.

**Predecessors:** RFC-MASK-0006.

The new behavior below explicitly extends the historical v1 scope. Preserve settled RFCs 0001–0005; update current architecture/user documentation only when the relevant implementation ships. See [source reconciliation](../design/SOURCE-RECONCILIATION.md), [shared contracts](../design/CONTRACTS.md), and [references](../design/REFERENCES.md).

## Decision

Support several approved Git repositories as independent sources. A **tap** retains the upstream source identity and resolves selected skill packages from it. A **copy import** vendors an exact selected package into a user-owned curated source, retaining upstream attribution and adaptation provenance. Neither term changes deployment: consumers still receive MASK-owned per-skill links, not copied destination trees.

Keep the Python standard-library core plus installed Git. No registry service, downloaded installer, dependency hooks, script evaluation, browser authentication, automatic repository publication, or runtime plugin execution is required.

## Source and package identities

A source alias is a portable human name, not the trust boundary. Its identity is a canonical credential-free repository URI plus declared package layout/index. A package coordinate is `(repository identity, package path, package id)`; a resolved package adds full commit/object identity and payload digest. Two aliases for different repositories are never silently equivalent; the same repository advertised through HTTPS and SSH is equivalent only under a documented normalization or explicit approved transport-alias mapping.

Normalize host/scheme/default port where appropriate; preserve repository-path case when the host's rules are unknown. Reject embedded passwords/tokens, NUL/newline, option-leading arguments, ambiguous scp syntax, unsupported protocols and arbitrary remote-helper syntax. Explicit `file`/local sources are machine-local fixture/authoring sources and cannot masquerade as portable URLs. Revalidate the final endpoint after a redirect; do not inherit approval across a moved repository just because its basename is unchanged. The baseline basename-only source identity check must be replaced. [M1: mask_git.py:checkout_preconditions]

Machine schema v2 separates approved source identity, local transport/auth binding, bare cache and optional authoring checkout. Portable declarations contain repository identity and layout but no local paths or credentials. Conflicting source identities under a local alias are typed errors, not search precedence.

## Layout and discovery

Support the existing `skills/<id>/SKILL.md`, a root-level single skill, and a bounded selected subdirectory. An optional `mask-source.json` index declares exact package paths and bundle definitions. A tap with no index may use bounded regular-tree discovery and return candidate coordinates. Nested skills are individually addressable; overlapping package roots are ambiguous unless the index selects exactly one interpretation. Never install every discovered skill by default.

A pasted GitHub repository/tree/blob URL is parsed into repository, ref and path. Resolve branch names containing slashes against known refs before selecting a subdirectory; ambiguous inputs return choices. Do not fetch a rendered HTML page as skill contents. A bare name resolves only against configured sources; duplicate matches require a qualified coordinate. No silent public search, fuzzy match or typo correction grants installation authority.

## Public operations

```text
mask source list
mask source show SOURCE
mask source inspect URL [--ref REF] [--path SUBDIR]
mask tap add SOURCE URL [--ref REF] [--packages PATH]
mask tap remove SOURCE
mask source fetch [SOURCE]
mask skill import URL --mode copy --into SOURCE [--ref REF] [--path SUBDIR]
mask skill provenance SOURCE/ID
```

All provide JSON and precise effects. Remote inspect/fetch are explicitly network-capable; dry-run never fetches and reports `resolution_required` when a cached proposal cannot be computed. `tap add` establishes a catalog source, not a deployment request. `tap remove` refuses live selection/lock/profile references unless a separate explicit migration/removal plan covers them; it never recursively deletes caches or upstream checkouts. The later fleet high-level install request composes these operations without a second resolver.

## Copy import contract

Prepare a package from frozen Git objects in a MASK-owned staging directory outside host discovery. Preserve exact upstream payload bytes and required adjacent notices. A copy operation writes only the chosen new curated-package path and provenance file after destination/precondition validation. It refuses overwrites of tracked or untracked existing material; replacing an earlier import is an explicit update with base digest and diff. Any sibling LICENSE/NOTICE incorporation is documented in the import manifest, not silently added to the payload hash.

The default operation does not commit or push the authoring checkout. Return exact changed paths. An optional later fleet `publish` authority may commit and push only the selected package/provenance changes in an isolated MASK-owned worktree after explicit scope approval. Do not sweep unrelated staged changes or ask the user to manually push after every already authorized fleet install.

Store upstream repository, upstream subpath, full imported commit, upstream payload digest, retrieval timestamp if useful, local curated coordinate/revision, and adaptation history. Unknown fields of historical provenance stay explicitly unknown; do not synthesize a trustworthy-looking origin from a package name. Distinguish publisher assertions from facts MASK verified by reading repository objects. A signature authenticates a signer, not the safety of a package.

## Baseline package safety, not a deferred scanner

Reuse and generalize structural validation: regular files/directories only; bounded sizes/count/depth; no path traversal, case/Unicode-normalization collisions, Windows-reserved components, links, reparse points, Git submodules, archive devices, external archive links or destination escapes. Source acquisition never runs the package or its install hooks. Read selected Git objects without checkout filters/smudge and without using hardlinks to the mutable authoring checkout. Unsupported Git LFS pointers are a typed blocked prerequisite, not the final asset contents.

Keep the documented MASK frontmatter parsing boundary explicit. Do not silently rewrite arbitrary YAML or claim complete Agent Skills conformance. An unsupported package returns a precise import limitation; expanding supported syntax can be a contained follow-up if actual desired packages need it. The machine-readable compatibility sidecar in RFC-MASK-0009 does not pretend to replace the broader Agent Skills specification. [E6]

Plain-skill imports reject known host autoactivation metadata, including `.claude-plugin/plugin.json`, and do not install hook/MCP/plugin configuration as incidental skill data. Claude explicitly documents in-place plugins in skill directories. Detection belongs to the adapter's package-kind guard, not to an optional heuristic audit. Unknown machine-active syntax cannot be labelled inert; preserve it in staging and report unsupported/explicit separate authority. This is not a general malware detector. [E7]

Machine-configured Git credential helpers remain trusted external programs. Managed bare caches do not ingest repository-local command configuration from downloaded contents. Apply network/file size/time limits, noninteractive authentication, hook suppression including named hooks, process-tree timeout cleanup, and output redaction. Installing public skills does not change a private curated repository's visibility.

## Integration and migration

`init --source PATH` continues to bind the legacy local source. An explicit configuration migration gives it a source alias, discovers its full identity for approval, and preserves existing roots/ownership. Do not claim old v1 declarations are portable multi-source declarations; the v2 resolver follows in RFC-MASK-0008. Source inspection/provenance can ship before consumers migrate.

Own new `mask_sources.py`, source schema/capabilities and import fixtures, plus the narrow Git identity/extraction changes. AgentSkills owns actual payload imports, notices and source-index content: record a handoff rather than editing its mutable board from MASK. The full AgentSkills implementation was not supplied. [M1]

## Acceptance criteria

- **RFC-MASK-0007-AC01** — Two private/public-style local bare remotes expose independent taps and nested/root packages; name ambiguity, path/ref ambiguity and conflicting aliases are actionable rather than silently selected.
- **RFC-MASK-0007-AC02** — Source identity checks bind the approved repository and transport policy, not just the basename; credential-bearing/unsupported URLs and unapproved redirects refuse without leaking secrets.
- **RFC-MASK-0007-AC03** — Copy import preserves byte provenance and notices, refuses existing unrelated destinations, records local adaptations, and performs no commit/push unless separately authorized.
- **RFC-MASK-0007-AC04** — Adversarial package fixtures cannot traverse paths, introduce special entries, run hooks/filters/package scripts, silently activate a plugin, or bypass bounded resource limits.
- **RFC-MASK-0007-AC05** — Source lifecycle and legacy-config migration preserve current ownership and old declarations; removing a referenced source refuses and reads/dry-runs remain observational.
- **RFC-MASK-0007-AC06** — Public CLI/capabilities describe resolution, catalog-only addition, mutation/network boundaries and provenance verification levels with deterministic errors.

## Live authorization

Accepted for implementation by the owner’s 2026-09-05 import-and-implement request. Follow the live card dependencies; native and external acceptance remain open until directly exercised.
