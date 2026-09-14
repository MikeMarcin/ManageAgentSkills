# ManageAgentSkills RFC tracker

Live RFCs are top-level `RFC-MASK-NNNN-*.md` files. Retained packets under `assets/` are provenance, never a second live RFC/card index. Status vocabulary: Proposed, Accepted, Implementing, Implemented, Auto-Verified, Rejected, Superseded.

The prepublication privacy rewrite changed historical commit IDs and redacted some retained packet bytes. Older revision references and packet checksums record the original work; they are not integrity checks for the redacted history. Use current source and verification commands for current bytes.

Only the main integrator imports, renumbers, edits tracker rules and confirms terminal status after integration. Each RFC has exactly one linked closeout card whose `closeout_for` includes the RFC. Store actual RFC_BASE_SHA before source implementation and record direct acceptance result/commit rows. Live board linkage selects work, not an arbitrary directory listing.

| RFC | Status | Title |
|---|---|---|
| RFC-MASK-0001 | Auto-Verified | Agent-friendly CLI and declarative project state |
| RFC-MASK-0002 | Auto-Verified | Ownership-safe planning, symlink deployment and recovery |
| RFC-MASK-0003 | Auto-Verified | Explicit source updates, portable launchers and program updates |
| RFC-MASK-0004 | Auto-Verified | Bootstrap cutover, native dogfood and bounded v1 closeout |

| RFC-MASK-0005 | Auto-Verified | User-level skill management |

## Import and verification

Reconcile live IDs before adopting packet IDs. Keep original packet IDs in provenance and record a LIVE_IMPORT mapping including external handoffs. Never rewind counters or recycle reservations. Run `python scripts/verify_documentation.py --root .` after import/integration and before terminal status. When working a lane, status changes are proposals until the integrator revalidates them on main.

## Readiness and fleet extension pack

| RFC | Status | Title |
|---|---|---|
| RFC-MASK-0006 | Auto-Verified | Automatic workspace readiness for clone, worktree, branch and agent startup |
| RFC-MASK-0007 | Auto-Verified | Multiple sources, taps, curated imports and upstream provenance |
| RFC-MASK-0008 | Implementing | True version pinning, immutable deployment artifacts and recoverable migration |
| RFC-MASK-0009 | Implementing | Per-skill scope-specific agent targeting and advertised compatibility |
| RFC-MASK-0010 | Accepted | Portable personal selections, reusable bundles and profile composition |
| RFC-MASK-0011 | Implementing | Where-used inventory, update diffs and deployment impact reports |
| RFC-MASK-0012 | Accepted | Explicit fleet enrollment, device identity and bounded remote transport |
| RFC-MASK-0013 | Accepted | Declarative fleet rollouts, optional continuous convergence and completion reports |
| RFC-MASK-0014 | Proposed | Optional MCP facade over the MASK management API |
| RFC-MASK-0015 | Proposed | Credential-provider references and an optional encrypted fleet vault |
| RFC-MASK-0016 | Proposed | Public trust evidence and staged supply-chain hardening |
| RFC-MASK-0017 | Implementing | Staged migration, agent workflow handoff and personal-use acceptance |

## Corrective UX and readiness pack

| RFC | Status | Title |
|---|---|---|
| RFC-MASK-0018 | Auto-Verified | Task-oriented CLI and human output |
| RFC-MASK-0019 | Accepted | Complete workflow readiness and checked-in native roles |
| RFC-MASK-0020 | Auto-Verified | Personal-scope workflow readiness for external implement-rfc state |

## Corrective managed-taps pack

| RFC | Status | Title |
|---|---|---|
| RFC-MASK-0021 | Implementing | Tap-only deployment, fetching updates and doctor migration |
