---
schema: "implement-rfc.card.v1"
id: "MASK-0126"
title: "Repair private-repository installer bootstrap"
status: "Ready"
rfcs: []
depends_on: []
priority: "P0"
metadata: {"field_report":"Unauthenticated raw GitHub installer URLs return 404 for the private repository; the Windows recipe also launches a separately blocked powershell.exe."}
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

No publication, repository visibility change, credential setup, PATH edit, elevation,
or real consumer migration is authorized.
