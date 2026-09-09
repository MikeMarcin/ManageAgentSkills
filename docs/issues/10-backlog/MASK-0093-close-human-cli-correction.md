---
schema: "implement-rfc.card.v1"
id: "MASK-0093"
title: "Verify and close the task CLI and human-output correction"
status: "Backlog"
rfcs: ["RFC-MASK-0018"]
depends_on: ["MASK-0091"]
priority: "P1"
metadata: {"packet": "mask-corrective-ux-readiness", "provisional_id": false, "packet_key": "close-human-cli-correction"}
closeout_for: ["RFC-MASK-0018"]
---

# MASK-0093: Verify and close the task CLI and human-output correction

Governing RFC: [RFC-MASK-0018](../../rfcs/RFC-MASK-0018-task-oriented-cli-and-human-output.md). Live IDs confirmed by the committed pack reservation `6d80121`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-ux-readiness.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-ux-readiness/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-ux-readiness/ACCEPTANCE.md).

## Objective and owned paths

This RFC, its closeout, current affected docs and integrated evidence references only.

## Bounded work

Reconcile all RFC-MASK-0018 criteria at their stated public boundaries. Reuse unchanged focused evidence, check current diff and documentation, and confirm no non-JSON command falls back to envelope serialization. This closeout does not certify unfinished workflow-role work.

## Acceptance

Every criterion has direct actual evidence and an implementation revision; every linked required card is Done. Required native human journeys cannot be marked passed from pipes/mocks alone. Preserve honest limitations and the real pre-implementation baseline.

Criterion coverage: RFC-MASK-0018-AC01, RFC-MASK-0018-AC02, RFC-MASK-0018-AC03, RFC-MASK-0018-AC04, RFC-MASK-0018-AC05, RFC-MASK-0018-AC06, RFC-MASK-0018-AC07, RFC-MASK-0018-AC08.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary. Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation, and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Not started. Claim the live remapped card before edits. No code implementation,
native result, host loading, user approval, or quota improvement is asserted.

## Durable closeout anchor

RFC_BASE_SHA: 6d80121b1c870f1be7864e8bc9db2b02a0e41c2d

Planned cards: MASK-0083, MASK-0084, MASK-0085, MASK-0086, MASK-0087, MASK-0091.

| Acceptance | Direct check / observation | Outcome | Implementation revision |
|---|---|---|---|
| RFC-MASK-0018-AC01 | `python3 -B -m unittest tests.test_task_commands tests.test_public_baseline` (macOS, subprocess CLI): `install alpha` from an unregistered project and `install alpha --user` from an unregistered personal scope each declare, register and link in one invocation; v2 install/remove of a third skill retains alpha/beta lock rows, alpha's `codex` override and the other scope; bare name in two approved sources -> `skill.ambiguous` with qualified choices (MASK-0086) | Pass at card boundary; native lanes open | `681e26b` |
| RFC-MASK-0018-AC02 | `python3 -B -m unittest tests.test_human_output tests.test_public_baseline` (macOS): every registered command has a renderer; inventory shows 3 skill rows / 6 links with per-agent states; help/version/empty/paginated/error results are text (MASK-0084); `install`/`remove`/`list` render text (`tests.test_task_commands`), `list` on an undeclared scope gives deliberate empty text (MASK-0086) | Pass at card boundary; native lanes open | `bc579976a289eb65cff1dee7224e36ba3752c8c5`, `681e26b` |
| RFC-MASK-0018-AC03 | Same run: `--json` stays one document for success and handled errors, `--` operand containing `--json` is data, effects identical across formats (MASK-0084); `python3 -B -m unittest tests.test_consent`: JSON consent refusal is one document carrying `data.confirmation`, format never selects or widens authority (MASK-0085) | Pass at card boundary | `bc579976a289eb65cff1dee7224e36ba3752c8c5`, `af82cd80165e7a6b976e5a6715524c4ba24f4c33` |
| RFC-MASK-0018-AC04 | `python3 -B -m unittest tests.test_consent tests.test_ensure` (macOS, POSIX pty): manual `ensure` on an unapproved project asks once in-process, yes completes links in the same invocation with no hash copied and no integration.json; no-op/already-authorized runs do not ask; JSON, DEVNULL/redirected and `--event` paths never prompt (`confirmation.required` / `integration.approval_required`); `--yes` cannot widen events, bypass `target.collision` or grant non-ordinary kinds (seam test) | Pass for the readiness authority; package-script/source/expanded-scope prompts land with MASK-0086/0087/0089 through the same seam; native Windows console prompt open | `af82cd80165e7a6b976e5a6715524c4ba24f4c33` |
| RFC-MASK-0018-AC05 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0018-AC06 | Same run: declaration changed after the prompt -> `plan.stale` exit 4 with nothing applied; no/EOF -> `confirmation.declined` exit 4; SIGINT at the prompt -> 130, no links, no pending.json; writer lock free during the prompt (concurrent `user init` succeeds); collision refusal retained under `--yes` | Pass for consent-related cases; `remove` with an edited leaf -> `target.collision` exit 4, edited file kept, lock row retained; dry run of a fresh scope writes nothing; `install`/`remove` refuse `recovery.required` (exit 8) with a pending journal (MASK-0086). Busy/interrupted-transaction cases of MASK-0087 still open | `af82cd80165e7a6b976e5a6715524c4ba24f4c33`, `681e26b` |
| RFC-MASK-0018-AC07 | Pending actual implementation evidence | Not run | Not recorded |
| RFC-MASK-0018-AC08 | Baseline fixtures do not inject --json (MASK-0083); native macOS/Windows journeys not yet exercised | Not run | Not recorded |

Closeout review runtime: Not recorded. Required native/upstream boundaries remain
open until their actual evidence is linked. Do not invent a PASS to close the board.

## Current continuation (corrective pack)

Milestone M0 (MASK-0083) is Done: import, reconciliation and the public regression baseline exist; see `docs/development/corrective-baseline.md`. Invariants: never inject `--json` in the human helper; never pre-register, approve or render roles for the command under test; the linked-consumer state keeps its old role files.

Milestone M1 (MASK-0084) is Done at `bc579976a289eb65cff1dee7224e36ba3752c8c5`: `mask_present.py` renders every registered command from the same result object; `RENDERERS` is the coverage table (`tests/test_human_output.py` rejects an unregistered command); `mask.py::main` has no JSON fallback; errors go to stderr with code/details/preserved state/remediation (`mask_core.REMEDIATION`). Invariants for later cards: a new command must add a `RENDERERS` entry and a `REMEDIATION` entry for any new user-facing refusal code; keep engine decisions out of the renderer; `mask_install.validate_program` and `tests/test_launcher.py` list runtime modules and must include any new module. Known unrelated failure: `tests.test_user_scope.test_scope_selection_and_parser` (state readable versions) predates this pack.

Milestone M2 (MASK-0085) is Done at `af82cd80165e7a6b976e5a6715524c4ba24f4c33`: `mask_consent.py` is the single consent seam (`request` -> `require`; kinds `readiness`, `source.trust`, `package.setup`, `overwrite`, `ref.rebind`, `scope.expand`; only `readiness` is ORDINARY and grantable by `--yes`). `mask.dispatch_impl` catches `ConsentRequired` outside the writer lock, asks on stderr, stores the hash on `args.consented`, resets the result object and reruns `locked_dispatch`; `granted_by` turns a changed hash into `plan.stale`. Manual `ensure` on an unapproved project now asks (or returns `confirmation.required` with `data.confirmation` when not interactive); events and `--check` keep `integration.approval_required`; an already usable unapproved project is a no-op with `approval: not_approved` (decided: no-op needs no consent, per contract section 3; `tests/test_ensure.py` expectations updated accordingly, and the nested-root case now reports `manifest.missing` because planning precedes the authority question). `ensure` joined GUARDED so `--expect-plan-hash` binds the frozen proposal. Invariants for later cards: new significant authority must go through `consent.request`/`require` with a non-ordinary kind (never a bespoke prompt, never `--yes`-grantable); prompts are stderr-only and require stdin/stdout/stderr ttys plus no `--json`/`--event`; never hold the writer lock while asking; recompute the proposal after consent. Interactive detection uses `isatty` on all three streams, so `mask ensure > file` never prompts. `tests/test_consent.py` uses a POSIX pty (macOS lane); SIGINT is sent directly rather than through a controlling tty. Known limitation: dry-run reports the proposal but `granted_by` is not evaluated for dry runs.

Milestone M3 (MASK-0086) is Done at `681e26b`: `mask_task.py` implements `install`/`remove`/`list`. Invariants for later cards: task commands are hooked in `mask.dispatch_impl` beside `mask_selection.dispatch` (before `locked_dispatch`) and take the writer lock themselves after unlocked resolution/preparation, rechecking `mask_pinned.snapshot`; `list` goes through the observational `local_dispatch` path. A fresh scope gets its declaration (and, on a schema-2 machine, an empty lock) written before planning because `mask_fs.plan`/`restore` require existing control files; those files are unlinked in `finally` unless the transaction committed, and the fresh-scope dry run reports `declaration_created` without computing a plan. `mask_fs.validate_pending` allowlists `install`/`remove` and lets `install` create the first user record (state schema 1 -> 2). v2 adds resolve only the new binding (`resolve_binding`, with one approved-source `sources.fetch` when the cache is missing and neither `--offline` nor `--dry-run`); prior lock rows are copied verbatim, never re-verified or rewritten. Bare IDs prefer a source already bound in the declaration, otherwise probe every approved catalog (fetching when live) and refuse `skill.ambiguous`/`source.unresolved`. `mask_pinned.merge_preparation` now keeps an explicit `data.network` unless a locked fetch occurred. Presenter `warnings()` prints scalar details only (nested shadowing rows stay in JSON). Decided: install/remove ask no confirmation (ordinary scoped authority, contract section 3); new source identity still requires `tap add`, so the `source.trust` kind is not yet produced. Known limitations: legacy `--agent` differing from the declaration's targets is refused (`selection.per_binding_unsupported`) rather than migrated; `remove` on an unregistered scope is refused; a refused v2 task after store materialization is still labelled `partial` by `merge_preparation` (pre-existing semantics, no pending journal exists); README keeps the lower-level recipes until MASK-0091.

Next bounded milestone: MASK-0087 (one-command safe updates) is now dependency-ready in Backlog and must be promoted to Ready by the integrator; MASK-0088 (RFC-MASK-0019 role artifacts) remains Ready and independent; MASK-0089 depends on 0085 and 0088. Open obligations: native Windows lane (ExampleWinHost station) for AC08 including the console confirmation journey and the task commands, real AgentSkills handoff (no ASK ID yet), host-loading observation. MASK-0094 links here rather than duplicating this record.
