# Public acceptance, not just helper qualification

This is the required test plan, **not a record that MASK passes**. Existing
source/test suites remain useful. New acceptance starts before the preparation
that previously hid the defects. Use temporary consumer/source/MASK_HOME roots
and local bare remotes. Do not change real SRV, user roles, credentials or host
trust to run these cases.

## Journey rules

The first user invocation after permitted one-time launcher/source preparation
must be the documented task command. No fixture callback may pre-register the
consumer, pre-approve future auto-readiness, render roles, manufacture a matching
local ownership manifest, or apply the change before the invocation under test.
For testing an already-installed broken consumer, intentionally retain the old
role state and do not repair it before ensure runs.

Separate a raw subprocess helper, a --json helper, and a human terminal helper.
The human helper must never inject --json. Pipe tests are not terminal prompt
qualification. POSIX pseudoterminal tests cover automated prompt mechanics;
native Windows requires an actual supported console/PTY path or a recorded
bounded console interaction, not a mocked os.name. Use stdlib at runtime; any
additional development harness dependency is explicit and not a user prerequisite.

## Core CLI cases

| ID | Starting state and public operation | Required observation |
|---|---|---|
| C01 | Source initialized; no .mask.json or registration; `install alpha` | Complete scoped selection/deployment in one invocation; no manual register/apply/hash step |
| C02 | No personal selection/registration; `install alpha --user` | Personal home selected safely; project declaration untouched |
| C03 | Existing v2 alpha/beta pins and distinct target overrides; `install gamma` then `remove gamma` | Unrelated exact pins/intent retained; legacy string-mutator refusal not used |
| C04 | Reinstall selected skill; repeat ensure | No prompt, no byte/generation churn, no script execution |
| C05 | Bare name exists in two approved sources or another catalog is unresolved | Qualified choices/incomplete resolution, never first match silently chosen |
| C06 | Three skills x two agents; `inventory` without --json | Three rows, six links, truthful source/unpinned/host limits; not a JSON envelope |
| C07 | Per-agent drift, different producers/digests, unavailable consumer, excluded target, partial page | No false merged row, false absence, suppressed warning or false complete count |
| C08 | v2 pinned and dev-link report data | Useful basic listing or explicit unsupported boundary; not empty 'all good' legacy report |
| C09 | `mask`, help, version, every registered command's normal result type | Intentional human presentation; registry coverage catches an unhandled renderer |
| C10 | Pipe/redirection/narrow terminal/NO_COLOR/control chars | Human text remains text, no prompt/ANSI injection; no semantic loss through clipping |
| C11 | Explicit --json, common option placement, '--' and operand values containing '--json' | Exact selected format, one JSON document; operand contents do not select machine mode |
| C12 | Invalid args, collision, missing config, warning, partial and no-op | Useful human outcome, preserved data and safe next action; same correct exit/result semantics in JSON |
| C13 | Prompt shown; another process changes the selected manifest or leaf before yes | No lock held during input; stale-plan refusal before application |
| C14 | No/EOF/Ctrl-C at confirmation; JSON/redirected/event invocation requiring authority | No unauthorized action or hang; default-no and typed pending/interruption result |
| C15 | --yes with a source/tracked-file/script/expanded-scope permission missing | No bypass; action remains incomplete or precisely refused |
| C16 | Normal online shared update against local bare remote | Fetch, freeze, human impact approval, activation and final verification in one invocation |
| C17 | Pinned scoped update; exact commit and unrelated bindings retained | Only selected refreshable bindings change; format does not change scope |
| C18 | Dry-run/offline/expected-hash update with cold or moved refs | No implicit fetch during preview/guarded apply; precise unresolved/stale result |
| C19 | Explicit local legacy update whose source affects other consumers | Expanded impact disclosed/approved; --yes cannot silently widen it |
| C20 | Interrupted declaration/link transaction or pending prior recovery | Existing recovery invariant/exit 8 preserved; no force/reset/overwrite workaround |
| C21 | Execute short README project/user/update recipes as written | Complete public workflow without injected JSON, hidden setup or manual hash transfer |

Golden files in examples/human show intended information hierarchy, not fixed
terminal-width glyph snapshots for every OS. Assert material facts and absence
of serialization fallback; reserve exact strings for stable small outputs.

## Workflow readiness cases

| ID | Starting state and public operation | Required observation |
|---|---|---|
| W01 | New selected implement-rfc contract, correct skill links, old roles without rfc-integrator; `ensure --check` | Nonzero complete readiness; exact missing/stale role named |
| W02 | Same starting state; `ensure` with static assets available | Typed exact role deployment, no generator/script prompt, recheck before success |
| W03 | Fresh Git clone with tracked correct native files and coherent portable lock, no local renderer manifest | Pass prerequisites without any script or ownership takeover; tracked bytes/index unchanged |
| W04 | Same tracked files but changed relevant consumer profile/input or output bytes | Stale/incomplete; automatic/event mode does not overwrite; explicit manual change requires shown approval |
| W05 | Only unrelated README/board content changes | No role regeneration or model calls; relevant-role fingerprint remains valid |
| W06 | Required generated variant, explicit interactive yes | One prompt, frozen staged preparation, exact publication/recheck, no copy/paste command instruction |
| W07 | Required generated variant, no/EOF; check/dry-run; unapproved JSON/event/--yes | No package code (including check function) runs; task remains incomplete |
| W08 | Noninteractive exact plan plus named setup action approval | Only those frozen actions run; malformed or foreign approval cannot grant execution |
| W09 | Script entrypoint or imported helper changes after approval | Frozen approved bytes used or stale refusal; live imports cannot evade fingerprint |
| W10 | Script timeout/cancel/output overflow/exception | Owned process tree stopped; bounded diagnostic output; correct stage/partial classification |
| W11 | Crash before/after launch, after staged output, during final publish, before journal cleanup | No silent redispatch; exact intent recovery or explicit uncertainty; no false rollback claim |
| W12 | Extra/traversing/symlink/unsupported native output, parent replacement, new collision during staging | No publication outside declared destinations; preserve observed conflicting objects |
| W13 | Existing renderer-owned legacy files, unknown marker-only files, and modified managed files | Explicit verifiable ownership handoff only; no glob deletion or marker-only adoption |
| W14 | Codex-only / Claude-only / not-applicable platform / user versus project / two worktrees | Correct selected outputs only, no cross-scope/context leak; host shadowing visible |
| W15 | Competing skills request same agent role name with different bytes; identical compatible contributions | Conflict with both producers, or deliberate sharing; removing one contribution does not remove another's required output |
| W16 | Candidate update adds integrator, retires legacy name or changes route/tools; explicit local override | Requirements evaluated from selected candidate; preserve local intent or block, never choose a silent fallback |
| W17 | install/update finish with script declined/failed; launch with incomplete prerequisites | Overall task nonzero and phases truthful; host never starts through strict prelaunch |
| W18 | Cheap inventory then doctor --check | Inventory does not execute/scan extra bodies to render; doctor observes declared prerequisites without package code |
| W19 | Actual AgentSkills package in two disposable consumer contexts via real MASK links | Consumer addenda, routing override and entrypoints remain correct and source immutable |
| W20 | Fresh native host observes current named role/configuration | Record host/version and actual discovery/loading boundary; no inherited default launch relabelled as integrator |
| W21 | Source-only validator and renderer unit suite pass, consumer roles deliberately absent | Consumer complete-readiness test still fails; source qualification cannot satisfy it |

## Native qualification scope

For macOS and Windows, run the ordinary CLI/launcher/terminal journey and focused
role-file/ownership/process tests on native Python/Git/filesystems. Reuse the
portable parser/selection tests instead of a full host x OS x interpreter cross
product. Linux results support portable logic but do not stand in for native lanes.

A CLI `--version` host launch is not role discovery. A role file on disk is not
proof the current session used its tools or effective model/effort. Fresh-host
read-only discovery without model turns should be used where available. Actual
subagent execution/model claims require separately approved bounded runtime work;
otherwise keep host_load/effective execution unverified and do not claim it.

No unapproved live SRV migration is needed. The SRV-shaped disposable fixture is
mandatory; a real consumer pilot may be added only with its own named scope and
ownership-safe window. Static/check-only pathways cannot be qualified solely by
synthetic role names when the claimed integration is the current implement-rfc.

## Reporting and test economy

Record each acceptance criterion with its exact command or observation, outcome,
implementation revision, and relevant limitation. Cases can share one fixture
journey where that is clearer; this table does not require 42 separately launched
agents, transcripts, full-suite runs or evidence bundles. Reuse unchanged results.
A focused regression that actually fails before the fix is stronger than another
broad 'qualified' label. Keep the closeout open when its required upstream/native
boundary was not exercised.

**W22 — Old MASK with a new workflow package:** the old successful link-only
ensure is not accepted as workflow readiness by the new implement-rfc preflight.
Capabilities/result-version mismatch is explicit; no silent program upgrade,
script execution, or generic-role fallback occurs. This is part of
RFC-MASK-0019-AC01/AC08, not permission to widen the pack into an auto-updater.
