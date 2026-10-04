---
schema: "implement-rfc.card.v1"
id: "MASK-0129"
title: "Let mask update show and ask about a program schema change instead of failing opaquely"
status: "Done"
rfcs: []
depends_on: []
priority: "P1"
metadata: {"origin":"Field report on bpr-linux (WSL) running mask update from 4b983e3 toward 40080e0 (2026-10-03)"}
acceptance: [{"criterion":"MASK-0129-AC1","outcome":"pass","revision":"9bd51cba4bff536966437429fc28d6296414ff76","evidence":{"kind":"command","detail":"tests.test_launcher test_program_update_separate_and_comment_only_schema_change_needs_no_question: title/description-only schema edit updates with exit 0, HEAD at candidate, stdout row 'machine-v3.schema.json comment wording only'"}},{"criterion":"MASK-0129-AC2","outcome":"pass","revision":"9bd51cba4bff536966437429fc28d6296414ff76","evidence":{"kind":"command","detail":"test_terminal_update_asks_once_and_applies_or_declines (POSIX pty, Linux): n and bare Enter decline with exit 4, Git unmoved, tap fetched; y applies in the same invocation with exactly one [y/N]. test_breaking_schema_and_protocol_changes_are_marked covers removed property, new required property and protocol bump as breaking. Native Windows console not exercised."}},{"criterion":"MASK-0129-AC3","outcome":"pass","revision":"9bd51cba4bff536966437429fc28d6296414ff76","evidence":{"kind":"command","detail":"test_additive_schema_change_is_shown_and_approved_exactly: --json exit 4 confirmation.required with data.confirmation.kind program.migration and classified rows, taps fetched; wrong --approve-plan -> plan.stale; right hash -> updated. program.migration is SIGNIFICANT, not ORDINARY."}},{"criterion":"MASK-0129-AC4","outcome":"pass","revision":"9bd51cba4bff536966437429fc28d6296414ff76","evidence":{"kind":"observation","detail":"mask_install.program_migration on the real ManageAgentSkills repo 4b983e3..40080e0: project-v2.schema.json additive 'adds optional bundle_state'; source-index.schema.json comment 'wording only'; protocol 2->2; 15 commits"}},{"criterion":"MASK-0129-AC5","outcome":"pass","revision":"9bd51cba4bff536966437429fc28d6296414ff76","evidence":{"kind":"command","detail":"test_approved_migration_recovers_without_asking_again: crash at git checkpoint after --approve-plan; pending git.consent recorded; tampered consent -> plan.stale; restored journal -> recover --complete reaches candidate and clears pending.json"}},{"criterion":"MASK-0129-AC6","outcome":"pass","revision":"9bd51cba4bff536966437429fc28d6296414ff76","evidence":{"kind":"command","detail":"assert_readable in launcher tests: no ESC/mark bytes and <=80 columns for redirected refusal, breaking refusal and success text; pty run with NO_COLOR has no ESC; colored pty shows ESC[32m on class words. mask update --help and docs/guides/sources-and-updates.md#program-update describe the review."}}]
---

# MASK-0129: Let mask update show and ask about a program schema change instead of failing opaquely

## Evidence

On a clean checkout 15 commits behind `origin/main`, `mask update` printed:

```
error: Program protocol or schema migration requires explicit review.
  code: source.candidate_invalid
  fetch: fetched
  state: no deployment changes were applied
  next: Inspect the reported inputs and retry only after resolving the condition.
```

The owner read this as "MASK is broken". The message has these problems:

- It doesn't say what changed. `validate_program` (`mask_install.py`) refuses when `PROTOCOL_VERSION` changes or when any `schemas/*.schema.json` file differs at all from the working tree. It reports neither which one fired nor which files.
- "Reported inputs" refers to nothing; no inputs were reported.
- It gives no way to approve. The only route was to know that `git -C ~/ManageAgentSkills pull --ff-only` is the approval, which bypasses MASK's own update journal.
- `source.candidate_invalid` suggests the remote is corrupt. Here the change was a routine, additive one:
  - `project-v2.schema.json` gained an optional `bundle_state` property. It isn't in `required`, so existing files stay valid.
  - `source-index.schema.json` changed only its `$comment`.

The same check runs from `mask_git.recover_git`, so an interrupted update hits the same dead end.

## Bounded work

Turn the refusal into a consent proposal through the existing in-process consent flow (`mask_consent`, RFC-MASK-0018 AC04). Don't add a parallel prompt.

1. **Classify the change.** Compare the candidate commit's `PROTOCOL_VERSION` and `schemas/` tree with the current revision. Produce one row per changed schema file, in one of these classes:
   - `comment`: only `$comment`, `description`, `title` or `examples` differ.
   - `additive`: new optional properties, or new `$defs` that nothing required references.
   - `breaking`: a property or `$defs` removed, a `required` entry added, a type, pattern or enum narrowed, a bound tightened, or an unparsable schema. Anything the classifier can't prove additive is `breaking`.

   Show a protocol bump separately; it is always `breaking`. Compare against the checked-out revision's tree, not working-tree bytes. Keep the existing LF/CRLF normalization.
2. **Add a consent kind.** Name it `program.migration`. Its plan hash binds the before commit, the candidate commit, the protocol pair and each changed schema's before and after blob ids. `--yes` doesn't grant it. The interactive prompt and `--expect-plan-hash HASH` do. Add it to `SIGNIFICANT`, not `ORDINARY`.
3. **Ask on a terminal.** A manual `mask update` on a TTY shows the review block below and asks one default-no question. Yes continues into the existing journalled fast-forward in the same invocation. No or EOF gives `confirmation.declined`, and Git doesn't move. Taps are fetched either way, and the output says so.
4. **Refuse readably elsewhere.** `--json`, events and redirected streams refuse with `confirmation.required`. The JSON includes `data.confirmation` and the classified `data.program_migration` rows. The text form repeats the review block and names both ways forward.
5. **Handle recovery.** Record the granted plan hash in `pending.json`. `recover_git` then completes an already-consented candidate without asking again. A candidate that changed since consent gives `plan.stale`.
6. **Update help and docs.** `mask update --help` mentions the review and `--expect-plan-hash`. The CLI contract gives the `program.migration` kind.

Out of scope: auto-migrating user state files, and changing what counts as a fast-forward.

## Output: make it beautiful

Use the existing presentation helpers (`mask_present.paint`, tones `review`/`error`/`success`, `NO_COLOR`/`TERM=dumb`/non-TTY fallbacks). Follow these rules: one idea per line; aligned columns; abbreviated commits with an arrow; `~`-relative paths; plain words for each class; no internal codes in the prose, only on the `code:` line. Keep the output within 80 columns.

Target interactive output (cyan headline from the `review` tone; class words in green for comment and additive, yellow for breaking):

```
MASK  4b983e3 → 40080e0  (15 commits)

  This update changes the files MASK uses to describe your setup.

  Protocol   v2, unchanged
  Schemas    2 changed
    project-v2.schema.json     additive   adds optional bundle_state
    source-index.schema.json   comment    wording only

  Your existing projects and taps stay valid with this version.
  What's new: git -C ~/ManageAgentSkills log --oneline 4b983e3..40080e0

  Taps were fetched.

Update MASK to 40080e0? [y/N]
```

After yes:

```
MASK updated  4b983e3 → 40080e0
  tap agentskills: fetched new commits
  Next: mask upgrade --dry-run
```

For a breaking change, the summary line becomes `Some existing files may no longer validate with this version.` and the question stays default-no.

Target non-interactive refusal on stderr:

```
error: MASK update needs your approval: it changes 2 schemas.
  code: confirmation.required
  from: 4b983e3 → 40080e0 (15 commits)
  schemas:
    project-v2.schema.json     additive   adds optional bundle_state
    source-index.schema.json   comment    wording only
  state: MASK not moved; taps were fetched
  next: run mask update on a terminal to review and confirm, or
        mask update --expect-plan-hash 3e9a5c1f…  to approve this exact change
```

## Owner decision (2026-10-03)

A candidate whose only schema changes are `comment` (no protocol bump) updates without asking. Its rows still appear in the success output under `Schemas`. The owner accepted this because comment wording isn't a contract change, and asking about it trains people to press `y` without reading.

## Acceptance

- **MASK-0129-AC1:** With a fixture bare remote, a comment-only candidate updates without a prompt and lists its rows in the success output.
- **MASK-0129-AC2:** For each class that asks (additive, breaking, protocol bump), using fixture bare remotes:
  - a manual TTY `mask update` shows the classified block and asks once;
  - yes fast-forwards in the same invocation;
  - no or EOF leaves Git unmoved, gives `confirmation.declined`, and still fetches taps.
- **MASK-0129-AC3:** `--json` and redirected runs never prompt. They return `confirmation.required` with `data.confirmation` and `data.program.program_migration`. `--approve-plan` with that hash completes the update. A hash from a different candidate gives `plan.stale`. `--yes` never grants `program.migration`.
- **MASK-0129-AC4:** The 4b983e3 -> 40080e0 change classifies as one `additive` row and one `comment` row.
- **MASK-0129-AC5:** An interrupted, consented update recovers through `recover_git` without asking again. A journal whose consent doesn't match gives `plan.stale`.
- **MASK-0129-AC6:** The text output matches the target layout, both with and without color. `NO_COLOR` and redirected output give no escape codes, and every line fits in 80 columns. `mask update --help` and the update guide describe the review.

## Run record

Implemented at `9bd51cb` (direct strategy, one session, on bpr-linux / WSL2 Linux).

Differences from the card as filed:
- The public flag is `--approve-plan HASH`, MASK's existing spelling for an exact approval. It maps to the engine's `expect_plan_hash`. `update` has no `--yes`. `program.migration` is in `SIGNIFICANT` and not `ORDINARY`, so `--yes` couldn't grant it anyway.
- Arrows are ASCII `->`, matching the rest of MASK's output, because every existing renderer is ASCII-only.
- Added: the background refresh inside `install`/`upgrade` never asks. It warns `update.review_required` and continues with the fetched taps.
- Added: a mismatched `--approve-plan` hash gives `plan.stale` instead of a second refusal.
- `validate_program` is replaced by `protocol_version` (the module and protocol readability check) and `program_migration` (the classifier). The design doc is updated to match.

Verification:
- Ran `python3 -B -m unittest tests.test_launcher tests.test_human_output tests.test_consent tests.test_update tests.test_cli_protocol`: 60 tests OK.
- Ran the full `scripts/run_tests.py`: 541 tests. 4 classes fail (`RecoveryEntrypoint`, `ReadmeText`, `RefreshV2`, `Readiness Launch`). They fail with the same 7 tests on an unmodified worktree at HEAD, so they predate this work and are unrelated to it.
- `scripts/verify_documentation.py` reports 0 violations.
- Native Windows console prompt: not exercised.
