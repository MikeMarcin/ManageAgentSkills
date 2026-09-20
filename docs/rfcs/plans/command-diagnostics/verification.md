# Command diagnostic verification

MASK-0123; direct primary implementation and self-review. No delegation or live
skill management. Baseline: `43c984c764e9427060e0d60767bde73da254924a`.

## Acceptance

- AC1: Unknown top-level commands show common examples, troubleshooting commands,
  further help and one plain error. Unknown nested commands show only the relevant
  group's commands and help. The parser supplies structured command context rather
  than a formatted list of every choice. No spelling correction is needed for this
  behavior. Human invocation errors omit the code/state/next diagnostic block.
- AC2: Public subprocess checks preserve exit class 2, empty human stdout, stderr
  diagnostics, the explicit JSON envelope and `--` operand separation. JSON keeps
  the typed invocation error and transaction state. The compact renderer applies
  only to invocation errors without result data, effects or warnings; operational
  failure diagnostics retain their evidence. Values remain sanitized. Only the
  error line receives terminal error color; pipes and NO_COLOR remain plain.
- AC3: The installed launcher was exercised on macOS, including a real terminal
  with TERM=xterm and NO_COLOR absent. Its output matches the public fixtures and
  colors the error line after the usage guide. Source self-review kept presentation
  separate from parser context and transaction behavior. No independent review or
  native Windows verification is claimed.

## Evidence

Runtime logs are under `.mask/sessions/command-diagnostics/`:

- `human-output.log`: 17 checks passed, including new public cases for arbitrary
  unknown commands, the reported misspelling, nested commands, required arguments,
  invalid options, conflicting selectors, control characters, JSON flag placement
  and operand separation. Existing human help/output checks also pass.
- `protocol.log`: five checks passed: the four retained protocol cases and the
  public command-surface/catalog case.
- `color.log`: one check passed, including red error-line placement and NO_COLOR.
- The direct workflow preflight reports ready; this does not establish host loading.
- Documentation validation: 23 RFCs, 123 cards, zero structural violations.
  `git diff --check` passes.

The preflight was initially saved with a `.json` suffix while its output was human
text. An attempted JSON read failed; inspection confirmed the ready human result.
This was an evidence-reading mistake, not a product or test failure. All focused
product checks passed on their first run. No full-suite acceptance is claimed.

The unrelated `.mask.lock.json` edit was excluded from commits. No setup scripts,
upgrades, state edits, publication or pushes were performed.
