---
schema: "implement-rfc.card.v1"
id: "MASK-0150"
title: "Implement central fleet taps and canonical skill guidance"
status: "Done"
rfcs: ["RFC-MASK-0026"]
depends_on: ["MASK-0149"]
closeout_for: ["RFC-MASK-0026"]
metadata: {"milestone_plan":{"id":"fleet-taps","path":"docs/rfcs/plans/fleet-taps/milestone-plan.json"}}
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"733df16981838e6b9b307cf6a0db80927b73d34c","evidence":{"kind":"observation","detail":"Public signed tap list/add/untap, exact hashes, scoped/default selection, offline refusal, lost acknowledgement and committed receipt recovery."}},{"criterion":"AC2","outcome":"pass","revision":"733df16981838e6b9b307cf6a0db80927b73d34c","evidence":{"kind":"observation","detail":"Public fixture exercised exact and namespace grant boundaries, stable descriptor, static/local ownership, pinned transport, no forwarding, scope exclusion, referenced removal, revocation and stale apply."}},{"criterion":"AC3","outcome":"pass","revision":"733df16981838e6b9b307cf6a0db80927b73d34c","evidence":{"kind":"observation","detail":"Public tap-to-fetch-to-install/upgrade path passed. Canonical AgentSkills 4a28361df3e56f08f2e1ed088aa3f9995e96dab9 validated, installed for both adapters, and matched documented options."}}]
---

# MASK-0150: Centrally managed fleet taps

[RFC-MASK-0026](../../rfcs/RFC-MASK-0026-fleet-taps.md) owns AC1–AC3.
RFC_BASE_SHA: 9c83fd3d4c2c2cac5d19b090150ddcb9d6c0a051
Planned card: MASK-0150.

Mandate r5 covers the reviewed catalog changes and canonical fleet guidance
in source. Fixture roots and local bare remotes exercise the public CLI.

## Closeout evidence

| Criterion | Observation | Result | Candidate |
| --- | --- | --- | --- |
| AC1 | The public signed RPC fixture listed, added and removed managed taps with default and explicit subsets. Offline preview, lost signed acknowledgement and a failed receipt write kept incomplete outcomes visible. The same approved hash recovered exact committed receipts. | Pass | `733df16981838e6b9b307cf6a0db80927b73d34c` |
| AC2 | Exact and namespace grants, the namespace lookalike refusals, scope isolation, local ownership, pinned transport, no forwarding, stable enrollment, reference checks and revoked/stale requests passed in disposable fixtures. | Pass | `733df16981838e6b9b307cf6a0db80927b73d34c` |
| AC3 | A fresh catalog progressed through explicit fetch, delegated skill install and upgrade, followed by profile withdrawal and catalog removal. The AgentSkills source at `4a28361df3e56f08f2e1ed088aa3f9995e96dab9` validated and installed for both adapters with exact reference bytes. ASK-0132 closed at `a856c8b532eb68f5a19eaa20a6d693f266dc1b87`. | Pass | `733df16981838e6b9b307cf6a0db80927b73d34c` |

The exact MASK candidate passed 51 fleet, source, tap bootstrap, launcher
schema and README tests on macOS. The fixture substituted SSH delivery and
used the actual CLI, signing and device RPC. The program migration classifier
reported the two optional machine schema fields as additive.
