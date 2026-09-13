# Corrective managed-taps live import

Original packet directory: `C:/Users/mikem/AppData/Local/Temp/claude/C--code-git-ManageAgentSkills/d22012d8-e7c8-42ea-8d6b-4a64f0d0d905/scratchpad/mask-corrective-managed-taps` (pack id `mask-corrective-managed-taps`, manifest schema `mask.corrective-pack.manifest.v1`, 24 files plus the manifest). Immutable retained copy: `mask-corrective-managed-taps/` (no editor or bytecode files were present).
Packet source basis: direct inspection of this repository at `d3e417478809e096be9cff155e38c7620d14ee71` and of the owner's `~/.mask` configuration (see retained `SOURCE_BASIS.md`); no source dump was used.
Repository: `C:/code/git/ManageAgentSkills`, branch `main`.
Pre-import commit: `d3e417478809e096be9cff155e38c7620d14ee71` (worktree clean; NEXT_ID `MASK-0098`).
Reservation and immutable pre-implementation baseline (RFC_BASE_SHA for RFC-MASK-0020): `b92372f224c04368b6f76d50c0312d95f8035ff3`.
Reservation receipt: `docs/issues/_reservations/MASK-0098--MASK-0106--0ce3827dec5c.json`.
Import commit: the commit introducing this file (`git log --diff-filter=A --format=%H -- <this path>`).

Source reconciliation at import: every file listed in the packet `SOURCE_BASIS.md` matched its recorded SHA-256 at the pre-import commit (the packet was authored from that commit in the same session). No live work already fixes the described defect: `init` still requires `--source`, machine config v2 still requires the legacy `source` block and `legacy_source`, `mask_fs.plan` still links legacy consumers into the clone, and pinned `update` still resolves from cache only. Packet validation (`tools/validate_pack.py`: 0 violations; `milestone_plan.py discover`/`check`: structurally valid) passed before import; that establishes packet consistency only.

Import starts Proposed. The owner's 2026-09-12 direction was to create and import the pack; implementation and acceptance are recorded under the live workflow when the owner directs `/implement-rfc` at RFC-MASK-0020. Only MASK-0098 starts Ready; every other card enters Ready after its actual dependencies are Done.

## Identity mapping

Packet IDs MASK-0098 to MASK-0106 were provisional. The live allocator returned the same numbers because live NEXT_ID was `MASK-0098`; they are live only through the committed reservation above. Packet RFC-MASK-0020 did not collide with live RFCs (live ended at RFC-MASK-0019), so the RFC ID is unchanged.

| Original | Live | Live destination |
|---|---|---|
| RFC-MASK-0020 | RFC-MASK-0020 | docs/rfcs/RFC-MASK-0020-tap-only-deployment.md |
| MASK-0098 | MASK-0098 | docs/issues/20-ready/MASK-0098-intake-and-legacy-baseline.md |
| MASK-0099 | MASK-0099 | docs/issues/10-backlog/MASK-0099-machine-v3-and-tap-bootstrap.md |
| MASK-0100 | MASK-0100 | docs/issues/10-backlog/MASK-0100-retire-live-checkout-engine.md |
| MASK-0101 | MASK-0101 | docs/issues/10-backlog/MASK-0101-update-fetch-and-isolation.md |
| MASK-0102 | MASK-0102 | docs/issues/10-backlog/MASK-0102-doctor-migration.md |
| MASK-0103 | MASK-0103 | docs/issues/10-backlog/MASK-0103-help-docs-and-capabilities-truth.md |
| MASK-0104 | MASK-0104 | docs/issues/10-backlog/MASK-0104-real-package-qualifier-on-taps.md |
| MASK-0105 | MASK-0105 | docs/issues/10-backlog/MASK-0105-owner-machine-migration-dogfood.md |
| MASK-0106 (closeout RFC-MASK-0020) | MASK-0106 | docs/issues/10-backlog/MASK-0106-close-tap-only-deployment.md |

Live rewrites: `metadata.provisional_id` set to false; a governing-RFC/provenance line added to each card body; `RFC_BASE_SHA` set on the closeout card; the live RFC carries one added provenance sentence. Card dependencies, acceptance identifiers and criterion coverage are unchanged from the packet. The RFC contract references `assets/mask-corrective-managed-taps/contracts/...` resolve unchanged from the live `docs/rfcs/` location.

## Milestone plan

The packet's authored plan `milestone-plan.json` (plan id `tap-only-deployment`, seven milestones) is discoverable from the retained pack through its manifest pointer and root convention. It was not adopted at import: on this Windows integrator `milestone_plan.py adopt --repo-root . --source-root docs/rfcs/assets/mask-corrective-managed-taps --plan milestone-plan.json` (run with `PYTHONUTF8=1`, which the generated-view comparison needs on Windows) fails with `expected safe relative path: 'docs\rfcs\plans\tap-only-deployment\source.json'` because the tool composes the receipt path with the native separator before its own safety check; nothing was written. `discover --source-root` and `check --plan` both report `structural: valid`. The first integrator adopts the plan at intake (on a POSIX host, or after the tool is corrected upstream) with the same command; no ID map is needed because no ID was renumbered.

## External handoff

No AgentSkills change is required for AgentSkills to become a tap. Upstream documentation that names `mask init --source` or the local-clone journey is a recorded documentation handoff on MASK-0103; no `external_depends_on` entry or placeholder ID is recorded and the AgentSkills tracker is not modified by this import.

## Preservation and exclusions

Existing RFCs 0001 to 0019, cards 0001 to 0097, reservations and tracker rules are preserved. `issue-plan.json` remains only inside the retained pack; the live card dependency graph is the scheduling authority. `contracts/machine-v3.schema.json` is a proposal, not a live schema under `schemas/`. No production command, hook installation, publication, credential change or migration of any machine occurred during import.
