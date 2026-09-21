---
schema: "implement-rfc.card.v1"
id: "MASK-0125"
title: "Retain exact package locks across content-equivalent branch advances"
status: "Done"
rfcs: []
depends_on: []
metadata: {"milestone_plan":{"id":"stable-package-locks","path":"docs/rfcs/plans/stable-package-locks/milestone-plan.json"}}
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"13abae4d683b42fc25a02790ffa95639215717d6","evidence":{"kind":"observation","detail":"Shipped public CLI fixture commits its own consumer lock, upgrades --all without further lock changes, then advances only a changed skill and converges after the next lock-only commit. The baseline failed this check before the fix."}},{"criterion":"AC2","outcome":"pass","revision":"13abae4d683b42fc25a02790ffa95639215717d6","evidence":{"kind":"observation","detail":"Resolver tests cover support/setup bytes, executable mode, metadata, provenance addition/change/removal, source/path identity, exact commits, selector changes, moved annotated tags, identical-content non-fast-forward branches, missing ancestry and tampered prior digest evidence. The new approved-repository regression exposed spelling-only reuse across distinct repositories; its same-identity correction passes the final focused rerun."}},{"criterion":"AC3","outcome":"pass","revision":"13abae4d683b42fc25a02790ffa95639215717d6","evidence":{"kind":"observation","detail":"Public warm/cold shared-consumer test retains distinct commits for equal payload digests and applies the preview hash. Missing-link repair keeps lock bytes unchanged. Pinned update/recovery, cold plan hashes, upgrade setup/readiness, legacy URL spelling and strict artifact checks pass."}},{"criterion":"AC4","outcome":"pass","revision":"13abae4d683b42fc25a02790ffa95639215717d6","evidence":{"kind":"observation","detail":"Combined focused run: 50 tests/225.201s, 49 passed and the repository-identity regression failed before its correction. Final corrected regression passes in 1.760s; 2 selector/identity checks also passed in 11.078s. No skips or remaining failures. Cooperative receipts preserve both live repositories declarations/locks; fixture roots empty. Documentation gate: 23 RFCs, 125 cards, 0 violations. git diff --check and focused code-simplifier self-review pass. No native Windows, serving-runtime or independent review claim; preexisting live state.drift left unchanged."}}]
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

## Verified result

Implementation: `13abae4d683b42fc25a02790ffa95639215717d6`. Branch candidates retain
the exact previous row only after candidate validation, proven locked-commit
ancestry, full identity/digest comparison and exact prior-resolution verification.
Payload views use the normalized complete resolution identity. Explicit selectors,
tag moves and approved actual rebinds still advance. The repository-change test
also exposed and corrected spelling-only reuse across different repositories.
The guide records the ancestry boundary and root-package limitation.

The baseline self-hosting regression failed because a lock-only commit produced
another lock change. The implemented public journey converges, advances only a
changed skill, preserves warm/cold shared resolutions and repairs missing links.
Focused integration ran 50 tests in 225.201s: 49 passed; the repository-identity
case failed before its correction. That case passed on the final code in 1.760s;
the selector/identity pair also passed in 11.078s. No skips or unresolved failures.
Checks cover `tests.test_locks`, `tests.test_stable_locks`, `tests.test_pinned_update`,
`tests.test_cold_store_plan_hash`, `tests.test_upgrade_readiness`, the legacy URI
lock-spelling test and the strict forwarded/reused artifact identity tests.

Cooperative qualification receipts in `/tmp/mask-content-lock-0125/` confirm both
live repositories' declaration/lock bytes were preserved; disposable fixture roots
are empty and all task commands have stopped. The initial combined command failed
only on the corrected case; its receipt still confirms unchanged live files.
Documentation validation reports 23 RFCs, 125 cards and zero violations. Focused
code-simplifier self-review and `git diff --check` pass. The direct milestone
checkpoint reports closeout. No push, live migration, native Windows acceptance,
independent review or serving-runtime verification is claimed.
