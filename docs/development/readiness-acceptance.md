# Workspace readiness acceptance

Native macOS boundary recorded September 5, 2026 at `98c0f2e24666bcf0b50b11fd8f3973d80f2eaf9a`.

| Component | Observed |
|---|---|
| OS / architecture | macOS 26.6.2 / arm64 |
| Fixture filesystem | APFS (queried through the temporary root's mounted device) |
| Python | 3.14.7 |
| Git | 2.50.1 (Apple Git-155) |
| Claude Code | 2.1.260 |
| Codex CLI | 0.153.2 |

`python3 -B -m unittest tests.test_host_integration.HostIntegrationTests.test_native_macos_launcher_and_installed_host_prelaunch`
passed. The disposable fixture installed the owned launcher, deployed real
native directory symlinks at a spaced/Unicode root, and launched both installed
host executables with `--version` after readiness. This does not open a model
session or verify first-prompt skill discovery. Earlier recorded native Git
fixtures cover branch/worktree/merge/manual-merge events and worktree removal.

Claude's adapter requests a reload but cannot block SessionStart. Codex's stop
output follows its documented hook contract; actual host enforcement and
first-prompt loading are unverified. Use `mask launch` for readiness before the
host starts. Existing Codex local-environment scripts are preserved; the adapter
returns a pinned command for composition rather than taking over setup.

Apple Git lacks named hooks. The fallback covers an installed repository and
its approved linked worktrees. Future clones require direct or repository-boundary approval and
startup/prelaunch readiness. The user-level startup adapter and physical clone-boundary policy are exercised by the MASK-0081 fixtures. Named hooks were subsequently exercised on ExampleWinHost with its existing Git 2.55.0.windows.3; no Git upgrade was performed.

Windows readiness acceptance passed on ExampleWinHost after the native fixes below.
The [station registry](remote-stations.md) records its setup and runtime limits.
No credentials, privileges or host trust were changed. First-prompt skill
loading remains unverified on both platforms; the accepted host boundary is
explicit prelaunch plus separately tested adapter protocol behavior.

No live project/personal skill deployment, host configuration or Git hook was
changed. Test-created roots were cleaned by their TemporaryDirectory fixtures.
The failed initial filesystem query against a directory was replaced by the
successful query against that directory's mounted device; it was not a failed
product acceptance check.

## Integration verification

At runtime revision `3a8182f`, `python3 -B -m unittest discover -s tests` ran 123 tests in 149.665 seconds: 119 passed, three skipped, and one hook-installation recovery test failed. MASK-0082 fixes the reused path variable responsible for that failure, removes unused-package requirements from inactive cleanup recovery, validates new-installation interpreter authority, and covers registered nested projects during Git events.

After those changes, `python3 -B -m unittest tests.test_git_integration tests.test_ensure tests.test_workspace_lifecycle tests.test_host_integration` ran 33 tests in 47.140 seconds; all passed. The previous affected recovery/integration pass also ran 29 tests successfully. Unchanged passing full-suite evidence is retained; the full suite was not repeated.

## Native Windows boundary

Verified on September 5, 2026 (September 6 UTC): Windows 11 Home
10.0.26200, AMD64, NTFS, Python 3.14.6 at
`C:\Program Files\Python314\python.exe`, Git 2.55.0.windows.3, Claude Code
2.1.259 and Codex CLI 0.153.4 for the public launcher probe. The Codex sandbox
also exposed a separate 0.153.3 executable; it was recorded separately, not
reported as the launcher-selected host.

At `3456e3954b51fa3fefa5a5c7072d4ab7067409f3`, the station ran 35 focused tests:
26 passed, four failed, two errored and three skipped. The app's inconsistent
Remote/SSH status initially obscured progress, so a direct SSH fallback also
ran the same modules plus the native missing-privilege mapping test: 36 tests
in 104.003s, 28 passed, three failed, two errored and three skipped. These are
failed initial passes, not complete acceptance. No full application suite was
run again.

Revision `c03f85c` fixes Windows separator comparison in worktree retirement,
accepts Git's appended event arguments on the fixed hook entrypoint, and tolerates
LF/CRLF checkout conversion when comparing schema contracts. It also restores
exact bytes in the recovery fixture and uses portable shell quoting for the
marker-hook fixture. Substantive schema and protocol changes still refuse.

The affected native recheck was:

```powershell
$env:PYTHONUTF8 = '1'
$env:PYTHONDONTWRITEBYTECODE = '1'
& 'C:\Program Files\Python314\python.exe' -B -m unittest -v tests.test_workspace_lifecycle tests.test_git_integration tests.test_launcher
```

At `c03f85c`, 17 tests ran in 88.489s: 16 passed, one skipped (the legacy-directory
collision case on named-hook-capable Git). This covers named checkout, worktree,
merge and manual-merge events; configured/directory hook suppression; inactive
cleanup and recovery; preservation of unavailable worktrees; and native launcher
and self-update behavior. macOS rechecks passed all 17 tests in 40.227s; after
strengthening the CRLF/schema-change fixture, that case passed in 4.843s.
Unchanged passing ensure and host-protocol evidence from the initial passes is
retained.

The station's separate disposable public probe installed `mask.cmd` in a
spaced/Unicode path, approved and ensured a declared project, checked native
symlinks and readiness, and launched both actual host executables with
`--version`. Both returned successfully. The existing Windows privilege was
sufficient for real directory symlinks; the native WinError 1314 refusal mapping
fixture also passed. No privilege was removed or granted to manufacture a result.
No model session, first-prompt discovery or host trust enforcement is claimed.

The station's original artifacts are under its ignored
`.mask/generated/implement-rfc/windows-acceptance/`; this report and the card
record the consumed results. The station checkout and workflow-source checkout
are retained for the owner's requested station. The separate direct-test clone
and transfer archives are removed after consumption. The owner-created manual
clone is untouched.

Final bookkeeping verification after the closeout move: 17 RFCs, 82 cards,
zero structural violations; the RFC-MASK-0006 queue has nine selected cards,
all Done. The pre-finish structure check correctly rejected terminal RFC status
while its closeout card was still In Progress; the completed move resolved it.

Consumed temporary roots:

- `C:\Users\example\AppData\Local\Temp\mask-windows-acceptance-tddvb6ly`:
  direct test clone, transferred bundles/archive and captured logs; removed after
  confirming no Python process referenced it.
- `/tmp/mask-windows-acceptance-tddvb6ly`:
  SSH command helpers, transfer files, copied logs and consumed finish decisions;
  removed after recording their results here and in the Done cards.

## Native Windows lane for setup and readiness entrypoints (RFC-MASK-0019)

Run on September 9, 2026 over the existing `example-win-host` SSH connection to
ExampleWinHost: Microsoft Windows 11 Home 10.0.26200, AMD64, Windows Python 3.14.7 at
`C:\Users\example\AppData\Local\Python\pythoncore-3.14-64\python.exe`, Git
2.55.0.windows.3 with the host's global `core.autocrlf=true`. The lane used a
disposable clone of a transferred Git bundle under
`%TEMP%\mask-m7b-lane\repo`; the registered station checkout
`C:\code\git\ManageAgentSkills-win-example-win-host`, the owner's other checkouts and the
real user profile were not touched (fixtures point `USERPROFILE`/`MASK_HOME`
at temporary roots). No credentials, privileges or host settings changed.

```powershell
$env:PYTHONUTF8 = '1'; $env:PYTHONDONTWRITEBYTECODE = '1'
& 'C:\Users\example\AppData\Local\Python\pythoncore-3.14-64\python.exe' -B -m unittest -v tests.test_setup tests.test_readiness_entrypoints
```

At `98bca4d`: 26 tests in 118.310s, 19 passed, one failed, six skipped. All
`tests.test_setup` non-terminal cases passed natively (JSON/check/dry-run/yes/event
invocations run nothing; exact `--expect-plan-hash` plus `--allow-setup` runs,
validates, publishes and rechecks; stale plan, timeout, overflow, invalid
outputs, post-run input changes, crash after launch, crash during publication,
tampered transaction id, refused journal, check-mode guard). The five
`TerminalSetupTests` cases skip on Windows (POSIX pseudoterminal mechanics) and
the `launch` fake-executable case skips; native Windows console consent and
native `launch` refusal remain open. The one failure,
`LegacyUpdate.test_update_adds_renames_and_converts_roles_from_the_candidate`,
was a fixture defect: the author clone and the shared-source checkout received
CRLF-converted role assets under `autocrlf`, so their declared fingerprints no
longer matched (`workflow.invalid`, `runtime/roles/claude/rfc-explorer.md`).
MASK refused rather than deploying converted bytes, which is the intended
behavior; the fixture now publishes `* -text` in `.gitattributes` like a real
package must, and the guide records that requirement.

At `3a26149`, `tests.test_readiness_entrypoints` reran on the same host from the
clean detached checkout: 6 tests in 28.951s, 5 passed, 1 skipped (`launch`).
After the review-driven hardening of the stage/journal write order, both modules
reran from a fresh disposable clone at `7ff6192`: 26 tests in 126.382s, 20 passed,
6 skipped (the same POSIX-only cases), no failures. macOS reruns at `7ff6192` pass.
One fixture root (`mask-public-*`, nearly empty) survived its TemporaryDirectory
cleanup after the first Windows run and was removed by hand; the final run left
none. The disposable clone, bundles, scripts and logs on ExampleWinHost were removed
after these results were recorded.

## Real implement-rfc package qualification (RFC-MASK-0019, MASK-0092)

Run on September 9, 2026 against the real AgentSkills package at
`154025bdd374a448a0aaa9742703d6459d64be2e` (ASK-0059 Done; descriptor
`skills/implement-rfc/mask-workflow.json`, sha256
`9575dc4fa8a69900236bd8d68634fdca5759124d91acf3cf8c22c6e83e4d70f1` as committed;
16 generated roles, one `prepare-roles` action). The retained evidence driver is
`scripts/qualify_real_package.py`: it runs only public MASK commands as
subprocesses with a private `MASK_HOME`/`HOME`/`USERPROFILE`, clones AgentSkills
into a disposable upstream plus a disposable source clone (the real checkout is
never edited), and builds two consumers with real `project.json`/`project.md`
(distinct `role_addenda`; the second also carries the optional
`execution-selection` input). No helper renders a role; the upstream
`generate_roles` is imported read-only at the very end to compare deployed bytes.

| Lane | Host | MASK revision | Result |
|---|---|---|---|
| macOS | macOS 26.6.2 arm64, Python 3.14.7, Git 2.50.1 (Apple Git-155) | `c6431a1` (first run at `cd4bc55` with the route fix uncommitted) | 44/44 steps |
| Windows | Windows 11 Home 10.0.26200 on ExampleWinHost over `example-win-host`, Windows Python 3.14.7, Git 2.55.0.windows.3 (`core.autocrlf=true`), disposable clone under `%TEMP%\mask-m8-lane` | `c5de2ca` | 44/44 steps |

Steps, in order: `skill validate implement-rfc` (fingerprint
`sha256:7ff27a61692d396346221f8d14e7f0618a39618f446be8df01cc26b215ebc116` on
macOS); first `ensure` exit 4 `workflow.incomplete` with all 16 roles
`setup_required`, links committed, no role files, no package code; upstream
`workflow_preflight.py --mask mask.py` `incomplete` with 16 blockers; `doctor
--check` exit 7; `launch --agent codex|claude` exit 4 with a fake host on PATH
(POSIX script on macOS, a copy of `cmd.exe` as `codex.exe` on Windows) never
invoked, in JSON and human mode; `--check`, `--dry-run` and `--event startup`
with the exact `--expect-plan-hash` plus `--allow-setup
legacy/implement-rfc:prepare-roles` grant report `not_run`; `--yes` alone
`consent_required`; a closed-stdin human `ensure` exits 4 without a prompt and
discloses "not sandboxed"; a wrong hash is `plan.stale`; a foreign action grant
runs nothing; the exact grant runs the frozen entrypoint and publishes 16 roles
plus `native-roles.lock.json` with the stage removed; every role then reports
its configured route (`claude-fable-5-1`/`low`, `gpt-6-astra`/`low` for the
integrator) with `host_load: not_verified`; the preflight is `ready`; no
`__pycache__` appears under the consumer or source; the unchanged rerun is
`ok`, `changed=false`, no setup proposal; `launch` then invokes the fake host
(`data.host.exit_code` 0); the second consumer's request lists
`execution-selection` with its sha256, its addendum appears only in its own
roles and the two consumers' bytes and locks differ; `doctor --check` exits 0
with both complete; the second consumer commits its roles and lock (with
`.gitattributes -text` entries), and a fresh clone passes `ensure --check` and
`ensure` as `repository-owned` with no setup proposal and tracked bytes
unchanged, while `project unrequire` plus `ensure` on that clone removes links
only; an edited role is reported `modified` and preserved (`doctor --check`
exit 7); `project unrequire` plus `ensure` on the first consumer removes the 15
unchanged managed roles and preserves the edited one with `native_role.released`;
a committed change to `SKILL.md` (a declared package input) in the disposable
upstream makes `source fetch` plus `update` exit 4 `workflow.incomplete` with the
roles back to `setup_required` and nothing run, after which a fresh consented
`ensure` completes again; the deployed bytes equal the upstream generator's
output for that consumer.

An earlier driver run used a consumer token that the package's own
`project.json` schema rejects; MASK reported `setup.failed` (exit 5, script exit
status 2, "nothing was published", stage discarded) and never retried, which is
the real package's bounded failure path.

Terminal consent journeys with the real package (a third consumer, `gamma`,
prepared by the driver's `--console prepare` mode):

- macOS pseudoterminal: `n` exits 4 with "declined; nothing ran" and no role
  files; `y` runs, validates and publishes 16 roles and the lock in the same
  invocation (exit 0) and the following `ensure --json` is `ok`, `changed=false`,
  no setup, all roles `ok`.
- Windows console, natively: the same `ensure` was typed into an interactive
  PowerShell started from an SSH session with a pseudoterminal (Windows OpenSSH
  ConPTY), so MASK saw a console on all three streams and asked `Run this setup?
  [y/N]`; `n` exited 4 with nothing run, `y` exited 0 with 16 roles and the lock
  published (`granted by prompt`), and the verification `ensure --json` was `ok`,
  `changed=false`, no setup, all roles `ok`, staging empty.

Findings fixed during qualification: a lock-vouched generated role reported an
empty configured route after publication (`c5de2ca`); a plainly quoted Claude
frontmatter scalar was reported with its quotes and the declined setup note read
"declined; declined" (`c6431a1`, display only; the Windows lane and console
journeys predate these two and show the earlier text).

Limitations. Fresh-host discovery/loading of the deployed roles was not
observed on either platform (`host_load: not_verified` throughout). The real
package has only the `baseline` routing profile, so the "explicit route
override" is limited to the optional `execution-selection` input being observed
and bound; no non-baseline route was renderable. The static no-script path and
the crash/journal recovery paths keep their synthetic-package evidence
(MASK-0088/MASK-0089); the real package is generated-only. On the `autocrlf`
Windows host the AgentSkills clone itself is checked out with CRLF (that
repository carries no `.gitattributes`), so the descriptor digest and lock
digests there differ from the macOS values; MASK stays consistent within a host
and would report a lock made on the other host as stale rather than accept it,
but a portable lock across mixed line-ending hosts needs the publisher to mark
its package inputs `-text` (recorded for AgentSkills, not fixed here). The
Windows fake host is `cmd.exe`, so only invocation versus refusal is observed.
The ExampleWinHost lane directory, bundles and scripts were removed after the results
were recorded; the registered station checkout (`3456e39`) and user profile were
not touched. Two older `mask-native-*` temporary directories from earlier lanes
remain in that `%TEMP%` and were not created by this run.
