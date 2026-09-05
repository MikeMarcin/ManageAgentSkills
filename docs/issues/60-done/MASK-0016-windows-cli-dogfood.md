---
id: MASK-0016
title: Verify Windows launcher and agent CLI path
status: Done
rfc: RFC-MASK-0004
depends_on: ["MASK-0015"]
platform: windows
---

# MASK-0016: Verify Windows launcher and agent CLI path

## Objective and owned paths

Own native Windows launcher/end-to-end evidence and contained fixes.

## Bounded work

Execute the actual installed launcher with spaced paths, JSON success/refusal/no-op and exit-code propagation. Verify selected shared skill context through the actual directory links; record host discovery only if observed.

## Acceptance

Windows support is backed by direct native CLI/launcher results; unobserved Claude/Codex loading is not asserted.

## Focused verification

Native Windows focused `tests.test_launcher` and `tests.test_end_to_end`; reuse unchanged symlink safety results from MASK-0008.

## Run record

Native Windows 11 build 26200, Python 3.14.7: final public end-to-end and actual shared-context directory-link scenarios PASS with PYTHONUTF8=0. Native installed mask.cmd passes spaced/Unicode argv, JSON success/refusal, exit 2, no-op and unrelated launcher preservation. Reused 19 earlier safety tests and 20 Git/helper/recovery/launcher tests. Corrected final all-project preflight selector PASS (initial abbreviated selector did not exist). PATH discovery test exposed Windows extension case mismatch; fixed by actual file identity and rerun PASS. Observational project show selector also PASS. No Claude/Codex UI loading asserted. Test-owned remote scratch root removed after consuming results; no native user repositories modified. Commit: this Done move.
