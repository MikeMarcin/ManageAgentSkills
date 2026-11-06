# Roll out skills from one controller

Use [fleet enrollment](fleet-enrollment.md) to authorize each device and scope.
Each device needs a compatible MASK program, a registered local scope with a
rollout grant, and local approval for the same tap identities. Enrollment and
tap approval happen once per device or when its grant changes.

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

## Install or update

Fetch the approved tap on the controller before reviewing an exact update.
The preview uses the fetched catalog and the frozen enrollment grants.

```sh
mask tap fetch agentskills
mask fleet install agentskills/code-simplifier --mode tap --all-devices --scope user --dry-run --json
mask fleet install agentskills/code-simplifier --mode tap --all-devices --scope user --approve-plan HASH
mask fleet update agentskills/code-simplifier --all-devices --scope user --dry-run --json
mask fleet update agentskills/code-simplifier --all-devices --scope user --approve-plan HASH
```

Use repeated `--device NAME` options for a subset, or `--project-alias ALIAS`
for preauthorized project mappings. Personal rollout leaves project scopes
alone. The fleet owns a separate contribution. Identical local selections can
share a deployment, and an incompatible locally held version blocks that
device. Removing a fleet contribution preserves an independent local choice.

Pass `--mode tap` to use an already approved tap directly. A name or GitHub
tree URL must resolve to one package. In copy mode, supply
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
