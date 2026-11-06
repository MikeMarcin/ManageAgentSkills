# Roll out skills from one controller

Use [fleet enrollment](fleet-enrollment.md) to authorize each device and scope.
Each device needs a compatible MASK program, a registered local scope with a
rollout grant, and either static approval for the same tap identities or a
central tap grant covering the repository and scope.

## Set up the control repository

Choose a dedicated private Git repository. Give the controller permission to
publish to it. MASK uses the existing noninteractive Git credentials for the
supplied transport. Preview the binding, then approve its plan hash.

```sh
mask fleet control configure ssh://git@git.example.com/owner/desired.git --dry-run --json
mask fleet control configure ssh://git@git.example.com/owner/desired.git --approve-plan HASH
```

The controller publishes a signed, linear history to `refs/heads/mask-fleet`.
Plans bind the control head, exact skill resolution, scope and enrolled device
identities. A competing publication or changed tap resolution requires a fresh
preview. Devices added after approval are excluded from that operation.

## Manage taps centrally

With [central tap delegation](fleet-enrollment.md#delegate-tap-management)
in place, run these commands on the controller.

```sh
mask fleet tap --json
mask fleet tap team https://github.com/your-org/skills.git --dry-run --json
mask fleet tap team https://github.com/your-org/skills.git --approve-plan HASH --json
mask tap fetch team
mask fleet untap team --dry-run --json
```

The default selection is all active enrolled devices. Repeat `--device NAME`
to select a subset. Additions default to ref `main` and package directory
`skills`. Supply `--ref` or `--packages` for a different catalog layout.
Review the exact alias, repository and targets before approving.

An addition also approves the same binding in the controller’s catalog
after at least one device verifies it. A matching local controller tap
is reused with its existing ownership and transport. A conflicting binding
blocks additions. Device-local taps stay independently owned, even if their
repository matches. Each machine continues to choose or pin its own
transport. Tap mutations only change catalogs. Fetch explicitly on the
controller before resolving skills.

Removal requires a fleet-owned, unused tap. A local declaration, lock,
profile or static grant that references the tap blocks removal. A subset
removal retains the controller tap for other devices. A removal across the
active fleet removes an unused fleet-owned controller tap after every selected
device verifies removal. Local controller taps and cached Git data stay in place.

In JSON, inspect `data.complete`, `data.device_results` and
`data.controller_result` after approval. An incomplete operation exits 9.
Retry a lost acknowledgement with the same command and hash. If a device
was offline during preview, review a fresh plan once it returns. Receipts
describe the approved operation. Use `fleet tap` for current catalog state.

## Install a skill

Fetch the approved tap on the controller before reviewing an exact update.
The preview uses the fetched catalog and the frozen enrollment grants.

```sh
mask tap fetch agentskills
mask fleet install code-simplifier --dry-run --json
mask fleet install code-simplifier --approve-plan HASH
```

Bare install selects enrolled active devices and their authorized personal
rollout aliases. Use repeated `--device NAME` options for a subset, or `--project-alias ALIAS`
for preauthorized project mappings. Personal rollout leaves project scopes
alone. The fleet owns a separate contribution. Identical local selections can
share a deployment, and an incompatible locally held version blocks that
device. Removing a fleet contribution preserves an independent local choice.

An unambiguous name from approved taps uses tap mode when no mode was
configured. A GitHub tree URL needs an explicit or configured mode and must
resolve to one package. In copy mode, supply
`--mode copy --into CURATED_TAP` to publish a provenance-bearing copy from an
approved upstream into a separate curated tap with an approved authoring
checkout. The preview shows the exact source ref, parent, package path and
commit to publish. The reviewed commit excludes unrelated authoring changes.
If source publication succeeds and control publication does not, re-preview.
The same exact source commit can be reused while it is still at the approved
ref.

Devices normally acquire the exact commit through their approved Git
transport. Add `--forward` to the preview and approval to permit bounded
package forwarding from the controller. Every source used by the requested
profile must permit forwarding in the device grant.

## Upgrade skills or update the MASK program

```sh
mask tap fetch agentskills
mask fleet upgrade --all --dry-run
mask fleet upgrade --all --approve-plan HASH

mask fleet update --dry-run
mask fleet update --approve-plan HASH
```

Both bare forms select active enrolled devices. Use repeated `--device NAME`
to review a subset. `fleet upgrade` uses the controller's fetched tap catalogs
and explicitly granted scopes. Add `--scope user` or `--project-alias ALIAS` to
narrow the scope. It preserves held versions and existing selections, including
the membership of installed bundles. Setup or role replacement that needs
local review blocks the affected scope. Eligible fleet-owned contributions
advance through the signed desired repository. When the same skill is selected
both locally and by the fleet, the two matching locks can advance together.

Across checkouts with matching starting controls, one eligible attached
checkout commits per repository. Checkouts at its parent receive the exact
commit. Checkouts on another parent receive a cherry-pick with the same control
changes. The bounded transfer covers the control-only commit, and unrelated
staging is preserved. A scope that needs a lock change is blocked if its
controls are dirty or diverged or if it cannot use a canonical commit. When
one of those scopes already matches its own exact candidate, the plan reports
`not_applicable` with reason `fleet.scope_current` and skips the local upgrade,
including repair and any Git changes. Personal scopes never commit.

`fleet update` reviews the exact revision advertised by the controller's
approved MASK origin. Each device needs its own program grant for that
repository and an eligible program checkout. The device fast-forwards through
ordinary MASK recovery and reports the exact Git revision in its signed
receipt. Overlapping local changes, diverged history and incompatible program
contracts block the update. `fleet update SOURCE/ID --all-devices --scope user`
retains the existing single fleet-contribution update.

The previews contact enrolled devices over signed SSH. Program previews read
the approved Git origin and can use disposable Git storage to check an exact
candidate. A maintenance retry with the same approved hash resumes the frozen
scope and uses durable receipts. A device that was offline during inspection
needs a fresh preview once it returns. Exit 9 means a requested effect remains
incomplete. Resolve a device's ordinary MASK recovery before retrying.

## Read the results and catch up

```sh
mask fleet operation show OPERATION_ID
mask fleet operation wait OPERATION_ID --timeout 30
mask fleet sync --all
mask fleet remove agentskills/code-simplifier --all-devices --scope user --dry-run
```

A rollout exits 9 when any selected device remains incomplete, even when the
signed intent and some deployments were saved. The operation ID, device rows
and host-loading status remain available. `show` reads historical verified
receipts and known blockers. `wait` queries outstanding receipts for a bounded
time. `sync` sends the newest approved intent for each scope. The default
authorization window for new application is seven days. Approve a fresh
operation to renew a desired revision after that window.

Use `fleet operation cancel OPERATION_ID --dry-run`, then approve its hash to
withdraw future dispatch of that request. An already dispatched apply can
finish, and verified prior effects remain visible. To remove installed content,
review a separate `fleet remove`. A newer revision can supersede a queued one.
Use `fleet operation rollback OPERATION_ID --dry-run` to review publishing that
operation’s exact profiles again as a new revision. The preview includes the
original frozen devices and all selections in those profiles.
If a device reports recovery required, resolve the ordinary local MASK journal
before retrying. Filesystem verification and running agent discovery are
reported separately.

## Optional device-side convergence

Give the device read access to the desired repository and write access to a
separate receipt repository. Give the controller read access to receipts.
Configure the desired and receipt repositories on both sides, using transport
spellings that resolve to the same desired repository identity.

```sh
mask fleet control configure ssh://git@git.example.com/owner/desired.git --receipts ssh://git@git.example.com/owner/receipts.git --dry-run
mask fleet control configure ssh://git@git.example.com/owner/desired.git --receipts ssh://git@git.example.com/owner/receipts.git --approve-plan HASH
mask fleet sync --local
```

Foreground pull verifies the signed latest desired revision, applies only the
granted scopes and publishes a signed device receipt to the separate store.
Each device uses its own Git credentials for exact source acquisition.

`fleet runner enable --dry-run` previews a current-user scheduler entry.
Use the same command with `--approve-plan HASH` to enable it. The default
interval is 300 seconds. `fleet runner status` reports ownership and next
poll, and `fleet runner disable` previews and removes the owned entry with the
same approval flow. The Windows preview binds the absolute signing executable
the task will use. Native qualification exercised launchd and Windows Task
Scheduler in the current user’s session. Foreground sync works without a
schedule. See the [native evidence](../development/fleet-native-acceptance.md#current-user-native-scheduler-qualification)
for the Windows link-traversal distinction across session types.
