---
schema: "implement-rfc.card.v1"
id: "MASK-0081"
title: "Complete approved clone boundaries and user-level startup fallback"
status: "Done"
rfcs: ["RFC-MASK-0006"]
depends_on: ["MASK-0024", "MASK-0027"]
metadata: {"discovery": "Integration review found that explicit-root-only approval and project-local host hooks require repeated setup for future clones."}
acceptance: [{"criterion":"RFC-MASK-0006-AC01","outcome":"pass","revision":"8ddb5d30c2fc876a458c11c9414d7e70fb822b1b","evidence":{"kind":"command","detail":"python3 -B -m unittest tests.test_ensure tests.test_host_integration tests.test_workspace_lifecycle: 24 tests passed. A generated user-level adapter command readies a future approved local clone and registered personal scope. Wrong-origin/outside/replaced-boundary requests and credential-bearing identities refuse; direct revoke refuses inherited authority. Project-local and user-level settings remain independently owned, with no actual host-loading claim."}},{"criterion":"RFC-MASK-0006-AC02","outcome":"pass","revision":"8ddb5d30c2fc876a458c11c9414d7e70fb822b1b","evidence":{"kind":"command","detail":"python3 -B -m unittest tests.test_ensure tests.test_host_integration tests.test_workspace_lifecycle: 24 tests passed. A generated user-level adapter command readies a future approved local clone and registered personal scope. Wrong-origin/outside/replaced-boundary requests and credential-bearing identities refuse; direct revoke refuses inherited authority. Project-local and user-level settings remain independently owned, with no actual host-loading claim."}},{"criterion":"RFC-MASK-0006-AC05","outcome":"pass","revision":"8ddb5d30c2fc876a458c11c9414d7e70fb822b1b","evidence":{"kind":"command","detail":"python3 -B -m unittest tests.test_ensure tests.test_host_integration tests.test_workspace_lifecycle: 24 tests passed. A generated user-level adapter command readies a future approved local clone and registered personal scope. Wrong-origin/outside/replaced-boundary requests and credential-bearing identities refuse; direct revoke refuses inherited authority. Project-local and user-level settings remain independently owned, with no actual host-loading claim."}},{"criterion":"RFC-MASK-0006-AC06","outcome":"pass","revision":"8ddb5d30c2fc876a458c11c9414d7e70fb822b1b","evidence":{"kind":"command","detail":"python3 -B -m unittest tests.test_ensure tests.test_host_integration tests.test_workspace_lifecycle: 24 tests passed. A generated user-level adapter command readies a future approved local clone and registered personal scope. Wrong-origin/outside/replaced-boundary requests and credential-bearing identities refuse; direct revoke refuses inherited authority. Project-local and user-level settings remain independently owned, with no actual host-loading claim."}}]
---

# MASK-0081: Complete approved clone boundaries and user-level startup fallback

## Scope and acceptance

Own mask.py, mask_ensure.py, mask_integration.py, focused ensure/host tests and current readiness docs. Implement the already accepted RFC-MASK-0006 repository-plus-physical-clone-root authority and default user-level host adapter installation. Preserve explicit root identity, host trust and unrelated settings; no actual user deployment or trust grant. Root-scoped revocation must not misleadingly claim to revoke inherited repository authority.

AC01/AC02: a future local clone under the explicitly approved physical boundary reaches ensure through the machine-owned host adapter, without separate registration/apply. Wrong repository, outside/replaced boundary and credential-bearing identity inputs refuse.

AC05/AC06: user-level and project-local host entries use the existing owned entry journal, preserve unrelated configuration, and report actual host loading as unverified. Focused fixture protocol and public CLI checks; no fabricated native host-loading observation.

Required discovered card for the RFC-MASK-0006 closeout. Existing Done cards retain their original slice evidence. No additional native-platform claim is made by this card.
