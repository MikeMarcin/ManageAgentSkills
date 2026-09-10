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

## Native lanes for RFC-MASK-0018 (MASK-0091)

Candidate `a85651002f3dbf2b9a94c45a2c0e6564771b4b09`, September 9, 2026.
Independent review (rfc-reviewer, claude-fable-5-1, effort high) of that candidate
found one AC07 failure: the README's first command refused on a home without
`~/.local` because the old `mkdir -p "$HOME/.local/bin"` line had been dropped.
`6dcd5a4c57b590bb511e778aa4eae40830055735` restores it, replays the README from
a fresh home in `tests/test_readme_journeys.py`, states `ensure` consent as
per-invocation, gives the Windows installation recipe in text form and corrects
the `update` scope sentence (`affected` includes the selected scope). The literal
chain (`mkdir -p`, `self install`, `init`, `install alpha`, `list`) was rerun from
an empty `HOME` on macOS at that revision; the Windows evidence below is from
`a856510` and was not rerun for these text/test-only corrections.

macOS 26.6.2 / arm64, Python 3.14.7: `python3 -B -m unittest
tests.test_readme_journeys tests.test_task_commands tests.test_consent
tests.test_public_baseline tests.test_human_output` (47 tests, OK). The README
recipes ran through the launcher `self install` wrote; the `ensure` yes/no/pipe
journey ran on a POSIX pseudoterminal.

Windows 11 Home 10.0.26200 (ExampleWinHost), Windows Python 3.14.7, Git 2.55.0.windows.3,
disposable clone of the candidate under `C:\code\git\mask-m6-disposable`
(removed afterwards): `py -3 -B -m unittest tests.test_readme_journeys
tests.test_task_commands tests.test_human_output tests.test_public_baseline
tests.test_launcher` (37 tests, OK, 1 pty skip) and `tests.test_consent.PipedConsentTests
tests.test_consent.ConsentSeamTests` plus the non-terminal `tests.test_update_task`
classes (15 tests, OK, 1 skip). The `mask.cmd` launcher ran `init`, `install`,
`list`, `ensure`, `remove` natively. The console confirmation was a recorded
bounded interaction in an OpenSSH ConPTY session (Git bash prompt, then
`powershell -NoProfile -File console.ps1`): `mask ensure` on an unapproved project
with one missing link printed the proposal and `[y/N]`; `y` created the link, exit
0, no `integration.json`; on a reset fixture `n` gave `confirmation.declined`, exit
4, no link. Nothing was written to the real profile; `MASK_HOME` was a temporary
directory.

Two defects found on the first Windows run and fixed in the candidate: the public
fixture set only `HOME`, so `install --user` wrote to the real `%USERPROFILE%`
(four dangling fixture links were removed by hand; `USERPROFILE` is now fixed
to the fixture home), and `text=auto` CRLF normalization changed the static
package's role bytes so every `implement-rfc` install refused `workflow.invalid`
(fixture paths are now `-text`). The second finding is a real requirement for any
package that declares role fingerprints: its repository must pin those assets to
exact bytes (`-text` or `eol=lf`), which belongs in the AgentSkills handoff
(MASK-0090). `stderr` is now reconfigured to UTF-8 like `stdout`, so human error
text with non-ASCII paths survives Windows pipes. Known cosmetic limitation:
Windows human output shows planned link targets with the `\\?\` extended-length
prefix. Host loading of any skill or role remains not verified on either OS.

## Not observed here

Host role loading and the real AgentSkills package (RFC-MASK-0019-AC07) are not
exercised; the synthetic static package uses model
`fixture-model-do-not-run` and is never installed into a real host.
