---
schema: "implement-rfc.card.v1"
id: "MASK-0123"
title: "Show useful human diagnostics for unknown commands"
status: "Done"
rfcs: []
depends_on: []
priority: "P2"
metadata: {"milestone_plan":{"id":"command-diagnostics","path":"docs/rfcs/plans/command-diagnostics/milestone-plan.json"}}
acceptance: [{"criterion":"AC1","outcome":"pass","revision":"80568d4db65333edaa97b4036ed38fffede152af","evidence":{"kind":"observation","detail":"Unknown commands show short examples, troubleshooting and help followed by one plain error. Nested mistakes show relevant group commands. No parser choice dump or transaction field block; no typo correction dependency. See docs/rfcs/plans/command-diagnostics/verification.md."}},{"criterion":"AC2","outcome":"pass","revision":"80568d4db65333edaa97b4036ed38fffede152af","evidence":{"kind":"observation","detail":"Public checks retain exit 2, human stderr, explicit JSON envelopes, operand separation and sanitized text. Operational errors keep effects; terminal error color respects NO_COLOR and pipes. See docs/rfcs/plans/command-diagnostics/verification.md."}},{"criterion":"AC3","outcome":"pass","revision":"80568d4db65333edaa97b4036ed38fffede152af","evidence":{"kind":"observation","detail":"17 human-output, 5 protocol/surface and 1 color checks pass. Installed launcher observed on macOS terminal; documentation gate has no violations. Source-only work preserves unrelated lock edit. See docs/rfcs/plans/command-diagnostics/verification.md."}}]
---

# MASK-0123: Show useful human diagnostics for unknown commands

Owner requests a concise usage guide and plain unknown-command error, like the
provided brew example, instead of argparse's full command-choice dump and technical
result fields. Continue directly. Baseline: `43c984c764e9427060e0d60767bde73da254924a`.

- AC1: Unknown commands show short useful examples and help discovery, plus one
  plain error. No raw command-choice dump, code/state/next field block, or reliance
  on typo correction. Nested command errors give relevant group guidance.
- AC2: Preserve exit class 2, stderr human diagnostics, explicit JSON protocol and
  operand separation. Other usage errors are concise without hiding operational
  failure evidence. Control characters remain sanitized and pipes remain plain.
- AC3: Focused public CLI checks and visual inspection demonstrate the output and
  JSON behavior. Document the result and commit only task-owned paths.

Source and fixture scope only. Preserve the unrelated `.mask.lock.json` edit.
No live upgrade, publication or delegation.

## Closeout

Implementation: `80568d4db65333edaa97b4036ed38fffede152af`.
[Verification](../../rfcs/plans/command-diagnostics/verification.md) records
AC1–AC3, all 23 passing focused checks and the installed terminal observation.
Unknown commands show useful examples and a plain error, nested mistakes show
group guidance, and explicit JSON retains typed diagnostics. Terminal color
highlights the error line; NO_COLOR and pipes stay plain. Operational failure
evidence is preserved. No full-suite or native Windows claim is made.

Closeout review runtime: direct primary self-review; no independent reviewer or
delegation. Task-owned commands are quiescent. The unrelated lock edit remains
uncommitted and no live management changes or publication occurred.
