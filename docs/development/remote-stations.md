# Remote stations

The owner authorized native Windows testing and implement-rfc station setup on
ExampleWinHost on September 5, 2026. The existing SSH alias `example-win-host` connects to
`ExampleWinHost.local` as `example`; key authentication and the existing host-key record
were verified without changing credentials, privileges or trust.

| Workstream | Station | Branch | Checkout | Environment | Authority | Provisioning |
|---|---|---|---|---|---|---|
| win | mask-win-example-win-host | codex/mask-win-example-win-host | `C:\code\git\ManageAgentSkills-win-example-win-host` | windows-native | read-only-proof | Setup in progress |

The local main integrator retains source edits, board updates and commit
acceptance. Windows station work is bounded verification of MASK-0029 with
fixture outputs only. Preserve existing checkouts and host settings. Native
Windows evidence must come from Windows Python and Git, not WSL. Use disposable
test fixture roots and record actual executable versions and limitations.

`gh repo clone` failed with HTTP 401 because the saved GitHub login is invalid.
Provisioning uses a local Git bundle transferred through the existing SSH
connection, with the original GitHub origin restored. No credentials are copied
or changed. The checkout is retained for the requested station; transfer archives
and temporary fixtures are removed after use.

Observed host: Windows 11 Home, build 10.0.26200, 64-bit. See
[readiness acceptance](readiness-acceptance.md) for actual test results. A connected
host or provisioned station is not passing acceptance evidence.
