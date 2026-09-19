# Cache ownership and unavailable-consumer repair

Field report, 2026-09-19: `mask update` refused `source.cache_invalid` and plain
`mask doctor` failed with `filesystem.failed`. These were separate failures.

The agentskills cache marker named the correct repository and inode, but its recorded
device number was 16777230 and the observed number was 16777231. A remount can change
device numbers; the observation does not prove why it changed. Directory identity
remains enforced. The new guarded `source repair-cache` retains the complete suspect
directory without trusting its Git configuration or objects. Ordinary fetch then
constructs a fresh cache from the approved remote.

Doctor's pinned observation called `stat()` on a deleted registered temporary
worktree before it could report the scope's existing `project.unavailable` blocker.
It now accumulates that typed failure while observing available scopes. All-scope
repair also records the unavailable scope and attempts the others. Unhandled OS
errors include available filenames and errno. Registration and approval records are
never silently pruned because a path is unavailable; explicit public unregister is
the separate cleanup operation.

## Verification

- Five new public regression cases cover project/personal unavailability, per-scope
  repair, retained OS error paths, cache identity refusal, read-only preview, stale
  guards, symlink/unrecognized-directory refusal, retention collisions and fresh fetch.
  The cache fixture also retains a deliberately invalid Git config without using it.
- The focused 45-test run covers the new cases plus source operations, readiness,
  pinned recovery and CLI protocol. Another 24 repair and tap-identity regression
  tests pass, for 69 distinct tests. Final narrow cache rechecks pass.
- The documentation gate and whitespace checks pass. Local self-review reused the
  existing native no-replace directory publication primitive and kept cache effects
  separate from deployment. No subagents or live model qualification were used.

## Reported machine

The guarded repair retained the original cache at
`MASK_HOME/sources/agentskills-8f2833997d1a17d8.git.retained-01c8b274068dfa7f`.
Its ownership marker was not edited. A fresh `source fetch agentskills` succeeded at
AgentSkills `f36b645c8c00e8b88225e51d446105ca912090ac`.

After doctor reported the exact absent temporary worktree, a reviewed
`project unregister PATH --keep-links --expect-plan-hash HASH` removed only its stale
registration. Approval records were retained. `mask doctor --check` then reported
healthy across the available scopes. `mask update --json` succeeded and fetched the
tap; the program checkout was held because this repair was still being authored.
No installed skills, global settings or authentication changed. Nothing was pushed.
