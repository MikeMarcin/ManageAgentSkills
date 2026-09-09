# MASK corrective RFC pack

**Simple commands. Useful output. A workflow that is actually set up.**

This pack corrects the public MASK experience demonstrated in the September 8–9
conversation. It does not replace MASK's ownership/recovery engine or reopen its
entire roadmap. It contains **two proposed RFCs and twelve provisional issue
cards**, with import instructions, concrete terminal examples, a bounded workflow
contract, regression fixtures, and pack-validation tools.

## The intended everyday experience

```sh
# In the project; source/launcher setup is a one-time prerequisite.
mask install implement-rfc
mask list
mask ensure
mask update
mask remove wizard

# Personal scope remains explicit and independent.
mask install coauthoring --user
```

`inventory` remains supported. `--project PATH` selects a different project.
`--json` explicitly requests the machine protocol. The command names above are
this pack's proposed task interface, not a claim that the supplied build already
supports them or a verbatim recovery of an earlier user-authored command list.
Existing lower-level commands remain available for precise automation.

Normal operations absorb declaration, registration, planning, deployment, and
verification. People do not copy plan hashes or orchestrate several commands to
install one skill. Significant new authority is confirmed within the operation.

Native role definitions may be checked into the skill repository or the consumer
repository. Generation is authoring work, not a mandatory installation ritual.
When a genuine consumer-specific setup script is necessary, `ensure` explains it,
asks `Run this setup? [y/N]`, executes the approved work, and verifies the result.
Declining or failing required setup never produces a ready result.

## Implementation units

| RFC | Corrective outcome | Initial implementation order |
|---|---|---|
| [RFC-MASK-0018](docs/rfcs/RFC-MASK-0018-task-oriented-cli-and-human-output.md) | Complete task commands, human output by default, straightforward confirmation, and a short executable README | Human renderer first; then task operations and update flow |
| [RFC-MASK-0019](docs/rfcs/RFC-MASK-0019-complete-workflow-readiness.md) | Declared native-role dependencies, checked-in assets, consented setup, and truthful ensure/launch readiness | Static checks/deployment first; optional scripts second; real workflow integration last |

IDs are **provisional**: the supplied MASK snapshot ends at RFC-MASK-0017 and
NEXT_ID MASK-0083. Import against the live board, not those historical numbers.
Do not overwrite settled RFCs, counter files, or unrelated cards.

## Start here

Give [IMPLEMENTATION_PROMPT.md](IMPLEMENTATION_PROMPT.md) to the implementing
agent. [IMPORT.md](IMPORT.md) describes reservation and integration.
[IMPLEMENTATION_ORDER.md](IMPLEMENTATION_ORDER.md) describes useful milestones;
the imported issue dependencies become the live scheduling authority.

Normative details are in [the CLI contract](contracts/CLI.md) and
[the workflow-readiness contract](contracts/WORKFLOW_READINESS.md).
[ACCEPTANCE.md](ACCEPTANCE.md) specifies public-command journeys, including
negative cases and native-platform boundaries. [SOURCE_BASIS.md](SOURCE_BASIS.md)
separates supplied source facts from proposed changes.

The [AgentSkills handoff](integration/AGENTSKILLS_HANDOFF.md) is explicit:
MASK owns the engine; AgentSkills owns its role payloads and runtime reporting.
This pack does not authorize edits to another repository or bulk consumer
migration. RFC-MASK-0019 cannot claim complete implement-rfc integration from a
synthetic package alone.

## What is deliberately not included

No fleet/daemon/MCP expansion, model or effort changes, new quota-saving claims,
mandatory live model benchmark, full package-hook framework, arbitrary install
shell commands, or replacement skill-copy deployment mode. This is a usability
and readiness correction, not a second package manager.

## Pack checks

```sh
python3 -B tools/validate_pack.py
python3 -B -m unittest discover -s tools -p 'test_pack.py'
```

These check this pack, not MASK implementation or native host loading. See
[VALIDATION.md](VALIDATION.md) for actual results. Golden outputs and the replacement
README are design fixtures, not claims of already implemented behavior.
