---
schema: "implement-rfc.card.v1"
id: "MASK-0105"
title: "Migrate the owner's real machine and personal scope (attended)"
status: "Parked"
rfcs: ["RFC-MASK-0020"]
depends_on: ["MASK-0102", "MASK-0103", "MASK-0107"]
priority: "P1"
metadata: {"packet":"mask-corrective-managed-taps","provisional_id":false,"packet_key":"owner-machine-migration-dogfood","milestone_plan":{"id":"tap-only-deployment","path":"docs/rfcs/plans/tap-only-deployment/milestone-plan.json"}}
parked_on: "human-review"
acceptance: [{"criterion":"After migration config.json is v3 with the agentskills tap whose authoring is the clone path","outcome":"pending","revision":"8ea0fe5","evidence":{"kind":"observation","detail":"Not run on the owner's machine (attended). Replica rehearsal of the owner's exact state on 8ea0fe5: doctor --migrate exit 0 committed; config v3 with tap agentskills, authoring = the clone, line_endings exact (d7 session scratchpad d7-final/rehearsal/report.json)."}},{"criterion":"doctor --check exits 0","outcome":"pending","revision":"8ea0fe5","evidence":{"kind":"observation","detail":"Replica rehearsal ends at doctor --check exit 7 with only workflow.incomplete: the personal scope lacks implement-rfc context and role setup, and this repository's 16 roles need consented setup after migration. Owner decision MASK-0105-doctor-check prepared in d7-mask-0105-attended.manifest.json."}},{"criterion":"Personal links resolve under MASK_HOME/store/v1/","outcome":"pending","revision":"8ea0fe5","evidence":{"kind":"observation","detail":"Replica rehearsal: install implement-rfc --user links both personal paths under store/v1 (exit 4 workflow.incomplete)."}},{"criterion":"update fetches and no-ops","outcome":"pending","revision":"8ea0fe5","evidence":{"kind":"observation","detail":"Replica rehearsal: update fetch ok, both consumers unchanged (exit 4 workflow.incomplete). The owner's SSH GitHub origin was not exercised."}},{"criterion":"The clone's HEAD, index and worktree are unchanged","outcome":"pending","revision":"8ea0fe5","evidence":{"kind":"observation","detail":"Replica rehearsal: clone HEAD, staged index, index file and status unchanged; the real clone and real checkout link texts unchanged under the guard."}},{"criterion":"The transcript is recorded in docs/development/tap-cutover-baseline.md","outcome":"pending","revision":"8ea0fe5","evidence":{"kind":"freeform","detail":"Awaiting the attended run. Owner decisions needed first: Q6 reviewer route (coordinator), MASK-0105-doctor-check, MASK-0105-migrated-declaration, and go/not-now for MASK-0105-attended-run."}}]
---

# MASK-0105: Migrate the owner's real machine and personal scope (attended)

Governing RFC: [RFC-MASK-0020](../../rfcs/RFC-MASK-0020-tap-only-deployment.md). Live IDs confirmed by the committed pack reservation `b92372f`; original packet retained under RFC assets ([LIVE_IMPORT](../../rfcs/assets/mask-corrective-managed-taps.LIVE_IMPORT.md)). Retained-pack ACCEPTANCE.md: [assets/mask-corrective-managed-taps/ACCEPTANCE.md](../../rfcs/assets/mask-corrective-managed-taps/ACCEPTANCE.md).

## Objective and owned paths

`docs/development/tap-cutover-baseline.md` (evidence section) only. No source changes; any defect found returns to its owning card.

## Bounded work

With the owner present, run `mask doctor`, `mask doctor --migrate --dry-run` and `mask doctor --migrate` on the real v1 machine (`~/.mask`, source root `C:\code\git\AgentSkills`, empty registry), then `mask install implement-rfc --user`, `mask list --user`, `mask update` and `mask doctor --check`. Record the transcript, the resulting `config.json` shape (redacting nothing that is not secret) and the link targets. Do not reset or clean the clone.

## Acceptance

After migration `config.json` is v3 with the `agentskills` tap whose `authoring` is the clone path, `doctor --check` exits 0, personal links resolve under `MASK_HOME/store/v1/`, `update` fetches and no-ops, and the clone's HEAD, index and worktree are unchanged. The transcript is recorded in the baseline document.

Criterion coverage: RFC-MASK-0020-AC04, RFC-MASK-0020-AC07.

## Focused verification

Use the corresponding cases in retained-pack ACCEPTANCE.md through the actual
selected CLI/engine boundary (subprocess argv, exit code, JSON stdout, stderr,
filesystem and Git effects). Preserve original failure evidence; a focused fix
receives a focused rerun. Record exact command, outcome, limitation and source
revision. No repeated unchanged full matrix or proof-of-proof bundle.

## Run record

Not started. Claim the live remapped card before edits. No code implementation,
native result, host loading, user approval or migration of a real machine is
asserted by this card's existence.

## Execution record

Dispatch `d7` of run `mask-rfc0020-2026-09-12-a`, producer `rfc-integrator-d7`, mandate revision `4`. Claimed at `f685595`. **Prepared, not run.** The owner's real machine has not been touched; the attended run needs the owner.

- **Candidate:** ManageAgentSkills `main` at product revision `8ea0fe5`.
  - The global launcher `%LOCALAPPDATA%\Programs\MASK\mask.cmd` runs `C:\code\git\ManageAgentSkills\mask.py`.
  - The checkout must therefore be clean, at `8ea0fe5` or a later commit that changes only records.
- **Live machine** (read-only inspection, schema versions and key names only):
  - `~/.mask/config.json` v1 (`source.root` is the AgentSkills clone; targets claude and codex).
  - `state.json` v1 is not an empty registry. It registers one legacy project, this repository, with 8 links into the clone and 16 `native_roles`. It also holds the `mask.cmd` launcher record.
  - `integration.json` holds one approval for this repository.
  - The clone is clean at `origin/main` `16192b7`.
  - The personal skill roots hold no entries MASK would collide with.
- **Rehearsal on the candidate:**
  - **Setup:** a disposable replica of that exact state. Owner files were copied byte-exact, with paths re-pointed. The guard passed, and the owner's files, the real clone and the real checkout's link texts were unchanged.
  - **The card's sequence:**
    - `doctor` 0;
    - `doctor --migrate --dry-run` 0, writing nothing;
    - `doctor --migrate` 0, committed;
    - `install implement-rfc --user` 4 `workflow.incomplete`;
    - `list --user` 0;
    - `update` 4 `workflow.incomplete`, fetching with no change;
    - `doctor --check` 7.
  - **Migrated state:** config v3 with tap `agentskills` (`authoring` is the clone, `line_endings: exact`). State becomes v3, keeping the launcher record. `integration.json` is unchanged. All consumer and personal links resolve under `store/v1`, and the clone's HEAD, index and status are unchanged.
  - **Evidence:** d7 session scratchpad `d7-final/rehearsal/`. The earlier run at `f9c7fbc` is in `d7-w1b/`.
- **What blocks the acceptance as written:**
  1. **Personal scope:** it has no implement-rfc context, and its 16 roles need consented setup. So `install --user`, `update` and `doctor --check` end 4, 4 and 7.
  2. **This repository's roles:** migration keeps the 16 role files but no longer vouches for them. Their lock's contract digest came from the working copy of `mask-workflow.json` that `core.autocrlf` had converted to CRLF, and the store holds exact bytes. Recovery is a consented setup (`agentskills/implement-rfc:prepare-roles`) through `mask ensure --project C:\code\git\ManageAgentSkills`, which runs package code.
  3. **Dirty checkout:** migration leaves `M .mask.json` (v2) and `?? .mask.lock.json` (4 rows at `16192b7`) in this checkout.
- **Owner decisions needed before the run:**
  - **Q6 (held by the coordinator):** the reviewer route for the unperformed MASK-0107 critical review. The configured `claude-fable-5-1` route hit its usage limit on 5 attempts; d6 judged the review needed before this run.
  - **MASK-0105-doctor-check:** extend the run with consented role setup (for this repository, and optionally the personal scope with personal context), or accept `doctor --check` 7 limited to `workflow.incomplete`. The second option amends this card's acceptance.
  - **MASK-0105-migrated-declaration:** commit the migrated `.mask.json` and `.mask.lock.json` with the transcript, or leave them to the owner.
  - **Go / not now** for the attended run on the candidate.
  - These are prepared as attended-review candidates in `.mask/generated/implement-rfc/runs/mask-rfc0020-2026-09-12-a/d7-mask-0105-attended.manifest.json`.
- **Attended command sequence** (the agent runs it with the owner present; transcript to `docs/development/tap-cutover-baseline.md`):
  - **Capture first:** `~/.mask` file hashes, the clone's HEAD, index hash and status, and the 8 link texts.
  - **Optional:** back up the three `~/.mask` files outside `~/.mask`.
  - **Commands:**
    - `mask doctor --json`
    - `mask doctor --migrate --dry-run --json` (note `plan_hash`)
    - `mask doctor --migrate --json` (`--expect-plan-hash` is available)
    - `mask install implement-rfc --user --json`
    - `mask list --user --json`
    - `mask update --json` (fetches `git@github.com:MikeMarcin/AgentSkills.git` over SSH, which the rehearsal did not exercise)
    - `mask doctor --check --json`
    - any setup steps the doctor-check decision adds
  - **Afterwards:** record the `config.json` shape and link targets, and re-check the clone.
  - **Rollback:** `mask recover --rollback` while the journal is pending.
