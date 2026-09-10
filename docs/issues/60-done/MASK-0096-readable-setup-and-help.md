---
schema: "implement-rfc.card.v1"
id: "MASK-0096"
title: "Stop futile setup retries and explain CLI tasks and failures"
status: "Done"
rfcs: ["RFC-MASK-0018", "RFC-MASK-0019"]
depends_on: []
priority: "P1"
acceptance: [{"criterion":"RFC-MASK-0018-AC02","outcome":"pass","revision":"3ece9c9","evidence":{"kind":"observation","detail":"Command and argument help coverage, subprocess task help and grouped per-consumer errors passed; obsolete output assertions were updated and rechecked."}},{"criterion":"RFC-MASK-0019-AC03","outcome":"pass","revision":"3ece9c9","evidence":{"kind":"command","detail":"python3 -m unittest tests.test_repair: 9 tests passed, including typed replacement backups, rollback, concurrent edit and symlink preservation."}},{"criterion":"RFC-MASK-0019-AC04","outcome":"pass","revision":"3ece9c9","evidence":{"kind":"observation","detail":"Explicit --repair/--yolo setup authority works without prompts, normal setup consent remains covered by the integrated suite, and check/event paths never run scripts."}},{"criterion":"RFC-MASK-0019-AC01","outcome":"pass","revision":"3ece9c9","evidence":{"kind":"command","detail":"Installed launcher ensure --all --repair made 8/8 scopes ready; follow-up --check had changed=false and doctor --all --check was healthy. 50 backups verified present; no host-loading claim."}}]
---

User-requested correction from the pasted SampleReview ensure/update output.
Baseline: e7c8466. Direct engineering authorized after the required workflow
preflight refused on this checkout's missing readiness approval.

One bounded milestone: prevent setup offers from promising to replace occupied,
unowned destinations; report failures grouped by consumer with actual file paths,
clear effects and actionable recovery; provide task help with scope explanations,
argument descriptions and runnable examples. Preserve JSON structure, ownership,
consent and unrelated changes. No consumer migration or approval changes.

Owned paths: mask_setup.py, mask_workflow.py, mask_present.py, mask.py,
tests/test_setup.py, tests/test_human_output.py, README.md and recovery guidance.
Acceptance: subprocess tests for the reproduced conflict and no repeated setup;
human multi-project errors identify each root; help explains everyday commands
and their scope; focused setup, presentation and parser checks pass.

Mandate amendment: the owner requested a simple option such as
`ensure --all --yolo` to make all registered projects and personal skills work.
Implement `--repair` with `--yolo` alias as explicit setup/replacement authority,
durable backups, independent scope results and no persistent approval changes.
This authorizes the bounded replacement mode beyond ordinary preservation;
normal ensure keeps its existing behavior. Additional owned paths: mask_repair.py,
mask_fs.py, mask_pinned.py, mask_install.py, mask_core.py, tests/test_repair.py,
tests/test_launcher.py, tests/test_task_commands.py, tests/test_workflow_roles.py,
tests/test_readiness_entrypoints.py and docs/architecture/cli-contract.md.
Additional acceptance: direct repair/backup/idempotence, all-project plus personal
selection with continuation after a broken scope, generation failure preservation,
concurrent-edit refusal, crash rollback and unchanged ordinary authority.

## Verification and live result

Implementation: `3ece9c9`. Nine repair subprocess tests pass, including unowned
role backup/replacement, idempotence, a broken first project followed by a healthy
project and personal scope, generator failure, concurrent edits, symlink
preservation, check/event restrictions, crash rollback, static roles and pinned
readiness without persistent approval.

The 96-case integration run covered setup, presentation, CLI protocol, launchers,
readiness entrypoints, native roles, ensure and pinned recovery. Its two failures
were old output-string assertions; both were corrected and the two affected
tests passed together. A separate 34-case output/task/protocol/readiness run
had the same remaining obsolete doctor assertion (33 passed); that assertion
was cleared by the targeted rerun. No unchanged broad suite was repeated.
Logs during the run: /tmp/mask-repair-integration.log,
/tmp/mask-final-output-tests.log, /tmp/mask-repair-final-tests.log.

The owner's all-scope repair mandate was exercised through the installed macOS
launcher: `mask ensure --all --repair --json`. All eight registered scopes became
ready. SampleReview, SamplePlanner, SampleLogs and sample_studio received 46 role
files; 50 exact backups (roles and old locks) remain under ~/.mask/backups with
original-path manifests. The other scopes required no role changes. Follow-up
`mask ensure --all --repair --check --json` returned success with changed=false,
and `mask doctor --all --check --json` returned healthy. No persistent approval,
source selection, credentials, Git push, or consumer Git commits were made.
Preexisting local native-role lock edits and the untracked MASK-0095 card were
preserved. Active host loading remains unverified; restart agents to load changes.

This closes the requested correction only, not the remaining RFC-MASK-0019 native
qualification or any other RFC milestone.
