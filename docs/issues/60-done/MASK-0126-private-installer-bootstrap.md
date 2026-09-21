---
schema: "implement-rfc.card.v1"
id: "MASK-0126"
title: "Repair private-repository installer bootstrap"
status: "Done"
rfcs: []
depends_on: []
priority: "P0"
metadata: {"field_report":"Unauthenticated raw GitHub installer URLs return 404 for the private repository; the Windows recipe also launches a separately blocked powershell.exe."}
acceptance: [{"criterion":"AC1: authenticated private downloads and current-shell PowerShell recipe","outcome":"pass","revision":"0284075fcba134b18d2591b23a6e8697a54a8535","evidence":{"kind":"observation","detail":"GitHub reported the repository PRIVATE; unauthenticated raw installer URLs returned 404, authenticated gh api downloads succeeded on Windows and WSL, and README/install.ps1 no longer invoke powershell.exe or ExecutionPolicy Bypass."}},{"criterion":"AC2: authenticated default clone and explicit repository override","outcome":"pass","revision":"0284075fcba134b18d2591b23a6e8697a54a8535","evidence":{"kind":"command","detail":"tests.test_installer passed the default gh repo clone shim and MASK_REPO override on native Windows and WSL; both installers now print the current mask tap agentskills URL command."}},{"criterion":"AC3: native disposable installer and README verification","outcome":"pass","revision":"0284075fcba134b18d2591b23a6e8697a54a8535","evidence":{"kind":"command","detail":"Windows tests.test_installer: 2 passed, 4 platform skips; WSL tests.test_installer: 4 passed, 2 platform skips; tests.test_readme_journeys: 5 passed in 222.512s; documentation gate: 23 RFCs, 126 cards, 0 violations; PowerShell and normalized sh syntax checks passed."}},{"criterion":"AC4: explicit WSL protocol/schema update recovery","outcome":"pass","revision":"0284075fcba134b18d2591b23a6e8697a54a8535","evidence":{"kind":"observation","detail":"The clean WSL program checkout advanced from 0b2e41f to cff275d through a one-off existing gh credential helper. The owned launcher needed no rewrite; mask --version is 0.3.0 and mask update --dry-run --json reports program status current with no consumer or MASK-state change."}}]
---

# MASK-0126: Repair private-repository installer bootstrap

## Objective and owned paths

Make the documented one-line install path work for the repository's actual private
visibility on macOS/Linux and Windows. Own `install.sh`, `install.ps1`, `README.md`,
`docs/guides/installation.md`, and focused installer/README tests.

## Acceptance

- **AC1:** The README and installation guide use authenticated GitHub CLI downloads
  for the private repository. The Windows recipe executes in the current PowerShell
  session and does not launch `powershell.exe` or require an execution-policy bypass.
- **AC2:** With no `MASK_REPO` override, both installers clone the private program
  through authenticated `gh repo clone`; an explicit repository override remains the
  deterministic fixture/fork path and uses ordinary Git.
- **AC3:** POSIX and native Windows tests execute the installer against disposable
  local bare remotes, prove install and in-place update, and leave the real profile,
  MASK home, and checkout untouched. README text and documentation validation pass.
- **AC4:** The installation guide explains that `source.candidate_invalid` is the
  intentional boundary for protocol/schema changes and directs the user to rerun
  the installer. The reported WSL 0.2 checkout is advanced explicitly to 0.3, its
  launcher remains owned, and `mask update --dry-run --json` reports the program
  current without changing a consumer.

No publication, repository visibility change, credential setup, PATH edit, elevation,
or real consumer migration is authorized.

## Run record

- GitHub reports `MikeMarcin/ManageAgentSkills` as private; unauthenticated raw URLs
  for both installers returned HTTP 404, while authenticated `gh api` downloads
  succeeded on Windows and WSL.
- `python -B -m unittest -v tests.test_installer` passed both native PowerShell
  cases on Windows (four POSIX skips). The same module under WSL passed all four
  POSIX cases (two Windows skips). Both platforms exercised install, update, the
  explicit local-repository override, and the default authenticated `gh repo clone`
  route through disposable bare remotes.
- `python -B -m unittest -v tests.test_readme_journeys` passed all five README
  text and public CLI journeys. `python scripts/verify_documentation.py --root .`
  reported 23 RFCs, 126 cards, and zero structural violations. Native PowerShell
  parsing and normalized POSIX `sh -n` parsing passed.
- The reported WSL installation was a clean 0.2.0 checkout at `0b2e41f`, 35 commits
  behind. It was explicitly fast-forwarded to `cff275d` with the existing `gh`
  credential helper, without changing Git credential configuration. `self install`
  found the owned launcher already current; `mask --version` now reports 0.3.0 and
  `mask update --dry-run --json` reports program status `current`. No consumer or
  MASK state was changed.
