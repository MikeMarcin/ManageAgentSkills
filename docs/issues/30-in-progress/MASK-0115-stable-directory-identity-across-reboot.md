---
schema: "implement-rfc.card.v1"
id: "MASK-0115"
title: "Keep registered directory identity valid when macOS renumbers the volume device"
status: "In Progress"
rfcs: []
depends_on: []
priority: "P1"
metadata: {"origin":"Field report on macOS after pulling 7ccf671 (2026-09-16)","milestone_plan":{"id":"public-source-preview","path":"docs/rfcs/plans/public-source-preview/milestone-plan.json"}}
---

# MASK-0115: Keep registered directory identity valid when macOS renumbers the volume device

## Evidence

`mask_core.identity(root)` records `{device: st_dev, inode: st_ino}`. `registered_root` refuses `*.identity_changed` when that pair differs.

On macOS (APFS), `st_dev` for the Data volume changed from `16777230` to `16777231`, most likely after a reboot. Every inode was unchanged, so these were the same directories.

- 7 of 8 scopes (six projects and the personal scope, `/sanitized-runtime/home`) failed with "Registered directory identity changed." The only one that passed had been registered again after the change.
- `mask list --user` showed every skill as `excluded`, with "no links expected here".
- `mask ensure --all --repair` ended `repair.incomplete` and couldn't fix it.
- `mask project unregister PATH` also refused with `project.identity_changed`, so no public command could recover.
- `mask doctor --migrate` only covers tap identity spellings and reported nothing to do.
- Recovery was a manual edit. After backing up to `~/.mask/backups/device-renumber-20260916-224518/`, 9 identity records in `state.json` and `integration.json` were rewritten to the new `st_dev`, only where the stored inode matched the current directory. After that, `ensure --all --repair` reported 8/8 ready and `doctor --all --check` reported healthy.

`st_dev` isn't stable across boots on macOS, and may not be for network or removable volumes either. The current check treats a routine restart as a directory being replaced.

## Bounded work

Choose one of these and record the decision in the state-and-recovery architecture doc:
- Compare a stable identity: the inode plus a persistent volume identifier, such as the APFS volume UUID from `statfs`/`getattrlist` on macOS or the volume serial number on Windows. Fall back to what's available today.
- Or allow a public, confirmed re-bind when the path resolves to the same place and the inode matches but the device doesn't. For example, `doctor`/`ensure --repair` offers it, or `project register` / `user register` accepts it for an already-registered root.

Either way:
- `unregister` must work for a consumer whose identity changed.
- The approval identities in `integration.json` (`identity`, `common_identity`) follow the same rule.
- A real replacement, where the inode differs at the same path, still refuses.

## Acceptance

- With a fixture that simulates a changed `st_dev` and the same inode, `ensure --all --repair` finishes ready (or with one documented confirmed step) without hand-editing state.
- A directory deleted and recreated at the same path still refuses `*.identity_changed`.
- `project unregister` succeeds on an identity-changed consumer.
- The same fixture covers approval records in `integration.json`.
- Docs describe the recovery.
