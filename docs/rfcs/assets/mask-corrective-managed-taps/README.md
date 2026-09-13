# MASK corrective RFC pack: tap-only deployment

**Add a tap. Install from MASK's own copy. Update and migrate with one command.**

This pack corrects a design gap in MASK: the tap, cache, store and lock machinery
exists, but the bootstrap still records the user's own local AgentSkills clone as
a live source and symlinks every consumer straight into it. The pack contains
**one proposed RFC and nine provisional issue cards**, an authored milestone
plan, normative CLI and migration contracts, a draft machine schema, import
instructions and a pack validator.

## The intended everyday experience

```sh
# Once per machine; no local skill checkout is required.
mask tap add agentskills https://github.com/MikeMarcin/AgentSkills.git

# In the project.
mask install implement-rfc
mask list
mask ensure
mask update

# Personal scope remains explicit and independent.
mask install coauthoring --user
```

`install` fetches the tap into a MASK-owned bare cache on demand, pins the exact
commit in `.mask.lock.json`, copies the payload into the content-addressed store
and links that copy. `update` fetches every referenced tap, re-resolves each
consumer against its selector and applies one journaled change. An existing
machine that still points at a local clone is migrated by `mask doctor --migrate`.
AgentSkills becomes an ordinary tap; a tap's optional authoring checkout serves
`source publish` and `source dev-link` only.

## Implementation unit

| RFC | Corrective outcome | Initial implementation order |
|---|---|---|
| [RFC-MASK-0020](docs/rfcs/RFC-MASK-0020-tap-only-deployment.md) | Tap-only deployment, fetching updates, doctor migration and retirement of the live-checkout mode | Baseline and fixtures first; bootstrap; engine retirement with fetching updates; doctor migration; docs; native qualification and owner migration; closeout |

IDs are **provisional**: the live board at authoring time ends at RFC-MASK-0019
and NEXT_ID `MASK-0098`. Import against the live board, not those numbers. Do not
overwrite settled RFCs, counter files or unrelated cards.

## Start here

Give [IMPLEMENTATION_PROMPT.md](IMPLEMENTATION_PROMPT.md) to the implementing
agent. [IMPORT.md](IMPORT.md) describes reservation and integration. The
[authored milestone plan](milestone-plan.json) groups the cards into integration
outcomes; [MILESTONES.md](MILESTONES.md) is its generated view. The imported card
dependency graph is the live scheduling authority.

Normative details are in [the CLI contract](contracts/CLI.md), [the migration
contract](contracts/MIGRATION.md) and [the draft machine schema](contracts/machine-v3.schema.json).
[ACCEPTANCE.md](ACCEPTANCE.md) specifies public-command journeys including
negative cases and native boundaries. [SOURCE_BASIS.md](SOURCE_BASIS.md)
records the inspected baseline and the observed defect. [CHANGE_MAP.md](CHANGE_MAP.md)
lists what is retired, added and retained.

## What is deliberately not included

No store or cache pruning, no eager fetch on `tap add`, no per-consumer consent
for rebound selectors, no dependency solving, no copy-deployment fallback, no
change to Windows symlink requirements, no fleet, daemon, registry or MCP work,
and no migration of any real machine other than the attended owner dogfood card.

## Pack checks

```sh
python3 -B tools/validate_pack.py
python3 -B /path/to/implement-rfc/examples/milestone-plans/validate.py milestone-plan.json
```

These check this pack, not MASK implementation or native behavior. See
[VALIDATION.md](VALIDATION.md) for actual results.
