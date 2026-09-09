# Corrective UX and readiness baseline (MASK-0083)

Pre-implementation observation for RFC-MASK-0018 and RFC-MASK-0019, recorded at
baseline `6d80121b1c870f1be7864e8bc9db2b02a0e41c2d` (`mask.py` SHA-256
`0b93ecc6499082565e7875cb3e48bd3e8dcf0e4186e0118449410a7ab696abe1`, identical to
the packet snapshot). Host: macOS (darwin), Python 3.14.7, private `MASK_HOME`,
disposable source and consumer roots. Nothing below is a product pass; it is the
failing expectation each later card must turn.

## Source reconciliation

Every MASK file named in the retained packet `source-basis.json` matched the
packet hash at the pre-import commit `49e3971e`. No live work already addressed
the defects. The packet reproducer (`docs/rfcs/assets/mask-corrective-ux-readiness/tools/reproduce_supplied_baseline.py --program mask.py`)
returned the same observations as the packet's Linux record:
`inventory` without `--json` parsed as JSON with six link rows; `ensure` and
`ensure --check` succeeded with readiness `ready_legacy_unpinned` while
`.codex/agents/rfc-integrator.toml` and `.claude/agents/rfc-integrator.md` were absent;
no package setup executed.

## Starting states (`tests/public_support.py`)

`PublicFixture` prepares only the one-time source (`mask init --source`) and
provides `raw`, `machine` (explicit `--json`) and `human` (never injects `--json`)
helpers. States: a fresh unregistered project; a fresh personal home with no
`user.json`; and `linked_consumer_with_stale_roles()`, a SRV-shaped consumer with
correct `implement-rfc` links, the fixture workflow context, an older
`rfc-worker` role file and no `rfc-integrator` for Codex or Claude. The old role
state is retained, never repaired, before the command under test.

## Recorded defects (`tests/test_public_baseline.py`, `expectedFailure`)

| Command (public CLI, human unless noted) | Required by | Baseline observation |
|---|---|---|
| `mask inventory --project P` | RFC-MASK-0018-AC02 | stdout is the indented result envelope |
| `mask --version` | RFC-MASK-0018-AC02 | stdout is the result envelope |
| `mask capabilities` | RFC-MASK-0018-AC02 | stdout is the result envelope |
| `mask install alpha` (fresh project) | RFC-MASK-0018-AC01 | exit 2 `invocation.invalid`; no such command |
| `mask install alpha --user` (fresh home) | RFC-MASK-0018-AC01 | exit 2 `invocation.invalid` |
| `mask ensure --project P --check --json` (missing rfc-integrator) | RFC-MASK-0019-AC01 (W01) | exit 0, `ok: true`, role never named |
| `mask ensure --project P --json` (missing rfc-integrator) | RFC-MASK-0019-AC01 | readiness `ready_legacy_unpinned`; no generator ran |

Run: `python3 -B -m unittest tests.test_public_baseline` — 10 tests, 3 pass
(starting states and non-injecting human helper), 7 expected failures. A later
fix removes the corresponding decorator; an unexpected success is that signal.

## Not observed here

Native Windows journeys, terminal prompt mechanics, host role loading and the
real AgentSkills package (RFC-MASK-0018-AC08, RFC-MASK-0019-AC07) are not
exercised by this baseline; the synthetic static package uses model
`fixture-model-do-not-run` and is never installed into a real host.
