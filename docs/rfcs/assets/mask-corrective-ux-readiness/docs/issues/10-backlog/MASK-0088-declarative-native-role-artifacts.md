---
schema: "implement-rfc.card.v1"
id: "MASK-0088"
title: "Check and deploy declared native roles without rendering"
status: "Backlog"
rfcs: ["RFC-MASK-0019"]
depends_on: ["MASK-0083"]
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": true, "packet_key": "declarative-native-role-artifacts"}
---

# MASK-0088: Check and deploy declared native roles without rendering

## Objective and owned paths

mask_packages.py passive workflow descriptor validation, mask_adapters.py typed role destinations, mask_fs/mask_pinned typed outputs and recovery schema, focused role fixtures.

## Bounded work

Implement the minimal descriptor, static asset validation and required consumer-input observation. Support already committed role files and portable locks without prior local renderer ownership. Publish absent/unchanged managed role files via the existing engine. Keep repository-owned files separate and preserve package hazard guards; add only the narrow explicit native-role artifact kind.

## Acceptance

Static package roles and valid consumer-checked-in roles pass on a fresh clone with zero script calls. Missing rfc-integrator, changed inputs, stale locks, invalid role content and wrong targets fail complete readiness. Unknown/edited/tracked files, linked parents, role collisions and foreign ownership are preserved; unrelated source docs do not cause regeneration.

Criterion coverage: RFC-MASK-0019-AC01, RFC-MASK-0019-AC02, RFC-MASK-0019-AC03, RFC-MASK-0019-AC06.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary. Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation, and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Not started. Claim the live remapped card before edits. No code implementation,
native result, host loading, user approval, or quota improvement is asserted.
