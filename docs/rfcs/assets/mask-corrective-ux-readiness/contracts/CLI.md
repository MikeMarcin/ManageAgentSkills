# Task CLI and human presentation contract

Normative for RFC-MASK-0018. These are proposed behavior changes; existing source
locations and distinctions are catalogued in SOURCE_BASIS.md.

## 1. A small ordinary command set

| Command | Complete intent |
|---|---|
| `mask install ID ...` | Add selected skills, prepare selected content, declare/register as needed, deploy, and check the result |
| `mask remove ID ...` | Remove only those local selections and their no-longer-required unchanged owned outputs |
| `mask list` | Show selected/deployed skills and agent states for the current project |
| `mask inventory` | Retain existing detailed inventory capability, with the same readable default |
| `mask ensure` | Make the current declaration usable without changing requested versions or membership |
| `mask update` | Acquire current approved update candidates, explain actual impact, and apply a frozen selected update |
| `mask self update` | Update the program only; preserve the compatibility guard and next-invocation requirement |

Project is the default for install/remove/list/ensure, using the existing
worktree-aware project resolver. `--project PATH` and `--user` are mutually
exclusive. `--all` remains available only where a multi-consumer operation is
actually supported; install/remove must never reinterpret it as all skills.
Personal scope uses the registered physical home; it does not follow a later
HOME change. `--home` still selects MASK's machine-state location.

No operand `mask` shows compact everyday help and exits 0; it does not mutate or
dump capabilities. Top-level help introduces the ordinary commands plus existing
advanced command groups. `--version` prints a version line, not a result object.
Keep install versus self install, selected skills versus available source catalog
(`skill list`), and skill update versus program update unambiguous.

One-time launcher/source selection remains `self install --bin-dir PATH` and
`init --source PATH`, with readable results. Do not select an arbitrary repository
or change PATH/credentials. An unconfigured install explains the one missing
source choice in the same interaction where practical; it does not expose six
unrelated state-management steps. No source federation or fleet setup is required
for the user's existing local checkout.

## 2. Install/remove are real engine operations

New verbs are not shell aliases to a sequence of independently committed
commands. Build one prospective intent through shared planner/resolver services.
Initialize missing declarations and registration within that operation; retain an
existing declaration's version. Do not silently convert a legacy consumer to
pins. New consumers use the configured source mode; v2 catalog consumers get a
coherent v2 selection/lock, and legacy-only machines remain usable without a
catalog migration prerequisite.

For v1, add/remove is union/subtraction; preserve unrelated membership and target
intent. For v2, resolve new bindings and retain unrelated exact resolutions,
source declarations, origins, conditions, and overrides. The supplied legacy
project.require/unrequire functions reject v2 input, so merely invoking those
functions does not implement this contract. Use/refactor the pinned transition
seam. Never rewrite unrelated locks to current upstream while adding one skill.

A bare ID resolves only when unambiguous across relevant approved catalogs. A
collision produces source-qualified choices; no first-source-wins behavior. Live
install may acquire approved missing catalog/artifact data as part of the
explicit request; --offline and every --dry-run remain network-free and report
what is missing. New repository identities require their own explicit approval.
No automatic credentials repair or arbitrary URL execution.

Default agents are all supported, locally enabled agents subject to existing
compatibility rules, independently by scope. `--agent AGENT` (repeatable) selects
agents for the newly requested binding, not a hidden global policy. Do not change
an already selected binding's explicit targets on a no-op reinstall. Where a v1
selection cannot express a per-binding override, offer explicit migration or an
honest unsupported request; never edit all skills' targets as a shortcut.

A successful task includes the verification available for its declared workflow.
Once RFC-MASK-0019 is implemented, install/update cannot report complete success
while required setup remains pending. They may retain a coherent completed
installation with workflow setup incomplete, but must report those phases and a
nonzero completion result. Removing a skill retains consumer-authored context,
checked-in roles, reports, and manually edited files. Shared role contributions
are removed only after the last selected contributor releases an identical
managed destination. Do not uninstall the other scope's independent selection.

## 3. Confirmation is part of the operation, not the human's job

A direct, explicit task command authorizes its ordinary scoped engine effects.
Do not prompt once for registration, again for declaration, and again for links.
No-op operations require no confirmation and preserve bytes/generation.

Use one clear proposal/confirmation for genuinely significant new authority:
new source identity, broader shared-update impact, changes to tracked role files,
or package script execution. Combine already known decisions into a readable
proposal when they describe the same operation. Package code must be named,
not hidden under a generic 'continue'. Approval to manage links is not approval
to run package code or permission to overwrite modified content.

On a human manual invocation with a usable interactive terminal, display the
proposal and a default-no question. EOF means decline; Ctrl-C is interruption.
Do not hold the writer lock while awaiting a human. After consent reacquire the
lock, re-read the bound inputs, and reject a stale proposal before any effects.
A changed plan can be shown for a new approval; never silently apply it under the
old approval. Plan hashes are retained inside the program, not copied by the user.

`--yes` authorizes ordinary noninteractive task effects within the explicit
scope. It is not a force option and does not authorize new source trust, package
scripts, overwritten edits, ref rebinding, or undisclosed cross-consumer effects.
Reviewed automation can continue using `--expect-plan-hash HASH` for a frozen
proposal. Package setup additionally requires a named `--allow-setup ACTION`
(repeatable) matched to that frozen proposal; see WORKFLOW_READINESS.md. Humans
answer a question and need neither flag.

Manual ensure gains one-invocation authority; it must not silently persist
integration approval. Startup/Git events retain their existing machine-local
policy requirement. Installing hooks, granting future-clone authority, network
fetch grants, and host trust remain separate opt-ins, not installation defaults.
The lower-level integration.approve command stays available and can provide its
own in-process confirmation in human mode.

## 4. Update semantics must be explicit, including compatibility

Do not change selection or authority based on --json or isatty. Normal update is
one task, but guarded/offline modes still have precise meanings:

* An ordinary online update may fetch approved candidates, freezes them, shows
  impact, and applies only the reviewed content. Fetch/cache effects before a
  declined application are reported separately; they are not activated skills.
* --dry-run never fetches or materializes. Show cached freshness and unresolved
  acquisition rather than inventing a complete preview. --offline uses only
  existing content. --expect-plan-hash binds cached/frozen candidate state and
  must not silently fetch a different candidate before applying it.
* An exact commit pin is not advanced. Moving a tag or unproven/non-fast-forward
  ref still needs the existing explicit ref-rebind authority. Dirty/unavailable/
  diverged inputs retain their current refusals; no reset, stash, clean or push.

**Preserve existing selector behavior in this corrective release.** Unqualified
update continues to select the existing legacy shared-source operation; explicitly
selected pinned updates use --project/--user/--all. Human help and output must name
this distinction. Do not quietly change an old unqualified automation command
into a current-project update. For a pinned-only installation with no legacy
update target, an unqualified command may offer the discovered project in the
same interactive invocation; machine mode reports the exact selector needed
rather than choosing a different scope silently. This bounded compatibility rule
avoids inventing a global-selection migration merely to fix UX.

An explicitly selected legacy update cannot truly isolate a shared checkout.
Show every affected registered legacy consumer and obtain expanded-scope consent
in that invocation, or refuse with the existing migration option. Noninteractive
expanded application requires --all or a matching reviewed impact-bound hash;
--yes alone cannot widen it. Pinned updates affect only selected bindings/scopes.
No full future fleet/impact-report system is required: current affected scopes,
content revision/digest changes, role changes, blockers, and acquisition effects
are sufficient to make this proposal honest.

The existing update pipeline and typed journal remain authoritative. Refactor
only what is necessary to compose acquisition, resolution, plan, consent,
activation, and final verification. Do not force a self-update or a state-schema
migration as an incidental effect of updating skills.

## 5. Human output is a renderer, not serialization with whitespace

Without --json, render a concise result from the same structured result object.
Every registered command must have an intentional human presentation. A registry
coverage test rejects a command that falls back to dumping arbitrary dicts/JSON.
Reuse a few layouts for summaries, inventories, changes, and diagnostics; do not
build a second business-logic layer in the renderer.

Inventory groups by physical consumer, scope, full source/skill coordinate, and
content authority; use agent columns only where those identities match. Three
skills deployed to two agents are three skill rows and six links, not six skills.
Show per-agent drift, missing, collision, excluded/not-applicable, and unknown
states. Do not suppress source collisions, unavailable consumers, shadowing, or
pagination. A partial page cannot claim a complete count or a missing agent for
rows not observed. Preserve total_rows/next_offset in JSON and show continuation
in human form. Implement minimal pinned list/inventory views from the existing
selection/outcome/ownership seams; do not wait for full RFC-MASK-0011 reporting.

Ordinary output gives the scope, actual result, material warnings, and next
necessary action. Detail paths, provenance, work counters, and transaction internals
belong in --verbose (proposed human detail option), --debug stderr, or --json.
Fatal errors include the relevant path/state, what was preserved, and safe
remediation. A success with warnings does not hide the warnings in data. Empty,
unconfigured, no-op, partial, and unsupported states each get deliberate text.

Success text goes to stdout. Human errors and progress/prompts go to stderr.
Final partial results must remain understandable with stderr captured; do not
print success before the last required phase. Emit a final newline. Narrow
terminals wrap/truncate safely; ASCII/plain output is fully usable. Optional
color must respect terminal detection/NO_COLOR and never carry sole meaning.
Sanitize untrusted control characters in names, paths, package descriptions, and
script log excerpts. Do not pass through arbitrary ANSI escapes from a package.

Redirection/piping disables decoration, not the selected format: without --json
it is still text. Do not start prompts from JSON, event hooks, noninteractive
stdin, or redirected output. Exact --json flag parsing must respect operand
values and -- separation; an operand literally containing '--json' is data.

## 6. JSON and exit compatibility

--json keeps the existing v1 envelope and one JSON document on stdout for handled
outcomes, including parser errors, refusal, interruption, and partial execution.
No prompts or progress enter stdout. Child script logs are bounded/captured, not
interleaved into machine output. Format selection must not change mutation,
source choice, or scope. New fields are additive; readers ignore unknown fields.
Existing lower-level command behavior and explicit guards remain supported.

Use the existing exit classes: 0 success/no-op/observational report; 2 invocation;
3 missing/invalid required input; 4 permission/precondition/stale-plan refusal;
5 external failure with no unresolved effects; 6 busy; 7 completed readiness check
found actionable drift; 8 partial/indeterminate effects/recovery; 10 invariant;
130 interruption. A declined required setup uses 4 with workflow incomplete;
its check-only counterpart uses 7. An observational inventory can succeed while
reporting incomplete readiness. Do not invent exit 9; it is already reserved in
planned fleet contracts.

An additive data.confirmation object may report the reason, exact scope/action
IDs, and plan hash for noninteractive consent. It is a proposed action, not an
execution receipt. Existing --json callers that relied on unguarded incidental
behavior receive a documented typed refusal, never a silent new authority grant.
Release notes/capabilities identify this stricter readiness/consent boundary.
