---
id: "RFC-MASK-0012"
title: "Explicit fleet enrollment, device identity and bounded remote transport"
status: "Accepted"
owner: "MikeMarcin"
created: "2026-09-05"
---

# RFC-MASK-0012: Explicit fleet enrollment, device identity and bounded remote transport

**Delivery stage:** D — enrolled fleet foundation. **Packet status:** proposed implementation contract; no implementation or acceptance is claimed.

**Predecessors:** RFC-MASK-0008, RFC-MASK-0009.

The new behavior below explicitly extends the historical v1 scope. Preserve settled RFCs 0001–0005; update current architecture/user documentation only when the relevant implementation ships. See [source reconciliation](../design/SOURCE-RECONCILIATION.md), [shared contracts](../design/CONTRACTS.md), and [references](../design/REFERENCES.md).

## Decision

Permit MASK to manage the owner's enrolled machines using one local reconciler per device. Begin with on-demand SSH transport and local execution; add pull delivery in RFC-MASK-0013. Do not require a hosted account, new cloud bill, a proprietary central service, or a remotely executing LLM on every device.

The supplied MASK station registry is empty. Existing hardware mentions and historical test hosts are not enrollment records. This RFC does not authorize this pack's author or an implementer to connect to or reconfigure real devices. Real enrollment is an explicit owner action with device-specific preconditions. [M1: docs/development/remote-stations.md]

## Identities and permissions

Each device receives a generated stable device ID, friendly display name, its own signing key/fingerprint, supported MASK protocol/schema versions, declared OS/architecture, enabled agent adapters, and a local mapping of authorized consumer aliases to physical roots. Clone-root boundaries, source approvals and existing personal-home identity remain local.

The controller has a distinct authorization/signing identity. Enrollment pins controller authority, device response identity, transport endpoint/SSH host key and allowed action/scope/source policies. Authentication and authorization are separate: a successful SSH connection does not approve arbitrary source installation or project creation.

Use established OpenSSH transport and file-signature support rather than new cryptographic primitives. The optional fleet module requires compatible installed `ssh` and `ssh-keygen` for this selected backend. Core local MASK stays standard-library Python plus Git. Use separate signature namespaces for intent and receipt. Record exact provider capabilities; an unsupported signing environment is a typed prerequisite, not an unsigned fallback. [E8, E9]

Do not weaken StrictHostKeyChecking, automatically accept a changed host key, copy private keys into Git, or enable agent forwarding. Existing SSH credential configuration can be used after explicit enrollment. A device lost/reinstalled at the same hostname is a new identity until re-enrolled.

## Public operations

```text
mask fleet device enroll NAME --ssh-config-alias ALIAS
mask fleet device show NAME
mask fleet device list
mask fleet device revoke NAME
mask fleet ping [--device NAME | --all]
mask fleet capability [--device NAME | --all]
mask rpc --stdio
```

Enrollment shows local and remote identity and the permitted scopes before accepting the binding. Config changes support dry-run. An ordinary command does not silently install Python, MASK, SSH server software, firewall rules, elevated permissions or credentials. A missing prerequisite yields a focused onboarding step; later automation can execute already-authorized setup but cannot infer it from a skill request.

## Remote protocol

The remote entrypoint is a fixed installed MASK command, not a shell command provided by the package, project, model output or network payload. SSH remote commands are shell-parsed even when the local subprocess uses an argv array; implement platform-specific quoting for a fixed validated launcher, or an enrolled forced-command wrapper. Send request data through bounded framed stdin, never as an interpolated shell expression.

Use `mask.rpc.v1` envelopes with request/operation ID, intended device ID, protocol/schema requirements, action enum, expected desired revision/generation, signed intent digest and typed payload. Initial allowed actions: capabilities, inspect, prepare, apply, receipt, cancel-request. No generic exec, arbitrary file path writes, credential readback or service-management command exists.

Frames have explicit length limits, closed schemas, UTF-8 JSON and no duplicate keys. stdout is protocol only; bounded redacted diagnostics go to stderr. Requests/responses name protocol versions and refusal reasons. The device checks its identity, pinned controller signature, locally granted action/source/scope authority and any expiry before planning.

Each mutation runs through the same local writer lock, validation and recovery machinery as the CLI. A controller-supplied plan hash is not sufficient by itself; the device recomputes local observations. No shared `MASK_HOME` on a NAS, cross-machine symlink, NFS lock, or remote copy of state.json is supported.

## Idempotency and interrupted delivery

An operation ID plus payload digest identifies a request. Repeating the same request returns an existing receipt or resumes only a known safe non-partial phase. Reusing an ID with different bytes refuses. A timeout/lost connection leaves the remote outcome **unknown** until querying that device's durable operation state. Do not kill an SSH transport and infer that a remote mutator stopped; remote execution is bounded separately and journals survive disconnect.

Receipt publication is journal-aware: commit the local operation record and references before acknowledging; if the process dies after deployment but before receipt creation, the next query reconstructs the receipt from the committed operation/desired-state record, not by reapplying blind changes. Duplicate requests never bypass `recovery_required`.

The enrolled device signs receipts containing intent revision/digest, observed package digests and effective scope/agent outcomes. A signed receipt authenticates what the device reported; it is not remote attestation of an uncompromised OS or proof of agent UI loading.

## Content transport

Prefer a device retrieving approved exact commits using its existing read-only Git credentials. If the device lacks source access but enrollment permits content distribution, the controller transfers the selected immutable package plus signed manifest—not its source credentials. Use a bounded content protocol with fixed package-relative paths, explicit lengths/digests and no archive link semantics. Materialize outside discovery and verify before activation.

A public remote URL must not leak unrelated private skill contents. Transport policy and source approval record whether forwarding a private artifact to each enrolled device is allowed. No generic credential vault is needed for this first fleet path.

## Concurrency and native support

Controller fan-out is bounded and configurable (initial default four devices); each device serializes its own effects and permits cheap observational polling. No controller holds a local deployment lock during remote network waits. Independent failures remain isolated and visible.

Test native Windows remote invocation, PowerShell/cmd quoting boundaries, path spaces/Unicode, process exit and noninteractive failure separately from POSIX. WSL is not native Windows acceptance. On macOS test the actual configured executable path and login-shell/PATH independence. Loopback fixture transport proves protocol logic, not real SSH or device enrollment.

## Acceptance criteria

- **RFC-MASK-0012-AC01** — Enrollment binds stable device/controller identities, permitted scopes/sources and host transport identity, and rejects changed/revoked/unknown peers without changing user SSH security settings.
- **RFC-MASK-0012-AC02** — Bounded framed RPC accepts only the fixed action schema; malformed messages, shell metacharacters, wrong device IDs and arbitrary paths cannot invoke generic remote execution.
- **RFC-MASK-0012-AC03** — Each remote mutation uses the ordinary local planner/lock/journal; duplicate operation IDs, changed payloads, disconnects and timeouts produce queryable truthful outcomes.
- **RFC-MASK-0012-AC04** — Exact package transfer validates paths/digests and never forwards credentials or unrelated private content; unavailable authentication remains a prerequisite.
- **RFC-MASK-0012-AC05** — Native Windows/macOS transport and launcher checks record actual host/runtime results, while fixture-only tests remain labelled as such.
- **RFC-MASK-0012-AC06** — Controller/device signing and receipt validation use the established provider with separate namespaces and no unsigned silent fallback for unattended requests.

## Live authorization

Accepted for implementation by the owner’s 2026-09-05 import-and-implement request. Follow the live card dependencies; native and external acceptance remain open until directly exercised.
