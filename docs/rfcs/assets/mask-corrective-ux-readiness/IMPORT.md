# Import without replacing live history

1. Confirm the actual ManageAgentSkills worktree, main ownership, current source,
   tracker, NEXT_ID, reservations, and any work that already fixes these defects.
   The uploaded snapshot is a reference, not an instruction to revert newer code.
2. Reserve twelve live MASK issue IDs using the repository allocator. Commit the
   counter and reservation through the live integrator's required reservation
   workflow before those IDs are used. Packet MASK-0083–0094 are not reservations.
   Reconcile RFC-MASK-0018/0019 independently against current RFC IDs.
3. Retain this pack under `docs/rfcs/assets/mask-corrective-ux-readiness/` as
   immutable provenance. Copy only the two live RFCs and twelve live cards into
   their proper top-level tracker/lane locations, rewriting IDs, filenames,
   frontmatter, acceptance identifiers, dependencies, and links together.
4. Add current RFC index rows without replacing tracker rules. Record packet to
   live mappings, exclusions, actual imported/source revisions, and real
   RFC_BASE_SHA values in a LIVE_IMPORT record beside the retained pack. Do not
   copy issue-plan.json or IMPLEMENTATION_ORDER.md as another mutable task board.
5. Supporting contracts remain in the retained pack. The RFCs refer to their
   locations as `assets/mask-corrective-ux-readiness/contracts/...`; preserve that
   relationship or remap it explicitly in live copies.
6. Run the repository structure gate and scoped queue. Only the intake card is
   initially Ready. Other cards enter Ready after their actual dependencies are
   Done. There is exactly one closeout card per RFC.

The pack deliberately contains no NEXT_ID replacement, reservation receipt,
claimed implementation revision, PASS acceptance record, live native role files,
user-local credentials, or raw usage archive. No production commands are run by
importing it. The fixture native role files use a fictitious model and must never
be installed into a real host.

The companion AgentSkills handoff has no fabricated ASK issue ID. If execution in
that repository is separately authorized, its integrator allocates its own card
and records the real `external_depends_on` reference and completion commit on
MASK's integration card. Until then, keep the dependency explicit in that card's
body. Do not misuse an invalid placeholder in canonical external_depends_on.

The RFCs are Proposed in this pack. A subsequent direction to implement can be
recorded as acceptance under the live workflow. No terminal status is implied by
pack integrity, source qualification, fixture success, or documentation edits.
