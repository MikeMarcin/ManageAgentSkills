---
schema: "implement-rfc.card.v1"
id: "MASK-0149"
title: "Implement and verify fleet command maintenance"
status: "Done"
rfcs: ["RFC-MASK-0025"]
depends_on: ["MASK-0074", "MASK-0146"]
closeout_for: ["RFC-MASK-0025"]
metadata: {"milestone_plan":{"id":"fleet-command-maintenance","path":"docs/rfcs/plans/fleet-command-maintenance/milestone-plan.json"}}
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"baa86711f80c6d28a837a3b3eb5b2868f214a99d","evidence":{"kind":"observation","detail":"Native pinned SSH pair and focused public fixture verified bare install and explicit legacy selection."}},{"criterion":"AC2","outcome":"pass","revision":"baa86711f80c6d28a837a3b3eb5b2868f214a99d","evidence":{"kind":"observation","detail":"Native same-parent fast-forward and differing-parent cherry-pick used one canonical commit. Staging, personal pin and locally co-owned contribution were preserved."}},{"criterion":"AC3","outcome":"pass","revision":"baa86711f80c6d28a837a3b3eb5b2868f214a99d","evidence":{"kind":"observation","detail":"Both native devices reached one reviewed program revision. Focused fixtures covered lost-ack retry, an overlapping edit and an incompatible protocol."}},{"criterion":"AC4","outcome":"pass","revision":"baa86711f80c6d28a837a3b3eb5b2868f214a99d","evidence":{"kind":"observation","detail":"macOS and Windows public commands and signed results verified. Disposable SSH listener and native fixture cleanup confirmed."}}]
---

# MASK-0149: Implement and verify fleet command maintenance

[RFC-MASK-0025](../../rfcs/RFC-MASK-0025-fleet-command-maintenance.md)
owns AC1–AC4. RFC_BASE_SHA: 80e2fc4130e9ac5b9fe8cf6164c35fdaac76cf93
Planned card: MASK-0149. The new commands use the existing enrolled endpoint,
identity and signed transport.

| Criterion | Evidence | Outcome | Revision |
| --- | --- | --- | --- |
| AC1 | Native pinned SSH pair and focused public fixture verified bare install and explicit legacy selection. | Pass | `baa8671` |
| AC2 | Native same-parent fast-forward and differing-parent cherry-pick used one canonical commit. Staging, personal pin and locally co-owned contribution were preserved. | Pass | `baa8671` |
| AC3 | Both native devices reached one reviewed program revision. Focused fixtures covered lost-ack retry, an overlapping edit and an incompatible protocol. | Pass | `baa8671` |
| AC4 | macOS and Windows public commands and signed results verified. Disposable SSH listener and native fixture cleanup confirmed. | Pass | `baa8671` |

See the [native verification record](../../development/fleet-native-acceptance.md#fleet-command-maintenance).
