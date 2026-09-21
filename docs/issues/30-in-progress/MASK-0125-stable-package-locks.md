---
schema: "implement-rfc.card.v1"
id: "MASK-0125"
title: "Retain exact package locks across content-equivalent branch advances"
status: "In Progress"
rfcs: []
depends_on: []
metadata: {"milestone_plan":{"id":"stable-package-locks","path":"docs/rfcs/plans/stable-package-locks/milestone-plan.json"}}
---

# MASK-0125: Retain exact package locks across content-equivalent branch advances

The owner approved the investigated fix for AgentSkills consuming its own skills:
committing an updated consumer lock advances the source branch without changing
the selected packages, so the next upgrade must not rewrite those package locks.
Use the existing exact-resolution contract in RFC-MASK-0008; this follow-up does
not close that RFC or extend its outstanding native acceptance.

Baseline: `18b82ec5248e3712e9d2e9cc0e0ac822ca471a73`.
Mandate: `stable-package-locks`, revision 1; owner `/root/astra_self_reference`.
The owner explicitly retained the same requested Astra/xhigh agent for investigation
and implementation. Direct strategy, no delegation; serving runtime is not attested.

- AC1: A self-hosted lock-only commit and unrelated package changes leave unchanged
  branch-selected package rows and lock bytes stable; actual package changes advance.
- AC2: Complete source/path/selector/digest identity and exact retained resolution
  verification remain enforced. Explicit selectors, moved tags and approved actual
  branch rebinds advance; unavailable or invalid exact evidence fails closed.
- AC3: Warm/cold shared consumer payload views preserve exact identities, public
  preview/apply agrees, and unchanged packages still receive readiness repair.
- AC4: Focused checks, documentation, self-review and explicit-path commits complete
  without altering the preexisting `.mask.lock.json` or live consumers.

Scope: resolver and payload-view integration, focused fixture tests, the source and
upgrade guide, and this follow-up's bookkeeping. No push, credential changes,
live tap fetches, live consumer migration, or AgentSkills source edits.

## Plan and checkpoint

Resolve and validate the candidate first; retain the prior row only for the same
branch and complete package identity after proving ancestry and verifying the
prior exact resolution. Keep payload views keyed to their exact resolution.
Document ancestry relative to the locked commit and the limitation when the lock
itself belongs to a root package's payload. Use temporary fixtures/local bare taps.

Live direct workflow preflight reports existing `state.drift`; no custom roles are
required. This work does not repair the live consumer. No independent or native
acceptance is required for this bounded fix; do not claim either from local tests.
