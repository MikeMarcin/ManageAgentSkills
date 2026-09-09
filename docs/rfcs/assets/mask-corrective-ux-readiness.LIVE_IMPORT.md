# Corrective UX and readiness live import

Original packet directory: `/Users/example/Downloads/MASK-Corrective-UX-and-Readiness-RFC-Pack` (pack id `mask-corrective-ux-readiness`, manifest schema `mask.corrective-pack.manifest.v1`, 68 files). Immutable retained copy: `mask-corrective-ux-readiness/` (editor/bytecode files excluded; none were present).
Packet source basis: MASK source dump `b88187f3445c572fbfac80b436f0370838e1e650060c70dbd379f89033060dd1`, AgentSkills source dump `092b1d58ad6c68d04b763526a45b75db543a2a6e49553099beafad551385aa4f` (see retained `SOURCE_BASIS.md`).
Repository: `/Users/example/Documents/GitHub/ManageAgentSkills`, branch `main`.
Pre-import commit: `49e3971e96e370b77cd2add66c8fc67fae80b6c8` (worktree clean; NEXT_ID `MASK-0083`).
Reservation and immutable pre-implementation baseline (RFC_BASE_SHA for both RFCs): `6d80121b1c870f1be7864e8bc9db2b02a0e41c2d`.
Reservation receipt: `docs/issues/_reservations/MASK-0083--MASK-0094--b44c57dc377d.json`.
Import commit: the commit introducing this file (`git log --diff-filter=A --format=%H -- <this path>`).

Source reconciliation at import: every MASK file listed in the packet `source-basis.json` (`mask.py`, `mask_ensure.py`, `mask_fs.py`, `mask_pinned.py`, `mask_report.py`, `mask_packages.py`, `mask_adapters.py`, `mask_process.py`, `tests/support.py`, `tests/test_cli_protocol.py`, `tests/test_inventory.py`, `tests/test_ensure.py`, `docs/architecture/cli-contract.md`, `docs/architecture/test-boundaries.md`, `docs/rfcs/README.md`, `docs/issues/NEXT_ID`, `AGENTS.md`, `.mask/skill-config/implement-rfc/project.md`) matched the packet SHA-256 at the pre-import commit. No live work already fixes the described defects: non-JSON success still serializes the result envelope, `tests/support.py::Fixture.call` still appends `--json`, and `ensure` still plans only declared skill links. Packet validation (`tools/validate_pack.py`, `tools/test_pack.py`: 11 tests) passed before import; that establishes packet consistency only.

Import starts Proposed. The user's 2026-09-09 mandate ("import and implement") authorizes implementation; acceptance is recorded under the live workflow in the commit following import. Only MASK-0083 starts Ready; every other card enters Ready after its actual dependencies are Done.

## Identity mapping

Packet IDs MASK-0083–0094 were provisional. The live allocator returned the same numbers because live NEXT_ID was `MASK-0083`; they are live only through the committed reservation above. Packet RFC-MASK-0018/0019 did not collide with live RFCs (live ended at RFC-MASK-0017), so RFC IDs are unchanged.

| Original | Live | Live destination |
|---|---|---|
| RFC-MASK-0018 | RFC-MASK-0018 | docs/rfcs/RFC-MASK-0018-task-oriented-cli-and-human-output.md |
| RFC-MASK-0019 | RFC-MASK-0019 | docs/rfcs/RFC-MASK-0019-complete-workflow-readiness.md |
| MASK-0083 | MASK-0083 | docs/issues/20-ready/MASK-0083-import-and-public-regression-baseline.md |
| MASK-0084 | MASK-0084 | docs/issues/10-backlog/MASK-0084-human-output-for-all-commands.md |
| MASK-0085 | MASK-0085 | docs/issues/10-backlog/MASK-0085-in-process-consent-and-authority.md |
| MASK-0086 | MASK-0086 | docs/issues/10-backlog/MASK-0086-complete-install-remove-list.md |
| MASK-0087 | MASK-0087 | docs/issues/10-backlog/MASK-0087-one-command-safe-updates.md |
| MASK-0088 | MASK-0088 | docs/issues/10-backlog/MASK-0088-declarative-native-role-artifacts.md |
| MASK-0089 | MASK-0089 | docs/issues/10-backlog/MASK-0089-approved-staged-setup.md |
| MASK-0090 | MASK-0090 | docs/issues/10-backlog/MASK-0090-ensure-launch-and-upstream-handoff.md |
| MASK-0091 | MASK-0091 | docs/issues/10-backlog/MASK-0091-native-human-journeys-and-readme.md |
| MASK-0092 | MASK-0092 | docs/issues/10-backlog/MASK-0092-real-workflow-native-journeys.md |
| MASK-0093 (closeout RFC-MASK-0018) | MASK-0093 | docs/issues/10-backlog/MASK-0093-close-human-cli-correction.md |
| MASK-0094 (closeout RFC-MASK-0019) | MASK-0094 | docs/issues/10-backlog/MASK-0094-close-workflow-readiness-correction.md |

Live rewrites: `metadata.provisional_id` set to false; a governing-RFC/provenance line added to each card body; `RFC_BASE_SHA` set on both closeout cards. Card dependencies, acceptance identifiers and criterion coverage are unchanged from the packet. The RFC contract references `assets/mask-corrective-ux-readiness/contracts/...` resolve unchanged from the live `docs/rfcs/` location.

## External handoff

`integration/AGENTSKILLS_HANDOFF.md` (retained) specifies the upstream AgentSkills responsibilities consumed by MASK-0090/MASK-0092. No AgentSkills card exists yet; no `external_depends_on` entry or placeholder ID is recorded. MASK-0090 stays open until the actual upstream card and integration commit exist. The AgentSkills tracker is not modified by this import.

## Preservation and exclusions

Existing RFCs 0001–0017, cards 0001–0082, reservations and tracker rules are preserved. `issue-plan.json` and `IMPLEMENTATION_ORDER.md` remain only inside the retained pack; the live card dependency graph is the scheduling authority. `examples/README.target.md`, `examples/human/*.txt` and `fixtures/**` are design fixtures, not shipped behavior; the fixture native role files use model `fixture-model-do-not-run` and are never installed into a real host. No production command, hook installation, publication, credential change or consumer migration occurred during import.
