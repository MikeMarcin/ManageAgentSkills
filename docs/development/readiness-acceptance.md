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

Windows acceptance is open. The repository's remote-station registry contains
no station and specifies local implementation. A Windows host/checkout was
requested from the owner; no access, privileges, host trust or enrollment was
changed. The source/pinning milestone depends on the readiness closeout and
cannot be promoted while its required native acceptance remains open.

No live project/personal skill deployment, host configuration or Git hook was
changed. Test-created roots were cleaned by their TemporaryDirectory fixtures.
The failed initial filesystem query against a directory was replaced by the
successful query against that directory's mounted device; it was not a failed
product acceptance check.
