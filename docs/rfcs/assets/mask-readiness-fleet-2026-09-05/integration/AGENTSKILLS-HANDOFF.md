# AgentSkills handoff request (no speculative upstream IDs)

## Requested ownership split

MASK owns runtime, source resolver/import transport, artifacts, locks, scope targeting, profiles, fleet operations, reports, tests and public CLI/protocol documentation. AgentSkills owns canonical skill text, reviewed compatibility metadata, source-index/bundle definitions, upstream notices/provenance content and any genuinely necessary shared helper adjustments.

The supplied dump does not include AgentSkills contents. Before implementation, inspect the real source for existing provenance/import/metadata conventions and reuse them where compatible; do not replace established useful records based on absence from MASK's dump.

## Bounded handoff

Update manage-agent-skills after the public commands exist. It should resolve exact inputs, preserve incremental versus exact-set scope, use ensure for lifecycle restoration, distinguish fetch/lock/update/publish, honor all-supported agent defaults and per-skill overrides, import copy versus tap under configured policy, and report per-device complete/pending/inapplicable/unknown results honestly.

It must not instruct agents to hand-edit state.json, copy user registries between machines, replace whole discovery roots, run a second installer into managed destinations, infer device enrollment from a past conversation, or bypass source/host/SSH trust. It should not force plan/hash/apply/doctor turns for routine already-authorized mechanics.

Add actual metadata/bundles/provenance only for inspected packages. Preserve free-text host metadata and notices; absent evidence is unknown. No blanket republishing, automatic external source push or production credential handling is part of this handoff.

## Live linkage

Upstream integrator allocates its own card IDs. Attach the actual upstream reference to the local handoff card's external_depends_on when available. Record upstream completion revision and a local public-CLI check before accepting integration. A proposed handoff file is not an upstream completion receipt.
