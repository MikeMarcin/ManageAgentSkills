# Start here

## What this pack authorizes and does not do

This deliverable records the requested feature design and a bounded execution plan. It contains no live changes. Importing/implementing it must use the user's actual repository, canonical implement-rfc workflow and explicit implementation authority. Device enrollment, host trust, credential provisioning, repository publication and consumer migration are not performed by packet generation.

## Read in order

Read README.md, docs/design/SOURCE-RECONCILIATION.md, docs/design/DECISIONS.md, docs/design/CONTRACTS.md, ROADMAP.md, then RFC-MASK-0006 and its cards. Load the live root/nearest AGENTS.md, current tracker contracts and canonical implement-rfc skill/context. The source dump does not include the linked shared skill bodies; do not fabricate them.

## Import procedure for the main integrator

1. Inspect the actual live Git root, branch, status, RFC table and issue counter/history. Preserve unrelated edits and all settled history. The supplied snapshot's next issue is MASK-0023 and its latest RFC is 0005; neither is a live reservation.
2. Reserve **58** issue IDs using the actual canonical allocator on main: `python -B scripts/allocate_issue_id.py --count 58 --reserve-for mask-readiness-fleet-2026-09-05`. Commit the resulting live counter/receipt before using the allocated IDs. Never copy a packet counter over the live file. Read the allocator result rather than assuming contiguous unused IDs from the snapshot.
3. Allocate/reconcile new RFC IDs against live history. Remap every file, frontmatter reference, dependency, acceptance ID, index row and cross-link. The packet's RFC-MASK-0006–0017 and card IDs are provisional. Import selected files and merge the index rows in integration/rfc-index-rows.md; do not replace existing README instructions with packet navigation.
4. Record the source snapshot digest and original-to-live mapping in a LIVE_IMPORT file using the template. Retain the original ZIP as immutable provenance if desired. Capture actual pre-implementation RFC_BASE_SHA on closeouts before relevant source edits. No SHA or test result in the synthetic examples is live acceptance.
5. Import RFCs as Proposed. When directed to implement the agreed work, record acceptance and promote dependency-ready cards through the live board. Every RFC has one closeout. Optional/stretch cards stay explicitly deferred; do not finish them merely because the core milestones ship.
6. Run the live `python -B scripts/verify_documentation.py --root .` and canonical board queue. Those wrappers require the real deployed shared skill. Packet validation is a separate narrower check.

## First implementation target

Deliver automatic workspace readiness on the current legacy source mode, with one authorized ensure operation and thin owned Git/host adapters. Do not delay it for fleet architecture. Source/pin/selection work follows as a coherent second milestone; preserve the old journal readers and explicit upgrade/migration boundary.

Use [INTEGRATOR-PROMPT.md](INTEGRATOR-PROMPT.md) as a handoff when implementation is authorized. The task graph in packet-index.json and ROADMAP.md is the execution order; a directory listing or RFC numeric order is not a license to run optional work early.

## Completion evidence

Focused checks per slice, one suitable integration pass per milestone, and actual native/host/device observations for claims that need them. Keep missing lanes open. No invented source revisions, passing results, human approvals or station enrollments. Routine deterministic work should not require a human to copy output back to the agent.
