---
id: "RFC-MASK-0020"
title: "Tap-only deployment, fetching updates and doctor migration"
status: "Implementing"
owner: "MikeMarcin"
created: "2026-09-12"
metadata: {"milestone_plan":{"id":"tap-only-deployment","path":"docs/rfcs/plans/tap-only-deployment/milestone-plan.json"}}
---

# RFC-MASK-0020: Tap-only deployment, fetching updates and doctor migration

**Corrective proposal; not implemented or qualified by this pack.** Live import of packet `RFC-MASK-0020` (no renumber needed; live RFCs ended at RFC-MASK-0019). Retained packet: [assets/mask-corrective-managed-taps/](assets/mask-corrective-managed-taps/README.md); import record: [LIVE_IMPORT](assets/mask-corrective-managed-taps.LIVE_IMPORT.md).

**Accepted for implementation (September 12, 2026)** by the owner's `/implement-rfc RFC-MASK-0020` direction; implementing from RFC_BASE_SHA `b92372f` under the adopted plan [plans/tap-only-deployment](plans/tap-only-deployment/milestone-plan.json). Current frontier and per-criterion evidence: closeout [MASK-0106](../issues/10-backlog/MASK-0106-close-tap-only-deployment.md). Nothing is qualified until that closeout records it.

**Owner decisions (September 13, 2026; run `mask-rfc0020-2026-09-12-a`, mandate revisions r2, r3 and r4).**
- An offline install of a bare ID before its only tap is fetched refuses `source.unresolved`, naming the tap. `lock.resolution_required` is the offline refusal for a qualified `SOURCE/ID`. Retained case B04 is read with this decision; the retained packet is unchanged.
- Taps keep exact bytes. MASK disables Git line-ending conversion for tap operations by default; only an explicit opt-in at tap registration enables `core.autocrlf`. It was implemented at `4c0549f` by [MASK-0107](../issues/60-done/MASK-0107-tap-line-endings-exact-bytes.md), and MASK-0104 and MASK-0105 depend on it.
- The remaining d2 follow-up candidates are filed outside this RFC as [MASK-0108](../issues/30-in-progress/MASK-0108-authoring-checkout-branch-refusal.md), [MASK-0109](../issues/30-in-progress/MASK-0109-ensure-cold-dry-run-plan-hash.md) and [MASK-0110](../issues/30-in-progress/MASK-0110-refusal-after-retained-preparation.md).
- Mandate r4, Q4 ("point users to install and remove"): v2 declarations get no `project/user set|require|unrequire`. Those commands keep refusing `selection.command_unsupported`, and the refusal, help and documentation point to `install` and `remove`. This supersedes the Retirement sentence below that says the four commands "remain for v2 declarations". [MASK-0103](../issues/60-done/MASK-0103-help-docs-and-capabilities-truth.md) carries it.
- Mandate r4, Q5 ("just make migration best effort, we're going to run migration on a single machine and then drop it entirely so dont put a lot into it"): `doctor --migrate` is best effort. The AC05 gate is unchanged, so `project unregister --keep-links` and `workspace forget` stay refused on a v1 or v2 machine. A consumer that migration cannot convert is restored on disk first, and MASK-0103 documents that briefly. No further migration features or hardening are planned. The recorded migration notes are closed unless they block the owner's machine migration ([MASK-0105](../issues/30-in-progress/MASK-0105-owner-machine-migration-dogfood.md)). No acceptance criterion text is narrowed.

Amends applicable current behavior from RFC-MASK-0003 (`init --source`, shared
checkout `update`), RFC-MASK-0007 (a v2 catalog that still requires a legacy
checkout binding), RFC-MASK-0008 (the legacy live-checkout mode "remains
available") and RFC-MASK-0018 (task commands over legacy declarations).
Historical RFCs and evidence remain unchanged; update current contracts when this
implementation lands.

## Decision

A skill source is a **tap**: an approved Git repository identity that MASK
fetches into its own bare cache and resolves into exact, content-addressed
artifacts. AgentSkills is an ordinary tap. Every project and personal selection
is pinned by a lock and deployed from `MASK_HOME/store`, never from a working
checkout that the user edits. The live-checkout deployment mode, its machine
configuration and its commands are retired; existing machines and consumers are
migrated by `mask doctor`, not by hand.

`mask update` handles updates end to end: it fetches every referenced tap,
re-resolves each consumer against its selectors, discloses the change and applies
one journaled lock/link transaction. A tap's optional authoring checkout is for
publishing and `source dev-link` only; it is never an ordinary link target.

## Evidence and failure mechanism

The intended design was always the tap model; the bootstrap never reached it.
`mask init` accepts only `--source PATH` and records the user's own clone as the
machine's single live source (`mask.py`, `init` branch of `local_dispatch`).
Every legacy install then creates directory symlinks from
`<consumer>/.claude/skills/<id>` and `<consumer>/.agents/skills/<id>` straight to
`<clone>/skills/<id>` (`mask_fs.plan` legacy branch; `mask_pinned.target` case
without `resolution`). Editing the clone edits every consumer at once, and
`mask update` fast-forwards the user's clone (`mask_git.update`) rather than a
MASK-owned cache.

Machine config v2 did not fix this. Its schema still requires the v1 `source`
block and a `legacy_source` alias whose `authoring` equals that clone
(`schemas/machine-v2.schema.json`, `mask_sources.validate_config`). The catalog,
cache, store and lock machinery from RFC-MASK-0007/0008 is complete but reachable
only after `source migrate` and per-consumer `migrate --to-pinned`, both of which
depend on the clone being clean and on the configured branch. New consumers on a
v1 machine are always legacy (`mask_task.fresh_declaration`). Pinned `update`
never fetches (`mask_pinned.transition_dispatch` resolves from cache only), so
"handling updates" still meant a manual `source fetch` first. README line 5 and
the installation guide document the clone-linking journey as the product.

The owner's machine demonstrates the outcome: `~/.mask/config.json` is v1 with
`source.root` `C:\code\git\AgentSkills`, so `mask install` in any project would
link into that clone. See `SOURCE_BASIS.md` in the retained pack.

## Contract

The normative contracts are `assets/mask-corrective-managed-taps/contracts/CLI.md`,
`contracts/MIGRATION.md` and `contracts/machine-v3.schema.json`. Summary:

**Machine config v3.** `schema_version: 3`, `default_targets`,
`git_timeout_seconds`, `sources` (0 to 256 tap entries; the entry shape of v2
plus the optional `line_endings` policy, `exact` or `autocrlf`, that the owner's
exact-bytes decision above adds through MASK-0107; absent means `exact`). No
`source` block and no `legacy_source`. `mask_core.config` still
parses v1 and v2 for migration only; every command other than `capabilities`,
`config show`, `doctor`, `recover` and `self *` refuses a v1/v2 configuration with
`migration.required` (exit 4) naming `mask doctor --migrate --dry-run`.

**Bootstrap.** `mask init [--target T ...] [--git-timeout N]` writes an empty v3
catalog and state. `mask tap add NAME URL [--ref REF] [--packages PATH]
[--checkout PATH] [--autocrlf]` creates the machine config and state when they are missing,
so one command bootstraps a machine. `tap add` stays catalog-only and network-free.
`--checkout` binds an authoring checkout whose origin must normalize to the tap
identity; it is never read by install, list, ensure or update.

**Install.** New declarations are always v2 with an empty lock. A bare `ID`
resolves against every approved tap (`skill.ambiguous` names the choices,
`source.unresolved` names unfetched taps, `--offline` never fetches). A live
install fetches the tap into its bare cache on demand, resolves the exact commit,
materializes the payload in the store, writes the declaration and lock, registers
the consumer and links the store payload in one journal. Every owned link text
resolves under `MASK_HOME/store/v1/`, except an explicit `source dev-link`.

**Update.** `mask update` with no scope selects every registered consumer;
`--project PATH`, `--user`, `--all` and `--skill SOURCE/ID` narrow it. Unless
`--dry-run`, `--offline` or `--expect-plan-hash` is given, it fetches each
referenced tap exactly once, then resolves every selected consumer from the cache.
A tap whose fetch fails blocks only the consumers that reference it; the others
are resolved, disclosed and applied, and the command ends `update.incomplete`
(exit 4) naming the blocked roots. A rebound selector (`lock.ref_rebound`) refuses
the invocation unless `--allow-ref-rebind`. All lock, store and link changes for
the selected consumers activate through one journal. `source fetch` without a
name fetches every approved tap and deploys nothing; `source fetch NAME` and
`source fetch --locked` are unchanged.

**Doctor migration.** `mask doctor` reports `data.migration` for a v1 or v2
machine and for every legacy consumer, registered or not; `--check` exits 7 while
migration is required. `mask doctor --migrate [--alias NAME] [--dry-run]
[--expect-plan-hash H]` converts the machine and every registered legacy consumer
in one recoverable journal: the legacy checkout becomes a tap whose repository is
its configured remote (a `file://` identity of the clone when it has none, with a
warning), `authoring` retains the clone path, v1 declarations become v2
declarations bound to that alias, lock rows name the clone's current HEAD, that
HEAD is acquired into the tap cache from the local clone over file transport,
payloads are materialized and owned links are retargeted to the store. A machine
with no registered consumers migrates its configuration only. Dirty, unborn,
detached, diverged or unavailable inputs are typed refusals; nothing is reset,
stashed, deleted or pushed. On a v3 machine, `doctor --migrate --project PATH
--alias NAME` (or `--user --alias NAME`) converts a straggler v1 declaration
through ordinary install semantics.

**Retirement.** `init --source/--remote/--branch`, `source status`,
`source migrate` and `migrate` are removed from the command table and from
`capabilities`; invoking them is `invocation.invalid` (exit 2). `mask_git.update`,
the `'AgentSkills'` basename checks, `mask_task.v1_proposal`, the planner's
legacy link branch, the checkout case of `mask_pinned.target`, the v1
`skill list/show/validate` path and the v1 branches of `project/user
set|require|unrequire` are deleted; those four commands remain for v2
declarations. `schemas/machine-v1.schema.json` and `machine-v2.schema.json` are
retained as read-only migration inputs. `source dev-link`, `source publish`,
`skill import/provenance/record-adaptation`, `lock`, `ensure`, `integration.*`,
`launch`, `link adopt`, `recover` and `self *` keep their semantics.

## Integration boundary

MASK owns bootstrap, catalog, cache, store, lock, link, update, migration and
recovery semantics. AgentSkills owns package content and its workflow descriptor;
it needs no change to become a tap. The implement-rfc skill's own `mask ensure`
preflight is unaffected. Upstream documentation that names `mask init --source`,
`project require` on legacy declarations or the local-clone journey is a recorded
handoff, not a MASK code change. This pack does not authorize edits to another
repository, and it does not migrate any real machine except through the attended
dogfood card on the owner's explicit run.

## Out of scope

No store or cache pruning, no eager fetch on `tap add`, no per-consumer consent
for rebound selectors, no dependency solving, no automatic host reload, no fleet,
daemon, registry or MCP expansion, no copy-deployment fallback, and no relaxation
of Windows directory-symlink requirements. Portable profiles (RFC-MASK-0010) and
impact reports (RFC-MASK-0011) are unchanged by this RFC beyond losing the legacy
branch.

## Acceptance criteria

**RFC-MASK-0020-AC01** — **Tap-first bootstrap.** On an empty `MASK_HOME`,
`mask tap add agentskills URL` followed by `mask install implement-rfc --project P`
exits 0, creates machine config v3 with one tap and one bare cache under
`MASK_HOME/sources`, writes a v2 `.mask.json` and `.mask.lock.json`, and links
every enabled agent path, with no `init --source` step and no working checkout
anywhere on disk.

**RFC-MASK-0020-AC02** — **Links target the store only.** Every owned link
recorded in `state.json` and observed on disk, for project and personal scopes,
before and after `update`, resolves under `MASK_HOME/store/v1/`; no planner,
adoption or recovery path can produce a link text into a Git checkout except an
explicit `source dev-link`, and `tap add --checkout` never changes a link target.

**RFC-MASK-0020-AC03** — **Fetching, isolated updates.** `mask update` fetches
each referenced tap exactly once, applies all selected consumers' lock and link
changes in one journal with per-consumer disclosed diffs, continues for consumers
on healthy taps when another tap is unreachable (blocked roots named,
`update.incomplete`, exit 4), refuses a rebound selector without
`--allow-ref-rebind`, and never fetches under `--dry-run`, `--offline` or
`--expect-plan-hash`.

**RFC-MASK-0020-AC04** — **Doctor migrates legacy installs.** On fixture v1 and
v2 machines holding a legacy project, a legacy personal scope and an unregistered
v1 declaration, `mask doctor` reports `migration.required` (`--check` exits 7),
`--migrate --dry-run` writes nothing, `--migrate` yields a v3 config with the
clone as a tap, v2 declarations and locks at the clone HEAD, store-targeted links
and pinned records, a crash at every journal checkpoint recovers with
`recover --rollback` to exact prior bytes and links or with `--complete`, and a
machine with an empty registry migrates its configuration only.

**RFC-MASK-0020-AC05** — **Retired paths refuse precisely.** `capabilities` no
longer lists `init --source`, `source status`, `source migrate` or `migrate`;
invoking them exits 2 `invocation.invalid`; and on a v1 or v2 configuration
every command other than `capabilities`, `config show`, `doctor`, `recover` and
`self *` exits 4 `migration.required` with a `doctor --migrate` remediation.

**RFC-MASK-0020-AC06** — **Truthful help and documentation.** `mask --help`,
`mask update --help`, `mask doctor --help`, README, the guides, the CLI contract
and the state/recovery architecture describe only the tap model and doctor
migration, and a documentation test finds no retired command spelling outside
`docs/rfcs/assets`, historical RFC text and the migration guide's old-command
table.

**RFC-MASK-0020-AC07** — **Native real-package qualification.**
`scripts/qualify_real_package.py` passes on native Windows 11 and macOS against
the real AgentSkills repository added as a tap, including an upstream push
followed by `mask update` and a legacy-lab doctor migration, and the owner's real
v1 machine is migrated by `doctor --migrate` with the transcript recorded.

**RFC-MASK-0020-AC08** — **Structure and suite gates.**
`python scripts/verify_documentation.py --root .` reports zero violations with
this RFC, its nine cards and their reservation, and the full
`python -B -m unittest` suite passes on Windows and macOS with the tap-first
fixtures.

## Rollout and rollback

Import against live IDs and record the actual pre-implementation baseline. Land
config v3 and the tap-first fixtures before deleting legacy code so the suite
stays green at every card. The migration gate (`migration.required`) lands with
the engine retirement, not before. A journal written by this program
(`doctor.migrate`, tap-fetching `update`) is refused by the previous program with
`recovery.conflict`; finish pending recovery before switching executables, and
keep the self-update schema guard. Rollback of a migrated machine is
`recover --rollback` while the journal is pending; afterwards the previous
program can still read the retained v1/v2 bytes only through explicit recovery,
never by MASK rewriting a v3 configuration back. Never delete the user's clone,
the caches or the store to make rollback look successful.

## Risks stated plainly

Windows directory symlinks still need existing privileges. Store and cache
growth is unbounded apart from the fetch ceiling; nothing prunes. A rebound
selector in any consumer refuses an unqualified `update` for everyone until
`--allow-ref-rebind` or scoping. Running agents may cache instructions; a
retargeted link does not prove a host reloaded. Migrated locks may name a HEAD
that is not pushed (`migration.unpublished_commit`), and a `file://` fallback tap
is machine-local; fresh machines cannot reproduce those locks until the commit is
published or the tap is re-added with a remote. A v1 machine migrates to a
derived alias such as `agentskills` while a v2 machine keeps its existing
`legacy` alias, so docs must show both. A bare-ID install may fetch every
unresolved tap.

## Closeout

Exactly one linked closeout card records every criterion, actual command or
observation, outcome and implementation revision. Missing native evidence or an
unrun owner migration keeps the closeout open. Pack validation, fixture success
and documentation edits are not acceptance.
