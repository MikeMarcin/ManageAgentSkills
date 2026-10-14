# Security policy

MASK is a source preview, currently version 0.3.0. Report defects against the
current main revision and include the command, platform, expected behavior and
a minimal reproduction in a disposable project. Older revisions are not a
separately maintained security branch.

Never send live credentials through any reporting channel. Share sanitized
reproductions and exploit details privately; keep private skill contents and
personal machine state out of public issues. Use GitHub private vulnerability reporting when the repository's
Security page offers it. Before the repository becomes public, that feature is
unavailable; use an existing private owner contact. Enabling and confirming the
private reporting endpoint is an owner action at the public visibility switch.
This document does not claim that reporting is already enabled.

MASK runs locally with your user permissions. Git sources and skill payloads
are untrusted data until reviewed. Declared package setup runs only under the
reviewed installation task's explicit approval; it is not sandboxed. MASK
preserves unmanaged content and changed owned leaves, checks parent links,
locks its machine writers, and journals supported mutations for explicit
recovery. Same-user hostile filesystem races and forged local state are outside
its cooperative ownership guarantees. A payload hash identifies bytes; it does
not certify that their instructions or scripts are safe.

Program and tap updates use the existing Git route. MASK supplies no daemon,
telemetry service, automatic program-update channel, credential vault or remote
fleet controller. Release signatures, signer rotation and independently
bootstrapped update authenticity remain proposed RFC work. Tests and recorded
native acceptance establish only their named platform/behavior boundaries.
See [state and recovery](docs/architecture/state-and-recovery.md),
[readiness acceptance](docs/development/readiness-acceptance.md), and the
[trust roadmap](docs/rfcs/RFC-MASK-0016-public-trust-and-supply-chain-hardening.md).
