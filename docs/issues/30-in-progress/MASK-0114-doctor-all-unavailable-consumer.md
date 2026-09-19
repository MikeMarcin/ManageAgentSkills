---
schema: "implement-rfc.card.v1"
id: "MASK-0114"
title: "Report an unavailable registered consumer instead of failing doctor --all with filesystem.failed"
status: "In Progress"
rfcs: []
depends_on: []
priority: "P1"
metadata: {"origin":"Field report on macOS after pulling 7ccf671 (2026-09-16)"}
---

# MASK-0114: Report an unavailable registered consumer instead of failing doctor --all with filesystem.failed

## Evidence

On macOS (Darwin 25.6.0, Python 3.14.7), at `7ccf671`, a registered project had been deleted: a Claude Code worktree under `BetterPullReview/.claude/worktrees/bpr-dif-integration-rfc-3c2904`.

- `mask doctor --all --check` exited 5 with `filesystem.failed`, "A filesystem operation failed.", and empty `details`, even with `--debug`. It did not name the path or say what to run next.
- Traceback, taken by hooking `MaskError`: `mask.diagnostics` → `mask_fs.plan` → `mask_pinned.observe` (line 247) → `mask_ensure.workspace_observation` (line 408) → `mask_core.identity` → `Path.stat()` raised `FileNotFoundError`.
- The top-level `except OSError` in `mask.py` (around line 716) discards the path and errno.
- `registered_root` already has a `project.unavailable` / `user.unavailable` refusal, but the pinned observation path calls `identity()` before that check runs.
- The workaround was `mask project unregister PATH --keep-links --yes`. After it, doctor ran.
- The deleted worktree's approval record stays in `integration.json`, and nothing reports or removes it.

## Bounded work

- Make `observe` and `workspace_observation` report a missing registered root as `project.unavailable` / `user.unavailable` for that scope, without failing the whole `--all` run.
- In `doctor --all` and `ensure --all --repair`, name the unavailable consumer. Suggest `mask project unregister PATH --keep-links` (or `workspace forget`) as the next step.
- The top-level `OSError` handler keeps `filename`, `filename2` and `errno` in `error.details`, and shows them under `--debug`.
- Decide whether approvals for worktrees that no longer exist should be reported by doctor. Record the decision; this card doesn't have to implement a prune.

## Acceptance

Through the public CLI:
- With one registered project deleted, `doctor --all --check` reports every other scope and names the missing one as unavailable, with a documented exit code.
- `ensure --all --repair` still attempts every other scope and reports the missing one as needing attention, with the unregister suggestion.
- An `OSError` that still reaches the top level includes the path in `error.details`.
- No state, integration or project bytes change during the check.
