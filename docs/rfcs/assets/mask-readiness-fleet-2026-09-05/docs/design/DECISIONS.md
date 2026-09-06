# Decision register

| ID | Decision | Basis / owner |
|---|---|---|
| D01 | Automatic clone/worktree/branch/startup readiness is first | Explicit latest user approval |
| D02 | Where-used and update diff/impact are core features | Explicit user selection |
| D03 | Personal selections must be portable, not machine state | User selection; design derives portable boundary from M1 |
| D04 | Named bundles expand into explicit selections initially | User selects bundles; flat expansion is proposed implementation |
| D05 | Preserve upstream provenance and local adaptations | Explicit user selection |
| D06 | Agent targeting is per skill independently in user/project scope; new default all supported | Explicit user requirement |
| D07 | Generic/specific agent/platform metadata is useful; no automatic requirement-tool execution | User requirement plus bounded implementation choice |
| D08 | Multiple independent sources/taps are core, not deferred | Explicit user direction superseding M2 |
| D09 | Pin deployed bytes with isolated artifacts, not only a recorded SHA | User requires true pinning; implementation design |
| D10 | One name/URL request should install across enrolled devices with a completion report | Explicit user goal |
| D11 | Resolve/import once, deploy the same exact artifacts everywhere | Proposed design supporting D09/D10 |
| D12 | Online push first; opt-in pull runner catches up offline devices | Proposed design supporting desired continuous behavior |
| D13 | Basic authority/integrity safeguards ship with core; public assurance is stretch | User prioritization plus existing ownership invariants |
| D14 | Passive heuristic audit is deferred | Explicit user preference |
| D15 | Additional agents remain tracked, not advertised without proof | Explicit user preference |
| D16 | Optional MCP facade, not a required new source/install engine | Proposed interpretation of broader design interest |
| D17 | Existing auth first; optional established-crypto vault later | Proposed design; no need to replicate credentials for base fleet use |
| D18 | No human gate for deterministic repeated mechanics under delegated policy | M1 unified-workflow constraints and latest usability goal |
| D19 | No all-devices success while offline/unknown/blocked devices remain | Derived truthfulness requirement for D10 |
| D20 | Separate source publication, content resolution, activation, host loading, and program update | Existing M1 separation extended to fleet |

No question in this register needs to be re-asked merely to import the pack. At implementation, genuinely new policy choices such as real device enrollment, key trust, publication scope or a default copy/tap mode must be resolved from live configuration or explicit owner input. The packet itself performs none of those actions.
