# Public v2 and private operation tests

`tests/test_cli_v2.py`, `tests/test_refresh_v2.py`, `tests/test_upgrade_readiness.py`,
`tests/test_cli_protocol.py`, `tests/test_tap_identity.py`, `tests/test_tap_bootstrap.py` and
`tests/test_readme_journeys.py` execute the shipped `mask.py` interface. These own
current command names, checkout defaults, scope isolation, combined review, pin
holds, enrollment, cleanup and the README journey.

`tests/engine_cli.py` is a test-only subprocess harness for private operation IDs.
`Fixture` and `EngineFixture` use it to construct intermediate states and exercise
retained journal, artifact, ownership and automatic-readiness contracts. Those
operation IDs are not public aliases and are absent from shipped capabilities.
The harness has no production environment switch and is not installed by MASK.
Tests of public behavior must use `PublicFixture`/the real entrypoint instead.

# Focused acceptance boundaries

Each row names a test module, what it proves and what it does not prove. Rows
using retired spellings describe private engine contracts through the harness above. A row is a boundary that task cards select, not a recorded pass.

| Module | Proves | Does not prove |
|---|---|---|
| `tests.test_cli_v2` | Checkout/user/all isolation, pin holds with readiness, fresh worktree enrollment, single task review, stale refusal, setup failure/recovery, explicit cleanup and preparation locking through the shipped CLI | Native Windows consoles, live catalog availability, host loading |
| `tests.test_refresh_v2` | 24-hour automatic refresh, no-update/offline/reviewed-plan behavior, explicit machine home and program re-exec, using disposable program clones | Updating the live checkout or external Git hosting |
| `tests.test_cli_protocol` | Actual subprocess argv/JSON/stderr/exit behavior, deterministic capabilities | Model reasoning or host skill discovery |
| `tests.test_manifest_registry` | Prospective edits, no-op bytes, explicit roots, registry lifecycle | Cross-machine state convergence |
| `tests.test_skill_catalog` | Flat package validation and passive inspection | Arbitrary YAML or script trustworthiness |
| `tests.test_reconcile_plan` | Ownership truth table, source/path checks, stale-plan fingerprint | Atomic multi-file application |
| `tests.test_reconcile_apply` | Actual symlinks, safe unlink, parent/type drift, journaled apply | Race-proof hostile same-user filesystem containment |
| `tests.test_recovery` | Restart after interruption, complete/rollback/refusal without user-data overwrite | Git checkout rollback or power-loss durability on all filesystems |
| `tests.test_subprocess_policy` | Bounded helper processes, no prompt, timeout cleanup, sanitized JSON | Control of arbitrary user Git helpers/filters |
| `tests.test_launcher` | Native launcher quoting, argument forwarding, exit propagation | Installation through package managers |
| `tests.test_end_to_end` | Full direct CLI workflow on fixtures and shared context cutover | Successful native results on an OS not exercised |
| `tests.test_public_baseline` | Public human/`--json`/raw invocations from unprepared starting states; the RFC-MASK-0018/0019 baseline cases, with no `expectedFailure` decorator left | Native terminal prompts, host role loading, the real AgentSkills package |
| `tests.test_readme_journeys` | The README's recipes, beginning with `tap NAME URL`, replayed as written through the installed launcher and the plain entrypoint on a local fixture tap, including terminal prompts on a POSIX pseudoterminal | Native Windows console prompts (recorded separately), host role loading, a network remote, `update` against a live remote |
| `tests.test_tap_bootstrap` | On an empty MASK_HOME with no working checkout on disk, `tap NAME URL` then `install` over a local bare upstream writes v3 config, a bare cache, a v2 declaration and lock, and store-targeted links. An offline install before any fetch refuses, naming the tap, and writes nothing. Retired `init` refuses; `config set` changes catalog defaults | A network remote or authentication, the real AgentSkills package, native results on an OS not exercised |
| `tests.test_update` | With two local `file` taps and three consumers, `upgrade` fetches each referenced tap once (counted from Git trace2 events) and activates one journal. An unreachable tap blocks only its consumers (`upgrade.incomplete`). `--dry-run`, `--offline` and `--expect-plan-hash` never fetch. A moved tag refuses without `--allow-ref-rebind`. Dev-link consumers are skipped, or refused when scoped. `source fetch` without a name deploys nothing. Git hooks are suppressed, bad candidates refuse typed and a late failure rolls back to exact bytes | Network transports or authentication, a real upstream |
| `tests.test_upgrade_readiness` | Upgrade reconciles registered project/personal scopes, candidate or unchanged-version setup, missing links, consent and stale previews, publication failure and crash recovery through the public CLI; setup reruns are idle | Real package semantics, Windows terminal interaction, host loading |
| `tests.test_link_producers` | An AST inventory of every `mask*.py` call that creates a link or computes a link text, and of every `mask_pinned.target` derivation, matches its allowlist. After public link producers run on a tap-first machine, every recorded and observed owned link is under `MASK_HOME/store/v1`, except the explicit `source dev-link`. | A link spelling outside the scanned call names, host discovery of the linked skill |
| `tests.test_tap_line_endings` | Under a disposable global `core.autocrlf=true`, an exact tap publishes exact bytes and refuses a converted clone before any effect. An `--autocrlf` tap records and discloses the conversion and matches the blobs Git itself stores. Committed line-ending attributes refuse. An entry without `line_endings` keeps exact bytes. Private capabilities, public `tap` help and the v3 schema describe the policy | Other Git line-ending or filter configurations, system Git configuration |

Use `python -m unittest <module>` on the selected interpreter, or `python -B scripts/run_tests.py` for every class in parallel, one process each. All fixture roots, fake remotes and MASK_HOME values must be private temporary locations. Preserve/review the root before cleanup; test fixture cleanup is allowed for test-owned temporary directories, but MASK runtime never recursively deletes user paths.

Windows and macOS native cards select only symlink/launcher tests and the one end-to-end path relevant to the claim. Do not multiply every Python version by every OS by every host/runtime. Linux results may support portable logic but do not satisfy native cards. Optional real-agent discovery must name the actual host/version and whether an enabled skill was observed; missing credentials or a runtime not present is not a product test pass.

No broad soak, repeated unchanged clean build, large evidence archive or model evaluation framework is requested. Record focused command/result/commit on the live card and reuse unchanged results.
