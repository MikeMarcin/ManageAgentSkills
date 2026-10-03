---
schema: "implement-rfc.card.v1"
id: "MASK-0064"
title: "Coordinate canonical AgentSkills guidance and metadata handoff"
status: "Backlog"
rfcs: ["RFC-MASK-0017"]
depends_on: ["MASK-0071", "MASK-0072", "MASK-0053"]
external_depends_on: ["AgentSkills:ASK-0095", "AgentSkills:ASK-0096"]
metadata: {"packet": "mask-readiness-fleet-2026-09-05", "packet_key": "agent-handoff", "stage": "A–D — integration and owner workflow", "provisional_id": false}
---

# MASK-0064: Coordinate canonical AgentSkills guidance and metadata handoff

Governing RFC: [RFC-MASK-0017](../../rfcs/RFC-MASK-0017-integration-and-personal-dogfood.md). Live IDs confirmed by the committed pack reservation; original packet retained under RFC assets.

## Objective and owned paths

Request an actual AgentSkills integrator card/revision for manage-agent-skills guidance and chosen metadata/bundles/provenance. It must describe ensure, locks, source-qualified imports and one-request fleet operations through public APIs with truthful partial reports. Do not invent ASK IDs or copy its mutable tracker; bind external_depends_on after the upstream card exists and record its completion revision.

Own only: `docs/development/agent-skills-handoff.md (new)`, `README.md`, `CONTRIBUTING.md`, `.mask/skill-config/implement-rfc/project.md`. Coordinate shared files with the integrator; no unrelated consumer or source publication is implied.

## Acceptance and focused verification

- RFC-MASK-0017-AC03: Actual canonical AgentSkills management guidance and selected metadata/bundle/provenance handoffs are recorded by upstream revision and verified locally without duplicate tracker ownership.

Proposed direct checks (not executed by this packet):

- Verify the actual upstream commit and run a bounded public command workflow from the updated management instructions.

Read the live RFC/card and current source before edits. Use temporary fixture roots/local bare remotes. Claim on the live board, preserve unrelated changes and commit explicit paths. Never bypass collisions or edit internal MASK state as a workaround.

## Run record

Not started. No implementation revision, native result, host-load observation or acceptance is asserted.

## Bounded named-bundle handoff — 2026-10-02

The owner authorized the canonical `agentskills/rfc` slice with MASK-0042.
Actual upstream ASK-0095 owns `mask-source.json`, companion/install guidance and
the disposable public verification. Candidate `a32377166fd02d3b4b35feb2dfb3c178e7b80f7e`
preserves all 16 package discoveries and supplies author-rfc, grill-rfc, grill-me
and implement-rfc. See [handoff](../../development/agent-skills-handoff.md).
Upstream completion revision is `b9e413673b7dc7b618487def3831049451010632`;
MASK `bc4f9f9015ee2bd3495101e91d0077f35ebc1733` verifies the canonical public
installation with healthy required setup, all four skills and all 16 packages.
This card remains Backlog for its broader management/provenance/fleet handoff;
its unrelated prerequisites and RFC-MASK-0017 acceptance remain open.

Install/uninstall/upgrade vocabulary follow-up is owned by actual upstream
ASK-0096 and MASK-0128 under `named-bundles-v3`. Prior candidate acceptance remains
historical; current revision/verification is recorded on completion. Package-version
upgrade policy awaits the owner's choice. Broader MASK-0064 remains Backlog.
