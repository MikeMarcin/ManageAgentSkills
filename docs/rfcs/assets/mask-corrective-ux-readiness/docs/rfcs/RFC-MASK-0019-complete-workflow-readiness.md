---
id: "RFC-MASK-0019"
title: "Complete workflow readiness and checked-in native roles"
status: "Proposed"
owner: "MikeMarcin"
created: "2026-09-08"
---

# RFC-MASK-0019: Complete workflow readiness and checked-in native roles

**Corrective proposal; not implemented or qualified by this pack.**

Amends applicable current behavior from RFC-MASK-0002, 0006, 0007 and applicable 0008/0009 artifact boundaries; explicit AgentSkills handoff. Historical RFCs and evidence
remain unchanged; update current contracts when this implementation lands.

## Decision

A declared workflow is not ready when only its skill directory is linked.
Require applicable context and native roles, prefer existing checked-in definitions,
and permit genuinely required setup only after explicit consent. Ensure must
complete and verify approved work or clearly report incomplete readiness.

## Evidence and failure mechanism

The supplied MASK ensure plans declared skill links and does not consume native
RFC-role requirements. The shared renderer detects missing/stale roles, but MASK
installation never invokes it. The qualifier rendered consumer fixtures separately;
new shared skill text and old consumer definitions could therefore coexist.
Checking source files or helper behavior does not close that deployment boundary.

The supplied renderer interpolates consumer addenda and selected routes. It also
owns its own destination manifest and writes directly into consumer native-agent
directories. These facts matter: MASK must not blindly copy one consumer's outputs
as universal defaults, and must not run that unchanged renderer as a competing
installer. See SOURCE_BASIS.md and integration/AGENTSKILLS_HANDOFF.md.

## Contract

The normative contract is
`assets/mask-corrective-ux-readiness/contracts/WORKFLOW_READINESS.md`, with a closed
passive descriptor schema and synthetic static/generated examples in the pack.
The descriptor identifies requirements; it grants no execution authority.

Add only typed native-role artifacts and narrowly declared staged setup to the
existing engine. Preserve passive package inspection, strict activation-hazard
rules, current scope targeting, root ownership and recovery. Separate repository-
owned checked-in files from machine-managed outputs. An existing valid checked-in
file must not need a prior local generated-file manifest to count as present.

Already correct outputs are checked without generation. Interactive missing setup
asks a readable default-no question; consent covers the disclosed bounded action
and recheck. Noninteractive setup uses an exact reviewed plan and named action
authority. A no, failure or uncertain execution cannot become complete readiness.

## Integration boundary

MASK owns prerequisite observation, plan/consent, typed deployment, final state
and host prelaunch. AgentSkills owns role bytes, consumer-context/routing semantics,
any staging generator, and consistent native role/dispatch reporting. Record the
actual upstream handoff rather than embedding a special implement-rfc renderer
or repository-name exception in MASK.

This RFC requires real package integration before terminal closeout. A missing
upstream dependency remains a local explicit blocked/open card; it does not
prevent the separate CLI/human-output correction from shipping.

Filesystem/configuration readiness is not provider execution. Native host loading
remains separately observed, not inferred from matching TOML/Markdown or a startup
banner. No silent fallback to default is part of this contract.

## Out of scope

No arbitrary install hooks, shell/eval commands, package-selected interpreters,
credentials/network remediation, hidden hot reload, generic job runner, new model
routes, task supervisor, or bulk deployment to the user's real consumers. Existing
skill payloads remain symlink-deployed. Static role-file materialization is a
specific typed artifact extension, not a skill-copy fallback.


## Acceptance criteria

**RFC-MASK-0019-AC01** — **Declared prerequisites are checked.** The selected workflow contract and applicable context/native roles participate in ensure, install/update final status, doctor --check and prelaunch. New skill plus missing/stale roles cannot produce complete readiness; plain skills are not mislabelled as comprehensively qualified.

**RFC-MASK-0019-AC02** — **No compulsory installation rendering.** Checked-in package definitions deploy without running a generator. Exact consumer-checked-in definitions and their coherent portable input/output lock pass on a fresh clone with no local renderer manifest and no package script execution.

**RFC-MASK-0019-AC03** — **Owned typed role artifacts.** Per-agent/scope native outputs use the existing engine and typed destination mapping. Modified/unknown/tracked content, linked parents, another producer and another owner are preserved; valid checked-in files are not automatically adopted or deleted.

**RFC-MASK-0019-AC04** — **Explicit executable setup.** Only genuinely necessary declared Python setup is offered with readable exact consent. Yes executes and verifies in the same command; no/EOF does not execute and returns incomplete. JSON/events/check/dry-run never prompt or run unauthorized code; package check functions are not exempt.

**RFC-MASK-0019-AC05** — **Staging, freezing and recovery.** Approved setup uses frozen code/inputs, bounded process-tree execution and staged outputs, then revalidation and journaled activation. Failed/uncertain/crashed actions never silently rerun, overwrite changes, or claim arbitrary external effects were rolled back.

**RFC-MASK-0019-AC06** — **Current target and route fidelity.** Role requirements follow the selected candidate, consumer profile/override, effective agent set and physical scope. Missing rfc-integrator and legacy-name drift are explicit. Configured/requested route is separate from host-observed execution; no silent default fallback or model-policy change.

**RFC-MASK-0019-AC07** — **Real consumer-path qualification.** The integrated current AgentSkills package is checked through MASK in two disposable consumer contexts, starting with missing/stale roles and no preparation shortcut. Native macOS/Windows output deployment is verified, and fresh host discovery/loading claims have actual named-host evidence or remain explicitly unverified.

**RFC-MASK-0019-AC08** — **Truthful adoption and documentation.** The upstream AgentSkills handoff is recorded, current docs describe static/checked-in and approved-setup paths, unchanged reruns are script-free/no-op, and closeout does not substitute pack/source/helper qualification for complete consumer readiness.

## Rollout and rollback

Import against live IDs, record the actual pre-implementation baseline, and
implement through the linked cards. Preserve existing interfaces where their
semantics remain supported; publish deliberate stricter readiness/consent changes
in capabilities and release notes. A compatible prior program is not automatically
safe after a new typed journal/schema has been written: finish pending recovery
before switching executables and retain the explicit updater compatibility guard.
Never delete user files or relax safety checks to make rollback look successful.

## Closeout

Exactly one linked closeout card records every criterion, actual command or
observation, outcome and implementation revision. A missing required native lane,
upstream handoff, or public journey remains open. Packet validation and synthetic
fixtures cannot supply those results. Reuse unchanged focused evidence; do not
create an exhaustive proof archive or repeated model-review loop.
