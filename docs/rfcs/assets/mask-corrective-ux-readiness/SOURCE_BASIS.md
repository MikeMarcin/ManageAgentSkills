# Source basis and limits

The pack is drafted from the uploaded source snapshots, the attached README, and
the user's corrections in this conversation. It is not a live GitHub audit or a
claim that the user's current checkout is identical to the supplied snapshot.
No outside documentation is used to override those sources.

| Input | Stated generation | Actual SHA-256 |
|---|---|---|
| ManageAgentSkills source, 311 files | 2026-09-07T18:48:22-07:00 | `b88187f3445c572fbfac80b436f0370838e1e650060c70dbd379f89033060dd1` |
| AgentSkills source, 365 files | 2026-09-08T20:06:53-07:00 | `092b1d58ad6c68d04b763526a45b75db543a2a6e49553099beafad551385aa4f` |
| Attached MASK README | Same bytes as the README in the MASK dump | `7c78fc422806db246994c1562daed101bac35d368d9311da440bf64fb5b22c57` |

`source-basis.json` contains selected extracted file hashes and byte provenance.
The original complete private dumps and SRV usage archives are not redistributed.

## Observed source facts

| Fact | Direct source location | Implication |
|---|---|---|
| Non-JSON success serializes the result object | MASK mask.py::main, final print branch | There is no proper default human renderer to reveal merely by removing --json from examples |
| Test helper always adds --json | MASK tests/support.py::Fixture.call | That helper does not test the human invocation |
| Contract forbids prompts | MASK docs/architecture/cli-contract.md, Common options | Interactive consent is a deliberate contract correction |
| ensure builds an fs.plan of declared skill deployment | MASK mask_ensure.py::ensure | Existing readiness does not evaluate an implement-rfc role requirement descriptor |
| Pinned membership needs real implementation | MASK mask.py::project_dispatch, selection.command_unsupported; mask_pinned.py transitions | A shell alias to old require/unrequire would fail v2 workflows |
| Legacy inventory skips pinned detail | MASK mask_report.py::dispatch, inventory.pinned_unsupported | Basic readable pinned listing cannot depend on this legacy-only result as-is |
| Passive package boundary rejects native discovery trees | MASK mask_packages.py, mask_adapters.py, CLI package contract | Use neutral role asset paths and explicit typed deployment, not a backdoor activation directory |
| Updater enforces schema compatibility | MASK mask_install.py and CLI contract | Keep updater/recovery version guards; do not force new journal bytes through old code |
| Renderer checks missing/stale files and owns its outputs | AgentSkills render_runtime_adapters.py::write_or_check / publish_adapters | Detection exists; invocation and ownership integration are missing |
| Rendered prompts contain consumer addenda and selected routes | AgentSkills render_runtime_adapters.py::rendered_role_instructions / main | Current consumer-generated outputs are not automatically universal package definitions |
| Source-only validator returns without consumer validation | AgentSkills validate_portable_agents.py::main | Source qualification is a different boundary |
| Native qualification prepares consumers explicitly | AgentSkills docs/rfcs/assets/RFC-ASK-0010-qualification.md | That evidence does not test normal MASK installation from the broken starting state |
| Live ID boundary in this snapshot | MASK docs/rfcs/README.md and docs/issues/NEXT_ID | RFC18/19 and MASK0083–0094 are provisional only |

## User decisions versus proposed mechanics

**User-required outcomes:** restore simple commands; human output without --json;
ensure should ask before necessary scripts and then finish; checked-in role
files should work; qualification must catch incomplete consumer setup. Existing
preferences retain agent-friendly automation and safety without manual ceremony.

**Proposed mechanics in this pack:** install/remove/list task spellings, a small
passive workflow descriptor, typed native-role outputs, portable consumer role
locks, staged Python setup and exact named noninteractive consent. These are
implementation proposals, not falsely attributed prior user syntax or features
already present. Historical plan/apply/raw commands remain available.

**Boundaries:** MASK cannot guarantee a model follows a prose startup template,
prove effective model/effort from configuration, or prevent malicious approved
Python code acting with user privileges. The AgentSkills handoff owns role prompt
consistency; native loading/execution stays separate. Stable coordinator context
and quota consumption are not reanalysed or optimized by this pack.

No live IDs, implementation baseline SHA, source handoff commit, native PASS,
consumer migration, or subscription saving is invented. The original Python
sources are inspected and may be exercised only in a disposable reproduction
fixture; such a baseline observation is not acceptance of these new requirements.
