# Remote stations

The owner authorized native Windows testing and implement-rfc station setup on
ExampleWinHost on September 5, 2026. The existing SSH alias `example-win-host` connects to
`ExampleWinHost.local` as `example`; key authentication and the existing host-key record
were verified without changing credentials, privileges or trust.

| Workstream | Station | Branch | Checkout | Environment | Authority | Provisioning |
|---|---|---|---|---|---|---|
| win | mask-win-example-win-host | codex/mask-win-example-win-host | `C:\code\git\ManageAgentSkills-win-example-win-host` | windows-native | read-only-proof | Provisioned; runner stopped and lease released after verification |

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

The SSH runner used `example` in Windows session 0, so its terminal was invisible
to the desktop in session 1. It was stopped without approving Claude's workspace
trust prompt; `station_lease.py status` then reported free. The Codex task's
tools used `CodexSandboxOffline`: normal inherited Git identity checks worked,
but the workflow helper's stripped Git environment exposed a dubious-ownership
refusal. The station verified the live lease through a read-only native lock
probe; no safe-directory configuration was added.

To run the retained station visibly, execute this in desktop PowerShell:

```powershell
py -3 'C:\code\git\AgentSkills-mask-station\skills\implement-rfc\scripts\launch_remote_station.py' win --repo-root 'C:\code\git\ManageAgentSkills-win-example-win-host' --machine example-win-host --read-only --permission-mode default
```

The operator handles any host workspace/hook trust prompt in that visible
terminal. The recorded station base remains `3456e3`; fixed revision `c03f85c`
was tested in a separate disposable clone. Refresh the station through its
ordinary controlled checkout-update workflow before testing newer revisions.
