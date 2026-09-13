# Import without replacing live history

1. Confirm the actual ManageAgentSkills worktree, main ownership, current source,
   tracker, NEXT_ID, reservations and any work that already fixes this defect.
   The baseline in SOURCE_BASIS.md is a reference, not an instruction to revert
   newer code.
2. Reserve nine live MASK issue IDs using the repository allocator
   (`python scripts/allocate_issue_id.py --count 9 --reserve-for
   mask-corrective-managed-taps`). Commit the counter and reservation before those
   IDs are used. Packet MASK-0098 to MASK-0106 are not reservations. Reconcile
   RFC-MASK-0020 independently against current RFC IDs.
3. Retain this pack under `docs/rfcs/assets/mask-corrective-managed-taps/` as
   immutable provenance. Copy only the live RFC and nine live cards into their
   top-level tracker and lane locations, rewriting IDs, filenames, front matter,
   acceptance identifiers, dependencies and links together.
4. Add the current RFC index row without replacing tracker rules. Record packet to
   live mappings, exclusions, actual pre-import revision and the real RFC_BASE_SHA
   in a LIVE_IMPORT record beside the retained pack. Do not copy issue-plan.json
   as another mutable task board.
5. Supporting contracts remain in the retained pack. The RFC refers to them as
   `assets/mask-corrective-managed-taps/contracts/...`; preserve that relationship
   from the live `docs/rfcs/` location.
6. Adopt the authored milestone plan under `docs/rfcs/plans/` with the installed
   `milestone_plan.py adopt --source-root <pack> --id-map <map>` when IDs were
   remapped, or record in the LIVE_IMPORT that the plan is discoverable from the
   retained pack's manifest pointer and will be adopted at intake.
7. Run the repository structure gate and scoped queue. Only the intake card is
   initially Ready. Other cards enter Ready after their actual dependencies are
   Done. There is exactly one closeout card.

The pack deliberately contains no NEXT_ID replacement, reservation receipt,
claimed implementation revision, PASS acceptance record, real machine
configuration, credentials or transcript of a real migration. No production
command is run by importing it, and no machine is migrated by importing it.

The RFC is Proposed in this pack. A subsequent direction to implement can be
recorded as acceptance under the live workflow. No terminal status is implied by
pack integrity, fixture success or documentation edits.
