# ManageAgentSkills local issue board

IDs are MASK-NNNN. NEXT_ID is the next unused ID, including burned reservations.
Use the [canonical board contract](../../.agents/skills/implement-rfc/references/bookkeeping.md)
for card schema, commands, acceptance records and guarded commits.

| Folder | Status |
|---|---|
| 00-inbox | Inbox |
| 10-backlog | Backlog |
| 20-ready | Ready |
| 30-in-progress | In Progress |
| 40-parked | Parked |
| 50-blocked | Blocked |
| 60-done | Done |

Cards require schema, id, title, status, rfcs and depends_on. Relationships are
arrays; independent work uses []. Platform eligibility belongs in platforms;
Ready means local dependencies are Done. Parked human-review cards are queryable
with `queue --human-waiting`. Other waits and blockers remain explicit.

Every RFC has exactly one closeout_for card with its immutable RFC_BASE_SHA,
planned cards and actual criterion/evidence/outcome/revision records. The RFC
owns its status; unresolved required human acceptance keeps it open.

On main, `python scripts/allocate_issue_id.py --count N --reserve-for TOKEN`
reserves IDs. Commit the returned counter and receipt before use; lane workers
do not allocate. Claim dependency-ready work before source edits, preserve
unrelated changes and commit explicit paths. Never recycle reservations.

Ordinary slices use focused checks. Pack/milestone integration normally has one
integration-focused pass, with full relevant suites or critical review where
warranted. No automatic exhaustive matrix, hermetic replay or manual checkpoints.
Retained RFC packets under assets are immutable provenance, not live tracker state.
