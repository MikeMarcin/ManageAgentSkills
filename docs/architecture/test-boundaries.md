# Focused acceptance boundaries

The test module names below are implementation targets used by task cards. The pack does not contain the finished program or claim these tests already pass.

| Module | Proves | Does not prove |
|---|---|---|
| `tests.test_cli_protocol` | Actual subprocess argv/JSON/stderr/exit behavior, deterministic capabilities | Model reasoning or host skill discovery |
| `tests.test_manifest_registry` | Prospective edits, no-op bytes, explicit roots, registry lifecycle | Cross-machine state convergence |
| `tests.test_skill_catalog` | Flat package validation and passive inspection | Arbitrary YAML or script trustworthiness |
| `tests.test_reconcile_plan` | Ownership truth table, source/path checks, stale-plan fingerprint | Atomic multi-file application |
| `tests.test_reconcile_apply` | Actual symlinks, safe unlink, parent/type drift, journaled apply | Race-proof hostile same-user filesystem containment |
| `tests.test_recovery` | Restart after interruption, complete/rollback/refusal without user-data overwrite | Source Git rollback or power-loss durability on all filesystems |
| `tests.test_git_update` | Local bare-remote update/refusal/source-vs-program distinction | Live GitHub authentication correctness |
| `tests.test_subprocess_policy` | Bounded helper processes, no prompt, timeout cleanup, sanitized JSON | Control of arbitrary user Git helpers/filters |
| `tests.test_launcher` | Native launcher quoting, argument forwarding, exit propagation | Installation through package managers |
| `tests.test_end_to_end` | Full direct CLI workflow on fixtures and shared context cutover | Successful native results on an OS not exercised |

Use `python -m unittest <module>` on the selected interpreter. All fixture roots, fake remotes and MASK_HOME values must be private temporary locations. Preserve/review the root before cleanup; test fixture cleanup is allowed for test-owned temporary directories, but MASK runtime never recursively deletes user paths.

Windows and macOS native cards select only symlink/launcher tests and the one end-to-end path relevant to the claim. Do not multiply every Python version by every OS by every host/runtime. Linux results may support portable logic but do not satisfy native cards. Optional real-agent discovery must name the actual host/version and whether an enabled skill was observed; missing credentials or a runtime not present is not a product test pass.

No broad soak, repeated unchanged clean build, large evidence archive or model evaluation framework is requested. Record focused command/result/commit on the live card and reuse unchanged results.
