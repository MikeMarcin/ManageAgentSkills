# Local BetterLeaks verification

MASK-0145 / local-integration, mandate `local-betterleaks-v1`,
coordinator-implementer recipe revision 2.
Baseline: `ff24d8a4f1221d1ebad5f4a72ad089378fe4fe19` on main.
Source integration: `a7a5323f74d939702fb9a6016797a72ac96341b7`.
Corrected source candidate: `5833457ff10d710a89ceb2b2fbca2b86448d0890`.

| Criterion | Actual evidence and result |
| --- | --- |
| AC1 | Explicit setup downloaded official 1.9.0 macOS ARM64, verified archive SHA-256 `83dd7eaab13d44a1e8e347a17064cdef153a1478db473276d41b38d55613d3f2`, and checked the exact binary version. Repeated setup reuses it. A missing binary, synthetic v2 binary and invalid archive checksum fail closed. No setup is called by scans or hooks. |
| AC2 | Eight focused disposable-fixture checks pass with network denied. Direct staged/tracked/history scans at the corrected candidate all exit 0 with zero findings. Fixtures demonstrate clean scans, secret detection with no secret output, partial staging in both directions, untracked-file exclusion, other-ref history detection, shallow-history refusal, config/allow-comment protection and narrow fixture exceptions. |
| AC3 | Actual fixture Git commits are blocked for staged secrets and for Git's alternate index (`commit -a`); clean commits pass. Existing different hooks and custom hooksPath survive refusal unchanged; installation is idempotent. The real checkout hook is executable, matches the owned bytes, ran on both source commits, and passes `git hook run pre-commit` at the corrected candidate. |
| AC4 | Contributor guide and local scanning documentation cover setup, commands and boundaries. Standard unittest discovery still finds 601 cases and zero BetterLeaks checks. `.github/workflows/verify.yml` is byte-unchanged from baseline; no existing test/CI entrypoint was edited. Documentation passes: 24 RFCs, 145 cards, zero structural violations. Whitespace check passes. |

The full focused run after the correction passed all eight checks in 8.711
seconds under `/usr/bin/sandbox-exec -p '(version 1)(allow default)(deny network*)'`.
The strengthened ignore/cwd negative control then passed independently in 2.088
seconds with the same network denial. Its caller cwd is outside the `--repo`
target. Both source ignore filenames cause exit 2 for staged, tracked and history,
preserving file bytes; a caller-cwd ignore alone does not suppress staged detection.
Test-only edits to strengthen that cwd check did not change the product candidate.
No broad MASK suite rerun was warranted by this separate local developer tool.

## Failures and corrections retained

The initial real tracked scan reported four findings and history reported five,
all synthetic URI-password rejection fixtures in three existing test files.
The exception is restricted to the intersection of the URI rule, those exact
files and three literal fake password values. Negative controls retain detection
for the same value elsewhere and for other rule findings in the named files.
No complete test/doc directory is excluded. The first directory export used
absolute paths, preventing that exception from matching; scanning from the export
root with relative paths corrected it, and the fixture check covers both modes.

A strengthened ignore-file negative control subsequently failed at the first
source commit: BetterLeaks 1.9.0 reads a source-directory ignore file even with
an explicit empty ignore path. The wrapper now refuses either source ignore
filename before scanning, preserves their bytes and prints actionable instructions.
The correction commit above and its passing direct negative control supersede
that failure. Inline allow comments are explicitly ignored by the scanner flag.

For comparison, installed Gitleaks 8.30.1 scanned baseline history with forced
default rules, empty ignore, ignored allow comments, full redaction and explicit
archive/decoding depths: exit 0, zero findings, with network denied. This is one
baseline comparison; it does not establish general scanner superiority.

## Scope and cleanup

Native evidence is macOS 26.6.2 ARM64 / Python 3.14.7. Other pinned release targets
remain unverified native platforms. No human or independent acceptance was
required or supplied for this standalone local milestone. The pre-existing MASK
`project.identity_changed` readiness observation remains unresolved and outside
scope; this work does not certify deployment readiness or observed native role
loading from configuration alone.

The installed tool cache and repository-local hook intentionally remain. Temporary
fixture repositories, exported trees, redacted reports and setup scratch space
were removed by their scoped contexts. Sanitized command receipts, the original
negative-control failure, plan binding/check and final ownership/commit identities
are retained under ignored `artifacts/local-betterleaks/`, with `handoff.json` as
the durable return. There is no review server, pending human decision, push,
global configuration change, MASK state repair or other consumer change.

Closeout self-review checked the touched code for unnecessary branching, removed
an unused Git-helper option and simplified the linked-parent check. It also
restricted hook changes to the invoked script's own checkout. Required scanner
output stays private even on failure; the user sees locations and rule names.
