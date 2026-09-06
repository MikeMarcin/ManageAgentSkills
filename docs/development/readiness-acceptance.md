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
