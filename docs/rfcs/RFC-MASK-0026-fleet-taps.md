---
id: "RFC-MASK-0026"
title: "Centrally managed fleet taps"
status: "Implementing"
owner: "MikeMarcin"
created: "2026-11-06"
metadata: {"milestone_plan":{"id":"fleet-taps","path":"docs/rfcs/plans/fleet-taps/milestone-plan.json"}}
---

# RFC-MASK-0026: Centrally managed fleet taps

The November 6 owner request adds central tap management and canonical
manage-agent-skills fleet guidance. [Fleet command maintenance](RFC-MASK-0025-fleet-command-maintenance.md)
remains historical.

- AC1. A controller lists, adds and removes fleet-owned taps through the public
  CLI. All active peers are selected by default and repeated device selectors
  narrow the operation. Mutations require an exact reviewed plan and return
  verified per-device results, with incomplete delivery and lost-ack retry
  distinguishable from convergence. The preview describes the controller catalog
  effect. Tap changes leave caches and deployments alone.
- AC2. A device can grant exact network repositories and named scope aliases once.
  Signed requests preserve the enrolled binding and independently granted static
  sources. Centrally added taps become effective sources only in those aliases
  and never grant forwarding. Local bindings, transport choices, references,
  revocation and stale observations are respected.
- AC3. A public disposable fixture verifies the tap-to-fetch-to-install and
  upgrade workflow, ownership/authority refusals and retries. Canonical
  manage-agent-skills guidance uses capability discovery and current fleet CLI
  commands and is validated as a portable package. Existing fleet behavior retains
  its prior acceptance.

Closeout: [MASK-0150](../issues/20-ready/MASK-0150-fleet-taps.md).
