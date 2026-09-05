---
id: MASK-0013
title: Verify noninteractive and partial-update boundaries
status: Done
rfc: RFC-MASK-0003
depends_on: ["MASK-0011", "MASK-0012"]
---

# MASK-0013: Verify noninteractive and partial-update boundaries

## Objective and owned paths

Own subprocess policy, fake-helper tests and any contained corrections to updates.

## Bounded work

Exercise hanging Git/helper process trees, remote ref changes between preview/apply, filter/hook boundaries, auth refusal, output redaction and source-advance-before-link-failure. Record no-effect versus partial state accurately.

## Acceptance

No continuing mutator is labeled safely stopped; no timeout/collision converts into a blind retry; pending state survives indeterminate failures. No live credentials needed.

## Focused verification

`python -m unittest tests.test_subprocess_policy tests.test_git_update tests.test_recovery` with targeted selectors.

## Run record

macOS: subprocess/Git/recovery modules 17 PASS; added checkout-failure selector PASS; manifest-registry 5 PASS after guard correction (an initial mistyped test module was corrected). Fake authentication output is redacted; repository selector environment is sanitized; spawned helper cannot write after timeout; repository post-merge hook suppressed. Frozen remote movement, directory case collision, symlink candidate, divergence, unavailable consumer, post-advance and checkout failure preserve boundaries and journals. Native Windows affected checks also run for final platform evidence. Narrow diff review passes. Commit: this Done move.

Critical review: native collaboration reviewer inspected immutable f2349ca (same model family; opposite-family runtime unavailable). Two confirmed findings: mid-apply manifest overwrite and directory-component case collisions. Both corrected in c5853d9, with direct regressions in this card. No unresolved review blocker; review was bounded to ownership/recovery/source-update changes. Review fixture files were removed.
