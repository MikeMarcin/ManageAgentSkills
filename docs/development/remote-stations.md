# Remote verification access

The owner authorized native Windows testing on ExampleWinHost on September 5, 2026.
The existing SSH alias `example-win-host` connects to `ExampleWinHost.local` as `example`;
SSH key authentication and the existing host-key record were verified without
changing credentials, privileges or trust.

Use disposable test checkouts under the remote user temporary directory. The
local integrator retains source edits, board updates and commit authority;
remote commands run tests and report evidence. Preserve existing checkouts and
host settings. Native Windows evidence must come from Windows Python and Git,
not WSL. Record each temporary root and remove it after consuming its results.

Observed host: Windows 11 Home, build 10.0.26200, 64-bit. See
[readiness acceptance](readiness-acceptance.md) for actual test results and versions.

No persistent agent station or remote write lane is provisioned. The portable
workflow station helpers remain optional and are not a MASK runtime feature.
