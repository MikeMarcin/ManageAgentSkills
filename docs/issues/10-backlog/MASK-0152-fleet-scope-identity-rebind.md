---
schema: "implement-rfc.card.v1"
id: "MASK-0152"
title: "Carry a reviewed directory rebind into the fleet scope binding"
status: "Backlog"
rfcs: []
depends_on: []
metadata: {"requested":"2026-11-10","origin":"Field report on macOS, MASK 0.3.0, following MASK-0115"}
---

# MASK-0152: Carry a reviewed directory rebind into the fleet scope binding

## Evidence

Field report, 2026-11-10. The machine is a macOS fleet controller that is also
an enrolled device. After a restart, `st_dev` for the data volume changed from
`16777231` to `16777232`. Every inode was unchanged.

- 20 scopes (the personal scope and 19 projects) refused `*.identity_changed`.
  `mask register --rebind` from MASK-0115 recovered each of them.
- Before the rebind, `mask fleet upgrade --all --all-devices --dry-run` reported
  18 of this device's enrolled scopes as `project.identity_changed` or
  `user.identity_changed`.
- After the rebind, the same preview reports all 19 available enrolled scopes
  on this device as `fleet.scope_changed`, "The enrolled consumer directory
  identity changed." They stay blocked when the plan is applied.
- The nineteenth scope already reported `fleet.scope_changed` before the
  rebind. That is consistent with an earlier renumbering, but its cause was
  not captured.

`mask_fleet.bind_authority` stores each scope's `root_identity` in the device's
`fleet/authority.json`. `mask_fleet.local_scope` refuses when that value differs
from the registration's `root_identity`. `mask_identity.rebind` rewrites
`state.json` and `integration.json` only, as its preview's `files` list shows.
The reviewed rebind therefore creates the mismatch it leaves behind.

The controller's stored binding holds no `root_identity`; `public_authority`
strips it. The mismatch is local to the device.

The only public recovery today is a new grant: a policy at a higher epoch
through `fleet device authorize`, then a new controller binding through
`fleet device enroll`. That is a full authority review for a change that grants
nothing new. MASK-0115 established that `st_dev` is not stable across boots on
macOS, so a routine restart removes the device from fleet rollout and upgrade
until its grant is reissued.

## Bounded work

Choose one of these and record the decision in the state-and-recovery
architecture doc:

- `register --rebind` also updates the matching fleet scope `root_identity`
  under the same reviewed plan. The preview lists the fleet control among its
  `files` and the plan hash binds its before and after values.
- Or a separate reviewed device-local step applies the same guards to the fleet
  scope binding.

Either way:

- The step applies only when the canonical path and inode match and the device
  number differs. A replacement inode still refuses `fleet.scope_changed`.
- No action, source, scope or grant is added. The epoch and the signed public
  authority stay the same, so the controller binding needs no new enrollment.
  If the design finds that the descriptor must change, say so and document the
  required review instead.
- The recovery guide's device-number section covers the fleet step.

## Acceptance

- AC1: A fixture simulates a changed `st_dev` with the same inode on an enrolled
  device scope. Record that rebind followed by a fleet upgrade preview reports
  `fleet.scope_changed` before the fix.
- AC2: After the chosen recovery, the same preview plans or reports that scope
  without a new epoch or controller enrollment, and the device descriptor's
  authority is unchanged.
- AC3: A directory deleted and recreated at the same path still refuses.
- AC4: The preview discloses the fleet control it will change, and a stale
  preview refuses `plan.stale`.
- AC5: Docs describe the recovery.

## Related observations, outside this card

These came from the same recovery. File them separately if they are wanted.

- Each rebind rewrites `state.json`, so previews taken together go stale. The 20
  scopes needed 20 sequential preview and approve pairs; `register --rebind` has
  no aggregate form.
- The tap cache refused `source.cache_invalid` for the same renumbering and
  needed `tap repair-cache` and a fetch. That recovery is documented and
  deliberate.
- `repair --all` and `upgrade --all`, with or without `--independent`, refused
  with `project.unavailable` and produced no plan while two registered
  worktrees no longer existed.
