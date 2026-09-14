# Corrective managed-taps live import

Original packet directory: `C:/Users/mikem/AppData/Local/Temp/claude/C--code-git-ManageAgentSkills/d22012d8-e7c8-42ea-8d6b-4a64f0d0d905/scratchpad/mask-corrective-managed-taps` (pack id `mask-corrective-managed-taps`, manifest schema `mask.corrective-pack.manifest.v1`, 24 files plus the manifest). Immutable retained copy: `mask-corrective-managed-taps/` (no editor or bytecode files were present).
Packet source basis: direct inspection of this repository at `d3e417478809e096be9cff155e38c7620d14ee71` and of the owner's `~/.mask` configuration (see retained `SOURCE_BASIS.md`); no source dump was used.
Repository: `C:/code/git/ManageAgentSkills`, branch `main`.
Pre-import commit: `d3e417478809e096be9cff155e38c7620d14ee71` (worktree clean; NEXT_ID `MASK-0098`).
Original reservation and pre-implementation baseline before rebase: `b92372f224c04368b6f76d50c0312d95f8035ff3`. Rebased pre-implementation baseline: `f81155aafc89196a192551a6baf77d168b8bacc6`.
Live reservation receipt: `docs/issues/_reservations/MASK-0100--MASK-0108--0ce3827dec5c.json`.
Import commit: the commit introducing this file (`git log --diff-filter=A --format=%H -- <this path>`).

Source reconciliation at import: every file listed in the packet `SOURCE_BASIS.md` matched its recorded SHA-256 at the pre-import commit (the packet was authored from that commit in the same session). No live work already fixes the described defect: `init` still requires `--source`, machine config v2 still requires the legacy `source` block and `legacy_source`, `mask_fs.plan` still links legacy consumers into the clone, and pinned `update` still resolves from cache only. Packet validation (`tools/validate_pack.py`: 0 violations; `milestone_plan.py discover`/`check`: structurally valid) passed before import; that establishes packet consistency only.

Import starts Proposed. The owner's 2026-09-12 direction was to create and import the pack; the later `/implement-rfc RFC-MASK-0020` direction targeted this tap pack before its rebase renumbering. Only the intake card starts Ready; every other card enters Ready after its actual dependencies are Done.

## Identity mapping

The retained packet keeps its original IDs. During rebase onto the latest main, the upstream personal-readiness work occupied RFC-MASK-0020 and MASK-0098/0099. The tap-only live RFC is RFC-MASK-0021 and its thirteen cards are MASK-0100 through MASK-0112. The original import and reservation commits remain historical evidence on `backup/pre-rebase-mask-20260914`; current live references and reservation receipts use the rebased IDs.

| Original | Live | Live destination |
|---|---|---|
| RFC-MASK-0020 | RFC-MASK-0021 | docs/rfcs/RFC-MASK-0021-tap-only-deployment.md |
| MASK-0098 | MASK-0100 | docs/issues/60-done/MASK-0100-intake-and-legacy-baseline.md |
| MASK-0099 | MASK-0101 | docs/issues/60-done/MASK-0101-machine-v3-and-tap-bootstrap.md |
| MASK-0100 | MASK-0102 | docs/issues/60-done/MASK-0102-retire-live-checkout-engine.md |
| MASK-0101 | MASK-0103 | docs/issues/60-done/MASK-0103-update-fetch-and-isolation.md |
| MASK-0102 | MASK-0104 | docs/issues/60-done/MASK-0104-doctor-migration.md |
| MASK-0103 | MASK-0105 | docs/issues/60-done/MASK-0105-help-docs-and-capabilities-truth.md |
| MASK-0104 | MASK-0106 | docs/issues/40-parked/MASK-0106-real-package-qualifier-on-taps.md |
| MASK-0105 | MASK-0107 | docs/issues/40-parked/MASK-0107-owner-machine-migration-dogfood.md |
| MASK-0106 | MASK-0108 | docs/issues/10-backlog/MASK-0108-close-tap-only-deployment.md |

The four owner-decision follow-ups originally MASK-0107 through MASK-0110 are live MASK-0109 through MASK-0112. Their retained reservation receipt is `docs/issues/_reservations/MASK-0109--MASK-0112--7dd347ff91b0.json`. The packet reservation receipt is `docs/issues/_reservations/MASK-0100--MASK-0108--0ce3827dec5c.json`. The current rebase baseline is `f81155aafc89196a192551a6baf77d168b8bacc6`; `b92372f224c04368b6f76d50c0312d95f8035ff3` is the original historical baseline.

Live rewrites preserve the packet criteria and dependencies while remapping identifiers. `metadata.provisional_id` remains false, and the adopted plan maps the retained source IDs to the live IDs. The retained packet bytes are unchanged.

## Milestone plan

The packet's authored plan `milestone-plan.json` (plan id `tap-only-deployment`, seven milestones) is discoverable from the retained pack through its manifest pointer and root convention. It was not adopted at import: on this Windows integrator `milestone_plan.py adopt --repo-root . --source-root docs/rfcs/assets/mask-corrective-managed-taps --plan milestone-plan.json` (run with `PYTHONUTF8=1`, which the generated-view comparison needs on Windows) fails with `expected safe relative path: 'docs\rfcs\plans\tap-only-deployment\source.json'` because the tool composes the receipt path with the native separator before its own safety check; nothing was written. `discover --source-root` and `check --plan` both report `structural: valid`. The first integrator adopts the plan at intake (on a POSIX host, or after the tool is corrected upstream) with the same command; no ID map is needed because no ID was renumbered.

**Adopted at intake (September 12, 2026, run `mask-rfc0020-2026-09-12-a`).** The published text above is retained unchanged. The same command, `milestone_plan.py adopt --repo-root <root> --source-root docs/rfcs/assets/mask-corrective-managed-taps --plan milestone-plan.json`, ran with the unmodified installed tool under WSL Ubuntu `python3` 3.13.15 (a POSIX host) against this checkout with `PYTHONUTF8=1`. It wrote `docs/rfcs/plans/tap-only-deployment/milestone-plan.json` (normalized JSON of the authored plan; grouping, order and exit text unchanged), the receipt `plans/tap-only-deployment/source.json` (`source_sha256` `635e6554…6664`, the retained file's SHA-256; empty mapping), and a `metadata.milestone_plan` link on RFC-MASK-0020 and MASK-0098 to MASK-0106. The retained pack bytes were not modified.

After rebase, the live plan and its source receipt contain the ID mapping in the table above. The live closeout outcome sentence also names RFC-MASK-0021; that prose identity edit is the only difference beyond the plan helper's field-level ID remapping. The preceding adoption paragraphs describe the original run; their empty-mapping and original-ID statements are historical. The retained authored plan and its source hash are unchanged.

The coordinator's Windows `discover --source-root` report `stale: generated MILESTONES.md has drifted` was an encoding artefact, not authored drift. Without `PYTHONUTF8=1`, Windows Python reads the retained view's non-ASCII separator in the ANSI code page. With UTF-8 the same discovery and `check --plan milestone-plan.json` report `found`/`structural: valid`. No generated `MILESTONES.md` is kept beside the live plan; the retained pack copy is the rendered view. As a result, Windows target-only discovery (`discover --target RFC-MASK-0020`) reports `found` from `live` without that setting. The Windows separator defect in `adopt`'s receipt path is an upstream AgentSkills tool defect. It is recorded here only; that repository was not edited.

## External handoff

No AgentSkills change is required for AgentSkills to become a tap. Upstream documentation that names `mask init --source` or the local-clone journey is a recorded documentation handoff on live MASK-0105 (original MASK-0103); no `external_depends_on` entry or placeholder ID is recorded and the AgentSkills tracker is not modified by this import.

## Preservation and exclusions

Existing RFCs 0001 to 0019, cards 0001 to 0097, reservations and tracker rules are preserved. `issue-plan.json` remains only inside the retained pack; the live card dependency graph is the scheduling authority. `contracts/machine-v3.schema.json` is a proposal, not a live schema under `schemas/`. No production command, hook installation, publication, credential change or migration of any machine occurred during import.
