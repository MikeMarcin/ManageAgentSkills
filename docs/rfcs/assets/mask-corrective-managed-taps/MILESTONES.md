# Milestones

> Generated from `milestone-plan.json`; edit the JSON, not this view.

Plan: **tap-only-deployment** · Coverage: **complete**

These are integration outcomes, not compulsory agent-launch boundaries.

## baseline

The live-checkout defect is recorded as evidence and a schema-true legacy machine fixture exists for later migration tests.

**Work:** `MASK-0098`

**Prerequisites:** None

**Completion:**

- The closeout card carries the real pre-implementation revision.
- A baseline test proves the current parsers accept the legacy fixture bytes and that a legacy install links into the clone.

**Boundary:** Evidence and fixtures only; no product behavior changes.

## bootstrap

A machine bootstraps from one tap and every test fixture starts that way.

**Work:** `MASK-0099`

**Prerequisites:** baseline

**Completion:**

- tap add on an empty MASK_HOME followed by install deploys a v2 consumer from the store with no checkout on disk.
- The full suite passes on the tap-first fixtures while legacy code still exists.

**Boundary:** Config v3 accepted, init without --source, tap-add bootstrap, fixture cutover; no legacy deletion yet.

## engine

The live-checkout engine is gone and update fetches every referenced tap.

**Work:** `MASK-0100`, `MASK-0101`

**Prerequisites:** bootstrap

**Completion:**

- No link producer can target a Git checkout except source dev-link.
- Retired commands are absent from capabilities and exit 2; legacy configuration exits 4 migration.required.
- update fetches each tap once, isolates failed taps and applies one journal.

**Boundary:** Engine retirement and the new update module; docs and migration follow.

## migration

doctor detects and migrates v1 and v2 machines, projects and personal scopes with recovery.

**Work:** `MASK-0102`

**Prerequisites:** engine

**Completion:**

- The fixture crash matrix recovers with rollback or complete at every checkpoint.
- A machine with an empty registry migrates its configuration only.

**Boundary:** Detection, mapping, journal and refusals from contracts/MIGRATION.md; no real machine is migrated here.

## truth

Help, documentation and capabilities describe only the tap model.

**Work:** `MASK-0103`

**Prerequisites:** engine, migration

**Completion:**

- README recipes replay verbatim through the public CLI.
- The retired-spelling documentation test passes.

**Boundary:** Presentation and documents; no engine changes.

## qualification

The real AgentSkills package and the owner's machine are exercised natively through taps.

**Work:** `MASK-0104`, `MASK-0105`

**Prerequisites:** truth

**Completion:**

- The qualifier passes on native Windows 11 and macOS including push-then-update and the legacy lab.
- The owner's v1 machine is migrated by doctor with the transcript recorded and the clone untouched.

**Boundary:** Evidence gathering; defects return to their owning cards.

## closeout

RFC-MASK-0020 is closed with direct evidence for every criterion.

**Work:** `MASK-0106`

**Prerequisites:** qualification

**Completion:**

- Every acceptance row names a real command or observation, outcome and revision.
- The structure gate reports zero violations and the full suite passes on both platforms.

**Boundary:** Closeout bookkeeping only.
