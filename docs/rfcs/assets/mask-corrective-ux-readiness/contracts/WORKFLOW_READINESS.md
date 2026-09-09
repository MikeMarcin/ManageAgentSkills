# Declared workflow readiness and optional setup

Normative for RFC-MASK-0019. This is a small prerequisite/artifact extension of the
existing engine, not a general package lifecycle-hook or agent supervisor system.

## 1. Distinguish the facts

A source can be valid while its consumer is not configured. Skill links can be
correct while native roles are missing. Role files can match while a running host
still uses cached definitions. Report these observations separately:

| Dimension | Meaning |
|---|---|
| skill deployment | Selected skill bytes/links are present under existing rules |
| workflow prerequisites | All declared applicable context and native-role requirements match |
| setup execution | Not needed, pending consent, completed, failed, or uncertain |
| host loading | Observed in a named fresh host, unsupported, or not verified |

ensure's successful completion requires deployment and declared prerequisites,
not a proven provider model run. Host loading remains an explicit distinct field.
A known unmet prerequisite blocks launch before starting the host. A provider's
warning-only startup hook is not magically a strict gate; retain mask launch for
prelaunch enforcement and do not assert already-running hosts were reloaded.

Plain skills with no declared workflow requirements remain installable. Report
workflow=not_declared, not a claim that every imaginable dependency was checked.
For implement-rfc, its published requirement contract must explicitly require
native roles for the coordinator mode; README prose alone is not machine metadata.
If an owner-supported direct mode exists, it must be explicit and separately
labelled. Never silently reinterpret a required-role workflow as a generic-agent
fallback to make ensure green.

## 2. Minimal passive descriptor

Add optional `mask-workflow.json` beside SKILL.md, independent of the closed
mask-skill.json v1 metadata contract. Its v1 shape is in the adjacent schema.
All paths are portable package-/consumer-relative values; no executable metadata
runs while parsing, validating a package, listing, checking, or previewing.

Fields: schema_version, bounded required consumer inputs, native_roles, and
optional setup actions. Each role is keyed by selected agent plus native name and
has exactly one producer: a checked-in package asset or a declared setup action.
All listed roles are required when that agent is selected. Optional future roles
are omitted from the requirement set rather than treated as successful skips.
The built-in adapter registry maps agent/name to allowed host destinations;
packages cannot supply arbitrary output destinations, host config paths, MCP
servers, hooks, environment commands, or registry writes.

A static role asset lives under a neutral directory such as
`runtime/roles/codex/rfc-integrator.toml`, not a nested .codex/.claude tree that
bypasses existing activation guards. It is an ordinary regular file, fingerprinted
with the selected package and explicit asset hash. Parse supported native fields
passively via a built-in adapter; reject unrecognized executable/hook/config
extensions. This narrowly declared artifact kind is not permission to weaken
plain-skill frontmatter, plugin, nested activation, traversal, or symlink guards.

Inputs identify only relevant bounded consumer context/routing files and their
expected kind (regular text or JSON). Built-in checks can validate existence,
UTF-8/JSON structure, safe paths and declared fingerprints. Semantic project-schema
validation not supported by a built-in reader is a declared setup/check action,
not an automatically executed package validator. Missing irreducible consumer
facts yield one actionable configuration requirement, not invented project data.

Descriptor constraints initially reuse the 1 MiB metadata bound, with at most
64 roles, 32 consumer inputs, and 8 setup actions per package. Each optional setup
has a Python entrypoint, declared input list/parameters, timeout up to 120 seconds,
and a fixed output set derived from the roles referencing it. Limits are proposed
implementation bounds, not performance evidence. Complex build/install dependency
languages and arbitrary shell commands are out of scope.

## 3. Generation belongs to authoring; installation prefers existing bytes

Support two ordinary script-free paths:

**Shipped definitions.** AgentSkills can author/render generic native definitions
once and check them into its repository. MASK verifies and materializes those
exact files through its typed file-ownership engine. It does not run a generator
on every consumer. Skill-directory deployment remains symlink-only; copying a
small declared native-role file is an explicit new artifact operation, not a
fallback that replaces skills with unmanaged copies.

**Consumer-checked-in definitions.** A project can commit its native role files
and a portable role-input/output lock under
`.mask/skill-config/implement-rfc/native-roles.lock.json`. A fresh clone with valid
matching files is immediately acceptable without a prior machine-local renderer
manifest or a script run. These files are repository-owned, not automatically
MASK-owned. MASK does not delete them when the skill is removed and never needs
to commit, edit the Git index, or change ignore rules just to accept them.

For static assets, exact selected asset bytes establish the expected role.
For context-specific generated files, the checked-in lock records the workflow
contract/role-input digest, applicable role set, current consumer-input and
explicit routing/profile digests, and exact output hashes. MASK recomputes those
inputs and output hashes passively. A matching source-relevant stamp is a
configuration assertion, not signature-based trust or proof of host loading.
Existence or a 'Generated by' marker alone is insufficient. A stale stamp, missing
required role, unknown configuration dependency, malformed output or edited role
is incomplete; do not accept it because another package/source's stamp matches.

Hash only defined role-relevant inputs for role staleness. Unrelated README/board
changes must not require regenerating roles. Full selected package identity is
still used for code-execution consent and artifact/source integrity. Avoid a
self-referential digest: the consumer lock is outside the package, and an input
set never contains its own output stamp. Relevant input changes invalidate the
stamp regardless of whether HEAD itself changed.

Generic static roles must retain consumer ownership/addenda and explicit routing
semantics, not flatten everyone to shared defaults. AgentSkills owns that authoring
refactor and its equivalence tests. Context-specific installations may continue
to use pre-generated consumer files or the exceptional setup path. The supplied
renderer interpolates project addenda and reads profile/override inputs, so its
current outputs cannot simply be labelled universally interchangeable.

## 4. Safe ownership, targeting, and updates

Add native_role as a typed engine output, with destination derived by built-in
adapter plus role name and physical consumer scope. Expected maps include exact
selected producer identity and content hashes. Use the existing planned intents,
preflight, writer lock, journal, and recovery; do not create an independent
installer with its own ownership database.

Absent destinations can be created. Unchanged MASK-owned outputs can be updated
or retired when no selected contributor requires them. Exact existing
repository-owned outputs can satisfy requirements without being adopted. Unknown
or modified files are preserved. A tracked role edit requires an explicit manual
proposal and approval; hooks and unattended ensure refuse it. Approval to run a
script is not approval to overwrite a tracked or modified destination.

Existing implement-rfc renderer ownership is a distinct owner. A one-time,
explicit handoff can transfer only exact previously recorded output hashes after
checking the old manifest and inputs; a marker is not sufficient. Preserve old
publication journals and active assignment/report records. No deletion of all
rfc-* files and no implicit adoption from another MASK_HOME or source.

Per-agent requirements follow each binding's effective target selection. Codex-only
selection must not write Claude files; a deliberately excluded platform remains
not_applicable rather than missing. Equal role name/agent/scope outputs from
multiple skills may share only when their exact content/authority is compatible;
otherwise report both producers and the collision. Project/user shadowing stays
visible; never guess host precedence. Worktrees use independent physical roots.

On update, compute required roles from the selected candidate, not the previously
installed skill or globally newest source. Detect additions, removals, route and
permission changes before declaring readiness. Preserve explicit consumer choices;
unsupported choices block instead of silently returning to package defaults.
Known active assignments prevent conflicting role replacement. Existing checks
are not a complete inventory of every native session; disclose that limitation
and never claim a safe hot reload. Automated branch events do not overwrite
tracked roles or authorize new script revisions.

## 5. Approved setup is exceptional and complete

A setup action is package Python code, including its 'check' operation. An
interactive manual ensure can ask one question that covers the shown bounded
check/setup/recheck sequence. Display the skill/source, selected content revision
or live fingerprint, exact script and interpreter, physical consumer, purpose,
role outputs, routing/permission changes, and the fact that execution is not
sandboxed. Keep the question short; verbose details remain available.

```text
implement-rfc needs consumer-specific native role setup.
Source: legacy/implement-rfc (selected content fingerprint shown)
Run: Python <installed-skill>/scripts/prepare_mask_roles.py
Target: this project's Codex and Claude role files
This runs package code with your user permissions; it is not sandboxed.
Run this setup? [y/N]
```

A yes must run and verify the approved work, not print a copy/paste command. A no
leaves setup incomplete, exit 4, no execution. A later run may ask again; no
unrequested persistent trust policy is created. No-op static or valid checked-in
roles run no scripts and ask no question.

--json, --check, --dry-run, Git/startup events, redirected streams and other
noninteractive calls never prompt. Check/dry-run never execute package code even
when --allow-setup is present. For unattended mutation, use exact
--expect-plan-hash plus named --allow-setup SOURCE/ID:ACTION entries; alternatively
an existing explicit machine policy can authorize that same exact content/action
if it supports such grants. This RFC does not require inventing a broad persistent
trust manager. --yes, source approval, skill selection, an old source qualification,
or auto-readiness approval do not constitute script approval.

The action interface is fixed: the selected MASK Python interpreter invokes the
frozen package entrypoint with --repo-root, --output-root, and --request-file.
There is no shell=True, eval, inline code flag, or package-chosen executable.
The JSON request is inert validated input containing the action ID, selected
agent/output set, exact context inputs and declared parameters; it cannot grant
additional authority. Resolve relative imports against a frozen package snapshot.
Pinned artifacts already supply stable bytes; legacy/dev-link code needs a
verified task-private execution snapshot or refusal on changed bytes. Hashing
only the entrypoint while imports keep changing is not sufficient.

Prepare outputs in a task-owned staging directory outside all host discovery
roots. The action never owns final deployment or MASK state. MASK validates the
complete returned output set and supported native fields, computes the resulting
stamp, and publishes through the same typed engine. In the supplied source the
renderer writes consumer destinations directly; it needs an upstream staging
entrypoint before being used this way. Do not quietly execute the unchanged
renderer as an independent installer.

Bound wall time and stdout/stderr, clean up the owned process tree on timeout or
cancellation using the existing process facilities, and suppress Python bytecode
writes into the package. Proposed default wall limit is 30 seconds, metadata can
request up to the 120-second program limit, output excerpts are at most 64 KiB per
stream. No unbounded prompt retry or status-polling/model loop. Package scripts
must declare no network/external mutations in this v1 contract, but ordinary user
process execution is not a security sandbox: MASK cannot prove or enforce that
promise against malicious same-user code. State that limitation rather than
advertising sandboxed installation.

## 6. Coherent phases, interruption, and recovery

Compute the complete proposal and consent before writes where possible. Do not
hold the writer lock while prompting. Record validated setup intent under the
existing operation mechanism before launching code, then stage outside the lock
while conflicting mutators observe the pending operation. Reacquire/recheck exact
root, branch/control inputs, selected package, script/interpreter, approvals,
expected destinations, and state generation before publishing.

The typed journal contains validated package/action identities and phase facts,
not arbitrary replayable commands from a serialized file. Recovery re-derives
executable/output locations from trusted adapters and the frozen selection. Evolve
the current journal schema explicitly; never reinterpret an old version's bytes.
Preserve v1/v2/v3 readers and the self-update schema compatibility guard.

If script execution was interrupted or completion is unknown, recovery must not
rerun it automatically. Inspect retained stage/output state, verify known
completed work, or request fresh explicit execution consent. Restore/remove only
unchanged owned effects. Stage cleanup is task-private; never recursively delete
consumer directories. Unexplained output or final-path changes produce an honest
partial/recovery state. Do not claim rollback undid arbitrary script side effects.

A link transaction can be committed while subsequent prerequisite execution was
declined or failed. Report link completion and workflow incompleteness separately,
with ok=false for the overall task. A fully known failure with no indeterminate
managed effects uses 4/5 as appropriate, not a fabricated recovery requirement.
Unknown/partial persistent effects use 8; Ctrl-C uses 130 with accurate recovery
data. Only return ready after final selected-role/context recheck succeeds.

## 7. Small public integration surface

ensure is the authoritative complete check/reconcile entrypoint. install/update
call the same service before their final success; launch calls it before host
startup. doctor --check shares its observational prerequisite checks. Cheap
inventory remains observational and must label unexamined workflow state unknown;
rendering a table must not run full payload scans or setup scripts.

Expose additive workflow_readiness detail: contract identity, applicable required
roles, per-role state and configured route, ownership (package-managed or
repository-owned), setup action state, blockers, and host_load. Keep requested/
configured model and effort distinct from observed execution. The new role files
must never make an already-running `default` child appear to have been launched
under rfc-integrator retroactively.

No broad periodic requalification. Warm checks hash the small relevant inputs and
role files with per-invocation deduplication; they do not scan the board, read usage
history, call a model, or rerun source test suites. Cached proof of a prior setup
is valid only while its exact declared inputs/outputs still match.

## 8. Version skew must not recreate false readiness

Advertise `workflow_readiness_v1`, typed native-role deployment, and approved
staged-setup support in capabilities when actually implemented. A new sidecar
alone is not a backwards-compatibility guard: older MASK versions can treat it as
an ordinary payload file and still report link-only readiness, as the retained
baseline reproduction shows. The AgentSkills startup preflight must require the
new capability/result contract before accepting MASK's workflow-ready result;
otherwise it reports unsupported readiness or uses an explicitly authorized
standalone check, never silently accepts the old success. Publish the compatible
MASK/AgentSkills handoff together and test the skew case. Do not claim that adding
an ignored JSON file upgrades old clients or that a newer source forces a running
host to reload.
