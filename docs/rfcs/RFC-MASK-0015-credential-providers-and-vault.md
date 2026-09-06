---
id: "RFC-MASK-0015"
title: "Credential-provider references and an optional encrypted fleet vault"
status: "Proposed"
owner: "MikeMarcin"
created: "2026-09-05"
---

# RFC-MASK-0015: Credential-provider references and an optional encrypted fleet vault

**Delivery stage:** E — optional credential extension. **Packet status:** proposed implementation contract; no implementation or acceptance is claimed.

**Predecessors:** RFC-MASK-0012, RFC-MASK-0013.

The new behavior below explicitly extends the historical v1 scope. Preserve settled RFCs 0001–0005; update current architecture/user documentation only when the relevant implementation ships. See [source reconciliation](../design/SOURCE-RECONCILIATION.md), [shared contracts](../design/CONTRACTS.md), and [references](../design/REFERENCES.md).

## Decision

The first fleet path uses existing Git/SSH credentials independently on each machine, or forwards approved exact artifacts without forwarding source credentials. A shared secret vault is not a prerequisite for “install this on my machines.” Design credential-provider references first; add encrypted shared-secret distribution only as an explicitly enabled extension.

Prefer per-device least-privilege credentials over one widely replicated master token. Never replace a working local Git helper, SSH agent or OS credential manager merely to centralize it in MASK.

## Provider boundary

Machine source/transport policy may reference a named credential **handle**, not a value. Portable profile data may declare a logical credential requirement but cannot select an executable helper, OS key path or secret destination. The device resolves the handle through approved local providers.

Initial provider interfaces: existing Git helper/SSH agent; OS keychain/credential manager through narrowly selected native adapters; optional sealed-vault provider. Capabilities describe availability and noninteractive/unlocked state without returning secrets. APIs are `probe`, `use_for_fixed_operation`, `rotate_binding` and `forget_binding`; there is no agent-accessible generic `get_secret` tool.

Only a small trusted transport helper receives the secret for a fixed allowlisted operation. Keep it off argv, logs, operation/receipt payloads, profile Git and generated shell snippets. Where an external tool only supports a weaker exposure channel, report that boundary or refuse unattended use rather than claiming secrecy. Debug mode does not waive redaction.

## Optional encrypted vault

Use an established encryption implementation such as age as a separately installed pinned provider; do not implement AES/envelope/key-derivation formats by hand in MASK. Encrypt opaque secret payloads to explicitly enrolled recipient keys. Sign the ciphertext/recipient metadata with the vault-authority key in a separate domain from fleet intents. Encryption does not authenticate who approved a secret. [E11]

Store a versioned manifest with secret handle, encrypted blob digest, authorized device recipient IDs, purpose/source restriction, rotation epoch and optional expiration. Avoid exposing meaningful credential names in public paths; the default vault/control store is private. Secret plaintext never appears in the desired selection, source metadata or a receipt.

Private recipient keys stay device-local, preferably protected by a native credential facility. The optional unattended mode must have a deliberate unlock policy; an interactive key prompt cannot silently hang a scheduler. An offline recipient remains pending, and no “rotation completed everywhere” report is produced until relevant receipts establish the configured boundary.

Decrypt in a controlled helper using bounded memory/stdin channels where possible. Memory zeroization is best-effort in Python and external processes; do not promise forensic erasure. If a provider requires a temporary file, create it with platform-appropriate restrictive permissions, avoid shared directories, minimize lifetime, and disclose crash-residue handling. No base64 “encryption.”

## Grants, revocation and recovery

Enrollment into the fleet does not automatically enroll a device for every secret. Grant the smallest purpose/device set explicitly. Revoke a device's authority for future secret distributions and rotate upstream tokens when needed; deleting a recipient from a manifest cannot erase already decrypted/copied secrets from that device. A stolen controller key and a stolen recipient key have different blast radii, which the report must explain.

Rotation is a staged versioned operation: publish new credential binding, verify the intended operation on online devices without echoing the value, preserve an explicit rollback window if the provider allows it, then revoke the old upstream credential only under separate authority. Do not auto-delete or revoke the last working credential based on a stale/offline receipt.

Recovery uses an owner-held recovery recipient or documented provider recovery flow; it is not a private key checked into the vault repo. Test restoring a disposable vault with the recovery recipient, and test refusal without any valid recipient. Loss of all keys means encrypted contents may be unrecoverable; do not imply MASK can recover them magically.

## Scope and test policy

Implement this after core fleet usability. No production credentials or account mutations are required for automated tests. Use temporary keys and synthetic secrets; ensure representative secret bytes never appear in captured stdout/stderr, JSON, reports, Git diff or logs. Add focused native provider tests only on the platforms actually supported. Unsupported providers remain capability-unavailable rather than replaced with plaintext.

## Acceptance criteria

- **RFC-MASK-0015-AC01** — Credential handles remain separate from values, and existing Git/SSH providers keep working without migration or a mandatory shared vault.
- **RFC-MASK-0015-AC02** — An optional sealed provider uses a pinned established encryption/signature implementation and enforces explicit recipient/purpose grants without plaintext in portable data or tool responses.
- **RFC-MASK-0015-AC03** — Locked/unavailable providers, rotation, revoked/offline recipients and recovery-key loss produce accurate outcomes rather than silent fallback or premature completion.
- **RFC-MASK-0015-AC04** — Synthetic-secret leakage checks and actual selected native provider tests support the advertised exposure boundary; production credential changes are not part of fixture acceptance.
