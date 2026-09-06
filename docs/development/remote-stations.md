# Remote stations

The owner authorized native Windows testing and implement-rfc station setup on
ExampleWinHost on September 5, 2026. The existing SSH alias `example-win-host` connects to
`ExampleWinHost.local` as `example`; key authentication and the existing host-key record
were verified without changing credentials, privileges or trust.

| Workstream | Station | Branch | Checkout | Environment | Authority | Provisioning |
|---|---|---|---|---|---|---|
| win | mask-win-example-win-host | codex/mask-win-example-win-host | `C:\code\git\ManageAgentSkills-win-example-win-host` | windows-native | read-only-proof | Codex task provisioned; Claude awaiting workspace trust |

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

The shared `launch_remote_station.py` and `station_lease.py` ran natively from
`C:\code\git\AgentSkills-mask-station`, source revision
`cd51863fd37d146cc90191de043bfa3190183883`. The launcher selected station ID
`stn-a56d2137` and Codex task `01a074a9-c988-7c93-88f6-4bcae49b32fa` using
Codex CLI 0.153.4. MASK base revision is
`3456e3954b51fa3fefa5a5c7072d4ab7067409f3`. Its branch and source checkout are
retained for the station. The owner's separately cloned checkout is untouched.

SSH's configured default shell is `C:\Program Files\Git\bin\bash.exe`.
Use explicit PowerShell for native commands; no default-shell setting was
changed. The cause of the SSH-session GitHub authentication failure remains
unresolved. Claude's trust prompt has not been approved, and host loading is
not inferred from Codex task provisioning.
