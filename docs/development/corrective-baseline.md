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

Run: `python3 -B -m unittest tests.test_public_baseline` — 10 tests. At the
baseline commit 3 passed (starting states and non-injecting human helper) and 7
were expected failures. A later fix removes the corresponding decorator; an
unexpected success is that signal.

MASK-0084 removed the three RFC-MASK-0018-AC02 decorators: `mask_present.py`
renders every registered command from the same result object (`RENDERERS` is the
coverage table checked by `tests/test_human_output.py`), `mask.py::main` no longer
falls back to indented JSON, `mask` alone prints everyday help, `--version` prints
a version line and handled errors go to stderr with code, relevant details,
preserved state and a remediation line. The four AC01/W01 rows remain expected
failures for MASK-0086 and MASK-0088.

MASK-0086 removed the two RFC-MASK-0018-AC01 decorators (`install` from a fresh
project and personal scope). MASK-0088 removed the two RFC-MASK-0019-AC01 rows:
`mask_workflow.py` reads the passive `mask-workflow.json`, `mask_fs.plan` derives
the required roles from the selected bindings and observes every destination,
`ensure --check` names the missing `rfc-integrator` role (exit 7 when the static
package can supply it, exit 4 `workflow.incomplete` when only preserved files
remain), and `ensure` deploys exact package assets through the journal while the
older `rfc-worker` bytes are kept. The starting state in `tests/public_support.py`
is now restored by hand after the engine's own deployment, because the same
engine that links also deploys declared static roles; nothing repairs that state
before the command under test.

MASK-0091 replaced the README everyday guide with the short task guide (advanced
material moved under `docs/guides/`) and added `tests/test_readme_journeys.py`,
which replays those recipes exactly as written (C21) through the launcher that
`self install` wrote: `init --source`, `install implement-rfc`, `list`, `ensure`
(pty yes completes, no declines, a pipe never asks), `install alpha --user`,
`list --user`, `remove`, `update --dry-run` and `update` against a local bare
remote. No `--json`, plan hash or pre-registration is involved. `self update` is
not replayed because it would touch the real program checkout's remote.

## Not observed here

Native Windows journeys, terminal prompt mechanics, host role loading and the
real AgentSkills package (RFC-MASK-0018-AC08, RFC-MASK-0019-AC07) are not
exercised by this baseline; the synthetic static package uses model
`fixture-model-do-not-run` and is never installed into a real host.
