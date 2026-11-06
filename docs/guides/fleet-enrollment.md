# Enroll a device for MASK fleet transport

The controller can verify the identity, authorization and current capabilities of
a device over SSH. The device can reconcile a registered scope against its exact
local lock and sign the outcome. A separately granted rollout scope can also
accept approved fleet contributions. See the [rollout guide](fleet-rollouts.md).

## Prepare identities and a device grant

Use installed MASK and Python on both machines, a working direct OpenSSH login
to the device, and compatible OpenSSH `ssh-keygen`. Use a distinct local ED25519
signing key for each role. OpenSSH must be able to read that key noninteractively.
Keep each private signing key with its role. The existing SSH login identity is
separate.

On the controller, initialize its identity. On the device, initialize the device
identity and register the project or personal scope with the ordinary MASK CLI.

```sh
# Controller
mask fleet controller init operator --signing-key /absolute/controller-key
mask fleet controller show --json

# Device
mask fleet device init laptop --signing-key /absolute/device-key
mask fleet device authorize --policy device-policy.json --dry-run --json
mask fleet device authorize --policy device-policy.json --approve-plan HASH
mask fleet device descriptor --json
```

Create the policy file locally on the device. It is an object with
`schema_version` set to `1`, `controller` set to the verified controller
`data.identity` object, and positive integers `epoch` and `minimum_sequence`.
Start a new grant at epoch and sequence 1. Use a strictly higher epoch to change
or restore a grant. Set `actions` to a list of allowed RPC actions. A controller
that enrolls and probes over SSH needs `capabilities`.

Set `scopes` to an object keyed by your chosen aliases. Each scope has `scope`
(`user` or `project`), `root` (an already registered absolute local path), and
`sources`. Each source is keyed by the approved tap name and has `repository`
(the exact canonical credential-free repository identity) and `forward`
(`true` only if the device may receive private package bytes from that source).
Use an empty object for scopes or sources when granting only capabilities or
when there are no applicable sources. The device binds the registered physical
identity locally. Add `"rollout": true` to a scope to permit the controller to
change its fleet-owned profile. That grant also needs `inspect`, `prepare`,
`apply`, and `receipt` in `actions`. Use one rollout alias per physical scope.
The descriptor omits the physical consumer paths and key files.

For `fleet upgrade`, grant the actions `upgrade-inspect` and
`upgrade-apply`, and add `"upgrade": true` to each allowed scope. Give an
eligible project scope `"commit": true` to allow a canonical controls commit
or its propagation. Use one upgrade alias per physical scope. Updating a
fleet-owned contribution also requires the rollout grant.

For `fleet update`, grant `program-inspect` and `program-update` and set the
top-level `program_origin` to the canonical repository identity of the device’s
MASK checkout. The controller must use the same program origin. A program
grant can use an empty `scopes` object. Change the epoch and review the device
policy and controller binding again when adding maintenance grants.

### Delegate tap management

Add `tap-inspect` and `tap-apply` to `actions` alongside `capabilities`. Add a
top-level `tap_management` object such as this one.

```json
{
  "repositories": ["ssh://git@git.example.com/owner/skills.git"],
  "namespaces": ["https://github.com/your-org"],
  "scopes": ["personal"]
}
```

Supply at least one exact canonical network repository or forge namespace.
Namespace grants use HTTPS identities on GitHub, GitLab, Bitbucket or
Codeberg and match complete, case-sensitive path components. A namespace can
include nested groups. It covers repositories beneath that path, so grant
only a namespace you trust to supply skills. Omit either repository list if
unused. An empty `scopes` list delegates catalog management alone.

Name existing scope aliases to make fleet-owned taps from this grant
available to their existing rollout and upgrade permissions. Package bytes
are acquired using that device’s own Git transport and credentials. A
delegated source never enables forwarding. An explicit static grant for the
same alias takes precedence.

Review the policy on the device and its binding on the controller once.
Subsequent tap operations within that policy use the existing enrollment.

## Review the SSH binding

Create the controller's binding file from the device's verified
`fleet device descriptor --json` output. The file contains:

- `schema_version` set to `1`, and `device` and `authority` copied from `data`.
- `host_key` set to the independently verified server public key in
  `ssh-ed25519 BASE64` form, without the comment.
- `launcher` with `python` (the device's absolute native Python executable),
  `program` (the device's absolute installed `mask.py`), and `home` (the device's
  absolute `MASK_HOME`). Use native paths. Spaces and Unicode are supported.

Use a direct OpenSSH config alias. The optional `--ssh-config PATH` selects
a specific local alias configuration. MASK pins the resolved host, login, port
and host key for the reviewed binding. The preview contacts that endpoint and
authenticates its signed descriptor. Review the shown fingerprints and policy
before applying the hash.

```sh
mask fleet device enroll laptop --ssh-config-alias laptop --binding laptop.json --dry-run --json
mask fleet device enroll laptop --ssh-config-alias laptop --binding laptop.json --approve-plan HASH
mask fleet device list
mask fleet device show laptop
mask fleet ping --all
mask fleet capability --device laptop
```

The transport uses existing noninteractive OpenSSH public-key authentication.
MASK copies only authentication references from the alias into the invocation.
Each connection uses an isolated known-host pin, disables forwarding and opens
a fresh connection. Endpoint or key changes require explicit review. Probes can
run in parallel with `--parallel 1` through `--parallel 16` (default 4), and
`--timeout` bounds each SSH invocation in seconds.

On the controller, preview and approve `mask fleet device revoke laptop` to
withdraw its binding. On the device, preview and approve
`mask fleet device revoke-controller` to withdraw that controller's grant at the
device itself. Re-enrolling a revoked identity requires a newer device grant.

## Effects and recovery

The device runs its ordinary planner against the authorized local scope.
`prepare` retrieves exact approved commits with the device's Git credentials
or accepts explicitly allowed, digest-checked files for its existing lock.
`apply` requires the prepared generation and matching local plan. It uses MASK's
usual writer lock and filesystem journal. Package setup remains a local reviewed
action. Exact preparation may retain verified content outside discovery.

If delivery times out, query the device using the operation ID and signed intent
digest. A complete deployment can produce its durable signed receipt after
the connection is lost. A partially applied local journal reports recovery
required, and ordinary `mask recover` can inspect it. A receipt describes the
filesystem, effective agent bindings and package digests observed on the device.
Agent discovery and current session loading are separate observations.

See the [wire contract](../architecture/cli-contract.md#fleet-rpc) and the
[native verification record](../development/fleet-native-acceptance.md).
