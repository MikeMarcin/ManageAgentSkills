---
id: "RFC-MASK-0016"
title: "Public trust evidence and staged supply-chain hardening"
status: "Proposed"
owner: "MikeMarcin"
created: "2026-09-05"
---

# RFC-MASK-0016: Public trust evidence and staged supply-chain hardening

**Delivery stage:** E — stretch public assurance. **Packet status:** proposed implementation contract; no implementation or acceptance is claimed.

**Predecessors:** RFC-MASK-0007, RFC-MASK-0008, RFC-MASK-0012, RFC-MASK-0013.

The new behavior below explicitly extends the historical v1 scope. Preserve settled RFCs 0001–0005; update current architecture/user documentation only when the relevant implementation ships. See [source reconciliation](../design/SOURCE-RECONCILIATION.md), [shared contracts](../design/CONTRACTS.md), and [references](../design/REFERENCES.md).

## Decision

Make MASK trustworthy by minimizing authority and providing inspectable evidence, not by claiming it can be proven universally safe. Prioritize the owner's working tool. Core safety requirements already belong to readiness/import/pinning/fleet RFCs and cannot be postponed here; public-distribution assurance is a separate stretch milestone.

This RFC does not require a heuristic prompt-injection scanner, model-driven safety grading, an exhaustive audit dashboard or support for agents the owner cannot test. Those remain tracked/deferred. It does require clear claims, narrow default permissions and a path to externally verifiable releases when the owner chooses publication.

## Threat model and claims

Protected against by design/tests: accidental overwrite; poisoned portable paths; swapped/ambiguous sources; unreviewed source advancement; package/install hooks; known host autoactivation packages masquerading as plain skills; credential leakage through outputs; duplicate/replayed fleet requests; unsigned/unapproved desired revisions; stale success reports.

Not solved: a compromised user's OS or same-user process; a compromised approved controller/signing key; a malicious skill's instructions executed later by a powerful agent; a malicious Git/SSH binary or approved credential helper; an authorized but mistaken operator; every future host plugin/discovery change. Package hashes and signatures establish identity/integrity, not benevolence. The skill manager is not an agent sandbox.

Publish these boundaries in SECURITY.md and permission/effect documentation. Separate verified facts, design intent and untested platforms. Maintain a vulnerability contact and private-report path when publication occurs; never publish credentials or private source history merely to appear transparent.

## Baseline evidence to assemble

Document exact local/network/configuration effects per command; disabled-by-default continuous operation; no telemetry by default; secret/source redaction; per-skill ownership; no elevation/force overwrite; upgrade and uninstall/recovery behavior. Keep a small dependency surface and make the optional fleet/MCP/vault providers visible.

Use focused adversarial tests at actual boundaries: source identity, import traversal/special entries, native Git configured-hook suppression, package-kind activation, artifact corruption, wrong-device signature, replay, stale plans and expired grants. Reuse those tests from the owning RFCs rather than manufacturing another broad proof archive. A concise risk-triggered independent review is appropriate for import, persistence or remote-authority changes; missing an optional second model does not block ordinary slices.

## Release authenticity

Before any public release, choose a source license and distribution scope explicitly. Provide source at a pinned tag/commit, reproducible build instructions where applicable, a minimal dependency manifest/SBOM, checksums, and signatures bound to the artifact and release identity. Checksum and binary from the same untrusted channel are not independent authenticity evidence. Pin third-party CI actions to immutable revisions and minimize CI token permissions when workflows are introduced. External publication requires owner authorization.

Use established signing/attestation tooling rather than homegrown update verification. Signer trust must be bootstrapped independently of the artifact being checked, and key rotation/revocation must be testable. An existing approved private Git flow can remain the owner's default distribution while public packaging is immature. Signing a dangerous artifact does not make it safe. [E8]

For an eventual unattended **program** update channel, evaluate a mature TUF implementation with trusted root distribution, version/expiry handling, rollback/freeze protection and key recovery. Do not implement a partial TUF-like protocol and label it TUF. This pack keeps program updates explicit; a documented evaluation and provider seam is sufficient until an actual automatic-program-update requirement exists. [E12]

## Verifiability and adoption

Offer an observational `mask trust show` / `mask self verify` report that states the executable/source revision, dependency/provider versions, signature checks actually performed, configured authorities, effective background behavior and unsupported verification modes. No green “safe” badge. A build from a dirty authoring checkout is labelled dirty and unverifiable against a release, not denied ordinary local development.

Document a non-destructive trial using temporary fixture roots, an uninstall that preserves unmanaged content, and how a reviewer can reproduce the relevant acceptance tests. Native Windows/macOS evidence is required only for claimed support; Linux/other hosts remain labelled accurately.

## Deferred boundaries

Additional agent adapters, passive heuristic audits and arbitrary MCP-server management are not silently included. Track them as future work with useful eligibility criteria. The optional secret vault has its own threat model and tests in RFC-MASK-0015. Public readiness may remain open while all core personal-use milestones are shipped.

## Acceptance criteria

- **RFC-MASK-0016-AC01** — Threat/effect documentation distinguishes integrity, authorization, deployment, host loading and content safety, with explicit non-goals and no universal safety claim.
- **RFC-MASK-0016-AC02** — Core boundary tests and provider/dependency inventory are reused in a compact trust report that labels dirty/unsigned/unverified conditions truthfully.
- **RFC-MASK-0016-AC03** — A proposed public release has an explicitly authorized distribution/license decision, independently bootstrapped artifact verification and reproducible verification instructions; no publication is assumed.
- **RFC-MASK-0016-AC04** — Key rotation/revocation and update-channel rollback/freeze considerations are documented/tested at the selected provider boundary, without adding an unrequested automatic program updater.
