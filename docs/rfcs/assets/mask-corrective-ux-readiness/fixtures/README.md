# Synthetic regression inputs

These are **test packages, not usable agent skills or live native role definitions**.
Their model field is deliberately `fixture-model-do-not-run`. Never deploy them
into a real user's host directories. They contain no user transcript or credentials.

static-package contains the eight role names found in the supplied current
AgentSkills roles.json for both agents, but not that package's substantive prompts
or routing values. It demonstrates the descriptor and no-generation contract.
generated-package demonstrates only the fixed staged fixture action interface;
it is not a replacement for the real AgentSkills handoff. legacy-inventory.json
is a privacy-normalized synthetic version of the six-row shape the user pasted.

The consumer directory contains intentionally minimal synthetic workflow inputs.
Real integration acceptance must use valid actual AgentSkills consumer contexts,
not pretend this placeholder is the production project schema.

Pack validation checks shapes, hashes, references and coverage. MASK acceptance
still needs to implement the protocol and exercise these cases through its actual
public command paths. A model name in a fixture is not evidence of available models.
