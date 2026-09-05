# ManageAgentSkills local issue board

IDs: `MASK-NNNN`. `NEXT_ID` contains the next unused local issue ID, including IDs burned by reservations. Local dependencies are JSON arrays in Markdown frontmatter. `external_depends_on` entries name another repository and are satisfied only by a recorded integrated commit; the local allocator never mutates an external board.

| Folder | Frontmatter status |
|---|---|
| 10-backlog | Backlog |
| 20-ready | Ready |
| 21-ready-win | Ready |
| 22-ready-mac | Ready |
| 23-ready-lin | Ready |
| 30-in-progress | In Progress |
| 40-parked | Parked |
| 50-blocked | Blocked |
| 60-done | Done |

Claim a dependency-ready card by committing its move to the appropriate in-progress lane before editing; leave no unrelated staged files between commits. Platform cards move from backlog to their matching platform-ready lane after prerequisites land. A missing external handoff keeps the card in backlog/blocked even if its local dependencies are done.

Every card has id, title, status, rfc and depends_on. Source slices list owned paths, bounded work, acceptance and focused verification. Closeouts have closeout: true, RFC_BASE_SHA, planned cards, actual result/commit rows and next-slice handoff. Do not mark a card Done for tests not run, including a skipped native platform.

On main: `python scripts/allocate_issue_id.py --count N --reserve-for <lane>` reserves IDs. Commit the counter and receipt before a lane uses them. Lanes may not write NEXT_ID, reservations or tracker READMEs. If the block is exhausted, request a new integrator reservation; never make up IDs. Gaps are allowed and unused reserved IDs are burned.

Only repo-local cards are a mutable tracker. Do not copy the packet's implementation-order file into another live task list. Use the structure gate and preserve unrelated user work. Optional independent review and remote helpers do not add automatic requirements beyond the named acceptance boundary.
