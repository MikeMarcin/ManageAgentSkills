# User requirement traceability

User decisions are requirements; RFC implementation details are proposed. No feature here is represented as shipped.

| Requirement | RFC / track | Concrete treatment |
|---|---|---|
| Automatic workspace readiness first | 0006 | ensure + owned Git/startup integration; no model bootstrap loop |
| Where-used | 0011 | Skill-centric inverse consumer/agent/source/artifact inventory |
| Update diff and impact | 0011, 0008 | Exact content diff and affected/unaffected pinned consumer report |
| Portable personal selections | 0010 | Selection+lock export/import and profile composition, never registry sync |
| Named bundles | 0010 | Recorded flat expansion; explicit refresh; no naive overlapping removal |
| Upstream provenance | 0007 | Frozen origin/path/revision/digest and local adaptation record |
| Per-skill per-user/project agent targeting; default all supported | 0009 | Independent consumer bindings, all semantics and preservation on v1 migration |
| Advertise generic/agent/platform support | 0009 | Passive machine-readable compatibility metadata and explicit applicability |
| Multiple sources/taps | 0007, 0008 | Approved source identities, URL/path discovery and exact source-qualified locks |
| True version pinning | 0008 | Isolated immutable deployed bytes, not a SHA beside a mutable checkout |
| Install by name or GitHub link, copy or tap, across all machines | 0013, 0012, 0017 | High-level resolve/import/publish/deploy/report plus canonical management handoff |
| Continuous fleet sync | 0013 | Opt-in scheduled catch-up of approved desired revisions, offline truthfulness |
| MCP design | 0014 | Optional stdio facade over the same operations, not arbitrary MCP-server installation |
| Secret vault design | 0015 | Provider references first; established encryption and explicit recipient grants later |
| Security/trust for strangers as stretch; useful personally first | 0016 plus core guards | Narrow permissions/integrity now; public verification/attestation and key lifecycle later |
| Passive audit not needed yet | Deferred tracking item | Heuristic audit deferred; structural/security invariants remain mandatory |
| Additional agents not yet provable but adoption concern | Deferred tracking item | Future adapter evidence criteria; Claude/Codex remain supported set |
| No high-ceremony deterministic workflow | 0006, 0013, 0017 | One ensure/install operation under standing authority; focused acceptance |

Every RFC acceptance criterion is copied to its unique closeout checklist and covered by at least one implementation card. The packet validator checks this correspondence and the local dependency graph.
