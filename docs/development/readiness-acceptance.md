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
startup/prelaunch readiness. The user-level startup adapter and physical clone-boundary policy are exercised by the MASK-0081 fixtures. Configured named-hook execution remains unverified
on a capable Git version; no Git upgrade was performed.

Windows acceptance is open and resumed on ExampleWinHost after the owner identified the
existing SSH connection and requested the implement-rfc station scripts. The
native Windows station and current provisioning limits are recorded in the
[station registry](remote-stations.md). No access, privileges or host trust were
changed. The source/pinning milestone still depends on completed readiness
acceptance; station provisioning alone does not satisfy it.

No live project/personal skill deployment, host configuration or Git hook was
changed. Test-created roots were cleaned by their TemporaryDirectory fixtures.
The failed initial filesystem query against a directory was replaced by the
successful query against that directory's mounted device; it was not a failed
product acceptance check.

## Integration verification

At runtime revision `3a8182f`, `python3 -B -m unittest discover -s tests` ran 123 tests in 149.665 seconds: 119 passed, three skipped, and one hook-installation recovery test failed. MASK-0082 fixes the reused path variable responsible for that failure, removes unused-package requirements from inactive cleanup recovery, validates new-installation interpreter authority, and covers registered nested projects during Git events.

After those changes, `python3 -B -m unittest tests.test_git_integration tests.test_ensure tests.test_workspace_lifecycle tests.test_host_integration` ran 33 tests in 47.140 seconds; all passed. The previous affected recovery/integration pass also ran 29 tests successfully. Unchanged passing full-suite evidence is retained; the full suite was not repeated.
