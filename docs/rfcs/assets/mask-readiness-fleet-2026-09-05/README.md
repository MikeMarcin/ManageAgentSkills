# MASK: workspace readiness, reproducible skills and personal fleet RFC pack

**Prepared:** September 5, 2026. **Basis:** supplied v0.2.0 source snapshot and the user's latest decisions. **State:** new proposed RFCs and implementation cards; no live repository/device changes or product acceptance.

Start with [START-HERE](START-HERE.md). The full pack contains **12 new RFCs, 56 implementation/closeout cards, and 2 deferred tracking items**. New IDs are provisional; existing RFCs 0001–0005 remain untouched.

## Product direction

Automatic workspace readiness ships first. After one-time integration/approval, normal clone/worktree/branch/startup operations use a single local ensure operation. Next, multiple sources and exact isolated artifacts make selections reproducible. Portable personal profiles, flat bundles, per-skill targeting, provenance and impact reports make the tool practical. Enrolled fleet rollout then lets Claude or Codex resolve a name/URL, import a copy or tap, deploy exact content to selected machines, and return a truthful report.

The default agent policy for new selections is every supported/enabled adapter, currently Claude and Codex; user and project bindings remain independent. Additional agents and heuristic content audit are tracked, not smuggled into core scope. Optional MCP facade, credential vault and public-release assurance are later tracks, not blockers for the owner's daily use.

## RFC index

| RFC | Title | Stage |
|---|---|---|
| [RFC-MASK-0006](docs/rfcs/RFC-MASK-0006-automatic-workspace-readiness.md) | Automatic workspace readiness for clone, worktree, branch and agent startup | A — first usable milestone |
| [RFC-MASK-0007](docs/rfcs/RFC-MASK-0007-sources-imports-and-provenance.md) | Multiple sources, taps, curated imports and upstream provenance | B — source foundation |
| [RFC-MASK-0008](docs/rfcs/RFC-MASK-0008-pinned-artifacts-and-recovery.md) | True version pinning, immutable deployment artifacts and recoverable migration | B — reproducible content |
| [RFC-MASK-0009](docs/rfcs/RFC-MASK-0009-scope-agent-targeting-and-compatibility.md) | Per-skill scope-specific agent targeting and advertised compatibility | B — selection semantics |
| [RFC-MASK-0010](docs/rfcs/RFC-MASK-0010-portable-selections-and-bundles.md) | Portable personal selections, reusable bundles and profile composition | C — portable composition |
| [RFC-MASK-0011](docs/rfcs/RFC-MASK-0011-inventory-and-update-impact.md) | Where-used inventory, update diffs and deployment impact reports | C — explainability |
| [RFC-MASK-0012](docs/rfcs/RFC-MASK-0012-fleet-enrollment-and-transport.md) | Explicit fleet enrollment, device identity and bounded remote transport | D — enrolled fleet foundation |
| [RFC-MASK-0013](docs/rfcs/RFC-MASK-0013-fleet-rollouts-and-continuous-sync.md) | Declarative fleet rollouts, optional continuous convergence and completion reports | D — personal fleet workflow |
| [RFC-MASK-0014](docs/rfcs/RFC-MASK-0014-optional-mcp-management-facade.md) | Optional MCP facade over the MASK management API | E — optional interface extension |
| [RFC-MASK-0015](docs/rfcs/RFC-MASK-0015-credential-providers-and-vault.md) | Credential-provider references and an optional encrypted fleet vault | E — optional credential extension |
| [RFC-MASK-0016](docs/rfcs/RFC-MASK-0016-public-trust-and-supply-chain-hardening.md) | Public trust evidence and staged supply-chain hardening | E — stretch public assurance |
| [RFC-MASK-0017](docs/rfcs/RFC-MASK-0017-integration-and-personal-dogfood.md) | Staged migration, agent workflow handoff and personal-use acceptance | A–D — integration and owner workflow |

## Important distinctions

“Copy” is a curated source import, not replacement of consumer skill directories. Restoring locked bytes is not upgrading upstream. Signed provenance is not proof of harmless content. A published fleet request is not a completed installation. Filesystem readiness is not evidence an active conversation forgot old instructions. Continuous runners are real opt-in installed software, not promises that a chat agent will work after it exits.

## Navigation

[Decision register](docs/design/DECISIONS.md) · [Source reconciliation](docs/design/SOURCE-RECONCILIATION.md) · [Shared contracts](docs/design/CONTRACTS.md) · [Roadmap](ROADMAP.md) · [Requirement traceability](TRACEABILITY.md) · [Primary references](docs/design/REFERENCES.md) · [Synthetic report preview](examples/fleet-report.html)

Use `python tools/validate_pack.py` to validate packet structure, dependencies, closeout coverage, links and fixture digests. The optional `--jsonschema` check also validates proposed examples using the separately installed jsonschema library. Neither command implements MASK or proves native/host/fleet behavior.

See [VALIDATION.md](VALIDATION.md) for the checks actually run on this packet. Integration commands, tests and schema shapes in RFCs are implementation targets until the corresponding capability ships.
