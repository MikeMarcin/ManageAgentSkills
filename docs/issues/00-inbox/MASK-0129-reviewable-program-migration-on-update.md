---
schema: "implement-rfc.card.v1"
id: "MASK-0129"
title: "Let mask update show and ask about a program schema change instead of failing opaquely"
status: "Inbox"
rfcs: []
depends_on: []
priority: "P1"
metadata: {"origin":"Field report on bpr-linux (WSL) running mask update from 4b983e3 toward 40080e0 (2026-10-03)"}
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

## Decision for the owner

Should a candidate whose only schema changes are `comment` (no protocol bump) update without asking? It would still print its rows in the success output. Recommendation: yes. Comment wording isn't a contract change, and asking about it trains people to press `y` without reading.

## Acceptance

- Using fixture bare remotes, for each class (comment, additive, breaking, protocol bump):
  - a manual TTY `mask update` shows the classified block and asks once;
  - yes fast-forwards in the same invocation;
  - no or EOF leaves Git unmoved, gives `confirmation.declined`, and still fetches taps.
- `--json` and redirected runs never prompt. They return `confirmation.required` with `data.confirmation` and `data.program_migration`. `--expect-plan-hash` with that hash completes the update. A hash from a different candidate gives `plan.stale`. `--yes` alone refuses.
- The 4b983e3 → 40080e0 change classifies as one `additive` row and one `comment` row.
- An interrupted, consented update recovers through `recover_git` without asking again.
- The text output matches the target layout, both with and without color. `NO_COLOR` gives no escape codes, and every line fits in 80 columns.
- `mask update --help` and the CLI contract describe the review.
