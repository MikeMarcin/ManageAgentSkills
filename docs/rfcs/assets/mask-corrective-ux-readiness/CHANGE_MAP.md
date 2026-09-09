# Correction map

| Existing boundary | Deliberate amendment | Retained invariant |
|---|---|---|
| CLI contract says no prompts | Human manual operations can confirm significant authority in process | Noninteractive, JSON, and event hooks never wait for a terminal |
| Non-JSON success dumps result JSON | Every command has human presentation; machine serializer only under --json | One result model and stable machine envelope |
| Tests/support.py always appends --json | Add an independent human/public/terminal test path | Existing protocol tests remain intact |
| Manifest/register/apply are separate public chores | install/remove are complete task operations; old primitives remain | Set union/subtraction, scope independence, exact preconditions |
| v2 legacy membership commands refuse | New task implementation edits pinned selections and coherent locks directly through typed engine operations | Retain unrelated resolutions; no implicit migration |
| Update requires callers to fetch/preview/copy hash | Normal update coordinates acquisition and a frozen preview/application | Offline/dry-run rules, exact pins, source identity, no reset/stash/push |
| ensure requires previously recorded auto-readiness approval | Explicit manual invocation provides one-operation authority; automatic events still require their policy | No implicit permanent approval, source trust, script or network grant |
| Ready means only declared skill links | Complete workflow readiness includes declared roles/context/setup | Host loading remains a separate observation |
| Skill install never executes package scripts | Static deployment still executes none; selected setup may execute after exact consent | No generic hooks, shell eval, elevated permissions, or silent code execution |
| All role files are locally generated/ignored | Support shipped static definitions and repository-owned checked-in outputs | Ownership is not inferred from a marker; tracked files preserved |
| Source qualification renders test consumers first | User-path acceptance starts without roles/registration and exercises public ensure | Source checks and native/product checks remain distinct |

Update current AGENTS.md, project.md, CLI contract, test-boundaries, help,
capabilities, and README where the implementation changes their instructions.
Leave settled RFC text and historical closeout evidence unchanged; the two new
RFCs explicitly amend their applicable clauses. Coordinate with unfinished
RFC-MASK-0011 reporting cards: simple default inventory is not contingent on full
impact reporting, profiles, or fleet work. Do not duplicate those larger features.
