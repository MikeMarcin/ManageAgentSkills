# ManageAgentSkills RFC tracker

Live RFCs are top-level `RFC-MASK-NNNN-*.md` files. Retained packets under `assets/` are immutable provenance, never a second live RFC/card index. Status vocabulary: Proposed, Accepted, Implementing, Auto-Verified, Rejected, Superseded.

Only the main integrator imports, renumbers, edits tracker rules and confirms terminal status after integration. Each RFC has exactly one linked closeout card with `closeout: true`. Store actual RFC_BASE_SHA before source implementation and record direct acceptance result/commit rows. Live board linkage selects work, not an arbitrary directory listing.

| RFC | Status | Title |
|---|---|---|
| RFC-MASK-0001 | Auto-Verified | Agent-friendly CLI and declarative project state |
| RFC-MASK-0002 | Auto-Verified | Ownership-safe planning, symlink deployment and recovery |
| RFC-MASK-0003 | Proposed | Explicit source updates, portable launchers and program updates |
| RFC-MASK-0004 | Proposed | Bootstrap cutover, native dogfood and bounded v1 closeout |

## Import and verification

Reconcile live IDs before adopting packet IDs. Keep original packet IDs in provenance and record a LIVE_IMPORT mapping including external handoffs. Never rewind counters or recycle reservations. Run `python scripts/verify_documentation.py --root .` after import/integration and before terminal status. When working a lane, status changes are proposals until the integrator revalidates them on main.
