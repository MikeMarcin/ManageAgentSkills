# Delivery roadmap and dependency plan

No hard dates are assigned. Each stage is independently useful and its claims remain bounded by actual acceptance.

| Stage | RFCs | User-visible checkpoint | Required predecessor |
|---|---|---|---|
| A | 0006 | Skills are reconciled for approved clone/worktree/branch/startup operations | Existing v0.2.0 baseline and explicit integration approval |
| B | 0007–0009 | Multiple sources, provenance, pinned isolated bytes, per-skill scope/agent choices | A; source and state migration are deliberate |
| C | 0010–0011 | Portable personal profiles, bundles, where-used and update-impact reports | B; initial legacy inventory can begin after ensure core |
| D | 0012–0013 plus 0017 handoff | One name/URL request installs across enrolled devices with truthful receipts and optional catch-up | Pinned selections + profiles + reports; real device enrollment |
| E (optional) | 0014–0016 | MCP interface, encrypted vault and public assurance | Core fleet; none blocks A–D |
| Core closeout | 0017 | Current docs, selected migrations, canonical management guidance and actual owner workflow | Required A–D evidence; optional tracks stay open |

## Scheduling rules

Import/reserve first. Finish the readiness milestone before advertising broader source/fleet capability. Within a milestone, work only dependency-ready cards and coordinate shared files. Card dependencies—not numeric RFC ordering—govern execution. Initial where-used work may run alongside the readiness milestone after the core ensure card, because it is observational and does not require new persistence.

Core code stays standard-library Python plus Git. Enrolled SSH/signature support adds explicit optional system-tool prerequisites. The MCP SDK and encrypted-vault provider are optional dependencies isolated from the core. Additional agents and heuristic audit remain Inbox tracking items.

Cross-repository AgentSkills work is a named handoff with actual external ID/revision attached after its integrator allocates it. The pack cannot reserve that repository's IDs. No live external prerequisite is assumed complete.

## Bounded task inventory

| Provisional card | RFC | Work | Dependencies |
|---|---|---|---|
| [MASK-0023](docs/issues/10-backlog/MASK-0023-import.md) | RFC-MASK-0017 | Reconcile live sources and import the staged RFC pack | None |
| [MASK-0024](docs/issues/10-backlog/MASK-0024-ensure-core.md) | RFC-MASK-0006 | Add one authorized ensure path over the existing reconciler | MASK-0023 |
| [MASK-0025](docs/issues/10-backlog/MASK-0025-ensure-lifecycle.md) | RFC-MASK-0006 | Implement branch inactivity and bounded readiness recovery | MASK-0024 |
| [MASK-0026](docs/issues/10-backlog/MASK-0026-git-integration.md) | RFC-MASK-0006 | Install owned Git integrations and suppress internal hooks | MASK-0025 |
| [MASK-0027](docs/issues/10-backlog/MASK-0027-host-integration.md) | RFC-MASK-0006 | Add Claude and Codex startup adapters and prelaunch fallback | MASK-0025 |
| [MASK-0028](docs/issues/10-backlog/MASK-0028-readiness-mac.md) | RFC-MASK-0006 | Verify native macOS workspace and host readiness | MASK-0026, MASK-0027 |
| [MASK-0029](docs/issues/10-backlog/MASK-0029-readiness-win.md) | RFC-MASK-0006 | Verify native Windows workspace and host readiness | MASK-0026, MASK-0027 |
| [MASK-0030](docs/issues/10-backlog/MASK-0030-sources.md) | RFC-MASK-0007 | Implement approved source identities and multi-source catalog | MASK-0067 |
| [MASK-0031](docs/issues/10-backlog/MASK-0031-source-discovery.md) | RFC-MASK-0007 | Resolve skill URLs and bounded indexed/nested packages | MASK-0030 |
| [MASK-0032](docs/issues/10-backlog/MASK-0032-imports.md) | RFC-MASK-0007 | Add curated copy imports with verifiable provenance | MASK-0031 |
| [MASK-0033](docs/issues/10-backlog/MASK-0033-package-guards.md) | RFC-MASK-0007 | Harden passive package acquisition and plain-skill boundaries | MASK-0031 |
| [MASK-0034](docs/issues/10-backlog/MASK-0034-lock-model.md) | RFC-MASK-0008 | Implement portable v2 selections and exact resolution locks | MASK-0068 |
| [MASK-0035](docs/issues/10-backlog/MASK-0035-artifact-store.md) | RFC-MASK-0008 | Build isolated raw-byte artifacts and exact hydration | MASK-0034, MASK-0033 |
| [MASK-0036](docs/issues/10-backlog/MASK-0036-artifact-reconcile.md) | RFC-MASK-0008 | Retarget owned links and recover lock/artifact transitions | MASK-0035 |
| [MASK-0037](docs/issues/10-backlog/MASK-0037-pin-migration.md) | RFC-MASK-0008 | Add explicit legacy migration and pinned update operations | MASK-0036 |
| [MASK-0038](docs/issues/10-backlog/MASK-0038-target-model.md) | RFC-MASK-0009 | Implement per-binding agent choices and compatibility metadata | MASK-0036 |
| [MASK-0039](docs/issues/10-backlog/MASK-0039-adapter-contract.md) | RFC-MASK-0009 | Consolidate adapter metadata and reject deployment-name conflicts | MASK-0038 |
| [MASK-0040](docs/issues/10-backlog/MASK-0040-target-native.md) | RFC-MASK-0009 | Verify native scope-specific pinned targeting | MASK-0039, MASK-0037 |
| [MASK-0041](docs/issues/10-backlog/MASK-0041-portable.md) | RFC-MASK-0010 | Implement portable personal profile export and import | MASK-0069, MASK-0070 |
| [MASK-0042](docs/issues/10-backlog/MASK-0042-bundles.md) | RFC-MASK-0010 | Implement flat named bundle expansion and guarded refresh | MASK-0041 |
| [MASK-0043](docs/issues/10-backlog/MASK-0043-subscriptions.md) | RFC-MASK-0010 | Compose subscribed profile and local selection contributions | MASK-0042 |
| [MASK-0044](docs/issues/10-backlog/MASK-0044-inventory.md) | RFC-MASK-0011 | Expose skill-centric where-used and actual deployment inventory | MASK-0024 |
| [MASK-0045](docs/issues/10-backlog/MASK-0045-impact.md) | RFC-MASK-0011 | Explain exact content diffs and selected consumer impact | MASK-0044, MASK-0069, MASK-0070, MASK-0071 |
| [MASK-0046](docs/issues/10-backlog/MASK-0046-report-render.md) | RFC-MASK-0011 | Add compact text JSON and offline HTML report renderers | MASK-0045 |
| [MASK-0047](docs/issues/10-backlog/MASK-0047-fleet-identity.md) | RFC-MASK-0012 | Implement local device enrollment and authorization records | MASK-0069, MASK-0070 |
| [MASK-0048](docs/issues/10-backlog/MASK-0048-fleet-rpc.md) | RFC-MASK-0012 | Implement bounded remote protocol and idempotent local dispatch | MASK-0047 |
| [MASK-0049](docs/issues/10-backlog/MASK-0049-fleet-ssh.md) | RFC-MASK-0012 | Add fixed-entrypoint SSH and exact artifact transfer | MASK-0048 |
| [MASK-0050](docs/issues/10-backlog/MASK-0050-fleet-native.md) | RFC-MASK-0012 | Verify native remote invocation and enrollment boundaries | MASK-0049 |
| [MASK-0051](docs/issues/10-backlog/MASK-0051-fleet-control.md) | RFC-MASK-0013 | Implement signed desired state and conflict-safe control publication | MASK-0071, MASK-0073 |
| [MASK-0052](docs/issues/10-backlog/MASK-0052-fleet-install.md) | RFC-MASK-0013 | Compose one-request copy or tap installation and fan-out | MASK-0051, MASK-0068, MASK-0072 |
| [MASK-0053](docs/issues/10-backlog/MASK-0053-fleet-receipts.md) | RFC-MASK-0013 | Track per-device completion failure and supersession | MASK-0052 |
| [MASK-0054](docs/issues/10-backlog/MASK-0054-fleet-runner.md) | RFC-MASK-0013 | Add opt-in native scheduled convergence and offline catch-up | MASK-0053 |
| [MASK-0055](docs/issues/10-backlog/MASK-0055-fleet-dogfood.md) | RFC-MASK-0013 | Demonstrate real two-machine install and offline convergence | MASK-0054, MASK-0050 |
| [MASK-0056](docs/issues/10-backlog/MASK-0056-mcp-service.md) | RFC-MASK-0014 | Add optional SDK-based MCP management facade | MASK-0074 |
| [MASK-0057](docs/issues/10-backlog/MASK-0057-mcp-hosts.md) | RFC-MASK-0014 | Verify optional client integration and cancellation semantics | MASK-0056 |
| [MASK-0058](docs/issues/10-backlog/MASK-0058-credential-seam.md) | RFC-MASK-0015 | Implement credential handle providers without exporting values | MASK-0073 |
| [MASK-0059](docs/issues/10-backlog/MASK-0059-sealed-vault.md) | RFC-MASK-0015 | Add opt-in established-provider encrypted vault delivery | MASK-0058, MASK-0074 |
| [MASK-0060](docs/issues/10-backlog/MASK-0060-vault-recovery.md) | RFC-MASK-0015 | Verify vault rotation revocation and recovery limitations | MASK-0059 |
| [MASK-0061](docs/issues/10-backlog/MASK-0061-trust-docs.md) | RFC-MASK-0016 | Publish inspectable threat and effect boundaries for review | MASK-0068, MASK-0069, MASK-0074 |
| [MASK-0062](docs/issues/10-backlog/MASK-0062-release-verification.md) | RFC-MASK-0016 | Prepare optional reproducible release and signature verification | MASK-0061 |
| [MASK-0063](docs/issues/10-backlog/MASK-0063-trust-rotation.md) | RFC-MASK-0016 | Document and test signer rotation and future update-channel boundaries | MASK-0062 |
| [MASK-0064](docs/issues/10-backlog/MASK-0064-agent-handoff.md) | RFC-MASK-0017 | Coordinate canonical AgentSkills guidance and metadata handoff | MASK-0071, MASK-0072, MASK-0053 |
| [MASK-0065](docs/issues/10-backlog/MASK-0065-core-migrate-docs.md) | RFC-MASK-0017 | Reconcile shipped current contracts and selected consumer migrations | MASK-0067, MASK-0068, MASK-0069, MASK-0070, MASK-0071, MASK-0072, MASK-0073, MASK-0074, MASK-0064 |
| [MASK-0066](docs/issues/10-backlog/MASK-0066-core-acceptance.md) | RFC-MASK-0017 | Record focused milestone and real owner-workflow acceptance | MASK-0065 |
| [MASK-0067](docs/issues/10-backlog/MASK-0067-close-6.md) | RFC-MASK-0006 | Verify and close RFC-MASK-0006 | MASK-0024, MASK-0025, MASK-0026, MASK-0027, MASK-0028, MASK-0029 |
| [MASK-0068](docs/issues/10-backlog/MASK-0068-close-7.md) | RFC-MASK-0007 | Verify and close RFC-MASK-0007 | MASK-0030, MASK-0031, MASK-0032, MASK-0033 |
| [MASK-0069](docs/issues/10-backlog/MASK-0069-close-8.md) | RFC-MASK-0008 | Verify and close RFC-MASK-0008 | MASK-0034, MASK-0035, MASK-0036, MASK-0037 |
| [MASK-0070](docs/issues/10-backlog/MASK-0070-close-9.md) | RFC-MASK-0009 | Verify and close RFC-MASK-0009 | MASK-0038, MASK-0039, MASK-0040 |
| [MASK-0071](docs/issues/10-backlog/MASK-0071-close-10.md) | RFC-MASK-0010 | Verify and close RFC-MASK-0010 | MASK-0041, MASK-0042, MASK-0043 |
| [MASK-0072](docs/issues/10-backlog/MASK-0072-close-11.md) | RFC-MASK-0011 | Verify and close RFC-MASK-0011 | MASK-0044, MASK-0045, MASK-0046 |
| [MASK-0073](docs/issues/10-backlog/MASK-0073-close-12.md) | RFC-MASK-0012 | Verify and close RFC-MASK-0012 | MASK-0047, MASK-0048, MASK-0049, MASK-0050 |
| [MASK-0074](docs/issues/10-backlog/MASK-0074-close-13.md) | RFC-MASK-0013 | Verify and close RFC-MASK-0013 | MASK-0051, MASK-0052, MASK-0053, MASK-0054, MASK-0055 |
| [MASK-0075](docs/issues/10-backlog/MASK-0075-close-14.md) | RFC-MASK-0014 | Verify and close RFC-MASK-0014 | MASK-0056, MASK-0057 |
| [MASK-0076](docs/issues/10-backlog/MASK-0076-close-15.md) | RFC-MASK-0015 | Verify and close RFC-MASK-0015 | MASK-0058, MASK-0059, MASK-0060 |
| [MASK-0077](docs/issues/10-backlog/MASK-0077-close-16.md) | RFC-MASK-0016 | Verify and close RFC-MASK-0016 | MASK-0061, MASK-0062, MASK-0063 |
| [MASK-0078](docs/issues/10-backlog/MASK-0078-close-17.md) | RFC-MASK-0017 | Verify and close RFC-MASK-0017 | MASK-0023, MASK-0064, MASK-0065, MASK-0066 |

## Deferred tracking items

- [MASK-0079: Track additional agent adapters as an adoption opportunity](docs/issues/00-inbox/MASK-0079-additional-agents.md)
- [MASK-0080: Defer passive heuristic skill auditing until a concrete need](docs/issues/00-inbox/MASK-0080-passive-audit.md)

## Scope and verification economy

A working local CLI is not held hostage by optional vault/public-release/MCP work. Real host/native/fleet claims still require actual evidence; missing a required lane stays open, but does not force unrelated work to stop. Use focused tests per card and one integration-focused pass at a milestone. A risk-triggered broad suite or independent review can be useful for persistence/remote authority; exhaustive host/interpreter cross-products and proof-of-proof archives are not default work.
